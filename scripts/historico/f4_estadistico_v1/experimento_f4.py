"""Walk-forward F4 únicamente sobre los CSV aprobados de F3."""
import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from collections import defaultdict
import csv
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
from itertools import groupby
import json
import math
import sys

import numpy as np
import scipy
from scipy.optimize import minimize_scalar
from scipy.special import softmax

from features_f3 import HASH, ROOT, SEASONS, file_hash, verify_base, write_csv
from modelos_f4 import attack_fit,b3,dixon_fit,elo_signals,fit_elo_map,fit_logistic,frequency,joint,markets,outcome,rates

INPUT=ROOT/"data/processed/f3_base_v1"
OUT=ROOT/"data/processed/f4_estadistico_v1"
F3="80e56c2d36b2311015052173bc6fa1019d5723e7bb80ba756a5bef652a415bcd"
CONFIG="75fcb37e9c11c6c88d18f55334db27a798cc94364dcfea377d45b209dd0742e0"
REFS=("B0","B1","B2","B3")
COL=("p1","px","p2")
EVAL=date(2025,1,1).toordinal()
EPS=1e-15
MARKET_KEYS=tuple(markets(np.ones(3)/3,np.eye(2)/2))


@dataclass(frozen=True)
class Game:
    key: int
    day: int
    season: str
    comp: str
    teams: tuple
    goals: tuple
    neutral: bool
    result: int
    x: dict


def day(s):
    return date.fromisoformat(s).toordinal()


def iso(n):
    return date.fromordinal(n).isoformat()


def read_inputs():
    verify_base()
    manifest=ROOT/"docs/MANIFIESTO_F3.json"
    config=ROOT/"docs/CONFIG_F4.json"
    if file_hash(manifest)!=F3 or file_hash(config)!=CONFIG:
        raise ValueError("Cambió el manifiesto o el prerregistro")
    hashes=json.loads(manifest.read_text(encoding="utf-8"))["sha256"]
    for p in (INPUT/"X.csv",INPUT/"y.csv",INPUT/"SNAPSHOT_FEATURES.json",ROOT/"scripts/features_f3.py"):
        if file_hash(p)!=hashes[p.relative_to(ROOT).as_posix()]:
            raise ValueError("Hash de F3 incorrecto")
    with (INPUT/"y.csv").open(encoding="utf-8",newline="") as f:
        labels=list(csv.DictReader(f))
    by={r["match_id"]:r for r in labels}
    with (INPUT/"X.csv").open(encoding="utf-8",newline="") as f:
        x=list(csv.DictReader(f))
    if len(labels)!=len(by) or len(by)!=len(x) or len(x)!=7720:
        raise ValueError("Universo o unicidad fuera del contrato")
    result=[]
    for row in x:
        d=day(row["fecha_objetivo"])
        if row["temporada"] not in SEASONS or row["available_at"] or day(row["corte_d2"])!=d-2:
            raise ValueError("Fecha o edición fuera del perfil")
        if any(row[f"{s}_fecha_ultima_historia"] and day(row[f"{s}_fecha_ultima_historia"])>d-2 for s in ("l","v")):
            raise ValueError("Historia posterior al corte")
        y=by.pop(row["match_id"])
        g=int(y["goles_local90"]),int(y["goles_visitante90"])
        klass=0 if g[0]>g[1] else 2 if g[0]<g[1] else 1
        if min(g)<0 or "1X2"[klass]!=y["resultado_1x2"]:
            raise ValueError("Etiqueta incoherente")
        result.append(Game(int(row["match_id"]),d,row["temporada"],row["competicion"],
                           (row["local_id"],row["visitante_id"]),g,row["sede_objetivo"]=="neutral",klass,row))
    if by:
        raise ValueError("Etiquetas sin partido")
    return sorted(result,key=lambda r:(r.day,r.key)),json.loads(config.read_text(encoding="utf-8"))


def phase(r):
    if r.season=="2021-22":
        return "arranque"
    if r.season in SEASONS[1:3]:
        return "seleccion"
    return "calibracion" if r.day<EVAL else "evaluacion"


def eligible(rows, d):
    return [r for r in rows if r.day<=d-2]


def predict(rows,cfg,chosen,stages,fits,generated):
    results=[]
    support,opts,minimum=cfg["soporte"],cfg["lbfgsb"],cfg["respaldo"]
    elo={c["id"]:elo_signals(rows,c) for c in cfg["familias"]["elo"] if c["id"] in chosen}
    def block(r):
        stage=phase(r)
        anchor=EVAL if stage=="evaluacion" else date(int(r.season[:4]),7,1).toordinal()
        return r.season,stage,(r.day-anchor)//cfg["dias_bloque"]
    for (season,stage,index), iterator in groupby((r for r in rows if phase(r) in stages),key=block):
        target=list(iterator)
        cutoff=target[0].day-2
        past=eligible(rows,target[0].day)
        assert past and max(r.day for r in past)<=min(r.day-2 for r in target)
        label=f"{season}/{stage}/{index}"
        groups={c:[r for r in past if r.comp==c] for c in sorted({r.comp for r in target})}
        gp,gr=frequency(past),rates(past)
        lp={c:frequency(g) if len(g)>=minimum["min_comp"] else gp for c,g in groups.items()}
        lr={c:rates(g) if len(g)>=minimum["min_comp"] else gr for c,g in groups.items()}
        totals=np.add.outer(np.arange(support["max_goles"]+1),np.arange(support["max_goles"]+1))

        def record(model,r,prior=None,lambdas=None,rho=None,fallback=False,nominal=None,thin=None):
            matrix=joint(*lambdas,rho,support) if lambdas is not None else None
            p=prior if matrix is None else outcome(matrix)
            if np.any(p<=0) or abs(p.sum()-1)>1e-10:
                raise ValueError("Probabilidades inválidas")
            result=dict(modelo=model,bloque=label,etapa=stage,temporada=season,partido=r.key,
                        competicion=r.comp,fecha=iso(r.day),corte_objetivo=iso(r.day-2),
                        corte_parametros=iso(cutoff),generado_utc=generated,version=cfg["version"],
                        neutral_confirmada=int(r.neutral),observado=r.result,gl=r.goals[0],gv=r.goals[1],
                        p1=float(p[0]),px=float(p[1]),p2=float(p[2]),respaldo=int(fallback),
                        equipo_local_historial_corto=None if thin is None else int(thin[0]),
                        equipo_visitante_historial_corto=None if thin is None else int(thin[1]),
                        lambda_l=float(lambdas[0]) if matrix is not None else None,
                        lambda_v=float(lambdas[1]) if matrix is not None else None,rho=rho,
                        p_bajos=float(matrix[:2,:2].sum()) if matrix is not None else None,
                        p_under25=float(matrix[totals<=2].sum()) if matrix is not None else None,
                        p_btts=float(matrix[1:,1:].sum()) if matrix is not None else None,
                        p_exacta=float(matrix[r.goals]) if matrix is not None and max(r.goals)<len(matrix) else None,
                        p1_si_nominal=float(nominal[0]) if nominal is not None else None,
                        px_si_nominal=float(nominal[1]) if nominal is not None else None)
            result.update(dict.fromkeys(MARKET_KEYS))
            result.update(markets(p,matrix))
            results.append(result)

        def log_fit(model,operation,n,diag,comp="*"):
            fits.append(dict(modelo=model,operacion=operation,bloque=label,competicion=comp,corte=iso(cutoff),n=n,**diag))

        def base_rates(r):
            rr=lr[r.comp]
            return np.repeat(rr.mean(),2) if r.neutral else rr

        for r in target:
            thin=len(groups[r.comp])<minimum["min_comp"]
            record("B0",r,gp)
            record("B1",r,lp[r.comp],fallback=thin)
            nominal=outcome(joint(*lr[r.comp],0.,support)) if r.neutral else None
            record("B2",r,lambdas=base_rates(r),rho=0.,fallback=thin,nominal=nominal)
            p3,fb=b3(lp[r.comp],r.x,minimum["min_forma"])
            record("B3",r,p3,fallback=fb)
        shared={}
        for family in ("poisson","dixon_coles"):
            for c in cfg["familias"][family]:
                name=c["id"]
                if name not in chosen:
                    continue
                for comp,g in groups.items():
                    fallback=len(g)<minimum["min_generativo_comp"]
                    rho=0.
                    if not fallback:
                        sig=(comp,c["l2"],c["vida_media"])
                        if sig not in shared:
                            shared[sig]=attack_fit(g,c,cutoff,opts,support)
                            log_fit(name,"ataque_defensa",len(g),shared[sig][1],comp)
                        predict_one,diag,lh,la,w,counts=shared[sig]
                        fallback=not diag["convergio"]
                        if family=="dixon_coles" and not fallback:
                            rho,diagnostic=dixon_fit(g,lh,la,w,support["rango_lambda"][1])
                            log_fit(name,"rho_condicional",len(g),dict(rho=rho,**diagnostic),comp)
                            fallback=not diagnostic["convergio"]
                    for r in target:
                        if r.comp==comp:
                            nominal=None
                            if r.neutral:
                                nr=replace(r,neutral=False)
                                nrate=base_rates(nr) if fallback else predict_one(nr,minimum["min_equipo"])
                                nominal=outcome(joint(*nrate,0. if fallback else rho,support))
                            record(name,r,lambdas=base_rates(r) if fallback else predict_one(r,minimum["min_equipo"]),
                                   rho=0. if fallback else rho,fallback=fallback,nominal=nominal,
                                   thin=None if fallback else [counts.get(t,0)<minimum["min_equipo"] for t in r.teams])
        for name,signals in elo.items():
            mapping,diag=fit_elo_map(past,signals,opts)
            log_fit(name,"conversion_elo",len(past),diag)
            advantage=next(c["localia"] for c in cfg["familias"]["elo"] if c["id"]==name)/400
            for r in target:
                nominal=mapping(signals[r.key]+advantage) if r.neutral and diag["convergio"] else None
                record(name,r,mapping(signals[r.key]) if diag["convergio"] else lp[r.comp],
                       fallback=not diag["convergio"],nominal=nominal)
        for c in cfg["familias"]["logistica"]:
            name=c["id"]
            if name not in chosen:
                continue
            cols=[k for g in c["grupos"] for k in cfg["features"][g]]
            classifier,diag=fit_logistic(past,cols,c["l2"],opts)
            log_fit(name,"logistica",len(past),diag)
            for r,p in zip(target,classifier(target)):
                record(name,r,p if diag["convergio"] else lp[r.comp],fallback=not diag["convergio"])
    return results


def grouped(rows):
    result=defaultdict(list)
    for r in rows:
        result[r["modelo"]].append(r)
    return result


def arrays(rows):
    return np.array([[r[c] for c in COL] for r in rows]), np.array([r["observado"] for r in rows],dtype=int)


def scores(rows,p=None):
    raw,y=arrays(rows)
    p=raw if p is None else p
    actual=p[np.arange(len(y)),y]
    error=p-np.eye(3)[y]
    return dict(n=len(y),log_loss=float(-np.log(np.maximum(EPS,actual)).mean()),
                brier=float(np.sum(error**2,axis=1).mean()),rps=float((np.cumsum(error,axis=1)[:,:2]**2).sum(axis=1).mean()/2),
                accuracy=float((p.argmax(axis=1)==y).mean()),clips=int((actual<EPS).sum()),
                respaldos=sum(r["respaldo"] for r in rows))


def paired(a,b,cfg,dias=None):
    other={r["partido"]:r for r in b}
    if {r["partido"] for r in a}!=other.keys():
        raise ValueError("No coinciden partidos de comparación")
    weeks=defaultdict(list)
    for r in a:
        name=COL[r["observado"]]
        d=day(r["fecha"])
        block=d//dias if dias else date.fromordinal(d).isocalendar()[:2]
        weeks[block].append(
            math.log(max(EPS,other[r["partido"]][name]))-math.log(max(EPS,r[name])))
    array=np.array([(sum(x),len(x)) for x in weeks.values()])
    rng=np.random.default_rng(cfg["semilla"])
    boots=array[rng.integers(len(array),size=(cfg["bootstrap"],len(array)))].sum(axis=1)
    return dict(diferencia=float(array[:,0].sum()/array[:,1].sum()),
                ic95=np.quantile(boots[:,0]/boots[:,1],[.025,.975]).tolist(),semanas=len(array))


def adjudicate(selection,cfg):
    by=grouped(selection)
    summary={k:scores(v) for k,v in by.items()}
    decisions={}
    for family,candidates in cfg["familias"].items():
        best=min((c["id"] for c in candidates),key=lambda m:summary[m]["log_loss"])
        diff=paired(by[best],by["B1"],cfg)
        deltas={s:paired([r for r in by[best] if r["temporada"]==s],
                         [r for r in by["B1"] if r["temporada"]==s],cfg)["diferencia"] for s in SEASONS[1:3]}
        decisions[family]=dict(candidato=best,frente_B1=diff,diferencias_por_temporada=deltas,
                               supera=diff["ic95"][1]<0 and max(deltas.values())<=-.005 and
                               summary[best]["log_loss"]<min(summary[m]["log_loss"] for m in REFS))
    winners=[d["candidato"] for d in decisions.values() if d["supera"]]
    return dict(elegido=min(winners or REFS,key=lambda m:summary[m]["log_loss"]),familias=decisions,metricas=summary)


def reports(later,fits,cfg):
    eval_rows=[r for r in later if r["etapa"]=="evaluacion"]
    bound=min(day(r["fecha"]) for r in eval_rows)-2
    metrics,bins,markets,comparison=[],[],[],{}
    base=grouped(eval_rows)["B1"]
    for name,rows in grouped(later).items():
        calibrating=[r for r in rows if r["etapa"]=="calibracion" and day(r["fecha"])<=bound]
        p,y=arrays(calibrating)
        objective=lambda t: -np.log(np.maximum(EPS,softmax(np.log(p)/t,axis=1)[np.arange(len(y)),y])).mean()
        fit=minimize_scalar(objective,bounds=(.5,3),method="bounded")
        t=float(fit.x) if fit.success else 1.
        fits.append(dict(modelo=name,operacion="temperatura",bloque="calibracion",corte=iso(bound),
                         n=len(y),temperatura=t,convergio=bool(fit.success),iteraciones=int(fit.nfev)))
        evaluation=[r for r in rows if r["etapa"]=="evaluacion"]
        comparison[name]=paired(evaluation,base,cfg)
        for c in ("*",*sorted({r["competicion"] for r in evaluation})):
            group=[r for r in evaluation if c=="*" or r["competicion"]==c]
            raw,y=arrays(group)
            for variant,p in (("bruta",raw),("temperatura",softmax(np.log(raw)/t,axis=1))):
                metrics.append(dict(modelo=name,version=variant,competicion=c,**scores(group,p)))
                for k in range(3):
                    for i in range(10):
                        mask=np.minimum(9,(p[:,k]*10).astype(int))==i
                        if mask.any():
                            n=int(mask.sum())
                            observed=float((y[mask]==k).mean())
                            z=1.95996398454
                            denominator=1+z*z/n
                            center=(observed+z*z/(2*n))/denominator
                            margin=z*np.sqrt(observed*(1-observed)/n+z*z/(4*n*n))/denominator
                            bins.append(dict(modelo=name,version=variant,competicion=c,clase="1X2"[k],bin=i,
                                             n=n,pronostico=float(p[mask,k].mean()),observado=observed,
                                             wilson_inf=max(0.,center-margin),wilson_sup=min(1.,center+margin)))
            for field in ("px","p_bajos","p_under25","p_btts","p_exacta"):
                sample=[r for r in group if r[field] is not None]
                if not sample:
                    continue
                functions={"px":lambda r:r["observado"]==1,"p_bajos":lambda r:max(r["gl"],r["gv"])<=1,
                           "p_under25":lambda r:r["gl"]+r["gv"]<=2,
                           "p_btts":lambda r:min(r["gl"],r["gv"])>0,"p_exacta":lambda r:True}
                p=np.array([r[field] for r in sample])
                actual=np.array([functions[field](r) for r in sample])
                loss=-np.log(np.maximum(EPS,np.where(actual,p,1-p)))
                markets.append(dict(modelo=name,competicion=c,mercado=field,n=len(p),p_media=float(p.mean()),
                                    frecuencia=None if field=="p_exacta" else float(actual.mean()),log_loss=float(loss.mean())))
    return eval_rows,metrics,bins,markets,comparison


def write_json(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def goal_diagnostics(rows):
    groups=defaultdict(list)
    for r in rows:
        if r["lambda_l"] is not None:
            groups[r["etapa"],r["modelo"],r["competicion"]].append(r)
    result=[]
    for (stage,model,comp), group in sorted(groups.items()):
        for suffix,field in (("l","gl"),("v","gv")):
            expected=np.array([r["lambda_"+suffix] for r in group])
            actual=np.array([r[field] for r in group])
            residual=(actual-expected)/np.sqrt(expected)
            result.append(dict(etapa=stage,modelo=model,competicion=comp,lado=suffix,n=len(group),
                               goles_media=float(actual.mean()),tasa_media=float(expected.mean()),
                               residuo_medio=float((actual-expected).mean()),
                               dispersion_pearson=float(np.mean(residual**2)),rmse=float(np.sqrt(np.mean((actual-expected)**2)))))
    return result


def block_summary(rows,predictions):
    blocks=defaultdict(dict)
    byid={r.key:r for r in rows}
    for p in predictions:
        blocks[p["bloque"]][p["partido"]]=byid[p["partido"]]
    result=[]
    for name,entries in blocks.items():
        group=list(entries.values())
        first,last=min(r.day for r in group),max(r.day for r in group)
        hist=eligible(rows,first)
        counts=np.bincount([r.result for r in group],minlength=3)
        result.append(dict(bloque=name,primera_fecha=iso(first),ultima_fecha=iso(last),
                           corte_maximo=iso(first-2),historia_n=len(hist),objetivos_n=len(group),
                           local=int(counts[0]),empate=int(counts[1]),visitante=int(counts[2]),
                           neutral_confirmada=sum(r.neutral for r in group)))
    return result


def main():
    generated=datetime.now(timezone.utc).isoformat()
    scripts={n:file_hash(ROOT/"scripts"/n) for n in ("experimento_f4.py","modelos_f4.py")}
    rows,cfg=read_inputs()
    assert all(len(x)<=cfg["presupuesto_maximo_por_familia"] for x in cfg["familias"].values())
    OUT.mkdir(parents=True,exist_ok=True)
    fits=[]
    candidates={c["id"] for fam in cfg["familias"].values() for c in fam}
    pre=[r for r in rows if phase(r) in ("arranque","seleccion")]
    selection=predict(pre,cfg,candidates,("seleccion",),fits,generated)
    choice=adjudicate(selection,cfg)
    write_json("seleccion_congelada.json",choice)
    print("Selección congelada:",choice["elegido"],flush=True)
    chosen={v["candidato"] for v in choice["familias"].values()}
    later=predict(rows,cfg,chosen,("calibracion","evaluacion"),fits,generated)
    evaluation,metrics,bins,markets,comparison=reports(later,fits,cfg)
    evaluation_by=grouped(evaluation)
    contrasts={}
    model=choice["elegido"]
    poisson=choice["familias"]["poisson"]["candidato"]
    dixon=choice["familias"]["dixon_coles"]["candidato"]
    reference=min(REFS,key=lambda r:choice["metricas"][r]["log_loss"])
    for a,b in {(model,reference),(dixon,poisson),(model,poisson),(model,dixon)}:
        if a==b or a not in evaluation_by or b not in evaluation_by:
            continue
        first,second=evaluation_by[a],evaluation_by[b]
        contrasts[a+"-"+b]={"semana":paired(first,second,cfg),"14_dias":paired(first,second,cfg,dias=14)}
    write_json("diferencias_pareadas.json",dict(sorted(contrasts.items())))
    write_csv(OUT/"diagnostico_goles.csv",goal_diagnostics(selection+later))
    write_csv(OUT/"bloques.csv",block_summary(rows,selection+later))
    verify_base()
    write_csv(OUT/"predicciones_desarrollo.csv",selection+later)
    write_csv(OUT/"metricas_evaluacion.csv",metrics)
    write_csv(OUT/"calibracion_bins.csv",bins)
    write_csv(OUT/"mercados_y_marcador.csv",markets)
    write_json("diagnosticos_ajustes.json",fits)
    write_json("comparacion_evaluacion_bruta.json",comparison)
    if any(file_hash(ROOT/"scripts"/n)!=h for n,h in scripts.items()):
        raise ValueError("Cambió el código durante la corrida")
    write_json("MANIFIESTO_F4.json",dict(snapshot_f3=F3,config=CONFIG,sqlite_v3=HASH,
              python=sys.version.split()[0],numpy=np.__version__,scipy=scipy.__version__,
              archivos={p.name:file_hash(p) for p in sorted(OUT.iterdir()) if p.name!="MANIFIESTO_F4.json"},
              scripts=scripts,
              n_ajustes=len(fits),generado_utc=generated,coste_mxn=0))
    print("Evaluación interna:",len({r["partido"] for r in evaluation}),"partidos,",len(fits),"ajustes.")


if __name__=="__main__":
    main()
