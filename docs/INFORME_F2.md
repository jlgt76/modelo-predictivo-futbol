# Informe de ingesta y calidad de F2

## Dictamen F2-A — Dataset base

**No aceptado todavía para avanzar a F3.** v3 es admisible como insumo de auditoría y para comprobar la mecánica de reconstrucción diaria. El modelo base puede obtener aprobación independiente del avanzado cuando satisfaga sus propios criterios y el usuario apruebe su alcance. En esta revisión aún faltan esas evidencias.

| Criterio vigente | Dictamen y evidencia |
| --- | --- |
| Linaje e integridad | Cumplido en v3. Los 35 archivos brutos referenciados existen y coinciden con sus hashes. SQLite respondió `ok`, sin referencias huérfanas, autorreferencias ni claves canónicas repetidas. Hash de v3 conservado. |
| Identidades, fechas y marcadores reglamentarios independientes | Parcial. Los nueve partidos de la jornada 34 de Bundesliga 2024/25 coinciden en pareja, fecha y marcador con la liga oficial. Se mantienen las correcciones y los ejemplos de prórroga/tanda ya auditados. Quedan identidades externas, otras competiciones y casos especiales por contrastar. |
| Cobertura mínima de 99 % por competición-temporada | No demostrada. La coincidencia 9/9 corresponde a una única jornada. Los recuentos históricos agregados no sustituyen denominadores independientes ni el cotejo de partidos elegibles. |
| Auditoría manual de 30 por competición y resolución de casos críticos | Incompleta. La discrepancia de identidad observada en OpenLigaDB para Champions no es admisible. Quedan comprobaciones de neutralidad y otras eliminatorias. |
| Actualización de las seis competiciones en 2026/27 | Incumplida. v3 sigue al 20/09/2026 en las cinco ligas y sin filas de Champions de esa edición. Hay fuentes candidatas más recientes y ninguna se fusionó en esta revisión. |
| Perfil reconstruido D−2, reserva y perfiles estrictos | D−2 preparado para auditoría de base. A fecha de referencia 03/06/2025 devuelve 7.720 candidatos hasta 01/06/2025. Excluye 2025/26, 2026/27, filas sin marcador y partidos ambiguos con varias revisiones. D−2 es un supuesto por fecha calendario, mantiene `available_at` desconocido y no valida T−24 h, T−3 h ni T−60 min. |

Evidencia reproducible en [auditoría de v3](AUDITORIA_BASE_F2.json). Fuente independiente de la muestra histórica. [Jornada 34 oficial](https://www.bundesliga.com/en/bundesliga/matchday/2024-2025/34).

**Prioridad 2026/27.** OpenLigaDB ofrece datos bajo ODbL 1.0. Su política permite uso, copia, modificación y almacenamiento interno y distingue los modelos calculados de la publicación de una base derivada. Aplican atribución y condiciones de redistribución. Conviene mantener la fuente separada hasta decidir publicación. La API es gratuita y pide contacto en el User-Agent, caché y consultas espaciadas. La comprobación de esta revisión usó páginas públicas puntuales. La fuente comunitaria carece de snapshots históricos públicos. [Licencia](https://www.openligadb.de/en/license) · [Condiciones](https://www.openligadb.de/en/terms-of-use).

| Competición | Siguiente contraste y decisión de incorporación |
| --- | --- |
| Bundesliga | Primera candidata abierta. Jornada 10 de OpenLigaDB tiene nueve partidos finalizados del 20 al 22 de noviembre. El calendario oficial coincide en los nueve cruces y el 1–1 Bayern–Köln se verificó también en la crónica oficial. Cotejar cada marcador restante y el calendario completo antes de usar una versión candidata. [OpenLigaDB](https://www.openligadb.de/Matches/bl1/2026/10) · [DFL, calendario](https://products.bundesliga.com/fixtures/export/pdf?league%5B0%5D=1d570dd9-b10b-44de-9f64-8c91e56bf168&matchday%5B0%5D=10&season=b2f90c16-d6ef-40b1-a974-e6b1bf102c2a) · [DFL, resultados y onces](https://www.bundesliga.com/en/bundesliga/news/team-news-line-ups-2026-27-bayern-dortmund-fantasy-20707) |
| Champions | Conservar los 144 partidos y 72 finalizados comunicados manualmente desde Football-Data.org como evidencia agregada. OpenLigaDB registra Excelsior–Villa donde UEFA publica Barcelona–Aston Villa. Rechazar esa correspondencia. Priorizar el cotejo UEFA y habilitar almacenamiento de otra fuente solo con permiso acreditado. [OpenLigaDB](https://www.openligadb.de/Matches/ucl/2026/4) · [UEFA](https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures-a/) |
| Premier League | OpenLigaDB lista diez cruces de la jornada 11 y advierte resultados incompletos en los diez. Útil como contraste parcial de calendario. Priorizar Football-Data.org Free cuando se verifiquen permisos. [Jornada 11](https://www.openligadb.de/Matches/pl/2026/11) |
| LaLiga, Serie A y Ligue 1 | No se verificó alternativa abierta anual con resultados actuales y cobertura suficiente. Priorizar consultas específicas a Football-Data.org Free y verificar uso y almacenamiento antes de incorporar. Usar centros oficiales como contraste manual, con licencias de reutilización independientes. |

## Dictamen F2-B — Dataset avanzado

**No aceptado. Variables avanzadas deshabilitadas.** Continúa vigente la evidencia manual de seis celdas de 132. Las otras 126 requieren verificación. La presencia puntual de xG, onces y datos individuales no demuestra cobertura por temporada ni publicación prepartido. Las pruebas de software no hacen admisibles esos datos.

- El integrador conserva un contador SQLite separado por proveedor en una ventana móvil de 24 horas y registra el intento antes de abrir la conexión mediante una transacción inmediata. Las políticas locales son 12 solicitudes para Football-Data.org y 90 para API-Football dentro de esa ventana. Son márgenes operativos, no cuotas anunciadas ni límites de aceptación de cobertura. Una lectura de caché consume cero intentos y un fallo de red consume uno. Un 429 persiste la pausa indicada cuando es numérica o bloquea 24 horas cuando falta una duración interpretable. El registro solo incluye proveedor y tiempo. No conoce llamadas manuales ni de otros programas, por lo que sigue siendo necesario comprobar el saldo del plan.
- Las equivalencias de partido exigen evidencia revisada, coincidencia de edición, dos equipos canónicos vinculados y en el mismo orden, y una fecha UTC compatible con una revisión de v3. Una reprogramación o diferencia de zona queda para revisión. La tanda de mappings se aplica atómicamente. No se insertaron datos de proveedores.
- [Wyscout/Pappalardo](https://figshare.com/collections/Soccer_match_event_dataset/4415000/2) documenta eventos, once, banca, sustituciones y entrenador de las cinco ligas nacionales en 2017/18. Las fichas de [eventos](https://figshare.com/articles/dataset/Events/7770599) y [partidos](https://figshare.com/articles/dataset/Matches/7770422) indican CC BY 4.0, que permite copia y adaptación con atribución y declaración de cambios. Los minutos podrían derivarse con controles. El xG tendría que estimarse. No cubre las ediciones objetivo ni bajas prepartido verificables.
- [SkillCorner](https://github.com/SkillCorner/opendata) ofrece una muestra de diez partidos de A-League 2024/25 con seguimiento, eventos y onces. Útil para estudiar estructuras y contratos, fuera del universo de clubes requerido. [SoccerMon](https://datasets.simula.no/soccermon/) publica datos CC BY 4.0 de lesiones y carga de dos equipos femeninos noruegos de 2020 y 2021. No sustenta bajas de los equipos objetivo. No se verificó un archivo abierto de suspensiones y lesiones con cobertura y publicación previa en el universo aprobado.

El siguiente paso de F2-B es verificar permisos y cobertura con muestras pequeñas. Los criterios originales de ambos dictámenes conservan su alcance. La aprobación documental o de código no equivale a aprobación de los datos.

## Revisión de integración gratuita

El usuario confirmó manualmente autenticación de Football-Data.org y API-Football. La evidencia de Champions 2026/27 ofrece un censo candidato de 144 partidos de fase liga, 72 finalizados y 144 sin equivalente en la base OpenFootball para esa edición. API-Football devolvió 380 partidos de Premier League 2024/25, igual al recuento OpenFootball. Esa igualdad aún requiere cotejar el universo partido a partido. La evidencia de alineaciones, estadísticas y bajas procede de un fixture. Consulte la [matriz de cobertura](COBERTURA_F2.md).

### Permisos y persistencia

Los términos de Football-Data.org exigen atribución, trato confidencial de la clave y restringen el uso visible tras la cancelación. API-Football traslada al usuario la verificación de derechos de terceros. Las páginas públicas revisadas no acreditan para este piloto almacenamiento indefinido ni reutilización para entrenamiento de ambas fuentes. La guía de API-Football contempla caché temporal para gestionar llamadas, cuya aplicación al proyecto requiere condiciones documentadas. Los tokens no estaban presentes en el entorno de esta ejecución. Se implementaron la integración, el plan y las pruebas sintéticas. La base candidata `proveedores_f2_v1.sqlite` se crea solo al ejecutar con permiso documentado de procesamiento y almacenamiento. Su origen se abre en solo lectura y se copia desde v3. [Football-Data.org](https://www.football-data.org/about), [términos API-Football](https://www.api-football.com/terms), [guía de caché](https://www.api-football.com/news/post/how-to-optimize-api-sports-calls-and-quota-usage).

### Uso y coste estimado

El [integrador](../scripts/ingesta_proveedores_f2.py) empieza en modo plan sin red. Toma partidos por competición y temporada y permite un detalle de hasta 20 IDs únicos, ordenados y procedentes del propio índice. `--desde` y `--hash-indice` permiten reanudar por posición y detienen la tanda si el índice cambió. Las filas de un lote se confirman en una transacción. Una respuesta idéntica reutiliza cuerpo y observaciones y conserva el instante de cada consulta real. Una revisión distinta obtiene su propio hash. Una página adicional requiere un plan explícito. El CLI actual es de muestra y admite hasta tres solicitudes por ejecución, con 7 segundos entre llamadas y parada por cuota anunciada o error HTTP. Revisar saldo de la cuenta antes de lanzarlo.

| Operación | Solicitudes estimadas |
| --- | ---: |
| Muestra de un calendario Football-Data.org 2026/27 | 1 |
| Primera consulta de seis competiciones 2026/27, sin paginación | 6 |
| Índice PL 2024/25 + detalle agrupado + lesiones del fixture indicado | hasta 3 |
| Índices API-Football de seis competiciones × tres temporadas | 18, suponiendo una página cada uno |
| Detalle histórico optimista en grupos de 20 | 294 adicionales según 5.769 filas de referencia de v3 repartidas en 18 grupos |
| Índice y detalle completos sin lesiones | 312 en el escenario agrupado. Las capacidades y los tamaños del proveedor real pueden diferir |
| Alternativa con cuatro endpoints individuales por partido | hasta 23.076 llamadas de detalle, más índices, según esa misma referencia |
| Lesiones | Separadas. Si se consultaran por partido, hasta 5.769 adicionales. Probar primero los filtros por liga y temporada y verificar paginación y cobertura |

Estas cifras son planificación, sin consumo de API en esta revisión. La documentación indica que `ids` puede incluir `events`, `lineups`, `statistics` y `players`, sujeto al plan y a la cobertura. El piloto distingue bloques ausentes, vacíos y poblados y cuenta métricas colectivas con valor. Lesiones se consultan por separado. Una respuesta incompleta queda en la posición actual para revisión. Se requiere decidir el alcance y el presupuesto de llamadas antes de una descarga amplia. [Guía de agrupación](https://www.api-football.com/news/post/how-to-get-all-data-from-a-league-with-api-football).

```powershell
.venv/Scripts/python.exe scripts/ingesta_proveedores_f2.py football-data CL 2026
.venv/Scripts/python.exe scripts/ingesta_proveedores_f2.py api-football PL 2024 --detalle 1 --fixture-id 1208021 --lesiones
```

Para ejecutar una muestra autenticada, cargar las variables de entorno según el procedimiento de esta página y añadir `--consultar --permisos RUTA_LOCAL`. El archivo local describe por proveedor `reference` de la evidencia, `valid_until` con zona, `processing` y `storage` booleanos. Las credenciales solo se leen del entorno. Añadir `--persistir` únicamente con permiso de almacenamiento confirmado. El permiso de entrenamiento se comprobará por separado. Sin persistencia, el proceso solo devuelve agregados de auditoría y no crea una caché de respuestas.

### Identidades y tiempo

La copia de proveedores distingue entidades externas por tipo y proveedor. Los mapeos canónicos requieren un expediente revisado con ID, evidencia y hora de revisión. `--mapeos-revisados` importa las correspondencias de equipo, partido y jugador, con destino existente. Los enlaces de partido también se verifican por competición y edición. El contraste usa primero el enlace confirmado y reporta los candidatos de nombre y fecha como provisionales. Las entradas de jugadores sin identidad canónica siguen como entidades del proveedor. Se conservan alineaciones, suplentes, formación y entrenador en el bloque de alineación, y eventos, estadísticas y bajas en bloques diferenciados y trazables. Un motivo de suspensión requiere evidencia explícita. Los precios y predicciones de la API quedan fuera del adaptador.

`kickoff_at` es la fecha del evento y `consulted_at` la de consulta. `available_at` permanece nulo por restricción de esquema para estos bloques históricos. El importador conserva nulos, distingue cero observado y bloque vacío, deja el resultado a 90 minutos nulo si falta y etiqueta estadísticas y eventos como posteriores al encuentro. Los perfiles estrictos deben usar evidencia prepartido propia, sin derivarla de la hora de consulta ni del marcador. La hora oficial y la neutralidad requieren contraste específico antes de habilitar una fila.

### Propuesta de validación avanzada

Mantener dos conjuntos de variables independientes. Base usa datos de calendario y resultados dentro del perfil aprobado. Avanzado añade históricos demostrables anteriores al partido y, para contexto del propio partido, solo fuentes con publicación acreditada antes del corte. Evaluar un respaldo explícito de base cuando falte el bloque avanzado. Para evaluar el valor incremental usar mismos partidos y cortes, reportar cobertura de la política completa por separado y evitar filtrar a posteriori por existencia del dato. Reservar el futuro test de 2025/26, que este conector rechaza.

Para el avanzado, si se aprueban las tres temporadas gratuitas, proponer entrenamiento inicial en 2022/23, selección walk-forward en 2023/24, calibración en un bloque temprano predefinido de 2024/25 y evaluación interna avanzada en un bloque posterior de 2024/25. Fijar límites por fechas antes de ver resultados y agrupar todas las emisiones de un mismo partido. Esta evaluación interna no sustituye la prueba final reservada de 2025/26. Para verificar el avanzado posteriormente, conseguir datos autorizados de esa reserva o acordar un periodo prospectivo independiente. Si la muestra no sostiene calibración por horizonte, declarar el horizonte no evaluable.

### Estado de cierre

El denominador parcial para CL 2026/27 y el recuento de PL 2024/25 son evidencia aportada por el usuario. La auditoría independiente de cobertura de las demás celdas, los emparejamientos, los marcadores y la neutralidad sigue abierta. En la revisión independiente de código se detectaron y corrigieron tres fallos: materialización del flujo de contraste, rechazo atómico de equipos idénticos y deduplicación de enlaces revisados y provisionales por partido canónico. Pasaron nueve pruebas sintéticas, incluido el flujo completo del CLI y las regresiones de esos casos. La calidad predictiva y los tres horizontes permanecen sin validar. Véase el [manifiesto de esta revisión](MANIFIESTO_PROVEEDORES_F2.json).

## Revisión posterior a la auditoría externa

F2 sigue abierta. `openfootball_v3.sqlite` conserva el linaje de v2 y añade 234 aliases con método y evidencia, 173 clubes canónicos y 37 clubes vinculados entre competiciones. La comparación exacta por país se complementó con equivalencias explícitas y sin coincidencia difusa. No se encontraron duplicados por pareja canónica y fase ni autorreferencias. Cuatro finales de desarrollo tienen neutralidad registrada. El resto se mantiene desconocido hasta contar con evidencia por sede. La edición 2025/26 está marcada como reserva final.

Se recuperaron los 20 marcadores reglamentarios de las jornadas finales española e italiana de 2024/25. Nantes–Toulouse 2025/26 se registra como abandonado, con 0–0 administrativo y goles de 90 minutos nulos. La vista auditada contiene 11.413 filas y 9.910 marcadores de 90 minutos bajo el contrato del adaptador. El snapshot v2 conserva los 9.890 originales. [LaLiga](https://www.laliga.com/es-US/laliga-easports/resultados/2024-25/jornada-38), [Serie A en OpenFootball](https://openfootball.github.io/italy/2024-25_1-seriea.html), [contraste del club en Serie A](https://www.torinofc.it/calendario/2024-2025/prima-squadra/38), [resolución Nantes–Toulouse](https://www.fcnantes.com/articles/article2809.php?num=49229).

La especificación de OpenFootball confirma que el primer par entre paréntesis en la variante con `a.e.t.` usada por el archivo corresponde a 90 minutos. Se contrastaron Real Madrid–Chelsea 2022 (1–3 en tiempo reglamentario, 2–3 tras prórroga) y Manchester City–Real Madrid 2024 (1–1 a 90 minutos y tras prórroga, 3–4 en tanda). La verificación individual de los demás casos permanece pendiente. [Especificación](https://openfootball.github.io/spec/#score-formats), [acta de 2022](https://www.uefa.com/uefachampionsleague/match/2034659--chelsea-vs-real-madrid/), [crónica UEFA de 2024](https://www.uefa.com/uefachampionsleague/news/028c-1aad6a5c7b4a-4c4a76ccd847-1000--report-real-madrid-beat-city-on-penalties/).

La consulta nueva de OpenFootball confirmó el 20/09/2026 como última fecha con marcador en las cinco ligas y HTTP 404 para Champions. UEFA publica 72 resultados de las primeras cuatro jornadas de su fase liga, hasta el 04/11/2026. La actualización canónica de 2026/27 sigue pendiente de una alimentación autorizada y de reconciliar identidades, partidos y sedes. No se atribuye la demora de OpenFootball al calendario real. [Resultados UEFA](https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures-a/).

### Contraste y disponibilidad de variables

- **Football-Data.org Free.** Sus términos exigen confidencialidad, atribución y restringen el uso visible tras cancelar. El cliente nuevo realiza comparación en memoria y guarda conteos agregados, con confirmación explícita de permisos aplicables a la cuenta. La prueba autenticada está pendiente de clave. El script registra discrepancias, candidatos sin emparejar y partidos finalizados del proveedor. El cruce por nombre y fecha UTC deja reprogramaciones, diferencias de zona, nomenclatura y clasificatorias para revisión manual. [Términos](https://www.football-data.org/about).
- **API-Football Free.** El cliente consulta el catálogo por temporada y competición. Lesiones, estadísticas individuales, minutos y onces requieren comprobar filas reales. Una rotación se deriva comparando onces. Las suspensiones requieren causa explícita y las fechas de publicación deben acreditarse por separado. El catálogo y el plan no garantizan completitud histórica. [Documentación](https://www.api-football.com/documentation-v3).
- **StatsBomb.** El catálogo descargado, con hash en `revision_f2.json`, solo enumera Ligue 1 2021/22 y 2022/23 dentro de las seis competiciones masculinas y temporadas objetivo. Una entrada de catálogo no garantiza edición completa. xG por tiro, xGA derivado del rival y alineaciones quedan como candidatos condicionados. La licencia PDF se descargó para verificación. Su alcance íntegro sigue pendiente de confirmación y no se incorporaron eventos ni alineaciones. [Repositorio y licencia](https://github.com/hudl/open-data).
- **Base.** Equipos y resultados quedan mejorados con aliases y revisiones. Forma 5/10/20, Elo y métricas de ataque/defensa son derivables tras aprobación. El descanso completo, la neutralidad generalizada y las variables avanzadas conservan sus restricciones de cobertura.

### Perfil reconstruido por fecha

Se propone un perfil diario que admite, para una fecha de referencia D, solo marcadores reglamentarios de desarrollo de partidos fechados como máximo en D−2 días calendario. D−2 es un margen metodológico configurable hacia arriba. No representa publicación y deja `available_at` nulo. Excluir abandonos, fechas/identidades disputadas hasta resolución y fuentes con semántica incierta. Congelar versiones y medir sensibilidad al ampliar el margen. Mantener aparte el perfil verificable que exige evidencia fechada de la revisión disponible en el corte. Los horizontes T−24 h, T−3 h y T−60 min siguen sin validar. El inventario de prueba de esta regla usa `scripts/perfil_f2.py` y excluye la reserva y la temporada en curso.

### Procedimiento de contraste

En PowerShell, leer las claves con entrada enmascarada y mantenerlas en el proceso de la sesión. Ejemplo para ambas variables.

```powershell
$env:FOOTBALL_DATA_TOKEN = Read-Host 'Clave Free de Football-Data.org' -MaskInput
$env:API_FOOTBALL_KEY = Read-Host 'Clave Free de API-Football' -MaskInput
.venv/Scripts/python.exe scripts/contraste_f2.py football-data CL 2026 --permisos-verificados
.venv/Scripts/python.exe scripts/contraste_f2.py api-football PL 2024 --permisos-verificados
Remove-Item Env:FOOTBALL_DATA_TOKEN, Env:API_FOOTBALL_KEY
```

Usar `--permisos-verificados` después de confirmar términos y alcance de la cuenta. El CLI bloquea 2025/26 para desarrollo. Auditar la reserva mediante un procedimiento aislado de calidad sin distribuir sus etiquetas para selección de variables o modelos.

Alcance aprobado: Champions League, Premier League, LaLiga, Bundesliga, Serie A y Ligue 1, de 2021/22 a 2025/26. La edición 2026/27 se informa por separado como abierta. Presupuesto de suscripciones: $0 MXN.

La muestra inicial tomó las primeras 12 filas de Premier League y 12 de Champions 2021/22. Las 24 se procesaron. Cinco de Champions carecían de hora explícita y las 24 carecían de evidencia de publicación histórica. Se ejecutó dos veces la misma muestra usando claves de objeto y fila para evitar duplicados físicos.

## Cobertura observada por competición, temporada y fuente

Se procesaron **35 de 36 archivos solicitados**. Las ediciones históricas aportaron 9.661 filas, de las cuales 9.640 tienen marcador y 422 carecen de hora de origen. La edición en curso aportó 1.752 filas de ligas nacionales, con 250 marcadores observados y 940 horas ausentes. La ruta de Champions 2026/27 devolvió HTTP 404. Ninguna de las 11.413 filas acredita disponibilidad histórica. Véase [Inventario por competición y temporada](COBERTURA_F2.md).

El manifiesto inicial `data/processed/cobertura.json` identifica fuente, URL, hash y resultados de normalización del snapshot v2. Dos reprocesamientos locales conservaron 11.413 revisiones y SQLite pasó `integrity_check` y `foreign_key_check`. La primera ampliación detectó dos formatos de marcador, eliminatorias con prórroga o tanda y cruces repetidos en fases distintas. Las correcciones posteriores de v3 figuran en la revisión de auditoría externa de este informe.

«Aceptada» indica que la fila pasó el adaptador. El denominador independiente, las comprobaciones de fechas y marcadores contra otra fuente y la auditoría manual propuesta siguen pendientes. Una fecha sin hora y un archivo posterior al partido no habilitan un corte estricto T−24 h, T−3 h o T−60 min.

La identidad del piloto usa el nombre exacto del proveedor dentro de cada competición. Los cruces de clubes entre competiciones quedan pendientes de mappings auditados. Champions se centra en `cl.txt`; los clasificatorios que el proveedor publique en otros archivos se registran como cobertura pendiente. Los formatos ambiguos se aíslan. Las horas se conservan como texto de origen sin inferir UTC.

## Contraste, permisos y variables

| Fuente | Evidencia disponible | Estado para el piloto |
| --- | --- | --- |
| OpenFootball | Repositorios [ligas](https://github.com/openfootball/football.json) y [Champions](https://github.com/openfootball/champions-league) publicados como CC0. Capturas y hashes locales. | Candidato base. Publicación histórica, neutralidad, reprogramaciones y marcador de eliminatorias requieren contraste. |
| Football-Data.org Free | [Cobertura](https://www.football-data.org/coverage) y [API v4](https://www.football-data.org/documentation/quickstart). Plan gratuito con las seis competiciones anunciadas. | Pendiente de clave y de confirmar temporadas efectivamente accesibles y condiciones de conservación. |
| API-Football Free | [Plan gratuito](https://www.api-football.com/pricing) y [documentación](https://www.api-football.com/documentation-v3). Catálogo de campos y límite de temporadas. | Pendiente de clave y permisos aplicables. Endpoint de lesiones y alineaciones no acredita revisiones publicadas para cada corte. |
| StatsBomb Open Data | [Repositorio y licencia](https://github.com/hudl/open-data). Eventos con xG y alineaciones de partidos seleccionados. | Evaluación documental. Sin incorporación hasta verificar licencia íntegra y cobertura del subconjunto. |

| Variable | Disponibilidad inicial |
| --- | --- |
| Fecha, equipos y goles de 90 minutos | Observados donde el adaptador puede interpretar el contrato. Necesitan validación independiente. |
| Localía, forma 5/10/20, ataque/defensa, Elo y calidad del rival | Derivables tras aprobación. Neutralidad, aliases y fuerza entre competiciones requieren evidencia adicional. |
| Descanso y carga | Cobertura incompleta de copas y otras competiciones. |
| xG/xGA y estadísticas individuales | Ausentes en OpenFootball. StatsBomb es un candidato para muestras seleccionadas. |
| Lesiones y suspensiones | Sin archivo prepartido auditado. API-Football es candidato condicionado por temporada y permiso. |
| XI histórico, minutos, formaciones y rotaciones | Ausentes en OpenFootball. Validar eventos, onces y su publicación en fuentes complementarias. |
| Cuotas y contexto avanzado | Sin datos de piloto incorporados. Habilitación posterior según los criterios ya aprobados. |

## Claves gratuitas

Solicita una clave Free en [Football-Data.org](https://www.football-data.org/client/register) y, si se quiere contrastar campos avanzados, en el [panel de API-Football](https://dashboard.api-football.com/). Guárdalas en un gestor de secretos o variables de sesión `FOOTBALL_DATA_TOKEN` y `API_FOOTBALL_KEY`, respectivamente. Usar las cabeceras `X-Auth-Token` y `x-apisports-key`. Evita pegarlas en el chat, archivos del proyecto, URLs o registros. El contraste autenticado aún está pendiente.

El informe sigue abierto hasta completar y revisar la evidencia de calidad. La puerta a F3 requiere aprobación explícita del usuario.

Para reproducir el inventario de OpenFootball, ejecutar `.venv/Scripts/python.exe scripts/f2.py --reprocesar`. La opción `--ampliar` consulta las 36 rutas públicas. Ambas guardan el resultado en un snapshot de actualización separado de v2. La construcción de v3 a partir de v2 está en `scripts/f2_revision.py`. El entorno usa Python 3.14.5 y biblioteca estándar.
