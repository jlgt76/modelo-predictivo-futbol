"""Selección prerregistrada, métricas y exportación del experimento F5."""
from collections import defaultdict
import json

import numpy as np

import experimento_f4 as f4
from eda_f3 import svg
from interpretabilidad_f5 import importance_chart
from modelos_f4 import markets
from modelos_f5 import from_components, log_loss, blocks
from revision_cierre_f4 import binary, class_summary, discrimination, write_csv, write_json

CLASSES = "1X2"
EVENTS = ("p1","px","p2","p_1x","p_x2","p_12","p_btts_si","p_btts_no",
          *(f"p_{a}_{i}5" for i in range(5) for a in ("over","under")))


def boot_delta(a,b,days,cfg,length):
    groups = (days-days.min())//length
    _,ids = np.unique(groups,return_inverse=True)
    sums = np.bincount(ids,weights=a-b)
    n = np.bincount(ids)
    seed = np.random.default_rng(cfg["semilla"])
    draws = seed.integers(len(n),size=(cfg["bootstrap"],len(n)))
    samples = sums[draws].sum(axis=1)/n[draws].sum(axis=1)
    lo,hi = np.quantile(samples,[.025,.975])
    return dict(delta=float(np.mean(a-b)),ic_inf=float(lo),ic_sup=float(hi),bloques=len(n))


def records_p(e,name,ids):
    return np.asarray([e.store[name][i] for i in ids])


def loss_rows(p,y):
    return -np.log(np.maximum(f4.EPS,p[np.arange(len(y)),y]))


def generative(e,ids,components):
    size = e.support["max_goles"]+1
    axis = np.arange(size)
    total = np.add.outer(axis,axis)
    result = []
    for i,c in zip(ids,components):
        matrix = from_components(c,e.support)
        u,v=e.goals[i]
        if max(u,v) >= size:
            raise ValueError("Resultado fuera de soporte, revisar la cobertura")
        p_truth=float(matrix[u,v])
        mean_l=float(matrix.sum(axis=1)@axis)
        mean_v=float(matrix.sum(axis=0)@axis)
        projection={"p_btts_si":float(matrix[1:,1:].sum())}
        projection["p_btts_no"]=1-projection["p_btts_si"]
        for k in range(5):
            projection[f"p_under_{k}5"]=float(matrix[total<=k].sum())
            projection[f"p_over_{k}5"]=1-projection[f"p_under_{k}5"]
        result.append(dict(ll=-np.log(max(f4.EPS,p_truth)),brier=float((matrix**2).sum()-2*p_truth+1),
                           ml=mean_l,mv=mean_v,**projection))
    return result


def known(event,y,g):
    if event=="p1":
        return y==0
    if event=="px":
        return y==1
    if event=="p2":
        return y==2
    if event in ("p_1x","p_x2","p_12"):
        return y!={"p_1x":2,"p_x2":0,"p_12":1}[event]
    if event=="p_btts_si":
        return g.min(axis=1)>0
    if event=="p_btts_no":
        return g.min(axis=1)==0
    _,side,line=event.split("_")
    return g.sum(axis=1)>int(line[0]) if side=="over" else g.sum(axis=1)<=int(line[0])


def ece(p,y):
    buckets=np.minimum(9,(p*10).astype(int))
    return sum(abs(float((p[flag]-y[flag]).sum())) for i in range(10) if (flag:=buckets==i).any())/len(p)


def freeze(e):
    options=e.cfg["promocion"]
    candidates={n for n in e.cfg["clasificadores"] if not n.startswith("ETmedio")} | {
        "ETmedio","S1","S2","S3","H1","H2","H3","H5","G1"}
    ids=np.asarray(sorted(i for i in e.store["E2"] if f4.phase(e.rows[i])=="seleccion"))
    season=np.asarray([e.rows[i].season for i in ids])
    x=e.y[ids]
    e2=records_p(e,"E2",ids)
    e2_loss=loss_rows(e2,x)
    e2_brier=float(np.mean(np.sum((e2-np.eye(3)[x])**2,axis=1)))
    competitors=options["verificar_tambien"]
    threshold=options["umbral_1x2"]
    ratings={}
    for name in sorted(candidates):
        p=records_p(e,name,ids)
        loss=loss_rows(p,x)
        diff={s:float((loss-e2_loss)[season==s].mean()) for s in f4.SEASONS[1:3]}
        intervals={d:boot_delta(loss,e2_loss,e.days[ids],e.cfg,d) for d in (7,14)}
        other={ref:float(loss.mean()-log_loss(records_p(e,ref,ids),x)) for ref in competitors}
        brier=float(np.mean(np.sum((p-np.eye(3)[x])**2,axis=1)))
        cal_delta=ece(p[:,1],x==1)-ece(e2[:,1],x==1)
        cover=(len(ids)-sum(i in e.fallback[name] for i in ids))/len(ids)
        promote=(max(diff.values())<=-threshold and all(v["ic_sup"]<0 for v in intervals.values())
                 and max(other.values())<=0 and cover>=options["cobertura_minima"]
                 and brier-e2_brier<=options["max_deterioro_brier"]
                 and cal_delta<=options["max_deterioro_brier"])
        ratings[name]=dict(log_loss=float(loss.mean()),por_temporada=diff,intervalos=intervals,
                           diferencias_otras_referencias=other,delta_brier=brier-e2_brier,
                           delta_ece_empate=cal_delta,cobertura_sin_respaldo=cover,promueve=promote)
    finalists={}
    for family in ("xgb","lgb","rf","et"):
        names=[n for n,s in e.cfg["clasificadores"].items() if s["familia"]==family and n!="H4"]
        finalists[family]=min(names,key=lambda n:ratings[n]["log_loss"])
    allowed=sorted(n for n in ratings if ratings[n]["promueve"])
    selected=min(allowed,key=lambda n:ratings[n]["log_loss"]) if allowed else "E2"
    base={n:generative(e,ids,[e.parts[n][i] for i in ids]) for n in ("P2","DC2")}
    goal_truth=e.goals[ids]
    markets_gen=EVENTS[6:]
    def market_loss(records,event):
        return binary(np.array([r[event] for r in records]),known(event,x,goal_truth))["log_loss"]
    base_market={n:{k:market_loss(r,k) for k in markets_gen} for n,r in base.items()}
    detail={}
    for name in ("H1","H2","H3","H5","G1"):
        matrix=generative(e,ids,[e.parts[name][i] for i in ids])
        score=np.asarray([m["ll"] for m in matrix])
        p2=np.asarray([m["ll"] for m in base["P2"]])
        dc2=np.asarray([m["ll"] for m in base["DC2"]])
        vs_p=boot_delta(score,p2,e.days[ids],e.cfg,7)
        vs_p14=boot_delta(score,p2,e.days[ids],e.cfg,14)
        vs_dc=boot_delta(score,dc2,e.days[ids],e.cfg,7)
        deltas={s:float((score-p2)[season==s].mean()) for s in f4.SEASONS[1:3]}
        market_max=max(market_loss(matrix,k)-min(base_market[n][k] for n in base) for k in markets_gen)
        ready=(max(deltas.values())<=-options["umbral_marcador"] and max(vs_p["ic_sup"],vs_p14["ic_sup"],vs_dc["ic_sup"])<0
               and market_max<=options["max_deterioro_mercados"]
               and ratings[name]["cobertura_sin_respaldo"]>=options["cobertura_minima"])
        detail[name]=dict(log_loss_marcador=float(score.mean()),por_temporada=deltas,vs_P2_7dias=vs_p,
                          vs_P2_14dias=vs_p14,vs_DC2_7dias=vs_dc,mayor_deterioro_mercado=market_max,promueve=ready)
    accepted=[n for n in detail if detail[n]["promueve"]]
    chosen=min(accepted,key=lambda n:detail[n]["log_loss_marcador"]) if accepted else "P2"
    print("Congelada selección F5:",selected,chosen,flush=True)
    return dict(seleccion_1x2=selected,seleccion_generativa=chosen,finalistas=finalists,
                clasificacion=ratings,generativos=detail)


def scopes(e,ids,full=True):
    groups=defaultdict(list)
    block_of={i:b for _,b,_,_,target in blocks(e.rows,e.cfg) for i in target}
    for j,i in enumerate(ids):
        r=e.rows[i]
        stage=f4.phase(r)
        groups[stage,"total","*"].append(j)
        if full:
            for key,value in (("competicion",r.comp),("temporada",r.season),("bloque",block_of[i]),
                              ("resultado",CLASSES[r.result]),
                              ("historia","corta" if min(int(r.x["l_w10_n"]),int(r.x["v_w10_n"]))<10 else "completa")):
                groups[stage,key,value].append(j)
    return groups,block_of


def capture(e,name,variant,entries,stats):
    ids=np.asarray(sorted(entries))
    p=np.asarray([entries[i][0] for i in ids])
    comps=[entries[i][1] for i in ids]
    gen=generative(e,ids,comps) if comps[0] is not None else None
    y=e.y[ids]
    totals, _=scopes(e,ids,True)
    primary=loss_rows(p,y)
    residuals=p-np.eye(3)[y]
    for (stage,group,value),index in totals.items():
        context=dict(modelo=name,version=variant,etapa=stage,desglose=group,valor=value)
        obs,fcast=y[index],p[index]
        cm,cls,summary=class_summary(obs,fcast)
        loss=primary[index]
        errors=residuals[index]
        stats["RESULTADOS_MODELOS_F5"].append(dict(**context,**summary,log_loss=float(loss.mean()),
                                                   brier=float((errors**2).sum(axis=1).mean()),
                                                   rps=float((np.cumsum(errors,axis=1)[:,:2]**2).sum(axis=1).mean()/2),
                                                   respaldos=sum(ids[j] in e.fallback[name] for j in index),
                                                   ece=float(np.mean([ece(fcast[:,k],obs==k) for k in range(3)]))))
        for k,c in enumerate(CLASSES):
            auc,ap=discrimination(fcast[:,k],obs==k)
            stats["RESULTADOS_CLASE_F5"].append(dict(**context,**cls[k],auc_roc=auc,average_precision=ap))
            for j,d in enumerate(CLASSES):
                stats["MATRICES_CONFUSION_F5"].append(dict(**context,real=c,argmax=d,n=int(cm[k,j])))
            if group not in {"total","competicion","temporada"}:
                continue
            binned=np.minimum(9,(fcast[:,k]*10).astype(int))
            for j in range(10):
                mask=binned==j
                if mask.any():
                    stats["CALIBRACION_BINS_F5"].append(dict(**context,clase=c,bin=j,n=int(mask.sum()),
                                                             pronostico=float(fcast[mask,k].mean()),observado=float(np.mean(obs[mask]==k))))
        xx=fcast[:,1]
        if group in {"total","competicion","temporada"}:
            positives=obs==1
            auc,ap=discrimination(xx,positives)
            score=binary(xx,positives)
            lo=hi=aplo=aphi=None
            if group=="total" and stage=="evaluacion":
                split=(e.days[ids[index]]-e.days[ids[index]].min())//7
                groups=[np.flatnonzero(split==g) for g in np.unique(split)]
                rng=np.random.default_rng(e.cfg["semilla"])
                trials=[]
                for draw in rng.integers(len(groups),size=(e.cfg["bootstrap"],len(groups))):
                    sample=np.concatenate([groups[k] for k in draw])
                    a,b=discrimination(xx[sample],positives[sample])
                    if a is not None:
                        trials.append((a,b))
                (lo,aplo),(hi,aphi)=np.quantile(trials,[.025,.975],axis=0).tolist()
            stats["EMPATES_F5"].append(dict(**context,**score,auc_roc=auc,auc_ic_inf=lo,auc_ic_sup=hi,
                                            average_precision=ap,ap_ic_inf=aplo,ap_ic_sup=aphi,
                                            ece=ece(xx,positives),precision=cls[1]["precision"],
                                            recall=cls[1]["recall"],f1=cls[1]["f1"],
                                            argmax=int(cm[:,1].sum()),aciertos=int(cm[1,1]),
                                            p05=float(np.quantile(xx,.05)),p50=float(np.median(xx)),
                                            p95=float(np.quantile(xx,.95)),pmax=float(xx.max())))
        for k,event in enumerate(EVENTS):
            if group not in {"total","competicion","temporada"}:
                continue
            goal=e.goals[ids[index]]
            if k<3:
                pred=fcast[:,k]
            elif k<6:
                pred=1-fcast[:,(2,0,1)[k-3]]
            elif gen is not None:
                pred=np.asarray([gen[j][event] for j in index])
            else:
                pred=None
            score=binary(pred,known(event,obs,goal)) if pred is not None else {
                k:None for k in ("n","positivos","p_media","frecuencia","brier","log_loss","recortes")}
            stats["MERCADOS_F5"].append(dict(**context,mercado=event,evaluable=int(pred is not None),
                                             n_total=len(index),**score))
        if gen is not None:
            gx=e.goals[ids[index]]
            ml=np.asarray([gen[j]["ml"] for j in index])
            mv=np.asarray([gen[j]["mv"] for j in index])
            error=np.column_stack((gx[:,0]-ml,gx[:,1]-mv,gx.sum(axis=1)-ml-mv))
            for j,(side,mu) in enumerate((("local",ml),("visitante",mv),("total",ml+mv))):
                z=error[:,j]
                stats["GOLES_Y_MARCADORES_F5"].append(dict(**context,n=len(index),lado=side,
                                                           mae=float(np.mean(abs(z))),rmse=float(np.sqrt(np.mean(z**2))),
                                                           dispersion=float(np.mean(z**2/mu)),
                                                           log_loss_marcador=float(np.mean([gen[k]["ll"] for k in index])),
                                                           brier_marcador=float(np.mean([gen[k]["brier"] for k in index]))))
    return ids,primary,gen


def compare(e, name,variant,ids,p,gen,rows):
    for reference in e.cfg["referencias"]:
        match=np.asarray([i in e.store[reference] for i in ids])
        subset=ids[match]
        other=records_p(e,reference,subset)
        obs=e.y[subset]
        raw=p[match]
        all_indices=np.arange(len(subset))
        marks=defaultdict(list)
        for j,i in enumerate(subset):
            r=e.rows[i]
            stage=f4.phase(r)
            marks[stage,"*"].append(j)
            if stage=="seleccion":
                marks[stage,r.season].append(j)
        baseline=loss_rows(other,obs)
        draw=obs==1
        ax=-np.log(np.maximum(f4.EPS,np.where(draw,records_current(e,name,variant,subset,2),1-records_current(e,name,variant,subset,2))))
        bx=-np.log(np.maximum(f4.EPS,np.where(draw,other[:,1],1-other[:,1])))
        contrasts=[("1X2",raw,baseline),("empate",ax,bx)]
        if gen is not None and e.parts[reference]:
            scores_gen=generative(e,subset,[e.parts[reference][i] for i in subset])
            contrasts.append(("marcador_exacto",np.asarray([gen[j]["ll"] for j in np.flatnonzero(match)]),
                              np.asarray([r["ll"] for r in scores_gen])))
        for (stage,season),j in marks.items():
            for length in (7,14):
                for metric,a,b in contrasts:
                    rows.append(dict(modelo=name,version=variant,referencia=reference,etapa=stage,temporada=season,
                                     metrica=metric,dias=length,n=len(j),**boot_delta(a[j],b[j],e.days[subset[j]],e.cfg,length)))


def records_current(e,name,variant,ids,_):
    if variant=="bruta":
        return records_p(e,name,ids)[:,1]
    return np.asarray([e.adjusted[name][i][variant][0][1] for i in ids])


def plot_reliability(rows,path,names):
    parts=[]
    for j,name in enumerate(names):
        x,y=54+(j%4)*230,97+(j//4)*194
        size=130
        parts.append(f'<text x="{x}" y="{y-10}" font-size="13">{name}</text><rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" stroke="#91a3a9"/>')
        parts.append(f'<path d="M {x} {y+size} L {x+size} {y}" stroke="#91a3a9"/>')
        for r in rows:
            if r["modelo"]!=name or r["clase"]!="X":
                continue
            color={"bruta":"#196989","cal_1x2":"#b9582f","cal_conjunta":"#36713b"}[r["version"]]
            cx=x+size*r["pronostico"]
            cy=y+size*(1-r["observado"])
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{2+min(120,r["n"])/40}" fill="{color}" opacity=".75"><title>{r["version"]}, n={r["n"]}</title></circle>')
    height=100+194*((len(names)+3)//4)
    svg("Fiabilidad de P(X) · F5","X: probabilidad. Y: frecuencia. Azul: bruta. Naranja: calibración 1X2. Verde: calibración conjunta.",
        "".join(parts),path,width=920,height=height)


def publish(e,generated,dataset,config_hash,calibrated,trace):
    e.adjusted=calibrated
    stats=defaultdict(list)
    coverage={}
    adjusted=defaultdict(lambda:defaultdict(dict))
    for name,group in calibrated.items():
        for i,variants in group.items():
            for variant,emission in variants.items():
                adjusted[name][variant][i]=emission
    _,block_of=scopes(e,range(len(e.rows)),False)
    def forecast_rows():
        for name,group in sorted(e.store.items()):
            if not group:
                continue
            entries={i:(p,e.parts[name].get(i)) for i,p in group.items()}
            for variant,sample in {"bruta":entries,**adjusted[name]}.items():
                ids,p_loss,gen=capture(e,name,variant,sample,stats)
                if name not in e.cfg["referencias"]:
                    compare(e,name,variant,ids,p_loss,gen,stats["COMPARATIVO_F4_F5"])
                scopeset,_=scopes(e,ids,False)
                for (stage,_,_),j in scopeset.items():
                    eligible=sum(f4.phase(r)==stage for r in e.rows)
                    coverage.setdefault(name,{})[variant+"/"+stage]=dict(n=len(j),universo=eligible,
                        cobertura=len(j)/eligible,respaldo=sum(ids[k] in e.fallback[name] for k in j),
                        mercados="distribucion_marcadores" if gen is not None else "1x2_y_doble_oportunidad")
                if name in e.cfg["referencias"]:
                    continue
                spec=e.definitions.get(name)
                groups=spec.get("grupos","") if spec else ""
                varlist="|".join(features_from(e,groups)) if groups else ""
                for j,i in enumerate(ids):
                    p,components=sample[i]
                    game=e.rows[i]
                    raw_markets=markets(p)
                    if gen is not None:
                        raw_markets.update({ev:gen[j][ev] for ev in EVENTS[6:]})
                    yield dict(match_id=game.key,competicion=game.comp,temporada=game.season,fecha=f4.iso(game.day),
                               corte=f4.iso(game.day-2),bloque=block_of[i],etapa=f4.phase(game),
                               modelo=name,version=e.cfg["version"],emision=variant,configuracion_sha256=config_hash,
                               datos_sha256=dataset,generado_utc=generated,
                               calibrador="" if variant=="bruta" else f"{e.cfg['version']}/{name}/{variant}",
                               variables=varlist,cobertura="respaldo" if i in e.fallback[name] else "estimador",
                               motivo=e.fallback[name].get(i,""),
                               lambda_l=gen[j]["ml"] if gen is not None else None,
                               lambda_v=gen[j]["mv"] if gen is not None else None,
                               matriz_componentes=json.dumps(components,separators=(",",":")) if components else "",
                               **dict(zip(f4.COL,p)),**{k:raw_markets.get(k) for k in EVENTS[3:]})
    target=e.directory
    write_csv(target/"PREDICCIONES_F5.csv",forecast_rows())
    write_csv(target/"ETIQUETAS_F5.csv",(dict(match_id=r.key,result=CLASSES[r.result],goles_l=r.goals[0],
                                             goles_v=r.goals[1]) for r in e.rows))
    write_json(target/"COBERTURA_MODELOS_F5.json",coverage)
    ablation=[]
    for name in ["ET1","ETmedio","ET2",*[n for n in e.definitions if n.startswith("ETmenos_")],"X1","H4","H1","H3"]:
        reference="X1" if name in {"X1","H4"} else "H1" if name in {"H1","H3"} else "ET2"
        ids=np.asarray(sorted(set(e.store[name])&set(e.store[reference])))
        for year in f4.SEASONS[1:3]:
            idx=np.asarray([i for i in ids if e.rows[i].season==year])
            y=e.y[idx]
            a=loss_rows(records_p(e,name,idx),y)
            b=loss_rows(records_p(e,reference,idx),y)
            ablation.append(dict(modelo=name,comparado_con=reference,temporada=year,n=len(idx),
                                 log_loss=float(a.mean()),**boot_delta(a,b,e.days[idx],e.cfg,7)))
    stats["RESULTADOS_ABLACION_F5"]=ablation
    stats["TIEMPOS_INFERENCIA_F5"]=e.inference
    for key,result in e.interpret.items():
        stats[key.upper()+"_F5"]=result
    for name,rows in stats.items():
        write_csv(target/(name+".csv"),rows)
    write_json(target/"AJUSTES_F5.json",e.telemetry)
    reliability=[r for r in stats["CALIBRACION_BINS_F5"] if r["etapa"]=="evaluacion" and r["desglose"]=="total"]
    plot_reliability(reliability,target/"FIABILIDAD_EMPATE_F5.svg",sorted({r["modelo"] for r in reliability}))
    if e.interpret["permutacion"]:
        importance_chart(target/"IMPORTANCIA_F5.svg",e.interpret["permutacion"],"delta_log_loss","Importancia por permutación",svg)
    if e.interpret["shap_global"]:
        importance_chart(target/"SHAP_F5.svg",e.interpret["shap_global"],"mean_abs","Magnitud media de TreeSHAP",svg)


def features_from(e,groups):
    from modelos_f5 import features
    return features(e.cfg,groups)
