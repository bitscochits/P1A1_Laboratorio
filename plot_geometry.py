#!/usr/bin/env python3
"""
VISUALIZACION - Benchmark 3D con columnas L
=============================================
Graficas de: planta, alzado, areas tributarias, columnas L, GDL.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import os

os.makedirs('results', exist_ok=True)

# ============================================================
# 1. PLANTA - Estructura y areas tributarias
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# --- Planta: areas tributarias ---
ax1 = axes[0]
ax1.set_title('AREAS TRIBUTARIAS - Losa 4x4 m', fontsize=13, fontweight='bold')
ax1.set_xlabel('X (m)')
ax1.set_ylabel('Y (m)')

# Losa (fondo gris claro)
ax1.fill([0, 4, 4, 0], [0, 0, 4, 4], alpha=0.15, color='gray', label='Losa')

# Triangulo viga Y=0 (abajo): vertices (0,0), (4,0), (2,2)
tri1 = plt.Polygon([[0,0], [4,0], [2,2]], alpha=0.4, color='blue', label='Triangulo (viga X)')
ax1.add_patch(tri1)

# Triangulo viga Y=4 (arriba): vertices (0,4), (4,4), (2,2)
tri2 = plt.Polygon([[0,4], [4,4], [2,2]], alpha=0.4, color='blue')
ax1.add_patch(tri2)

# Triangulo viga X=0 (izq): vertices (0,0), (0,4), (2,2)
tri3 = plt.Polygon([[0,0], [0,4], [2,2]], alpha=0.4, color='red', label='Triangulo (viga Y)')
ax1.add_patch(tri3)

# Triangulo viga X=4 (der): vertices (4,0), (4,4), (2,2)
tri4 = plt.Polygon([[4,0], [4,4], [2,2]], alpha=0.4, color='red')
ax1.add_patch(tri4)

# Vigas
ax1.plot([0, 4], [0, 0], 'b-', linewidth=3)  # viga X inferior
ax1.plot([0, 4], [4, 4], 'b-', linewidth=3)  # viga X superior
ax1.plot([0, 0], [0, 4], 'r-', linewidth=3)  # viga Y izquierda
ax1.plot([4, 4], [0, 4], 'r-', linewidth=3)  # viga Y derecha

# Columnas L (esquinas)
for cx, cy in [(0,0), (4,0), (0,4), (4,4)]:
    # Dibujar forma L simple
    rect = patches.FancyBboxPatch((cx-0.15, cy-0.15), 0.30, 0.30,
                                   boxstyle="round,pad=0.02",
                                   facecolor='black', edgecolor='black')
    ax1.add_patch(rect)

# Etiquetas de carga por nodo
F_nodo = 5.25 * 4 * 4 / 8  # 10.5 kN
for cx, cy in [(0,0), (4,0), (0,4), (4,4)]:
    ax1.text(cx, cy+0.3, f'{F_nodo:.1f} kN', ha='center', fontsize=9, color='darkgreen')

# Punto centro (交点 de diagonales)
ax1.plot(2, 2, 'kx', markersize=10, markeredgewidth=2)
ax1.text(2, 2.3, 'Centro', ha='center', fontsize=9)

# Diagonales punteadas
ax1.plot([0, 4], [0, 4], 'k--', linewidth=0.8, alpha=0.5)
ax1.plot([0, 4], [4, 0], 'k--', linewidth=0.8, alpha=0.5)

# Ejes
for x in [0, 4]:
    ax1.axvline(x=x, color='gray', linestyle=':', linewidth=0.6, alpha=0.4)
for y in [0, 4]:
    ax1.axhline(y=y, color='gray', linestyle=':', linewidth=0.6, alpha=0.4)

ax1.text(0, -0.6, 'Eje 1', ha='center', fontsize=10, color='gray')
ax1.text(4, -0.6, 'Eje 2', ha='center', fontsize=10, color='gray')
ax1.text(-0.6, 0, 'A', va='center', fontsize=10, color='gray', rotation=90)
ax1.text(-0.6, 4, 'B', va='center', fontsize=10, color='gray', rotation=90)

ax1.set_xlim(-1.2, 5.2)
ax1.set_ylim(-1.2, 5.2)
ax1.set_aspect('equal')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)

# --- Alzado con columna L ---
ax2 = axes[1]
ax2.set_title('ALZADO - Columna tipo L', fontsize=13, fontweight='bold')
ax2.set_xlabel('X (m)')
ax2.set_ylabel('Z (m)')

# Columna L (perfil)
# Forma: cuadrado 30x30 con recorte 15x15
col_pts = np.array([
    [0, 0], [0.30, 0], [0.30, 0.15], [0.15, 0.15],
    [0.15, 0.30], [0, 0.30], [0, 0]
])
col_x = col_pts[:, 0] - 0.15  # centrar
col_y = col_pts[:, 1]

# Dibujar columna L a escala (exagerada para visibilidad)
scale = 2
for cx_base in [0, 4]:
    col_plot_x = col_x * scale + cx_base
    col_plot_y = col_y * scale
    ax2.fill(col_plot_x, col_plot_y, alpha=0.8, color='black')

# Vigas
ax2.plot([0, 4], [3, 3], 'b-', linewidth=4, label='Viga X')

# Flechas de carga
n_flechas = 8
for i in range(n_flechas + 1):
    x = i * 4.0 / n_flechas
    ax2.annotate('', xy=(x, 3), xytext=(x, 3.6),
                 arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
ax2.text(2, 3.8, 'q = 5.25 kN/m2', ha='center', fontsize=10, color='red')

# Losa
ax2.fill_between([0, 4], 3, 3.15, alpha=0.3, color='blue', label='Losa 15 cm')

# Apoyos
for cx in [0, 4]:
    tri = patches.RegularPolygon((cx, 0), 3, radius=0.2, orientation=0,
                                  facecolor='gray', edgecolor='black')
    ax2.add_patch(tri)

# Cotas
ax2.annotate('', xy=(-0.5, 3), xytext=(-0.5, 0),
             arrowprops=dict(arrowstyle='<->', color='green'))
ax2.text(-0.8, 1.5, '3.0 m', va='center', fontsize=10, color='green', rotation=90)
ax2.annotate('', xy=(4, -0.5), xytext=(0, -0.5),
             arrowprops=dict(arrowstyle='<->', color='green'))
ax2.text(2, -0.8, '4.0 m', ha='center', fontsize=10, color='green')

# Leyenda de columna L
ax2.text(0, 1.5, 'Col L\n30x30\nespesor 15', fontsize=8, ha='center',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

ax2.set_xlim(-1.5, 5.5)
ax2.set_ylim(-1, 4.5)
ax2.set_aspect('equal')
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/tributary_areas.png', dpi=150, bbox_inches='tight')
print('  results/tributary_areas.png')

# ============================================================
# 2. SECCION L - Detalle
# ============================================================
fig2, ax3 = plt.subplots(1, 1, figsize=(6, 6))
ax3.set_title('SECCION COLUMNA TIPO L\n30x30 cm, espesor 15 cm', fontsize=13, fontweight='bold')

# Forma L
col_fill_x = [0, 30, 30, 15, 15, 0, 0]
col_fill_y = [0, 0, 15, 15, 30, 30, 0]
ax3.fill(col_fill_x, col_fill_y, alpha=0.7, color='steelblue', edgecolor='black', linewidth=2)

# Cotas
# Ancho total
ax3.annotate('', xy=(30, -3), xytext=(0, -3),
             arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
ax3.text(15, -5, '30 cm', ha='center', fontsize=11, color='green')

# Alto total
ax3.annotate('', xy=(-3, 30), xytext=(-3, 0),
             arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
ax3.text(-5, 15, '30 cm', va='center', fontsize=11, color='green', rotation=90)

# Espesor brazo horizontal
ax3.annotate('', xy=(30, 17), xytext=(15, 17),
             arrowprops=dict(arrowstyle='<->', color='orange', lw=1.5))
ax3.text(22.5, 19, '15 cm', ha='center', fontsize=10, color='orange')

# Espesor brazo vertical
ax3.annotate('', xy=(17, 30), xytext=(17, 15),
             arrowprops=dict(arrowstyle='<->', color='orange', lw=1.5))
ax3.text(19, 22.5, '15 cm', va='center', fontsize=10, color='orange', rotation=90)

# Propiedades
ax3.text(15, 8, 'A = 675 cm2\nIy = Iz = 46375 cm4',
         ha='center', fontsize=10, color='white', fontweight='bold',
         bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))

# Centroide
ax3.plot(12.5, 12.5, 'r+', markersize=12, markeredgewidth=2)
ax3.text(14, 14, 'G (12.5, 12.5)', fontsize=9, color='red')

ax3.set_xlim(-8, 35)
ax3.set_ylim(-8, 35)
ax3.set_aspect('equal')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/section_L.png', dpi=150, bbox_inches='tight')
print('  results/section_L.png')

# ============================================================
# 3. GDL POR NODO
# ============================================================
fig3, ax4 = plt.subplots(1, 1, figsize=(8, 6))
ax4.set_title('GDL POR NODO - 6 grados de libertad', fontsize=13, fontweight='bold')
ax4.set_xlim(-2, 6)
ax4.set_ylim(-2, 5)
ax4.set_aspect('equal')
ax4.grid(True, alpha=0.3)

ax4.plot(2, 2, 'ko', markersize=12, zorder=5)
ax4.text(2, 2.3, 'Nodo', ha='center', fontsize=11, fontweight='bold')

# Traslaciones
ax4.annotate('', xy=(4, 2), xytext=(2, 2),
             arrowprops=dict(arrowstyle='->', color='blue', lw=2))
ax4.text(4.2, 2, 'UX (1)', fontsize=10, color='blue')

ax4.annotate('', xy=(2, 4), xytext=(2, 2),
             arrowprops=dict(arrowstyle='->', color='blue', lw=2))
ax4.text(2, 4.2, 'UY (2)', fontsize=10, color='blue', ha='center')

ax4.annotate('', xy=(3, 3.5), xytext=(2, 2),
             arrowprops=dict(arrowstyle='->', color='blue', lw=2))
ax4.text(3.2, 3.7, 'UZ (3)', fontsize=10, color='blue')

# Rotaciones
arc_rx = patches.Arc((2, 2), 1.5, 1.5, angle=0, theta1=30, theta2=150,
                      color='red', lw=2)
ax4.add_patch(arc_rx)
ax4.text(1, 3.2, 'thetaX (4)', fontsize=10, color='red')

arc_ry = patches.Arc((2, 2), 1.5, 1.5, angle=0, theta1=-60, theta2=60,
                      color='red', lw=2)
ax4.add_patch(arc_ry)
ax4.text(3.2, 1.2, 'thetaY (5)', fontsize=10, color='red')

arc_rz = patches.Arc((2, 2), 2.0, 2.0, angle=0, theta1=200, theta2=340,
                      color='red', lw=2)
ax4.add_patch(arc_rz)
ax4.text(2, -0.2, 'thetaZ (6)', fontsize=10, color='red', ha='center')

ax4.plot([], [], 'b-', linewidth=2, label='Traslaciones (DOF 1-3)')
ax4.plot([], [], 'r-', linewidth=2, label='Rotaciones (DOF 4-6)')
ax4.legend(loc='lower left', fontsize=10)

plt.tight_layout()
plt.savefig('results/gdl.png', dpi=150, bbox_inches='tight')
print('  results/gdl.png')

print('\nTodas las graficas generadas en results/')
