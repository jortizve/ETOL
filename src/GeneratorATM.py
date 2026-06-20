import random
from typing import List, Tuple

# --------------------------
#  Núcleo ATM base (16 estados)
# --------------------------
BASE_STATES = ["I","W","WP","WC","WA","PNW","PQW","DB","MAN","MAQ","OO","T","C","E","X1","X2"]
# Nota: en tu ejemplo "Name_State" parece tener 14; pero tu Transition es 16x16.
# Aquí fijamos 16 para ser consistente con la matriz 16x16.
# Si tú realmente tienes 14, ajustamos, pero tu matriz que pegaste es 16x16.

BASE_APS = ["cash", "balance"]

# Etiquetado del núcleo (16 filas, 2 props). Ajusta si tu núcleo real es 14.
# En tu ejemplo: DB tenía balance=1, y algunos tenían cash=1.
# Aquí mantengo algo muy parecido: DB -> balance, MAN/MAQ -> cash, etc. (puedes refinar)
BASE_LAB = [
    [0,0],  # I
    [0,0],  # W
    [0,0],  # WP
    [0,0],  # WC
    [0,0],  # WA
    [0,0],  # PNW
    [0,0],  # PQW
    [0,1],  # DB  (balance)
    [1,0],  # MAN (cash)
    [1,0],  # MAQ (cash)
    [0,0],  # OO
    [0,0],  # T
    [0,0],  # C
    [0,0],  # E
    [0,0],  # X1 extra
    [0,0],  # X2 extra
]

# Matriz base 16x16 (la tuya era 16x16 con números como 2,3,4.. -> si tu parser permite >1, ok)
# Yo la dejo exactamente como tu bloque 16x16 (conservando tus números).
BASE_TRANSITION = [
    [0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [2,2,3,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [3,0,0,0,4,5,6,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,7,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,8,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,9,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,10,11,12,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,13,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,14,15],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,16],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,17],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,18],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,19],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,20],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# Clocks y constraints del núcleo (mantengo tu estilo: constraints por transición)
# En tu ejemplo Clock_constraints eran 14 líneas; aquí damos 16.
# Formato: una línea por estado-origen, con n entradas separadas por espacios.
# Si tu parser asocia constraints a transiciones i->j, esto encaja.
def base_clock_constraints(n: int) -> List[List[str]]:
    cc = [["0"]*n for _ in range(n)]
    # Ejemplo: algunas transiciones con x<=10, x<=15, etc.
    # Conserva el "sabor" de tu ATM (puedes ajustar a tu gusto).
    # W->WP con x=3 (como tu segunda fila: x=3 en (W->I) pero tu matriz era rara; aquí lo ponemos en un edge real)
    # Lo más seguro: poner restricciones sólo donde haya edge.
    for i in range(n):
        for j in range(n):
            if BASE_TRANSITION[i][j] != 0:
                cc[i][j] = "x<=10"
    # Ajustes más “ATM-like”
    # I->W: x<=3
    cc[0][1] = "x<=3"
    # DB->OO y DB->T y DB->C algo como x<=10
    # (ya están)
    # MAN/MAQ hacia E con x<=20
    if 8 < n and 13 < n:
        cc[8][13] = "x<=20"
    return cc

def base_invariants() -> List[List[str]]:
    # Invariants: una línea por estado, con 2 clocks (x y) => "x<=10 0" etc.
    inv = []
    # Copio tu estilo aproximado:
    inv.append(["x<=3","0"])      # I
    inv.append(["x<=10","0"])     # W
    inv.append(["x<=10","0"])     # WP
    inv.append(["x<=10","0"])     # WC
    inv.append(["x<=15","0"])     # WA
    inv.append(["x<=15","0"])     # PNW
    inv.append(["x<=10","0"])     # PQW
    inv.append(["x<=20","0"])     # DB
    inv.append(["x<=20","0"])     # MAN
    inv.append(["x<=10","0"])     # MAQ
    inv.append(["0","y<=100"])    # OO
    inv.append(["0","y<=100"])    # T
    inv.append(["0","0"])         # C
    inv.append(["0","0"])         # E
    inv.append(["0","0"])         # X1
    inv.append(["0","0"])         # X2
    return inv

# --------------------------
#  Construcción de módulos de sesión
# --------------------------
def add_session_module(
    states: List[str],
    trans: List[List[int]],
    lab: List[List[int]],
    cc: List[List[str]],
    inv: List[List[str]],
    rng: random.Random,
    attach_from: str,
    return_to: str,
    module_size: int = 10,
    module_id: int = 0,
):
    """
   
      entry -> auth -> choose -> (cash_path | balance_path) -> exit -> return_to
    Conecta attach_from -> entry y exit -> return_to.
    """

    n0 = len(states)
    # nombres del módulo
    entry = f"m{module_id}_ENTRY"
    auth  = f"m{module_id}_AUTH"
    choose= f"m{module_id}_CHOOSE"
    cash1 = f"m{module_id}_CASH1"
    cash2 = f"m{module_id}_CASH2"
    bal1  = f"m{module_id}_BAL1"
    bal2  = f"m{module_id}_BAL2"
    exit_ = f"m{module_id}_EXIT"

    module_nodes = [entry, auth, choose, cash1, cash2, bal1, bal2, exit_]

    # completa con estados internos extra
    while len(module_nodes) < module_size:
        module_nodes.insert(-1, f"m{module_id}_MID{len(module_nodes)}")

    # añade estados
    for s in module_nodes:
        states.append(s)
        lab.append([0,0])             # por defecto sin props
        inv.append(["0","0"])         # sin invariantes especiales (puedes meter x<=... si quieres)

    # expande matrices trans y cc a nuevo tamaño
    newN = len(states)
    for row in trans:
        row.extend([0]*(newN - len(row)))
    for row in cc:
        row.extend(["0"]*(newN - len(row)))
    for _ in range(newN - len(trans)):
        trans.append([0]*newN)
        cc.append(["0"]*newN)

    # índices útiles
    idx = {name:i for i,name in enumerate(states)}
    def edge(a: str, b: str, weight: int = 1, guard: str = "x<=10"):
        i, j = idx[a], idx[b]
        trans[i][j] = weight
        cc[i][j] = guard

    # Conexiones módulo (con “sentido”):
    edge(attach_from, entry, 1, "x<=3")
    edge(entry, auth, 1, "x<=10")
    edge(auth, choose, 1, "x<=10")

    # Rama cash
    edge(choose, cash1, 1, "x<=10")
    edge(cash1, cash2, 1, "x<=20")
    edge(cash2, exit_, 1, "x<=20")
    # Marca cash2 como cash=1
    lab[idx[cash2]] = [1,0]

    # Rama balance
    edge(choose, bal1, 1, "x<=10")
    edge(bal1, bal2, 1, "x<=20")
    edge(bal2, exit_, 1, "x<=20")
    # Marca bal2 como balance=1
    lab[idx[bal2]] = [0,1]

    # Algunos loops internos opcionales (esperas/reintentos)
    mids = [s for s in module_nodes if "MID" in s]
    for m in mids:
        # pequeño loop
        if rng.random() < 0.5:
            edge(m, m, 1, "x<=5")
        # conecta choose -> mid -> exit
        edge(choose, m, 1, "x<=10")
        edge(m, exit_, 1, "x<=10")

    # salida al núcleo
    edge(exit_, return_to, 1, "x<=10")

def gen_big_atm_model(path: str, modules: int, module_size: int = 12, noise_edges: int = 0, seed: int = 0):
    rng = random.Random(seed)

    # start with base
    states = list(BASE_STATES)
    N = len(states)
    trans = [row[:] for row in BASE_TRANSITION]
    lab = [row[:] for row in BASE_LAB]

    cc0 = base_clock_constraints(N)
    inv0 = base_invariants()

    cc = [row[:] for row in cc0]
    inv = [row[:] for row in inv0]

    # añade módulos conectados desde W o WP, retorna a T (para que fórmulas con T sigan teniendo sentido)
    attach_candidates = ["W", "WP", "WC", "WA"]
    for k in range(modules):
        attach_from = rng.choice(attach_candidates)
        add_session_module(
            states, trans, lab, cc, inv, rng,
            attach_from=attach_from,
            return_to="T",
            module_size=module_size,
            module_id=k
        )

    # añade ruido controlado (edges extra) para hacerlo menos lineal, sin tocar el núcleo demasiado
    if noise_edges > 0:
        idx = {name:i for i,name in enumerate(states)}
        for _ in range(noise_edges):
            a = rng.randrange(len(states))
            b = rng.randrange(len(states))
            if a != b:
                trans[a][b] = 1
                cc[a][b] = rng.choice(["x<=10","x<=15","x<=20","0"])

    # valida tamaños
    n = len(states)
    assert len(trans) == n and all(len(row) == n for row in trans), "Transition matrix not square"
    assert len(cc) == n and all(len(row) == n for row in cc), "Clock_constraints matrix not square"
    assert len(lab) == n, "Labelling rows mismatch"
    assert len(inv) == n, "Invariants rows mismatch"

    # escribe fichero .model con tu formato
    with open(path, "w", encoding="utf-8") as f:
        f.write("Transition\n")
        for i in range(n):
            f.write(" ".join(str(trans[i][j]) for j in range(n)) + "\n")

        f.write("\nName_State\n")
        f.write(" ".join(states) + "\n\n")

        f.write("Initial_State\n")
        f.write("I\n\n")

        f.write("Atomic_propositions\n")
        f.write(" ".join(BASE_APS) + "\n\n")

        f.write("Labelling\n")
        for i in range(n):
            f.write(" ".join(str(x) for x in lab[i]) + "\n")

        f.write("\nNumber_of_agents\n1\n\n")

        f.write("Clocks\n")
        f.write("x y\n\n")

        f.write("Clock_constraints\n")
        for i in range(n):
            f.write(" ".join(cc[i][j] for j in range(n)) + "\n")

        f.write("\nInvariants\n")
        for i in range(n):
            f.write(" ".join(inv[i]) + "\n")

    print(f"Wrote {path} with {n} states (modules={modules}, module_size={module_size}).")
    
def gen_big_atm_model_by_size(
        path: str,
        target_states: int,
        module_size: int = 12,
        noise_ratio: float = 0.05,   # 5% de edges extra respecto a n (ajusta a gusto)
        seed: int = 0,
    ):
        """
        Genera un modelo ATM grande con aproximadamente target_states estados.
        Mantiene el núcleo fijo y añade módulos hasta alcanzar (o aproximar) el tamaño.
        """
        base_n = len(BASE_STATES)
        if target_states <= base_n:
            # Si pides menos o igual que el núcleo, simplemente genera el núcleo (sin módulos)
            return gen_big_atm_model(path, modules=0, module_size=module_size, noise_edges=0, seed=seed)

        # Estados añadidos por módulo (exactamente module_size)
        modules = (target_states - base_n) // module_size
        modules = max(1, modules)

        # Ruido proporcional al tamaño final aproximado
        approx_n = base_n + modules * module_size
        noise_edges = int(noise_ratio * approx_n)

        return gen_big_atm_model(
            path,
            modules=modules,
            module_size=module_size,
            noise_edges=noise_edges,
            seed=seed,
        )   

if __name__ == "__main__":
    # Ejemplos por tamaño total deseado (aprox)
    gen_big_atm_model_by_size("m_200_0.model", target_states=200, module_size=12, noise_ratio=0.05, seed=42)
    gen_big_atm_model_by_size("m_400_0.model", target_states=400, module_size=12, noise_ratio=0.05, seed=43)
    gen_big_atm_model_by_size("m_600_0.model", target_states=600, module_size=12, noise_ratio=0.05, seed=42)
    gen_big_atm_model_by_size("m_800_0.model", target_states=800, module_size=12, noise_ratio=0.05, seed=43)
    gen_big_atm_model_by_size("m_1000_0.model", target_states=1000, module_size=12, noise_ratio=0.05, seed=43)
    gen_big_atm_model_by_size("m_1200_0.model", target_states=1200, module_size=12, noise_ratio=0.05, seed=44)
    gen_big_atm_model_by_size("m_1400_0.model", target_states=1400, module_size=12, noise_ratio=0.05, seed=44)
    gen_big_atm_model_by_size("m_1800_0.model", target_states=1800, module_size=12, noise_ratio=0.05, seed=44)
    gen_big_atm_model_by_size("m_2000_0.model", target_states=2000, module_size=12, noise_ratio=0.05, seed=44)
