"""Estimadores tabulares, híbridos y mezclas de la fase experimental."""
from collections import defaultdict
from dataclasses import dataclass
from itertools import groupby
import time

import lightgbm as lgb
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import softmax
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import xgboost as xgb

from experimento_f4 import phase, EVAL, EPS, day
from modelos_f4 import joint


def blocks(rows, config):
    def block(r):
        stage = phase(r)
        anchor = EVAL if stage == "evaluacion" else day(f"{r.season[:4]}-07-01")
        return stage, r.season, (r.day - anchor) // config["dias_bloque"]

    days = np.asarray([r.day for r in rows])
    if (np.diff(days) < 0).any():
        raise ValueError("Fechas de desarrollo fuera de orden")
    for (stage, year, index), ids in groupby(range(len(rows)), key=lambda i: block(rows[i])):
        target = np.fromiter(ids, dtype=int)
        if stage != "arranque":
            bound = days[target[0]] - config["dias_corte"]
            yield stage, f"{year}/{stage}/{index}", int(bound), np.flatnonzero(days <= bound), target


def early_split(ids, days, cfg):
    last = int(days[ids[-1]])
    pivot = last - cfg["dias_validacion"] + 1
    train = ids[days[ids] <= pivot-2]
    valid = ids[days[ids] >= pivot]
    if len(train) < cfg["min_entrenamiento"] or len(valid) < cfg["min_validacion"]:
        return None
    return train, valid


def causal_elo(rows, config):
    """Emite los dos ratings previos en lotes, usando solo goles/etiquetas elegibles."""
    ratings = defaultdict(float)
    dates = [(d, list(g)) for d, g in groupby(rows, key=lambda r: r.day)]
    pos = 0
    state = {}
    for day_target, targets in dates:
        while dates[pos][0] <= day_target - 2:
            delta = defaultdict(float)
            for r in dates[pos][1]:
                h, a = ((r.comp, name) for name in r.teams)
                gap = ratings[h] - ratings[a] + config["localia"] * (not r.neutral)
                expectation = 1 / (1 + 10**(-gap/400))
                change = config["K"] * ((1., .5, 0.)[r.result] - expectation)
                delta[h] += change
                delta[a] -= change
            for key, change in delta.items():
                ratings[key] += change
            pos += 1
        for r in targets:
            h, a = (ratings[r.comp, t] + 1500 for t in r.teams)
            d = (h - a + config["localia"] * (not r.neutral)) / 400
            state[r.key] = h, a, d
    return state


def probability(p):
    p = np.asarray(p, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or not np.isfinite(p).all():
        raise ValueError("Matriz 1X2 fuera del contrato")
    if (p < 0).any() or not np.allclose(p.sum(axis=1), 1, atol=1e-6, rtol=0):
        raise ValueError("Probabilidades 1X2 inválidas")
    # Evita infinitos en métricas, offsets logarítmicos y calibración posteriores.
    clipped = np.maximum(EPS, p)
    return clipped / clipped.sum(axis=1, keepdims=True)


def features(config, groups):
    raw = [f for group in groups for f in config["grupos"][group]]
    return [x.replace("{lado}", side) for x in raw for side in ("l", "v") if "{lado}" in x] + [
        x for x in raw if "{lado}" not in x]


class Encoder:
    """Categorías e imputación determinadas exclusivamente por las filas de ajuste."""
    categorical = {"competicion", "l_racha_tipo", "v_racha_tipo"}

    def fit(self, values, columns, ids):
        self.columns = tuple(columns)
        self.fill = {}
        self.levels = {}
        self.names = []
        for name in self.columns:
            selected = values[name][ids]
            if name in self.categorical:
                levels = sorted({v for v in selected if v})
                self.levels[name] = levels
                self.names.extend(f"{name}={v}" for v in levels)
                self.names.append(name + "=sin_categoria")
            else:
                finite = np.isfinite(selected)
                self.fill[name] = float(np.median(selected[finite])) if finite.any() else 0.
                self.names.extend((name, name + "=faltante"))
        return self

    def transform(self, values, ids):
        result = []
        for name in self.columns:
            x = values[name][ids]
            if name in self.categorical:
                levels = self.levels[name]
                result.extend(x == lvl for lvl in levels)
                result.append(~np.isin(x, levels))
            else:
                ok = np.isfinite(x)
                result.extend((np.where(ok, x, self.fill[name]), ~ok))
        return np.column_stack(result).astype(np.float32)


@dataclass
class Pipeline:
    encoder: Encoder
    model: object
    regression: bool
    offset: bool

    def predict(self, values, ids, margin=None):
        x = self.encoder.transform(values, ids)
        lgb_booster = getattr(self.model, "booster_", None)
        if self.regression:
            output = (lgb_booster.predict(x, num_threads=1) if lgb_booster is not None else
                      self.model.predict(x, base_margin=margin) if self.offset else self.model.predict(x))
            if not np.isfinite(output).all() or (output <= 0).any():
                raise ValueError("El estimador Poisson emitió una tasa inválida")
            return output
        if tuple(self.model.classes_) != (0, 1, 2):
            raise ValueError("Orden de clases inválido")
        return probability(lgb_booster.predict(x, num_threads=1) if lgb_booster is not None else self.model.predict_proba(x))


def train(values, columns, y, ids, days, config, candidate, regression=False, offsets=None):
    started = time.perf_counter()
    name = candidate["familia"]
    params = dict(candidate["params"], n_jobs=config["hilos"], random_state=config["semilla"])
    offset = offsets is not None
    split = early_split(ids, days, config["early_stopping"]) if name == "xgb" and not regression else None
    best_iteration = None
    if name == "xgb":
        builder = xgb.XGBRegressor if regression else xgb.XGBClassifier
        params.update(objective="count:poisson" if regression else "multi:softprob", tree_method="hist")
        if split is not None:
            a, b = split
            local = Encoder().fit(values, columns, a)
            early = builder(**params, eval_metric="mlogloss",
                            early_stopping_rounds=config["early_stopping"]["alto"])
            early.fit(local.transform(values, a), y[a], eval_set=[(local.transform(values, b), y[b])], verbose=False)
            best_iteration = int(early.best_iteration) + 1
            params["n_estimators"] = best_iteration
    elif name == "lgb":
        builder = lgb.LGBMRegressor if regression else lgb.LGBMClassifier
        params.update(objective="poisson" if regression else "multiclass", verbosity=-1,
                      subsample_freq=1, force_col_wise=True)
    else:
        builder = {"rf": RandomForestClassifier, "et": ExtraTreesClassifier}[name]
    encoder = Encoder().fit(values, columns, ids)
    model = builder(**params)
    model.fit(encoder.transform(values, ids), y[ids], **({"base_margin": offsets[ids]} if offset else {}))
    history = dict(n=len(ids), segundos_ajuste=time.perf_counter()-started, arboles=params["n_estimators"],
                   ajustes=1+int(split is not None), early_iter=best_iteration,
                   early_train_max=int(days[split[0][-1]]) if split else None,
                   early_valid_min=int(days[split[1][0]]) if split else None,
                   early_valid_max=int(days[split[1][-1]]) if split else None)
    return Pipeline(encoder, model, regression, offset), history


def from_components(components, support):
    matrix = np.zeros((support["max_goles"] + 1,) * 2)
    if not components or abs(sum(c[3] for c in components) - 1) > 1e-10:
        raise ValueError("Los pesos de marcadores no suman uno")
    for h, a, rho, weight in components:
        if not np.isfinite([h, a, rho, weight]).all() or min(h, a) <= 0 or weight < 0:
            raise ValueError("Componente de marcador incompatible")
        matrix += weight * joint(h, a, rho, support)
    if abs(matrix.sum() - 1) > 1e-10 or (matrix < 0).any():
        raise ValueError("Distribución de marcadores incompatible")
    return matrix


def past_oof(store, ids, names, days, cutoff):
    return np.asarray([i for i in ids if days[i] <= cutoff and all(i in store[m] for m in names)], dtype=int)


def stacking_input(cube):
    return (np.log(cube[:, :, :2]) - np.log(cube[:, :, 2:])).reshape(len(cube), -1)


def ensemble_fit(cube, labels, seed):
    n = cube.shape[1]
    observed = cube[np.arange(len(cube)), :, labels]
    fit = minimize(lambda w: -np.log(np.maximum(EPS, observed @ w)).mean(), np.ones(n)/n,
                   bounds=[(0., 1.)] * n, constraints={"type": "eq", "fun": lambda w: w.sum()-1},
                   method="SLSQP", options={"ftol": 1e-10})
    weights = np.clip(fit.x, 0, 1) if fit.success else np.ones(n)
    meta = LogisticRegression(C=.15, random_state=seed).fit(stacking_input(cube), labels)
    if tuple(meta.classes_) != (0, 1, 2):
        raise ValueError("Clases del metaestimador inválidas")
    return weights / weights.sum(), meta, bool(fit.success)


def log_loss(p, y):
    return float(-np.log(np.maximum(EPS, p[np.arange(len(y)), y])).mean())


def calibrator(kind, p, labels, config):
    if kind == "temperatura":
        loss = lambda t: log_loss(softmax(np.log(p) / t, axis=1), labels)
        fit = minimize_scalar(loss, bounds=config["temperatura"], method="bounded")
        if not fit.success:
            raise ValueError("No convergió la calibración escalar")
        return float(fit.x)
    return LogisticRegression(C=config["regularizacion_logistica_C"]).fit(np.log(p), labels)


def calibrate(kind, fitted, p):
    if kind == "bruta":
        return p
    if kind == "temperatura":
        return probability(softmax(np.log(p) / fitted, axis=1))
    return probability(fitted.predict_proba(np.log(p)))


def calibrator_choice(p, labels, days, bound, config):
    if len(days) == 0:
        return "bruta", None, {}, 0
    pivot = int(days[-1]) - config["dias_validacion"] + 1
    before = days <= min(bound, pivot - 2)
    after = (days >= pivot) & (days <= bound)
    available = days <= bound
    if min(np.bincount(labels[before], minlength=3)) < config["min_por_clase"] or not after.any():
        return "bruta", None, {}, int(available.sum())
    scores = {"bruta": log_loss(p[after], labels[after])}
    for kind in ("temperatura", "logistica"):
        fit = calibrator(kind, p[before], labels[before], config)
        scores[kind] = log_loss(calibrate(kind, fit, p[after]), labels[after])
    best = min(scores, key=scores.get)
    if scores["bruta"] - scores[best] < config["mejora_minima"]:
        best = "bruta"
    return best, (None if best == "bruta" else calibrator(best, p[available], labels[available], config)), scores, int(available.sum())
