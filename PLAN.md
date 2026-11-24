# Plan de desarrollo y criterios de aceptación

Fecha: 2026-11-24. Estado: **F1 aprobada, F2-A y F2-B abiertas, F3 y F4 experimentales aprobadas, F5 experimental autorizada, F6–F9 pendientes**. Presupuesto máximo: **$0 MXN**. Evidencia en [Informe F2](docs/INFORME_F2.md), [Informe F3](docs/INFORME_F3.md) e [Informe F4](docs/INFORME_F4.md).

Cada fase termina con explicación del método, resultados reales cuando correspondan, limitaciones, evidencias reproducibles y una solicitud de aprobación para la siguiente. Las condiciones siguientes son propuestas de aceptación, no resultados ya alcanzados. Una etapa puede finalizar con una conclusión negativa y conservarse como evidencia; eso no autoriza promover un modelo o iniciar otra fase.

## F1 — Arquitectura e investigación de fuentes

**Aprobada.** Arquitectura, estrategia de datos, controles estadísticos y organización de agentes.

Aceptación:

- Están presentes AGENTS, README, PLAN, registro de decisiones y documentos de arquitectura, fuentes, base de datos y riesgos.
- Los 15 módulos solicitados tienen responsabilidad y fase asignadas.
- Las fuentes distinguen cobertura anunciada de cobertura comprobada; incluyen coste, límites, restricciones y enlaces primarios fechados.
- El esquema permite reconstruir qué revisión era conocida al predecir; cuotas, resultados de 90 minutos y liquidación tienen semántica explícita.
- La ruta del piloto respeta el presupuesto propuesto de $0 MXN; alcance de competiciones/temporadas y calidad real siguen pendientes de comprobar, sin activar servicios de pago.
- Los diez requisitos ampliados quedan trazados a arquitectura, datos, metodología y criterios de fase en la matriz siguiente.
- El catálogo enumera candidatos estadísticos, ML e híbridos. Están definidos el nivel base, el avanzado, las variables, sus requisitos de calidad y los cortes T−24 h, T−3 h y T−60 min. Las fuentes gratuitas y de pago están comparadas por capacidad. El nivel avanzado tiene una ruta de habilitación posterior.
- No se ha implementado ingesta ni entrenado modelos.

**Puerta:** aprobación del usuario de F1 y de la ruta/presupuesto del piloto. Esta aprobación no aprueba los datos.

### Verificación de los diez requisitos de revisión

Todos están **incorporados al diseño**, no implementados ni validados con datos.

| Requisito | Especificación principal | Aceptación posterior |
| --- | --- | --- |
| 1. Multiobjetivo: acierto/multiplicador/Edge/EV/incertidumbre/riesgo | ARQUITECTURA y METODOLOGIA: vector, unidades y direcciones | F7: conservar seis dimensiones y restricciones, sin puntuación única implícita |
| 2. Frontera de Pareto | METODOLOGIA y BASE_DATOS: dominancia y persistencia | F7: comprobar no dominancia contra enumeración pequeña y estabilidad; F9: mostrarla |
| 3. Evaluación neutral 1X2/DC/Over/Under/BTTS | ARQUITECTURA y METODOLOGIA: catálogo y elegibilidad | F6: todos los mercados observados evaluados o rechazo motivado, sin sesgo por tipo |
| 4. Objetivos 5x/10x/15x/20x/30x/40x/custom | ARQUITECTURA y BASE_DATOS: configuración/retorno | F7: modo, tolerancia y factibilidad registrados; ninguna cuota fabricada |
| 5. Sensibilidad ±1/3/5 pp y escenarios estadísticos | METODOLOGIA y BASE_DATOS: estrés coherente | F8: cambio solicitado/efectivo, factibilidad y resultados por escenario |
| 6. Captura manual/CSV/Excel Draftea | ARQUITECTURA, FUENTES y BASE_DATOS | F2 si se autoriza el contrato de importación; F6: validación de ofertas reales aportadas, sin apuestas |
| 7. Historial de predicciones | BASE_DATOS y ARQUITECTURA: registro inmutable | F4–F6: fecha/hora/corte/modelo/probabilidades/cuotas/resultados enlazados |
| 8. Lesiones/sanciones sobre xG y rotaciones | METODOLOGIA y ARQUITECTURA: contrato condicionado | F3/F5: disponibilidad, cobertura, ablación e incertidumbre; deshabilitar si insuficiente |
| 9. Coherencia matemática | METODOLOGIA: complementos, sumas, inclusión, monotonicidad | F4/F5/F7: pruebas antes y después de calibrar/perturbar |
| 10. Referencias simples y mercado sin margen | METODOLOGIA y FUENTES | F4/F6: mismos cortes/partidos; sin cuotas completas declarar comparación no evaluable |

Las rutas figuran en [README](README.md). Los dictámenes favorables de ingeniería y validación independiente corresponden a la revisión anterior de estos diez requisitos. La ampliación de modelos y horizontes se registra por separado en [Decisiones técnicas](DECISIONES_TECNICAS.md).

## F2 — Ingesta piloto, limpieza y aprobación de datos

- **F2-A, dataset base.** Contraste independiente, actualización 2026/27, identidad y evidencia del perfil diario reconstruido. Puede obtener aprobación por separado si cumple los criterios vigentes. El dictamen de aceptación regular de F2-A sigue pendiente. F3 y F4 experimentales se rigen por ADR-025 y ADR-026.
- **F2-B, dataset avanzado.** Muestreo de fuentes autorizadas, disponibilidad prepartido, cuota persistente y mapeos. Dictamen actual no aceptado. Variables avanzadas deshabilitadas.

Los [dictámenes](docs/INFORME_F2.md) preservan sin rebaja los umbrales de cobertura y auditoría manual. 2025/26 sigue reservada.

Módulos 1 y 2. Responsable: ingeniería de datos; revisión: validación independiente.

Entregables: adaptadores autorizados, esquema físico y migraciones, diccionario, archivos brutos con manifiesto, dataset versionado, informe de cobertura y errores, informe de licencia y evidencia temporal. Empezar por una muestra estratificada por competición/temporada y casos difíciles antes de una descarga amplia.

Ruta propuesta: OpenFootball para históricos básicos; football-data.org Free para contraste donde tenga acceso; otros conjuntos gratuitos solo como ampliaciones justificadas. La capacidad de importación manual/CSV/Excel Draftea se diseñará/implementará en F2 únicamente dentro del alcance aprobado; ningún archivo de ofertas ni conector se crea en F1. Las ofertas reales aportadas se evaluarán en F6, después de validar el importador.

Aceptación propuesta:

- 100 % de filas aceptadas trazables a fuente, lote, hash y versión. Reejecutar una ingesta no crea duplicados.
- Cero claves huérfanas, duplicados canónicos no resueltos, equipos enfrentándose a sí mismos o goles inválidos en el conjunto aceptado. Las discrepancias se conservan en cuarentena y se cuantifican.
- Identidad, competición, temporada y marcador reglamentario completos en todos los partidos utilizados como etiquetas. Fecha/hora y disponibilidad cumplen el perfil temporal elegido; una hora desconocida no se rellena con medianoche ficticia.
- Cobertura objetivo de al menos 99 % de partidos finalizados elegibles por competición-temporada, frente a un calendario completo independiente y autorizado. Es un objetivo operativo propuesto: cualquier rebaja requiere alcance y aprobación explícitos. Informar denominadores y sesgos; no aplicar porcentajes a muestras incompletas como si fueran temporadas.
- Auditoría manual estratificada propuesta: 30 partidos por competición, repartidos entre temporadas, más todos los conflictos y casos especiales detectados. Exigir cero discrepancias críticas sin resolver en esa revisión; la muestra no certifica ausencia universal de errores.
- 100 % de variables habilitadas tienen regla de disponibilidad y linaje; cero accesos posteriores al corte en las pruebas temporales. Clasificar por separado evidencia verificable, reconstruida y desconocida.
- Informar faltantes y disponibilidad de las capacidades base y avanzadas por liga, temporada, horizonte y proveedor. Registrar qué evidencia habilitaría cada variable pendiente. Tratar una baja desconocida como dato faltante.
- Publicar matriz de cuotas completas y comparables para cada mercado, casa, línea y hora; no condicionar la calidad básica de resultados a comprar cuotas. Separar aprobación de resultados de aprobación de evaluaciones económicas.
- Para importación manual/CSV/Excel: campos obligatorios, zona horaria, esquema versionado, hash, idempotencia, selecciones exactas, evidencia, tipo de retorno y cuarentena de filas inválidas. No ejecutar fórmulas/macros ni admitir importes/retornos ambiguos como cuotas comparables. Registrar fechas de observación e ingesta por separado.
- Conjunto mínimo propuesto para desarrollo: cinco temporadas completas consecutivas por competición (dos iniciales de ajuste, dos de desarrollo walk-forward y una reserva final). Es un diseño inicial, no garantía de potencia estadística; revisar tamaño y disponibilidad antes de fijar los cortes. La temporada 2026/27 incompleta no se llama temporada completa.

**Puerta obligatoria:** el usuario aprueba el informe de calidad, versión/hash del dataset, restricciones, perfil temporal y variables habilitadas. Sin esto no se ajusta ningún modelo.

## F3 — Exploración, variables y protocolo de evaluación

**Autorización excepcional del usuario.** Se aprobó la entrega experimental de EDA y variables para los 7.720 candidatos de v3 con D−2 por objetivo. Los criterios de F2 siguen vigentes. La reserva 2025/26 y la edición 2026/27 quedan fuera de desarrollo. Los horizontes prepartido requieren verificación posterior. [Informe F3](docs/INFORME_F3.md) y [Protocolo aplicado en F4](docs/PROTOCOLO_VALIDACION_F3.md).

Módulo 3 y contratos previos de 8/9. Responsables: estadística e ingeniería de datos; auditoría: validación.

Entregables de F3. EDA de desarrollo, correlaciones, variables base con ventanas 5/10/20 y contratos del nivel avanzado. Prerregistrar métricas y cortes de los tres horizontes con partidos agrupados. Reservar el test final.

Aceptación:

- Cada variable tiene fórmula, unidad, ventana, población, denominador, instante de disponibilidad y política de faltantes.
- Todas las ventanas excluyen el propio partido y partidos cuyos resultados aún no se conocían; calendarios incompletos se reflejan en descanso/carga.
- Analizar dispersión de goles, empates, neutralidad, cambios de formato, ascensos y diferencias entre ligas; distinguir correlación descriptiva de dependencia predictiva y causalidad.
- Fechas exactas de ajuste, selección, calibración y prueba fijadas por calendario; todos los partidos simultáneos permanecen en el mismo bloque. Cualquier embargo responde al solapamiento real de etiquetas, no a un número arbitrario de filas.
- Congelar métrica primaria (propuesta: Log Loss 1X2), Brier, diagnóstico de calibración, presupuesto de búsqueda y regla de promoción antes del ajuste.
- Lesiones/suspensiones sobre xG y rotaciones: contrato de publicación, minutos/plantillas, reemplazos, objetivo y cobertura; deshabilitadas en el piloto básico si estos requisitos no se cumplen. No definir penalizaciones fijas sin estimación.
- Fijar referencia de titularidad, unidad e intervalo de impacto, indicador configurable desde 0.20 xG y umbral de rotación derivado de desarrollo. Documentar criterios de habilitación del nivel avanzado. Véase [Feature engineering](docs/FEATURE_ENGINEERING.md).

**Puerta:** aprobación de variables, EDA y protocolo.

## F4 — Referencias y modelos estadísticos

Autorización experimental registrada en ADR-026. El ajuste usa el snapshot congelado de F3 con D−2 y protege 2025/26. La configuración de selección se fijó en [CONFIG_F4.json](docs/CONFIG_F4.json) antes de ajustar.

El usuario aprobó F4 experimental en ADR-028. E2 quedó seleccionado para 1X2. P2 y DC2 presentan diferencias internas inciertas y se conservan sus resultados. [Informe F4](docs/INFORME_F4.md).

La revisión complementaria completó clasificación por clase, empate, cobertura por mercado y registros separados de probabilidades y etiquetas. E2 y la corrida original se conservaron. [Dictamen complementario](docs/REVISION_CIERRE_F4.md).

Módulos 4, 5, 6 y backtesting de desarrollo del 8. Responsable: estadística; auditoría: validación.

Entregables de F4. Frecuencias históricas, Poisson, Dixon-Coles, Elo secuencial y regresión logística multinomial regularizada. Predicciones fuera de muestra, cobertura y diagnósticos por cada corte evaluable.

Aceptación:

- Explicar qué estima cada modelo, cómo se ajusta y cuándo falla; registrar inicialización de equipos, restricciones de identificabilidad y regularización.
- Probabilidades no negativas y suma uno dentro de tolerancia numérica 1e−10; controlar masa truncada de marcadores, con objetivo propuesto de cola <1e−8 por partido o ampliar soporte.
- Dixon-Coles mantiene factores de corrección válidos y convergencia documentada. Elo se actualiza solo con resultados disponibles y tiene una transformación explícita a tres resultados si predice 1X2.
- Comparar modelos en los mismos partidos/cortes mediante Brier, Log Loss y calibración, con intervalos y análisis por liga/horizonte. Conservar resultados negativos; no seleccionar por ROI de desarrollo.
- Derivar 1X2, doble oportunidad, Over/Under y BTTS de una distribución compatible; comprobar sumas, complementos, inclusión y monotonicidad por línea. Registrar toda predicción con hora real de generación, corte histórico/prospectivo, versiones y distribución original, sin sobrescribirla después.

**Puerta:** aprobación del aprendizaje y de las referencias a conservar; un modelo que no mejora puede descartarse sin ocultar su evaluación.

## F5 — Machine Learning y calibración

Autorización experimental en ADR-028. Comparación y calibración sobre el perfil D−2 de desarrollo. [Prerregistro](docs/CONFIG_F5.json) y [protocolo F5](docs/PROTOCOLO_VALIDACION_F5.md).

Módulos 7 y 9. Responsable: ML; revisión: estadística y validación.

Entregables de F5. Comparación de XGBoost, LightGBM, Random Forest y Extra Trees con F4. Evaluar híbridos de tasas ML con Poisson o Dixon-Coles y ensembles de salidas compatibles. Registrar regularización, búsqueda de hiperparámetros interna, interpretación SHAP, importancia por permutación y calibración separada para cada horizonte.

Aceptación:

- Imputación, escalado, selección y ajuste se aprenden exclusivamente dentro del bloque de entrenamiento correspondiente.
- Hiperparámetros, ensembles y calibradores no ven etiquetas del bloque externo ni del test final; las predicciones usadas para calibrar son anteriores y fuera de muestra del modelo base.
- Evaluar modelo bruto y calibrado en el mismo bloque posterior; reportar diagramas de fiabilidad y tamaños por intervalo. No imponer isotónica con muestras escasas sin justificarlo.
- Comparar con F4 usando diferencias pareadas e incertidumbre. Promoción solo bajo regla fijada en F3; ausencia de mejora deja activa la referencia más simple.
- Documentar impacto de xG, lesiones y cuotas con ablaciones; separar modelo deportivo de modelo que incorpora precios.
- Comparar predicciones de xG/xGA y rotaciones con/sin disponibilidad de jugadores en los mismos bloques y medir incertidumbre, si se aprueban esos datos. Una asociación predictiva no autoriza afirmar causalidad. Las probabilidades calibradas deben conservar la coherencia necesaria para mercados relacionados.
- Comparar base y avanzado sobre partidos comunes y reportar cobertura de cada nivel en el universo elegible. Validar tasas positivas, corrección Dixon-Coles y coherencia de ensembles. Publicar intervalos de diferencias frente a referencias simples, estabilidad temporal y motivo de promoción o descarte.

**Puerta:** aprobación de candidatos y configuraciones congeladas.

## F6 — Mercados y backtest final

Módulos 8 y 10. Responsables: mercados y validación independiente.

Entregables: liquidación determinista, probabilidades implícitas/sin margen, Edge, EV y simulación histórica cronológica de selecciones simples. Se congela la estrategia antes de consultar el test final. Un benchmark con cierre posterior al corte se etiqueta como retrospectivo.

Aceptación:

- Cuotas conocidas al corte, no suspendidas ni caducadas según la política fijada, y coincidencia de casa, mercado, línea, periodo y reglas. Las etiquetas de cierre sin timestamp no certifican CLV ejecutable.
- `min_edge=0.06` y referencia registrados, junto con cada candidato aceptado/rechazado. EV después de costes; no optimizar el filtro usando el test final.
- Pruebas de ganancias, pérdidas, void/push y aplazamientos; liquidaciones parciales requieren implementación y validación específicas o exclusión del mercado.
- ROI, CLV y drawdown con fórmula, denominadores, exposición, muestra efectiva, intervalos y comparación temporal. Reportar «no evaluable» si faltan precios, reglas o información suficiente; publicar tasa de exclusión.
- Mantener capital disponible y exposición simultánea; no reutilizar capital pendiente. Agrupar liquidaciones simultáneas para que el drawdown no dependa del orden arbitrario de filas.
- Una sola evaluación final del candidato congelado; una modificación posterior exige otro periodo verdaderamente no observado o seguimiento prospectivo.
- Evaluar neutralmente todos los mercados observados del catálogo: 1X2, 1X/X2/12, Over y Under en cada línea y BTTS sí/no. Publicar universo, motivos de exclusión y tasas por tipo; no ocultar un lado por su rendimiento. Las líneas con push o liquidación parcial exigen contrato específico, o se registran como no evaluables.
- Comparar referencias simples y probabilidades de mercado sin margen en los mismos partidos/cortes y con igual tratamiento del precio. Para doble oportunidad derivar la referencia de 1X2 sin margen o de un contrato complementario válido, nunca normalizar 1X/X2/12 juntos.
- Enlazar cotización manual/importada Draftea y resultado posterior a cada predicción; conservar las versiones originales y separar revisión, backfill y predicción prospectiva. Un multiplicador de combinación no permite inferir cuotas individuales.

**Puerta:** revisión del resultado, incluso si es negativo. Aprobar esta etapa no autoriza apuestas reales.

## F7 — Dependencia y optimización de parlays

Módulos 11 y 12. Responsables: estadística, mercados y optimización.

Entregables: probabilidad conjunta, generador de candidatos, **optimización multiobjetivo y frontera de Pareto** sobre acierto, multiplicador, Edge, EV, incertidumbre y riesgo; preferencias configurables y comparador exhaustivo pequeño.

Aceptación:

- Sumar intersecciones de eventos sobre una misma distribución de marcadores para mercados de goles del mismo partido. Combinaciones incompatibles tienen probabilidad cero; eventos redundantes no inflan probabilidades.
- No construir una distribución conjunta de tres o más eventos únicamente a partir de correlaciones por pares. La dependencia entre partidos se justifica o se analiza mediante escenarios y límites.
- Cuota conjunta ofrecida y reglas observadas para evaluar EV económico; si faltan, mostrar análisis probabilístico/escenarios, sin ROI de parlays afirmado como histórico ejecutable.
- Restricciones configurables: número de selecciones, exposición por partido/equipo, solapamiento, pérdida y liquidez simulada. Permitir elegir ninguna combinación.
- Validar el optimizador contra enumeración completa pequeña y medir sensibilidad al error de probabilidad. Desarrollo sobre datos de desarrollo; confirmar en un periodo nuevo, no reutilizar el test final de F6 como prueba independiente de una estrategia nueva.
- Definir direcciones, unidades, riesgo/importe/horizonte común, intervalos y tolerancias de dominancia. No denominar frontera global a una aproximación heurística; guardar dominadores, candidatos, razones de exclusión y frontera aproximada cuando proceda.
- Configurar objetivos **5x, 10x, 15x, 20x, 30x, 40x y personalizados** sobre multiplicador bruto confirmado: mínimo, rango o cercanía con tolerancia explícita. Un objetivo no relaja Edge/riesgo ni crea una oferta inexistente. Informar «sin combinación elegible» si corresponde.
- Separar exploración probabilística sin cotización de frontera económica con las seis dimensiones evaluables. No usar cero como valor sustituto de Edge/EV/riesgo desconocidos. Comparar sensibilidad de pertenencia a la frontera.
- Calcular riesgo por método exacto/enumeración validada cuando sea posible; si requiere Monte Carlo pendiente de F8, etiquetar la frontera F7 como parcial hasta completar y aprobar esa dimensión, sin adelantar la fase.

**Puerta:** aprobación del modelo conjunto y del objetivo de optimización.

## F8 — Monte Carlo, sensibilidad y riesgo

Módulos 13 y 14. Responsable: optimización/riesgo; revisión: estadística.

Aceptación:

- Semillas, distribución conjunta, parámetros, número de simulaciones y criterio de parada registrados. Reutilizar un mismo resultado simulado por partido en todas las selecciones que lo comparten.
- Contrastar Monte Carlo con soluciones exactas disponibles; estimar su error numérico y aumentar simulaciones hasta una precisión preregistrada adecuada a la decisión. Cero aciertos simulados no implica probabilidad real cero.
- Separar simulación de resultados de incertidumbre de parámetros/modelo; más simulaciones no corrigen mala especificación.
- Escenarios conservador/central/optimista sobre probabilidades, precios, dependencia, faltantes y costes; escenarios fundamentados en intervalos/perturbaciones declaradas y coherentes, no probabilidades inventadas.
- Ejecutar estrés **±1, ±3 y ±5 puntos porcentuales** sobre eventos declarados y regenerar mercados desde la conjunta. Registrar magnitud solicitada, efectiva y factibilidad; separar estos choques de intervalos derivados de datos. Recalcular Edge/EV, cumplimiento del objetivo, elegibilidad y Pareto por escenario.
- Reportar distribución de rendimiento, drawdown, cola de pérdidas y probabilidad de agotar la banca simulada; estabilidad bajo escenarios adversos y exposición compartida.

**Puerta:** aprobación de interpretación y límites de riesgo.

## F9 — Dashboard e integración

Módulo 15. Responsable: visualización; revisión: todos los responsables de contratos.

Aceptación:

- Filtros de competición, temporada, horizonte y modelo; páginas de calidad, predicción, calibración, mercados, combinaciones y riesgo.
- Vista Pareto con las seis métricas y sus unidades, objetivos de multiplicador configurables, tabla neutral por mercado, panel ±1/3/5 pp y registro histórico de predicciones/resultados. Captura/importación Draftea con previsualización, errores y confirmación de datos locales, sin envío de apuestas.
- Toda cifra enlaza a dataset/modelo/configuración; mostrar instante de corte, vigencia de cuotas, incertidumbre, tamaño de muestra y alcance verificable/reconstruido.
- Interfaz completamente en español, distinción clara entre observado, estimado y simulado; estados honestos cuando falta información.
- Reproducibilidad desde entorno fijado y artefactos aprobados. Pruebas integradas de filtros y coherencia de totales; ningún mecanismo de apuestas reales.

**Puerta:** aceptación del dashboard y decisión separada sobre cualquier publicación externa.

## Registro de avance

| Fase | Estado | Evidencia/aprobación |
| --- | --- | --- |
| F1 | Aprobada | Autorización explícita del usuario registrada en ADR-021. |
| F2 | En curso | v3 intacta. Evidencia manual de CL 2026/27 y PL 2024/25. Integración incremental y pruebas sintéticas realizadas. Pendientes permisos de persistencia, pruebas agrupadas, actualización autorizada, cobertura independiente y revisión de cierre. |
| F3 | Aprobada en alcance experimental | EDA, X/y y protocolo. ADR-026. |
| F4 | Aprobada en alcance experimental | Informe y dictamen complementario. ADR-028. |
| F5 | Autorizada en alcance experimental | D−2 de desarrollo, sin cierre de F2 ni uso de la reserva. |
| F6–F9 | No iniciadas | Requieren sus respectivas aprobaciones. |
