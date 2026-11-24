"""Inventario conservador por fecha de referencia, sin atribuir publicación histórica."""

import argparse
from datetime import date, timedelta
import json
import sqlite3

from f2_revision import CANON


def inventory(db, reference, margin=2):
    if margin < 2:
        raise ValueError("El margen mínimo es D−2")
    limit = reference - timedelta(days=margin)
    counts = db.execute("""
        WITH eligible AS (
            SELECT id, competition, season, match_date
            FROM audited_results
            WHERE partition='desarrollo' AND season NOT IN ('2025-26','2026-27')
            GROUP BY id, competition, season, match_date
            HAVING count(*)=1 AND count(home90)=1 AND count(away90)=1
        ), unambiguous AS (
            SELECT id FROM audited_results WHERE partition='desarrollo'
            GROUP BY id HAVING count(*)=1
        )
        SELECT competition,season,count(*)
        FROM eligible JOIN unambiguous USING(id)
        WHERE match_date <= ?
        GROUP BY competition,season ORDER BY competition,season
    """, (limit.isoformat(),)).fetchall()
    return {
        "perfil": "reconstruido_por_fecha", "referencia": reference.isoformat(),
        "hasta": limit.isoformat(), "margen_dias": margin, "available_at_atribuido": False,
        "uso": "candidatos_para_auditoria", "total": sum(n for _, _, n in counts),
        "por_competicion_temporada": [{"competicion": c, "temporada": s, "filas": n} for c, s, n in counts],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fecha", type=date.fromisoformat)
    parser.add_argument("--margen-dias", type=int, default=2)
    args = parser.parse_args()
    if args.margen_dias < 2:
        parser.error("El margen mínimo del perfil reconstruido es de dos fechas calendario.")
    with sqlite3.connect((CANON / "openfootball_v3.sqlite").as_uri() + "?mode=ro", uri=True) as db:
        print(json.dumps(inventory(db, args.fecha, args.margen_dias), ensure_ascii=False))


if __name__ == "__main__":
    main()
