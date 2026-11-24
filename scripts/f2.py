"""Ingesta piloto reproducible, con biblioteca estándar de Python."""

import argparse
from collections import Counter
from datetime import UTC, date, datetime
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
FILES = dict(PL="en.1.json", PD="es.1.json", BL1="de.1.json",
             SA="it.1.json", FL1="fr.1.json", CL="cl.txt")
SEASONS = [f"{year}-{(year + 1) % 100:02d}" for year in range(2021, 2027)]
PREFIX = "https://raw.githubusercontent.com/openfootball/"
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS raw_objects(
 id INTEGER PRIMARY KEY, url TEXT NOT NULL, sha256 TEXT NOT NULL,
 path TEXT NOT NULL, ingested_at TEXT NOT NULL, license TEXT NOT NULL,
 UNIQUE(url,sha256));
CREATE TABLE IF NOT EXISTS teams(
 id INTEGER PRIMARY KEY, namespace TEXT NOT NULL, source_name TEXT NOT NULL,
 UNIQUE(namespace,source_name));
CREATE TABLE IF NOT EXISTS seasons(
 competition TEXT, season TEXT, in_progress INTEGER NOT NULL,
 PRIMARY KEY(competition,season));
CREATE TABLE IF NOT EXISTS matches(
 id INTEGER PRIMARY KEY, competition TEXT NOT NULL, season TEXT NOT NULL,
 home INTEGER NOT NULL REFERENCES teams(id), away INTEGER NOT NULL REFERENCES teams(id),
 stage_key TEXT NOT NULL, CHECK(home<>away), UNIQUE(competition,season,home,away,stage_key),
 FOREIGN KEY(competition,season) REFERENCES seasons(competition,season));
CREATE TABLE IF NOT EXISTS match_revisions(
 match_id INTEGER REFERENCES matches(id), raw_id INTEGER REFERENCES raw_objects(id),
 source_row INTEGER, match_date TEXT NOT NULL, source_time TEXT, phase TEXT,
 home90 INTEGER CHECK(home90>=0), away90 INTEGER CHECK(away90>=0),
 available_at TEXT, PRIMARY KEY(raw_id,source_row),
 CHECK((home90 IS NULL)=(away90 IS NULL)));
CREATE TABLE IF NOT EXISTS findings(
 raw_id INTEGER REFERENCES raw_objects(id), source_row INTEGER, reason TEXT,
 PRIMARY KEY(raw_id,source_row,reason));
"""


def source(code, season):
    repo = "champions-league" if code == "CL" else "football.json"
    return f"{PREFIX}{repo}/master/{season}/{FILES[code]}"


def read_rows(data, code, season):
    if code != "CL":
        for i, row in enumerate(json.loads(data)["matches"], 1):
            score = row.get("score")
            if isinstance(score, dict):
                score = score.get("ft")
            yield i, (row.get("date"), row.get("time"), row.get("round"),
                      row.get("team1"), row.get("team2"), score)
        return
    day = phase = None
    for i, line in enumerate(data.decode("utf-8-sig").splitlines(), 1):
        line = line.strip()
        if line.startswith("▪"):
            phase = line[1:].strip()
        header = re.fullmatch(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) ([A-Z][a-z]{2}) (\d{1,2})(?: (\d{4}))?", line)
        if header:
            month, num, year = header.groups()
            year = year or str(int(season[:4]) + (month in "Jan Feb Mar Apr May Jun Jul".split()))
            day = datetime.strptime(f"{month} {num} {year}", "%b %d %Y").date().isoformat()
        if " v " not in line:
            continue
        match = re.fullmatch(r"(?:(\d\d:\d\d)\s+)?(.+?)\s+v\s+(.+?)\s+(\d+)-(\d+)(?:\s+\(\d+-\d+\))?", line)
        if not match:
            match = re.fullmatch(r"(?:(\d\d:\d\d)\s+)?(.+?)\s+v\s+(.+?)\s+(?:\d+-\d+ pen\. )?\d+-\d+ a\.e\.t\. \((\d+)-(\d+), \d+-\d+\)", line)
        if match:
            time, home, away, h, a = match.groups()
            yield i, (day, time, phase, home, away, [int(h), int(a)])
        else:
            yield i, None


def ingest(db, code, season, data, limit):
    url = source(code, season)
    sha = hashlib.sha256(data).hexdigest()
    path = ROOT / "data/raw" / (sha + Path(FILES[code]).suffix)
    path.write_bytes(data)
    rows = list(read_rows(data, code, season))
    rows = rows[:limit] if limit else rows
    counts = Counter(leidas=len(rows))
    seen = set()
    with db:
        db.execute("INSERT OR IGNORE INTO raw_objects VALUES(NULL,?,?,?,?,?)",
                   (url, sha, str(path.relative_to(ROOT)), datetime.now(UTC).isoformat(), "CC0-1.0"))
        raw_id = db.execute("SELECT id FROM raw_objects WHERE url=? AND sha256=?", (url, sha)).fetchone()[0]
        db.execute("INSERT OR IGNORE INTO seasons VALUES(?,?,?)", (code, season, int(season == SEASONS[-1])))
        for i, row in rows:
            try:
                if row is None:
                    raise ValueError("formato de Champions o liquidación no resueltos")
                day, time, phase, home, away, score = row
                date.fromisoformat(day)
                if time:
                    datetime.strptime(time, "%H:%M")
                if not all(isinstance(n, str) and n.strip() for n in (home, away)) or home.strip() == away.strip():
                    raise ValueError("identidad inválida")
                if score is not None and (not isinstance(score, list) or len(score) != 2
                                          or any(type(n) is not int or n < 0 for n in score)):
                    raise ValueError("marcador inválido")
                pair = (home.strip(), away.strip())
                stage_key = (phase or "") if code == "CL" else ""
                identity = (*pair, stage_key)
                if identity in seen:
                    counts["duplicadas_o_conflictivas"] += 1
                    raise ValueError("pareja repetida en la edición")
                seen.add(identity)
            except (ValueError, TypeError) as exc:
                counts["cuarentena"] += 1
                db.execute("INSERT OR IGNORE INTO findings VALUES(?,?,?)", (raw_id, i, str(exc)))
                continue
            ids = []
            for name in pair:
                db.execute("INSERT OR IGNORE INTO teams VALUES(NULL,?,?)", (code, name))
                ids.append(db.execute("SELECT id FROM teams WHERE namespace=? AND source_name=?", (code, name)).fetchone()[0])
            key = (code, season, *ids, stage_key)
            db.execute("INSERT OR IGNORE INTO matches VALUES(NULL,?,?,?,?,?)", key)
            match_id = db.execute("SELECT id FROM matches WHERE competition=? AND season=? AND home=? AND away=? AND stage_key=?", key).fetchone()[0]
            db.execute("INSERT OR IGNORE INTO match_revisions VALUES(?,?,?,?,?,?,?,?,NULL)",
                       (match_id, raw_id, i, day, time or None, phase, *(score or [None, None])))
            counts["aceptadas"] += 1
            counts["sin_hora"] += not bool(time)
            counts["sin_marcador"] += score is None
            counts["sin_disponibilidad_historica"] += 1
    return {"sha256": sha, **counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ampliar", action="store_true", help="Consultar las 36 combinaciones autorizadas.")
    parser.add_argument("--reprocesar", action="store_true", help="Releer los objetos del inventario ampliado sin red.")
    options = parser.parse_args()
    folder = ROOT / "data/canonical"
    folder.mkdir(exist_ok=True)
    report = []
    expanded = options.ampliar or options.reprocesar
    prior = ROOT / "data/processed/cobertura.json"
    cached = {(r["competicion"], r["temporada"]): r for r in json.loads(prior.read_text(encoding="utf-8"))} if options.reprocesar else {}
    with sqlite3.connect(folder / "openfootball_refresh.sqlite") as db:
        db.executescript(SCHEMA)
        for season in SEASONS if expanded else SEASONS[:1]:
            for code in FILES if expanded else ("PL", "CL"):
                result = dict(fuente="OpenFootball", competicion=code, temporada=season,
                              en_curso=season == SEASONS[-1], url=source(code, season))
                try:
                    if options.reprocesar:
                        previous = cached[code, season]
                        if "sha256" not in previous:
                            report.append(previous)
                            continue
                        data = (ROOT / "data/raw" / (previous["sha256"] + Path(FILES[code]).suffix)).read_bytes()
                        if hashlib.sha256(data).hexdigest() != previous["sha256"]:
                            raise ValueError("hash de objeto local distinto del inventario")
                    elif options.ampliar:
                        with urlopen(result["url"], timeout=15) as response:
                            data = response.read()
                    else:
                        data = (ROOT / "data/raw" / ("pilot-en.json" if code == "PL" else "pilot-cl.txt")).read_bytes()
                    result.update(ingest(db, code, season, data, None if expanded else 12))
                    result["estado"] = "procesado"
                except (HTTPError, URLError, OSError, ValueError, KeyError) as exc:
                    result.update(estado="no_procesado", motivo=str(exc))
                report.append(result)
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Referencias huérfanas")
    name = "cobertura_refresh" if expanded else "muestra_refresh"
    (ROOT / "data/processed" / f"{name}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{name}: {sum(r['estado'] == 'procesado' for r in report)}/{len(report)} archivos procesados")


if __name__ == "__main__":
    main()
