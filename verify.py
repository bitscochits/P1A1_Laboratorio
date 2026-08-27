#!/usr/bin/env python3
"""
VERIFICACIÓN — Laboratorio Benchmark 3D
========================================
Cálculos manuales para comparar con OpenSees.
"""

import math

print("=" * 65)
print("  VERIFICACIÓN MANUAL — Marco 3D 4×4 m, 1 piso")
print("=" * 65)

# ============================================================
# DATOS
# ============================================================
Lx = 4.0     # m (vanos en X)
Ly = 4.0     # m (vanos en Y)
H  = 3.0     # m (altura)
t  = 0.15    # m (espesor losa)
gamma = 25.0 # kN/m³

col_b, col_h = 0.30, 0.30   # m
v_b,  v_h   = 0.25, 0.50    # m
fpc = 21.0                   # MPa
Ec  = 4700 * math.sqrt(fpc) * 1000  # kPa

q_acabados = 1.5   # kN/m²
q_viva     = 2.0   # kN/m²

# ============================================================
# 1. CARGAS
# ============================================================
print("\n--- 1. CALCULO DE CARGAS ---")

# Peso propio
w_losa    = gamma * t            # kN/m²
w_total   = w_losa + q_acabados  # kN/m² (carga muerta)
w_viga    = gamma * v_b * v_h    # kN/m (peso propio viga)

print(f"  Peso propio losa:    {w_losa:.2f} kN/m²")
print(f"  Acabados:            {q_acabados:.2f} kN/m²")
print(f"  Carga muerta total:  {w_total:.2f} kN/m²")
print(f"  Peso propio viga:    {w_viga:.2f} kN/m")
print(f"  Carga viva:          {q_viva:.2f} kN/m²")

# Áreas tributarias
area_losa = Lx * Ly
print(f"\n  Área de losa:        {area_losa:.2f} m²")

# ============================================================
# 2. CARGA TOTAL MUERTA (G)
# ============================================================
print("\n--- 2. CARGA MUERTA TOTAL (G) ---")

peso_losa     = w_total * area_losa
peso_vigas    = 4 * w_viga * Lx  # 4 vigas, cada una de longitud Lx
carga_G_total = peso_losa + peso_vigas

print(f"  Peso losa+acabados: {peso_losa:.2f} kN")
print(f"  Peso 4 vigas:       {peso_vigas:.2f} kN")
print(f"  TOTAL G:            {carga_G_total:.2f} kN")

# ============================================================
# 3. REACCIÓN POR COLUMNA (G)
# ============================================================
print("\n--- 3. REACCION POR COLUMNA (G) ---")

R_col_G = carga_G_total / 4
print(f"  Por simetría: {carga_G_total:.2f} / 4 = {R_col_G:.2f} kN/columna")

# ============================================================
# 4. CARGA VIVA TOTAL (Q)
# ============================================================
print("\n--- 4. CARGA VIVA TOTAL (Q) ---")

carga_Q_total = q_viva * area_losa
R_col_Q = carga_Q_total / 4

print(f"  TOTAL Q:            {carga_Q_total:.2f} kN")
print(f"  Reacción/columna:   {R_col_Q:.2f} kN")

# ============================================================
# 5. DESPLAZAMIENTO VERTICAL (estimación)
# ============================================================
print("\n--- 5. ESTIMACIÓN DE DESPLAZAMIENTO VERTICAL ---")

# Modelo simplificado: viga simplemente apoyada con carga uniforme
# δ_max = 5·w·L⁴ / (384·E·I)
# Pero aquí tenemos un marco rígido, no simplemente apoyado.

# Para una viga con rigidización de columna:
# Usamos el modelo de viga empotrada (peor caso):
# δ = w·L⁴ / (384·E·I)
w_viga_muerta = w_total * Ly / 2 + w_viga  # kN/m (tributario + peso propio)

I_viga = v_b * v_h**3 / 12  # m⁴

delta_estimado = 5 * w_viga_muerta * Lx**4 / (384 * Ec * I_viga)
print(f"  Carga distribuida viga: {w_viga_muerta:.2f} kN/m")
print(f"  I viga:                 {I_viga:.6f} m⁴")
print(f"  E:                      {Ec:.0f} kPa")
print(f"  δ estimado (viga):      {delta_estimado*1000:.4f} mm")
print(f"  Nota: El marco rígido reduce este valor")

# ============================================================
# 6. FUERZA AXIAL EN COLUMNA
# ============================================================
print("\n--- 6. FUERZA AXIAL EN COLUMNA ---")

# La fuerza axial en la columna es igual a la reacción
P_columna = R_col_G
print(f"  P_columna = R_columna = {P_columna:.2f} kN (compresión)")

# Verificación: esfuerzo
sigma = P_columna / (col_b * col_h)
print(f"  Esfuerzo axial: {sigma:.2f} kPa = {sigma/1000:.4f} MPa")
print(f"  f'c = {fpc:.0f} MPa →factor de seguridad: {fpc/(sigma/1000):.1f}")

# ============================================================
# 7. MOMENTO EN EXTREMO DE VIGA
# ============================================================
print("\n--- 7. MOMENTO EN EXTREMO DE VIGA ---")

# Para una viga empotrada con carga uniforme:
# M = w·L²/12
M_viga = w_viga_muerta * Lx**2 / 12
print(f"  M_empotramiento = w·L²/12 = {w_viga_muerta:.2f} × {Lx}² / 12")
print(f"  M = {M_viga:.4f} kN·m")
print(f"  Nota: En marco rígido el momento real varía según rigidez relativa")

# ============================================================
# 8. RESUMEN PARA COMPARACIÓN
# ============================================================
print("\n" + "=" * 65)
print("  RESUMEN DE VALORES DE REFERENCIA")
print("=" * 65)
print(f"  {'Magnitud':<35} {'Valor':<15} {'Unidad'}")
print(f"  {'─'*35} {'─'*15} {'─'*10}")
print(f"  {'Carga muerta total (G)':<35} {carga_G_total:<15.2f} kN")
print(f"  {'Carga viva total (Q)':<35} {carga_Q_total:<15.2f} kN")
print(f"  {'Reacción columna (G)':<35} {R_col_G:<15.2f} kN")
print(f"  {'Reacción columna (Q)':<35} {R_col_Q:<15.2f} kN")
print(f"  {'Fuerza axial columna':<35} {P_columna:<15.2f} kN")
print(f"  {'Momento extremo viga':<35} {M_viga:<15.4f} kN·m")
print(f"  {'Desplazamiento vertical (est.)':<35} {delta_estimado*1000:<15.4f} mm")
print("=" * 65)

print("\n  Valores a comparar con OpenSees:")
print("  1. ΣF_aplicadas = ΣR  (equilibrio)")
print("  2. R_columna ≈ valores manuales")
print("  3. Desplazamientos coherentes")
print("  4. Momento de extremo coherente")
