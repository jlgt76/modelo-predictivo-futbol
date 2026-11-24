"""Modelos estadísticos y referencias para la evaluación experimental D−2."""

from collections import defaultdict
from itertools import groupby
import math

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import logsumexp, softmax


def frequency(rows):
    return (np.bincount([r.result for r in rows], minlength=3) + 1) / (len(rows) + 3)


def rates(rows):
    return (np.sum([r.goals for r in rows], axis=0) + 1) / (len(rows) + 1)


def poisson_vector(lam, maximum):
    out = np.empty(maximum+1)
    out[0] = math.exp(-lam)
    for k in range(1, maximum+1):
        out[k] = out[k-1]*lam/k
    return out


def factors(h, a, rho):
    return 1-h*a*rho, 1+h*rho, 1+a*rho, 1-rho


def joint(h, a, rho, support):
    matrix = np.outer(poisson_vector(h, support["max_goles"]), poisson_vector(a, support["max_goles"]))
    correction = factors(h, a, rho)
    if min(correction) <= 0:
        raise ValueError("Factor Dixon-Coles no positivo")
    matrix[:2,:2] *= np.asarray(correction).reshape(2, 2)
    mass = matrix.sum()
    if abs(1-mass) > support["cola_max"]:
        raise ValueError("Masa fuera del soporte")
    return matrix/mass


def outcome(matrix):
    return np.array([np.tril(matrix, -1).sum(), np.trace(matrix), np.triu(matrix, 1).sum()])


def markets(p, matrix=None):
    h, d, a = p
    result = {"p_1x": float(h+d), "p_12": float(h+a), "p_x2": float(d+a)}
    if matrix is None:
        return result
    total = np.add.outer(np.arange(len(matrix)), np.arange(len(matrix)))
    for line in range(5):
        under = float(matrix[total <= line].sum())
        result[f"p_under_{line}5"] = under
        result[f"p_over_{line}5"] = 1-under
    result["p_btts_si"] = float(matrix[1:,1:].sum())
    result["p_btts_no"] = 1-result["p_btts_si"]
    return result


def b3(prior, x, minimum):
    if min(int(x["l_w10_n"]), int(x["v_w10_n"])) < minimum:
        return prior, True
    d = (float(x["l_w10_ppg"])-float(x["v_w10_ppg"]))/3
    return softmax(np.log(prior) + np.array([d,0,-d])), False


def attack_fit(rows, cfg, cutoff, options, support):
    names = sorted({team for r in rows for team in r.teams})
    mapping = {team: i for i,team in enumerate(names)}
    n = len(names)
    h, a = np.asarray([[mapping[t] for t in r.teams] for r in rows]).T
    gh, ga = np.asarray([r.goals for r in rows]).T
    local = np.array([not r.neutral for r in rows], dtype=float)
    half = cfg["vida_media"]
    w = np.exp2(-(cutoff-np.asarray([r.day for r in rows]))/half) if half else np.ones(len(rows))
    low, high = np.log(support["rango_lambda"])

    def component(params):
        att, defense = params[2:2+n], params[2+n:]
        return att-att.mean(), defense-defense.mean()

    def predict_raw(params, hs, vs, nominal):
        att, defense = component(params)
        return (params[0]+params[1]*nominal+att[hs]+defense[vs],
                params[0]+att[vs]+defense[hs])

    def loss(params):
        e1,e2 = predict_raw(params, h, a, local)
        z1,z2 = np.clip(e1,low,high),np.clip(e2,low,high)
        lam1,lam2 = np.exp(z1),np.exp(z2)
        d1 = w*(lam1-gh)*((e1>low)&(e1<high))
        d2 = w*(lam2-ga)*((e2>low)&(e2<high))
        ag = np.bincount(h,d1,n)+np.bincount(a,d2,n)
        dg = np.bincount(a,d1,n)+np.bincount(h,d2,n)
        ridge = cfg["l2"]
        grad = np.r_[sum(d1+d2), np.dot(local,d1), ag-ag.mean(),dg-dg.mean()]
        grad[1:] += ridge*params[1:]
        return (np.dot(w,lam1+lam2-gh*z1-ga*z2)+ridge/2*np.dot(params[1:],params[1:]),grad)

    base = rates(rows)
    init = np.r_[math.log(base[1]),math.log(base[0]/base[1]),np.zeros(n*2)]
    result = minimize(loss, init, jac=True, method="L-BFGS-B", options=options)
    params = result.x
    att, defense = component(params)
    lam1,lam2 = [np.exp(np.clip(e,low,high)) for e in predict_raw(params,h,a,local)]
    residuals = ((gh-lam1)**2/lam1+(ga-lam2)**2/lam2)
    diagnostics = dict(convergio=bool(result.success), mensaje=str(result.message), iteraciones=int(result.nit),
                       equipos=n, ventaja_local_log=float(params[1]), intercepto=float(params[0]),
                       dispersion_pearson=float(residuals.sum()/max(1,2*len(rows)-2*n)),
                       residuo_local=float(np.mean(gh-lam1)),residuo_visitante=float(np.mean(ga-lam2)),
                       ataque={t:float(att[i]) for t,i in mapping.items()},
                       concesion={t:float(defense[i]) for t,i in mapping.items()},
                       suma_ataque=float(att.sum()),suma_concesion=float(defense.sum()))
    counts = dict(zip(names, np.bincount(np.r_[h,a], minlength=n)))

    def predict(row, minimum):
        effects = []
        for name in row.teams:
            i = mapping.get(name)
            effects.append((att[i],defense[i]) if counts.get(name,0)>=minimum else (0.,0.))
        (ah,dh),(aa,da) = effects
        logs = [params[0]+params[1]*(not row.neutral)+ah+da,params[0]+aa+dh]
        return np.exp(np.clip(logs,low,high))

    return predict, diagnostics, lam1, lam2, w, counts


def dixon_fit(rows, lam1, lam2, w, maximum):
    gh,ga = np.asarray([r.goals for r in rows]).T
    slope = np.select([(gh==0)&(ga==0),(gh==0)&(ga==1),(gh==1)&(ga==0),(gh==1)&(ga==1)],
                      [-lam1*lam2,lam1,lam2,-1.], default=0.)
    # Intervalo factible para todos los pares futuros con tasas acotadas.
    res = minimize_scalar(lambda rho: -np.dot(w,np.log1p(slope*rho)), bounds=(-0.999/maximum,0.999/maximum**2),
                          method="bounded", options={"xatol": 1e-8})
    return float(res.x) if res.success else 0., {"convergio": bool(res.success), "iteraciones":int(res.nfev),
                                                 "mensaje":str(res.message)}


def elo_signals(rows, settings):
    ratings, signals = {}, {}
    updates = iter(groupby(rows, key=lambda r:r.day))

    def key(row,t):
        return (row.comp,t) if settings["ambito"]=="competicion" else t

    def get(row,t):
        year=int(row.season[:4])
        value, last = ratings.get(key(row,t),(0.,year))
        return value*(1-settings["regresion"])**max(0,year-last)

    def gap(r):
        return get(r,r.teams[0])-get(r,r.teams[1])+settings["localia"]*(not r.neutral)

    waiting = next(updates,None)
    for day, group in groupby(rows, key=lambda r:r.day):
        while waiting is not None and waiting[0]<=day-2:
            changes = defaultdict(float)
            before = {}
            for r in waiting[1]:
                ra,rb = r.teams
                expected=1/(1+10**(-gap(r)/400))
                observed=(1.,.5,0.)[r.result]
                factor=math.log2(1+max(1,abs(r.goals[0]-r.goals[1]))) if settings["margen"] else 1.
                move=settings["K"]*factor*(observed-expected)
                for team, change in ((ra,move),(rb,-move)):
                    k = key(r,team)
                    changes[k] += change
                    before[k] = get(r,team),int(r.season[:4])
            for k,change in changes.items():
                prev,year=before[k]
                ratings[k]=prev+change,year
            waiting=next(updates,None)
        for r in group:
            signals[r.key]=gap(r)/400
    return signals


def fit_elo_map(rows, signals, options):
    d=np.asarray([signals[r.key] for r in rows])
    observed=np.eye(3)[[r.result for r in rows]]
    def loss(x):
        logits=np.column_stack((x[0]*d/2,np.full(len(d),x[1]),-x[0]*d/2))
        residual=softmax(logits,axis=1)-observed
        return (np.mean(logsumexp(logits,axis=1)-(logits*observed).sum(axis=1))+.001*np.dot(x,x),
                np.array([np.mean((residual[:,0]-residual[:,2])*d/2),residual[:,1].mean()])+.002*x)
    fit=minimize(loss,[2.,-.4],jac=True,method="L-BFGS-B",bounds=[(0,12),(-4,3)],options=options)
    a,b=fit.x
    return lambda d:softmax([a*d/2,b,-a*d/2]),dict(convergio=bool(fit.success), pendiente=float(a),
           intercepto_empate=float(b),iteraciones=int(fit.nit),mensaje=str(fit.message))


def fit_logistic(rows, fields, l2, options):
    numerical=[f for f in fields if f!="competicion"]
    cats=sorted({r.comp for r in rows})[1:] if "competicion" in fields else []
    def raw(rows):
        return np.array([[float(r.x[f]) if r.x[f] else np.nan for f in numerical] for r in rows])
    train=raw(rows)
    missing=np.isnan(train)
    med=np.array([np.median(col[np.isfinite(col)]) if np.isfinite(col).any() else 0 for col in train.T])
    imp=np.where(missing,med,train)
    center=imp.mean(axis=0)
    sd=imp.std(axis=0)
    sd[sd==0]=1
    used=missing.any(axis=0)
    def design(rows, x):
        bad=np.isnan(x)
        columns=(np.where(bad,med,x)-center)/sd
        cat=np.array([[r.comp==c for c in cats] for r in rows],dtype=float)
        return np.column_stack((np.ones(len(rows)),columns,bad[:,used],cat))
    z=design(rows,train)
    observed=np.eye(3)[[r.result for r in rows]]
    penalty=np.ones(z.shape[1])
    penalty[0]=0
    def loss(flat):
        beta=flat.reshape(-1,2)
        logits=np.c_[z@beta,np.zeros(len(z))]
        error=(softmax(logits,axis=1)-observed)[:,:2]
        return (np.mean(logsumexp(logits,axis=1)-(logits*observed).sum(axis=1))+l2/2*np.sum(penalty[:,None]*beta**2),
                (z.T@error/len(z)+l2*penalty[:,None]*beta).ravel())
    res=minimize(loss,np.zeros(z.shape[1]*2),method="L-BFGS-B",jac=True,options=options)
    beta=res.x.reshape(-1,2)
    return (lambda subset: softmax(np.c_[design(subset,raw(subset))@beta,np.zeros(len(subset))],axis=1),
            dict(convergio=bool(res.success), iteraciones=int(res.nit), mensaje=str(res.message),
                 coeficientes=beta.tolist(), columnas=["intercepto",*numerical,
                 *[f+"_falta" for f,v in zip(numerical,used) if v],*cats], mediana=med.tolist(), media=center.tolist(),
                 escala=sd.tolist(), condicion_diseno=float(np.linalg.cond(z))))
