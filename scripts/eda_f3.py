"""EDA descriptiva de v3 y diagnóstico de redundancias en las variables D−2."""

from collections import Counter, defaultdict
import csv
from datetime import date
from html import escape
import json
import math
import statistics as st

from features_f3 import HASH, LINES, OUT, ROOT, file_hash, load_matches, verify_base, write_csv


def pearson(a, b):
    return st.correlation(a, b) if len(a) > 1 and min(a) != max(a) and min(b) != max(b) else None


def ranks(data):
    out = [0.0]*len(data)
    order = sorted(range(len(data)), key=data.__getitem__)
    i = 0
    while i < len(order):
        j = i+1
        while j < len(order) and data[order[i]] == data[order[j]]:
            j += 1
        for k in order[i:j]:
            out[k] = (i+1+j)/2
        i = j
    return out


def association(a, b):
    return pearson(a, b), pearson(ranks(a), ranks(b))


def describe(values):
    n = len(values)
    avg = st.mean(values)
    variance = st.variance(values) if n > 1 else None
    sd = math.sqrt(variance) if variance is not None else None
    skew = n/((n-1)*(n-2))*sum(((x-avg)/sd)**3 for x in values) if sd and n > 2 else None
    return dict(media=avg, mediana=st.median(values), varianza=variance, desviacion=sd,
                asimetria=skew, var_media=variance/avg if avg and variance is not None else None)


def eda_groups(matches):
    groups = defaultdict(list)
    for m in matches:
        for key in (("global", "*", "*"), ("competicion", m.comp, "*"),
                    ("temporada", "*", m.season), ("competicion_temporada", m.comp, m.season)):
            groups[key].append(m)
        if m.comp == "CL":
            regime = "ediciones_fase_liga" if m.season == "2024-25" else "ediciones_grupos"
            groups["formato_cl", "CL", regime].append(m)
            phase = (m.phase or "").lower()
            stage = ("fase_liga" if phase.startswith("league") else
                     "fase_grupos" if phase.startswith(("group", "gruppe")) else
                     "playoff" if phase.startswith("playoffs") else "eliminacion")
            groups["fase_cl", "CL", f"{m.season}/{stage}"].append(m)
    return groups


def describe_group(key, matches):
    a, b = [m.hg for m in matches], [m.ag for m in matches]
    n = len(a)
    p, s = association(a, b)
    row = dict(nivel=key[0], competicion=key[1], temporada=key[2], n=n,
               victoria_local=sum(x > y for x, y in zip(a,b)),
               empate=sum(x == y for x, y in zip(a,b)), victoria_visitante=sum(x < y for x,y in zip(a,b)),
               btts_si=sum(x > 0 and y > 0 for x,y in zip(a,b)),
               arco_cero_local=b.count(0), arco_cero_visitante=a.count(0),
               dif_goles_local_visitante=st.mean(a)-st.mean(b), pearson_goles=p, spearman_goles=s,
               neutrales=sum(m.neutral == 1 for m in matches),
               sede_desconocida=sum(m.neutral is None for m in matches),
               sin_fase=sum(not m.phase for m in matches),
               sin_hora_fuente=sum(not m.source_time for m in matches),
               sin_available_at=sum(m.available_at is None for m in matches))
    row["btts_no"] = n-row["btts_si"]
    for line in LINES:
        over = sum(x+y > line for x,y in zip(a,b))
        row[f"over{line}5"] = over
        row[f"under{line}5"] = n-over
    for name in ("victoria_local", "empate", "victoria_visitante", "btts_si", "btts_no",
                 "arco_cero_local", "arco_cero_visitante", *[f"{side}{i}5" for i in LINES for side in ("over","under")]):
        row[name+"_pct"] = 100*row[name]/n
    row["brecha_victoria_local_visitante_pp"] = row["victoria_local_pct"]-row["victoria_visitante_pct"]
    for name, vector in (("local",a), ("visitante",b), ("total",[x+y for x,y in zip(a,b)])):
        row.update({name+"_"+k:v for k,v in describe(vector).items()})
    return row


def time_series(matches):
    by_month = defaultdict(list)
    for m in matches:
        month = date.fromordinal(m.day).isoformat()[:7]
        for comp in ("*",m.comp):
            by_month[comp,month].append(m)
    for (comp, month), group in sorted(by_month.items()):
        n = len(group)
        yield dict(competicion=comp, mes=month, n=n, goles_local=st.mean(m.hg for m in group),
                   goles_visitante=st.mean(m.ag for m in group), victoria_local=sum(m.hg>m.ag for m in group)/n,
                   empate=sum(m.hg==m.ag for m in group)/n, victoria_visitante=sum(m.hg<m.ag for m in group)/n)


def validate_index(rows, matches):
    expected = {m.key: (m.day, m.comp, m.season) for m in matches}
    if len(rows) != len(expected):
        raise ValueError("Tamaño de X distinto del universo experimental")
    for r in rows:
        day = date.fromisoformat(r["fecha_objetivo"]).toordinal()
        key = int(r["match_id"])
        if expected.pop(key, None) != (day, r["competicion"], r["temporada"]):
            raise ValueError("ID de X duplicado o incompatible con la base")
        if date.fromisoformat(r["corte_d2"]).toordinal() != day-2 or r["available_at"]:
            raise ValueError("Corte D−2 o disponibilidad de X incompatible")
        for side in ("l", "v"):
            last = r[f"{side}_fecha_ultima_historia"]
            if last and date.fromisoformat(last).toordinal() > day-2:
                raise ValueError("Historia posterior al corte")


def read_feature_diagnostics(path, matches):
    provenance = json.loads((OUT/"SNAPSHOT_FEATURES.json").read_text(encoding="utf-8"))
    expected = {"version": OUT.name, "perfil": "D-2", "filas": len(matches),
                "base_antes": HASH, "base_despues": HASH, "X": file_hash(path),
                "y": file_hash(OUT/"y.csv"), "codigo": file_hash(ROOT/"scripts/features_f3.py")}
    if provenance != expected:
        raise ValueError("X/y y su snapshot no coinciden; ejecuta features_f3.py")
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    validate_index(rows, matches)
    columns = list(rows[0])
    groups = defaultdict(list)
    for row in rows:
        groups[row["competicion"], row["temporada"]].append(row)
    coverage = {
        "version": "f3_base_v1", "n": len(rows),
        "regla": "vacío CSV significa desconocido/no evaluable; cero numérico observado se conserva",
        "global": {col: sum(r[col] != "" for r in rows) for col in columns},
        "por_competicion_temporada": [
            dict(competicion=key[0], temporada=key[1], n=len(g),
                 presentes={col: sum(r[col] != "" for r in g) for col in columns})
            for key,g in sorted(groups.items())
        ],
    }
    (OUT/"COBERTURA_FEATURES_F3.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")
    selected = [f"{side}_{var}" for side in ("l","v") for var in
                ("w5_ppg","w10_ppg","w20_ppg","w10_win","w10_gf","w10_ga","w10_dg","w10_over25",
                 "w10_under25","ponderada_ppg","ppg_ponderado_rival","ataque_rel","concesion_rel",
                 "dias_ultimo_registrado","partidos_reg_14d")]
    numeric = {c: [float(r[c]) if r[c] else None for r in rows] for c in selected}
    correlations = []
    for i,a in enumerate(selected):
        for b in selected[i:]:
            pairs = [(x,y) for x,y in zip(numeric[a],numeric[b]) if x is not None and y is not None]
            x,y = zip(*pairs) if pairs else ((),())
            p,s = association(x,y) if len(x)>=30 else (None,None)
            correlations.append(dict(variable_a=a, variable_b=b, n=len(pairs), pearson=p, spearman=s))
    write_csv(OUT/"correlaciones_features.csv", correlations)


def svg(title, description, content, path, width=860, height=390):
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">'
                    f'<title>{escape(title)}</title><desc>{escape(description)}</desc><rect width="100%" height="100%" fill="#fff"/>'
                    f'<g font-family="Segoe UI, sans-serif" fill="#14252e"><text x="38" y="36" font-size="23">{escape(title)}</text>'
                    f'<text x="38" y="59" font-size="13">{escape(description)}</text>{content}</g></svg>', encoding="utf-8")


def bars(matches, out):
    local, away = Counter(m.hg for m in matches), Counter(m.ag for m in matches)
    keys = list(range(max(local.keys() | away.keys())+1))
    top = math.ceil(max(max(local.values()), max(away.values()))/500)*500
    parts = []
    for y in range(0, top+1, 500):
        height = 289 - y/top*194
        parts.append(f'<path d="M62 {height}H820" stroke="#d9e3e7"/><text x="14" y="{height+4}" font-size="12">{y}</text>')
    step = 736/len(keys)
    for i in keys:
        x = 70 + i*step
        for shift, count, color in ((0,local[i],"#086c72"),(21,away[i],"#ba641b")):
            h = count/top*194
            parts.append(f'<rect x="{x+shift}" y="{289-h}" width="19" height="{h}" fill="{color}"/>')
        parts.append(f'<text x="{x+16}" y="309" font-size="12">{i}</text>')
    parts.append('<text x="66" y="341" font-size="14">Goles por equipo · <tspan fill="#086c72">Local</tspan> · <tspan fill="#ba641b">Visitante</tspan></text>')
    svg("Distribución de goles reglamentarios",f"Partidos de desarrollo: {len(matches)} · frecuencia absoluta", "".join(parts), out)


def trends(rows, out):
    all_months = [r for r in rows if r["competicion"]=="*"]
    start = date.fromisoformat(all_months[0]["mes"]+"-01")
    ordinals = [(date.fromisoformat(r["mes"]+"-01")-start).days for r in all_months]
    p = []
    ceiling = math.ceil(max(r[f] for r in all_months for f in ("goles_local","goles_visitante")))
    scale = 196/ceiling
    for value in range(ceiling+1):
        y = 297-value*scale
        p.append(f'<path d="M65 {y}H820" stroke="#d9e3e7"/><text x="41" y="{y+4}" font-size="12">{value}</text>')
    for field,color in (("goles_local","#086c72"),("goles_visitante","#ba641b")):
        coords = [(65+750*i/ordinals[-1],297-scale*r[field]) for i,r in zip(ordinals,all_months)]
        for k, ((x,y), row, day) in enumerate(zip(coords,all_months,ordinals)):
            if k and day-ordinals[k-1] <= 32:
                px,py = coords[k-1]
                p.append(f'<path d="M{px} {py}L{x} {y}" stroke="{color}" stroke-width="2"/>')
            p.append(f'<circle cx="{x}" cy="{y}" r="{2 if row["n"]>=30 else 4}" fill="{color}"><title>{row["mes"]}: {row[field]:.3f}; n={row["n"]}</title></circle>')
    for i,r in zip(ordinals,all_months):
        if r["mes"].endswith(("-01","-08")):
            p.append(f'<text x="{65+750*i/ordinals[-1]-18}" y="319" font-size="11">{r["mes"]}</text>')
    p.append('<text x="66" y="348" font-size="14"><tspan fill="#086c72">Local</tspan> · <tspan fill="#ba641b">Visitante</tspan> · círculos grandes: n &lt; 30</text>')
    svg("Goles por equipo a través del tiempo","Media mensual en las seis competiciones · sin unir meses sin partidos", "".join(p), out)


def main():
    verify_base()
    matches = load_matches()
    OUT.mkdir(parents=True, exist_ok=True)
    groups = eda_groups(matches)
    write_csv(OUT/"eda_resumen.csv", (describe_group(k, g) for k,g in sorted(groups.items())))
    write_csv(OUT/"marcadores_exactos.csv", (
        dict(nivel=k[0], competicion=k[1], temporada=k[2], gl=a, gv=b, frecuencia=n, porcentaje=100*n/len(g))
        for k,g in sorted(groups.items()) for (a,b),n in sorted(Counter((m.hg,m.ag) for m in g).items())
    ))
    months = list(time_series(matches))
    write_csv(OUT/"eda_mensual.csv", months)
    bars(matches, OUT/"distribucion_goles.svg")
    trends(months, OUT/"goles_mensuales.svg")
    read_feature_diagnostics(OUT/"X.csv", matches)
    verify_base()


if __name__ == "__main__":
    main()
