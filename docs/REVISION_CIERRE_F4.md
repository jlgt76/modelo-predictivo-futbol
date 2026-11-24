# Dictamen complementario de F4 experimental

**Cumple el alcance complementario y queda listo para decisión de cierre experimental.** Se reutilizaron 69.120 predicciones, los ocho calibradores almacenados y la selección E2. Los 806 ajustes originales, las métricas y el informe siguen disponibles. Se verificaron antes y después los hashes del manifiesto original, sus diez resultados, el informe, la configuración, las versiones históricas del código y los CSV de desarrollo de F3. El análisis real requirió **0 ajustes nuevos, 0 consultas y $0 MXN**.

## Clasificación y empate

La evaluación interna contiene **1.015 partidos**, con 425 victorias locales, **237 empates (23,35 %)** y 353 victorias visitantes. A continuación se muestra la clasificación argmax. La temperatura positiva preservó las decisiones en los ocho modelos.

| Modelo | Empates elegidos | Empates acertados | Recall empate | Macro-F1 | Balanced Accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| B0 | 0 | 0 | 0,00 % | 0,1968 | 0,3333 |
| B1 | 0 | 0 | 0,00 % | 0,1968 | 0,3333 |
| B2 | 0 | 0 | 0,00 % | 0,1968 | 0,3333 |
| B3 | 0 | 0 | 0,00 % | 0,3560 | 0,4136 |
| P2 | 0 | 0 | 0,00 % | 0,3927 | 0,4517 |
| DC2 | 1 | 1 | 0,42 % | 0,3957 | 0,4532 |
| E2 | 0 | 0 | 0,00 % | 0,3982 | 0,4576 |
| L2 | 1 | 1 | 0,42 % | 0,3928 | 0,4495 |

Las matrices tienen filas de clase real y columnas de clase pronosticada. Los empates numéricos de probabilidad siguen el orden original 1, X, 2. La precisión queda vacía si el modelo nunca eligió esa clase. El F1 se calcula como 2TP/(soporte + predichos) y es cero cuando hay casos reales y no se acierta ninguno. Macro-F1 promedia las tres clases y Balanced Accuracy promedia su Recall. Los CSV desglosan los resultados por competición y versión bruta o calibrada.

| Modelo | P(X) bruta media | Brier empate bruto | Log Loss empate bruto | AUC ROC bruta | Precisión promedio bruta |
| --- | ---: | ---: | ---: | ---: | ---: |
| B3 | 24,46 % | 0,17794 | 0,54041 | 0,547 | 0,249 |
| P2 | 23,43 % | 0,17695 | 0,53734 | 0,567 | 0,286 |
| DC2 | 24,60 % | 0,17679 | 0,53687 | 0,573 | 0,290 |
| E2 | 24,30 % | 0,17854 | 0,54191 | 0,525 | 0,248 |
| L2 | 24,82 % | 0,17786 | 0,54021 | 0,549 | 0,287 |

La P(X) bruta de E2 alcanzó un máximo de **27,17 %**. Para que una clase sea argmax de tres probabilidades que suman uno, necesita al menos 33,33 %. Los percentiles 5–95 de E2 fueron **18,87–27,07 %** entre empates reales y **17,32–27,07 %** entre los demás partidos. El solapamiento y el AUC de 0,525 indican escasa separación descriptiva. La precisión promedio de 0,248 queda cerca de la prevalencia de 0,2335.

Con la temperatura original, E2 acercó la media de P(X) a la frecuencia observada, de 24,30 % a 23,15 %, y redujo el error de calibración de diez bins de 0,00949 a 0,00250. A la vez, su Log Loss binario pasó de 0,54191 a 0,54204, su Brier de 0,17854 a 0,17858 y el AUC se mantuvo cerca de 0,525. La mejora en calibración agregada de P(X) deja prácticamente intacta su capacidad de ordenar los partidos. Los bins pequeños y el ECE son descriptivos. DC2 obtuvo las mejores puntuaciones binarias brutas para empate en esta muestra. Se conserva E2 para el objetivo prerregistrado 1X2, sin umbrales añadidos ni selección a partir de estos diagnósticos.

## Mercados y cobertura

| Emisión | 1X2 y doble oportunidad 1X, X2 y 12 | Over/Under 0,5 a 4,5, BTTS sí/no y marcador exacto |
| --- | --- | --- |
| Bruta B2, P2 y DC2 | 1.015/1.015 por modelo | 1.015/1.015 por modelo |
| Bruta B0, B1, B3, E2 y L2 | 1.015/1.015 por modelo | No evaluables por el estimador |
| Temperatura, ocho modelos | 1.015/1.015 por modelo | No evaluables bajo esta calibración |

El Brier binario usa la media de (p−y)² y el Log Loss binario la media de la pérdida logarítmica con piso de 10⁻¹⁵ en la probabilidad del resultado. 1X2 se puntúa por evento uno contra el resto, además de las métricas multiclase de la corrida original. La doble oportunidad usa el complemento de la clase excluida. Los complementos, totales y BTTS se derivan del mismo perfil de probabilidad. Las tablas conservan el denominador, el número evaluado, los positivos y el motivo cuando falta capacidad. Las 1.089 celdas del soporte 0–32 por lado incluyen marcadores con cero apariciones. Cada celda se evalúa como evento binario. El marcador exacto multiclase usa la probabilidad asignada a la celda observada y Brier como suma cuadrática sobre todo el soporte.

| Distribución bruta | Brier marcador exacto | Log Loss marcador exacto | MAE local | MAE visitante | MAE total |
| --- | ---: | ---: | ---: | ---: | ---: |
| B2 | 0,93677 | 3,03143 | 1,05064 | 0,90396 | 1,30751 |
| P2 | 0,93004 | 2,91529 | 0,94166 | 0,86284 | 1,28498 |
| DC2 | 0,93027 | 2,91677 | 0,94166 | 0,86284 | 1,28498 |

El MAE compara los goles observados con la esperanza de la matriz en cada lado y en el total. Las esperanzas de P2 y DC2 coinciden porque la corrección de los cuatro marcadores bajos redistribuye masa y conserva las marginales. `mercados.csv`, `marcadores_exactos_binarios.csv` y `mae_goles.csv` contienen los resultados de las seis competiciones y el agregado.

## Protocolo, linaje y protección

- Se mantuvieron los cortes D−2 de cada objetivo y de cada ajuste. La muestra histórica evaluada es enero a mayo de 2025. La extrapolación a predicciones operativas y a los horizontes verificables originales sigue pendiente.
- `predicciones_brutas.csv` conserva 69.120 emisiones incluyendo probabilidades de mercados y, cuando procede, tasas y rho para reconstruir la matriz. Se excluyó la columna original que evaluaba la probabilidad del marcador **observado**, porque requiere la etiqueta. `etiquetas_desarrollo.csv` conserva los 5.769 resultados de los tramos que emitieron pronósticos, unidos por `partido`.
- `predicciones_calibradas_1x2.csv` contiene **8.120** filas de evaluación. Reaplica el calibrador escalar archivado con la misma fórmula y registra su ID. Las 926 filas elegibles de calibración por modelo sirvieron para ajustar ese calibrador en la corrida original. Las etapas de selección y calibración conservan solo predicciones brutas en el registro nuevo. La emisión calibrada incluye 1X2 y doble oportunidad, con un indicador explícito de que carece de matriz bruta asociada a esas probabilidades.
- Los dos registros guardan la versión y fecha de generación de origen, el hash de configuración y un SHA-256 compuesto del mapa canónico de hashes de X e y. El manifiesto enumera los dos componentes, los hashes de las fuentes y cada archivo publicado. `calibradores.json` aporta ID, valor, corte y tamaño de ajuste del calibrador.
- La entrada actual de experimentos y la revisión requieren un directorio nuevo. La creación exclusiva falla si el destino existe y bloquea también los subdirectorios de la corrida original. El script original se conserva byte por byte en [el archivo histórico](../scripts/historico/f4_estadistico_v1/experimento_f4.py), con su mismo SHA-256 del manifiesto original. La entrada activa añade protección de salida y validaciones de entrada sin cambiar los estimadores. Para reproducir solo este complemento, usar un nombre de salida nuevo:

```powershell
.\.venv\Scripts\python.exe scripts/revision_cierre_f4.py --salida data/processed/f4_cierre_reproduccion_01
.\.venv\Scripts\python.exe -m unittest discover -s scripts -p 'test_*.py'
```

**28 pruebas locales aprobadas**, siete nuevas. Incluyen mutación de etiquetas no elegibles con ajustes pequeños de las cuatro familias, aislamiento de calibración, rechazo de reserva antes de cargar etiquetas como registros, respaldo por equipo y competición, validez del soporte, rechazo de inconsistencias, métricas de clase con denominadores vacíos y protección de directorios. Las pruebas con ajuste usan únicamente casos sintéticos.

La verificación de salidas reprodujo el Log Loss de las 112 filas de la tabla 1X2 original con diferencia inferior a 10⁻¹² y comprobó 18 hashes de fuentes y 13 hashes de resultados nuevos. La revisión independiente confirmó el recuento de empates, la separación de etiquetas, las 8.120 probabilidades recalibradas, el soporte de marcadores y la integridad de la corrida original.

## Límites que permanecen

**Dixon-Coles conserva el ajuste condicional de dos pasos.** Primero se estiman las tasas Poisson. Después se maximiza respecto a rho con las tasas fijas. Los parámetros de ataque, concesión y localía no se vuelven a estimar bajo la verosimilitud corregida. Las cotas factibles protegen el soporte y pueden limitar el óptimo. Las métricas se aplican a esta formulación y no establecen cómo se comportaría una estimación conjunta completa.

La señal de empate por argmax es insuficiente para un uso que exija identificar empates como clase dominante. La calibración 1X2 no resuelve la calibración conjunta de goles. Siguen pendientes los horizontes T−24 h, T−3 h y T−60 min, la calidad pendiente de F2-A/F2-B, la referencia de mercado sin margen y las métricas económicas. La prueba final 2025/26 permanece reservada. El dictamen cubre el experimento interno D−2 y deja F5 pendiente de autorización.

[Manifiesto complementario](../data/processed/f4_cierre_v1/MANIFIESTO_CIERRE_F4.json) · [Clasificación](../data/processed/f4_cierre_v1/clasificacion_clase.csv) · [Matrices](../data/processed/f4_cierre_v1/matrices_confusion.csv) · [Empate](../data/processed/f4_cierre_v1/empate_resumen.csv) · [Mercados y cobertura](../data/processed/f4_cierre_v1/mercados.csv)
