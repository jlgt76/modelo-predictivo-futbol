"""Controles sintéticos para los límites del perfil, sin usar la reserva."""

from dataclasses import replace
from datetime import date
import unittest

from features_f3 import Match, feature_rows
from eda_f3 import validate_index


def match(key, day, home="a", away="b", goals=(2, 0), neutral=None):
    return Match(key, "PL", "2024-25", date(2025, 1, day).toordinal(),
                 home, away, *goals, neutral)


def rows(matches):
    return {r["match_id"]: r for r in feature_rows(matches)}


class TemporalTests(unittest.TestCase):
    def test_mutar_futuro_corte_y_objetivo_no_cambia_x(self):
        source = [match(1, 2), match(2, 3), match(3, 4), match(4, 4, "c", "a"), match(5, 5)]
        altered = [replace(m, hg=9, ag=8) if m.key in {2,3,4,5} else m for m in source]
        original, changed = rows(source), rows(altered)
        self.assertEqual(original[3], changed[3])
        self.assertEqual(original[4], changed[4])
        self.assertEqual(original[3]["l_w5_n"], 1)
        self.assertEqual(original[3]["l_w5_gf"], 2)
        self.assertEqual(original[3]["l_partidos_reg_7d"], 1)
        self.assertIsNone(original[3]["available_at"])
        self.assertNotEqual(original[5]["l_w5_gf"], changed[5]["l_w5_gf"])

    def test_sin_historia_y_sedes(self):
        source = [match(1, 1, neutral=1), match(2, 2), match(3, 4)]
        result = rows(source)
        self.assertIsNone(result[1]["l_w5_gf"])
        self.assertEqual(result[1]["l_sin_historia"], 1)
        self.assertEqual(result[3]["l_general_n"], 2)
        self.assertEqual(result[3]["l_neutral_n"], 1)
        self.assertEqual(result[3]["l_rol_home_n"], 1)
        self.assertEqual(result[3]["l_rol_home_sede_desconocida_n"], 1)

    def test_empate_de_fechas_en_frontera_no_se_rompe_por_id(self):
        source = [match(1, 1), match(2, 1), *[match(i, i-1) for i in range(3,7)], match(7, 8)]
        self.assertEqual(rows(source)[7]["l_w5_n"], 6)
        self.assertEqual(rows(source)[7], rows(list(reversed(source)))[7])

    def test_calidad_de_rival_solo_usa_su_historia_anterior_al_cruce(self):
        source = [match(i, i, "b", "c", (0, 1)) for i in range(1,7)]
        source += [match(7, 8, "a", "b"), match(8, 10, "b", "c", (7, 0)), match(9, 13, "a", "c")]
        original = rows(source)[9]
        altered = rows([replace(m, hg=0) if m.key==8 else m for m in source])[9]
        self.assertEqual(original["l_rival_ppg_previo"], 0)
        self.assertEqual(original["l_rival_ppg_previo"], altered["l_rival_ppg_previo"])
        self.assertEqual(original["l_ppg_ponderado_rival"], 3)

    def test_indice_eda_rechaza_duplicado_y_corte_reconstruido_incorrecto(self):
        source = [match(1, 2), match(2, 4)]
        valid = list(feature_rows(source))
        validate_index(valid, source)
        with self.assertRaises(ValueError):
            validate_index([valid[0], valid[0]], source)
        with self.assertRaises(ValueError):
            validate_index([valid[0], dict(valid[1], corte_d2="2025-01-03")], source)


if __name__ == "__main__":
    unittest.main()
