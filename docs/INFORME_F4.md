# F4 experimental · Comparación de modelos estadísticos

**Elo E2 quedó seleccionado en los dos bloques anuales de desarrollo.** En la evaluación interna redujo el Log Loss 1X2 de la mejor referencia simple, B3, de **1,02243 a 0,98695**. La diferencia pareada fue −0,03548, con IC 95 % semanal [−0,04987; −0,02251]. Poisson P2 y Dixon-Coles DC2 quedaron cerca de E2, con intervalos pareados que incluyen cero. Se conserva la elección tomada antes de esta evaluación. Para tareas que necesiten una distribución de marcadores, P2 ofrece la referencia generativa más parsimoniosa de las dos variantes finalistas.

## Alcance y cronología

Se verificaron X, y, el generador de F3, su manifiesto y la configuración antes del primer ajuste. El pipeline unió por `match_id` los 7.720 partidos autorizados y verificó el SHA-256 de v3 antes y después. SQLite se leyó como archivo para comprobar su hash, sin consultas SQL ni escrituras. Quedaron fuera las etiquetas de 2025/26 y 2026/27. No hubo consultas a proveedores ni gasto.

| Uso | Universo | Partidos | Bloques evaluados |
| --- | --- | ---: | ---: |
| Arranque | 2021/22 | 1.951 | — |
| Selección | 2022/23 y 2023/24 | 3.828 | 23 |
| Calibración fuera de muestra | Primera parte de 2024/25 | 926 | 6 |
| Evaluación interna | Desde el 1 de enero de 2025 | 1.015 | 6 |

Cada X dispone de su corte individual D−2. En cada bloque de 28 días se ajustan los parámetros con historia expansiva hasta D−2 de la primera fecha con partidos. Elo además actualiza su estado por fecha, con lotes de resultados elegibles, y usa el mismo estado para todos los encuentros de la fecha objetivo. Los partidos de calibración se pronosticaron con configuraciones ya fijadas. El calibrador se congeló con las 926 etiquetas disponibles hasta el 30 de diciembre. Durante evaluación se siguió la política expansiva fijada antes del ajuste.

## Estimadores, variables y presupuesto

| Familia | Diseño | Variantes |
| --- | --- | --- |
| B0 y B1 | Frecuencias 1/X/2 con suavizado aditivo de uno por clase, denominador n + 3. B1 agrupa por competición y usa B0 con menos de 30 partidos elegibles. | Deterministas |
| B2 | Poisson de medias por competición, con un gol y un partido de suavizado por lado. Usa tasas globales si hay menos de 30 observaciones. En sedes neutrales confirmadas, usa la media de las dos tasas. | Determinista |
| B3 | Ajusta los logaritmos de B1 por `[d, 0, -d]`, donde d es la diferencia de puntos por partido en diez partidos dividida por tres. Vuelve a B1 con menos de cinco observaciones en cualquiera de los equipos. La fórmula se fijó sin optimizar pesos. | Determinista |
| Poisson | Intercepto y ventaja nominal por competición, efectos de ataque y de concesión por equipo con suma cero en cada familia. Una concesión positiva eleva la tasa del rival. L2 sobre efectos y localía. Un equipo con menos de cinco cruces elegibles en esa competición recibe efectos de referencia. No se trasladan sus efectos automáticamente tras un ascenso. | P1 uniforme y P2 ponderado con semivida de 365 días |
| Dixon-Coles | Reutiliza las tasas del Poisson correspondiente. Estima rho en un segundo paso por verosimilitud condicional ponderada, con cotas que aseguran correcciones positivas para todas las tasas admitidas. Es un ajuste en dos pasos. | DC1 sobre P1 y DC2 sobre P2 |
| Elo | Inicio equivalente a 1.500 puntos, diferencia escalada por 400 y actualización simultánea. Una softmax de dos logits simétricos y un intercepto de empate ajustado convierte el estado en tres probabilidades. E3 comparte identidad entre competiciones, incluida Champions, para probar sensibilidad a la conexión. Las diferencias entre grupos desconectados carecen de validación. | E1 estándar, E2 con margen y regresión parcial del 20 %, E3 enlazado |
| Logística | Multinomial L2 con clase visitante de referencia. Lista reducida de forma, fuerza, rol nominal, tamaño del historial y, en L3, calendario observado. Mediana, escalado, indicadores de faltantes y codificación de competición se ajustan en el entrenamiento de cada bloque. | L1, L2 y L3 |

El [prerregistro](CONFIG_F4.json) identifica entradas permitidas, excluidas y condicionadas por modelo, hiperparámetros, reglas de respaldo, semillas y tolerancias. Se probaron **10 configuraciones entrenables** repartidas en 2/2/3/3, con un límite de 12 por familia. Los **806 ajustes efectivos** fueron 318 ataque-defensa, 318 rho condicionales, 81 conversiones Elo, 81 logísticas y ocho temperaturas. Las parejas Poisson/Dixon-Coles reutilizaron el ajuste de tasas dentro de cada bloque. Los 806 ajustes informaron convergencia. Las tasas de goles se estiman de resultados reglamentarios históricos. El xG de tiros continúa fuera del snapshot autorizado.

La extensión de dependencia se basa en la corrección de marcadores bajos de Dixon y Coles. Los ajustes multivariados usan L-BFGS-B con gradiente explícito. [Dixon y Coles, 1997](https://rss.onlinelibrary.wiley.com/doi/10.1111/1467-9876.00065) y [documentación de SciPy](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html).

## Selección y evaluación 1X2

| Modelo | Log Loss selección | Log Loss interno bruto | Log Loss con temperatura | Brier bruto | RPS bruto | Accuracy bruta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 1,06905 | 1,07475 | 1,07487 | 0,65133 | 0,23604 | 41,87 % |
| B1 | 1,06936 | 1,07326 | 1,07326 | 0,65080 | 0,23628 | 41,87 % |
| B2 | 1,06893 | 1,07638 | 1,07625 | 0,65276 | 0,23683 | 41,87 % |
| B3 | 1,02333 | 1,02243 | 1,02042 | 0,61403 | 0,21805 | 49,06 % |
| P2 | 0,98961 | 0,98516 | 0,98514 | 0,58763 | 0,20534 | 52,81 % |
| DC2 | 0,98920 | 0,98483 | 0,98453 | 0,58738 | 0,20530 | 52,91 % |
| E2 | **0,98632** | 0,98695 | 0,98931 | 0,58867 | **0,20506** | **53,40 %** |
| L2 | 0,99221 | 0,98993 | 0,98885 | 0,59062 | 0,20638 | 52,81 % |

E2 superó a B1 por 0,07110 y 0,09544 en las dos temporadas de selección. Su IC 95 % pareado agregado frente a B1 fue [−0,09252; −0,07285]. El criterio prerregistrado fijó E2 antes del tramo interno. La diferencia interna E2–P2 fue +0,00179 [−0,00714; +0,01059] y E2–DC2 fue +0,00211 [−0,00809; +0,01273]. El remuestreo de 14 días obtuvo la misma lectura. Estos intervalos agrupan partidos por fecha, con 21 semanas o 12 bloques de 14 días. El bajo número de bloques y la dependencia entre partidos de un club limitan la precisión.

La temperatura ajustada para E2 fue 0,8956 y empeoró su Log Loss interno. La observación se conserva para revisión, sin cambiar el candidato ni elegir retrospectivamente un calibrador. La calibración escalar se evalúa solo para 1X2. Los mercados de goles mantienen la distribución conjunta bruta. Hay 81 partidos de Champions, 171 de Bundesliga, 170 de Ligue 1, 199 de LaLiga, 192 de Premier League y 202 de Serie A. Los bins con poca muestra y sus intervalos Wilson permiten una lectura descriptiva. Esos intervalos por bin no corrigen dependencia entre partidos.

## Goles, marcadores, neutralidad y estabilidad

P2 y DC2 usan exactamente las mismas tasas, partidos y cortes. DC2 mejoró 0,00032 en Log Loss 1X2 frente a P2, con IC 95 % [−0,00269; +0,00211]. El Log Loss binario de empate fue 0,53687 frente a 0,53734 de P2. Los cuatro marcadores corregidos en conjunto y el Under 2,5 tienen la misma masa en ambos modelos: las cuatro celdas están por debajo de 2,5 y la corrección redistribuye su masa total. La probabilidad media BTTS subió de 53,29 % a 53,88 % frente a 54,98 % observado, pero su Log Loss pasó de 0,69225 a 0,69247. Para el marcador exacto, DC2 obtuvo 2,91677 frente a 2,91529 de P2 sobre 1.015 partidos.

- **Poisson.** La dispersión condicional de Pearson fuera de muestra en P2 varió entre 0,776 y 1,383 por competición y lado. El extremo superior corresponde a goles del local designado en Champions. La ventaja local estimada de P2 fue de 0,0875 a 0,3261 en escala log a través de sus ajustes. La mediana del cambio absoluto entre ajustes sucesivos de un mismo equipo y competición fue 0,015 en ataque y 0,016 en concesión. El percentil 95 fue 0,087 y 0,083. Las comparaciones entre P1 y P2 cambian a la vez semivida y penalización, por lo que la diferencia observada corresponde a ambas configuraciones.
- **Historia escasa.** P1/DC1 usaron efectos parciales de referencia en 258 partidos por candidato. P2/DC2 lo hicieron en 344 cada uno a través de selección, calibración y evaluación. En el tramo de evaluación interna esa situación ocurrió en cero objetivos P2/DC2. El registro distingue el historial insuficiente de un equipo del respaldo del estimador completo.
- **Dixon-Coles.** En DC2, 23 de 193 ajustes quedaron a menos de 0,00001 de una cota de rho. Las cotas protegen probabilidades para tasas futuras dentro de [0,02; 6] y limitan la flexibilidad. Se comprobó que rho igual a cero recupera Poisson y que el soporte 0–32 cumple la tolerancia de masa.
- **Neutralidad.** Hay cuatro sedes confirmadas en la base de desarrollo, tres en tramos pronosticados y una en evaluación. En esos tres casos, tratar el partido como neutral redujo P(1) de P2 en 7,2 a 8,9 puntos porcentuales respecto a la configuración nominal del mismo ajuste. Es una sensibilidad descriptiva con muestra pequeña. Para sedes desconocidas se usa el rol designado del calendario y la ventaja estimada combina los efectos de ese rol.
- **Logística.** El número de condición de L2 quedó entre 3,54 × 10¹⁷ y 2,05 × 10¹⁹. Las ventanas y máscaras de faltantes que coinciden contribuyen a la redundancia. L2 estabiliza la predicción, pero esta evidencia limita la interpretación individual de coeficientes. El percentil 95 del cambio absoluto de coeficientes entre ajustes consecutivos fue 0,016 en la escala estandarizada de cada bloque. Elastic Net y cualquier modificación del diseño se reservan para otro ciclo expresamente autorizado.

## Reproducción y revisión

- [Manifiesto y hashes](../data/processed/f4_estadistico_v1/MANIFIESTO_F4.json), [selección congelada](../data/processed/f4_estadistico_v1/seleccion_congelada.json), [predicciones históricas](../data/processed/f4_estadistico_v1/predicciones_desarrollo.csv) y [cortes por bloque](../data/processed/f4_estadistico_v1/bloques.csv).
- [Métricas por competición](../data/processed/f4_estadistico_v1/metricas_evaluacion.csv), [diferencias pareadas](../data/processed/f4_estadistico_v1/diferencias_pareadas.json), [detalle de marcadores y mercados](../data/processed/f4_estadistico_v1/mercados_y_marcador.csv), [residuos y dispersión](../data/processed/f4_estadistico_v1/diagnostico_goles.csv) y [ajustes](../data/processed/f4_estadistico_v1/diagnosticos_ajustes.json).
- [Diagrama de calibración E2](calibracion_f4/E2.svg), [bins de todos los modelos](../data/processed/f4_estadistico_v1/calibracion_bins.csv) y [manifiesto de los ocho diagramas](calibracion_f4/MANIFIESTO_GRAFICAS.json).

Con Python 3.14.5 y las versiones de [requirements-f4.txt](../requirements-f4.txt), se puede reproducir en un directorio nuevo desde la raíz, conservando la corrida publicada.

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'scripts'); import experimento_f4 as f; f.OUT=f.ROOT/'data/processed/f4_reproduccion_01'; f.OUT.mkdir(parents=True,exist_ok=False); f.main()"
.\.venv\Scripts\python.exe -m unittest discover -s scripts -p 'test_*.py'
```

Pasaron **21 pruebas locales**. La revisión independiente verificó hashes, exclusión de temporadas reservadas, unicidad, separación cronológica, coherencia de mercados y coincidencia de Log Loss y Brier recalculados. Se corrigieron dos hallazgos relativos a identificar equipos con historia corta y verificar que el código se mantuviera intacto durante la corrida. Se registran 69.120 filas modelo–partido sin probabilidad 1X2 recortada.

La evidencia corresponde a D−2 reconstruido. Los horizontes T−24 h, T−3 h y T−60 min, la referencia de mercado sin margen y las métricas económicas siguen pendientes de disponibilidad verificable. La fase F2 conserva sus dos líneas abiertas. La reserva final y F5 quedan pendientes de autorización explícita.
