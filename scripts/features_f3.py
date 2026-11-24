"""Construye variables experimentales D−2 a partir de partidos de desarrollo."""

from bisect import bisect_right
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import csv
import json
import math
import re
import sqlite3

from f2_revision import CANON, ROOT

DB = CANON / "openfootball_v3.sqlite"
OUT = ROOT / "data/processed/f3_base_v1"
HASH = "c195a52cfdff831c1c847e50e30b031c541adec03f4ee6273183033369819d19"
SEASONS = ("2021-22", "2022-23", "2023-24", "2024-25")
WINDOWS = (5, 10, 20)
LINES = (0, 1, 2, 3, 4)


@dataclass(frozen=True)
class Match:
    key: int
    comp: str
    season: str
    day: int
    home: str
    away: str
    hg: int
    ag: int
    neutral: int | None = None
    phase: str | None = None
    source_time: str | None = None
    raw_id: int | None = None
    source_row: int | None = None
    available_at: str | None = None


def verify_base():
    checksum = file_hash(DB)
    if checksum != HASH:
        raise ValueError("El hash de la base difiere del snapshot autorizado")
    return checksum


def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()


def load_matches():
    with closing(sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True)) as db:
        rows = db.execute("""
          SELECT r.id,r.competition,r.season,r.match_date,r.canonical_home,r.canonical_away,
                 r.home90,r.away90,r.neutral,m.phase,m.source_time,r.raw_id,r.source_row,r.available_at
          FROM audited_results r JOIN match_revisions m
            ON m.match_id=r.id AND m.raw_id=r.raw_id AND m.source_row=r.source_row
          WHERE r.partition='desarrollo' AND r.season IN (?,?,?,?)
            AND r.home90 IS NOT NULL AND r.away90 IS NOT NULL AND r.match_date<='2025-06-01'
          ORDER BY r.match_date,r.id
          """, SEASONS).fetchall()
    matches = [Match(*row[:3], date.fromisoformat(row[3]).toordinal(), *row[4:]) for row in rows]
    if len(matches) != 7720 or len({m.key for m in matches}) != 7720:
        raise ValueError("El universo difiere de los 7.720 partidos autorizados")
    if any(m.home == m.away or min(m.hg, m.ag) < 0 for m in matches):
        raise ValueError("Registro inválido en v3")
    return matches


@dataclass(frozen=True)
class Appearance:
    match: Match
    opponent: str
    gf: int
    ga: int
    side: str

    @property
    def points(self):
        return 3 if self.gf > self.ga else int(self.gf == self.ga)


class Timeline:
    def __init__(self, rows, day):
        self.rows = rows
        self.days = [day(row) for row in rows]

    def through(self, cutoff):
        return self.rows[:bisect_right(self.days, cutoff)]


def recent(rows, n):
    start = max(0, len(rows) - n)
    # No ordenar artificialmente dentro del día que delimita la ventana.
    while start and rows[start - 1].match.day == rows[start].match.day:
        start -= 1
    return rows[start:]


def mean(values):
    return sum(values) / len(values) if values else None


def summary(rows, prefix, full=False):
    n = len(rows)
    out = {prefix + "_n": n}
    metrics = {
        "gf": [r.gf for r in rows], "ga": [r.ga for r in rows], "ppg": [r.points for r in rows],
    }
    if full:
        metrics.update(dg=[r.gf-r.ga for r in rows], win=[r.points == 3 for r in rows],
                       draw=[r.points == 1 for r in rows], loss=[r.points == 0 for r in rows],
                       cs=[r.ga == 0 for r in rows], btts=[min(r.gf, r.ga) > 0 for r in rows])
        for line in LINES:
            metrics[f"over{line}5"] = [r.gf+r.ga > line for r in rows]
            metrics[f"under{line}5"] = [r.gf+r.ga <= line for r in rows]
    out.update({f"{prefix}_{k}": mean(v) for k, v in metrics.items()})
    return out


def streak(rows):
    if not rows:
        return None, None
    kind = rows[-1].points
    size = 0
    i = len(rows)
    while i:
        j = i - 1
        while j and rows[j - 1].match.day == rows[i - 1].match.day:
            j -= 1
        states = {r.points for r in rows[j:i]}
        if size == 0 and len(states) > 1:
            return None, None
        if states != {kind}:
            break
        size += i - j
        i = j
    return {0: "derrota", 1: "empate", 3: "victoria"}[kind], size


def ratio(x, y):
    return x / y if x is not None and y else None


def delta(x, y):
    return x - y if x is not None and y is not None else None


def feature_rows(matches):
    matches = sorted(matches, key=lambda m: (m.day, m.key))
    teams, leagues = defaultdict(list), defaultdict(list)
    for m in matches:
        teams[m.home].append(Appearance(m, m.away, m.hg, m.ag, "home"))
        teams[m.away].append(Appearance(m, m.home, m.ag, m.hg, "away"))
        leagues[m.comp, m.season].append(m)
    teams = {k: Timeline(rows, lambda r: r.match.day) for k, rows in teams.items()}
    leagues = {k: Timeline(rows, lambda r: r.day) for k, rows in leagues.items()}

    def team_history(name, cutoff):
        return teams[name].through(cutoff)

    # Fortaleza de cada adversario antes de su partido histórico, nunca su posición final.
    prior_ppg = {}
    for m in matches:
        for team in (m.home, m.away):
            form = recent(team_history(team, m.day - 2), 10)
            prior_ppg[m.key, team] = mean([r.points for r in form]) if len(form) >= 5 else None

    for m in matches:
        cutoff = m.day - 2
        competition = leagues[m.comp, m.season].through(cutoff)
        league_avg = mean([(r.hg+r.ag)/2 for r in competition])
        phase_matchday = re.search(r"\bMatchday\s+(\d+)\b", m.phase or "", re.I)
        row = {
            "match_id": m.key, "fecha_objetivo": date.fromordinal(m.day).isoformat(),
            "corte_d2": date.fromordinal(cutoff).isoformat(), "available_at": None,
            "competicion": m.comp, "temporada": m.season, "fase_fuente": m.phase,
            "jornada_fuente": int(phase_matchday.group(1)) if phase_matchday else None,
            "local_id": m.home, "visitante_id": m.away,
            "sede_objetivo": "neutral" if m.neutral == 1 else "no_neutral" if m.neutral == 0 else "desconocida",
            "comp_temporada_n": len(competition), "comp_goles_por_equipo": league_avg,
        }
        for side, team, opponent in (("l", m.home, m.away), ("v", m.away, m.home)):
            history = team_history(team, cutoff)
            assert all(r.match.day <= cutoff and r.match.key != m.key for r in history)
            row.update(summary(history, side+"_general"))
            for n in WINDOWS:
                form = recent(history, n)
                row.update(summary(form, f"{side}_w{n}", full=True))
                row[f"{side}_w{n}_completa"] = int(len(form) >= n)
            for venue in ("home", "away"):
                sample = [r for r in history if r.side == venue and r.match.neutral != 1]
                stem = f"{side}_rol_{venue}"
                row.update(summary(sample, stem))
                row[stem+"_sede_desconocida_n"] = sum(r.match.neutral is None for r in sample)
                for k in ("gf", "ga", "ppg"):
                    row[stem+"_vs_general_"+k] = delta(row[stem+"_"+k], row[side+"_general_"+k])
            row[f"{side}_neutral_n"] = sum(r.match.neutral == 1 for r in history)
            own = [r for r in history if (r.match.comp, r.match.season) == (m.comp, m.season)]
            row.update(summary(own, side+"_comp_temporada"))
            row[side+"_ataque_rel"] = ratio(row[side+"_comp_temporada_gf"], league_avg)
            row[side+"_concesion_rel"] = ratio(row[side+"_comp_temporada_ga"], league_avg)
            row[side+"_sin_historia"] = int(not history)
            row[side+"_sin_historia_comp"] = int(not any(r.match.comp == m.comp for r in history))
            row[side+"_sin_partidos_edicion_comp"] = int(not own)
            run_type, run_length = streak(history)
            row[side+"_racha_tipo"], row[side+"_racha_n"] = run_type, run_length
            form = recent(history, 20)
            weights = [math.exp2(-(m.day-r.match.day)/30) for r in form]
            for key, values in (("gf", [r.gf for r in form]), ("ga", [r.ga for r in form]),
                                ("ppg", [r.points for r in form])):
                row[side+"_ponderada_"+key] = sum(w*x for w, x in zip(weights, values))/sum(weights) if weights else None
            opponents = [(r, prior_ppg[r.match.key, r.opponent]) for r in recent(history, 10)]
            observed = [(r, strength) for r, strength in opponents if strength is not None]
            row[side+"_rival_ppg_n"] = len(observed)
            row[side+"_rival_ppg_previo"] = mean([s for _, s in observed])
            # El peso aumenta con la forma histórica del rival. Normalizar para no cambiar unidades.
            row[side+"_ppg_ponderado_rival"] = (sum((1+s/3)*r.points for r, s in observed) /
                                               sum(1+s/3 for _, s in observed)) if observed else None
            h2h = recent([r for r in history if r.opponent == opponent and m.day-r.match.day <= 730], 20)
            row.update(summary(h2h, side+"_h2h", full=True))
            row[side+"_h2h_ultimo_dias"] = m.day-h2h[-1].match.day if h2h else None
            row[side+"_dias_ultimo_registrado"] = m.day-history[-1].match.day if history else None
            row[side+"_fecha_ultima_historia"] = date.fromordinal(history[-1].match.day).isoformat() if history else None
            for days in (7, 14, 30):
                in_window = [r for r in history if m.day-days <= r.match.day]
                row[f"{side}_partidos_reg_{days}d"] = len(in_window)
                row[f"{side}_comp_reg_{days}d"] = len({r.match.comp for r in in_window})
        for field in ("w5_ppg", "w10_ppg", "w20_ppg", "w10_gf", "w10_ga", "w10_dg",
                      "ponderada_ppg", "oponente_ppg", "ataque_rel", "concesion_rel", "dias_ultimo_registrado",
                      "ppg_ponderado_rival", "partidos_reg_14d", "h2h_ppg"):
            actual = "rival_ppg_previo" if field == "oponente_ppg" else field
            row["delta_"+actual] = delta(row["l_"+actual], row["v_"+actual])
        yield row


def label(m):
    return {"match_id": m.key, "goles_local90": m.hg, "goles_visitante90": m.ag,
            "resultado_1x2": "1" if m.hg > m.ag else "2" if m.ag > m.hg else "X",
            "raw_id": m.raw_id, "source_row": m.source_row}


def write_csv(path, rows):
    rows = iter(rows)
    first = next(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, first)
        writer.writeheader()
        writer.writerow(first)
        writer.writerows(rows)


if __name__ == "__main__":
    before = verify_base()
    matches = load_matches()
    features = list(feature_rows(matches))
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT/"X.csv", features)
    write_csv(OUT/"y.csv", map(label, matches))
    after = verify_base()
    (OUT/"SNAPSHOT_FEATURES.json").write_text(json.dumps({
        "version": OUT.name, "perfil": "D-2", "filas": len(matches),
        "base_antes": before, "base_despues": after,
        "codigo": file_hash(ROOT/"scripts/features_f3.py"),
        "X": file_hash(OUT/"X.csv"), "y": file_hash(OUT/"y.csv"),
    }, indent=2)+"\n", encoding="utf-8")
