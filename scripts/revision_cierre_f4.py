"""Auditoría de F4 a partir de la corrida congelada, sin ajustar estimadores."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from hashlib import sha256
from itertools import chain
import json
from pathlib import Path

import numpy as np
from scipy.special import softmax

from experimento_f4 import COL, CONFIG, EVAL, EPS, F3, ORIGINAL, ROOT, SEASONS, day, file_hash, new_run_dir
from modelos_f4 import joint, markets, outcome

ORIGINAL_HASH = "b02ba878a39f11cbdb0203f51de5bb6c3f192904209e5ba77fb37c1a448f35c9"
MODEL_PATH = ROOT / "scripts/historico/f4_estadistico_v1"
GEN = {"B2", "P1", "P2", "DC1", "DC2"}
CLASSES = ("1", "X", "2")
DOUBLES = ("1X", "X2", "12")
SCORES = (("over", "Over"), ("under", "Under"))
GOAL_COLUMNS = tuple(f"p_{key}_{i}5" for key, _ in SCORES for i in range(5))
META = ("modelo", "partido", "temporada", "etapa", "competicion", "fecha", "bloque",
        "corte_objetivo", "corte_parametros", "generado_utc", "version")
COUNTS = {"seleccion": 3828, "calibracion": 926, "evaluacion": 1015}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def write_csv(path, records):
    it = iter(records)
    first = next(it)
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(first))
        writer.writeheader()
        writer.writerows(chain((first,), it))


def verified_sources():
    manifest = ORIGINAL / "MANIFIESTO_F4.json"
    original = read_json(manifest)
    sources = {manifest: ORIGINAL_HASH,
               ROOT / "docs/INFORME_F4.md": "6ef6a09f9db79ce3b92af144134a5886ba420d7a8b65be93e4fe9e0f3f54fb88",
               ROOT / "docs/CONFIG_F4.json": CONFIG, ROOT / "docs/MANIFIESTO_F3.json": F3}
    sources.update({ORIGINAL / name: digest for name, digest in original["archivos"].items()})
    sources[MODEL_PATH / "experimento_f4.py"] = original["scripts"]["experimento_f4.py"]
    sources[ROOT / "scripts/modelos_f4.py"] = original["scripts"]["modelos_f4.py"]
    snapshot = read_json(ROOT / "docs/MANIFIESTO_F3.json")["sha256"]
    inputs = {p: snapshot[p] for p in ("data/processed/f3_base_v1/X.csv", "data/processed/f3_base_v1/y.csv")}
    sources.update({ROOT / p: digest for p, digest in inputs.items()})
    check_hashes(sources)
    combined = sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return original, sources, inputs, combined


def check_hashes(files):
    for path, digest in files.items():
        if file_hash(path) != digest:
            raise ValueError(f"SHA-256 distinto del original en {path.name}")


def calibrators(finalists):
    fits = read_json(ORIGINAL / "diagnosticos_ajustes.json")
    result = {}
    for r in fits:
        if r["operacion"] != "temperatura":
            continue
        model = r["modelo"]
        t = r["temperatura"]
        if model in result or not r["convergio"] or not .5 <= t <= 3:
            raise ValueError(f"Calibrador archivado inválido: {model}")
        result[model] = dict(id=f"temperatura_escalar_f4_v1/{model}", corte=r["corte"],
                             n=r["n"], temperatura=t, origen="diagnosticos_ajustes.json")
    if result.keys() != finalists:
        raise ValueError("Universo de calibradores incompatible")
    return result


def check_row(r):
    if r["temporada"] not in SEASONS[1:]:
        raise ValueError("Temporada fuera de desarrollo")
    d = day(r["fecha"])
    if day(r["corte_objetivo"]) != d - 2 or day(r["corte_parametros"]) > d - 2:
        raise ValueError("Corte D−2 incoherente")
    phase = "seleccion" if r["temporada"] in SEASONS[1:3] else (
        "calibracion" if d < EVAL else "evaluacion")
    if phase != r["etapa"]:
        raise ValueError("Etapa incompatible con la fecha")
    p = np.array([float(r[c]) for c in COL])
    if not np.isfinite(p).all() or min(p) <= 0 or abs(p.sum() - 1) > 1e-10:
        raise ValueError("Vector 1X2 inválido")
    values = [r[c] for c in ("lambda_l", "lambda_v", "rho")]
    if (r["modelo"] in GEN and not all(values)) or (r["modelo"] not in GEN and any(values)):
        raise ValueError("Capacidad generativa incoherente")
    h, a, klass = (int(r[x]) for x in ("gl", "gv", "observado"))
    if min(h, a) < 0 or klass != (0 if h > a else 2 if h < a else 1):
        raise ValueError("Marcador incompatible con su etiqueta 1X2")
    return p, h, a, klass


def individual_records(directory, calibrator, provenance, original):
    seen, labels, groups = set(), {}, defaultdict(list)
    counts = Counter()

    def raw_rows():
        with (ORIGINAL / "predicciones_desarrollo.csv").open(encoding="utf-8", newline="") as stream:
            for r in csv.DictReader(stream):
                p, h, a, klass = check_row(r)
                model, match = r["modelo"], int(r["partido"])
                if (model, match) in seen or r["generado_utc"] != original["generado_utc"]:
                    raise ValueError("Predicción repetida o fecha de generación distinta de la corrida")
                seen.add((model, match))
                label = dict(partido=match, temporada=r["temporada"], etapa=r["etapa"],
                             competicion=r["competicion"], fecha=r["fecha"],
                             goles_local_90=h, goles_visitante_90=a, resultado_1x2=CLASSES[klass])
                if labels.setdefault(match, label) != label:
                    raise ValueError("Etiquetas contradictorias para el mismo partido")
                counts[model, r["etapa"]] += 1
                if r["etapa"] == "evaluacion":
                    groups[model].append((r, p, h, a, klass, match))
                keys = (*META, *COL, "p_1x", "p_x2", "p_12", *GOAL_COLUMNS, "p_btts_si", "p_btts_no",
                        "lambda_l", "lambda_v", "rho", "respaldo", "equipo_local_historial_corto",
                        "equipo_visitante_historial_corto")
                yield {**{k: r[k] for k in keys}, **provenance,
                       "formato_probabilidad": "bruta",
                       "matriz_marcadores_bruta": int(model in GEN), "calibrador_id": ""}

    write_csv(directory / "predicciones_brutas.csv", raw_rows())
    expected = {i for i, r in labels.items() if r["etapa"] == "evaluacion"}
    if (len(seen) != 69120 or set(groups) != calibrator.keys()
            or Counter(r["etapa"] for r in labels.values()) != COUNTS
            or any({row[-1] for row in entries} != expected for entries in groups.values())):
        raise ValueError("La corrida no contiene el universo congelado común")
    for model, cal in calibrator.items():
        if counts[model, "calibracion"] != COUNTS["calibracion"] or counts[model, "seleccion"] != COUNTS["seleccion"]:
            raise ValueError("Faltan emisiones del candidato finalista")
        limit = min(day(r["corte_objetivo"]) for r, *_ in groups[model])
        eligible = sum(r["etapa"] == "calibracion" and day(r["fecha"]) <= limit for r in labels.values())
        if day(cal["corte"]) != limit or cal["n"] != eligible:
            raise ValueError("Calibrador fuera de su ventana histórica")

    def calibrated_rows():
        for model, entries in groups.items():
            cal = calibrator[model]
            for r, raw, *_ in entries:
                p = softmax(np.log(raw) / cal["temperatura"])
                yield {**{k: r[k] for k in META}, **provenance, **dict(zip(COL, p)), **markets(p),
                       "formato_probabilidad": "temperatura_1x2",
                       "matriz_marcadores_bruta": 0, "calibrador_id": cal["id"]}

    write_csv(directory / "predicciones_calibradas_1x2.csv", calibrated_rows())
    write_csv(directory / "etiquetas_desarrollo.csv", labels.values())
    return groups


def class_summary(y, p):
    cm = np.zeros((3, 3), dtype=int)
    np.add.at(cm, (y, p.argmax(axis=1)), 1)
    details = []
    for i, klass in enumerate(CLASSES):
        support, predicted, tp = int(cm[i].sum()), int(cm[:, i].sum()), int(cm[i, i])
        details.append(dict(clase=klass, soporte=support, pronosticados=predicted, aciertos=tp,
                            precision=tp / predicted if predicted else None,
                            recall=tp / support if support else None,
                            f1=2 * tp / (support + predicted) if support + predicted else None))
    summary = dict(n=len(y), accuracy=float(np.trace(cm) / len(y)),
                   macro_f1=float(np.mean([r["f1"] or 0 for r in details])),
                   balanced_accuracy=float(np.mean([r["recall"] for r in details if r["soporte"]])))
    return cm, details, summary


def binary(p, actual):
    n = len(actual)
    match_p = np.where(actual, p, 1. - p)
    return dict(n=n, positivos=int(np.sum(actual)), p_media=float(np.mean(p)),
                frecuencia=float(np.mean(actual)), brier=float(np.mean((p - actual)**2)),
                log_loss=float(-np.log(np.maximum(match_p, EPS)).mean()),
                recortes=int(np.sum(match_p < EPS)))


def discrimination(p, actual):
    positives, negatives = np.count_nonzero(actual), np.count_nonzero(~actual)
    if not positives:
        return None, None
    order = np.argsort(-p, kind="stable")
    score, flags = p[order], actual[order]
    ends = np.r_[np.flatnonzero(score[1:] != score[:-1]), len(p) - 1]
    tp = np.cumsum(flags)[ends]
    fp = ends + 1 - tp
    delta_tp = np.diff(np.r_[0, tp])
    ap = float(np.sum(delta_tp * tp / (ends + 1)) / positives)
    if not negatives:
        return None, ap
    concordant = np.sum(np.diff(np.r_[0, fp]) * (tp - delta_tp / 2))
    return float(concordant / (positives * negatives)), ap


def draw_diagnostics(p, y, cm, context, out):
    mask = y == 1
    raw = binary(p, mask)
    auc, ap = discrimination(p, mask)
    bins = np.minimum(9, (p * 10).astype(int))
    total_ece = 0.
    for i in range(10):
        flag = bins == i
        n = int(flag.sum())
        obs = float(mask[flag].mean()) if n else None
        mean = float(p[flag].mean()) if n else None
        if n:
            total_ece += n * abs(obs - mean) / len(y)
        out["empate_calibracion"].append(dict(**context, bin=i, limite_inferior=i/10, limite_superior=(i+1)/10,
                                             n=n, p_media=mean, frecuencia=obs))
    raw.update(auc_roc=auc, precision_promedio=ap, ece_10_bins=total_ece,
               sesgo_media=raw["p_media"] - raw["frecuencia"], elecciones_argmax=int(cm[:, 1].sum()),
               aciertos_argmax=int(cm[1, 1]))
    out["empate_resumen"].append(dict(**context, **raw))
    for population, subset in (("todos", p), ("empate", p[mask]), ("otro", p[~mask])):
        quantiles = np.quantile(subset, [0, .05, .25, .5, .75, .95, 1]).tolist() if len(subset) else [None]*7
        out["empate_distribucion"].append(dict(**context, grupo=population, n=len(subset),
                                               media=float(subset.mean()) if len(subset) else None,
                                               **dict(zip(("min", "p05", "p25", "p50", "p75", "p95", "max"), quantiles))))


def market_result(context, name, event, n_total, p=None, actual=None, reason=""):
    score = (dict(n=0, positivos=None, p_media=None, frecuencia=None, brier=None, log_loss=None, recortes=None)
             if p is None else binary(p, actual))
    return dict(**context, mercado=name, evento=event, n_total=n_total, cobertura=score["n"]/n_total,
                estado="no_evaluable" if p is None else "evaluable", motivo=reason, **score)


def matrices(entries, support):
    result = []
    axes = np.arange(support["max_goles"] + 1)
    for r, raw, h, a, *_ in entries:
        l, v, rho = (float(r[x]) for x in ("lambda_l", "lambda_v", "rho"))
        if not all(support["rango_lambda"][0] <= k <= support["rango_lambda"][1] for k in (l, v)):
            raise ValueError("Tasa fuera del intervalo registrado")
        matrix = joint(l, v, rho, support)
        if max(h, a) >= len(axes):
            raise ValueError("Marcador observado fuera del soporte registrado")
        projected = markets(outcome(matrix), matrix)
        expected = [*raw, *(float(r[key]) for key in projected), float(r["p_exacta"])]
        actual = [*outcome(matrix), *projected.values(), matrix[h, a]]
        if not np.allclose(actual, expected, rtol=0, atol=1e-10):
            raise ValueError(f"El marcador reconstruido no concuerda con la corrida original: {r['partido']}")
        result.append(matrix)
    return np.asarray(result)


def exact_scores(cube, h, a, context, out):
    n, size, _ = cube.shape
    actual = np.ravel_multi_index((h, a), (size, size))
    flat = cube.reshape(n, -1)
    truth = flat[np.arange(n), actual]
    coverage = dict(n_total=n, cobertura=1., estado="evaluable", motivo="")
    score = dict(n=n, positivos=None, p_media=float(truth.mean()), frecuencia=None,
                 brier=float(np.mean(np.sum(flat**2, axis=1) - 2*truth + 1)),
                 log_loss=float(-np.log(np.maximum(truth, EPS)).mean()), recortes=int((truth < EPS).sum()))
    out["mercados"].append(dict(**context, mercado="marcador_exacto", evento="multiclase", **coverage, **score))
    for i in range(size):
        for j in range(size):
            rows = binary(cube[:, i, j], (h == i) & (a == j))
            out["marcadores_exactos_binarios"].append(dict(**context, goles_local=i, goles_visitante=j,
                                                          **coverage, **rows))
    mean_h = np.sum(cube.sum(axis=2) * np.arange(size), axis=1)
    mean_a = np.sum(cube.sum(axis=1) * np.arange(size), axis=1)
    for side, expected, obs in (("local", mean_h, h), ("visitante", mean_a, a), ("total", mean_h+mean_a, h+a)):
        out["mae_goles"].append(dict(**context, lado=side, **coverage, n=n, media=float(expected.mean()),
                                    observado=float(obs.mean()), mae=float(np.mean(abs(expected - obs)))))


def evaluate(groups, calibrator, support):
    out = defaultdict(list)
    for model, entries in sorted(groups.items()):
        raw = np.asarray([r[1] for r in entries])
        temp = softmax(np.log(raw) / calibrator[model]["temperatura"], axis=1)
        if not np.array_equal(raw.argmax(axis=1), temp.argmax(axis=1)):
            raise ValueError("El calibrador archivado cambió una elección argmax")
        h, a, y = np.asarray([r[2:5] for r in entries]).T
        comps = np.asarray([r[0]["competicion"] for r in entries])
        cube = matrices(entries, support) if model in GEN else None
        for comp in ("*", *sorted(set(comps))):
            keep = np.ones(len(y), dtype=bool) if comp == "*" else comps == comp
            local, visitor, result = h[keep], a[keep], y[keep]
            n = len(result)
            for version, forecasts in (("bruta", raw), ("temperatura", temp)):
                p = forecasts[keep]
                context = dict(modelo=model, competicion=comp, version=version)
                cm, detail, summary = class_summary(result, p)
                out["clasificacion_resumen"].append(dict(**context, **summary))
                out["clasificacion_clase"].extend(dict(**context, **record) for record in detail)
                out["matrices_confusion"].extend(dict(**context, clase_real=c, clase_argmax=d, n=int(cm[i,j]))
                                                  for i,c in enumerate(CLASSES) for j,d in enumerate(CLASSES))
                draw_diagnostics(p[:, 1], result, cm, context, out)
                for i, c in enumerate(CLASSES):
                    out["mercados"].append(market_result(context, "1X2", c, n, p[:, i], result == i))
                for i, name in zip((2, 0, 1), DOUBLES):
                    out["mercados"].append(market_result(context, "doble_oportunidad", name, n, 1-p[:, i], result != i))
                scope = cube[keep] if cube is not None and version == "bruta" else None
                reason = ("Calibración 1X2 sin distribución de marcadores" if version == "temperatura"
                          else "Estimador sin distribución de marcadores")
                for key, title in SCORES:
                    for line in range(5):
                        field = f"p_{key}_{line}5"
                        actual = local + visitor > line if key == "over" else local + visitor <= line
                        prob = np.asarray([float(r[0][field]) for r, use in zip(entries, keep) if use]) if scope is not None else None
                        out["mercados"].append(market_result(context, title, f"{line}.5", n, prob, actual, reason if prob is None else ""))
                for event, actual in (("si", (local > 0) & (visitor > 0)), ("no", (local == 0) | (visitor == 0))):
                    prob = np.asarray([float(r[0][f"p_btts_{event}"]) for r, use in zip(entries, keep) if use]) if scope is not None else None
                    out["mercados"].append(market_result(context, "BTTS", event, n, prob, actual, reason if prob is None else ""))
                if scope is not None:
                    exact_scores(scope, local, visitor, context, out)
                else:
                    out["mercados"].append(market_result(context, "marcador_exacto", "multiclase", n, reason=reason))
                    out["mae_goles"].extend(dict(**context, lado=side, n_total=n, cobertura=0., estado="no_evaluable",
                                                 motivo=reason, n=0, media=None, observado=None, mae=None)
                                            for side in ("local", "visitante", "total"))
    return out


def run(path):
    original, sources, inputs, dataset = verified_sources()
    source_code = {p: file_hash(p) for p in (Path(__file__).resolve(), ROOT / "scripts/experimento_f4.py")}
    selection = read_json(ORIGINAL / "seleccion_congelada.json")
    finalists = {"B0", "B1", "B2", "B3", *(x["candidato"] for x in selection["familias"].values())}
    cal = calibrators(finalists)
    target = new_run_dir(path)
    provenance = dict(dataset_sha256=dataset, configuracion_sha256=CONFIG)
    groups = individual_records(target, cal, provenance, original)
    for name, records in evaluate(groups, cal, read_json(ROOT / "docs/CONFIG_F4.json")["soporte"]).items():
        write_csv(target / (name+".csv"), records)
    write_json(target / "calibradores.json", cal)
    check_hashes(sources | source_code)
    to_relative = lambda mapping: {p.relative_to(ROOT).as_posix(): h for p,h in mapping.items()}
    write_json(target / "MANIFIESTO_CIERRE_F4.json",
               dict(revision=target.name, generado_utc=datetime.now(timezone.utc).isoformat(),
                    corrida_original=ORIGINAL.name, seleccion=selection["elegido"], dataset_sha256=dataset,
                    componentes_dataset=inputs, configuracion_sha256=CONFIG,
                    ajustes_nuevos=0, solicitudes_api=0, gasto_mxn=0,
                    n_predicciones_brutas=69120, n_predicciones_calibradas=sum(map(len, groups.values())),
                    n_etiquetas=sum(COUNTS.values()), n_evaluacion=COUNTS["evaluacion"],
                    fuentes_verificadas=to_relative(sources), codigo=to_relative(source_code),
                    resultados={p.name: file_hash(p) for p in sorted(target.iterdir())}))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, required=True)
    run(parser.parse_args().salida)
