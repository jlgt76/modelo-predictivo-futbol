"""Pruebas con respuestas sintéticas. No consultan APIs ni archivos de la reserva."""

from datetime import UTC, date, datetime
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import unittest
from unittest.mock import patch

from contraste_f2 import contrast_rows
from perfil_f2 import inventory
from ingesta_proveedores_f2 import (
    DailyQuota, Pilot, SCHEMA, StopPilot, detail_inventory, import_payload,
    link_identities, main, unpack,
)

STAMP = "2026-11-24T00:00:00+00:00"
REQUEST = "/fixtures?ids=101"


def match():
    return {
        "fixture": {"id": 101, "date": "2024-08-16T19:00:00Z", "status": {"short": "FT"}},
        "league": {"id": 39, "season": 2024},
        "teams": {"home": {"id": 1}, "away": {"id": 2}},
        "score": {"fulltime": {"home": 0, "away": 2}},
        "lineups": [],
        "statistics": [{"team": {"id": 1}, "statistics": [
            {"type": "expected_goals", "value": None}, {"type": "Shots", "value": 0},
        ]}],
        "players": [{"team": {"id": 1}, "players": [{"player": {"id": 7}}]}],
    }


class IngestaTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.executescript("""
          CREATE TABLE matches(id INTEGER PRIMARY KEY, competition TEXT, season TEXT);
          CREATE TABLE canonical_teams(id TEXT PRIMARY KEY);
          INSERT INTO matches VALUES(10,'PL','2024-25'), (11,'PL','2025-26');
          INSERT INTO canonical_teams VALUES('a'), ('b');
          CREATE VIEW canonical_matches AS SELECT *, 'a' AS canonical_home, 'b' AS canonical_away FROM matches;
          CREATE TABLE match_revisions(match_id INTEGER, match_date TEXT);
          INSERT INTO match_revisions VALUES(10,'2024-08-16'), (11,'2025-08-16');
        """ + SCHEMA)

    def load(self, rows, stamp=STAMP, year=2024, request=REQUEST):
        import_payload(self.db, "api-football", request, json.dumps({"response": rows}).encode(),
                       stamp, "permiso sintético", "PL", year, (101,))

    def count(self, table):
        return self.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]

    def test_idempotencia_y_procedencia(self):
        self.load([match()])
        self.load([match()])
        self.load([match()], "2026-11-24T01:00:00+00:00")
        self.assertEqual(self.count("provider_payloads"), 1)
        self.assertEqual(self.count("provider_fetches"), 2)
        self.assertEqual(self.count("provider_fixtures"), 1)
        self.assertEqual(self.count("provider_observations"), 4)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_temporalidad_y_faltantes(self):
        self.load([match()])
        self.load([], request="/injuries?fixture=101")
        states = dict(self.db.execute("SELECT kind,state FROM provider_observations"))
        self.assertEqual(states["lineups"], "empty")
        self.assertEqual(states["events"], "absent")
        self.assertEqual(states["injuries"], "empty")
        self.assertEqual(self.db.execute("SELECT count(available_at) FROM provider_observations").fetchone()[0], 0)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE provider_observations SET available_at=?", (STAMP,))
        self.assertEqual(detail_inventory([match()])["metricas_colectivas_con_valor"], ["Shots"])

    def test_rechazo_atomico_de_duplicados_y_reserva(self):
        with self.assertRaises(ValueError):
            self.load([match(), match()])
        self.assertEqual(self.count("provider_payloads"), 0)
        with self.assertRaises(ValueError):
            self.load([match()], year=2025)
        row = match()
        row["league"]["season"] = 2025
        with self.assertRaises(ValueError):
            self.load([row])
        self.assertEqual(self.count("provider_fixtures"), 0)
        row = match()
        row["teams"]["away"]["id"] = row["teams"]["home"]["id"]
        with self.assertRaises(ValueError):
            self.load([row])
        self.assertEqual(self.count("provider_payloads"), 0)

    def test_mapeo_por_id_revisado(self):
        self.load([match()])
        m = dict(provider="api-football", kind="match", external_id=101, canonical_id=10,
                 reviewed_at=STAMP, evidence="Registro sintético verificado")
        home = dict(m, kind="team", external_id=1, canonical_id="a")
        away = dict(m, kind="team", external_id=2, canonical_id="b")
        with self.assertRaises(ValueError):
            link_identities(self.db, [m])
        with self.assertRaises(ValueError):
            link_identities(self.db, [m, dict(home, canonical_id="b"), dict(away, canonical_id="a")])
        self.assertEqual(self.count("provider_identity_links"), 0)
        self.db.execute("UPDATE match_revisions SET match_date='2024-08-17' WHERE match_id=10")
        self.db.commit()
        with self.assertRaises(ValueError):
            link_identities(self.db, [m, home, away])
        self.assertEqual(self.count("provider_identity_links"), 0)
        self.db.execute("UPDATE match_revisions SET match_date='2024-08-16' WHERE match_id=10")
        self.db.commit()
        link_identities(self.db, [m, home, away, m])
        self.assertEqual(self.count("provider_identity_links"), 3)
        with self.assertRaises(ValueError):
            link_identities(self.db, [dict(m, canonical_id=11)])
        with self.assertRaises(sqlite3.IntegrityError):
            link_identities(self.db, [dict(m, kind="team", external_id=999, canonical_id="a")])

    def test_cache_y_limite_sin_red(self):
        now = datetime.now(UTC).isoformat()
        self.load([match()], now)
        pilot = Pilot("api-football", "token-sintetico", 0, self.db, 1)
        with patch("ingesta_proveedores_f2.build_opener") as network:
            _, restored = pilot.fetch(REQUEST)
            self.assertEqual(restored, now)
            with self.assertRaises(StopPilot):
                pilot.fetch("/fixtures?ids=102")
            network.assert_not_called()

    def test_error_y_paginacion_no_equivalen_a_cobertura_cero(self):
        for payload in ({"errors": {"plan": "simulado"}, "response": []},
                        {"paging": {"total": 2}, "response": []}):
            with self.assertRaises(StopPilot):
                unpack("api-football", payload)

    def test_cli_detalle_lesiones_y_contraste_sin_red(self):
        row = match()
        response = json.dumps({"response": [row]}).encode()
        injuries = json.dumps({"response": []}).encode()
        argv = ["f2", "api-football", "PL", "2024", "--detalle", "1",
                "--fixture-id", "101", "--lesiones", "--consultar"]
        with patch("sys.argv", argv), patch.dict("os.environ", {"API_FOOTBALL_KEY": "sintetica"}), \
             patch("ingesta_proveedores_f2.verify_permission", return_value="sintética"), \
             patch.object(Pilot, "fetch", side_effect=[(response, STAMP), (response, STAMP), (injuries, STAMP)]), \
             redirect_stdout(StringIO()) as output:
            main()
        summary = json.loads(output.getvalue())
        self.assertEqual(summary["estado"], "procesado")
        self.assertEqual(summary["contraste"]["recibidos"], 1)
        self.assertEqual(summary["detalle"]["recibidos"], 1)
        self.assertEqual(summary["lesiones"]["estado"], "sin_registros")

    def test_marcador_reglamentario_y_edicion_football_data(self):
        row = dict(id=123, utcDate="2026-09-01T20:00:00Z", status="FINISHED",
                   season={"startDate": "2026-08-01"}, competition={"code": "CL"},
                   homeTeam={"id": 1}, awayTeam={"id": 2},
                   score={"duration": "PENALTY_SHOOTOUT", "fullTime": {"home": 5, "away": 4},
                          "regularTime": {"home": 1, "away": 1}})
        request = "/competitions/CL/matches?season=2026"
        def load(data):
            import_payload(self.db, "football-data", request, json.dumps({"matches": [data]}).encode(),
                           STAMP, "permiso sintético", "CL", 2026)
        load(row)
        self.assertEqual(self.db.execute("SELECT home90,away90 FROM provider_fixtures").fetchone(), (1, 1))
        with self.assertRaises(ValueError):
            load(dict(row, season={"startDate": "2025-08-01"}))
        self.assertEqual(self.count("provider_payloads"), 1)

    def test_contraste_cuenta_una_vez_id_canónico(self):
        self.db.executescript("""
          ALTER TABLE canonical_teams ADD COLUMN name TEXT;
          UPDATE canonical_teams SET name='Arsenal FC' WHERE id='a';
          UPDATE canonical_teams SET name='Chelsea FC' WHERE id='b';
          CREATE TABLE audited_results(id,competition,season,match_date,canonical_home,canonical_away,home90,away90);
          INSERT INTO audited_results VALUES(10,'PL','2024-25','2024-08-16','a','b',1,0);
        """)
        row = dict(id=5, utcDate="2024-08-16T19:00:00Z", status="FINISHED",
                   homeTeam={"name": "Arsenal FC"}, awayTeam={"name": "Chelsea FC"},
                   score={"duration": "REGULAR", "fullTime": {"home": 1, "away": 0}})
        audit = contrast_rows("PL", 2024, self.db, [row, dict(row, id=6)], mapped_matches={5: 10})
        self.assertEqual(audit["emparejados"], 1)
        self.assertEqual(audit["duplicado_proveedor"], 1)
        self.assertEqual(audit["pendientes_base"], 0)

    def test_cuota_persiste_y_caduca(self):
        with TemporaryDirectory() as tmp, patch.dict("ingesta_proveedores_f2.DAILY_LIMIT", {"football-data": 2}):
            path = Path(tmp) / "cuota.db"
            DailyQuota(path).reserve("football-data", 100000)
            with self.assertRaises(StopPilot):
                DailyQuota(path).reserve("football-data", 100003)
            DailyQuota(path).reserve("football-data", 100008)
            with self.assertRaises(StopPilot):
                DailyQuota(path).reserve("football-data", 100100)
            DailyQuota(path).reserve("api-football", 100100)
            DailyQuota(path).reserve("football-data", 186401)

    def test_bloqueo_respuesta_proveedor_persiste(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "cuota.db"
            DailyQuota(path).reserve("api-football", 100000)
            DailyQuota(path).block("api-football", 60)
            with self.assertRaises(StopPilot):
                DailyQuota(path).reserve("api-football")

    def test_perfil_dos_dias_excluye_reserva_y_revisiones_ambiguas(self):
        self.db.executescript("""
          CREATE TABLE audited_results(id,competition,season,partition,match_date,home90,away90);
          INSERT INTO audited_results VALUES
          (1,'PL','2024-25','desarrollo','2025-05-10',0,0),
          (2,'PL','2024-25','desarrollo','2025-05-11',1,0),
          (3,'PL','2025-26','reserva_final','2025-05-10',1,0),
          (4,'PL','2024-25','desarrollo','2025-05-08',1,0),
          (4,'PL','2024-25','desarrollo','2025-05-09',1,0),
          (5,'PL','2024-25','desarrollo','2025-05-09',NULL,NULL);
        """)
        summary = inventory(self.db, date(2025, 5, 12))
        self.assertEqual(summary["total"], 1)
        self.assertFalse(summary["available_at_atribuido"])


if __name__ == "__main__":
    unittest.main()
