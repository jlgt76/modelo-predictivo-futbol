"""Publica una revisión local de F2 sin alterar el snapshot anterior."""

from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "data/canonical"
PD = "https://www.laliga.com/es-US/laliga-easports/resultados/2024-25/jornada-38"
SA = "https://openfootball.github.io/italy/2024-25_1-seriea.html"
NANTES = "https://www.fcnantes.com/articles/article2809.php?num=49229"
COUNTRIES = dict(PL="ENG", PD="ESP", BL1="GER", SA="ITA", FL1="FRA")
VARIANTS = {
    "AS Monaco": "AS Monaco FC",
    "Atlético Madrid": "Club Atlético de Madrid",
    "Atalanta": "Atalanta BC",
    "Bayer Leverkusen": "Bayer 04 Leverkusen",
    "Bayern München": "FC Bayern München",
    "Dinamo Zagreb": "GNK Dinamo Zagreb",
    "ES Troyes AC": "ESTAC Troyes",
    "Inter": "FC Internazionale Milano",
    "Juventus": "Juventus FC",
    "Manchester City": "Manchester City FC",
    "Manchester United": "Manchester United FC",
    "Olympique Marseille": "Olympique de Marseille",
    "Paris Saint-Germain": "Paris Saint-Germain FC",
    "RB Salzburg": "FC Red Bull Salzburg",
    "RC Lens": "Racing Club de Lens",
    "RC Strasbourg": "RC Strasbourg Alsace",
    "Real Madrid": "Real Madrid CF",
    "Shakhtar Donetsk": "FK Shakhtar Donetsk",
    "SL Benfica": "Sport Lisboa e Benfica",
    "Sporting CP": "Sporting Clube de Portugal",
    "Stade Rennais": "Stade Rennais FC 1901",
    "Tottenham Hotspur": "Tottenham Hotspur FC",
}
CORRECTIONS = {
    "PD": {
        "Real Betis Balompié": (1, 1), "Real Madrid CF": (2, 0),
        "CD Leganés": (3, 0), "RCD Espanyol de Barcelona": (2, 0),
        "Deportivo Alavés": (1, 1), "Getafe CF": (1, 2),
        "Rayo Vallecano de Madrid": (0, 0), "Girona FC": (0, 4),
        "Villarreal CF": (4, 2), "Athletic Club": (0, 3),
    },
    "SA": {
        "Como 1907": (0, 2), "SSC Napoli": (2, 0), "Bologna FC 1909": (1, 3),
        "AC Milan": (2, 0), "Atalanta BC": (2, 3), "Empoli FC": (1, 2),
        "SS Lazio": (0, 1), "Torino FC": (0, 2), "Udinese Calcio": (2, 3),
        "Venezia FC": (2, 3),
    },
}


def club(namespace, original):
    tag = re.fullmatch(r"(.+) \(([A-Z]{3})\)", original) if namespace == "CL" else None
    name, country = tag.groups() if tag else (original, COUNTRIES.get(namespace, namespace))
    if name in ("AS Monaco", "AS Monaco FC") and country == "FRA":
        country = "MCO"
    canonical = VARIANTS.get(name, name)
    method = "equivalencia_curada" if canonical != name or country == "MCO" else "nombre_exacto_y_pais"
    return country, canonical, method


def main():
    old = CANON / "openfootball_v2.sqlite"
    out = CANON / "openfootball_v3.sqlite"
    if out.exists():
        raise SystemExit("La revisión v3 ya existe. Se conserva sin sobrescribir.")
    stamp = datetime.now(UTC).isoformat()
    with sqlite3.connect(old.as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(out) as db:
        src.backup(db)
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript("""
        CREATE TABLE canonical_teams(
            id TEXT PRIMARY KEY, country TEXT NOT NULL, name TEXT NOT NULL, UNIQUE(country,name));
        CREATE TABLE team_aliases(
            source_team_id INTEGER PRIMARY KEY REFERENCES teams(id),
            canonical_team_id TEXT NOT NULL REFERENCES canonical_teams(id),
            method TEXT NOT NULL, evidence TEXT NOT NULL, reviewed_at TEXT NOT NULL);
        CREATE TABLE result_corrections(
            match_id INTEGER PRIMARY KEY REFERENCES matches(id), home90 INTEGER, away90 INTEGER,
            administrative_home INTEGER, administrative_away INTEGER,
            status TEXT NOT NULL, evidence TEXT NOT NULL, observed_at TEXT NOT NULL);
        CREATE TABLE venue_evidence(
            match_id INTEGER PRIMARY KEY REFERENCES matches(id), neutral INTEGER NOT NULL,
            evidence TEXT NOT NULL);
        CREATE VIEW canonical_matches AS
        SELECT m.*, h.canonical_team_id AS canonical_home, a.canonical_team_id AS canonical_away,
               v.neutral, CASE WHEN season='2025-26' THEN 'reserva_final'
                   WHEN season='2026-27' THEN 'en_curso' ELSE 'desarrollo' END AS partition
        FROM matches m JOIN team_aliases h ON h.source_team_id=m.home
        JOIN team_aliases a ON a.source_team_id=m.away
        LEFT JOIN venue_evidence v ON v.match_id=m.id;
        CREATE VIEW audited_results AS
        SELECT m.id, m.competition, m.season, m.partition, m.neutral,
               m.canonical_home, m.canonical_away, r.match_date, r.available_at,
               CASE WHEN c.status='abandonado_adjudicado' THEN NULL ELSE coalesce(c.home90,r.home90) END AS home90,
               CASE WHEN c.status='abandonado_adjudicado' THEN NULL ELSE coalesce(c.away90,r.away90) END AS away90,
               c.status AS correction_status, c.evidence, r.raw_id, r.source_row
        FROM canonical_matches m JOIN match_revisions r ON r.match_id=m.id
        LEFT JOIN result_corrections c ON c.match_id=m.id;
        """)
        for team_id, namespace, original in db.execute("SELECT id,namespace,source_name FROM teams").fetchall():
            country, name, method = club(namespace, original)
            identifier = sha256(f"{country}:{name}".encode()).hexdigest()
            db.execute("INSERT OR IGNORE INTO canonical_teams VALUES(?,?,?)", (identifier, country, name))
            db.execute("INSERT INTO team_aliases VALUES(?,?,?,?,?)",
                       (team_id, identifier, method, f"OpenFootball {namespace}: {original} → {country}/{name}", stamp))
        missing = db.execute("""
          SELECT m.id,m.competition,m.season,r.match_date,h.source_name,a.source_name
          FROM matches m JOIN match_revisions r ON r.match_id=m.id
          JOIN teams h ON h.id=m.home JOIN teams a ON a.id=m.away
          WHERE m.season<'2026-27' AND r.home90 IS NULL
        """).fetchall()
        if len(missing) != 21:
            raise ValueError("La revisión requiere el snapshot v2 con 21 marcadores históricos ausentes")
        for mid, code, season, day, home, away in missing:
            if (code, season, day, home, away) == ("FL1", "2025-26", "2026-05-17", "FC Nantes", "Toulouse FC"):
                fields = (None, None, 0, 0, "abandonado_adjudicado", NANTES)
            elif season == "2024-25" and day in ("2025-05-23", "2025-05-24", "2025-05-25"):
                fields = (*CORRECTIONS[code][home], None, None, "recuperado", PD if code == "PD" else SA)
            else:
                raise ValueError("Partido no contemplado en el expediente")
            db.execute("INSERT INTO result_corrections VALUES(?,?,?,?,?,?,?,?)", (mid, *fields, stamp))
        for mid, season in db.execute("SELECT id,season FROM matches WHERE competition='CL' AND stage_key IN ('Final','Finals, Final')").fetchall():
            if season != "2025-26":
                db.execute("INSERT INTO venue_evidence VALUES(?,1,?)",
                           (mid, "https://www.uefa.com/uefachampionsleague/history/"))
        if db.execute("PRAGMA foreign_key_check").fetchall() or db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("Incidencia de integridad")
        if db.execute("SELECT count(*) FROM canonical_matches WHERE canonical_home=canonical_away").fetchone()[0]:
            raise ValueError("Una asignación produjo un partido contra el mismo club")
        counts = Counter(dict(db.execute("SELECT status,count(*) FROM result_corrections GROUP BY status")))
        manifest = {
            "observed_at": stamp, "source_database_sha256": sha256(old.read_bytes()).hexdigest(),
            "clubs": db.execute("SELECT count(*) FROM canonical_teams").fetchone()[0],
            "aliases": db.execute("SELECT count(*) FROM team_aliases").fetchone()[0],
            "cross_competition": db.execute("""SELECT count(*) FROM (
                SELECT canonical_team_id FROM team_aliases JOIN teams ON teams.id=source_team_id
                GROUP BY canonical_team_id HAVING count(DISTINCT namespace)>1)""").fetchone()[0],
            "corrections": counts,
            "coverage": db.execute("""SELECT competition,season,count(*),count(home90),
                max(CASE WHEN home90 IS NOT NULL THEN match_date END),count(available_at),count(neutral)
                FROM audited_results GROUP BY competition,season""").fetchall(),
        }
    (ROOT / "data/processed/revision_f2.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print({k: v for k, v in manifest.items() if k != "coverage"})


if __name__ == "__main__":
    main()
