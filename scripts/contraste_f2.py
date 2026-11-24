"""Contraste gratuito de F2. Solo conserva agregados del proveedor."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import json
import os
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from f2_revision import CANON, ROOT, club

COMPETITIONS = dict(CL=2, PL=39, PD=140, BL1=78, SA=135, FL1=61)


def get(url, header, token):
    with urlopen(Request(url, headers={header: token}), timeout=20) as response:
        return json.load(response)


def football_data(code, year, token, db):
    rows = get(f"https://api.football-data.org/v4/competitions/{code}/matches?season={year}",
               "X-Auth-Token", token)["matches"]
    return contrast_rows(code, year, db, rows)


def contrast_rows(code, year, db, rows, *, mapped_matches=None):
    rows = list(rows)
    season = f"{year}-{(year+1)%100:02d}"
    local = defaultdict(list)
    by_id = defaultdict(list)
    for mid, d, home, away, gh, ga in db.execute("""
        SELECT r.id,r.match_date,h.name,a.name,r.home90,r.away90
        FROM audited_results r JOIN canonical_teams h ON h.id=r.canonical_home
        JOIN canonical_teams a ON a.id=r.canonical_away
        WHERE r.competition=? AND r.season=?
        """, (code, season)):
        local[home, away].append((mid, d, gh, ga))
        by_id[mid].append((mid, d, gh, ga))
    summary = Counter(recibidos=len(rows))
    matched = set()
    for row in rows:
        names = [row[side].get("name") for side in ("homeTeam", "awayTeam")]
        if not all(names):
            summary["identidad_pendiente"] += 1
            continue
        time = datetime.fromisoformat(row["utcDate"])
        mapped = (mapped_matches or {}).get(row["id"])
        pair = tuple(club(code, name)[1] for name in names)
        if mapped is not None:
            same_day = by_id[mapped]
            if len(same_day) == 1 and same_day[0][1] != time.date().isoformat():
                summary["fecha_distinta_con_id_revisado"] += 1
                continue
        else:
            same_day = [item for item in local[pair] if item[1] == time.date().isoformat()]
        if len(same_day) != 1:
            summary["sin_emparejar_o_fecha_distinta"] += 1
            continue
        mid, _, home90, away90 = same_day[0]
        if mid in matched:
            summary["duplicado_proveedor"] += 1
            continue
        matched.add(mid)
        summary["emparejados"] += 1
        summary["por_id_revisado" if mapped is not None else "por_nombre_fecha_provisional"] += 1
        if row["status"] == "FINISHED":
            score = row["score"]
            regular = (score.get("regularTime") or {}) if score["duration"] != "REGULAR" else score["fullTime"]
            goals = (regular.get("home"), regular.get("away"))
            if None in goals or None in (home90, away90):
                summary["marcador_no_comparable"] += 1
            else:
                summary["marcador_igual" if goals == (home90, away90) else "marcador_distinto"] += 1
    summary["filas_fuente_base"] = sum(map(len, local.values()))
    summary["pendientes_base"] = summary["filas_fuente_base"] - len(matched)
    summary["finalizados_proveedor"] = sum(x["status"] == "FINISHED" for x in rows)
    return summary


def api_football(code, year, token):
    query = urlencode({"id": COMPETITIONS[code], "season": year})
    payload = get(f"https://v3.football.api-sports.io/leagues?{query}", "x-apisports-key", token)
    if payload.get("errors"):
        return {"estado": "error_o_restriccion_del_proveedor"}
    rows = [s["coverage"] for row in payload["response"] for s in row["seasons"] if s["year"] == year]
    return {"estado": "documentado_por_api" if rows else "sin_cobertura_devuelta", "capacidades": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proveedor", choices=("football-data", "api-football"))
    parser.add_argument("competicion", choices=COMPETITIONS)
    parser.add_argument("temporada", choices=range(2021, 2027), type=int)
    parser.add_argument("--permisos-verificados", action="store_true")
    args = parser.parse_args()
    if args.temporada == 2025:
        parser.error("2025/26 está reservada. Auditarla por separado sin usarla en desarrollo.")
    if not args.permisos_verificados:
        parser.error("Confirma primero los permisos aplicables a tu cuenta y al contraste local.")
    name = "FOOTBALL_DATA_TOKEN" if args.proveedor == "football-data" else "API_FOOTBALL_KEY"
    token = os.environ.get(name)
    if not token:
        parser.error(f"Falta {name} en el entorno del proceso.")
    try:
        if args.proveedor == "football-data":
            path = (CANON / "openfootball_v3.sqlite").as_uri() + "?mode=ro"
            with sqlite3.connect(path, uri=True) as db:
                result = football_data(args.competicion, args.temporada, token, db)
        else:
            result = api_football(args.competicion, args.temporada, token)
    except HTTPError as exc:
        result = {"estado": "http", "codigo": exc.code}
    except (URLError, TimeoutError, ValueError, KeyError):
        result = {"estado": "respuesta_no_disponible_o_invalida"}
    path = ROOT / "data/processed" / f"contraste_{args.proveedor}_{args.competicion}_{args.temporada}.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
