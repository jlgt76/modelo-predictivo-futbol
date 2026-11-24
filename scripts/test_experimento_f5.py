"""Pruebas pequeñas de invariantes de F5 sin usar resultados de reserva."""
from dataclasses import replace
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase

import experimento_f5 as f5
import numpy as np

from experimento_f4 import Game, day, new_run_dir, validate_index
from evaluar_f5 import capture
from modelos_f4 import markets, outcome
from modelos_f5 import (Encoder, blocks, calibrate, calibrator_choice, causal_elo, early_split,
                        ensemble_fit, features, from_components, past_oof, probability, train)
from revision_cierre_f4 import check_hashes


def game(key, stamp, season="2024-25", result=0, goals=(1,0)):
    return Game(key,day(stamp),season,"PL",("a","b"),goals,False,result,{})


def config():
    return {"hilos":1,"semilla":7,"dias_corte":2,"dias_bloque":28,
            "early_stopping":{"dias_validacion":6,"min_validacion":3,"min_entrenamiento":5,"alto":2}}


class F5Tests(TestCase):
    def test_objetivo_simultaneidad_y_mutacion_futura_en_ajuste(self):
        rows=[game(i,f"2024-12-{i:02d}") for i in range(10,31)] + [game(31,"2025-01-01"),game(32,"2025-01-01"),game(33,"2025-01-02")]
        stage,_,cut,train_ids,ids=list(blocks(rows,config()))[-1]
        self.assertEqual(stage,"evaluacion")
        self.assertEqual(cut,day("2024-12-30"))
        self.assertFalse(set(train_ids)&set(ids))
        self.assertEqual(list(ids), [21,22,23])
        days=np.asarray([r.day for r in rows])
        data={"a":np.arange(len(rows),dtype=float)}
        y=np.arange(len(rows))%3
        changed=y.copy()
        changed[ids]=(changed[ids]+1)%3
        model={"familia":"rf","params":{"n_estimators":5,"max_depth":2}}
        a,_=train(data,["a"],y,train_ids,days,config(),model)
        b,_=train(data,["a"],changed,train_ids,days,config(),model)
        np.testing.assert_array_equal(a.predict(data,ids),b.predict(data,ids))

    def test_imputacion_y_categorias_solo_en_pasado(self):
        x={"a":np.asarray([1.,5.,np.nan,1000.]),"competicion":np.asarray(["PL","PL","CL","CL"])}
        encoder=Encoder().fit(x,["a","competicion"],[0,1])
        np.testing.assert_array_equal(encoder.transform(x,[2,3]),[[3,1,0,1],[1000,0,0,1]])
        self.assertEqual(encoder.levels["competicion"],["PL"])
        all_missing=Encoder().fit({"a":np.array([np.nan,99.])},["a"],[0])
        np.testing.assert_array_equal(all_missing.transform({"a":np.array([np.nan,99.])},[0]),[[0.,1.]])

    def test_early_stopping_excluye_externo_y_respeta_embargo(self):
        ids=np.arange(21)
        days=np.arange(27)+800000
        a,b=early_split(ids,days,config()["early_stopping"])
        self.assertLessEqual(days[a[-1]],days[b[0]]-2)
        self.assertEqual(b[-1],20)
        y=np.arange(len(days))%3
        model={"familia":"xgb","params":{"n_estimators":6,"max_depth":2}}
        x={"a":np.arange(len(days),dtype=float)}
        pipe,h=train(x,["a"],y,ids,days,config(),model)
        self.assertEqual(h["ajustes"],2)
        self.assertEqual(h["early_valid_max"],days[20])
        self.assertEqual(tuple(pipe.model.classes_),(0,1,2))
        np.testing.assert_allclose(pipe.predict(x,np.arange(21,27)).sum(axis=1),1)

    def test_filtro_de_variables_y_reserva(self):
        payload=f5.json.loads(f5.CONFIG.read_text(encoding="utf-8"))
        names=features(payload,payload["conjuntos"]["ampliado"])
        self.assertEqual(len(names),len(set(names)))
        self.assertFalse(set(names)&{"match_id","available_at","fecha_objetivo","fase_fuente","local_id"})
        for season in ("2025-26","2026-27"):
            sample={"match_id":"1","fecha_objetivo":season[:4]+"-09-01","temporada":season}
            with self.assertRaisesRegex(ValueError,"edición"):
                validate_index([sample],1)

    def test_elo_oof_y_ausencia_de_club(self):
        initial=[game(1,"2024-12-29"),game(2,"2024-12-30"),game(3,"2024-12-31"),
                 game(4,"2025-01-01"),game(5,"2025-01-02")]
        changed=[replace(r,result=2,goals=(0,4)) if r.key>=3 else r for r in initial]
        cfg={"K":20,"localia":55}
        a=causal_elo(initial,cfg)
        b=causal_elo(changed,cfg)
        self.assertEqual(a[1],(1500.,1500.,55/400))
        self.assertEqual(a[4],b[4])
        self.assertNotEqual(a[5],b[5])

    def test_meta_solo_oof_comun_y_pesos_validos(self):
        store={"A":{0:1,1:2,2:3,4:4},"B":{0:1,2:2,3:3,4:4}}
        ids=past_oof(store,np.arange(5),["A","B"],np.array([1,2,3,4,5]),3)
        np.testing.assert_array_equal(ids,[0,2])
        fixture=np.array([[[.7,.2,.1],[.6,.3,.1]],[[.2,.6,.2],[.2,.5,.3]],[[.1,.2,.7],[.1,.3,.6]]]*3)
        weights,meta,success=ensemble_fit(fixture,np.array([0,1,2]*3),7)
        self.assertTrue(success)
        self.assertAlmostEqual(weights.sum(),1.)
        self.assertTrue((weights>=0).all())
        self.assertEqual(tuple(meta.classes_),(0,1,2))

    def test_calibracion_ignora_validacion_posterior_al_corte(self):
        day_idx=np.arange(24)
        y=np.arange(24)%3
        p=np.array([[.93,.05,.02],[.35,.45,.2],[.64,.15,.21]]*8)
        options={"dias_validacion":8,"min_por_clase":2,"temperatura":[.5,3.],
                 "regularizacion_logistica_C":.25,"mejora_minima":0.}
        old=calibrator_choice(p,y,day_idx,20,options)
        other=y.copy()
        other[21:]=(other[21:]+1)%3
        new=calibrator_choice(p,other,day_idx,20,options)
        self.assertEqual((old[0],old[2],old[3]),(new[0],new[2],new[3]))
        np.testing.assert_array_equal(calibrate(old[0],old[1],p),calibrate(new[0],new[1],p))

    def test_offset_poisson_logaritmico_y_matriz(self):
        ids=np.arange(18)
        x={"a":np.arange(len(ids),dtype=float)}
        y=np.arange(len(ids))%3
        margin=np.full(len(ids),np.log(1.2))
        model={"familia":"xgb","params":{"n_estimators":6,"max_depth":2,"learning_rate":.1}}
        reg,_=train(x,["a"],y,ids,ids,config(),model,regression=True,offsets=margin)
        prediction=reg.predict(x,ids,margin)
        np.testing.assert_allclose(reg.predict(x,ids,margin+np.log(2)),2*prediction,rtol=1e-6)
        self.assertTrue((prediction>0).all())
        support={"max_goles":32,"cola_max":1e-8}
        parts=[(1.5,.9,-.02,.35),(1.2,1.1,0.,.65)]
        matrix=from_components(parts,support)
        w=outcome(matrix)
        projections=markets(w,matrix)
        self.assertAlmostEqual(w.sum(),1.)
        self.assertAlmostEqual((matrix.sum(axis=1)*np.arange(33)).sum(),.35*1.5+.65*1.2)
        self.assertAlmostEqual(projections["p_btts_no"]+projections["p_btts_si"],1)
        for i in range(5):
            self.assertAlmostEqual(projections[f"p_under_{i}5"]+projections[f"p_over_{i}5"],1.)
            if i:
                self.assertLess(projections[f"p_under_{i-1}5"],projections[f"p_under_{i}5"])
        with self.assertRaisesRegex(ValueError,"Masa fuera"):
            from_components(parts,{"max_goles":2,"cola_max":1e-8})
        with self.assertRaisesRegex(ValueError,"suman uno"):
            from_components(parts[:1],support)
        with self.assertRaisesRegex(ValueError,"fuera del contrato"):
            probability([[.5,np.nan,.5]])

    def test_hash_y_directorio_exclusivo(self):
        with TemporaryDirectory() as directory:
            target=new_run_dir(Path(directory)/"corrida")
            with self.assertRaises(FileExistsError):
                new_run_dir(target)
            path=target/"marca"
            path.write_bytes(b"experimental")
            check_hashes({path:f5.digest(path)})
            with self.assertRaisesRegex(ValueError,"SHA-256"):
                check_hashes({path:"cambio"})

    def test_evaluacion_distingue_1x2_de_distribucion_conjunta(self):
        support={"max_goles":32,"cola_max":1e-8}
        fixture=[
            replace(game(j,f"2022-09-0{j}","2022-23",j-1,score),x={"l_w10_n":"8","v_w10_n":"9"})
            for j,score in enumerate(((2,0),(1,1),(0,1)),1)
        ]
        e=SimpleNamespace(rows=fixture,cfg=config(),days=np.asarray([r.day for r in fixture]),
                          y=np.arange(3),goals=np.asarray([r.goals for r in fixture]),
                          support=support,fallback=defaultdict(dict))
        components=[(1.3,1.,.01,1.)]
        p=outcome(from_components(components,support))
        result=defaultdict(list)
        capture(e,"sintetico","bruta",{i:(p,components) for i in range(3)},result)
        capture(e,"sintetico","cal_1x2",{i:(p,None) for i in range(3)},result)
        market=[r for r in result["MERCADOS_F5"] if r["desglose"]=="total" and r["mercado"]=="p_over_15"]
        self.assertEqual([r["evaluable"] for r in market],[1,0])
        self.assertEqual(market[0]["positivos"],2)
        self.assertTrue(np.isfinite(market[0]["log_loss"]))
        self.assertIsNone(market[1]["log_loss"])
