"""Audita salidas F5 y referencias calibradas F4 sin volver a ajustar modelos."""
from argparse import ArgumentParser
from collections import Counter, defaultdict
import csv
from pathlib import Path
import sys
import time

import experimento_f5 as f5
import numpy as np
from joblib import load
from scipy.special import softmax

from eda_f3 import svg
from evaluar_f5 import boot_delta, loss_rows
from modelos_f4 import markets, outcome
from modelos_f5 import causal_elo, features, blocks, from_components, probability, stacking_input
from revision_cierre_f4 import check_hashes, read_json, write_csv, write_json


def csv_rows(path):
    with path.open(encoding="utf-8",newline="") as source:
        yield from csv.DictReader(source)


def build_inputs(rows,config,reference,diagnostics):
    values={}
    categories={"competicion","l_racha_tipo","v_racha_tipo"}
    for name in features(config,"ABCDEQ"):
        if name in categories:
            values[name]=np.array([r.x[name] for r in rows])
        else:
            values[name]=np.array([float(r.x[name]) if r.x[name] else np.nan for r in rows])
    state=causal_elo(rows,config["senal_elo"])
    for k,name in enumerate(f5.EXTRA_SIGNALS[:3]):
        values[name]=np.array([state[r.key][k] for r in rows])
    for name in f5.EXTRA_SIGNALS[3:]:
        values[name]=np.full(len(rows),np.nan)
    parameter={r["bloque"]:r["parametros"] for r in diagnostics if r["modelo"]=="senal_Elo_E1"}
    for _,block,_,_,ids in blocks(rows,config):
        params=parameter[block]
        for i in ids:
            z=params["pendiente"]*state[rows[i].key][2]/2
            p=softmax([z,params["intercepto_empate"],-z])
            values["elo_p1"][i],values["elo_px"][i]=p[:2]
            for name,model,key in (("p2_l","P2","lambda_l"),("p2_v","P2","lambda_v"),
                                   ("dc2_px","DC2","px"),("dc2_bajos","DC2","p_bajos")):
                values[name][i]=float(reference[model][i][key])
    return values


def original_probabilities(run,groups,rows,values,public,config):
    for stage,block,_,history,ids in groups:
        folder=run/"modelos"/block.replace("/","_")
        for path in sorted(folder.glob("*.joblib")):
            name=path.stem
            if name not in config["clasificadores"] and not name.startswith("ETmenos_"):
                continue
            pipe=load(path)
            tabular=pipe.encoder.transform(values,ids)
            estimator=pipe.model
            lightgbm=getattr(estimator,"booster_",None)
            def infer(matrix):
                return lightgbm.predict(matrix,num_threads=1) if lightgbm is not None else estimator.predict_proba(matrix)
            native=infer(tabular)
            recorded=np.array([public[name,rows[i].key] for i in ids])
            restored=probability(probability(native))
            difference=float(np.max(abs(restored-recorded)))
            if difference>1e-11:
                raise ValueError(f"Las probabilidades archivadas de {name} no reproducen {block}")
            label=np.array([rows[i].result for i in ids])
            affected=(native<f5.f4.EPS)
            trained_labels=np.array([rows[i].result for i in history])
            train_score=float(loss_rows(probability(infer(pipe.encoder.transform(values,history))),trained_labels).mean())
            outside=float(loss_rows(recorded,label).mean())
            yield dict(modelo=name,bloque=block,etapa=stage,n=len(ids),min_nativo=float(native.min()),
                       max_error_normalizacion=float(np.max(abs(native.sum(axis=1,dtype=float)-1))),
                       n_ceros=int(np.sum(native==0)),n_inferiores_piso=int(affected.sum()),
                       filas_alteradas_por_piso=int(affected.any(axis=1).sum()),
                       eventos_observados_recortados=int(affected[np.arange(len(ids)),label].sum()),
                       diferencia_maxima_reconstruccion=difference,
                       log_loss_entrenamiento=train_score,log_loss_bloque=outside,
                       brecha_descriptiva=outside-train_score)


def calibrated_comparison(rows,forecasts,reference,config):
    lookup={str(r.key):r for r in rows if f5.f4.phase(r)=="evaluacion"}
    f4={}
    for record in reference:
        model=record["modelo"]
        f4.setdefault(model,{})[record["partido"]]=[float(record[c]) for c in ("p1","px","p2")]
    by=defaultdict(dict)
    for r in forecasts:
        if r["etapa"]=="evaluacion":
            by[r["modelo"],r["emision"]][r["match_id"]]=[float(r[c]) for c in ("p1","px","p2")]
    for (model,variant),records in sorted(by.items()):
        for ref,rhs in sorted(f4.items()):
            ids=sorted(records.keys() & rhs.keys())
            if set(ids)!=set(lookup):
                raise ValueError("Cobertura distinta de F4 calibrada")
            target=[lookup[i] for i in ids]
            date=np.array([r.day for r in target])
            obs=np.array([r.result for r in target])
            p=np.array([records[i] for i in ids])
            q=np.array([rhs[i] for i in ids])
            for metric,left,right in (
                ("1X2",loss_rows(p,obs),loss_rows(q,obs)),
                ("empate",-np.log(np.where(obs==1,p[:,1],1-p[:,1])),
                 -np.log(np.where(obs==1,q[:,1],1-q[:,1])))):
                for length in (7,14):
                    yield dict(modelo=model,emision=variant,referencia=ref,emision_referencia="temperatura_F4",
                               metrica=metric,n=len(ids),dias=length,**boot_delta(left,right,date,config,length))


def valid_release(forecasts,rows,config):
    index={r.key:r for r in rows}
    seen=set()
    counts=Counter()
    max_joint_error=0.
    for r in forecasts:
        row=index[int(r["match_id"])]
        if (r["temporada"] not in f5.f4.SEASONS or r["temporada"]!=row.season
                or r["corte"]!=f5.f4.iso(row.day-2) or r["etapa"]!=f5.f4.phase(row)):
            raise ValueError("Temporada, etapa o corte incoherente en el registro de predicciones")
        key=r["modelo"],r["emision"],r["match_id"]
        if key in seen or {"gl","gv","observado","result"} & r.keys():
            raise ValueError("Clave duplicada o etiqueta mezclada en el registro de predicciones")
        seen.add(key)
        p=np.asarray([float(r[k]) for k in f5.f4.COL])
        probability(p[None,:])
        if abs(p.sum()-1)>1e-10:
            raise ValueError("Masa 1X2 publicada distinta de uno")
        components=f5.json.loads(r["matriz_componentes"]) if r["matriz_componentes"] else None
        if components is not None:
            if r["emision"]=="cal_1x2":
                raise ValueError("Calibración 1X2 vinculada a una matriz")
            matrix=from_components(components,config["soporte"])
            means=[matrix.sum(axis=axis)@np.arange(len(matrix)) for axis in (1,0)]
            err=max(float(np.max(abs(outcome(matrix)-p))),abs(means[0]-float(r["lambda_l"])),
                    abs(means[1]-float(r["lambda_v"])))
            max_joint_error=max(max_joint_error,err)
            if err>1e-10:
                raise ValueError("Marcador, marginal o mercado no consistente con su matriz")
            counts["emisiones_generativas"]+=1
        else:
            matrix=None
            if r["p_btts_si"] or r["p_over_05"] or r["lambda_l"]:
                raise ValueError("Salida no generativa con mercados de goles")
        for name,expected in markets(p,matrix).items():
            if abs(expected-float(r[name]))>1e-10:
                raise ValueError(f"Mercado no coherente: {name}")
        counts["emisiones_totales"]+=1
        counts[r["etapa"]]+=1
        counts[r["emision"]]+=1
    return dict(cuentas=dict(counts),error_max_matriz_1x2_o_marginal=max_joint_error)


def derived_inference(run,forecasts,rows,cfg,ref,telemetry):
    joined={(r["modelo"],int(r["match_id"])):(np.array([float(r[c]) for c in f5.f4.COL]),
              f5.json.loads(r["matriz_componentes"]) if r["matriz_componentes"] else None)
            for r in forecasts if r["emision"]=="bruta" and r["modelo"] in
            {"X1","LGB1","S1","S2","S3","G1","H3"}}
    weights={r["bloque"]:r["pesos"] for r in telemetry if r["modelo"]=="S2/S3"}
    for stage,b,_,_,ids in blocks(rows,cfg):
        keys=[rows[i].key for i in ids]
        x=np.asarray([[joined["X1",key][0],joined["LGB1",key][0],
                       [float(ref["B3"][i][c]) for c in f5.f4.COL]] for i,key in zip(ids,keys)])
        file=run/"modelos"/b.replace("/","_")/"S3.joblib"
        estimator=load(file) if file.exists() else None
        for name in ("S1","S2","S3","H3","G1"):
            entries=[joined[name,key] for key in keys]
            start=time.perf_counter()
            if name=="S1" or (name in {"S2","S3"} and b not in weights):
                p=x.mean(axis=1)
            elif name=="S2":
                p=np.einsum("nmc,m->nc",x,weights[b])
            elif name=="S3":
                p=estimator.predict_proba(stacking_input(x))
            else:
                p=np.asarray([outcome(from_components(c,cfg["soporte"])) for _,c in entries])
            elapsed=time.perf_counter()-start
            if not np.allclose(p,[q for q,_ in entries],atol=1e-10,rtol=0):
                raise ValueError(f"No se reproduce la combinación de {name} en {b}")
            labels=np.array([rows[i].result for i in ids])
            affected=(p<f5.f4.EPS)
            yield dict(modelo=name,bloque=b,etapa=stage,n=len(ids),segundos_inferencia=elapsed,
                       ambito="mezcla_o_proyeccion_sin_incluir_estimadores_base",
                       minimo_nativo=float(p.min()),n_ceros=int(np.sum(p==0)),
                       n_inferiores_piso=int(affected.sum()),
                       eventos_observados_recortados=int(affected[np.arange(len(ids)),labels].sum()))


def calibrated_provenance(source,forecasts,rows):
    matches={r.key:r for r in rows if f5.f4.phase(r)=="evaluacion"}
    outputs=defaultdict(lambda:defaultdict(dict))
    for r in forecasts:
        if r["etapa"]=="evaluacion" and r["emision"] in {"bruta","cal_1x2"}:
            outputs[r["modelo"]][r["emision"]][int(r["match_id"])]=np.asarray([float(r[k]) for k in f5.f4.COL])
    for name,info in read_json(source/"CALIBRADORES_F5.json").items():
        fold=outputs[name]
        ids=sorted(fold["cal_1x2"])
        if set(ids)!=set(matches) or set(ids)!=set(fold["bruta"]):
            raise ValueError("No se puede reconstruir la calibración de un objetivo")
        p=np.asarray([fold["bruta"][i] for i in ids])
        stored=np.asarray([fold["cal_1x2"][i] for i in ids])
        kind=info["elegido"]
        if kind=="temperatura":
            native=softmax(np.log(p)/info["temperatura"],axis=1)
        elif kind=="logistica":
            path=source/"modelos/calibracion"/f"{name}_1x2.joblib"
            native=load(path).predict_proba(np.log(p))
        else:
            native=p
        norm=probability(native)
        if not np.allclose(norm,stored,atol=1e-11,rtol=0):
            raise ValueError(f"Calibración registrada inconsistente de {name}")
        y=np.array([matches[i].result for i in ids])
        affected=(native<f5.f4.EPS)
        yield dict(modelo=name,metodo=kind,n=len(ids),minimo_nativo=float(native.min()),n_ceros=int(np.sum(native==0)),
                   n_inferiores_piso=int(affected.sum()),eventos_observados_recortados=int(affected[np.arange(len(ids)),y].sum()))


def chart(path,bins,models):
    data=defaultdict(list)
    for r in bins:
        if r["etapa"]=="evaluacion" and r["desglose"]=="total":
            data[r["modelo"],r["clase"]].append(r)
    parts=[]
    for i,model in enumerate(models):
        for j,klass in enumerate("1X2"):
            x,y=100+j*245,100+i*133
            size=96
            parts.append(f'<text x="{x}" y="{y-9}" font-size="12">{model} · {klass}</text>')
            parts.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" stroke="#98a6af"/>')
            parts.append(f'<path d="M{x} {y+size} L{x+size} {y}" stroke="#98a6af"/>')
            for r in data[model,klass]:
                col={"bruta":"#176a8c","cal_1x2":"#ad502e","cal_conjunta":"#497a55"}[r["version"]]
                cx=x+size*float(r["pronostico"])
                cy=y+size*(1-float(r["observado"]))
                parts.append(f'<circle cx="{cx}" cy="{cy}" r="{2+min(int(r["n"]),120)/45}" fill="{col}"><title>n={r["n"]}</title></circle>')
    svg("Fiabilidad 1X2 de finalistas y referencias","X: probabilidad; Y: frecuencia. Azul: bruta. Naranja: calibración 1X2. Verde: calibración conjunta.",
        "".join(parts),path,width=790,height=100+133*len(models))


def run(source,destination):
    manifest_path=source/"MANIFIESTO_F5.json"
    manifest_digest=f5.digest(manifest_path)
    manifest=read_json(manifest_path)
    hashes={source/k:v for k,v in manifest["resultados"].items()}
    hashes.update({f5.ROOT/k:v for k,v in (manifest["scripts"] | manifest["fuentes"]).items()})
    script=Path(__file__).resolve()
    hashes[script]=f5.digest(script)
    hashes[manifest_path]=manifest_digest
    evidence=f5.F4_CLOSE
    baseline=evidence.parent/"predicciones_calibradas_1x2.csv"
    hashes[evidence]=f5.F4_CLOSE_HASH
    hashes[baseline]=read_json(evidence)["resultados"][baseline.name]
    hashes[f5.CONFIG]=f5.CONFIG_HASH
    check_hashes(hashes)
    target=f5.f4.new_run_dir(destination)
    rows,_=f5.f4.read_inputs()
    config=read_json(f5.CONFIG)
    forecasts=source/"PREDICCIONES_F5.csv"
    public={(r["modelo"],int(r["match_id"])):[float(r[c]) for c in ("p1","px","p2")]
            for r in csv_rows(forecasts) if r["emision"]=="bruta"}
    ref=f5.reference_rows(rows,config)
    telemetry=read_json(source/"AJUSTES_F5.json")
    values=build_inputs(rows,config,ref,telemetry)
    integrity=valid_release(csv_rows(forecasts),rows,config)
    write_csv(target/"PROBABILIDADES_NATIVAS_QA_F5.csv",
              original_probabilities(source,blocks(rows,config),rows,values,public,config))
    write_csv(target/"COMPARATIVO_CALIBRADO_F4_F5.csv",calibrated_comparison(rows,csv_rows(forecasts),csv_rows(baseline),config))
    write_csv(target/"TIEMPOS_INFERENCIA_DERIVADOS_F5.csv",derived_inference(source,csv_rows(forecasts),rows,config,ref,telemetry))
    write_csv(target/"PISOS_CALIBRACION_F5.csv",calibrated_provenance(source,csv_rows(forecasts),rows))
    write_json(target/"INTEGRIDAD_PROBABILIDADES_F5.json",integrity)
    selection=read_json(source/"SELECCION_CONGELADA_F5.json")
    chart(target/"FIABILIDAD_1X2_F5.svg",csv_rows(source/"CALIBRACION_BINS_F5.csv"),
          ("E2","P2","DC2",*selection["finalistas"].values(),"H1","H2","H5","S3"))
    check_hashes(hashes)
    write_json(target/"MANIFIESTO_AUDITORIA_F5.json",
               dict(origen=source.name,python=sys.version.split()[0],sha256_manifiesto=manifest_digest,original_calibrado_F4=f5.digest(baseline),
                    codigo_sha256=hashes[script],ajustes_nuevos=0,
                    resultados={p.name:f5.digest(p) for p in sorted(target.iterdir())}))


if __name__=="__main__":
    cli=ArgumentParser(description=__doc__)
    cli.add_argument("--origen",required=True,type=Path)
    cli.add_argument("--salida",required=True,type=Path)
    args=cli.parse_args()
    run(args.origen,args.salida)
