# Variables del modelo base y avanzado

Diseño de F1. Cada variable tendrá unidad, fórmula, población, ventana, instante de disponibilidad, versión y motivo de ausencia. Se aprobará por competición, temporada, nivel y horizonte. Un dato faltante se conserva como desconocido. Las transformaciones aprendidas se ajustarán dentro del entrenamiento cronológico.

## Modelo base

| Familia | Cálculo propuesto y límites |
| --- | --- |
| Resultados y localía | Victorias, empates, derrotas y goles a favor/en contra en 90 minutos. Separar local, visitante y sede neutral. |
| Ataque y defensa | Tasas de goles por equipo, ajustadas por localía, rival y competición, con regularización hacia una referencia cuando la muestra sea pequeña. |
| Forma 5, 10 y 20 | Resumir los últimos N partidos terminados y publicados antes del corte. Conservar tamaños reales y evaluar ventanas generales, por localía y por competición cuando tengan soporte. |
| Elo y calidad del rival | Usar el Elo previo a cada encuentro histórico y actualizarlo después de conocer el resultado. Documentar ascensos, clubes con poco historial y comparabilidad entre ligas. |
| Rendimiento ajustado por rival | Promediar residuos entre rendimiento observado y esperado frente al rival, con expectativas calculadas usando información anterior a aquel partido. Comparar con agregados sin ajuste. |
| Ponderación temporal | Propuesta de peso exponencial `exp(-ln(2)*edad_días/vida_media)`. Normalizar por suma de pesos y elegir la vida media en desarrollo. Mantener ventanas sin ponderar como referencia. |
| Competición | Tasas y rendimiento por torneo, fase y régimen de formato. Agrupar o regularizar estimaciones con poca exposición. |
| Descanso y carga | Días desde el último compromiso completado y partidos/minutos recientes. Exigir cobertura de copas, otras ligas y compromisos pertinentes. Con calendario incompleto, marcar cobertura parcial o abstenerse. |

## Modelo avanzado

Amplía el nivel base con xG y xGA históricos de definición homogénea, estados de lesión/suspensión, convocatorias, onces probables y confirmados, minutos y rendimiento individual. Usa formaciones, cambios de entrenador y contexto competitivo si sus revisiones eran conocidas. Los indicadores de motivación se limitan a hechos observables como puntos, desempates, partidos restantes y marcador global anterior. Definir «necesita ganar» respecto a una condición explícita de clasificación o permanencia y a las reglas conocidas. No atribuir estados mentales a partir de la clasificación.

| Variable | Cálculo propuesto y evidencia |
| --- | --- |
| Índice de rotación | `1 - tamaño(intersección de onces)/11` con dos onces completos comparables. Especificar si la referencia es el último once o uno habitual estimado con historia anterior al corte. Para onces probables, calcular el índice por escenario de once completo. |
| Continuidad de titulares | Fracción de titulares proyectados que repiten respecto a la referencia, complementada con frecuencia de titularidad y minutos recientes. Conservar denominadores y distinguir continuidad de causa de cambio. |
| Titulares lesionados y suspendidos | Contar por separado integrantes del once de referencia previo con baja documentada. Registrar dudas, elegibilidad específica del torneo, cobertura y coincidencias entre causas para evitar duplicar la misma ausencia. |
| Minutos históricos perdidos | Sumar minutos esperados en partidos anteriores perdidos por bajas documentadas. Estimar cada expectativa con minutos y roles conocidos antes de ese encuentro. Distinguir proxy estimado de minutos realmente disputados. |
| Aporte ofensivo y defensivo ausente | Agregar aportes por rol y exposición esperada, estimados con estadísticas previas y regularización por posición y minutos. Usar métricas ofensivas y defensivas compatibles con el proveedor. Evitar sumar estimaciones que cuenten dos veces el mismo efecto de equipo. |
| Calidad relativa del sustituto | Comparar titular y reemplazo plausible en el mismo rol y unidad de exposición. Guardar escenarios si hay varios sustitutos y marcar soporte insuficiente para jugadores con pocos minutos. |
| Impacto en xG y xGA | Contrastar la proyección con el once de referencia y la proyección con sustituciones factibles, manteniendo fijo rival, sede y contexto. Guardar por separado pérdida de xG propio y aumento de xGA, dirección, intervalo, versión del estimador y soporte. Validar con xG/xGA vistos después y ablaciones cronológicas. Es un contraste predictivo sujeto a confusión táctica y selección. |
| Fatiga por jugador y equipo | Usar minutos previos ponderados por recencia, descanso y cobertura del calendario. Agregar por once proyectado y minutos esperados. La carga observada es un indicador indirecto de fatiga. |
| Fortaleza de la alineación | Combinar aportes regularizados, roles, exposición y continuidad. Comparar con la fuerza habitual del equipo mediante ablaciones. Mantener separado el componente ofensivo del defensivo. |
| Entrenador y formación | Fecha efectiva y publicación del cambio, partidos previos bajo el entrenador y formación probable/confirmada. Las formaciones observadas durante el juego sirven como historia de partidos previos o como etiquetas. |

El indicador de ausencia relevante usa el umbral configurable inicial **0.20 xG por partido**. Se activa cuando la pérdida estimada de xG propio o el aumento estimado de xGA llega a 0.20. Guardar componente, signo, estimación e intervalo, y marcar «indeterminado» si falta soporte. El umbral clasifica una estimación y no se resta automáticamente a la tasa de goles. Para «rotación excesiva», definir un umbral configurable sobre el índice o cambios de titulares y fijarlo con distribución histórica en desarrollo por contexto antes de evaluar. El valor numérico queda pendiente de evidencia.

## Disponibilidad por corte

| Horizonte | Información que puede incorporarse si está disponible |
| --- | --- |
| T−24 h | Predicción inicial con historia y contexto conocidos. |
| T−3 h | Convocatorias, bajas, sanciones y escenarios de onces probables publicados hasta el corte. |
| T−60 min | Onces confirmados, rotaciones, novedades y cuotas vigentes con evidencia anterior o igual al corte. |

Un once probable se representa con escenarios completos y pesos estimados dentro de desarrollo si hay evidencia suficiente. Un once publicado después de T−60 min no modifica esa predicción. Si un dato avanzado falta, emitir el modelo base validado para ese mismo horizonte, si existe, y registrar la causa. La evaluación mide tanto el subconjunto común como la cobertura total de esta política.

## Habilitación y validación

Las variables avanzadas siguen en el alcance. Pueden pasar de «pendiente de datos» a «elegible» cuando se documenten permisos, identidad, cobertura, revisiones, evidencia temporal y consistencia, con aprobación del conjunto correspondiente. La captura prospectiva autorizada puede resolver campos que un histórico gratuito no conserva. La activación se valida con ablaciones pareadas sobre los mismos partidos y cortes, incluyendo tamaños de muestra, intervalos y desempeño por horizonte. Registrar si una variable carece de soporte y qué evidencia permitiría revisarla.
