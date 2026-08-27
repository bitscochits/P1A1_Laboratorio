# Lab Benchmark 3D

Marco estructural para el laboratorio de la Semana 1.

## Modelo

- **Geometria**: 4.0 m x 4.0 m, 1 piso (3.0 m)
- **Columnas**: 4 x tipo L 30x30 cm (espesor 15 cm)
- **Vigas**: 4 x tipo L (losa colaborante ACI)
- **Losa**: 15 cm
- **Material**: Hormigon f'c = 25 MPa (G-25), Ec = 23469 MPa
- **Unidades**: m, kN, kPa

## Seccion L de Viga (losa colaborante)

La viga se modela como una seccion L que representa la losa colaborante segun ACI:

```
   +------------------+  100 cm (ala = L/4)
   |     15 cm        |
   +------+-----+     |
          |     |     |
          |25x35|     |
          |     |     |
          +-----+     |
```

- **Ala**: 100 x 15 cm (losa colaborante, ancho = L/4)
- **Alma**: 25 x 35 cm (parte bajo la losa)
- **Area**: 0.2375 m2
- **I_grav**: 4.63e-3 m4 (+78% vs viga sola)
- **I_lat**: 2.07e-2 m4

## Cargas

- **Carga muerta (G)**: Peso propio losa (3.75 kN/m2) + acabados (1.5 kN/m2) + peso vigas L
- **Carga viva (Q)**: 2.0 kN/m2
- **Sismo (EX)**: 50 kN por nodo del techo

## Areas tributarias

Para losa cuadrada (4x4 m):
- Vigas X: triangulos de base 4m, altura 2m (4 m2 por viga)
- Vigas Y: triangulos de base 4m, altura 2m (4 m2 por viga)
- Cada nodo esquina recibe: q * Lx * Ly / 8 = 10.50 kN

## Archivos

- `benchmark_3d.py` - Modelo principal OpenSeesPy
- `verify.py` - Verificacion manual de resultados
- `plot_geometry.py` - Graficas de geometria, areas tributarias, seccion L, GDL
- `results/` - Resultados JSON y graficas PNG

## Como ejecutar

```bash
# Modelo principal
py -3.12 benchmark_3d.py

# Verificacion manual
py -3.12 verify.py

# Graficas
py -3.12 plot_geometry.py
```

## Resultados

- **Equilibrio G**: 179.00 kN aplicados = 179.00 kN reacciones (error = 0)
- **Equilibrio Q**: 32.00 kN aplicados = 32.00 kN reacciones (error = 0)
- **UX sismo**: 104.0 mm
