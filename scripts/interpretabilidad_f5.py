"""Importancia, permutación en datos fuera de ajuste y TreeSHAP exacto de XGBoost."""
from collections import defaultdict
import numpy as np
from xgboost import DMatrix

from modelos_f5 import log_loss, probability


def explain(state, name, block, pipeline, values, ids, labels, config, rows):
    x = pipeline.encoder.transform(values, ids)
    names = pipeline.encoder.names
    model = pipeline.model
    def predict(w):
        return probability(model.booster_.predict(w, num_threads=1) if hasattr(model, "booster_")
                           else model.predict_proba(w))

    y = labels[ids]
    loss = log_loss(predict(x), y)
    rng = np.random.default_rng(config["semilla"])
    for group in pipeline.encoder.columns:
        cols = [j for j, f in enumerate(names) if f == group or f.startswith(group+"=")]
        delta = []
        for _ in range(config["interpretacion"]["perm_repeticiones"]):
            swapped = x.copy()
            swapped[:, cols] = x[rng.permutation(len(x))][:, cols]
            delta.append(log_loss(predict(swapped), y) - loss)
        state["permutacion"].append(dict(modelo=name, bloque=block, variable=group, n=len(y),
                                         delta_log_loss=float(np.mean(delta)), dispersion=float(np.std(delta))))
    for col, score in zip(names, model.feature_importances_):
        state["nativa"].append(dict(modelo=name, bloque=block, variable=col, importancia=float(score)))
    if not hasattr(model, "get_booster"):
        return
    size = min(len(x), config["interpretacion"]["shap_muestra_por_bloque"])
    sample = np.linspace(0,len(x)-1,size,dtype=int)
    booster = model.get_booster()
    matrix = DMatrix(x[sample], nthread=1)
    values_shap = booster.predict(matrix, pred_contribs=True, strict_shape=True)
    margins = booster.predict(matrix, output_margin=True, strict_shape=True)
    if not np.allclose(values_shap.sum(axis=2), margins, atol=2e-5, rtol=0):
        raise ValueError("TreeSHAP no reconstruye el margen del modelo")
    for k, label in enumerate("1X2"):
        for j, col in enumerate(names):
            vals = values_shap[:,k,j]
            state["shap_global"].append(dict(modelo=name,bloque=block,clase=label,variable=col,n=size,
                                             mean_abs=float(np.mean(abs(vals))), p05=float(np.quantile(vals,.05)),
                                             p50=float(np.median(vals)), p95=float(np.quantile(vals,.95))))
        for i in range(min(3,size)):
            variables = np.argsort(-abs(values_shap[i,k,:-1]))[:5]
            for j in variables:
                state["shap_local"].append(dict(modelo=name,bloque=block,clase=label,
                                                match_id=rows[ids[sample[i]]].key,variable=names[j],
                                                valor=float(x[sample[i],j]),contribucion=float(values_shap[i,k,j]),
                                                margen=float(margins[i,k]), base=float(values_shap[i,k,-1])))
    n_inter = min(size,config["interpretacion"]["interacciones_muestra"])
    interaction = booster.predict(DMatrix(x[sample[:n_inter]],nthread=1),pred_interactions=True,strict_shape=True)
    summary = abs(interaction[:,1,:-1,:-1]).mean(axis=0)
    pairs = [(summary[i,j], i,j) for i in range(len(names)) for j in range(i+1,len(names))]
    for impact,i,j in sorted(pairs, reverse=True)[:8]:
        state["shap_interacciones"].append(dict(modelo=name,bloque=block,clase="X",variable_a=names[i],
                                                variable_b=names[j],n=n_inter,media_absoluta=float(impact)))


def importance_chart(path, records, field, title, svg):
    agg = defaultdict(list)
    for r in records:
        agg[r["modelo"], r["variable"]].append(r[field])
    top = sorted(((float(np.mean(x)),f"{a} · {b}") for (a,b),x in agg.items()),reverse=True)[:15]
    scale = max(abs(v) for v,_ in top) or 1
    from html import escape
    parts = []
    for j,(v,label) in enumerate(top):
        y=88+j*20
        parts.append(f'<text x="28" y="{y+13}" font-size="12">{escape(label)}</text>')
        parts.append(f'<rect x="310" y="{y}" width="{390*max(0,v)/scale}" height="13" fill="#29848c"/>')
        parts.append(f'<text x="711" y="{y+12}" font-size="11">{v:.4f}</text>')
    svg(title,"Promedio por bloque de evaluación interna, escala propia de la métrica", "".join(parts),path,
        width=820,height=405)
