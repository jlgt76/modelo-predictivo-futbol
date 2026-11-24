"""Experimento F5 sobre el snapshot de desarrollo de F3 y predicciones congeladas de F4."""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

from argparse import ArgumentParser
from collections import defaultdict
import csv
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import time

from joblib import dump
import numpy as np
from scipy.optimize import minimize_scalar

import experimento_f4 as f4
from interpretabilidad_f5 import explain
from modelos_f4 import dixon_fit, fit_elo_map, markets, outcome
from modelos_f5 import (blocks, calibrate, calibrator_choice, causal_elo, ensemble_fit, features,
                        from_components, log_loss, past_oof, probability, stacking_input, train)
from revision_cierre_f4 import verified_sources, check_hashes, write_json, write_csv

ROOT = f4.ROOT
CONFIG = ROOT / "docs/CONFIG_F5.json"
CONFIG_HASH = "ddc03df04afec3382342aa9ce053fd93a78a06f52bd2cff55ae7517fc2d26d63"
CONFIG_F4 = ROOT / "docs/CONFIG_F4.json"
F4_CLOSE = ROOT / "data/processed/f4_cierre_v1/MANIFIESTO_CIERRE_F4.json"
F4_CLOSE_HASH = "7a42875ab762a1c8b7d2165cf046627ac7b227f46046cb1ef7a08bb2b33439c6"
PACKAGE_NAMES = ("cloudpickle","joblib","lightgbm","narwhals","numpy","scikit-learn","scipy","threadpoolctl","xgboost")
EXTRA_SIGNALS = ("elo_l","elo_v","elo_d","elo_p1","elo_px","p2_l","p2_v","dc2_px","dc2_bajos")


def digest(path):
    return f4.file_hash(path)


def reference_rows(rows, config):
    by_key = {r.key:i for i,r in enumerate(rows)}
    ref = defaultdict(dict)
    with (f4.ORIGINAL / "predicciones_desarrollo.csv").open(encoding="utf-8", newline="") as f:
        for record in csv.DictReader(f):
            name = record["modelo"]
            if name not in config["referencias"]:
                continue
            idx = by_key[int(record["partido"])]
            game = rows[idx]
            if (record["corte_objetivo"] != f4.iso(game.day-2) or int(record["observado"]) != game.result
                    or record["competicion"] != game.comp or record["etapa"] != f4.phase(game)
                    or idx in ref[name]):
                raise ValueError("Universo, etiqueta o corte no coincide con la referencia congelada")
            ref[name][idx] = record
    ids = {i for i,r in enumerate(rows) if f4.phase(r) != "arranque"}
    if any(set(ref[name]) != ids for name in config["referencias"]):
        raise ValueError("Referencias incompletas")
    return ref


def prepare_features(rows, config, config_f4, ref, telemetry):
    values = {}
    for field in features(config, "ABCDEQ"):
        if field in ("competicion","l_racha_tipo","v_racha_tipo"):
            values[field] = np.asarray([r.x[field] for r in rows])
        else:
            values[field] = np.asarray([float(r.x[field]) if r.x[field] else np.nan for r in rows])
    signals = causal_elo(rows, config["senal_elo"])
    for j,name in enumerate(EXTRA_SIGNALS[:3]):
        values[name] = np.asarray([signals[r.key][j] for r in rows])
    for name in EXTRA_SIGNALS[3:]:
        values[name] = np.full(len(rows), np.nan)
    gaps = {r.key: signals[r.key][2] for r in rows}
    for stage, block, cutoff, train_ids, target in blocks(rows, config):
        if any(ref["P2"][i]["corte_parametros"] != f4.iso(cutoff) for i in target):
            raise ValueError("Señal estadística y bloque original tienen cortes distintos")
        start = time.perf_counter()
        mapper, diagnostic = fit_elo_map([rows[i] for i in train_ids],gaps,config_f4["lbfgsb"])
        if not diagnostic["convergio"]:
            raise ValueError("No convergió la conversión de la señal Elo base")
        telemetry.append(dict(modelo="senal_Elo_E1",bloque=block,corte=f4.iso(cutoff),n=len(train_ids),
                              ajustes=1,segundos_ajuste=time.perf_counter()-start,
                              parametros=diagnostic))
        for i in target:
            p = mapper(gaps[rows[i].key])
            values["elo_p1"][i], values["elo_px"][i] = p[:2]
            values["p2_l"][i] = float(ref["P2"][i]["lambda_l"])
            values["p2_v"][i] = float(ref["P2"][i]["lambda_v"])
            values["dc2_px"][i] = float(ref["DC2"][i]["px"])
            values["dc2_bajos"][i] = float(ref["DC2"][i]["p_bajos"])
    return values


class Experiment:
    def __init__(self, rows, ref, config, legacy, directory):
        self.rows, self.ref, self.cfg, self.directory = rows, ref, config, directory
        self.days = np.asarray([r.day for r in rows])
        self.y = np.asarray([r.result for r in rows])
        self.goals = np.asarray([r.goals for r in rows])
        self.telemetry, self.definitions = [], {}
        self.values = prepare_features(rows, config, legacy, ref, self.telemetry)
        self.store, self.parts, self.fallback = defaultdict(dict), defaultdict(dict), defaultdict(dict)
        self.inference = []
        self.interpret = defaultdict(list)
        self.support = config["soporte"]
        for name, src in config["clasificadores"].items():
            self.definitions[name] = dict(src, params=src.get("params") or config["clasificadores"][src["params_de"]]["params"])
        for name, group in ((f"ETmenos_{g}",g) for g in config["ablacion"]["retirar"]):
            spec = self.definitions["ET2"]
            self.definitions[name] = dict(spec, grupos="".join(k for k in spec["grupos"] if k not in group))
        self.definitions.update(config["generativos"])
        for name, mapping in ref.items():
            for i,r in mapping.items():
                self.store[name][i] = np.array([float(r[s]) for s in f4.COL])
                if r["lambda_l"]:
                    self.parts[name][i] = [(float(r["lambda_l"]),float(r["lambda_v"]),float(r["rho"]),1.)]

    def save_model(self, block, name, side, obj):
        folder = self.directory / "modelos" / block.replace("/", "_")
        folder.mkdir(parents=True,exist_ok=True)
        path = folder / f"{name}{side}.joblib"
        with path.open("xb") as output:
            dump(obj,output,compress=1)

    def record(self, name, target, p, fallback=""):
        if any(i in self.store[name] for i in target):
            raise ValueError("Emisión duplicada")
        self.store[name].update(zip(target,probability(p)))
        if fallback:
            self.fallback[name].update((i, fallback) for i in target)

    def joint_record(self, name, target, components, fallback=""):
        self.parts[name].update(zip(target,components))
        p = np.asarray([outcome(from_components(c,self.support)) for c in components])
        self.record(name,target,p,fallback)

    def log(self, name, block, bound, audit, side="", **extras):
        self.telemetry.append(dict(modelo=name,bloque=block,corte=f4.iso(bound),lado=side,**audit,**extras))

    def make_classifier(self,name,block,cutoff,history,target,explain_names):
        spec = self.definitions[name]
        cols = features(self.cfg,spec["grupos"])
        pipe,audit = train(self.values,cols,self.y,history,self.days,self.cfg,spec)
        start = time.perf_counter()
        self.record(name,target,pipe.predict(self.values,target))
        self.inference.append(dict(modelo=name,bloque=block,n=len(target),segundos=time.perf_counter()-start))
        self.log(name,block,cutoff,audit)
        self.save_model(block,name,"",pipe)
        if name in explain_names:
            explain(self.interpret,name,block,pipe,self.values,target,self.y,self.cfg,self.rows)

    def make_rates(self,name,block,cutoff,history,target):
        spec = self.definitions[name]
        offset = name == "H5"
        if offset:
            history = past_oof(self.store,history,[spec["offset"]],self.days,cutoff)
            if len(history) < spec["min_oof"]:
                self.joint_record(name,target,[self.parts[spec["offset"]][i] for i in target],"offset_oof_insuficiente")
                return
        cols = features(self.cfg,spec["grupos"])
        result = []
        for j,side in enumerate(("l","v")):
            margin = np.log(self.values[f"p2_{side}"]) if offset else None
            pipe,audit = train(self.values,cols,self.goals[:,j],history,self.days,self.cfg,spec,
                               regression=True,offsets=margin)
            start = time.perf_counter()
            rates = pipe.predict(self.values,target,margin[target] if offset else None)
            self.inference.append(dict(modelo=name,bloque=block,n=len(target),segundos=time.perf_counter()-start))
            clipped = np.clip(rates,*self.support["rango_lambda"])
            self.log(name,block,cutoff,audit,side,recortes=int(np.sum(clipped != rates)))
            self.save_model(block,name,"_"+side,pipe)
            result.append(clipped)
        self.joint_record(name,target,[[(float(a),float(b),0.,1.)] for a,b in zip(*result)])

    def make_dixon(self,block,cutoff,history,target):
        cfg = self.definitions["H3"]
        eligible = past_oof(self.store,history,[cfg["base"]],self.days,cutoff)
        rho = 0.
        fallback = "rho_oof_insuficiente" if len(eligible) < cfg["min_oof"] else ""
        if not fallback:
            start = time.perf_counter()
            h,a = np.asarray([self.parts[cfg["base"]][i][0][:2] for i in eligible]).T
            weight = np.exp2(-(cutoff - self.days[eligible])/cfg["vida_media"])
            rho,diag = dixon_fit([self.rows[i] for i in eligible],h,a,weight,self.support["rango_lambda"][1])
            if not diag["convergio"]:
                fallback = "rho_no_convergio"
            self.log("H3",block,cutoff,dict(n=len(eligible),ajustes=1,segundos_ajuste=time.perf_counter()-start),
                     rho=rho,diagnostico=diag)
        self.joint_record("H3",target,[[(h,a,rho,w) for h,a,_,w in self.parts[cfg["base"]][i]] for i in target],fallback)

    def make_ensemble(self,block,cutoff,history,target):
        cfg = self.cfg["ensembles"]
        names = cfg["componentes"]
        cube = lambda ids: np.asarray([[self.store[m][i] for m in names] for i in ids])
        current = cube(target)
        simple = current.mean(axis=1)
        self.record("S1",target,simple)
        eligible = past_oof(self.store,history,names,self.days,cutoff)
        if len(eligible) < cfg["min_oof"]:
            self.record("S2",target,simple,"meta_oof_insuficiente")
            self.record("S3",target,simple,"meta_oof_insuficiente")
        else:
            start = time.perf_counter()
            weights,meta,success = ensemble_fit(cube(eligible),self.y[eligible],self.cfg["semilla"])
            self.record("S2",target,np.einsum("nmc,m->nc", current, weights),"" if success else "pesos_no_convergentes")
            self.record("S3",target,meta.predict_proba(stacking_input(current)))
            self.save_model(block,"S3","",meta)
            self.log("S2/S3",block,cutoff,dict(n=len(eligible),ajustes=2,segundos_ajuste=time.perf_counter()-start),
                     pesos=weights.tolist(),componentes=names,max_oof=f4.iso(int(self.days[eligible[-1]])))
        family = cfg["G1"]
        self.joint_record("G1",target,[[(a,b,rho,w*family[m]) for m in family for a,b,rho,w in self.parts[m][i]] for i in target])

    def walk(self, stages, names, explained=()):
        for stage,block,cutoff,history,target in blocks(self.rows,self.cfg):
            if stage not in stages:
                continue
            for name in names:
                self.make_classifier(name,block,cutoff,history,target,explained if stage == "evaluacion" else ())
            for name in ("H1","H2","H5"):
                self.make_rates(name,block,cutoff,history,target)
            self.make_dixon(block,cutoff,history,target)
            self.make_ensemble(block,cutoff,history,target)
            print(block,len(target),flush=True)

    def freeze(self):
        from evaluar_f5 import freeze
        return freeze(self)

    def calibrate_models(self,names):
        begin = min(r.day for r in self.rows if f4.phase(r) == "evaluacion")
        bound = begin-self.cfg["dias_corte"]
        options = self.cfg["calibracion"]
        result, trace = {}, {}
        for name in names:
            ids = [i for i in self.store[name] if f4.phase(self.rows[i]) == "calibracion" and self.days[i] <= bound]
            result[name], trace[name] = self.calibrate_model(name,ids,bound,options)
        return result,trace

    def calibrate_model(self,name,ids,bound,options):
        p = np.asarray([self.store[name][i] for i in ids])
        started = time.perf_counter()
        kind,fitted,scores,n = calibrator_choice(p,self.y[ids],self.days[ids],bound,options)
        trial_count = 2 + int(kind != "bruta") if scores else 0
        self.log(name,"calibrador_1x2",bound,dict(n=n,ajustes=trial_count,segundos_ajuste=time.perf_counter()-started))
        if fitted is not None:
            self.save_model("calibracion",name,"_1x2",fitted)
        trace = dict(elegido=kind,n=n,corte=f4.iso(bound),validacion=scores,
                     temperatura=fitted if kind == "temperatura" else None)
        result = {i: {} for i in self.store[name] if f4.phase(self.rows[i]) == "evaluacion"}
        indexes = list(result)
        adjusted = calibrate(kind,fitted,np.asarray([self.store[name][i] for i in indexes]))
        for i,probs in zip(indexes,adjusted):
            result[i]["cal_1x2"] = (probs,None)
        if not self.parts[name]:
            return result,trace
        # Se explora un factor común a tasas sobre el tramo interno de calibración.
        pivot = int(self.days[ids[-1]]) - options["dias_validacion"] + 1
        train_ids = [i for i in ids if self.days[i] <= pivot-2]
        validation = [i for i in ids if self.days[i] >= pivot]
        trace["calibracion_generativa"] = dict(elegido="bruta",escala=1.,validacion={})
        if not train_ids or not validation:
            return result,trace

        def components(i, scale):
            low,high = self.support["rango_lambda"]
            return [(float(np.clip(a*scale,low,high)),float(np.clip(b*scale,low,high)),r,w)
                    for a,b,r,w in self.parts[name][i]]

        def loss(group, s):
            return float(np.mean([-np.log(max(f4.EPS,from_components(components(i,s),self.support)[tuple(self.goals[i])]))
                                  for i in group]))
        start = time.perf_counter()
        trial = minimize_scalar(lambda scale: loss(train_ids,scale),bounds=options["escala_tasas"],
                                method="bounded",options={"xatol":.001})
        baseline,challenger = loss(validation,1.),loss(validation,float(trial.x))
        scale = 1.
        accepted = trial.success and baseline-challenger >= options["mejora_minima"]
        if accepted:
            final = minimize_scalar(lambda scale:loss(ids,scale),bounds=options["escala_tasas"],
                                    method="bounded",options={"xatol":.001})
            scale = float(final.x) if final.success else 1.
        trace["calibracion_generativa"] = dict(elegido="escala" if scale!=1. else "bruta",escala=scale,
                                               validacion={"bruta":baseline,"escala":challenger})
        self.log(name,"calibrador_conjunto",bound,dict(n=len(ids),ajustes=1+int(accepted),
                                                     segundos_ajuste=time.perf_counter()-start))
        for i in indexes:
            c = components(i,scale)
            result[i]["cal_conjunta"] = (outcome(from_components(c,self.support)),c)
        return result,trace


def run(path):
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    original, sources, _, dataset = verified_sources()
    scripts = {ROOT/"scripts"/n:digest(ROOT/"scripts"/n) for n in
               ("experimento_f5.py","modelos_f5.py","evaluar_f5.py","interpretabilidad_f5.py",
                "experimento_f4.py","revision_cierre_f4.py","modelos_f4.py")}
    sources.update({CONFIG: CONFIG_HASH, F4_CLOSE:F4_CLOSE_HASH})
    check_hashes(sources)
    target = f4.new_run_dir(path)
    generated = datetime.now(timezone.utc).isoformat()
    rows, legacy = f4.read_inputs()
    print("Snapshot y referencias verificadas",flush=True)
    experiment = Experiment(rows,reference_rows(rows,config),config,legacy,target)
    names = list(config["clasificadores"]) + [f"ETmenos_{g}" for g in config["ablacion"]["retirar"]]
    experiment.walk(("seleccion",),names)
    selection = experiment.freeze()
    write_json(target/"SELECCION_CONGELADA_F5.json",selection)
    winners = set(selection["finalistas"].values())
    later = [n for n in config["clasificadores"] if n in winners | {"X1","LGB1","H4"}]
    experiment.walk(("calibracion","evaluacion"),later,winners)
    trained = later + ["H1","H2","H3","H5","S1","S2","S3","G1"]
    calibrated,trace = experiment.calibrate_models(trained)
    write_json(target/"CALIBRADORES_F5.json",trace)
    from evaluar_f5 import publish
    publish(experiment,generated,dataset,CONFIG_HASH,calibrated,trace)
    f4.verify_base()
    check_hashes(sources | scripts)
    manifest = dict(version=config["version"],generado_utc=generated,hash_datos=dataset,
                    configuracion_sha256=CONFIG_HASH,sqlite_v3=f4.HASH,seleccion_original_f4="E2",
                    ajustes_efectivos=sum(r["ajustes"] for r in experiment.telemetry),
                    presupuesto_mxn=0,apis=0,temporadas=list(f4.SEASONS),
                    dependencias={pkg:version(pkg) for pkg in PACKAGE_NAMES},
                    fuentes={p.relative_to(ROOT).as_posix():h for p,h in sources.items()},
                    scripts={p.relative_to(ROOT).as_posix():h for p,h in scripts.items()},
                    resultados={p.relative_to(target).as_posix():digest(p) for p in sorted(target.rglob("*")) if p.is_file()})
    write_json(target/"MANIFIESTO_F5.json",manifest)
    print("F5 publicada:",target.name,flush=True)


if __name__ == "__main__":
    cli = ArgumentParser(description=__doc__)
    cli.add_argument("--salida",required=True,type=Path)
    run(cli.parse_args().salida)
