# Sistema predictivo de fútbol

**F1 aprobada. F2 en curso con $0 MXN en suscripciones.** Los resultados, la reproducción del piloto y los pasos de contraste están en [Informe F2](docs/INFORME_F2.md).

Diseño de un sistema Python para estimar distribuciones de resultados, contrastar probabilidades con mercados y estudiar combinaciones de parlays con dependencia y riesgo explícitos.


## Alcance inicial propuesto

Champions League y primeras divisiones masculinas de Inglaterra, España, Alemania, Italia y Francia: Premier League, LaLiga, Bundesliga, Serie A y Ligue 1. La categoría masculina es una propuesta de alcance, modificable antes de la ingesta. La cobertura de rivales de Champions fuera de estas ligas debe declararse y ampliarse cuando sea necesaria.

El sistema estimará probabilidades de **1X2, doble oportunidad, Over, Under y BTTS sí/no** sobre 90 minutos más descuento. Emitirá una predicción inicial en **T−24 h**, actualizará convocatorias, bajas y onces probables en **T−3 h**, e incorporará onces confirmados, rotaciones y cuotas disponibles en **T−60 min**. Cada horizonte tendrá calibración y evaluación propias.

El proyecto es de análisis y simulación. No ejecutará apuestas reales ni prometerá rentabilidad.

## Documentación para revisar

| Documento | Contenido |
| --- | --- |
| [Plan por fases](PLAN.md) | Entregables, criterios de aceptación y aprobaciones |
| [Arquitectura](docs/ARQUITECTURA.md) | Capas Python, contratos, módulos y flujo |
| [Fuentes de datos](docs/FUENTES_DATOS.md) | Cobertura, precios publicados, restricciones y verificaciones pendientes |
| [Base de datos](docs/BASE_DATOS.md) | Entidades, claves, revisiones y disponibilidad temporal |
| [Metodología y riesgos](docs/METODOLOGIA_Y_RIESGOS.md) | Validación, fórmulas, incertidumbre y controles |
| [Feature engineering](docs/FEATURE_ENGINEERING.md) | Variables base y avanzadas, fórmulas, umbral de 0.20 xG y condiciones de habilitación |
| [Decisiones técnicas](DECISIONES_TECNICAS.md) | Decisiones fijadas por el usuario y propuestas por aprobar |
| [Reglas para agentes](AGENTS.md) | Alcance autorizado y coordinación |

## Propuesta técnica

Monolito modular Python: archivos brutos inmutables, SQLite como registro canónico, Parquet para conjuntos analíticos y DuckDB opcional como motor de consulta sobre esos archivos. Interfaz local futura con Streamlit. Ninguna de estas dependencias se ha instalado en F1.

Separar resultados históricos básicos, datos enriquecidos y cuotas. Comenzar con un piloto de calidad de seis competiciones, condicionado a la licencia y a la cobertura real. La fuente principal se seleccionará después de la revisión documental y antes de la descarga. No se exige disponer de xG, lesiones y alineaciones para comenzar un modelo básico; sí se exige declarar su ausencia y aprobar ese alcance reducido.

La selección futura de combinaciones comparará **acierto, multiplicador, Edge, EV, incertidumbre y riesgo mediante una frontera de Pareto**. Tendrá objetivos 5x, 10x, 15x, 20x, 30x, 40x y personalizados; un objetivo puede no tener solución admisible. Se probarán perturbaciones de ±1/±3/±5 puntos porcentuales y escenarios estadísticos coherentes. Las probabilidades de mercados relacionados se derivarán de una distribución compatible.

El diseño incluye captura manual/importación CSV o Excel de ofertas de Draftea y un historial inmutable de predicciones y evaluaciones posteriores. No presupone una exportación oficial de Draftea ni automatiza apuestas. Lesiones, suspensiones sobre xG y detección de rotaciones quedan condicionadas a evidencia y calidad suficientes.

## Ruta gratuita recomendada y límites iniciales

Se propone **OpenFootball** como primer candidato para resultados históricos, y **football-data.org Free** para contraste/calendarios dentro de sus temporadas y permisos accesibles. StatsBomb Open Data queda como conjunto separado de investigación, sujeto a licencia y cobertura; API-Football Free es un candidato opcional de prueba, no un archivo histórico completo confirmado. Véanse enlaces y alcance verificado en [Fuentes](docs/FUENTES_DATOS.md).

El **modelo base** incorpora goles, localía, ataque y defensa, forma 5/10/20, Elo, rivales y rendimiento por competición. Descanso y carga se habilitan con cobertura suficiente. El **avanzado** incorpora xG/xGA y contexto de jugadores, técnico, formaciones y clasificación. Se incorporará por bloques cuando exista evidencia temporal, cobertura suficiente y aprobación del conjunto. La ruta gratuita inicial puede habilitar primero el modelo base.

Los candidatos incluyen **Poisson, Dixon-Coles, Elo, regresión logística, XGBoost, LightGBM, Random Forest y Extra Trees**, además de híbridos de tasas de ML con Poisson o Dixon-Coles y ensembles compatibles. La promoción se basa en comparación cronológica fuera de muestra con referencias simples, calibración e incertidumbre. La interpretación incluirá importancia de variables y SHAP.

El primer modelo sería retrospectivo y limitado al subconjunto aprobado; los históricos gratuitos no prueban por sí solos lo que se sabía antes de cada partido. Sin precios comparables, la referencia de mercado sin margen, Edge, EV, ROI y CLV quedarán no evaluables para esas filas. Las capturas manuales futuras construirían un archivo prospectivo; no completan el pasado ni garantizan rentabilidad.

## Decisiones que deberá confirmar el usuario

La aprobación de F1 debe indicar alcance, horizonte, ruta gratuita y criterios del piloto bajo el presupuesto propuesto de $0 MXN. No se recomienda contratar ningún servicio en este piloto. Si la cobertura gratuita no alcanza, se documentará un alcance menor o una limitación pendiente de aprobación, sin cambiar automáticamente el presupuesto.

La siguiente etapa sería **F2: piloto de ingesta y auditoría de calidad**, sin entrenamiento. Su entrega será un informe con datos reales y un conjunto versionado admisible. Solo una aprobación explícita de esa calidad permitirá avanzar a F3.

## Cómo reproducir esta fase

Leer los documentos anteriores y seguir sus enlaces primarios, consultados el 2026-11-24. Los precios describen lo publicado por el proveedor en esa fecha; no constituyen una compra ni un presupuesto cerrado. No hay comandos de ejecución del modelo porque su implementación todavía no está autorizada.
