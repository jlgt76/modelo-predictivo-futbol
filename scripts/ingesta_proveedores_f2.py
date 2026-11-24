"""Piloto de proveedores F2. Usa credenciales del entorno y un presupuesto explícito."""

import argparse
from collections import Counter
from contextlib import closing
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3
from time import monotonic, sleep
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.error import HTTPError, URLError

from contraste_f2 import COMPETITIONS, contrast_rows
from f2_revision import CANON, ROOT

VERSION = "proveedores-f2-v1"
SOURCES = {
    "football-data": ("https://api.football-data.org/v4", "X-Auth-Token", "FOOTBALL_DATA_TOKEN"),
    "api-football": ("https://v3.football.api-sports.io", "x-apisports-key", "API_FOOTBALL_KEY"),
}
DAILY_LIMIT = {"football-data": 12, "api-football": 90}
BLOCKS = ("events", "lineups", "statistics", "players")
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS provider_payloads(
    id INTEGER PRIMARY KEY, provider TEXT NOT NULL, request TEXT NOT NULL,
    sha256 TEXT NOT NULL, permission_reference TEXT NOT NULL, body BLOB NOT NULL,
    UNIQUE(provider,request,sha256));
CREATE TABLE IF NOT EXISTS provider_fetches(
    id INTEGER PRIMARY KEY, payload_id INTEGER NOT NULL REFERENCES provider_payloads(id),
    consulted_at TEXT NOT NULL, UNIQUE(payload_id,consulted_at));
CREATE TABLE IF NOT EXISTS provider_entities(
    provider TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('match','team','player','coach')),
    external_id INTEGER NOT NULL CHECK(external_id>0),
    PRIMARY KEY(provider,kind,external_id));
CREATE TABLE IF NOT EXISTS provider_identity_links(
    provider TEXT NOT NULL, kind TEXT NOT NULL, external_id INTEGER NOT NULL,
    canonical_team_id TEXT REFERENCES canonical_teams(id), canonical_match_id INTEGER REFERENCES matches(id),
    canonical_player_id INTEGER REFERENCES pilot_players(id),
    evidence TEXT NOT NULL CHECK(length(trim(evidence))>0), reviewed_at TEXT NOT NULL,
    CHECK((kind='team' AND canonical_team_id IS NOT NULL AND canonical_match_id IS NULL AND canonical_player_id IS NULL)
       OR (kind='match' AND canonical_match_id IS NOT NULL AND canonical_team_id IS NULL AND canonical_player_id IS NULL)
       OR (kind='player' AND canonical_player_id IS NOT NULL AND canonical_match_id IS NULL AND canonical_team_id IS NULL)),
    PRIMARY KEY(provider,kind,external_id),
    FOREIGN KEY(provider,kind,external_id) REFERENCES provider_entities(provider,kind,external_id));
CREATE TABLE IF NOT EXISTS pilot_players(id INTEGER PRIMARY KEY, display_name TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS provider_unique_match_link
    ON provider_identity_links(provider,canonical_match_id) WHERE kind='match';
CREATE TABLE IF NOT EXISTS provider_fixtures(
    payload_id INTEGER NOT NULL REFERENCES provider_payloads(id), provider TEXT NOT NULL,
    fixture_id INTEGER NOT NULL, fixture_kind TEXT NOT NULL DEFAULT 'match' CHECK(fixture_kind='match'),
    competition TEXT NOT NULL, season INTEGER NOT NULL CHECK(season<>2025),
    kickoff_at TEXT NOT NULL, status TEXT NOT NULL, home_id INTEGER, away_id INTEGER,
    home90 INTEGER CHECK(home90>=0), away90 INTEGER CHECK(away90>=0),
    CHECK(home_id<>away_id), CHECK((home90 IS NULL)=(away90 IS NULL)),
    PRIMARY KEY(payload_id,fixture_id),
    FOREIGN KEY(provider,fixture_kind,fixture_id) REFERENCES provider_entities(provider,kind,external_id));
CREATE TABLE IF NOT EXISTS provider_observations(
    payload_id INTEGER NOT NULL REFERENCES provider_payloads(id), provider TEXT NOT NULL, fixture_id INTEGER NOT NULL,
    fixture_kind TEXT NOT NULL DEFAULT 'match' CHECK(fixture_kind='match'),
    kind TEXT NOT NULL CHECK(kind IN ('events','lineups','statistics','players','injuries')),
    timing TEXT NOT NULL CHECK(timing IN ('post_match','historical_unknown')),
    available_at TEXT CHECK(available_at IS NULL), state TEXT NOT NULL CHECK(state IN ('absent','empty','present')),
    body TEXT CHECK(body IS NULL OR json_valid(body)),
    PRIMARY KEY(payload_id,fixture_id,kind),
    FOREIGN KEY(provider,fixture_kind,fixture_id) REFERENCES provider_entities(provider,kind,external_id));
"""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class StopPilot(Exception):
    """La consulta debe detenerse sin repetir la llamada."""


def digest(data):
    return sha256(data).hexdigest()


def utc(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Hora del partido sin zona")
    return parsed.astimezone(UTC).isoformat()


def fixture(provider, row, code, year):
    if provider == "football-data":
        season = row.get("season") or {}
        competition = row.get("competition") or {}
        if date_year(season.get("startDate")) != year or competition.get("code", code) != code:
            raise ValueError("Partido de Football-Data.org fuera de la edición solicitada")
        score = row.get("score") or {}
        regular = score.get("fullTime") if score.get("duration") == "REGULAR" else score.get("regularTime")
        return row["id"], utc(row["utcDate"]), row["status"], row["homeTeam"].get("id"), row["awayTeam"].get("id"), regular
    league, f = row["league"], row["fixture"]
    if league["season"] != year or league["id"] != COMPETITIONS[code]:
        raise ValueError("Partido fuera del universo solicitado")
    return (f["id"], utc(f["date"]), f["status"]["short"], row["teams"]["home"].get("id"),
            row["teams"]["away"].get("id"), (row.get("score") or {}).get("fulltime"))


def date_year(value):
    return int(value[:4]) if isinstance(value, str) and value[:4].isdigit() else None


def unpack(provider, payload):
    if provider == "api-football" and payload.get("errors"):
        raise StopPilot("API-Football devolvió una restricción o un error. Se detuvo el lote.")
    rows = payload["matches" if provider == "football-data" else "response"]
    if not isinstance(rows, list):
        raise ValueError("Respuesta sin lista de registros")
    if (payload.get("paging") or {}).get("total", 1) > 1:
        raise StopPilot("Respuesta paginada. Completar el inventario de páginas en un plan separado.")
    return rows


def api_contrast_rows(rows, code, year):
    for row in rows:
        fid, kickoff, status, _, _, regular = fixture("api-football", row, code, year)
        yield {
            "id": fid, "utcDate": kickoff,
            "status": "FINISHED" if status in ("FT", "AET", "PEN") else status,
            "homeTeam": row["teams"]["home"], "awayTeam": row["teams"]["away"],
            "score": {"duration": "REGULAR", "fullTime": regular or {}},
        }


def link_identities(db, mappings):
    """Aplica solamente correspondencias revisadas y respaldadas por evidencia."""
    with db:
        order = {"team": 0, "player": 1, "match": 2}
        for m in sorted(mappings, key=lambda row: order[row["kind"]]):
            provider, kind, external, canonical = (m[k] for k in ("provider", "kind", "external_id", "canonical_id"))
            column = {"team": "canonical_team_id", "match": "canonical_match_id", "player": "canonical_player_id"}[kind]
            if provider not in SOURCES or type(external) is not int or external <= 0:
                raise ValueError("Identidad de origen inválida")
            if not isinstance(m["evidence"], str) or not m["evidence"].strip():
                raise ValueError("Falta evidencia de la correspondencia")
            reviewed = utc(m["reviewed_at"])
            prior = db.execute(f"SELECT {column} FROM provider_identity_links WHERE provider=? AND kind=? AND external_id=?",
                               (provider, kind, external)).fetchone()
            if prior:
                if prior[0] != canonical:
                    raise ValueError("La correspondencia contradice una revisión previa")
            if kind == "match":
                target = db.execute("""SELECT competition,season,canonical_home,canonical_away
                                     FROM canonical_matches WHERE id=?""", (canonical,)).fetchone()
                sources = db.execute("""SELECT DISTINCT competition,season,home_id,away_id,kickoff_at
                                      FROM provider_fixtures WHERE provider=? AND fixture_id=?""",
                                     (provider, external)).fetchall()
                dates = {row[0] for row in db.execute("SELECT match_date FROM match_revisions WHERE match_id=?", (canonical,))}
                if not target or not sources or target[1] == "2025-26":
                    raise ValueError("Partido canónico inexistente, fuera de origen o reservado")
                for c, y, home_id, away_id, kickoff in sources:
                    teams = [db.execute("""SELECT canonical_team_id FROM provider_identity_links
                                          WHERE provider=? AND kind='team' AND external_id=?""",
                                        (provider, tid)).fetchone() for tid in (home_id, away_id)]
                    if (c, f"{y}-{(y+1)%100:02d}") != target[:2] or any(t is None for t in teams):
                        raise ValueError("Competición, temporada o equipos sin verificar")
                    if tuple(t[0] for t in teams) != target[2:] or kickoff[:10] not in dates:
                        raise ValueError("Localía, identidad o fecha incompatible con el partido canónico")
            if prior:
                continue
            db.execute(f"""INSERT INTO provider_identity_links
                           (provider,kind,external_id,{column},evidence,reviewed_at) VALUES(?,?,?,?,?,?)""",
                       (provider, kind, external, canonical, m["evidence"].strip(), reviewed))


def detail_inventory(rows):
    inv = {block: Counter() for block in BLOCKS}
    metrics = set()
    for row in rows:
        for block in BLOCKS:
            value = row.get(block)
            inv[block]["ausente" if value is None else "con_datos" if value else "vacio"] += 1
        for team in row.get("statistics") or []:
            metrics.update(item["type"] for item in team.get("statistics", []) if item.get("value") is not None)
    return {"bloques": inv, "metricas_colectivas_con_valor": sorted(metrics)}


def entity(db, provider, kind, value):
    if value is not None:
        if type(value) is not int or value <= 0:
            raise ValueError("Identificador externo inválido")
        db.execute("INSERT OR IGNORE INTO provider_entities VALUES(?,?,?)", (provider, kind, value))


def observe(db, pid, provider, fid, kind, body):
    state = "absent" if body is None else "present" if body else "empty"
    timing = "post_match" if kind in ("statistics", "players", "events") else "historical_unknown"
    db.execute("""INSERT OR IGNORE INTO provider_observations
                  (payload_id,provider,fixture_id,kind,timing,state,body) VALUES(?,?,?,?,?,?,?)""",
               (pid, provider, fid, kind, timing, state, None if body is None else json.dumps(body, ensure_ascii=False)))
    for group in body or []:
        for role in ("team", "player", "coach", "assist"):
            info = group.get(role)
            if isinstance(info, dict):
                entity(db, provider, "player" if role == "assist" else role, info.get("id"))
        for member in group.get("startXI", []) + group.get("substitutes", []) + group.get("players", []):
            entity(db, provider, "player", member.get("player", {}).get("id"))


def import_payload(db, provider, request, raw, consulted_at, reference, code, year, expected_ids=()):
    if year == 2025:
        raise ValueError("2025/26 reservada")
    path = request.split("?", 1)[0]
    rows = unpack(provider, json.loads(raw))
    with db:
        blob = digest(raw)
        db.execute("""INSERT OR IGNORE INTO provider_payloads(provider,request,sha256,permission_reference,body)
                      VALUES(?,?,?,?,?)""", (provider, request, blob, reference, raw))
        pid = db.execute("SELECT id FROM provider_payloads WHERE provider=? AND request=? AND sha256=?",
                         (provider, request, blob)).fetchone()[0]
        db.execute("INSERT OR IGNORE INTO provider_fetches(payload_id,consulted_at) VALUES(?,?)", (pid, consulted_at))
        if path == "/injuries":
            grouped = {fid: [] for fid in expected_ids}
            for row in rows:
                fid = row["fixture"]["id"]
                if fid not in grouped or row["league"]["season"] != year or row["league"]["id"] != COMPETITIONS[code]:
                    raise ValueError("Lesión fuera del lote solicitado")
                grouped[fid].append(row)
            for fid, injury_rows in grouped.items():
                entity(db, provider, "match", fid)
                observe(db, pid, provider, fid, "injuries", injury_rows)
            return
        seen = set()
        for row in rows:
            fid, kickoff, status, home, away, regular = fixture(provider, row, code, year)
            if type(fid) is not int or fid <= 0 or fid in seen or (expected_ids and fid not in expected_ids):
                raise ValueError("Partido duplicado o fuera del lote")
            if home is not None and home == away:
                raise ValueError("Equipo local y visitante idénticos")
            seen.add(fid)
            for kind, value in (("match", fid), ("team", home), ("team", away)):
                entity(db, provider, kind, value)
            regular = regular or {}
            gh, ga = regular.get("home"), regular.get("away")
            if any(v is not None and (type(v) is not int or v < 0) for v in (gh, ga)):
                raise ValueError("Marcador inválido")
            if status not in ("FINISHED", "FT", "AET", "PEN") or None in (gh, ga):
                gh = ga = None
            db.execute("""INSERT INTO provider_fixtures
                          (payload_id,provider,fixture_id,competition,season,kickoff_at,status,home_id,away_id,home90,away90)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(payload_id,fixture_id) DO NOTHING""",
                       (pid, provider, fid, code, year, kickoff, status, home, away, gh, ga))
            if expected_ids:
                for block in BLOCKS:
                    observe(db, pid, provider, fid, block, row.get(block))


def open_store():
    path = CANON / "proveedores_f2_v1.sqlite"
    if not path.exists():
        with sqlite3.connect((CANON / "openfootball_v3.sqlite").as_uri() + "?mode=ro", uri=True) as base:
            with sqlite3.connect(path) as target:
                base.backup(target)
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    return db


def verify_permission(path, provider, persist):
    if path is None:
        raise StopPilot("Falta evidencia local de permiso para consultar. Se conserva el modo de planificación.")
    approval = json.loads(path.read_text(encoding="utf-8"))[provider]
    reference = approval.get("reference")
    expiry = utc(approval["valid_until"])
    if approval.get("processing") is not True or not reference or expiry <= datetime.now(UTC).isoformat():
        raise StopPilot("La evidencia de procesamiento falta o está vencida.")
    if persist and approval.get("storage") is not True:
        raise StopPilot("La persistencia requiere permiso de almacenamiento confirmado.")
    return reference


class DailyQuota:
    """Cuenta intentos locales por proveedor en una ventana móvil de 24 horas."""

    def __init__(self, path):
        self.path = path

    def reserve(self, provider, now=None):
        now = now if now is not None else datetime.now(UTC).timestamp()
        with closing(sqlite3.connect(self.path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS quota_attempts(
                        id INTEGER PRIMARY KEY, provider TEXT NOT NULL, attempted_at REAL NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS quota_blocks(
                        provider TEXT PRIMARY KEY, until_at REAL NOT NULL)""")
            block = db.execute("SELECT until_at FROM quota_blocks WHERE provider=?", (provider,)).fetchone()
            count, last = db.execute("""SELECT count(*),max(attempted_at) FROM quota_attempts
                                        WHERE provider=? AND attempted_at>?""", (provider, now-86400)).fetchone()
            if (block and block[0] > now) or count >= DAILY_LIMIT[provider]:
                raise StopPilot("Límite diario persistente local alcanzado.")
            if last is not None and now - last < 7:
                raise StopPilot("Espera siete segundos entre intentos al mismo proveedor.")
            db.execute("INSERT INTO quota_attempts(provider,attempted_at) VALUES(?,?)", (provider, now))

    def block(self, provider, seconds):
        until = datetime.now(UTC).timestamp() + seconds
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""INSERT INTO quota_blocks VALUES(?,?)
                         ON CONFLICT(provider) DO UPDATE SET until_at=max(until_at,excluded.until_at)""",
                       (provider, until))


class Pilot:
    def __init__(self, provider, token, budget, db=None, ttl=0, quota=None):
        self.provider, self.token, self.budget, self.db, self.ttl = provider, token, budget, db, ttl
        self.calls = 0
        self.remaining = None
        self.last_call = None
        self.quota = quota

    def fetch(self, request):
        if self.db and self.ttl:
            bound = (datetime.now(UTC) - timedelta(hours=self.ttl)).isoformat()
            cached = self.db.execute("""
                SELECT p.body,f.consulted_at FROM provider_payloads p JOIN provider_fetches f ON f.payload_id=p.id
                WHERE p.provider=? AND p.request=? AND f.consulted_at>=? ORDER BY f.consulted_at DESC LIMIT 1
                """, (self.provider, request, bound)).fetchone()
            if cached:
                return cached
        if self.calls >= self.budget or self.remaining == 0:
            raise StopPilot("Presupuesto agotado. Reanuda desde la última consulta guardada.")
        if self.last_call is not None:
            sleep(max(0, 7.1 - (monotonic() - self.last_call)))
        base, header, _ = SOURCES[self.provider]
        if self.quota is not None:
            self.quota.reserve(self.provider)
        self.calls += 1
        self.last_call = monotonic()
        try:
            with build_opener(NoRedirect()).open(Request(base + request, headers={header: self.token}), timeout=20) as response:
                daily = response.headers.get("x-ratelimit-requests-remaining", "")
                limits = [daily, response.headers.get("x-ratelimit-remaining", ""),
                          response.headers.get("X-Requests-Available-Minute", "")]
                remaining = [int(n) for n in limits if n.isdecimal()]
                self.remaining = min(remaining) if remaining else None
                if self.quota is not None and daily == "0":
                    self.quota.block(self.provider, 86400)
                body = response.read()
        except HTTPError as exc:
            if exc.code == 429 and self.quota is not None:
                retry = exc.headers.get("Retry-After", "") if exc.headers else ""
                daily = exc.headers.get("x-ratelimit-requests-remaining", "") if exc.headers else ""
                delay = max(60, int(retry)) if retry.isdecimal() else 86400
                self.quota.block(self.provider, max(86400, delay) if daily == "0" else delay)
            raise
        return body, datetime.now(UTC).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=SOURCES)
    parser.add_argument("code", choices=COMPETITIONS)
    parser.add_argument("year", type=int)
    parser.add_argument("--detalle", type=int, choices=range(1, 21))
    parser.add_argument("--desde", type=int, default=0)
    parser.add_argument("--hash-indice", help="SHA-256 del índice registrado en la tanda anterior.")
    parser.add_argument("--fixture-id", type=int, help="Selecciona un partido que exista en el índice autorizado.")
    parser.add_argument("--lesiones", action="store_true")
    parser.add_argument("--consultar", action="store_true")
    parser.add_argument("--permisos", type=Path)
    parser.add_argument("--persistir", action="store_true")
    parser.add_argument("--mapeos-revisados", type=Path)
    parser.add_argument("--cache-horas", type=int, default=24, metavar="0–168")
    parser.add_argument("--max-solicitudes", type=int, default=3, choices=range(1, 4))
    args = parser.parse_args()
    allowed = (2026,) if args.provider == "football-data" else (2022, 2023, 2024)
    if args.year not in allowed or args.desde < 0:
        parser.error("Temporada fuera del piloto o posición inválida. 2025/26 está reservada.")
    if not 0 <= args.cache_horas <= 168:
        parser.error("El intervalo de caché debe estar entre 0 y 168 horas.")
    if (args.detalle and args.provider != "api-football") or (args.lesiones and not args.detalle):
        parser.error("Detalle y lesiones requieren un lote de API-Football.")
    if args.lesiones and args.detalle != 1:
        parser.error("La muestra de lesiones se limita a un partido.")
    if args.fixture_id is not None and (args.detalle != 1 or args.desde):
        parser.error("Un fixture ID concreto exige --detalle 1 y una posición inicial.")
    if args.desde and (not args.detalle or not args.hash_indice):
        parser.error("Reanudar requiere --detalle y --hash-indice de la tanda previa.")
    if args.mapeos_revisados and not args.persistir:
        parser.error("Los mapeos requieren una base de proveedores autorizada.")
    planned = 1 + bool(args.detalle) + args.lesiones
    output = {"provider": args.provider, "competition": args.code, "season": args.year, "estimacion_maxima": planned}
    if not args.consultar:
        print(json.dumps(output, ensure_ascii=False))
        return
    if args.max_solicitudes < planned:
        parser.error("El plan de llamadas supera el presupuesto declarado.")
    name = SOURCES[args.provider][2]
    token = os.environ.get(name, "").strip()
    if not token:
        parser.error(f"Falta {name} en el entorno.")
    db = client = None
    try:
        reference = verify_permission(args.permisos, args.provider, args.persistir)
        db = open_store() if args.persistir else None
        client = Pilot(args.provider, token, args.max_solicitudes, db, args.cache_horas,
                       DailyQuota(CANON / "cuota_proveedores_f2.sqlite"))
        query = (f"/competitions/{args.code}/matches?season={args.year}" if args.provider == "football-data"
                 else "/fixtures?" + urlencode({"league": COMPETITIONS[args.code], "season": args.year}))

        def fetch(request, ids=(), expected_hash=None):
            raw, stamp = client.fetch(request)
            checksum = digest(raw)
            if expected_hash and expected_hash != checksum:
                raise StopPilot("Cambió el índice. Revisa la lista antes de reanudar por posición.")
            payload = json.loads(raw)
            rows = unpack(args.provider, payload)
            if db:
                import_payload(db, args.provider, request, raw, stamp, reference, args.code, args.year, ids)
            return rows, stamp, checksum

        rows, output["consulted_at"], output["hash_indice"] = fetch(query, expected_hash=args.hash_indice)
        records = [fixture(args.provider, row, args.code, args.year) for row in rows]
        ids = sorted({r[0] for r in records if r[2] in ("FT", "AET", "PEN", "FINISHED")})
        output.update(recibidos=len(records), finalizados=len(ids), duplicados=len(records)-len({r[0] for r in records}))
        if args.mapeos_revisados:
            link_identities(db, json.loads(args.mapeos_revisados.read_text(encoding="utf-8")))
        mappings = dict(db.execute("""SELECT external_id,canonical_match_id FROM provider_identity_links
                                      WHERE provider=? AND kind='match'""", (args.provider,))) if db else {}
        comparable = rows if args.provider == "football-data" else api_contrast_rows(rows, args.code, args.year)
        with sqlite3.connect((CANON / "openfootball_v3.sqlite").as_uri() + "?mode=ro", uri=True) as base:
            output["contraste"] = contrast_rows(args.code, args.year, base, comparable, mapped_matches=mappings)
        if args.detalle:
            if args.fixture_id is not None and args.fixture_id not in ids:
                raise StopPilot("El fixture ID no pertenece al índice finalizado autorizado.")
            selected = [args.fixture_id] if args.fixture_id is not None else ids[args.desde:args.desde + args.detalle]
            if not selected:
                raise StopPilot("La posición indicada no contiene partidos finalizados.")
            detail, _, output["hash_detalle"] = fetch("/fixtures?ids=" + "-".join(map(str, selected)), selected)
            returned = {fixture(args.provider, row, args.code, args.year)[0] for row in detail}
            if len(returned) != len(detail) or not returned.issubset(selected):
                raise StopPilot("El lote devolvió identidades repetidas o fuera de la solicitud.")
            output["detalle"] = {
                "solicitados": len(selected), "recibidos": len(detail),
                **detail_inventory(detail),
                "siguiente_desde": None if args.fixture_id is not None else
                args.desde + len(selected) if len(returned) == len(selected) else args.desde,
            }
            if args.lesiones:
                injuries, _, output["hash_lesiones"] = fetch(f"/injuries?fixture={selected[0]}", selected)
                output["lesiones"] = {"registros": len(injuries), "estado": "con_datos" if injuries else "sin_registros"}
        output["estado"] = "procesado"
    except HTTPError as exc:
        output.update(estado="http", codigo=exc.code)
    except (URLError, TimeoutError, ValueError, KeyError, sqlite3.Error, OSError, TypeError):
        output.update(estado="respuesta_o_configuracion_invalida")
    except StopPilot as exc:
        output.update(estado=str(exc))
    finally:
        if db is not None:
            db.close()
    output["solicitudes_emitidas"] = client.calls if client else 0
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
