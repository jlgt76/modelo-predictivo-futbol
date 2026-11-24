# Protocolo propuesto de validación · F3 experimental

Propuesta para aprobar antes de ajustar modelos. Universo de 7.720 partidos en 2021/22–2024/25. Cada fila ya tiene X reconstruida con su propio corte D−2. Excluir 2026/27. La edición 2025/26 queda aislada sin leer etiquetas para desarrollo y no puede emplearse hasta la evaluación autorizada de reserva.

| Bloque calendario propuesto | Uso posterior autorizado por fase |
| --- | --- |
| 2021/22 | Historia de arranque y entrenamiento inicial. Marcar historial corto. Informar cuántos partidos afectan las reglas de cobertura. |
| 2022/23 | Selección inicial mediante walk-forward con ventana expansiva y bloques sucesivos de cuatro semanas, días completos. |
| 2023/24 | Segunda ronda de selección walk-forward. Congelar candidatos, fórmulas, tolerancias, presupuesto y estrategia antes de calibrar. |
| 2024/25 hasta 2024-12-31 inclusive | Calibrar con predicciones fuera de muestra de los candidatos ya fijados y con etiquetas elegibles. |
| 2024/25 desde 2025-01-01 | Evaluación interna de desarrollo. Se admite actualización expansiva del estimador solo con política prefijada y resultados elegibles. Mantener el calibrador congelado en esta comparación. |
| 2025/26 | Prueba final reservada. Acceso separado y explícito. Salvo autorización futura, ninguna etiqueta alimenta X, EDA ni selección, calibración o ajuste. |

El EDA de F3 describe las cuatro temporadas. Por ello el bloque de 2024/25 es una evaluación interna y la prueba final es la única reserva sin explorar. Para cada objetivo D, los bloques de entrenamiento tienen como última fecha admisible D−2. Para el primer objetivo de un bloque, el calibrador y la selección también deben respetar su corte. Los días cercanos a la transición se omiten de las etiquetas utilizables hasta que entren por la política prevista. Congelar todos los partidos del mismo día en el mismo bloque. Reportar por cada bloque fechas, n, distribución, calidad, tamaño de historia y alcance realmente evaluable.

## Comparación y métricas

- **Primaria propuesta:** Log Loss 1X2 = promedio de `−log(p de la clase observada)`. Definir tratamiento de ceros y mostrar cuántos se recortaron. Menor es mejor.
- **Brier multiclase:** promedio de la suma sobre 1/X/2 de `(p_k−y_k)^2`, rango [0,2].
- **RPS:** para 1/X/2 en ese orden, promedio de `[(p_1−y_1)^2 + (p_1+p_X−y_1−y_X)^2]/2`, rango [0,1].
- **Accuracy secundaria:** fracción de clases argmax acertadas, con regla de empates prefijada y distribución por clase.
- **Calibración:** diagramas por clase y competición, n por bin e intervalos. Proponer límites de bins acordados antes de evaluar. Reducir desgloses de baja potencia con aviso explícito.
- **Incertidumbre:** remuestreo pareado por bloques de fechas con partidas simultáneas juntas, intervalos 95 %, sensibilidad a longitud y dispersión por competición. La dependencia a través de equipos limita la precisión.
- Mismos partidos para comparación pareada, con resultados por competición y horizonte. Comparar con frecuencias históricas suavizadas, una referencia de localía y Poisson de tasas medias calculadas solo con el pasado elegible. Un benchmark de mercado sin margen requiere precios admisibles. Sin evidencias y reglas, métricas económicas quedan no evaluables.

Poisson, Dixon-Coles y los híbridos podrán consumir goles a 90 minutos y variables por equipo como entradas separadas. Elo secuencial podrá consumir la cronología y las identidades mediante el contrato del diccionario. Clasificación multinomial, XGBoost, LightGBM, Random Forest, Extra Trees y ensembles tendrán el mismo índice cronológico de X/y. Toda selección supervisada, imputación, escalado, codificación aprendida, regularización, búsqueda, ponderación de ensembles y calibración se ajustará en su bloque permitido. Las correlaciones descriptivas no eliminan variables automáticamente. Priorizar parsimonia cuando la diferencia pareada sea pequeña o incierta.

Los tres horizontes **T−24 h, T−3 h y T−60 min** conservan la exigencia de evidencia temporal propia. La evaluación D−2 se reportará como reconstruida y separada. F4 requiere autorización explícita posterior.
