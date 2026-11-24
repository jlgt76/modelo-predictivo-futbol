# Instrucciones para agentes

## Autorizaciones experimentales de F3 a F5

El usuario aprobó F3 y F4 experimentales y autorizó F5 experimental para ML, híbridos, ensembles y calibración. Usar exclusivamente X e y congelados de F3, 2021/22–2024/25, D−2 por objetivo y como máximo un subagente para validación independiente. La reserva 2025/26 y la edición 2026/27 se excluyen. F2-A y F2-B continúan abiertas y los criterios originales siguen vigentes. F6 y las predicciones operativas requieren autorización posterior.

## Alcance y autoridad

Proyecto Python de investigación probabilística de fútbol. Toda explicación, documentación, mensajes de interfaz y comentarios se redactan en español. Los identificadores técnicos pueden conservar convenciones habituales de Python.

F2 comprende ingesta piloto, limpieza y auditoría para las seis competiciones documentadas, 2021/22 a 2025/26 y 2026/27 como edición en curso separada. El presupuesto máximo de suscripciones es $0 MXN. El cierre de F2 y el paso regular por las puertas de aceptación requieren aprobación explícita.

El usuario debe revisar y aprobar **cada fase** antes de comenzar la siguiente. El ajuste antes de aprobar F2 se limita a las excepciones experimentales expresas de F4 y F5. Registrar aprobación, alcance y evidencia en `DECISIONES_TECNICAS.md`; nunca inferirla del silencio.

El usuario aprobó F1 y autorizó F2. Mantener la arquitectura aprobada, usar como máximo un subagente simultáneo y realizar la revisión independiente al finalizar la auditoría.

## Organización del trabajo

El coordinador divide tareas por entregable y asigna un único propietario de escritura por archivo. Otros agentes revisan y proponen cambios mediante mensajes. Acordar contratos compartidos antes de implementar; el coordinador integra y resuelve discrepancias. No modificar archivos asignados a otro agente sin transferencia explícita.

| Especialidad | Responsabilidad | Evidencia exigida |
| --- | --- | --- |
| Ingeniería de datos | Adaptadores, identidad, revisiones, disponibilidad temporal y calidad | Manifiestos, linaje, cobertura y cuarentena |
| Estadística de fútbol | Poisson, Dixon-Coles, Elo y supuestos | Explicación, diagnóstico y comparación con referencias |
| Machine Learning | Variables, pipelines y ajuste interno cronológico | Configuración y predicciones fuera de muestra |
| Validación independiente | Auditar fuga temporal, calibración y backtesting | Informe reproducible de aceptación o rechazo |
| Mercados | Cuotas, margen, liquidación, Edge, EV y CLV | Referencia temporal y reglas comparables |
| Optimización y riesgo | Dependencia conjunta, parlays y simulación | Restricciones, incertidumbre y exposición agregada |
| Visualización | Dashboard explicable de artefactos aprobados | Trazabilidad, unidades, filtros y estados sin datos |

Se pueden combinar roles cuando haya menos agentes disponibles. La revisión de validación debe ser independiente de quien propone el modelo. Paralelizar únicamente tareas con entradas y archivos independientes.

## Reglas obligatorias

1. No inventar partidos, cuotas, probabilidades, métricas ni resultados. Los datos sintéticos, cuando una fase posterior los requiera para pruebas, deben estar identificados y aislados de los datos reales.
2. Verificar documentación y permisos del proveedor antes de automatizar acceso. Una web pública, un CSV gratuito o una librería de scraping no equivalen a autorización de reutilización. No compartir claves ni datos restringidos en el repositorio.
3. Preservar datos brutos y revisiones. Mantener separados momento del hecho, publicación/disponibilidad, observación del proveedor e ingesta local. No atribuir una fecha histórica de disponibilidad sin evidencia.
4. Las variables de una predicción solo pueden usar revisiones admisibles antes de su `decision_at`. Etiquetas futuras se usan exclusivamente para evaluación o entrenamiento posterior autorizado. Nunca usar datos finales de temporada para construir información pasada.
5. Usar particiones cronológicas y walk-forward. Agrupar partidos simultáneos, separar ajuste, calibración y prueba, y proteger el test final. Prohibir particiones aleatorias para demostrar rendimiento futuro.
6. Comparar Brier Score, Log Loss y calibración con convenciones fijas. Reportar tamaño de muestra, cobertura y dispersión por liga, temporada y horizonte. Un ROI positivo aislado no valida un modelo.
7. El filtro inicial de Edge es configurable: **0.06 = seis puntos porcentuales**, con referencia y alcance explícitos. Propuesta para contrato binario sin devoluciones: `p_modelo - 1/cuota_decimal`; alcance inicial `selection`, con Edge conjunto informado cuando sea definible. Guardar también Edge sin margen. Para pushes u otros pagos aplicar el contrato específico de Metodología. No confundirlo con 6 % relativo.
8. No asumir independencia de mercados del mismo partido. Derivar su intersección de una distribución conjunta coherente. No multiplicar cuotas individuales para inventar una cuota de parlay ofrecida.
9. Evaluar ROI, CLV y máximo drawdown solo cuando existan datos comparables suficientes. Si faltan, indicar «no evaluable», nunca sustituir por cero.
10. Incluir escenarios conservador, central y optimista; separar error de estimación, error de simulación e incertidumbre del proceso futbolístico.
11. **No automatizar apuestas reales**: no introducir módulos de ejecución, credenciales de apuestas, transferencias ni órdenes. Las carteras son simuladas.
12. Evaluar neutralmente todos los mercados disponibles del alcance: **1X2, doble oportunidad (1X/X2/12), Over, Under y BTTS sí/no**. Aplicar los mismos controles de calidad, corte y elegibilidad; registrar por qué un mercado no puede evaluarse. No favorecer Over, favoritos u otro tipo de selección por diseño.
13. La optimización será **multiobjetivo**: probabilidad de acierto, multiplicador, Edge y EV a maximizar; incertidumbre y riesgo a minimizar. Conservar la **frontera de Pareto** y hacer explícita cualquier preferencia posterior; no ocultar todo en una puntuación única arbitraria. Objetivos configurables **5x, 10x, 15x, 20x, 30x, 40x y personalizados**, sin forzar combinaciones para alcanzarlos.
14. Incluir perturbaciones de **±1, ±3 y ±5 puntos porcentuales**, además de escenarios fundamentados estadísticamente. Preservar coherencia conjunta; las perturbaciones fijas son pruebas de estrés, no intervalos de confianza.
15. Diseñar captura manual e importación **CSV/Excel de multiplicadores de Draftea** como datos aportados por el usuario, con hora, evidencia, contrato y cotización conjunta exacta. No asumir una API o exportación oficial ni activar scraping. Esta fase solo define el contrato de importación.
16. Conservar un registro inmutable de predicciones, fecha/hora de generación y corte, versiones de datos/modelo/calibrador, probabilidades proyectadas, cuotas vinculadas y resultados posteriores separados. Diferenciar predicción prospectiva de reconstrucción histórica.
17. Estudiar lesiones y suspensiones sobre xG/xGA y detectar rotaciones solo con datos suficientes, identidades resueltas y disponibilidad temporal demostrada. No imponer descuentos de xG inventados ni presentar asociaciones como efectos causales.
18. Exigir identidades matemáticas de mercados relacionados y comparación con referencias simples y probabilidades de mercado sin margen cuando sean calculables. No normalizar las tres selecciones solapadas de doble oportunidad como si fueran excluyentes; no inventar una referencia sin margen para una combinación sin mercado completo.
19. Mantener niveles base y avanzado. Habilitar variables avanzadas por fuente, competición, temporada y horizonte al aprobar su calidad. Conservar un plan de ampliación para los campos que falten en el piloto gratuito.
20. Evaluar y calibrar T−24 h, T−3 h y T−60 min de forma independiente. Agrupar las tres emisiones del mismo partido en la misma partición externa. Registrar corte y revisión de calendario. Usar cada convocatoria, alineación, baja o cuota solo desde su disponibilidad acreditada.
21. Comparar Poisson, Dixon-Coles, Elo, regresión logística, XGBoost, LightGBM, Random Forest, Extra Trees, híbridos y ensembles bajo el protocolo independiente de validación. Documentar regularización, búsqueda interna, calibración, importancia y SHAP. Justificar la selección frente a referencias simples con resultados fuera de muestra.
22. Registrar umbrales configurables de impacto de ausencia desde 0.20 xG y de rotación excesiva. El primero clasifica impactos estimados con datos. Definir el segundo con evidencia de desarrollo. Conservar dirección, unidad e incertidumbre.

## Flujo técnico posterior a la aprobación

Usar funciones de dominio pequeñas y tipadas, configuración versionada, dependencias fijadas y semillas registradas. Los notebooks explican resultados; la lógica reproducible residirá en el paquete Python. Escribir pruebas para invariantes relevantes: tiempo, identidad, probabilidades, liquidación y reproducibilidad. No crear pruebas que solo repitan la implementación.

Antes de cerrar una fase: presentar qué cambió, evidencia de verificación, limitaciones, decisiones abiertas y alcance concreto de la fase siguiente. Dejar `PLAN.md` sincronizado. No declarar una fase aprobada porque sus archivos ya existen.
