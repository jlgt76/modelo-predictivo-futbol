"""Controles de coherencia y temporalidad con partidos sintéticos."""
from dataclasses import replace
import unittest

import numpy as np

from experimento_f4 import Game, day, eligible, phase
from modelos_f4 import elo_signals, factors, joint, markets, outcome, poisson_vector

SUPPORT={"max_goles":32,"cola_max":1e-8}
ELO={"ambito":"competicion","regresion":.2,"localia":55,"K":25,"margen":True}


def game(key,stamp,pair=("a","b")):
    return Game(key,day(stamp),"2024-25","PL",pair,(2,1),False,0,{})


class StatisticalTests(unittest.TestCase):
    def test_dos_dias_y_frontera_del_bloque(self):
        history=[game(1,"2024-12-30"),game(2,"2024-12-31"),
                 game(3,"2025-01-01"),game(4,"2025-01-02")]
        self.assertEqual([r.key for r in eligible(history,day("2025-01-01"))],[1])
        self.assertEqual([r.key for r in eligible(history,day("2025-01-02"))],[1,2])
        self.assertEqual([phase(r) for r in history],["calibracion"]*2+["evaluacion"]*2)

    def test_elo_ignora_objetivo_simultaneos_y_futuros(self):
        rows=[game(1,"2024-12-30"),game(2,"2024-12-31"),game(3,"2025-01-01"),
              game(4,"2025-01-01",("a","c")),game(5,"2025-01-02")]
        modified=[replace(r,goals=(0,5),result=2) if r.key>=2 else r for r in rows]
        first,second=elo_signals(rows,ELO),elo_signals(modified,ELO)
        self.assertEqual([first[i] for i in (1,2,3,4)],[second[i] for i in (1,2,3,4)])
        self.assertNotEqual(first[5],second[5])
        swapped=elo_signals(rows[:2]+rows[2:4][::-1]+rows[4:],ELO)
        self.assertEqual(first,swapped)

    def test_dixon_rho_cero_y_factores_positivos(self):
        raw=np.outer(poisson_vector(1.57,32),poisson_vector(.78,32))
        np.testing.assert_allclose(joint(1.57,.78,0.,SUPPORT),raw/raw.sum(),rtol=0.,atol=1e-15)
        for rho in (-.999/6,0.,.999/36):
            for h in (.02,1.57,6):
                for a in (.02,.78,6):
                    self.assertGreater(min(factors(h,a,rho)),0)
                    self.assertAlmostEqual(joint(h,a,rho,SUPPORT).sum(),1.)

    def test_coherencia_de_mercados_y_restriccion_1x2(self):
        matrix=joint(1.57,.78,-.1,SUPPORT)
        p=outcome(matrix)
        projected=markets(p,matrix)
        self.assertAlmostEqual(p.sum(),1.)
        self.assertAlmostEqual(projected["p_1x"]+p[2],1.)
        self.assertAlmostEqual(projected["p_x2"]+p[0],1.)
        self.assertAlmostEqual(projected["p_12"]+p[1],1.)
        self.assertAlmostEqual(projected["p_btts_si"]+projected["p_btts_no"],1.)
        self.assertLessEqual(projected["p_btts_si"],projected["p_over_15"])
        unders=[projected[f"p_under_{i}5"] for i in range(5)]
        self.assertEqual(unders,sorted(unders))
        for i,u in enumerate(unders):
            self.assertAlmostEqual(u+projected[f"p_over_{i}5"],1.)
        self.assertEqual(set(markets(p)),{"p_1x","p_x2","p_12"})


if __name__=="__main__":
    unittest.main()
