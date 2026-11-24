# Informe de F3 · Base experimental

Se analizaron **7.720 partidos de 2021/22 a 2024/25**, con variables construidas usando el corte D−2 de cada objetivo. v3 se abrió en modo solo lectura y mantiene el SHA-256 `c195a52cfdff831c1c847e50e30b031c541adec03f4ee6273183033369819d19`. La consulta de F3 excluyó las etiquetas de la reserva 2025/26 y de la edición 2026/27. El gasto fue de $0 MXN y no hubo solicitudes a proveedores. F2-A y F2-B permanecen abiertas.

## Goles, resultados y localía observada

| Métrica | Local designado | Visitante designado |
| --- | ---: | ---: |
| Media de goles | 1,562 | 1,279 |
| Mediana | 1 | 1 |
| Varianza muestral | 1,754 | 1,413 |
| Desviación estándar | 1,324 | 1,189 |
| Asimetría muestral ajustada | 1,006 | 1,034 |
| Varianza/media | 1,123 | 1,105 |
| Victorias | 43,80 % (3.381) | 31,33 % (2.419) |
| Porterías a cero | 29,52 % | 22,19 % |

El empate fue **24,87 %** (1.920) y ambos equipos marcaron en **54,51 %**. El marcador más frecuente fue **1–1** (929), seguido de 1–0 (730) y 2–1 (641). La brecha de victorias fue de 12,46 puntos porcentuales y la de goles de 0,283 por partido. Son diferencias del rol designado en la mezcla observada. Solo cuatro partidos tienen sede neutral confirmada y 7.716 tienen sede desconocida. La diferencia no identifica un efecto causal de jugar en casa.

| Línea | Over | Under |
| --- | ---: | ---: |
| 0,5 | 93,78 % | 6,22 % |
| 1,5 | 77,49 % | 22,51 % |
| 2,5 | 53,55 % | 46,45 % |
| 3,5 | 31,98 % | 68,02 % |
| 4,5 | 16,26 % | 83,74 % |

## Diferencias entre torneos y cambios en el tiempo

| Competición | n | Goles/partido | Victoria local | Empate | Victoria visitante |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bundesliga | 1.224 | 3,161 | 44,12 % | 25,00 % | 30,88 % |
| Champions | 564 | 3,090 | 48,58 % | 18,62 % | 32,80 % |
| Ligue 1 | 1.372 | 2,821 | 42,86 % | 24,56 % | 32,58 % |
| LaLiga | 1.520 | 2,570 | 44,93 % | 26,58 % | 28,49 % |
| Premier League | 1.520 | 2,971 | 44,54 % | 23,03 % | 32,43 % |
| Serie A | 1.520 | 2,650 | 40,72 % | 27,50 % | 31,78 % |

Los promedios por temporada fueron **2,824**, **2,780**, **2,892** y **2,870** goles por partido. La gráfica mensual muestra variación adicional. Entre meses con al menos 30 encuentros, la media local observada fue de 1,304 en marzo de 2025 (181 partidos) a 1,725 en octubre de 2022 (309). Las composiciones y tamaños mensuales varían. Estas diferencias no demuestran una tendencia ni un efecto del calendario.

En Champions se observan 96 partidos por fase de grupos en cada una de las tres primeras ediciones. En 2024/25 hay 144 en fase de liga y 16 de playoff. Las fases de grupos arrojan 3,094 / 3,167 / 3,083 goles por partido y 18,75 % / 19,79 % / 20,83 % de empates. La fase de liga de 2024/25 arroja 3,264 goles y 12,50 % de empates. La única edición de ese formato y el cambio de rivales impiden atribuirle causalmente la diferencia. El CSV separa comparación por edición y por fase.

## Dispersión y relación entre goles

El total promedió 2,841 goles con varianza 2,885. La dispersión inferior a la media en algunos estratos y superior en otros se ve en la tabla por competición y temporada. Para los goles de cada lado, la dispersión global supera su media. La mezcla de equipos, torneos y temporadas puede producir esa diferencia incluso si un Poisson condicional fuera útil como referencia. Estas métricas no prueban equidispersión condicional. Pearson entre goles local y visitante fue **−0,090** y Spearman **−0,067**, asociaciones descriptivas débiles. LaLiga fue ligeramente positiva en ambos coeficientes. Los conteos son discretos y Spearman usa rangos medios en empates.

## Calidad, faltantes y redundancia

La muestra elegible no tiene marcadores ausentes. La selección de candidatos de F2 excluye los registros sin resultado admisible y no certifica cobertura poblacional. Faltan 292 horas de origen, todas en Champions. La jornada explícita se extrajo en 7.412 de 7.720 partidos. La publicación histórica no se acredita para ninguna fila. No se observaron equipos con más de un encuentro por día en este universo. El sesgo de cobertura de competiciones ajenas a las seis incluidas limita descanso, carga y formas entre torneos.

Los historiales completos de 5/10/20 partidos son 7.342/6.984/6.291 para el local y 7.333/6.976/6.305 para el visitante. El proxy previo del rival tiene valor en 7.392/7.386 objetivos respectivamente. El PPG de H2H local tiene soporte en 5.949. Los faltantes quedan visibles en lugar de convertirse en ceros.

La matriz triangular de 30 predictores numéricos seleccionados incluye Pearson, Spearman y n de pares completos. Es un diagnóstico de redundancias, no una selección supervisada. En el local, Pearson entre PPG de 5 y 10 partidos fue 0,843, y entre 10 y 20 fue 0,900. Over y Under 2,5 de la misma ventana dieron −1 exacto. PPG y PPG ponderado por calidad del rival de la ventana de 10 dieron 0,959. GF/GA/DG, proporciones 1X2, complementos O/U, diferencias entre lados y sus componentes requieren cuidado por relaciones algebraicas o multicolinealidad. Las variables se conservaron para decidir en el bloque de entrenamiento.

## Archivos y controles

- [Variables X](../data/processed/f3_base_v1/X.csv) y [etiquetas y](../data/processed/f3_base_v1/y.csv), unidas exclusivamente por `match_id`. La versión contiene 287 columnas en X, con claves y metadatos incluidos.
- [Tablas generales y estratificadas](../data/processed/f3_base_v1/eda_resumen.csv), [marcadores exactos](../data/processed/f3_base_v1/marcadores_exactos.csv) y [series mensuales](../data/processed/f3_base_v1/eda_mensual.csv).
- [Distribución de goles](../data/processed/f3_base_v1/distribucion_goles.svg) y [evolución mensual](../data/processed/f3_base_v1/goles_mensuales.svg).
- [Correlaciones](../data/processed/f3_base_v1/correlaciones_features.csv), [cobertura de variables](../data/processed/f3_base_v1/COBERTURA_FEATURES_F3.json), [diccionario](DICCIONARIO_FEATURES_F3.md), [protocolo](PROTOCOLO_VALIDACION_F3.md) y [manifiesto](MANIFIESTO_F3.json).

Reproducir con `.venv/Scripts/python.exe scripts/features_f3.py` y después `.venv/Scripts/python.exe scripts/eda_f3.py`. Ejecutar pruebas con `.venv/Scripts/python.exe -m unittest discover -s scripts -p test_features_f3.py`. La revisión independiente detectó que el EDA podía aceptar un archivo X anterior del mismo tamaño. Se corrigió verificando hashes de base, código, X e y, unicidad y universo de IDs, fechas y cortes. Las pruebas cubren mutaciones futuras, objetivo y simultaneidad, disponibilidad desconocida, límites empatados de ventana y rechazo de índices inconsistentes.

F3 deja preparados datos y protocolo experimentales. Elo, los demás modelos, los horizontes prepartido verificables y las variables avanzadas quedan pendientes de sus requisitos y de autorización posterior.
