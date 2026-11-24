# Metodología estadística y registro de riesgos

Estado: diseño F1. No contiene probabilidades calculadas, recomendaciones de apuestas ni métricas empíricas. Los métodos se implementarán y explicarán por fases después de aprobar datos y protocolo.

Ampliación: evaluación neutral de mercados, multiobjetivo/Pareto, objetivos de multiplicador y sensibilidad ±1/±3/±5 pp. El presupuesto inicial propuesto de $0 MXN limita los datos disponibles, no autoriza imputar precios o efectos de jugadores. F2 continúa pendiente.

## Pregunta predictiva y universo

Estimar una distribución del resultado de 90 minutos más descuento con la información disponible en T−24 horas, T−3 horas y T−60 minutos. Cada corte tiene evaluación y calibración propias. Separar resultado del partido, resultado de la eliminatoria, prórroga y penaltis.

Fijar antes del ajuste: competiciones, temporadas, partidos excluidos, horizontes, variables, comparadores, presupuesto de búsqueda y métricas. Conservar equipos descendidos y ascendidos del histórico; seleccionar clubes por su participación actual produciría sesgo de supervivencia. El conjunto elegible se determina por calidad y contrato, no por aciertos posteriores.

## Evitar filtración de información

Aplicar el [contrato temporal](BASE_DATOS.md) tanto a las variables como a las etiquetas disponibles para ajustar/recalibrar. Un partido iniciado antes del corte puede seguir en juego; `shift(1)` no basta para asegurar que su resultado era conocido. Ordenar por disponibilidad, congelar los estados de partidos simultáneos y actualizar Elo cuando se publique el resultado.

Casos prohibidos: usar promedios de toda la temporada, ranking final, lesiones reconstruidas después, xG del propio partido, alineación confirmada posterior al horizonte, cuotas de cierre para una decisión anterior o escaladores ajustados sobre todos los años. Las revisiones posteriores no deben cambiar snapshots congelados.

Los transformadores aprendidos se ajustan dentro de cada entrenamiento. Una arquitectura con `Pipeline` ayuda a separar transformaciones, pero no corrige variables creadas previamente con datos futuros. Referencia: [errores comunes y leakage, scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html).

No es posible demostrar ausencia absoluta de filtración mediante una sola prueba. El objetivo obligatorio es impedirla por diseño, auditar invariantes y declarar dónde la fuente no permite reconstruir la disponibilidad histórica.

## Validación cronológica propuesta

La división se hace por fechas y disponibilidad de etiquetas, no por orden aleatorio ni número de filas sin contexto. `TimeSeriesSplit` señala el requisito de muestras equiespaciadas para comparar duraciones; los partidos requieren cortes propios de calendario. Referencia: [documentación de TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).

Secuencia de cada corte externo:

1. Entrenar con el pasado admisible. Seleccionar hiperparámetros mediante cortes internos todavía anteriores al periodo externo.
2. Generar predicciones pasadas fuera de muestra para ajustar el calibrador, con etiquetas ya disponibles al corte externo. No entrenarlo con las mismas predicciones ajustadas a sus propias etiquetas por el estimador base.
3. Evaluar sobre el bloque posterior, sin retocar parámetros por lo observado en ese bloque.
4. Avanzar en el tiempo con una política preregistrada de ventana expansiva o deslizante, actualización y demora de etiquetas. Una actualización dentro de evaluación solo usa resultados ya publicados.
5. Reservar un periodo final sin explorar. Una estrategia nueva diseñada después de verlo requiere datos nuevos para su confirmación.

Propuesta de partida: cinco temporadas completas, con dos iniciales, dos para desarrollo walk-forward y una final reservada. Fechas exactas, anchura de bloques, calibración y frecuencia de actualización se fijan en F3 después de medir cobertura. Si no hay datos suficientes, reducir alcance o esperar evidencia; no duplicar partidos para crear una muestra aparente.

El embargo entre ventanas se deriva de la publicación de etiquetas y del solapamiento del objetivo. Compartir historia pasada conocida en ventanas de 5, 10 y 20 partidos es admisible. Asignar todas las filas del mismo partido, incluidos sus tres cortes, niveles y mercados, al mismo bloque externo. Dentro de ese bloque cada corte conserva su información propia. Bloquear partidos simultáneos y exigir etiquetas publicadas antes de cada ajuste interno.

## Qué aporta cada modelo

| Modelo | Interpretación y salida | Supuestos y controles |
| --- | --- | --- |
| Frecuencia histórica | Probabilidades 1X2 por liga estimadas solo con el pasado | Referencia mínima; suavizar si procede y reportar muestra |
| Poisson | Tasas positivas de goles locales/visitantes; matriz de marcadores | Ataque, defensa y localía; independencia condicional de goles en la versión básica, equidispersión y estabilidad aproximada |
| Dixon-Coles | Ajusta la masa de marcadores bajos y admite ponderación temporal | Restricciones para evitar probabilidades negativas; decaimiento elegido sin futuro; no modela toda dependencia posible |
| Elo | Estado dinámico de fuerza relativa antes de cada partido | Inicialización, ascensos, ventaja local y actualización documentadas; expectativa de puntuación no equivale a probabilidades 1X2 |
| Regresión logística multinomial | Probabilidades 1X2 y referencia supervisada con Elo y variables deportivas | Regularización y preprocesamiento aprendidos solo en entrenamiento. Con tres clases permite derivar doble oportunidad. |
| XGBoost y LightGBM | Árboles potenciados como clasificadores o candidatos a regresión de tasas | Acotar profundidad, hojas, regularización, iteraciones y parada temprana en desarrollo cronológico. |
| Random Forest y Extra Trees | Ensambles de árboles como clasificadores o regresores | Acotar profundidad, variables por división, hojas y tamaño mínimo por hoja. |
| Híbridos ML + Poisson o Dixon-Coles | Estimar tasas de goles locales/visitantes y generar una distribución conjunta de marcadores | Tasas positivas, soporte, corrección de marcadores bajos válida en cada partido y comparación contra el modelo sin componente ML. |
| Ensemble de modelos seleccionados | Mezcla de distribuciones compatibles o de probabilidades de un mismo evento | Elegir integrantes y pesos no negativos que sumen uno usando predicciones anteriores fuera de muestra. |

Para el Poisson básico, si `H` y `V` son goles locales y visitantes y sus tasas son `λH, λV`, se propone:

`P(H=h,V=v) = Poisson(h; λH) × Poisson(v; λV)`.

Las tasas pueden modelarse con enlace logarítmico, ataque/defensa y localía, con restricciones de identificabilidad. Las probabilidades 1X2 se obtienen sumando las celdas `h>v`, `h=v` y `h<v`. Esto es una definición del futuro modelo, no una estimación obtenida de datos.

Dixon-Coles es una referencia de la literatura sobre regresión Poisson y dinámica de equipos. Su evaluación histórica no acredita rentabilidad en temporadas actuales. Referencia primaria: [Dixon y Coles, 1997](https://rss.onlinelibrary.wiley.com/doi/10.1111/1467-9876.00065).

Medir sobredispersión, errores por marcadores y evolución de fuerzas. Si los supuestos fallan, comparar extensiones en desarrollo, sin sustituir modelos solo porque mejoran ganancias retrospectivas. Para equipos de otras ligas o recién ascendidos, usar una inicialización/regularización justificada y declarar mayor incertidumbre.

Para un híbrido, ajustar la esperanza condicional de goles observados con una pérdida apropiada para conteos y un enlace que asegure tasas positivas o una transformación validada. Las tasas proyectadas representan goles por partido. El xG observado del proveedor es otra medida. Con tasas `λH, λV` de ML, Dixon-Coles exige por predicción `max(-1/λH,-1/λV) ≤ ρ ≤ min(1,1/(λH*λV))` para mantener no negativos los cuatro factores de corrección. Si la corrección falla fuera de entrenamiento, conservar el diagnóstico y aplicar Poisson solo bajo una regla de respaldo preregistrada y evaluada fuera de muestra. Comprobar normalización, cola, goles esperados y calibración marginal.

Una mezcla de matrices de marcadores válidas conserva la coherencia. Los clasificadores 1X2 solo se mezclan como predictores de resultados y doble oportunidad, salvo que un procedimiento de reconciliación validado produzca una matriz compatible. Usar predicciones cronológicas fuera de ajuste para estimar la corrección híbrida cuando se haga en dos etapas, seleccionar y ponderar componentes del ensemble. Calibrar el resultado en un bloque posterior separado y evaluar en el bloque externo.

Fijar presupuesto de búsqueda, espacio de hiperparámetros, semillas y métrica antes de la comparación. En cada bloque externo, ajustar transformadores, selección de variables, parada temprana y parámetros exclusivamente con divisiones internas anteriores. Registrar regularización por candidato y evaluar diferencias pareadas contra referencias simples, incluyendo incertidumbre por bloques. Comparar base y avanzado en partidos comunes para estimar la aportación de datos y en el universo completo para medir cobertura de la política. Exigir evidencia por horizonte para promover un candidato. Ante resultados indistinguibles, conservar el más simple.

Plan de interpretación. Usar importancia por permutación en bloques de desarrollo no usados para ajustar el modelo, con grupos de variables correlacionadas y ablaciones cuando proceda. Calcular SHAP global y por partido sobre el espacio de salida declarado, con referencia derivada del entrenamiento y revisión de estabilidad temporal. En un híbrido, distinguir explicación de la tasa y explicación de un mercado derivado. Las atribuciones describen al estimador. El diseño de variables y estimación de ausencias se detalla en [Feature engineering](FEATURE_ENGINEERING.md).

## Métricas y criterios de comparación

Orden fijo de clases 1X2: local, empate, visitante. Reportar media por partido y desgloses por competición, temporada, horizonte y cobertura. No tratar varias cuotas del mismo partido como nuevos resultados independientes.

| Métrica | Convención del proyecto |
| --- | --- |
| Brier 1X2 | `mean_i(sum_k((p_ik - y_ik)^2))`, rango 0–2; no dividir por tres ni por dos silenciosamente |
| Brier binario | `mean_i((p_i - y_i)^2)`, rango 0–1 |
| Log Loss | `mean_i(-ln(p_i,clase_observada))`; logaritmo natural |
| Calibración | Diagramas de fiabilidad por clase/mercado, recuentos e intervalos por bin; ECE complementaria, con bins preregistrados |

Las bibliotecas pueden cambiar valores predeterminados y escalas; fijar nuestra convención y probarla con casos manuales. Fuentes: [Brier Score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html) y [Log Loss](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html).

Conservar probabilidades originales; cualquier recorte numérico para calcular Log Loss tendrá epsilon explícito y contador de valores afectados. Una probabilidad cero asignada a un resultado observado se reporta como fallo de soporte, no se oculta tras el recorte. La matriz truncada tendrá masa omitida medida; ampliar soporte hasta tolerancia y documentar cualquier renormalización. Nunca interpretar la probabilidad fuera del corte como cero real.

Comparar modelos sobre los mismos partidos y con diferencias pareadas. Propuesta de incertidumbre: intervalos al 95 % mediante remuestreo por bloques de calendario, con mercados de un encuentro agrupados y sensibilidad al tamaño de bloque; la dependencia entre clubes limita su precisión. Publicar dispersión entre temporadas y muestra efectiva, no solo media global.

La regla de promoción se fija en F3: métrica primaria, mejora mínima relevante y tolerancia de no deterioro en calibración/subgrupos. Si los datos no distinguen candidatos, conservar el más simple. No hay umbral universal de Brier o ROI que certifique rentabilidad.

## Calibración y coherencia conjunta

Una buena probabilidad debe concordar con frecuencias observadas en grupos comparables. Brier mezcla componentes de fiabilidad y discriminación; su mejora aislada no prueba mejor calibración. Comparar predicciones originales y calibradas en un bloque posterior, con tamaños por bin. El calibrador necesita datos separados del ajuste del modelo base. Referencia: [calibración de probabilidades, scikit-learn](https://scikit-learn.org/stable/modules/calibration.html).

Seleccionar y versionar el calibrador para cada horizonte y variante publicada, incluido cualquier respaldo base. Comparar calibración original frente a métodos candidatos como ajuste sigmoide o isotónico cuando la muestra lo sustente. Evaluar por corte y comparar la mejora incremental sobre los mismos partidos. Si un horizonte carece de evidencia para calibrar, registrar estado no evaluable o no habilitado. Una alineación que llega tarde jamás se traslada a un corte anterior.

Para alimentar parlays, no basta calibrar independientemente 1X2, totales y ambos anotan: podrían dejar de corresponder a una única matriz de marcadores. Mantener una distribución conjunta calibrada o reconciliarla con un procedimiento validado. Si no se logra, esas predicciones marginales pueden evaluarse individualmente, pero quedan fuera del cálculo conjunto.

## Evaluación neutral e identidades matemáticas

El universo comprende todas las ofertas observadas de **1X2, doble oportunidad (1X/X2/12), Over, Under y BTTS sí/no**, con sus líneas, periodos y reglas. Se aplican idénticos controles de tiempo, calidad, costes y elegibilidad, sin priorizar una familia ni suprimir resultados adversos. Publicar evaluados, rechazados y no evaluables por familia; la falta de oferta no se interpreta como probabilidad cero. No se presume que Draftea ofrezca todas las familias en cada partido.

Para una misma distribución de goles de 90 minutos, mismas versiones y mismo corte, exigir:

| Relación | Invariante |
| --- | --- |
| 1X2 | `p1 + pX + p2 = 1` |
| Doble oportunidad | `p1X = p1+pX = 1-p2`; `pX2 = pX+p2`; `p12 = p1+p2`; las tres suman **2**, no 1 |
| Total en media línea `L` | `P(Over L)+P(Under L)=1` |
| Total en línea entera `L` | `P(Over L)+P(Under L)+P(goles=L)=1`; la igualdad puede liquidarse como push según contrato |
| Monotonicidad | Si `L1<L2`, `P(Over L1)>=P(Over L2)` y `P(Under L1)<=P(Under L2)` |
| BTTS | `P(sí)+P(no)=1`; `P(sí)<=P(Over 1.5)` |
| Inclusión/intersección | Si `A` implica `B`, `P(A)<=P(B)` y `P(A∩B)=P(A)`; incompatible → cero; cotas de Fréchet para el resto |

Comprobar tolerancias numéricas, soporte y masa de cola antes/después de calibración y de cada perturbación. Líneas asiáticas de cuarto de gol y pagos parciales requieren estados de liquidación específicos, nunca se reducen automáticamente a una etiqueta binaria. Si un mercado no está soportado, permanece inventariado con motivo; neutralidad no significa calcular un contrato mal definido.

## Comparadores simples y de mercado sin margen

Usar como mínimo frecuencias históricas calculadas solo con el pasado y un Poisson de tasas medias de liga como referencias simples cuando sus salidas sean compatibles con el evento; registrar suavizado/ventanas. Comparar los modelos candidatos con estas referencias sobre idénticos partidos, horizontes y definiciones, con Brier, Log Loss y calibración, además del tamaño y sesgo del subconjunto con cuotas.

El benchmark de mercado requiere precios contemporáneos de selecciones exhaustivas y excluyentes: 1X2 completo, Over/Under de media línea o BTTS sí/no. Aplicar un método de quitar margen fijado antes de evaluar. Para doble oportunidad, derivar `q1X=q1+qX`, etc., del **1X2 sin margen de la misma casa/corte** cuando exista; etiquetar como referencia derivada. Alternativamente se requiere un contrato complementario válido. No normalizar 1X, X2 y 12 como tres clases excluyentes. Una discrepancia entre precios de familias se reporta; no se fuerza coherencia de precios observados a costa de ocultar arbitrajes o errores.

Sin mercado completo, mostrar probabilidad implícita bruta donde proceda y dejar sin margen «no evaluable». No construir la probabilidad sin margen de un parlay multiplicando referencias marginales dependientes. Cuotas posteriores al corte pueden ser referencia retrospectiva de cierre, nunca benchmark disponible al emitir la predicción. Con la ruta gratuita básica, este comparador puede estar ausente para gran parte del histórico: se informa, no se sustituye con cuotas inventadas.

## Probabilidad implícita, margen, Edge y EV

Para cuota decimal `o > 1` y probabilidad calibrada `p`:

`p_implicita = 1/o`

`edge_bruto = p - p_implicita`

Para un conjunto exhaustivo y excluyente del mismo mercado, casa e instante compatible, la eliminación proporcional del margen es:

`q_j = (1/o_j) / sum_k(1/o_k)`; `overround = sum_k(1/o_k) - 1`.

`edge_sin_margen = p - q_j`.

Esta normalización es un supuesto de reparto del margen, no una probabilidad verdadera observada. No aplicarla a mercados solapados como doble oportunidad ni a un conjunto artificial de mejores cuotas de distintas casas. Comparar otros métodos solo dentro del periodo de desarrollo.

Configuración inicial propuesta: `min_edge = 0.06`, `edge_reference = implied_raw`. Se exige diferencia absoluta de seis puntos porcentuales y EV neto positivo, además de calidad y vigencia del precio. La estimación de Edge también tiene incertidumbre; el umbral no la elimina.

En una selección binaria sin devolución ni comisión, beneficio esperado por unidad:

`EV = p × (o - 1) - (1 - p) = p × o - 1`.

Con devoluciones, liquidaciones parciales o comisiones, usar `EV = sum_s P(s) × beneficio_neto(s)` sobre todos los estados. No reutilizar la fórmula binaria para contratos distintos. Sin cuota observada o regla conocida, EV comercial queda «no evaluable».

Para un contrato con push íntegro, `1/o` se contrasta con `P(win)/(P(win)+P(loss))` como probabilidad condicionada a resolución, si el denominador es positivo; conservar además las probabilidades incondicionales y calcular EV con devolución. No mezclar ese Edge con el de acierto total sin indicar la base. Para combinaciones con recotización tras anulaciones o pagos parciales, no se define automáticamente Edge por `1/M`: exigir un contrato equivalente validado o marcarlo no evaluable. El filtro inicial de 0.06 se aplica a candidatos simples elegibles; `edge_scope` podrá ser `selection`, `combination` o `both`, fijado antes del backtest. Propuesta inicial: `selection`, con Edge conjunto reportado cuando sea definible y EV neto positivo obligatorio para la combinación; cambiar el alcance no es neutro y se registra.

## Dependencia y parlays

Para eventos `A` y `B` definidos sobre el mismo marcador:

`P(A ∩ B) = sum_(h,v) P(H=h,V=v) × I_A(h,v) × I_B(h,v)`.

Victoria local y más de 2.5 goles comparten celdas y no son independientes, incluso cuando Poisson asume independencia entre goles locales y visitantes. Eventos imposibles reciben cero; eventos redundantes no se cuentan dos veces. Para tres o más selecciones se necesita una conjunta completa: correlaciones por parejas no la determinan.

Los mercados de tarjetas, córners y jugadores requieren otros modelos y una dependencia conjunta validada. No se derivan de una matriz de goles. Entre partidos puede existir incertidumbre compartida por parámetros, equipos, calendario y otros factores; cualquier independencia condicional debe quedar declarada y sometida a sensibilidad. Para una probabilidad conjunta desconocida se pueden reportar cotas, por ejemplo `max(0, sum(p_i)-(n-1)) <= P(intersección) <= min(p_i)`, sin convertirlas en una estimación puntual.

La cuota conjunta ofrecida se registra con selecciones, casa, instante y reglas. El producto de cuotas simples no acredita una oferta de same-game parlay. En parlays entre partidos, multiplicar cuotas solo puede usarse como escenario explícito o cuando las reglas de la oferta lo justifiquen y se conserve evidencia.

## Optimización multiobjetivo y frontera de Pareto

Se sustituye la propuesta anterior de maximizar únicamente EV conservador. Para cada combinación factible `c`, conservar el vector con seis dimensiones y no reducirlo silenciosamente a un único score:

| Objetivo | Dirección | Definición propuesta |
| --- | --- | --- |
| Probabilidad de acierto | Maximizar | `p_hit`: probabilidad conjunta de satisfacer todas las selecciones; declarar por separado pushes/anulaciones |
| Multiplicador | Maximizar | `M`: retorno bruto total por unidad de una oferta observada y compatible, no producto inventado de cuotas |
| Edge | Maximizar | Diferencia con referencia explícita; para contrato binario sin devoluciones `p_hit-1/M`, con restricciones anteriores para otros contratos |
| EV | Maximizar | Beneficio neto esperado por unidad, incluidos todos los estados/costes; `p_hit*M-1` solo en contrato binario ordinario |
| Incertidumbre | Minimizar | Anchura de intervalo al 95 % de `p_hit` obtenido con método/hipótesis y muestra declarados; no igualar a ±1/3/5 pp |
| Riesgo | Minimizar | Propuesta: CVaR al 95 % de pérdida neta de la cartera simulada al incluir el candidato, con misma banca, importe, horizonte y escenario; acompañar drawdown/exposición |

Para pérdida `L`, definir `CVaR_alpha = min_eta {eta + E[max(L-eta,0)]/(1-alpha)}`. En una apuesta binaria aislada con importe fijo, la cola de pérdida puede ser idéntica entre candidatos; reconocer esa degeneración, sin inventar separación. El riesgo de cartera depende también del solapamiento y dependencia entre tickets. No comparar riesgo de un importe con EV de otro. Acierto, multiplicador, Edge y EV tienen relaciones algebraicas y no representan seis fuentes independientes de evidencia.

En F7 usar riesgo exacto/por enumeración validada cuando sea posible. Si su estimación requiere Monte Carlo de F8, mantener la dimensión no evaluable y una frontera parcial hasta validar ese módulo. No hay dependencia circular que autorice adelantar F8 o inventar su resultado.

**Dominancia:** `c1` domina `c2` si no es peor en ninguna dimensión según esas direcciones y es estrictamente mejor en al menos una, con tolerancias numéricas fijadas por métrica. La frontera contiene los candidatos factibles no dominados. Mostrar unidades originales; cualquier normalización de visualización es versionada y no cambia la dominancia. Un precio, intervalo o riesgo desconocido no equivale a cero: fuera de la frontera completa, permitir solo exploración parcial claramente rotulada.

Comparar primero dentro de cada universo/escenario/capital/horizonte; guardar todos los candidatos, exclusiones y dominadores. La frontera sobre estimaciones puntuales no garantiza dominancia verdadera: publicar intervalos, sensibilidad de pertenencia a la frontera y comparaciones conservadoras cuando el método lo permita. Si el generador es heurístico, llamarla **frontera aproximada sobre candidatos explorados**, sin afirmar optimalidad global. Validar contra enumeración exhaustiva pequeña.

Las preferencias son una segunda decisión explícita: filtros de acierto, incertidumbre, exposición, riesgo y EV conservador; eventualmente pesos o selección lexicográfica aprobados en desarrollo. Mantener la frontera original para permitir revisión. La solución «ninguna combinación elegible» siempre es admisible.

### Objetivos de multiplicador

Presets requeridos: **5x, 10x, 15x, 20x, 30x y 40x**, además de un valor personalizado válido `>1`. Configurar `target_multiplier` sobre retorno bruto normalizado, `target_mode` y tolerancia/límites:

- `minimum` (propuesta inicial): `M>=objetivo`; no afirma igualdad con el preset.
- `range`: `limite_inferior<=M<=limite_superior`, ambos explícitos.
- `nearest`: usar cercanía al objetivo como preferencia posterior entre candidatos factibles y dentro de tolerancia declarada, conservando las seis métricas y la frontera original para comparar.

No crear cuotas, añadir selecciones redundantes, relajar el Edge o extrapolar probabilidades solo para alcanzar 40x. Los límites de número de patas, exposición por equipo/partido y solapamiento siguen vigentes. La cuota conjunta elegible debe corresponder al conjunto exacto de selecciones. Un objetivo no es un resultado proyectado ni una promesa de retorno.

## Lesiones, suspensiones, xG y rotaciones

Rama de investigación condicionada a datos, inicialmente deshabilitada en la ruta gratuita básica. Requiere publicación de estados antes del corte, identidades/plantillas temporales, minutos y roles históricos, reemplazos plausibles, rival/localía/descanso y xG/xGA de definición homogénea. El xG posterior puede ser una etiqueta de evaluación, nunca variable del encuentro que se predice. Distinguir tasas de goles estimadas por Poisson de xG observado por disparos.

Comparar modelos con y sin información de ausencias sobre xG/xGA futuro y probabilidades de resultados, mediante ablaciones en iguales cortes cronológicos e intervalos. Una diferencia proyectada `ΔxG` se guarda como estimación con incertidumbre, no como hecho observado. No asignar por criterio informal «−0.3 xG por lesión» ni estimar impacto causal de una asociación: calidad de rival, decisiones tácticas, fatiga y selección de jugadores pueden confundirla.

Detección descriptiva propuesta de rotación: `n_cambios = 11 - |titulares_actuales ∩ titulares_previos|` solo cuando ambos onces completos sean comparables; registrar también estabilidad respecto a últimos 5/10 partidos y minutos previos. Con menos jugadores, guardar denominador real/estado incompleto y no llamar once completo al conjunto. Una alineación confirmada posterior al corte sirve para evaluar una predicción anterior de rotación, no para mejorarla retroactivamente. Cambios por sanción, lesión, transferencia o decisión técnica solo se atribuyen con evidencia; una rotación táctica no se deduce automáticamente del número de cambios.

Si falla cobertura, precisión temporal, soporte por jugador o homogeneidad de xG, mantener estas variables excluidas y documentar el alcance. Obtener una alineación aislada gratis no habilita todo el modelo de impacto.

## Estrés de ±1, ±3 y ±5 puntos porcentuales

Son pruebas deterministas de fragilidad, separadas de escenarios estadísticos estimados. Usar `delta ∈ {-0.05,-0.03,-0.01,+0.01,+0.03,+0.05}` de diferencia absoluta; no porcentajes relativos. Declarar evento objetivo, nivel (mercado o combinación), escenario y distribución base. No mover cada marginal de forma independiente.

Construcción coherente propuesta para un evento `A` con `0<p=P(A)<1`: fijar `p_objetivo=clip(p+delta,0,1)` y redistribuir masa de la conjunta `P(s)`:

`P_delta(s) = P(s)*(p_objetivo/p)` para `s∈A`, y `P_delta(s) = P(s)*((1-p_objetivo)/(1-p))` para `s∉A`.

Esta construcción mantiene no negatividad y suma uno; todas las probabilidades relacionadas se recalculan desde la misma conjunta perturbada. Registrar `delta_efectivo=p_objetivo-p`; un límite puede impedir realizar el choque completo. Para `p=0` o `p=1`, o soporte numérico insuficiente, declarar no factible bajo este procedimiento, revisar soporte o especificar otro modelo justificado; nunca dividir por cero ni introducir masa en eventos lógicamente imposibles.

Aplicar primero choques uno a uno. Si se quieren choques simultáneos a varios eventos, resolver restricciones sobre una única distribución (por ejemplo proyección de mínima divergencia) y comprobar factibilidad; no concatenar cambios que deshagan la meta anterior. Para parlays entre partidos se necesita una conjunta de esos partidos: si no existe, reportar cotas o no evaluable, no asumir independencia para poder perturbar.

Recalcular en cada choque: acierto, Edge, EV, riesgo con igual importe/horizonte, cumplimiento del multiplicador, elegibilidad y frontera de Pareto. Con precios fijados el multiplicador observado no cambia; los choques de precio son escenarios separados. Mantener el método de incertidumbre declarado; no reinterpretar el choque elegido como confianza estadística.

Los escenarios fundamentados se obtendrán de remuestreo temporal, incertidumbre de parámetros/calibración o modelos de dependencia respaldados por datos aprobados, preservando distribuciones conjuntas. Usar esas distribuciones para definir central/conservador/optimista y reportar su soporte, en lugar de llamar «conservador al 95 %» a un −5 pp arbitrario. Sin datos suficientes, solo existe la especificación del análisis, no intervalos calculados.

## Backtesting económico, Monte Carlo y escenarios

| Indicador | Definición y datos mínimos |
| --- | --- |
| ROI | Beneficio neto total / importe total simulado, con convención de voids explícita; propuesta incluir importe inicialmente comprometido y reportar también el excluyendo anulados |
| CLV de precio | `cuota_entrada/cuota_cierre - 1`, mismo contrato, línea y fuente comparable; publicar también comparación sin margen si procede |
| Drawdown máximo | `max_t((max_(u<=t) E_u - E_t) / max_(u<=t) E_u)`, con capital inicial positivo y curva patrimonial `E` bien definida |

Para CLV, el cierre es la última observación preinicio admisible dentro de una tolerancia fijada, no necesariamente el último precio real del operador. Si solo hay una etiqueta de cierre sin hora, se puede describir una comparación retrospectiva separada, no certificar ejecución. No comparar entradas de una línea con cierre de otra.

Registrar importes, precio, comisiones, disponibilidad, momento de aceptación hipotético y liquidación. Una cuota en una API no demuestra que el usuario hubiera podido ejecutar ese importe: los resultados son simulaciones bajo supuestos declarados. El máximo drawdown sobre resultados liquidados no mide toda la pérdida potencial de posiciones abiertas; mostrar también capital comprometido y exposición pendiente. No usar un orden arbitrario de liquidaciones simultáneas para modificar la curva.

Monte Carlo reutilizará un marcador por partido para todas sus selecciones y combinaciones; los partidos compartidos no se sortean de nuevo para cada ticket. Simular también incertidumbre de parámetros/modelo con un procedimiento justificado. Para una frecuencia estimada con sorteos independientes condicionales, el error estándar aproximado es `sqrt(p_hat × (1-p_hat)/N)`; cerca de cero/uno usar intervalos adecuados, y no interpretar cero aciertos como imposibilidad. Comprobar contra probabilidades exactas disponibles.

Escenarios propuestos:

- **Central:** configuración y precios admisibles según protocolo.
- **Conservador:** perturbaciones adversas justificadas por incertidumbre, precios peores/costes y dependencia común; excluir información débil.
- **Optimista:** perturbaciones favorables dentro de rangos declarados, sin introducir datos ficticios como observados.

Perturbar distribuciones o parámetros manteniendo probabilidades válidas y coherencia conjunta; no sumar/restar una constante a cada mercado por separado. Más simulaciones reducen error numérico, no sesgo, falta de cobertura ni incertidumbre estructural. Los intervalos de ROI/CLV también requieren bloques que respeten dependencia; no fijar un tamaño universal de muestra como garantía de suficiencia.

## Registro de riesgos y condiciones de bloqueo

Prioridades: crítica bloquea uso/promoción afectada; alta requiere mitigación o limitación explícita aprobada. Los controles son propuestos para fases posteriores, no verificaciones ya ejecutadas.

| ID / prioridad | Riesgo | Control y evidencia | Responsable / bloqueo |
| --- | --- | --- | --- |
| R01 crítica | Disponibilidad histórica o revisión no demostrable | Sobre temporal, perfiles separados y manifiesto de revisiones | Datos + validación; excluir del perfil estricto |
| R02 crítica | Fuga por variables, etiquetas o transformadores | Pruebas de corte, bloqueo simultáneo, splits internos y pipelines | ML + validación; impedir ejecución/promoción |
| R03 crítica | Cuota de cierre posterior usada como entrada | Comparar snapshot/actualización con decisión y contrato | Mercados; rechazar candidato |
| R04 crítica | Duplicados o identidad incorrecta | Mappings auditables, restricciones y contraste de calendarios | Datos; cuarentena hasta resolver |
| R05 alta | xG heterogéneo o recalculado | Proveedor/definición/versiones y ablaciones | Datos + estadística; deshabilitar mezcla no validada |
| R06 alta | Lesiones/alineaciones publicadas tarde | Estado previsto/confirmado, evidencia y horizontes separados | Datos; excluir variable/corte no sustentado |
| R07 alta | Carga y descanso basados en calendario parcial | Incluir copas/otras ligas o marcar cobertura insuficiente | Datos; no presentar descanso parcial como completo |
| R08 alta | UCL, ligas y equipos poco comparables | Reportes por torneo, fuerza de rivales, cold-start y regularización | Estadística; limitar afirmaciones sin soporte |
| R09 alta | Cambio de formato/reglas y drift | Reglas por temporada, evaluación por régimen y seguimiento | Estadística; reevaluar estabilidad |
| R10 crítica | Reutilizar test o selección masiva de estrategias | Registro de experimentos, presupuesto de búsqueda, nueva confirmación | Validación; invalida afirmación fuera de muestra |
| R11 alta | Muestra pequeña, supervivencia o faltantes selectivos | Denominadores, exclusiones, intervalos y análisis por equipos/épocas | Validación; «evidencia insuficiente» |
| R12 crítica | Independencia falsa y calibración incompatible | Matriz conjunta, casos exactos y reconciliación validada | Estadística; bloquear combinaciones |
| R13 crítica | Cuotas combinadas inventadas/contrato incorrecto | Cotización conjunta y reglas verificables | Mercados; EV/ROI no evaluables |
| R14 alta | Optimizador explota errores extremos | Límites de exposición, sensibilidad y comparación exhaustiva | Optimización; abstenerse si no hay robustez |
| R15 alta | Sobreestimar rentabilidad ejecutable | Antigüedad, costes, límites, capital bloqueado y escenarios | Mercados + riesgo; reportar simulación condicionada |
| R16 alta | Monte Carlo da falsa certeza | Error numérico y de parámetros por separado, convergencia | Riesgo; no publicar precisión injustificada |
| R17 crítica | Licencia incompatible o términos cambiantes | Condiciones versionadas, permisos por uso y fuente alternativa | Coordinación; bloquear ingesta/redistribución afectadas |
| R18 alta | Datos no reproducibles o revisión silenciosa | Bruto inmutable, hashes, snapshots y versiones fijadas | Datos; no aceptar experimento sin linaje |
| R19 alta | Filtración de secretos o gasto accidental | Logs saneados, entorno, presupuesto y reintentos limitados | Ingeniería; detener conector afectado |
| R20 alta | Puntuación multiobjetivo arbitraria o Pareto tratado como certeza | Conservar vector/unidades, frontera por escenario, intervalos y universo explorado | Optimización; no afirmar óptimo global si búsqueda parcial |
| R21 crítica | Choques ±pp rompen relaciones de mercados | Perturbar conjunta, registrar delta efectivo/factibilidad y comprobar identidades | Estadística; rechazar escenario incoherente |
| R22 alta | Errores de captura o tipo de retorno Draftea | Contrato de importación, evidencia/hora, datos originales y cuarentena | Datos + mercados; EV no evaluable si retorno ambiguo |
| R23 alta | Atribuir efecto causal de lesiones o rotación sin datos | Ablaciones cronológicas, contexto/reemplazos, intervalos y exclusión inicial | ML + estadística; deshabilitar ajustes no sustentados |
| R24 alta | Sesgo por capturar solo ofertas atractivas | Protocolo de muestreo previo, universo observado, descartados y denominadores | Validación; limitar inferencia de rentabilidad al universo capturado |

UCL cambió su formato desde 2024/25 a una fase de liga de 36 clubes con ocho encuentros por equipo; no extrapolar automáticamente los conteos ni los patrones de la fase de grupos anterior. Fuente: [explicación oficial de UEFA](https://www.uefa.com/uefachampionsleague/news/0268-12157d69ce2d-9f011c70f6fa-1000--new-champions-league-format/).

## Entrega pedagógica de cada modelo

Cada fase de modelado deberá mostrar: pregunta que responde, ecuaciones/supuestos, datos usados y excluidos, un ejemplo trazable a datos aprobados, comparación fuera de muestra, calibración, errores habituales y decisión de conservar/modificar/descartar. Si se necesita un ejemplo sintético para explicar una fórmula, se etiquetará y aislará; nunca se confundirá con una probabilidad real de un partido.

Las referencias se consultaron el 2026-11-24. Las condiciones de paso y las aprobaciones siguen [PLAN](../PLAN.md), no este documento de manera independiente.
