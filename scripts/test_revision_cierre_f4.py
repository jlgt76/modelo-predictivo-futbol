"""Pruebas sintéticas de ajuste, calibración y publicación de F4."""
from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import numpy as np

import experimento_f4 as f4
from modelos_f4 import joint, rates
from revision_cierre_f4 import check_row, class_summary, discrimination
from test_experimento_f4 import ELO, game


def config():
    return dict(
        soporte={"max_goles": 32, "cola_max": 1e-8, "rango_lambda": [.02, 6]},
        lbfgsb={"maxiter": 180, "gtol": 1e-6, "ftol": 1e-10},
        respaldo={"min_comp": 3, "min_generativo_comp": 3, "min_equipo": 2, "min_forma": 2},
        version="sintetica", dias_bloque=28, features={"A": ["l_w10_ppg"]},
        familias={"poisson": [{"id": "P1", "l2": 4, "vida_media": None}],
                  "dixon_coles": [{"id": "DC1", "l2": 4, "vida_media": None}],
                  "elo": [dict(id="E1", **ELO)],
                  "logistica": [{"id": "L1", "l2": .03, "grupos": ["A"]}]},
    )


def fixtures():
    dates = ("2024-12-24", "2024-12-26", "2024-12-29", "2024-12-30",
             "2024-12-31", "2025-01-01", "2025-01-01", "2025-01-02", "2025-02-01")
    scores = ((2, 0, 0), (0, 1, 2), (1, 1, 1), (3, 1, 0), (2, 1, 0),
              (0, 0, 1), (1, 2, 2), (2, 2, 1), (4, 0, 0))
    return [
        replace(game(i, d, ("club_nuevo", "b") if i == 6 else ("a", "b")),
                goals=(h, a), result=klass,
                x={"l_w10_n": "0" if i == 6 else "4", "v_w10_n": "4",
                   "l_w10_ppg": "" if i == 6 else str(i / 4), "v_w10_ppg": "1"})
        for i, (d, (h, a, klass)) in enumerate(zip(dates, scores), 1)
    ]


class AuditTests(TestCase):
    def test_mutar_etiquetas_no_elegibles_no_cambia_ajustes_ni_pronostico_previo(self):
        rows = fixtures()
        changed = [replace(r, goals=(8, 0), result=0) if r.key >= 5 else r for r in rows]

        def run(matches):
            fits = []
            predictions = f4.predict(matches, config(), {"P1", "DC1", "E1", "L1"},
                                     ("evaluacion",), fits, "sintetico")
            return {(r["modelo"], r["partido"]): tuple(r[k] for k in f4.COL) for r in predictions}, fits

        p, a = run(rows)
        q, b = run(changed)
        self.assertTrue(all(r["convergio"] for r in a + b))
        for model in ("B0", "B1", "B2", "P1", "DC1", "E1", "L1"):
            for match in (6, 7):
                self.assertEqual(p[model, match], q[model, match])
            self.assertNotEqual(p[model, 9], q[model, 9])
        self.assertEqual([r for r in a if r["corte"] == "2024-12-30"],
                         [r for r in b if r["corte"] == "2024-12-30"])

    def test_calibrador_ignora_etiquetas_fuera_del_corte_y_de_evaluacion(self):
        sample = [
            dict(fecha="2024-12-26", etapa="calibracion", p1=.6, px=.3, p2=.1, observado=0),
            dict(fecha="2024-12-30", etapa="calibracion", p1=.2, px=.3, p2=.5, observado=1),
            dict(fecha="2024-12-31", etapa="calibracion", p1=.2, px=.3, p2=.5, observado=2),
            dict(fecha="2025-01-01", etapa="evaluacion", p1=.5, px=.3, p2=.2, observado=0),
        ]
        bound = f4.day("2024-12-30")
        fit = f4.fit_temperature(sample, bound)
        self.assertEqual(fit["n"], 2)
        self.assertEqual(fit, f4.fit_temperature(sample[:2] + [dict(r, observado=1) for r in sample[2:]], bound))
        self.assertNotEqual(fit["temperatura"], f4.fit_temperature([dict(sample[0], observado=2), *sample[1:]],
                                                                 bound)["temperatura"])
        with self.assertRaisesRegex(ValueError, "Sin etiquetas elegibles"):
            f4.fit_temperature(sample, f4.day("2024-12-25"))

    def test_reserva_se_rechaza_antes_de_abrir_etiquetas(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "X.csv").write_text("match_id,fecha_objetivo,temporada,available_at,corte_d2\n"
                                        "1,2025-08-12,2025-26,,2025-08-10\n", encoding="utf-8")
            real = f4.validate_index
            path_open = Path.open

            def trace(path, *args, **kwargs):
                if path.name == "y.csv":
                    self.fail("Se abrió y.csv tras encontrar la reserva")
                return path_open(path, *args, **kwargs)

            hashes = {"sha256": {p: "hash" for p in
                                 ("X.csv", "y.csv", "SNAPSHOT_FEATURES.json", "scripts/features_f3.py")}}
            (root / "docs").mkdir()
            (root / "docs/MANIFIESTO_F3.json").write_text(json.dumps(hashes), encoding="utf-8")
            with (patch.object(f4, "INPUT", root), patch.object(f4, "ROOT", root),
                  patch.object(f4, "verify_base"), patch.object(f4, "CONFIG", "hash"),
                  patch.object(f4, "F3", "hash"), patch.object(f4, "file_hash", return_value="hash"),
                  patch.object(f4, "validate_index", side_effect=lambda rows, _: real(rows, 1)),
                  patch.object(Path, "open", trace)):
                with self.assertRaisesRegex(ValueError, "edición fuera"):
                    f4.read_inputs()
        with self.assertRaisesRegex(ValueError, "edición fuera"):
            f4.validate_index([dict(match_id="1", fecha_objetivo="2026-08-12", temporada="2026-27")], 1)

    def test_respaldo_equipo_y_competicion_insuficiente(self):
        rows, cfg = fixtures(), config()
        records = f4.predict(rows, cfg, {"P1"}, ("evaluacion",), [], "sintetico")
        target = next(r for r in records if r["modelo"] == "P1" and r["partido"] == 6)
        self.assertEqual((target["respaldo"], target["equipo_local_historial_corto"],
                          target["equipo_visitante_historial_corto"]), (0, 1, 0))
        cfg["respaldo"]["min_generativo_comp"] = 100
        records = f4.predict(rows, cfg, {"P1", "DC1"}, ("evaluacion",), [], "sintetico")
        targets = [r for r in records if r["modelo"] in {"P1", "DC1"} and r["partido"] == 6]
        self.assertEqual(len(targets), 2)
        for r in targets:
            self.assertEqual((r["lambda_l"], r["lambda_v"]), tuple(rates(rows[:4])))
            self.assertEqual((r["respaldo"], r["rho"]), (1, 0))
            self.assertIsNone(r["equipo_local_historial_corto"])

    def test_soporte_invalido_y_datos_inconsistentes(self):
        with self.assertRaisesRegex(ValueError, "Masa fuera"):
            joint(6, 6, 0, {"max_goles": 2, "cola_max": 1e-8})
        with self.assertRaisesRegex(ValueError, "Factor Dixon-Coles"):
            joint(6, 6, .5, config()["soporte"])
        x = {"match_id": "1", "fecha_objetivo": "2025-01-02", "temporada": "2024-25",
             "available_at": "", "corte_d2": "2024-12-31",
             "l_fecha_ultima_historia": "2025-01-01", "v_fecha_ultima_historia": ""}
        with self.assertRaisesRegex(ValueError, "unicidad"):
            f4.validate_index([x, x], 2)
        with self.assertRaisesRegex(ValueError, "Historia posterior"):
            f4.validate_index([x], 1)
        with self.assertRaisesRegex(ValueError, "universo incompatible"):
            f4.join_labels([x], [{"match_id": "2"}])
        with self.assertRaisesRegex(ValueError, "Etiqueta incoherente"):
            f4.join_labels([x], [{"match_id": "1", "goles_local90": "1",
                                "goles_visitante90": "0", "resultado_1x2": "X"}])
        r = dict(temporada="2024-25", etapa="evaluacion", fecha="2025-01-02",
                 corte_objetivo="2024-12-31", corte_parametros="2024-12-30",
                 p1=".5", px="nan", p2=".2")
        with self.assertRaisesRegex(ValueError, "Vector 1X2 inválido"):
            check_row(r)

    def test_confusion_y_empates_de_probabilidad(self):
        y = np.array([0, 1, 2])
        p = np.array([[.6, .3, .1], [.6, .3, .1], [.1, .3, .6]])
        cm, classes, summary = class_summary(y, p)
        np.testing.assert_array_equal(cm, [[1, 0, 0], [1, 0, 0], [0, 0, 1]])
        self.assertEqual(classes[1], dict(clase="X", soporte=1, pronosticados=0, aciertos=0,
                                         precision=None, recall=0., f1=0.))
        self.assertAlmostEqual(summary["macro_f1"], 5/9)
        self.assertAlmostEqual(summary["balanced_accuracy"], 2/3)
        self.assertEqual(discrimination(p[:, 1], y == 1), (.5, 1/3))
        self.assertEqual(discrimination(np.array([.2, .9, .1]), y == 1), (1., 1.))

    def test_no_sobrescribir_experimentos(self):
        with TemporaryDirectory() as directory:
            target = Path(directory) / "ejecucion"
            self.assertEqual(f4.new_run_dir(target), target.resolve())
            marker = target / "manifiesto.json"
            marker.write_text("histórico", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                f4.new_run_dir(target)
            self.assertEqual(marker.read_text(encoding="utf-8"), "histórico")
            with patch.object(f4, "read_inputs") as read:
                with self.assertRaises(FileExistsError):
                    f4.main()
                read.assert_not_called()
            with self.assertRaises(FileExistsError):
                f4.new_run_dir(f4.ORIGINAL / "otro")
