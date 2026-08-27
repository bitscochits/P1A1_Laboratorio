
import openseespy.opensees as ops
import json
import math
import os

# ============================================================
# 1. DATOS GEOMETRICOS
# ============================================================
X = [0.0, 4.0]
Y = [0.0, 4.0]
Z = [0.0, 3.0]
nX, nY, nNivel = len(X), len(Y), len(Z)
nNodosPorPiso = nX * nY

# ============================================================
# 2. MATERIAL Y SECCIONES
# ============================================================
fpc   = 25.0
Ec    = 4700.0 * math.sqrt(fpc) * 1000.0
Gc    = Ec / (2.0 * (1.0 + 0.2))
gamma = 25.0

# Columna cuadrada 30x30
col_b, col_h = 0.30, 0.30
A_col  = col_b * col_h
Iy_col = col_b * col_h**3 / 12.0
Iz_col = col_h * col_b**3 / 12.0
J_col  = min(Iy_col, Iz_col) * 0.3

# Viga L (losa colaborante ACI)
A_vig  = 0.237500
Iy_vig = 2.07271107e-02   # lateral
Iz_vig = 4.62842654e-03   # gravedad
J_vig  = 2.03909066e-03

t_losa_carga = 0.15

# ============================================================
# 3. CARGAS
# ============================================================
q_losa = gamma * t_losa_carga + 1.5   # 5.25 kN/m2 (muerta sobre losa)
q_viva = 2.0                           # kN/m2

# ============================================================
# 4. FUNCIONES
# ============================================================

def construir_modelo():
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 6)
    ops.uniaxialMaterial('Elastic', 1, Ec)

    ops.geomTransf('Linear', 1, 1, 0, 0)   # columnas
    ops.geomTransf('Linear', 2, 0, 0, 1)   # vigas X
    ops.geomTransf('Linear', 3, 0, 0, 1)   # vigas Y

    coords = {}
    nid = 1
    for iz in range(nNivel):
        for ix in range(nX):
            for iy in range(nY):
                coords[nid] = (X[ix], Y[iy], Z[iz])
                ops.node(nid, X[ix], Y[iy], Z[iz])
                nid += 1

    for i in range(1, nNodosPorPiso + 1):
        ops.fix(i, 1, 1, 1, 1, 1, 1)

    tag = 1
    columnas, vigas_x, vigas_y = [], [], []

    for ix in range(nX):
        for iy in range(nY):
            n1 = 1 + ix * nY + iy
            n2 = 1 + nNodosPorPiso + ix * nY + iy
            ops.element('elasticBeamColumn', tag, n1, n2,
                        A_col, Ec, Gc, J_col, Iy_col, Iz_col, 1)
            columnas.append(tag)
            tag += 1

    for iy in range(nY):
        n1 = 1 + nNodosPorPiso + 0 * nY + iy
        n2 = 1 + nNodosPorPiso + 1 * nY + iy
        ops.element('elasticBeamColumn', tag, n1, n2,
                    A_vig, Ec, Gc, J_vig, Iz_vig, Iy_vig, 2)
        vigas_x.append(tag)
        tag += 1

    for ix in range(nX):
        n1 = 1 + nNodosPorPiso + ix * nY + 0
        n2 = 1 + nNodosPorPiso + ix * nY + 1
        ops.element('elasticBeamColumn', tag, n1, n2,
                    A_vig, Ec, Gc, J_vig, Iz_vig, Iy_vig, 3)
        vigas_y.append(tag)
        tag += 1

    return coords, columnas, vigas_x, vigas_y


def aplicar_carga_distribuida(q, vigas_x, vigas_y, incluir_peso_vigas=False):
    """
    Carga de losa como DISTRIBUIDA UNIFORME sobre las vigas via eleLoad.

    Reparto: losa cuadrada -> cada viga toma q*Lx*Ly/4 del total.
    Como carga uniforme equivalente sobre su luz:  w = carga_viga / L.

    Para las vigas del modelo (geomTransf vecxz=(0,0,1)), la gravedad
    se aplica en el 2do componente de -beamUniform (Wz local).
    Sintaxis: eleLoad('-ele',tag,'-type','-beamUniform', Wy, Wz, Wx)
    """
    Lx = X[1] - X[0]
    Ly = Y[1] - Y[0]

    # Vigas X
    for tag in vigas_x:
        carga_viga = q * Lx * Ly / 4.0
        w = carga_viga / Lx
        if incluir_peso_vigas:
            w += gamma * A_vig          # peso propio distribuido (kN/m)
        ops.eleLoad('-ele', tag, '-type', '-beamUniform', 0.0, -w, 0.0)

    # Vigas Y
    for tag in vigas_y:
        carga_viga = q * Lx * Ly / 4.0
        w = carga_viga / Ly
        if incluir_peso_vigas:
            w += gamma * A_vig
        ops.eleLoad('-ele', tag, '-type', '-beamUniform', 0.0, -w, 0.0)


def resolver():
    ops.system('BandGeneral')   # mas robusto que BandSPD con eleLoad
    ops.numberer('RCM')
    ops.constraints('Transformation')
    ops.integrator('LoadControl', 1.0)
    ops.algorithm('Linear')
    ops.analysis('Static')
    ok = ops.analyze(1)
    ops.reactions()
    return ok


def extraer_resultados(coords):
    disp = {nid: [ops.nodeDisp(nid, i) for i in range(1, 7)] for nid in coords}
    reac = {nid: [ops.nodeReaction(nid, i) for i in range(1, 7)]
            for nid in range(1, nNodosPorPiso + 1)}
    return disp, reac


# ============================================================
# 5. EJECUCION
# ============================================================
print("=" * 60)
print("  LAB BENCHMARK 3D - CARGA DISTRIBUIDA (eleLoad)")
print("=" * 60)

coords, cols, vx, vy = construir_modelo()
nodos_piso1 = list(range(nNodosPorPiso + 1, 2 * nNodosPorPiso + 1))
print(f"\n  Columnas: {len(cols)} | Vigas X: {len(vx)} | Vigas Y: {len(vy)}")

# CASO G (distribuida + peso propio)
print("\n[G] Carga muerta distribuida...")
construir_modelo()
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)
aplicar_carga_distribuida(q_losa, vx, vy, incluir_peso_vigas=True)
ok_G = resolver()
disp_G, reac_G = extraer_resultados(coords)
# fuerzas internas AHORA si tienen sentido (viga con carga en su luz)
fuerzas_G = {etag: [round(f, 4) for f in ops.eleForce(etag)] for etag in vx}
print(f"    Convergencia: {'OK' if ok_G == 0 else 'FALLO'}")

# CASO Q
print("[Q] Carga viva distribuida...")
construir_modelo()
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)
aplicar_carga_distribuida(q_viva, vx, vy, incluir_peso_vigas=False)
ok_Q = resolver()
disp_Q, reac_Q = extraer_resultados(coords)
print(f"    Convergencia: {'OK' if ok_Q == 0 else 'FALLO'}")

# CASO EX (lateral, sigue siendo nodal)
print("[EX] Carga lateral...")
construir_modelo()
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)
F_sismo = 50.0
for nid in nodos_piso1:
    ops.load(nid, F_sismo, 0.0, 0.0, 0.0, 0.0, 0.0)
ok_EX = resolver()
disp_EX, reac_EX = extraer_resultados(coords)
print(f"    Convergencia: {'OK' if ok_EX == 0 else 'FALLO'}")

# ============================================================
# 6. EQUILIBRIO
# ============================================================
print("\n" + "=" * 60)
print("  EQUILIBRIO")
print("=" * 60)

Lx, Ly = X[1] - X[0], Y[1] - Y[0]
area = Lx * Ly

# G: losa+acabados sobre area + peso propio de las 4 vigas
G_losa = q_losa * area
G_peso_vigas = 4 * gamma * A_vig * Lx
G_tot = G_losa + G_peso_vigas
Q_tot = q_viva * area

sG = sum(reac_G[n][2] for n in reac_G)
sQ = sum(reac_Q[n][2] for n in reac_Q)
sX = sum(reac_EX[n][0] for n in reac_EX)

print(f"\n  G: aplicado {G_tot:.2f} kN | reaccion {sG:.2f} kN | error {abs(G_tot-sG):.6f}")
print(f"  Q: aplicado {Q_tot:.2f} kN | reaccion {sQ:.2f} kN | error {abs(Q_tot-sQ):.6f}")
print(f"  EX: aplicado {F_sismo*4:.2f} kN | reaccion {sX:.2f} kN | error {abs(F_sismo*4+sX):.6f}")

# ============================================================
# 7. DESPLAZAMIENTOS Y MOMENTOS
# ============================================================
print("\n" + "=" * 60)
print("  DESPLAZAMIENTOS NODO TECHO")
print("=" * 60)
print(f"  {'Nodo':<6}{'UZ_G(mm)':<12}{'UZ_Q(mm)':<12}{'UX_EX(mm)':<12}")
for nid in nodos_piso1:
    print(f"  {nid:<6}{disp_G[nid][2]*1000:<12.5f}"
          f"{disp_Q[nid][2]*1000:<12.5f}{disp_EX[nid][0]*1000:<12.5f}")

print("\n" + "=" * 60)
print("  MOMENTO EN VIGAS (Caso G) - ahora SI hay flexion interna")
print("=" * 60)
print("  eleForce = [Pi,V2i,V3i,Ti,M2i,M3i, Pj,V2j,V3j,Tj,M2j,M3j]")
print("  (el momento de gravedad esta en M2 -> indices 4 y 10)")
for etag in vx:
    f = fuerzas_G[etag]
    # Con vecxz=(0,0,1) la flexion vertical genera momento M2 (indices 4 e i, 10 en j)
    print(f"  Viga {etag}: M2_i={f[4]:.3f}  M2_j={f[10]:.3f} kN·m  |  "
          f"V3_i={f[2]:.3f} kN (cortante vertical)")

# ============================================================
# 8. GUARDAR JSON
# ============================================================
os.makedirs('results', exist_ok=True)
resultados = {
    'model_info': {
        'description': 'Marco 3D vigas L, CARGA DISTRIBUIDA (eleLoad beamUniform)',
        'metodo_carga': 'distribuida uniforme equivalente sobre vigas',
        'material': {'fpc_MPa': fpc, 'Ec_kPa': round(Ec, 0)},
        'units': 'm, kN, kPa',
    },
    'nodes': {str(k): list(v) for k, v in coords.items()},
    'elements': {'columns': cols, 'beams_x': vx, 'beams_y': vy},
    'load_cases': {
        'G': {'applied_kN': round(G_tot, 2), 'reaction_kN': round(sG, 2),
              'error_kN': round(abs(G_tot-sG), 6),
              'displacements': {str(k): [round(v[i], 8) for i in range(3)]
                                for k, v in disp_G.items()},
              'reactions': {str(k): [round(v[i], 4) for i in range(3)]
                            for k, v in reac_G.items()}},
        'Q': {'applied_kN': round(Q_tot, 2), 'reaction_kN': round(sQ, 2),
              'error_kN': round(abs(Q_tot-sQ), 6),
              'displacements': {str(k): [round(v[i], 8) for i in range(3)]
                                for k, v in disp_Q.items()}},
        'EX': {'applied_kN': F_sismo*4,
               'displacements': {str(k): [round(v[i], 8) for i in range(3)]
                                 for k, v in disp_EX.items()}},
    },
}
with open('results/lab_results.json', 'w') as f:
    json.dump(resultados, f, indent=2)

print(f"\nGuardado en results/lab_results.json")
print("=" * 60)