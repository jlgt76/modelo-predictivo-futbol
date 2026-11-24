# Registro de decisiones técnicas

## ADR-028 — Aprobación de F4 y autorización experimental de F5

El usuario aprobó F4 experimental y autorizó F5 experimental el 24 de noviembre de 2026. El trabajo cubre modelos ML, híbridos, ensembles y calibración bajo D−2 reconstruido y el snapshot f3_base_v1, exclusivamente de 2021/22 a 2024/25. El presupuesto sigue en $0 MXN. Se conserva la selección E2 y la corrida de F4. F2-A y F2-B siguen abiertas. Quedan fuera las variables avanzadas, el acceso a las etiquetas reservadas y las predicciones operativas. F6 requiere autorización explícita posterior.

El [prerregistro F5](docs/CONFIG_F5.json) se fijó antes de ajustar con SHA-256 `ddc03df04afec3382342aa9ce053fd93a78a06f52bd2cff55ae7517fc2d26d63`. La auditoría F4 acredita la revisión de sus artefactos y su perfil experimental. Siguen pendientes la publicación prepartido verificable, los tres horizontes, la referencia sin margen, métricas económicas, suficiencia para detectar empates por argmax y el análisis con datos avanzados. La aprobación experimental de F4 conserva estos pendientes.

## ADR-027 — Revisión complementaria sin reajuste de F4 experimental

E2 permanece como elección congelada. El complemento se genera en un directorio nuevo a partir de las emisiones, calibradores y etiquetas archivados. Se registran de forma separada las probabilidades brutas con distribución de marcadores cuando procede, las emisiones 1X2 por temperatura y las etiquetas. La evaluación por clase y mercado documenta el desempeño interno y sus límites. La formulación Dixon-Coles conserva las tasas Poisson fijas al estimar rho. La corrida original, su informe y el prerregistro permanecen archivados. [Dictamen complementario](docs/REVISION_CIERRE_F4.md).

## ADR-026 — Aprobación de F3 y autorización experimental de F4

El usuario aprobó F3 experimental y autorizó F4 experimental el 24 de noviembre de 2026. El ajuste compara referencias, Poisson, Dixon-Coles, Elo y regresión logística multinomial usando exclusivamente los 7.720 partidos de desarrollo congelados en F3. Se conserva D−2 por objetivo y la reserva 2025/26. La edición 2026/27 queda fuera. F2-A y F2-B siguen abiertas y sus criterios de aceptación continúan vigentes. La autorización se limita a F4 experimental y requiere una nueva aprobación para F5.

Configuración fijada antes del ajuste en [CONFIG_F4.json](docs/CONFIG_F4.json), SHA-256 `75fcb37e9c11c6c88d18f55334db27a798cc94364dcfea377d45b209dd0742e0`.

Resultado de la ejecución. E2 quedó congelado tras la selección de desarrollo. En evaluación interna superó a B3 por 0,03548 de Log Loss 1X2 y sus diferencias pareadas frente a P2 y DC2 fueron inciertas. Los ajustes, el diagnóstico de calibración, los resultados negativos y la revisión independiente quedan disponibles para la puerta experimental. [Informe F4](docs/INFORME_F4.md).

## ADR-025 — Autorización experimental de F3

El usuario autorizó explícitamente F3 con los 7.720 candidatos de 2021/22–2024/25 en v3, en modo solo lectura y D−2 individual. Se mantiene el cierre de F2-A y F2-B pendiente y los requisitos originales vigentes. Se excluyen 2025/26 y 2026/27, quedan deshabilitadas las variables avanzadas y se separan X e y. Este permiso cubrió EDA, generación determinista de variables y propuesta de protocolo. La autorización posterior de F4 y del ajuste experimental figura en ADR-026. [Informe F3](docs/INFORME_F3.md).

## ADR-024 — Dictámenes independientes F2-A y F2-B

Se separan base y avanzado sin modificar los criterios vigentes. F2-A conserva v3 y documenta un contraste oficial de 9/9 en la última jornada de Bundesliga 2024/25. El contraste poblacional, frescura y cobertura siguen pendientes. F2-B añade control local persistente de cuota y comprobación de equipos y fecha para las correspondencias. Sus variables siguen deshabilitadas. La posible aprobación separada del base requiere evidencia y aprobación explícita. [Dictámenes](docs/INFORME_F2.md).

## ADR-023 — Integración condicionada de Football-Data.org y API-Football

**Estado propuesto y probado localmente.** Football-Data.org es candidato para 2026/27. API-Football aporta evidencia puntual de PL 2024/25 e informa acceso a las ediciones iniciadas en 2022, 2023 y 2024. La persistencia requiere evidencia de permisos de procesamiento y almacenamiento y crea una copia separada de v3. Los bloques históricos no acreditan `available_at`. La vinculación utiliza IDs externos con correspondencias revisadas. Las consultas agrupadas quedan condicionadas a una prueba real del plan Free. La reserva 2025/26 queda excluida de la ingesta candidata. La validación interna del avanzado se propone dentro de 2022/23–2024/25. Véanse [informe](docs/INFORME_F2.md) y [cobertura](docs/COBERTURA_F2.md).

## ADR-022 — Correcciones de auditoría, snapshot v3

Conservar v2 y publicar v3 con identidad canónica y aliases auditables. Aplicar 20 correcciones trazables fuera de la reserva y clasificar Nantes–Toulouse como abandono con resultado administrativo. Reservar 2025/26. Adoptar como propuesta de investigación un perfil diario reconstruido con margen mínimo de dos días, separado de disponibilidad verificable. Sigue pendiente el contraste autorizado de cobertura y sedes y la actualización de 2026/27 mediante una fuente admisible. Véase [Informe F2](docs/INFORME_F2.md).

## ADR-021 — Aprobación de F1 e inicio de F2

El usuario aprobó F1 y autorizó F2 para CL, PL, PD, BL1, SA y FL1, temporadas 2021/22 a 2025/26, con 2026/27 separada y $0 MXN de suscripciones. El piloto usa Python 3.14.5, biblioteca estándar y SQLite. La muestra de 24 filas precedió a la ampliación a 35 archivos y 11.413 revisiones. La identidad es provisional dentro de cada competición. Los datos carecen de evidencia de publicación histórica. Las claves gratuitas, el contraste y la revisión independiente de cierre siguen pendientes. Véase [Informe F2](docs/INFORME_F2.md). La aprobación del informe determina el paso a F3.

Fecha inicial: 2026-11-24. Los estados son **fijada por el usuario**, **propuesta**, **aprobada** o **sustituida**. Ninguna propuesta se convierte en aprobación por haber sido documentada.

## ADR-001 — Desarrollo por fases

**Estado:** fijada por el usuario al inicio de F1. Revisar y aprobar cada etapa antes de avanzar. Las autorizaciones posteriores están en ADR-021, ADR-025 y ADR-026. El cierre de calidad de F2 sigue pendiente.

## ADR-002 — Python y documentación en español

**Estado:** fijada por el usuario. Arquitectura y futuro cálculo en Python; documentación e interfaz en español. Versiones exactas de Python y dependencias se fijarán al implementar F2 tras comprobar compatibilidad, sin afirmar aquí que una versión sea la más reciente.

## ADR-003 — Monolito modular local

**Estado:** propuesta. Un paquete Python con adaptadores y contratos claros; evitar inicialmente servicios distribuidos. SQLite mantiene identidad, revisiones y catálogo; Parquet guarda datasets; DuckDB se incorpora opcionalmente para consultar snapshots cuando se justifique. PostgreSQL se reconsidera si aparecen escritores concurrentes, servicio multiusuario o escala que lo justifique. Contrapartida: se simplifica operación a cambio de serializar escrituras canónicas.

## ADR-004 — Separar resultados, enriquecimiento y cuotas

**Estado:** propuesta sustituida por ADR-013 en cuanto a prioridad y presupuesto. La versión inicial proponía evaluar una ruta contractual con football-data.org y The Odds API; se conserva este antecedente, sin autorizarlo. Se mantiene separar resultados, enriquecimiento y cuotas. Véase [evaluación de fuentes](docs/FUENTES_DATOS.md).

## ADR-005 — Historial de disponibilidad y revisiones

**Estado:** propuesta que implementa la prohibición de leakage del usuario. Separar hecho, disponibilidad, observación e ingesta; seleccionar revisiones a fecha de corte. El dato descargado hoy no adquiere una fecha de disponibilidad pasada por corresponder a un partido antiguo. Distinguir backtest verificable, reconstruido bajo supuestos y no evaluable.

## ADR-006 — Universo y horizonte

**Estado:** universo propuesto. UCL masculina y cinco grandes ligas masculinas. Objetivo de 90 minutos más descuento. Ventana inicial candidata de cinco temporadas completas consecutivas. Aprobar universo y fechas tras medir cobertura, incluidos rivales de UCL ajenos a esas ligas. ADR-020 amplía los horizontes.

## ADR-007 — Edge y valor esperado

**Estado:** umbral fijado por el usuario; referencia propuesta. `min_edge=0.06`, por defecto `edge_reference=implied_raw`, es decir, probabilidad calibrada menos `1/cuota_decimal`. Guardar además Edge sin margen. Filtrar también por EV neto positivo y calidad/vigencia del precio. Cambiar referencia o umbral implica una configuración nueva, sin optimizar retrospectivamente contra el test final.

Ampliación de diseño: esta fórmula directa corresponde a contratos binarios sin devoluciones. Registrar `edge_scope`, propuesto inicialmente como `selection`; reportar Edge de combinación cuando sea definible y exigir EV neto positivo conjunto. Pushes y pagos parciales usan las convenciones específicas de Metodología. El usuario fijó seis puntos porcentuales, no aprobó todavía esta propuesta de alcance.

## ADR-008 — Modelos y validación

**Estado:** validación cronológica fijada por el usuario; secuencia propuesta. Referencias simples, Poisson, Dixon-Coles y Elo antes de ML. Comparar Brier, Log Loss y calibración en los mismos cortes. Calibración y ajuste separados del test. ROI/CLV/drawdown condicionados a datos suficientes; ningún objetivo de rentabilidad se presenta como criterio garantizado.

Ampliación solicitada el 2026-11-24: comparar además con probabilidades de mercado sin margen en el subconjunto con mercados completos y cotizaciones contemporáneas; declarar no evaluable cuando falte evidencia. No dar acceso al cierre posterior a modelos prepartido.

## ADR-009 — Dependencia y parlays

**Estado:** prohibición de independencia dentro del partido fijada por el usuario; mecanismo propuesto. Usar la matriz conjunta de marcadores para sus mercados compatibles, y modelos/escenarios explícitos para dependencia entre encuentros. Cuota conjunta observada para EV de un producto real; el producto de cuotas individuales no sustituye una cotización de same-game parlay.

## ADR-010 — Sin ejecución de apuestas

**Estado:** fijada por el usuario. Solo análisis y carteras simuladas. No crear adaptadores de colocación de apuestas. No es una opción de configuración que pueda activarse accidentalmente.

## ADR-011 — Calidad por capacidad, no por fuente en bloque

**Estado:** propuesta. Aprobar datos por competición, temporada, campo y horizonte. Un conjunto puede servir para resultados de 90 minutos y ser inadecuado para lesiones históricas o CLV. Las variables no admisibles se excluyen; no se completan mediante supuestos presentados como observaciones.

## ADR-012 — Coordinación sin conflictos de escritura

**Estado:** fijada por el usuario. Asignaciones independientes y un propietario de escritura por archivo. En F1 se hicieron revisiones paralelas de fuentes, estadística y arquitectura de datos; el coordinador integró la documentación. Las fases posteriores deben conservar revisión independiente de validación.

## Aprobaciones pendientes

La evaluación técnica preliminar favorable del usuario **no es aprobación de F1 ni autorización de F2**. El mensaje posterior «sigue» continúa la revisión de F1.

| Puerta | Qué debe quedar registrado | Estado |
| --- | --- | --- |
| F1 → F2 | Mensaje del usuario, alcance, presupuesto, fuente/ruta y criterios aceptados | Pendiente |
| F2 → F3 | Informe de calidad, hash/versiones, perfil temporal, variables y exclusiones aprobadas | Pendiente |
| F3 → F4 experimental | Aprobación y alcance explícito de ajuste | ADR-026 |
| F4 → F5 experimental | Aprobación y alcance explícito, reserva intacta | ADR-028 |
| F5 → F6 y siguientes | Evidencias de fase y alcance explícito de la siguiente | Pendiente |

Las futuras decisiones deben añadir fecha, responsable, alternativas, motivos, consecuencias y referencia a la aprobación cuando corresponda. Las decisiones sustituidas se conservan enlazadas a su reemplazo.

## ADR-013 — Prioridad gratuita y presupuesto del piloto

**Fecha:** 2026-11-24. **Estado:** prioridad fijada por el usuario; presupuesto de $0 MXN en suscripciones propuesto por el usuario. **Responsable:** coordinación e ingeniería de datos. Sustituye la ruta principal de ADR-004: OpenFootball primero, football-data.org Free como contraste condicionado, StatsBomb separado y API-Football Free opcional. Los planes pagados quedan fuera del piloto. Consecuencia: no prometer historia enriquecida ni económica completa; reducir alcance con aprobación si falta cobertura. No se han creado cuentas ni descargado datos.

## ADR-014 — Multiobjetivo, Pareto y multiplicadores

**Fecha:** 2026-11-24. **Estado:** requisitos fijados por el usuario; definiciones de métricas propuestas en Metodología. **Responsable:** optimización + validación. Evaluar acierto, multiplicador, Edge, EV, incertidumbre y riesgo, conservar soluciones no dominadas y separar comparación de preferencias. Se sustituye la anterior propuesta de maximizar únicamente EV conservador. Objetivos 5x/10x/15x/20x/30x/40x/personalizados sobre retorno bruto normalizado, con modo y tolerancia configurables. No existe obligación de alcanzar un multiplicador si las restricciones lo impiden.

## ADR-015 — Neutralidad y coherencia de mercados

**Fecha:** 2026-11-24. **Estado:** fijada por el usuario. **Responsable:** estadística + mercados. Incluir 1X2, doble oportunidad, Over, Under y BTTS sí/no con los mismos filtros temporales/de calidad; soportar todas las líneas disponibles cuya liquidación esté validada. Registrar los no evaluables. Derivar probabilidades relacionadas de una conjunta coherente; contrastar referencias simples y sin margen sin tratar doble oportunidad como partición excluyente.

## ADR-016 — Estrés y escenarios fundamentados

**Fecha:** 2026-11-24. **Estado:** magnitudes fijadas por el usuario, construcción propuesta. **Responsable:** estadística + riesgo. Perturbar ±1/±3/±5 puntos porcentuales mediante redistribución válida sobre resultados conjuntos y registrar cambios efectivos/factibilidad. Separar estas pruebas de estrés de intervalos y escenarios obtenidos de incertidumbre estimada. Mantener los mismos escenarios, capital y horizonte al comparar candidatos.

## ADR-017 — Draftea y registro histórico

**Fecha:** 2026-11-24. **Estado:** captura manual/CSV/Excel y registro requeridos por el usuario; contrato de datos propuesto. **Responsable:** ingeniería de datos + mercados. Conservar oferta exacta, origen, hora de observación/ingesta, formato de momio, tipo de retorno, evidencia y reglas. Importación local no implica API/exportación oficial. Predicciones inmutables con `generated_at` y `decision_at`, versiones, probabilidades, cuotas y resultados posteriores enlazados. Promociones y contratos ambiguos no entran al MVP económico. No se realiza captura o importación en F1.

## ADR-018 — Lesiones, suspensiones, xG y rotaciones

**Fecha:** 2026-11-24. **Estado:** requisito condicionado a datos, fijado por el usuario. **Responsable:** datos + estadística + ML. Estimar cambios de xG/xGA y efectos predictivos de disponibilidad solo con historial admisible, sustitutos y contexto. Detectar rotaciones por conjuntos de titulares/minutos previos conocidos; distinguir previsto de confirmado. Validar por ablaciones temporales e intervalos; no usar penalizaciones fijas inventadas ni afirmar causalidad. Estas variables quedan inicialmente fuera de la ruta gratuita básica hasta aprobar su cobertura.

## Evidencia de revisión de esta ampliación

Los dictámenes del párrafo siguiente corresponden a la versión anterior a ADR-019 y ADR-020.

2026-11-24: se asignaron tareas separadas a ingeniería de datos y validación independiente para fuentes gratuitas. Tras interrupciones iniciales por límite de uso, **ambos agentes completaron sus revisiones documentales favorablemente**. Ingeniería revisó ruta gratuita, exclusiones, captura Draftea, historial y esquema; validación revisó fuentes, Pareto, sensibilidad, push, coherencia y plan. El coordinador integró los documentos y comprobó consistencia y 21 enlaces locales. No se encontraron hallazgos accionables; no se certifican calidad real, permisos pendientes o cobertura completa. La aprobación del usuario y F2 siguen pendientes.

## ADR-019 — Candidatos y niveles predictivos

**Estado fijado por el usuario.** Dos niveles complementarios y catálogo estadístico, ML e híbrido. La familia del estimador es independiente del nivel de datos. Los conjuntos avanzados se pueden habilitar después del piloto por competición, temporada y corte. Propuestas de diseño en [Metodología](docs/METODOLOGIA_Y_RIESGOS.md) y [Feature engineering](docs/FEATURE_ENGINEERING.md). La investigación de pago conserva el presupuesto inicial propuesto de $0 MXN y deja cualquier contratación para una decisión posterior.

## ADR-020 — Tres cortes y umbrales de contexto

**Estado fijado por el usuario.** T−24 h, T−3 h y T−60 min con evaluación y calibración separadas. El diseño agrupa emisiones de un mismo partido en el bloque externo y propone respaldos base por horizonte. Se fija un indicador configurable desde 0.20 xG de impacto estimado. La alerta de rotación queda parametrizada con umbral a determinar en desarrollo.

En esta ampliación se solicitó investigación al agente de ingeniería. Su ejecución se interrumpió por límite de uso y el coordinador integró la consulta de fuentes primarias. Validación aportó la restricción de Dixon-Coles con tasas variables antes de interrumpirse. La revisión independiente integral de esta versión queda pendiente.
