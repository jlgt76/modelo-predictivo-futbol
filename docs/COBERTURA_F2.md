# Inventario por competición y temporada

La auditoría externa confirmó 132 celdas de proveedores, con seis observaciones manuales y 126 pendientes. La [auditoría del dataset base](AUDITORIA_BASE_F2.json) es adicional y no cambia esas celdas. El [dictamen](INFORME_F2.md) registra las muestras actuales de OpenLigaDB y sus límites.

## Matriz de proveedores candidatos

Evidencia de sesión manual comunicada por el usuario. Pendiente significa que falta una respuesta observada para esa combinación. La columna de variables de la muestra describe únicamente el fixture 1208021. Un rechazo del plan se registra como restricción de acceso, sin inferir ausencia de datos en el proveedor. El [inventario JSON](COBERTURA_PROVEEDORES_F2.json) desglosa las celdas por endpoint, temporada y competición.

| Proveedor, competición | Temporada | Endpoint y observación | Variables que quedan pendientes |
| --- | --- | --- | --- |
| Football-Data.org, CL | 2026/27 | `/competitions/CL/matches`: 144 recibidos, 72 finalizados, 144 sin equivalente en OpenFootball | Cotejo de marcadores reglamentarios, estado, hora y sede por registro |
| Football-Data.org, PL | 2026/27 | `/competitions/PL/matches`: pendiente | Calendario, resultado, estado y frescura |
| Football-Data.org, PD | 2026/27 | `/competitions/PD/matches`: pendiente | Calendario, resultado, estado y frescura |
| Football-Data.org, BL1 | 2026/27 | `/competitions/BL1/matches`: pendiente | Calendario, resultado, estado y frescura |
| Football-Data.org, SA | 2026/27 | `/competitions/SA/matches`: pendiente | Calendario, resultado, estado y frescura |
| Football-Data.org, FL1 | 2026/27 | `/competitions/FL1/matches`: pendiente | Calendario, resultado, estado y frescura |
| API-Football, PL | 2024/25 | `/fixtures`: 380 partidos recibidos | Emparejamiento uno a uno, duplicados, resultados comparables y revisiones |
| API-Football, PL | 2024/25 | `/fixtures/lineups`: dos registros de equipo | Once, suplentes, formación, entrenador e ID observados solo en la muestra. Publicación pendiente |
| API-Football, PL | 2024/25 | `/fixtures/players`: observación puntual | Minutos, posición, rating, goles, asistencias, tiros, pases, duelos, entradas, tarjetas y portería observados. Cobertura poblacional pendiente |
| API-Football, PL | 2024/25 | `/fixtures/statistics`: observación puntual | Tiros, posesión, córners, pases, `expected_goals` y `goals_prevented` observados. Homogeneidad pendiente |
| API-Football, PL | 2024/25 | `/injuries`: 5 Missing Fixture y 1 Questionable | Tipo y motivo por jugador, suspensiones explícitas y fecha de publicación |
| API-Football, PL | 2024/25 | `/fixtures?ids=…` y `/fixtures/events`: pendiente | Eventos y comparación real de bloques frente a consultas individuales |
| API-Football, cada una de las seis | 2022/23 y 2023/24 | `/fixtures`, `/fixtures?ids=…` y `/injuries`: pendientes por competición y temporada | Todos los campos hasta ejecutar muestras |
| API-Football, CL, PD, BL1, SA y FL1 | 2024/25 | `/fixtures`, `/fixtures?ids=…` y `/injuries`: pendientes por competición | Todos los campos hasta ejecutar muestras |
| API-Football, consultas del usuario | 2026/27 | Rechazadas por el plan. La cuenta informa años iniciales 2022, 2023 y 2024 | La integración limita el piloto a esos años |
| API-Football, alcance del piloto | 2022/23–2024/25 | Archivo de cuotas históricas indisponible según catálogo consultado | Cuotas y métricas económicas quedan pendientes de otra fuente autorizada |

La cobertura de xGA requiere el xG rival del mismo partido, método y periodo. `goals_prevented` tiene significado propio. El nivel avanzado conserva los campos faltantes como desconocidos. Una rotación requiere onces comparables de varios partidos y su uso prepartido exige evidencia del corte.

## Referencia OpenFootball original

Fuente: OpenFootball. Los recuentos son de filas aceptadas por el adaptador. El denominador independiente sigue pendiente.

| Competición | Temporada | Estado | Filas | Sin marcador | Sin hora de origen |
| --- | --- | --- | ---: | ---: | ---: |
| PL | 2021-22 | Histórica | 380 | 0 | 0 |
| PD | 2021-22 | Histórica | 380 | 0 | 0 |
| BL1 | 2021-22 | Histórica | 306 | 0 | 0 |
| SA | 2021-22 | Histórica | 380 | 0 | 0 |
| FL1 | 2021-22 | Histórica | 380 | 0 | 0 |
| CL | 2021-22 | Histórica | 125 | 0 | 39 |
| PL | 2022-23 | Histórica | 380 | 0 | 0 |
| PD | 2022-23 | Histórica | 380 | 0 | 0 |
| BL1 | 2022-23 | Histórica | 306 | 0 | 0 |
| SA | 2022-23 | Histórica | 380 | 0 | 0 |
| FL1 | 2022-23 | Histórica | 380 | 0 | 0 |
| CL | 2022-23 | Histórica | 125 | 0 | 37 |
| PL | 2023-24 | Histórica | 380 | 0 | 0 |
| PD | 2023-24 | Histórica | 380 | 0 | 0 |
| BL1 | 2023-24 | Histórica | 306 | 0 | 0 |
| SA | 2023-24 | Histórica | 380 | 0 | 0 |
| FL1 | 2023-24 | Histórica | 306 | 0 | 0 |
| CL | 2023-24 | Histórica | 125 | 0 | 84 |
| PL | 2024-25 | Histórica | 380 | 0 | 0 |
| PD | 2024-25 | Histórica | 380 | 10 | 0 |
| BL1 | 2024-25 | Histórica | 306 | 0 | 0 |
| SA | 2024-25 | Histórica | 380 | 10 | 0 |
| FL1 | 2024-25 | Histórica | 306 | 0 | 0 |
| CL | 2024-25 | Histórica | 189 | 0 | 132 |
| PL | 2025-26 | Histórica | 380 | 0 | 0 |
| PD | 2025-26 | Histórica | 380 | 0 | 0 |
| BL1 | 2025-26 | Histórica | 306 | 0 | 0 |
| SA | 2025-26 | Histórica | 380 | 0 | 0 |
| FL1 | 2025-26 | Histórica | 306 | 1 | 0 |
| CL | 2025-26 | Histórica | 189 | 0 | 130 |
| PL | 2026-27 | En curso | 380 | 330 | 0 |
| PD | 2026-27 | En curso | 380 | 311 | 290 |
| BL1 | 2026-27 | En curso | 306 | 270 | 198 |
| SA | 2026-27 | En curso | 380 | 330 | 260 |
| FL1 | 2026-27 | En curso | 306 | 261 | 192 |
| CL | 2026-27 | Sin archivo (404) |  |  |  |
