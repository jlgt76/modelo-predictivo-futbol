# Protocolo de validación de F5 experimental

## Datos, autorización y cortes

ADR-028 autoriza F5 exclusivamente sobre los 7.720 partidos de desarrollo de \`f3_base_v1\`. El manifiesto conserva el SHA-256 de la configuración, del snapshot, de los archivos de referencia de F4 y de las fuentes. 2025/26 y 2026/27 quedan fuera. Se consulta SQLite solo como bytes para verificar el hash. Cada objetivo conserva su X y su corte reconstruido D−2. El ajuste de un bloque usa el D−2 de su primera fecha, de modo que cualquier etiqueta de ajuste es admisible para todos sus objetivos. Elo dinámico actualiza el estado por fecha con lotes simultáneos. La evidencia reconstruida permanece separada de T−24 h, T−3 h y T−60 min verificables.

| Tramo | Uso |
| --- | --- |
| 2021/22 | Historia inicial, sin puntuaciones fuera de muestra exigidas |
| 2022/23 y 2023/24 | Selección en bloques de 28 días, ventana expansiva |
| Primera parte de 2024/25 | Ajuste y selección interna de calibración con predicciones fuera de muestra |
| Enero a mayo de 2025 | Evaluación interna ya observada en F4, comparación descriptiva de decisiones congeladas |
| 2025/26 | Reserva con acceso pendiente de autorización |

## Ajuste, variables y modelos

Los grupos y parámetros completos figuran en el [prerregistro](CONFIG_F5.json). Se comparan formulaciones reducidas, intermedias y ampliadas. Cada bloque ajusta medianas y niveles categóricos con su pasado elegible. Si una columna carece de observaciones en el bloque, su constante técnica de imputación se acompaña de un indicador de faltante. Los árboles no requieren escalado. La optimización de XGBoost aplica early stopping en los últimos 56 días **del pasado elegible**, con un embargo D−2 del entrenamiento interno. Después se reajusta sobre el pasado disponible con el número de árboles fijado. Con muestra insuficiente se usa el presupuesto fijo. Ningún preprocesador aprende del bloque externo.

Las señales Elo provienen de una versión fija de Elo E1 con K 20 y localía nominal 55, ajuste de probabilidad en el pasado del bloque y ratings dinámicos por fecha. Las señales de P2 y DC2 reutilizan predicciones de F4 con corte comprobado. Las variantes P2 y DC2 se seleccionaron en F4 usando 2022/23 y 2023/24, por lo que reutilizarlas en las ablaciones y en H5 es una investigación de desarrollo. La comparación de esas configuraciones en los mismos años no constituye una confirmación independiente. La selección de sus parámetros por bloque y sus tasas quedan fuera del resultado objetivo.

H1 y H2 estiman tasas con objetivos Poisson nativos. H3 reutiliza H1 y maximiza condicionalmente en rho sobre tasas H1 históricas fuera de muestra. H5 usa \`log(lambda_P2)\` como offset de XGBoost y aprende una corrección multiplicativa. H4 compara el mismo XGBoost con y sin señales Elo. Las tasas son esperanzas de goles reglamentarios obtenidas del histórico. El xG observado de tiros, las variables avanzadas, las cuotas y los metadatos retrospectivos quedan fuera.

Los ensembles S1/S2/S3 usan X1 y LGB1, variantes prefijadas de grupos A–D, y B3, referencia determinista. Se excluyen del metaestimador los ganadores retrospectivos de F4 y los modelos que contienen sus señales. S1 es soft voting equiponderado. S2 ajusta pesos convexos y S3 una logística regularizada sobre log-razones. En cada bloque usan únicamente pronósticos base previos, comunes, fuera de muestra y con etiquetas D−2 admisibles. Los primeros bloques conservan S1 como respaldo si falta historia. G1 mezcla las matrices de H1 y H2 con pesos iguales. Una mezcla conjunta valida su masa antes de derivar los mercados.

## Selección, calibración y evaluación

La selección compara Log Loss 1X2 sobre partidos comunes de ambas temporadas, con límite de 0,005 frente a E2 en cada una e IC95 favorable con bloques de 7 y 14 días. También exige no perder frente a P2, DC2 y L2 en el agregado, limitar el deterioro de Brier y ECE de empate a 0,005 y lograr 99 % de cobertura sin respaldo en selección. La promoción generativa aplica su propio umbral de 0,005 de pérdida de marcador exacto por temporada frente a P2, intervalos pareados con P2 y DC2, control de deterioro en mercados y cobertura. El criterio de complejidad se refleja en conservar la referencia cuando falta evidencia para promover. Los diagnósticos posteriores al congelamiento no cambian este resultado.

La calibración se divide internamente por fecha con retención final de 70 días y embargo D−2. La comparación enfrenta emisión bruta, temperatura y logística multinomial sobre log-probabilidades. Se exige el soporte prerregistrado por clase y mejora interna mínima de 0,001 antes de readaptar el calibrador seleccionado a toda su muestra elegible. La calibración isotónica queda aplazada por el soporte disponible por clase y partición. Las variantes generativas comparan además una escala común de tasas elegida por pérdida de marcador exacto. Se mantienen separados los perfiles brutos, 1X2 calibrados y conjuntos calibrados. Solo una emisión con matriz conjunta puede producir mercados de goles.

Las métricas de clasificación se calculan con orden 1, X, 2. Los mercados binarios usan Brier medio y pérdida logarítmica con piso de 10⁻¹⁵. Se mide pérdida y Brier multiclase del marcador exacto, error de ambas esperanzas y dispersión de Pearson. El soporte 0–32 por lado se comprueba con una cola máxima de 10⁻⁸. La incertidumbre pareada se aproxima por bloques de 7 y 14 días. Los partidos de un club pueden quedar repartidos entre bloques, por lo que los intervalos conservan dependencia residual. El análisis de empate conserva argmax y utiliza además AUC, precisión promedio, probabilidades, Brier, pérdida binaria y fiabilidad.

La interpretación usa importancias nativas, permutación en el bloque externo y TreeSHAP exacto de XGBoost sobre márgenes de clase. Se preservan las máscaras de faltantes y niveles categóricos al permutar su variable de origen. Las explicaciones locales corresponden a ejemplos históricos. Las correlaciones pueden repartir o alterar las atribuciones. No se interpretan como efectos causales.
