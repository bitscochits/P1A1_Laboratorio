#!/usr/bin/env python3
# shebang: le dice al sistema operativo que use Python para ejecutar este archivo

"""
LAB Benchmark 3D - Marco con vigas en L (losa colaborante ACI)
===============================================================
Descripcion:
  Modelo estructural 3D de un marco de un piso.
  - Columnas cuadradas 30x30 cm
  - Vigas tipo L (losa colaborante segun ACI, ancho ala = L/4)
  - Losa 15 cm con carga distribuida sobre vigas via eleLoad

Geometria:
  Planta: 4.0 m x 4.0 m (1 vano en cada direccion)
  Altura: 3.0 m (1 piso)

Material:
  Hormigon f'c = 25 MPa (G-25) -> Ec = 23469 MPa

Unidades: metros (m), kilonewtons (kN), kilopascales (kPa)
"""

# ============================================================
# IMPORTACIONES
# ============================================================
import openseespy.opensees as ops  # libreria de analisis estructural OpenSees
import json                         # para guardar resultados en formato JSON
import math                         # para operaciones matematicas (sqrt)
import os                           # para crear carpetas (makedirs)

# ============================================================
# 1. DATOS GEOMETRICOS
# ============================================================
# Coordenadas de los ejes de la estructura
X = [0.0, 4.0]   # dos ejes en X: Eje1 en x=0, Eje2 en x=4 -> 1 vano de 4m
Y = [0.0, 4.0]   # dos ejes en Y: EjeA en y=0, EjeB en y=4 -> 1 vano de 4m
Z = [0.0, 3.0]   # niveles: base en z=0, techo en z=3    -> altura de 3m

# Cantidad de ejes en cada direccion
nX, nY, nNivel = len(X), len(Y), len(Z)  # 2, 2, 2

# Total de nodos por piso = ejesX * ejesY = 2 * 2 = 4 nodos
nNodosPorPiso = nX * nY  # = 4

# ============================================================
# 2. MATERIAL Y SECCIONES
# ============================================================

# --- Material: Hormigon f'c = 25 MPa (G-25) ---
fpc   = 25.0                              # resistencia a compresion (MPa)
Ec    = 4700.0 * math.sqrt(fpc) * 1000.0  # modulo de elasticidad: 4700*sqrt(f'c)
                                           # se multiplica por 1000 para convertir MPa -> kPa
Gc    = Ec / (2.0 * (1.0 + 0.2))          # modulo de corte: G = E / (2*(1+nu))
                                           # asumimos nu = 0.2 (coeficiente de Poisson)
gamma = 25.0                               # peso unitario del hormigon armado (kN/m3)

# --- Columna cuadrada 30x30 cm ---
col_b = 0.30  # ancho de la columna (m)
col_h = 0.30  # altura de la columna (m)

A_col  = col_b * col_h              # area = 0.30 * 0.30 = 0.0900 m2
Iy_col = col_b * col_h**3 / 12.0    # inercia fuerte: b*h^3/12 = 6.75e-4 m4
Iz_col = col_h * col_b**3 / 12.0    # inercia debil: h*b^3/12 = 6.75e-4 m4
                                     # (iguales porque es cuadrada)
J_col  = min(Iy_col, Iz_col) * 0.3  # torsion: 30% del menor I = 2.025e-4 m4

# --- Viga tipo L (losa colaborante ACI) ---
# La seccion L representa la viga con la losa colaborante
# Alma: 25 x 35 cm (parte que sobresale bajo la losa)
# Ala: 100 x 15 cm (losa colaborante, ancho = L/4 = 4.0/4 = 1.0 m)
#
#   +------------------+  100 cm (ala = L/4)
#   |     15 cm        |
#   +------+-----+     |
#          |     |     |
#          |25x35|     |
#          |     |     |
#          +-----+     |
#
# Propiedades calculadas por composicion de rectangulos:
A_vig  = 0.237500        # area = 0.25*0.35 + 1.0*0.15 = 0.2375 m2
Iy_vig = 2.07271107e-02  # inercia LATERAL (ala ancha) = 2.07e-2 m4
Iz_vig = 4.62842654e-03  # inercia de GRAVEDAD (centroide corrido) = 4.63e-3 m4
                          # esta inercia es 1.78x mayor que la viga sola
J_vig  = 2.03909066e-03  # torsion (suma St. Venant) = 2.04e-3 m4

t_losa_carga = 0.15  # espesor de losa para calculo de cargas (m)

# ============================================================
# 3. CARGAS
# ============================================================
# Carga muerta (G) = peso propio losa + acabados
q_losa = gamma * t_losa_carga + 1.5   # = 25*0.15 + 1.5 = 5.25 kN/m2
                                       # peso propio losa: 3.75 kN/m2
                                       # acabados: 1.5 kN/m2 (pisos, ceramica, etc.)

# Carga viva (Q) segun usos (oficina/educacion)
q_viva = 2.0  # kN/m2

# ============================================================
# 4. FUNCIONES
# ============================================================

def construir_modelo():
    """
    Construye el modelo 3D completo en OpenSees.
    
    Pasos:
    1. Limpiar modelo anterior (wipe)
    2. Definir modelo 3D con 6 GDL por nodo
    3. Crear material elástico
    4. Definir transformaciones geometricas (orientacion de ejes locales)
    5. Crear nodos en las posiciones de la grilla
    6. Fijar apoyos en la base
    7. Crear elementos (columnas y vigas)
    
    Retorna:
        coords: diccionario {id_nodo: (x, y, z)}
        columnas: lista de tags de columnas
        vigas_x: lista de tags de vigas en X
        vigas_y: lista de tags de vigas en Y
    """
    
    # Limpiar cualquier modelo anterior en memoria de OpenSees
    ops.wipe()  # borra todo el modelo previo
    
    # Crear modelo basico 3D con 6 grados de libertad por nodo
    # -ndm 3: tres dimensiones (x, y, z)
    # -ndf 6: seis GDL por nodo (3 traslaciones + 3 rotaciones)
    ops.model('basic', '-ndm', 3, '-ndf', 6)
    
    # Material elástico unidimensional con modulo Ec
    # Se usa para las vigas y columnas (elasticBeamColumn requiere un material)
    ops.uniaxialMaterial('Elastic', 1, Ec)  # tag=1, rigididad=Ec

    # --- TRANSFORMACIONES GEOMETRICAS ---
    # Definen como se mapea el eje local del elemento al sistema global
    # Sintaxis: geomTransf('Linear', tag, vecxz_x, vecxz_y, vecxz_z)
    # El vector vecxz define el plano local x-z del elemento
    
    # Transformacion 1: COLUMNAS (eje local vertical, +Z global)
    # vecxz=(1,0,0) -> eje local z queda vertical, eje local y horizontal
    ops.geomTransf('Linear', 1, 1, 0, 0)  # tag=1
    
    # Transformacion 2: VIGAS EN X (eje local en +X global)
    # vecxz=(0,0,1) -> eje local z queda vertical (paralelo a Z global)
    # Esto es critico: la inercia de gravedad (Iz_vig) flexiona en el plano vertical
    ops.geomTransf('Linear', 2, 0, 0, 1)  # tag=2
    
    # Transformacion 3: VIGAS EN Y (eje local en +Y global)
    # vecxz=(0,0,1) -> misma orientacion que vigas X
    ops.geomTransf('Linear', 3, 0, 0, 1)  # tag=3

    # --- CREACION DE NODOS ---
    # Numeracion: se recorre nivel -> ix -> iy
    # Piso 0 (base):     nodos 1, 2, 3, 4
    # Piso 1 (techo):    nodos 5, 6, 7, 8
    
    coords = {}   # diccionario para guardar coordenadas {id: (x,y,z)}
    nid = 1       # contador de id de nodo, empieza en 1
    
    for iz in range(nNivel):       # recorre niveles: 0 (base), 1 (techo)
        for ix in range(nX):       # recorre ejes X: 0 (x=0), 1 (x=4)
            for iy in range(nY):   # recorre ejes Y: 0 (y=0), 1 (y=4)
                coords[nid] = (X[ix], Y[iy], Z[iz])  # guardar coordenadas
                ops.node(nid, X[ix], Y[iy], Z[iz])    # crear nodo en OpenSees
                nid += 1  # siguiente id

    # --- APOYOS: fijos en la base (todos los GDL restringidos) ---
    # Los nodos 1, 2, 3, 4 (nivel 0) son apoyos fijos
    # fix(nodeTag, dofx, dofy, dofz, dofrx, dofry, dofrz)
    # 1 = restringido (fijo), 0 = libre
    for i in range(1, nNodosPorPiso + 1):  # nodos 1 a 4
        ops.fix(i, 1, 1, 1, 1, 1, 1)  # todos los GDL fijos (empotramiento)

    # --- CREACION DE ELEMENTOS ---
    tag = 1        # tag del siguiente elemento (identificador unico)
    columnas = []  # lista para guardar tags de columnas
    vigas_x  = []  # lista para guardar tags de vigas en X
    vigas_y  = []  # lista para guardar tags de vigas en Y

    # --- COLUMNAS: conectan base (nivel 0) con techo (nivel 1) ---
    # Cada columna va del nodo base al nodo tope en la misma posicion
    for ix in range(nX):       # recorre columnas en X
        for iy in range(nY):   # recorre columnas en Y
            n1 = 1 + ix * nY + iy             # nodo del piso 0 (base)
            n2 = 1 + nNodosPorPiso + ix * nY + iy  # nodo del piso 1 (tope)
            
            # Crear elemento: elasticBeamColumn
            # Sintaxis: element('elasticBeamColumn', tag, ni, nj, A, E, G, J, Iy, Iz, transfTag)
            ops.element('elasticBeamColumn', tag, n1, n2,
                        A_col, Ec, Gc, J_col, Iy_col, Iz_col, 1)
            columnas.append(tag)  # guardar tag de esta columna
            tag += 1  # siguiente tag

    # --- VIGAS EN X: conectan nodos con mismo Y, distinto X ---
    # Para cada eje Y, hay una viga que va de X=0 a X=4
    for iy in range(nY):  # recorre ejes Y: 0 y 1
        n1 = 1 + nNodosPorPiso + 0 * nY + iy  # nodo en (0, Y[iy], 3)
        n2 = 1 + nNodosPorPiso + 1 * nY + iy  # nodo en (4, Y[iy], 3)
        
        # Crear viga con transformacion 2 (vecxz=0,0,1)
        # NOTA: pasamos Iz_vig como Iy_local e Iy_vig como Iz_local
        # porque con esta transformacion, el plano local x-z es VERTICAL
        # y la flexion por gravedad usa Iy_local (plano x-z)
        ops.element('elasticBeamColumn', tag, n1, n2,
                    A_vig, Ec, Gc, J_vig, Iz_vig, Iy_vig, 2)
        vigas_x.append(tag)  # guardar tag
        tag += 1

    # --- VIGAS EN Y: conectan nodos con mismo X, distinto Y ---
    # Para cada eje X, hay una viga que va de Y=0 a Y=4
    for ix in range(nX):  # recorre ejes X: 0 y 1
        n1 = 1 + nNodosPorPiso + ix * nY + 0  # nodo en (X[ix], 0, 3)
        n2 = 1 + nNodosPorPiso + ix * nY + 1  # nodo en (X[ix], 4, 3)
        
        # Misma logica de inercias que vigas X
        ops.element('elasticBeamColumn', tag, n1, n2,
                    A_vig, Ec, Gc, J_vig, Iz_vig, Iy_vig, 3)
        vigas_y.append(tag)  # guardar tag
        tag += 1

    return coords, columnas, vigas_x, vigas_y


def aplicar_carga_distribuida(q, vigas_x, vigas_y, incluir_peso_vigas=False):
    """
    Aplica carga de losa como DISTRIBUIDA UNIFORME sobre las vigas.
    
    Usa eleLoad con -beamUniform para aplicar carga distribuida real,
    lo que genera momentos y cortantes internos en las vigas.
    
    Metodo: cada viga recibe 1/4 del total de la losa (por simetria).
    La carga uniforme equivalente es: w = (q * Lx * Ly / 4) / L
    
    Args:
        q: carga uniforme sobre la losa (kN/m2)
        vigas_x: lista de tags de vigas en X
        vigas_y: lista de tags de vigas en Y
        incluir_peso_vigas: si True, agrega el peso propio de las vigas
    
    Sintaxis eleLoad:
        eleLoad('-ele', tag, '-type', '-beamUniform', Wy, Wz, Wx)
        Wy = carga en direccion local y (horizontal para vigas con vecxz=0,0,1)
        Wz = carga en direccion local z (vertical para vigas con vecxz=0,0,1)
        Wx = carga axial (0 para gravedad)
    """
    Lx = X[1] - X[0]  # longitud en X = 4.0 m
    Ly = Y[1] - Y[0]  # longitud en Y = 4.0 m

    # --- VIGAS EN X ---
    for tag in vigas_x:
        # Carga total que recibe esta viga = 1/4 del total de la losa
        carga_viga = q * Lx * Ly / 4.0  # kN
        
        # Carga uniforme distribuida = carga total / longitud de la viga
        w = carga_viga / Lx  # kN/m
        
        # Agregar peso propio de la viga si se solicita
        if incluir_peso_vigas:
            w += gamma * A_vig  # peso propio = 25 * 0.2375 = 5.9375 kN/m
        
        # Aplicar carga distribuida via eleLoad
        # Wy=0.0 (sin carga horizontal), Wz=-w (gravedad hacia abajo)
        ops.eleLoad('-ele', tag, '-type', '-beamUniform', 0.0, -w, 0.0)

    # --- VIGAS EN Y ---
    for tag in vigas_y:
        carga_viga = q * Lx * Ly / 4.0  # misma carga total
        w = carga_viga / Ly  # kN/m (divide por Ly porque la viga va en Y)
        
        if incluir_peso_vigas:
            w += gamma * A_vig
        
        # Misma sintaxis: Wz=-w para gravedad
        ops.eleLoad('-ele', tag, '-type', '-beamUniform', 0.0, -w, 0.0)


def resolver():
    """
    Configura y ejecuta el analisis estatico lineal.
    
    Configuracion:
    - BandGeneral: sistema de ecuaciones en banda (mas robusto con eleLoad)
    - RCM: numerador Reverse Cuthill-McKee (reduce ancho de banda)
    - Transformation: restricciones para eleLoad
    - LoadControl 1.0: aplica la carga completa en 1 paso
    - Linear: algoritmo sin iteracion (modelo lineal)
    
    Retorna:
        ok: 0 si convergio, != 0 si fallo
    """
    ops.system('BandGeneral')       # sistema de ecuaciones en banda
    ops.numberer('RCM')             # numerador RCM
    ops.constraints('Transformation')  # restricciones para eleLoad
    ops.integrator('LoadControl', 1.0)  # paso de carga completo
    ops.algorithm('Linear')         # algoritmo lineal (sin iteracion)
    ops.analysis('Static')          # analisis estatico
    ok = ops.analyze(1)             # ejecutar 1 paso
    ops.reactions()                 # calcular reacciones en apoyos
    return ok  # 0 = exitoso


def extraer_resultados(coords):
    """
    Extrae desplazamientos y reacciones del modelo resuelto.
    
    Args:
        coords: diccionario de coordenadas {id_nodo: (x,y,z)}
    
    Returns:
        disp: diccionario {id_nodo: [ux, uy, uz, rx, ry, rz]}
        reac: diccionario {id_nodo: [fx, fy, fz, mx, my, mz]} (solo apoyos)
    """
    # Desplazamientos de TODOS los nodos
    disp = {nid: [ops.nodeDisp(nid, i) for i in range(1, 7)] for nid in coords}
    
    # Reacciones SOLO en los apoyos (nodos 1 a 4)
    reac = {nid: [ops.nodeReaction(nid, i) for i in range(1, 7)]
            for nid in range(1, nNodosPorPiso + 1)}
    
    return disp, reac


# ============================================================
# 5. EJECUCION PRINCIPAL
# ============================================================

# Imprimir titulo
print("=" * 60)
print("  LAB BENCHMARK 3D - CARGA DISTRIBUIDA (eleLoad)")
print("=" * 60)

# Construir el modelo (nodos, apoyos, elementos)
coords, cols, vx, vy = construir_modelo()

# Identificar nodos del piso superior (techo)
# Nodos base: 1 a 4, Nodos techo: 5 a 8
nodos_piso1 = list(range(nNodosPorPiso + 1, 2 * nNodosPorPiso + 1))

# Imprimir resumen
print(f"\n  Columnas: {len(cols)} | Vigas X: {len(vx)} | Vigas Y: {len(vy)}")

# --- CASO G: CARGA MUERTA (distribuida + peso propio) ---
print("\n[G] Carga muerta distribuida...")
construir_modelo()  # modelo limpio

# Configurar patron de carga
ops.timeSeries('Linear', 1)   # serie temporal: carga incremental lineal
ops.pattern('Plain', 1, 1)    # patron plano, usa serie temporal 1

# Aplicar carga muerta distribuida (losa + acabados + peso vigas)
aplicar_carga_distribuida(q_losa, vx, vy, incluir_peso_vigas=True)

# Resolver
ok_G = resolver()

# Extraer resultados
disp_G, reac_G = extraer_resultados(coords)

# Extraer fuerzas internas de las vigas X
# eleForce retorna: [Pi, V2i, V3i, Ti, M2i, M3i, Pj, V2j, V3j, Tj, M2j, M3j]
fuerzas_G = {etag: [round(f, 4) for f in ops.eleForce(etag)] for etag in vx}

print(f"    Convergencia: {'OK' if ok_G == 0 else 'FALLO'}")

# --- CASO Q: CARGA VIVA (distribuida, sin peso propio) ---
print("[Q] Carga viva distribuida...")
construir_modelo()  # modelo limpio

ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)

# Aplicar solo carga viva (sin peso de vigas)
aplicar_carga_distribuida(q_viva, vx, vy, incluir_peso_vigas=False)

ok_Q = resolver()
disp_Q, reac_Q = extraer_resultados(coords)
print(f"    Convergencia: {'OK' if ok_Q == 0 else 'FALLO'}")

# --- CASO EX: CARGA LATERAL (sismo en X) ---
print("[EX] Carga lateral...")
construir_modelo()  # modelo limpio

ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)

# Carga lateral: 50 kN en +X en cada nodo del techo
F_sismo = 50.0  # kN

for nid in nodos_piso1:  # nodos 5, 6, 7, 8
    ops.load(nid, F_sismo, 0.0, 0.0, 0.0, 0.0, 0.0)  # carga en X

ok_EX = resolver()
disp_EX, reac_EX = extraer_resultados(coords)
print(f"    Convergencia: {'OK' if ok_EX == 0 else 'FALLO'}")

# ============================================================
# 6. VERIFICACION DE EQUILIBRIO
# ============================================================
print("\n" + "=" * 60)
print("  EQUILIBRIO")
print("=" * 60)

# Dimensiones del vano
Lx, Ly = X[1] - X[0], Y[1] - Y[0]  # 4.0 m, 4.0 m
area = Lx * Ly  # 16.0 m2

# --- Carga muerta total (G) ---
G_losa = q_losa * area          # peso losa+acabados: 5.25*16 = 84 kN
G_peso_vigas = 4 * gamma * A_vig * Lx  # peso 4 vigas: 4*25*0.2375*4 = 95 kN
G_tot = G_losa + G_peso_vigas   # total: 84+95 = 179 kN

# --- Carga viva total (Q) ---
Q_tot = q_viva * area  # 2.0*16 = 32 kN

# --- Sumar reacciones ---
sG = sum(reac_G[n][2] for n in reac_G)  # suma Fz en apoyos (caso G)
sQ = sum(reac_Q[n][2] for n in reac_Q)  # suma Fz en apoyos (caso Q)
sX = sum(reac_EX[n][0] for n in reac_EX)  # suma Fx en apoyos (caso EX)

# Imprimir verificacion
print(f"\n  G: aplicado {G_tot:.2f} kN | reaccion {sG:.2f} kN | error {abs(G_tot-sG):.6f}")
print(f"  Q: aplicado {Q_tot:.2f} kN | reaccion {sQ:.2f} kN | error {abs(Q_tot-sQ):.6f}")
print(f"  EX: aplicado {F_sismo*4:.2f} kN | reaccion {sX:.2f} kN | error {abs(F_sismo*4+sX):.6f}")

# ============================================================
# 7. DESPLAZAMIENTOS Y MOMENTOS
# ============================================================
print("\n" + "=" * 60)
print("  DESPLAZAMIENTOS NODO TECHO")
print("=" * 60)

# Imprimir encabezado de tabla
print(f"  {'Nodo':<6}{'UZ_G(mm)':<12}{'UZ_Q(mm)':<12}{'UX_EX(mm)':<12}")

# Recorrer nodos del techo
for nid in nodos_piso1:  # nodos 5, 6, 7, 8
    # Imprimir desplazamientos convertidos de m a mm
    print(f"  {nid:<6}{disp_G[nid][2]*1000:<12.5f}"
          f"{disp_Q[nid][2]*1000:<12.5f}{disp_EX[nid][0]*1000:<12.5f}")

# --- MOMENTOS EN VIGAS ---
print("\n" + "=" * 60)
print("  MOMENTO EN VIGAS (Caso G) - ahora SI hay flexion interna")
print("=" * 60)
print("  eleForce = [Pi,V2i,V3i,Ti,M2i,M3i, Pj,V2j,V3j,Tj,M2j,M3j]")
print("  (el momento de gravedad esta en M2 -> indices 4 y 10)")

# Recorrer vigas X y mostrar momentos
for etag in vx:
    f = fuerzas_G[etag]  # [Pi, V2i, V3i, Ti, M2i, M3i, Pj, V2j, V3j, Tj, M2j, M3j]
    # Con vecxz=(0,0,1):
    # - M2 (indice 4 en nodo i, indice 10 en nodo j) = momento de gravedad
    # - V3 (indice 2 en nodo i) = cortante vertical
    print(f"  Viga {etag}: M2_i={f[4]:.3f}  M2_j={f[10]:.3f} kN·m  |  "
          f"V3_i={f[2]:.3f} kN (cortante vertical)")

# ============================================================
# 8. GUARDAR RESULTADOS EN JSON
# ============================================================
# Crear carpeta results si no existe
os.makedirs('results', exist_ok=True)

# Construir diccionario de resultados
resultados = {
    'model_info': {  # informacion general del modelo
        'description': 'Marco 3D vigas L, CARGA DISTRIBUIDA (eleLoad beamUniform)',
        'metodo_carga': 'distribuida uniforme equivalente sobre vigas',
        'material': {'fpc_MPa': fpc, 'Ec_kPa': round(Ec, 0)},
        'units': 'm, kN, kPa',
    },
    'nodes': {str(k): list(v) for k, v in coords.items()},  # coordenadas nodos
    'elements': {'columns': cols, 'beams_x': vx, 'beams_y': vy},  # tags elementos
    'load_cases': {  # casos de carga
        'G': {  # carga muerta
            'applied_kN': round(G_tot, 2),        # carga aplicada
            'reaction_kN': round(sG, 2),           # suma reacciones
            'error_kN': round(abs(G_tot-sG), 6),   # error equilibrio
            'displacements': {  # desplazamientos (solo UX, UY, UZ)
                str(k): [round(v[i], 8) for i in range(3)]
                for k, v in disp_G.items()
            },
            'reactions': {  # reacciones (solo Fx, Fy, Fz)
                str(k): [round(v[i], 4) for i in range(3)]
                for k, v in reac_G.items()
            }
        },
        'Q': {  # carga viva
            'applied_kN': round(Q_tot, 2),
            'reaction_kN': round(sQ, 2),
            'error_kN': round(abs(Q_tot-sQ), 6),
            'displacements': {
                str(k): [round(v[i], 8) for i in range(3)]
                for k, v in disp_Q.items()
            }
        },
        'EX': {  # sismo en X
            'applied_kN': F_sismo*4,  # 50*4 = 200 kN total
            'displacements': {
                str(k): [round(v[i], 8) for i in range(3)]
                for k, v in disp_EX.items()
            }
        },
    },
}

# Guardar en archivo JSON
with open('results/lab_results.json', 'w') as f:
    json.dump(resultados, f, indent=2)  # indent=2 para formato legible

# Imprimir confirmacion
print(f"\nGuardado en results/lab_results.json")
print("=" * 60)
