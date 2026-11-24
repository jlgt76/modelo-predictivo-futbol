# F5 experimental · Machine Learning, híbridos y calibración

**La selección de F5 conserva Elo E2 para 1X2 y Poisson P2 para marcadores.** Ningún candidato superó los criterios fijados antes del ajuste. E2 conserva también su condición de selección congelada de F4.

## Selección walk-forward

Se compararon los modelos sobre los mismos 3.828 partidos de 2022/23 y 2023/24. Los finalistas por familia fueron X2, LGB2, RF1 y ET2. Extra Trees ET2 obtuvo el menor Log Loss 1X2 de los candidatos, **0,98552** frente a **0,98632** de E2. Sus diferencias por temporada fueron −0,00006 y −0,00157, por debajo de la mejora mínima exigida en magnitud. El intervalo pareado semanal agregado fue **[−0,00579; +0,00423]**. Las variantes ampliadas de XGBoost y LightGBM tuvieron una pequeña ventaja en 2023/24 y una pérdida en 2022/23 respecto a E2.

H5 obtuvo el menor Log Loss de marcador exacto entre los híbridos, **2,94104** frente a **2,94236** de P2. La diferencia fue +0,00082 en 2022/23 y −0,00355 en 2023/24. Su intervalo pareado semanal fue **[−0,00404; +0,00142]** y tuvo respaldo P2 en el 9,72 % de los objetivos de selección. H1, H2, H3 y G1 obtuvieron pérdidas agregadas de marcador exacto superiores a P2. Se conservaron los resultados positivos y negativos sin elegir hiperparámetros ni calibradores a partir de la evaluación interna.

## Diseño y control de datos

El universo autorizado contiene 7.720 partidos de desarrollo. El arranque 2021/22 aporta 1.951 etiquetas elegibles conforme avanzan las fechas. Los tramos fuera de muestra contienen 3.828 partidos de selección, 926 de calibración y 1.015 de evaluación interna. Los modelos avanzados siguen deshabilitados. Se verificaron los snapshots F3/F4 y el hash de SQLite v3. La prueba final 2025/26 y las etiquetas 2026/27 quedan excluidas. La evaluación interna de enero a mayo de 2025 ya era conocida por F4 y conserva carácter exploratorio.

Se fijaron configuraciones parsimoniosas antes de ajustar. Los conjuntos reducido, intermedio y ampliado contienen 23, 36 y 60 variables previas a codificación. La selección compara candidatos de XGBoost, LightGBM, Random Forest y Extra Trees. Se conserva el contraste de ablación en ambos años y la búsqueda de XGBoost usa parada temprana cronológica interna. Se reutilizan B0, B1, B2, B3, P2, DC2, E2 y L2 sobre los mismos objetivos y cortes.

- **H1 y H2.** XGBoost y LightGBM estiman conteos Poisson por lado con tasas acotadas y una matriz conjunta de goles reglamentarios.
- **H3.** Usa las tasas H1 y ajusta condicionalmente rho por verosimilitud con pronósticos H1 pasados fuera de muestra. El respaldo con rho cero conserva Poisson mientras falta historia. Las tasas quedan fijas durante el segundo paso.
- **H4.** Compara XGBoost con y sin ratings previos, diferencia y probabilidades de Elo E1.
- **H5.** Aprende una corrección multiplicativa mediante offset logarítmico de P2. Usa solo offsets históricos fuera de muestra y vuelve a P2 si hay poca historia de corrección.
- **S1, S2 y S3.** Soft voting equiponderado, mezcla de pesos convexos y stacking logístico. Las tres entradas son X1, LGB1 y B3, fijadas con anterioridad al experimento. S2 y S3 empiezan con S1 hasta disponer del mínimo prerregistrado de emisiones OOF comunes.
- **G1.** Mezcla las matrices de H1 y H2 por igual. Los mercados resultan de la matriz de la mezcla. Las medias de goles publicadas son las esperanzas marginales de esa matriz.

La escala de tasas de la calibración generativa cambia la distribución conjunta completa. La temperatura y la calibración logística multinomial se aplican solo a 1X2 y doble oportunidad, en emisiones separadas. Estas decisiones se toman dentro del tramo de calibración, sin usar enero–mayo de 2025. P2 y DC2 mantienen el diseño de F4. En particular, DC2 conserva el ajuste condicional en dos pasos.

## Reproducibilidad y límites del alcance

Se usó Python 3.14.5, un hilo por estimador y dependencias fijadas en [requirements-f5.txt](../requirements-f5.txt). El experimento y la auditoría derivada exigen un directorio de salida nuevo. Los modelos, preprocesadores, pesos y calibradores se conservan por bloque o en su registro de configuración. Las etiquetas están en un archivo separado. En el pronóstico, D−2 es el corte histórico reconstruido y \`generado_utc\` identifica el inicio real de la emisión por lotes de la corrida. El timestamp no acredita disponibilidad histórica de la fuente.

El manifiesto identifica snapshot, configuración, versión y archivos. Las emisiones con marcador incluyen los componentes \`[lambda_local, lambda_visitante, rho, peso]\` para reconstruir la matriz. Las variables por modelo se registran en el archivo de predicciones y, para las mezclas, también en el prerregistro y el registro de ajustes. Consultar la [política de validación](PROTOCOLO_VALIDACION_F5.md) para reproducir cortes, promoción e intervalos.

\`\`\`powershell
.\\.venv\\Scripts\\python.exe scripts/experimento_f5.py --salida data/processed/f5_reproduccion_01
.\\.venv\\Scripts\\python.exe scripts/auditoria_f5.py --origen data/processed/f5_reproduccion_01 --salida data/processed/f5_auditoria_reproduccion_01
.\\.venv\\Scripts\\python.exe -m unittest discover -s scripts -p 'test_*.py'
\`\`\`

Quedan pendientes los horizontes T−24 h, T−3 h y T−60 min verificables, la cobertura y los contratos pendientes de F2-A/F2-B, el modelo avanzado con evidencia temporal, la comparación sin margen y las métricas económicas. La protección y la interpretación del bloque de evaluación interna se mantienen aunque F5 haya ajustado modelos experimentales. Las señales de P2/DC2 en F5 tienen ventanas causales por partido, pero sus variantes fueron elegidas en el mismo período de selección de F4. El stacking evita esa dependencia mediante entradas prefijadas sin esas señales.

Las interfaces de modelos y de atribuciones usadas en la implementación están documentadas por sus proyectos. [API de XGBoost 3.4.1](https://xgboost.readthedocs.io/en/stable/python/python_api.html?highlight=early_stopping_rounds) y [API de LightGBM](https://lightgbm.readthedocs.io/en/stable/_modules/lightgbm/sklearn.html).
