"""Auditoría reproducible de v3 en solo lectura, sin usar etiquetas de la reserva."""

from contextlib import closing
from datetime import date
from hashlib import sha256
import json
import sqlite3

from f2_revision import CANON, ROOT
from perfil_f2 import inventory

INDEPENDENT_URL = "https://www.bundesliga.com/en/bundesliga/matchday/2024-2025/34"
ROUND = {
    ("FC St. Pauli 1910", "VfL Bochum 1848"): (0, 2),
    ("Borussia Mönchengladbach", "VfL Wolfsburg"): (0, 1),
    ("1. FSV Mainz 05", "Bayer 04 Leverkusen"): (2, 2),
    ("FC Augsburg", "1. FC Union Berlin"): (1, 2),
    ("SC Freiburg", "Eintracht Frankfurt"): (1, 3),
    ("1. FC Heidenheim 1846", "SV Werder Bremen"): (1, 4),
    ("TSG 1899 Hoffenheim", "FC Bayern München"): (0, 4),
    ("Borussia Dortmund", "Holstein Kiel"): (3, 0),
    ("RB Leipzig", "VfB Stuttgart"): (2, 3),
}


def audit(path):
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        byte_checks = []
        for relative, expected in db.execute("SELECT path,sha256 FROM raw_objects ORDER BY id"):
            raw = ROOT / relative
            byte_checks.append(raw.is_file() and sha256(raw.read_bytes()).hexdigest() == expected)
        actual = {(h, a): (hg, ag) for h, a, hg, ag in db.execute("""
            SELECT h.name,a.name,r.home90,r.away90 FROM audited_results r
            JOIN canonical_teams h ON h.id=r.canonical_home JOIN canonical_teams a ON a.id=r.canonical_away
            WHERE partition='desarrollo' AND competition='BL1' AND season='2024-25' AND match_date='2025-05-17'
        """)}
        current = {c: {"filas": n, "marcadores": scored, "ultima_fecha": last}
                   for c, n, scored, last in db.execute("""
            SELECT competition,count(*),count(home90),max(CASE WHEN home90 IS NOT NULL THEN match_date END)
            FROM audited_results WHERE partition='en_curso' GROUP BY competition
        """)}
        current.setdefault("CL", {"filas": 0, "marcadores": 0, "ultima_fecha": None})
        anomalies = db.execute("""
            SELECT count(*) FROM canonical_matches WHERE canonical_home=canonical_away
        """).fetchone()[0]
        duplicates = db.execute("""
            SELECT count(*) FROM (
                SELECT competition,season,canonical_home,canonical_away,stage_key
                FROM canonical_matches GROUP BY 1,2,3,4,5 HAVING count(*)>1)
        """).fetchone()[0]
        return {
            "sha256_v3": sha256(path.read_bytes()).hexdigest(),
            "integridad_sqlite": db.execute("PRAGMA integrity_check").fetchone()[0],
            "claves_huerfanas": len(db.execute("PRAGMA foreign_key_check").fetchall()),
            "partidos_con_autorreferencia": anomalies,
            "claves_canonicas_repetidas": duplicates,
            "archivos_brutos": {"existentes_y_hash_valido": sum(byte_checks), "total": len(byte_checks)},
            "contraste_independiente": {
                "fuente": INDEPENDENT_URL, "universo": "BL1 2024/25 jornada 34",
                "esperados": len(ROUND), "en_v3": len(actual),
                "coinciden_identidad_fecha_marcador": sum(actual.get(pair) == goals for pair, goals in ROUND.items()),
            },
            "actualizacion_2026_27": current,
            "perfil_d_menos_2": inventory(db, date(2025, 6, 3)),
            "reserva_excluida_de_muestras": "2025/26",
        }


if __name__ == "__main__":
    print(json.dumps(audit(CANON / "openfootball_v3.sqlite"), ensure_ascii=False, indent=2))
