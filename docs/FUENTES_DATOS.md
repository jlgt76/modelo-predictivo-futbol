# Fuentes de datos históricas

Fecha de consulta documental: **2026-11-24**. Estado: propuesta de F1, pendiente de aprobación. No se crearon cuentas, contrataron servicios, ejecutaron llamadas autenticadas ni descargaron datasets. Los precios son los publicados en la fecha de consulta; no representan una oferta cerrada.

**Prioridad revisada por instrucción del usuario:** fuentes gratuitas y presupuesto inicial propuesto de **$0 MXN en suscripciones**. F2 no está autorizada. Se recomienda evaluar OpenFootball primero; los planes pagados de la comparación se conservan como referencia fuera del piloto, no como propuesta de contratación.

## Qué está comprobado y qué falta comprobar

Se distingue entre **verificado documentalmente** —lo que publica el proveedor— y **verificado con datos**, que requerirá el piloto F2. Ninguna fuente ha superado todavía nuestra auditoría de integridad, exactitud, identidad o disponibilidad temporal. Una competición listada no demuestra que todas sus temporadas, partidos o variables estén disponibles.

La cobertura objetivo propuesta es Champions League y las primeras divisiones masculinas de Inglaterra, España, Alemania, Italia y Francia. Se necesitan tres componentes separables: resultados/calendarios, enriquecimiento deportivo y cuotas. No se ha encontrado evidencia de una fuente gratuita única que garantice todas las variables solicitadas, las seis competiciones, un archivo continuo y sus versiones conocidas antes de cada partido.

## Comparación de fuentes

### football-data.org: complemento gratuito condicionado para contraste

| Aspecto | Evaluación documental |
| --- | --- |
| Cobertura | El catálogo incluye Champions League, Premier League, La Liga, Bundesliga, Serie A y Ligue 1. [Cobertura oficial](https://www.football-data.org/coverage). |
| Histórico y precio | Plan gratuito: 12 competiciones, resultados/calendarios con retraso y 10 llamadas/minuto. ML Pack Light: **€29/mes**, 10 temporadas, 20 llamadas/minuto. No atribuir esas diez temporadas al gratuito. Free + Deep Data: €29/mes y 30 llamadas/minuto, con alineaciones, sustituciones y plantillas. Complemento de cuotas prepartido 1X2: €15/mes. Puede aplicar IVA. [Precios](https://www.football-data.org/pricing). |
| Variables pendientes | No quedó acreditado xG, lesiones históricas ni archivo de cuotas con snapshots temporales. El plan histórico y el plan de datos ampliados son productos distintos: no asumir que sus características se acumulan por el mismo precio. |
| Condiciones | Registro y clave para una aplicación; atribución visible obligatoria y política de uso razonable. Los términos restringen referenciar los datos en un sitio o servicio después de cancelar. No se verificó una autorización contractual expresa de retención local perpetua o entrenamiento ML. El nombre del plan no sustituye esa comprobación. [Condiciones](https://www.football-data.org/about). |
| Papel propuesto | **Solo Free en el piloto de $0 MXN:** contraste de resultados/calendarios dentro de temporadas accesibles y permisos compatibles. No se ha acreditado que Free entregue cinco temporadas; el plan histórico y los complementos pagados quedan fuera del piloto. |

### API-Football: alternativa para resultados y enriquecimiento

| Aspecto | Evaluación documental |
| --- | --- |
| Cobertura | UCL y cinco ligas figuran en el catálogo. Debe verificarse la combinación competición/temporada/campo. [Catálogo](https://www.api-football.com/coverage). |
| Coste y límites | La página canónica muestra gratis **100 solicitudes/día**; Pro **USD16/mes**, 7.500/día; Ultra USD26/mes, 75.000/día; Mega USD36/mes, 150.000/día. Precios sin IVA. Los planes incluyen competiciones/endpoints, con temporadas limitadas en el gratuito. Se encontró también la variante `/pricing/` indexada con Pro a USD19: reconfirmar antes de contratar. [Precios canónicos](https://www.api-football.com/pricing), [variante publicada](https://www.api-football.com/pricing/). |
| Permisos | Prohíbe compartir cuentas y multiplicarlas para ampliar el plan gratuito. No concede derechos comerciales sobre las competiciones; pueden existir derechos de terceros. No se documentó aquí una garantía expresa de retención indefinida y entrenamiento. [Términos](https://www.api-football.com/terms). |
| Papel propuesto | **Solo Free, opcional:** probar campos/temporadas accesibles si F2 se aprueba; no se garantiza acceso al contexto de la temporada vigente ni histórico íntegro. No usar como archivo plurianual de cuotas. Pro y superiores quedan fuera del piloto. |

Limitaciones temporales verificadas en la [documentación v3](https://www.api-football.com/documentation-v3), secciones **Leagues**, **Fixtures → Lineups**, **Injuries** y **Odds (Pre-Match) → Odds**:

- El indicador de cobertura puede variar por temporada; un valor verdadero no garantiza integridad total.
- Alineaciones generalmente entre 20 y 40 minutos antes del partido; algunas competiciones las reciben después. Su existencia histórica no prueba que fueran conocidas en T−60 minutos.
- Lesiones desde abril de 2021; distingue baja y disponibilidad dudosa. No quedó acreditado un historial de cuándo se conoció cada revisión.
- Cuotas prepartido entre uno y catorce días antes, con actualización cada tres horas y **siete días de retención histórica**. Un parámetro `season` no implica archivo de cuotas antiguas.
- No quedó acreditada cobertura histórica estable de xG; comprobar campos y temporadas antes de habilitarlos.

### Sportmonks: alternativa futura fuera del presupuesto del piloto

| Aspecto | Evaluación documental |
| --- | --- |
| Datos | Publicita resultados, estadísticas, alineaciones, lesiones/suspensiones y xG mediante complemento. Las temporadas y campos exactos requieren el catálogo por liga y prueba autenticada. [Producto](https://www.sportmonks.com/football-api/), [cobertura](https://www.sportmonks.com/football-api/coverage/). |
| Coste | Starter: **€29/mes**, cinco competiciones, 2.000 llamadas por entidad/hora. Growth: €99/mes, 30 competiciones, 2.500/hora. Liga adicional desde €4/mes. Histórico anterior a tres temporadas: complemento desde €29, pago único. xG anunciado desde €24/mes promocional, frente a €29. No asumir que el precio mínimo cubre todas las ligas o el archivo completo. [Planes](https://www.sportmonks.com/football-api/plans-pricing/). |
| Alcance | UCL más las cinco ligas suma seis competiciones: Starter por sí solo no cubre el alcance. El presupuesto debe confirmar una liga adicional o un plan mayor. |
| xG | La FAQ sitúa el comienzo en la temporada **2024** y declara que no dispone de xG anteriores. Es una limitación para un historial enriquecido de cinco temporadas. Tampoco prueba la fecha de publicación de cada valor. [FAQ](https://www.sportmonks.com/faq/). |
| Cuotas | Ofrece cuotas y complementos, pero no quedó verificado un archivo plurianual con timestamps y condiciones suficientes para nuestro backtest. No equiparar “histórico de fútbol” a “histórico de cuotas”. |

Existe una discrepancia documental que debe resolverse antes de guardar datos de esta fuente: el artículo 6.2 de los [términos](https://www.sportmonks.com/terms-of-service/) exige consentimiento escrito para almacenamiento y otras formas de reproducción, mientras que [Integrity support](https://www.sportmonks.com/integrity-support/) declara permitido cachear datos en una base propia. Los términos también limitan la reventa y expresan precios sin IVA, salvo indicación distinta; la suscripción específica puede prevalecer sobre las condiciones generales. Registrar el permiso aplicable, incluido entrenamiento y conservación después de cancelar, antes de seleccionar este proveedor. No se contactó a Sportmonks.

### StatsBomb Open Data: investigación de eventos y xG

El repositorio oficial redirige actualmente a Hudl. Ofrece JSON de competiciones, partidos, eventos y alineaciones, además de datos 360 para una selección de partidos. El README contempla investigación y pide atribución a StatsBomb y su logo al publicar resultados. [Repositorio](https://github.com/hudl/open-data).

El catálogo contiene temporadas seleccionadas de UCL y ligas europeas; la presencia de una temporada no certifica que estén todos sus partidos. Auditar contra un calendario completo antes de usarlo para comparación entre equipos. [Catálogo](https://github.com/hudl/open-data/blob/master/data/competitions.json).

La documentación oficial muestra xG por disparo y su agregación. Para este proyecto, `xGA` significará **goles esperados concedidos**, no asistencias esperadas; conservar proveedor, definición, versión y periodo al agregar eventos. [Ejemplos oficiales de StatsBomb](https://blogarchive.statsbomb.com/uploads/2021/11/Working-with-R.pdf).

Coste de acceso al conjunto abierto: cero. La lectura íntegra de su [licencia PDF](https://github.com/hudl/open-data/blob/master/LICENSE.pdf) queda pendiente: el navegador no consiguió extraerla. No asumir permiso comercial irrestricto ni que el README reemplaza todas las condiciones. Propuesta: conjunto separado de aprendizaje/investigación, sujeto a licencia, sin usarlo como prueba de cobertura continua de las seis competiciones. No aporta cuotas ni un historial general de lesiones prepartido en la estructura descrita.

### football-data.co.uk: archivo útil, con restricciones de uso

Publica CSV de ligas nacionales, incluidas las cinco del alcance; su descripción anuncia resultados desde 1993/94 y cuotas desde 2000/01, con diferencias entre ligas/temporadas. Desde 2019/20 distingue cuotas previas y de cierre. No se identificó UCL en el catálogo ni xG, lesiones o alineaciones en la descripción. Desde el 23/07/2025 advierte desactualización de cuotas Pinnacle. Las columnas de cierre no acreditan por sí mismas el instante exacto de captura. [Descripción del archivo](https://football-data.co.uk/data).

La política actual permite usos particulares/académicos especificados mediante descarga manual o automatización ligera de hasta dos veces por semana, y excluye proyectos comerciales o de entrenamiento AI. No se interpreta “gratis” como licencia abierta ni como permiso para este proyecto ML. [Política de uso](https://football-data.co.uk/contact.php).

**Decisión propuesta:** no usarlo como fuente automatizada predeterminada. Cualquier uso deberá encajar en condiciones expresamente compatibles; si no, seleccionar otra fuente. No descargarlo para eludir esta limitación mediante una librería o espejo.

### The Odds API: histórico pagado fuera del piloto

| Aspecto | Evaluación documental |
| --- | --- |
| Plan | Gratis: 500 créditos/mes sin precios históricos. Primer plan con histórico: **USD30/mes**, 20.000 créditos. También aparecen USD59/100.000, USD119/5 millones y USD249/15 millones. UCL y cinco ligas están listadas. Los impuestos finales no quedaron acreditados. [Precios y cobertura](https://the-odds-api.com/). |
| Permisos | Los términos permiten almacenar y conservar indefinidamente, calcular valores derivados y entrenar modelos estadísticos/ML. Permiten aplicaciones analíticas, pero prohíben revender o redistribuir el feed como producto de datos independiente. No requiere atribución, aunque la aprecia. [Condiciones](https://the-odds-api.com/terms-and-conditions.html). |
| Papel propuesto | Histórico pagado fuera del piloto de $0 MXN. El nivel gratuito podría complementar una captura prospectiva limitada si se autoriza, pero no aporta precios históricos ni confirma cobertura de Draftea. No es dependencia obligatoria del piloto. |

El histórico de mercados principales usa snapshots cada diez minutos desde junio de 2020 y cada cinco minutos desde septiembre de 2022. El inicio publicado para PL, Bundesliga, Serie A y La Liga es **2020-06-06**; UCL **2020-07-10** y Ligue 1 **2020-07-16**. La clasificación de UCL tiene cobertura separada desde **2023-07-22**. Mercados adicionales comienzan desde mayo de 2023, según disponibilidad. La API devuelve el snapshot más cercano que no supera la fecha solicitada; guardar tanto ese instante como la actualización de la casa/mercado. El inicio del torneo no garantiza continuidad de cada casa o mercado. [Histórico y fechas iniciales](https://the-odds-api.com/historical-odds-data/).

La resolución de cinco minutos no acredita el último precio exacto anterior al inicio. Definir una tolerancia de antigüedad para CLV, registrar faltantes y rechazar snapshots posteriores al corte. Tampoco quedó verificada una cuota conjunta ofrecida de same-game parlay; no construirla multiplicando cuotas simples.

### OpenFootball: primera opción propuesta para históricos gratuitos

| Repositorio | Evidencia documental | Limitación |
| --- | --- | --- |
| [football.json](https://github.com/openfootball/football.json) | Licencia CC0; directorios de temporadas desde 2010-11 hasta 2026-27. Acceso público sin cuota de suscripción. | El árbol de carpetas no acredita cada liga completa ni campos uniformes. Auditar partidos y marcadores por competición/temporada. |
| [champions-league](https://github.com/openfootball/champions-league) | Licencia CC0; directorios observados desde 2011-12 hasta 2025-26. | No garantiza actualización hasta la temporada actual; formato y alcance requieren un adaptador propio y contraste de calendarios. |

La alternativa abierta sirve para estudiar resultados básicos si supera F2. No se ha acreditado aquí xG, lesiones, alineaciones o cuotas, ni un archivo de su disponibilidad histórica. La licencia permite reutilización, pero no certifica exactitud. Una fecha de commit registra una revisión del repositorio; no demuestra cuándo se publicó originalmente un resultado ni cuándo habría estado disponible para nuestro sistema.

## Captura manual y archivos de Draftea

Fuente propuesta de ofertas aportadas por el usuario: captura manual o importación de CSV/Excel local según nuestro contrato. No se ha verificado una API pública, exportación CSV/Excel oficial, archivo histórico completo ni catálogo gratuito de Draftea accesible al proyecto; no prometer esas capacidades. No se iniciará sesión, depositará dinero, contratará ni ejecutará apuestas para obtener datos.

La ayuda oficial describe el momio decimal como retorno total que incluye el importe inicial y explica que una combinación del mismo partido puede recotizarse, sin equivaler al producto de sus patas. Conservar siempre la oferta conjunta exacta, además del formato/base de retorno. [Explicación oficial de momios](https://help.draftea.com/support/solutions/articles/150000212083--c%25C3%25B3mo-funcionan-los-momios-).

Las reglas de fútbol definen por defecto 90 minutos más descuento, salvo indicación distinta, y contemplan combinaciones no aceptadas y anulaciones. Registrar la versión aplicable a cada oferta; una descripción general no reemplaza el contrato concreto. [Reglas de fútbol](https://www.draftea.mx/page/reglas-de-apuestas-futbol).

Registrar fecha/hora y zona, captura/archivo original, partidos/selecciones/líneas, tipo de retorno y reglas. Validar errores de transcripción, duplicados y promociones. Una hora declarada sin evidencia no demuestra disponibilidad histórica. Capturar también universo y descartados con un protocolo previo evita estudiar únicamente ofertas que parecían atractivas. Ver [contrato de importación](BASE_DATOS.md).

Sin coste de suscripción del proyecto para procesar archivos aportados; esto no presupone acceso, permisos de redistribución ni disponibilidad de la plataforma. Inicialmente mantener datos privados de análisis, sin divulgar archivos de terceros. Las capturas futuras construyen un historial prospectivo, no rellenan automáticamente cuotas pasadas ni permiten afirmar CLV sin observación de cierre comparable.

## Recomendación de fuentes para F2 con $0 MXN

**Ruta principal revisada:** auditar resultados/calendarios de OpenFootball y usar football-data.org Free solo para contraste dentro de lo accesible y autorizado. Conservar todos los huecos y discrepancias. Si no se pueden cubrir las seis competiciones/cinco temporadas, presentar un subconjunto menor para aprobación; no pagar ni completar datos ficticios. La ruta contractual de la versión anterior queda sustituida.

| Prioridad | Fuente propuesta | Qué se puede obtener sin suscripción de pago | Qué no queda garantizado |
| --- | --- | --- | --- |
| 1 | OpenFootball, repositorios de ligas y UCL | Resultados, equipos, competición, temporada y fechas disponibles en los archivos públicos CC0 | Horas exactas, versiones históricamente conocidas, cobertura completa por liga/año, enriquecimiento o cuotas |
| 2 | football-data.org Free | Calendarios/resultados/tablas del catálogo gratuito, con retrasos y límites publicados | Cinco temporadas, xG, bajas o cuotas; confirmar condiciones antes de incorporar y conservar datos |
| 3, separada | StatsBomb Open Data | Eventos/xG y alineaciones de partidos seleccionados, sujeto a licencia completa | Representatividad/continuidad de seis ligas, historial de lesiones o disponibilidad prepartido |
| 4, opcional | API-Football Free | Prueba de temporadas/campos permitidos bajo 100 solicitudes/día | Temporadas concretas, actualidad, campos completos y disponibilidad pasada; no prometer enriquecimiento hasta probar |
| Complemento prospectivo | Ofertas Draftea aportadas manualmente/CSV/Excel | Multiplicadores observados y reglas si el usuario dispone de ellos | Mercado exhaustivo, timestamps verificables, cierres, cuotas por pata o API/exportación oficial |

La información de acceso y permisos procede de las páginas primarias enlazadas en cada ficha. La prioridad es una recomendación de ingeniería, no certificación de datos: todavía no se inspeccionó ninguna muestra descargada. Se propone **$0 MXN en suscripciones** para todas las opciones del piloto; existen costes de trabajo y mantenimiento, sin cuantificarlos aquí. No usar pruebas gratuitas con conversión automática a pago. Un bloqueo de cuota se resuelve con espera, caché permitida o menor alcance, nunca comprando ni multiplicando cuentas.

### Qué habilitaría el primer modelo y qué queda excluido

| Variable/capacidad | Estado inicial propuesto | Límite |
| --- | --- | --- |
| Goles a favor/en contra y resultado 90 minutos | Habilitable tras QA y separación de prórroga/tanda | Marcadores incompletos/conflictivos en cuarentena |
| Localía/visita, forma 5/10/20 y fuerza histórica/Elo | Derivables después de aprobar datos y la fase de modelo | Neutralidad, rivales no cubiertos, historia corta y publicación incierta se declaran |
| Fechas y descanso | Fecha si está disponible; descanso solo cuando calendario completo/precisión lo permitan | Copas y otras competiciones faltantes invalidan descanso/carga completos |
| xG/xGA homogéneos para seis competiciones | **Excluidos del MVP básico** | StatsBomb seleccionado no representa un panel continuo; no sustituir xG con goles |
| Impacto de lesiones/suspensiones sobre xG | **Excluido inicialmente** | Sin historial admisible de estados, minutos/reemplazos y xG no se estima un efecto defendible |
| Alineaciones y detección/predicción de rotaciones | **Excluidas inicialmente** | Se requieren onces/plantillas/minutos históricos y publicación; dato posterior no sirve como predictor |
| Cuotas/multiplicadores históricos, Edge/EV y CLV | **No evaluables donde falten ofertas y reglas comparables** | Ni la fecha del partido ni un precio actual reconstruyen una oferta pasada |
| Referencia de mercado sin margen | Condicionada a mercado completo del mismo corte | No disponible a partir de un multiplicador conjunto aislado ni de cuotas DC solapadas |
| Optimización económica/Pareto completa | Condicionada a cuotas conjuntas, probabilidades validadas, incertidumbre/riesgo | Puede estudiarse diseño/probabilidades sin declarar una frontera comercial completa |

El primer modelo futuro sería una referencia y Poisson/Dixon-Coles con goles, localía y fuerza pasada sobre el subconjunto aprobado, con Elo como comparador/variable según protocolo. **No se entrenará en F2.** Sin evidencia de publicación histórica, su backtest será reconstruido y no una demostración de ejecución real a T−24h. No incorporará ajustes por noticias/bajas, ni justificará rentabilidad histórica, objetivos de 40x o calibración de todas las ligas por el solo hecho de existir resultados. Los horizontes finos se excluyen si falta precisión horaria.

## Referencia de coste fuera del piloto

Los precios pagados anteriores sirven solo para una decisión futura separada. No forman parte de la recomendación actual ni son requisito para aprobar resultados deportivos. Si el usuario modificara el presupuesto, se volverían a verificar condiciones, impuestos y cobertura antes de contratar.

Para el endpoint de cuotas históricas principales de The Odds API, el consumo publicado es:

`créditos = 10 × consultas de snapshots facturables × mercados × regiones`

Ejemplo **estrictamente hipotético de presupuesto**, sin partidos o cuotas reales: 100 consultas, tres mercados y una región consumirían 3.000 créditos. Una consulta por liga e instante puede contener varios eventos; no sustituir consultas por número de partidos indiscriminadamente. Endpoints históricos por evento añaden esa dimensión. Consultas de descubrimiento, reintentos facturables y otros endpoints deben presupuestarse aparte. [Reglas de consumo](https://the-odds-api.com/liveapi/guides/v4/).

## Disponibilidad temporal y compatibilidad de variables

Guardar para cada observación la fuente, versión, instante del hecho, publicación conocida, timestamp del proveedor e ingesta local, conforme a [Base de datos](BASE_DATOS.md). No rellenar una fecha histórica de disponibilidad a partir de la fecha del partido. Clasificar evidencia verificable, reconstruida y desconocida.

| Variable | Condición para habilitarla |
| --- | --- |
| Goles, localía y forma 5/10/20 | Marcador reglamentario y condición de local/visitante/neutral. Solo partidos terminados con resultado disponible antes del corte. |
| xG/xGA | Misma definición y proveedor o ajuste documentado; agregación del periodo correcto. Guardar revisiones. El xG del partido que se predice nunca es una variable prepartido. |
| Lesiones y sanciones | Fuente, estado y revisión conocida al corte. Un campo ausente no significa jugador sano. La baja que hoy aparece para un partido antiguo no prueba su anuncio previo. |
| Alineaciones y rotaciones | Separar previstas, confirmadas y observadas después. Auditar el instante de publicación en T−24 h, T−3 h y T−60 min. Una probable en T−3 h y una confirmada en T−60 min requieren evidencia propia. |
| Fortaleza del rival | Identidad entre torneos y actualización cronológica. Los rivales UCL fuera de las cinco ligas necesitan historial adicional o política de equipo sin suficiente información. |
| Descanso y carga | Calendario completo de cada club, incluidas copas y otras competiciones. Si falta, indicar que el descanso calculado es parcial. |
| Cuotas, Edge y CLV | Misma casa, mercado, periodo, línea y reglas; snapshot anterior al corte y antigüedad aceptada. Cierre exclusivamente como referencia posterior de evaluación. |

No mezclar xG de proveedores como si fueran la misma medida ni aceptar estadísticas acumuladas finales de temporada para reconstruir predicciones pasadas. Una fuente puede aprobarse para resultados y rechazarse para cuotas o variables sensibles al momento de publicación.

## Pruebas pendientes para F2

Estas comprobaciones comienzan solo después de aprobar F1 y el alcance del piloto; no se han ejecutado:

1. **Licencia y coste:** registrar condiciones/fecha y permisos de ingesta, persistencia, entrenamiento y publicación bajo $0 MXN. Leer íntegramente la licencia StatsBomb si se utiliza. Sportmonks y demás planes pagados quedan fuera del piloto; no activar sus pruebas con cargo posterior.
2. **Inventario real:** enumerar temporadas y campos accesibles por cada una de las seis competiciones. Contrastar al menos una temporada antigua y otra reciente antes de ampliar a la ventana completa de cinco temporadas propuesta en PLAN.
3. **Cobertura:** confrontar contra calendario independiente autorizado; contar esperados, observados, excluidos y faltantes. Separar clasificatorias UCL, fase principal, neutralidad, partidos aplazados, abandonados y adjudicados.
4. **Semántica de resultado:** comprobar 90 minutos más descuento frente a prórroga y penaltis; verificar participantes, fecha/hora, zona, temporada y duplicados. No convertir fechas incompletas en horas ficticias.
5. **Disponibilidad:** auditar revisión y publicación para cada variable/horizonte. Deshabilitar lo que no cumpla el perfil temporal aprobado y distinguir reconstrucción de captura contemporánea.
6. **Enriquecimiento:** medir faltantes y homogeneidad de xG, lesiones y alineaciones por competición/temporada. Confirmar calendarios adicionales para carga y contexto de rivales.
7. **Cuotas, cuando se autoricen:** probar cobertura por casa/mercado/línea/instante, retraso, margen completo y reglas de liquidación; verificar consumo frente al presupuesto. Reportar CLV o ROI no evaluables si no hay evidencia suficiente.
8. **Reproducibilidad:** guardar archivos brutos autorizados, hashes, manifiestos, identificadores y revisiones; comprobar idempotencia, trazabilidad y cuarentena. Aplicar los criterios cuantitativos de [F2 en PLAN](../PLAN.md).

El entregable será un informe de calidad con evidencia real y una recomendación de aceptar, limitar o rechazar cada fuente. La selección documental actual no autoriza entrenar modelos ni constituye aprobación de los datos.

## Cobertura documental para habilitar el nivel avanzado

La matriz agrupa las diez capacidades solicitadas. «Por verificar» indica que el plan exacto, temporadas, completitud o archivo de revisiones requieren evidencia adicional. xGA se deriva de xG rival en el mismo partido, periodo y versión. La base de datos de eventos puede permitir reconstruir minutos y formaciones iniciales si los eventos y las sustituciones son completos.

| Fuente | Resultados / calendario | Estadísticas partido / jugador | xG / xGA | XI histórico / minutos / formación | Lesiones / sanciones | Cuotas históricas / actuales |
| --- | --- | --- | --- | --- | --- | --- |
| OpenFootball CC0 | Candidato principal. Cobertura y semántica por auditar | Sin cobertura acreditada | Sin cobertura acreditada | Sin cobertura acreditada | Sin cobertura acreditada | Sin cobertura acreditada |
| football-data.org Free y pago | Free en las seis competiciones. Profundidad por verificar. ML Pack Light anuncia diez temporadas | Estadísticas de partido mediante complemento. Rendimiento individual integral sin acreditar | Sin cobertura acreditada | Deep Data publica XI y sustituciones. Minutos y formaciones por verificar | Sin archivo acreditado | 1X2 prepartido en complemento. Archivo temporal por verificar |
| StatsBomb Open Data / Hudl comercial | Identidades, fechas y resultados en selección abierta. Universo comercial por cotizar | Eventos por partido y jugador. Agregados derivados con cobertura | Por disparo. xGA derivable | XI y eventos. Minutos/formación cuando consten los eventos necesarios | Archivo prepartido sin acreditar | Sin cobertura acreditada |
| API-Football Free y pago | Calendarios/resultados. Free limita temporadas | Endpoints por partido y jugador | Campos y continuidad por verificar | XI, formación y estadísticas individuales con minutos según cobertura | Endpoint de lesiones. Sanciones, temporadas y revisiones prepartido por verificar | Actual y retención prepartido breve. Sin archivo plurianual acreditado |
| Sportmonks y complementos | Calendarios/resultados. Histórico extenso como complemento según plan | Estadísticas de equipo y jugador según cobertura | Complemento por equipo y jugador. xGA derivable | XI, formación y detalle por jugador. Minutos y profundidad por auditar | Documenta bajas por lesión y suspensión. Historial de publicaciones por verificar | Cuotas según producto. Continuidad e instante de observación por verificar |
| Opta / Stats Perform, comercial | Alcance por cotizar | Eventos y seguimiento individual según producto | xG documentado. xGA derivable | Pedir XI, minutos y formación por edición | Pedir revisiones fechadas y cobertura | Pedir oferta específica si corresponde |
| The Odds API | Eventos de mercado y horarios. El resultado deportivo se valida aparte | Fuera de alcance | Fuera de alcance | Fuera de alcance | Fuera de alcance | Actual y snapshots históricos en planes pagados. Auditar casa, mercado y corte |
| Draftea, aportación del usuario | Cruce con partido canónico | Fuera de alcance | Fuera de alcance | Fuera de alcance | Fuera de alcance | Captura manual prospectiva. Histórico solo si el usuario aporta evidencia verificable |

El catálogo y los costes de los planes gratuitos y de pago figuran en las fichas anteriores. Para Hudl StatsBomb y Opta, el coste aplicable sigue **por cotizar**. Sus páginas acreditan datos de eventos y xG. Una propuesta comercial debe enumerar derechos de almacenamiento y entrenamiento, profundidad, cobertura histórica y fechas de publicación por campo. [Documentación de eventos de Hudl](https://support.hudl.com/s/article/filter-event-data-statsbomb?language=en_US), [Opta Vision](https://www.statsperform.com/products/opta-vision/), [definiciones Opta de xG](https://www.statsperform.com/opta-event-definitions/).

Sportmonks distingue alineaciones y formaciones confirmadas de previstas y describe bajas por lesión o sanción. Publica un complemento de onces probables sobre Growth y Pro. La vista anual consultada muestra €159 por mes con pago anual e IVA aparte. Confirmar el importe del contrato y si conserva cada revisión previa al encuentro. La respuesta posterior al partido podría contener la alineación final aunque una probable distinta estuviera publicada en T−3 h. [Guía oficial de alineaciones](https://docs.sportmonks.com/v3/tutorials-and-guides/tutorials/lineups-and-formations), [complemento y modalidad de precio](https://www.sportmonks.com/football-api/expected-lineups-api/), [xG por equipo y jugador](https://www.sportmonks.com/blogs/how-to-use-xg-data-with-sportmonks-football-api/).

Para convocatorias, entrenadores y contexto competitivo, considerar publicaciones oficiales de clubes y organizadores con fecha verificable. Evaluar licencia, estabilidad y representatividad antes de sistematizar su uso. Derivar las condiciones de clasificación con reglas y tabla conocidas en el corte. Una lesión o sanción histórica describe el estado deportivo. Debe acreditarse aparte el momento en que ese estado se conoció.

### Ruta de ampliación posterior al piloto

1. Conservar OpenFootball y el contraste gratuito como ruta del nivel base con **$0 MXN propuestos**.
2. Evaluar StatsBomb abierto como muestra acotada de eventos y xG, API-Football como candidato de contexto y Sportmonks o un proveedor comercial de eventos si hace falta continuidad. Cotizar y decidir por capacidad, sin contratación en esta fase.
3. Antes de habilitar un bloque avanzado, solicitar documentación o muestras autorizadas de cobertura por liga, temporada y campo. Medir por horizonte cobertura, publicación, demora, correcciones, permisos, completitud de minutos y enlaces jugador/club. Medir sesgo de cobertura por equipo. Pedir ejemplos de una alineación probable sustituida por la confirmada y de una lesión corregida.
4. Si el archivo de revisiones históricas no existe, diseñar captura prospectiva bajo permisos y aprobación. Mantener la variable pendiente hasta contar con historial suficiente y evaluar el incremento frente al modelo base en los mismos cortes.

## Revisión de ingeniería de datos de la versión anterior

El agente de ingeniería completó la revisión en un reintento después de una interrupción por límite de uso. **Dictamen documental favorable**: ruta gratuita condicionada a cobertura, exclusiones iniciales, identidad/revisiones/disponibilidad, importación Draftea y registro histórico coherentes. Confirma OpenFootball como candidato principal CC0 sujeto a auditoría; football-data.org Free no demuestra cinco temporadas y API-Football Free no garantiza todas las temporadas/campos requeridos. El dictamen no certifica datos reales, licencias pendientes, cobertura completa ni factibilidad de multiplicadores. No autoriza F2.

## Revisión de validación independiente de la versión anterior

La revisión específica de esta ampliación fue completada en un reintento después de una interrupción por límite de uso de agentes. **Dictamen documental favorable, sin hallazgos accionables**: la ruta de $0 MXN separa licencia/cobertura de disponibilidad histórica, excluye enriquecimiento no defendible y condiciona correctamente la evaluación económica. También revisó coherencia, Pareto, sensibilidad y trazabilidad al plan. Este dictamen corresponde a la versión ampliada; no certifica calidad de datos, no implica aprobación del usuario y no autoriza F2. No se descargaron datasets.
