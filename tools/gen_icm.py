#!/usr/bin/env python3
"""Generate the ICM (Intro a Ciencia dos Materiais) catalogs and previews.

Writes src/catalog_exercicios.c and src/catalog_teoria.c from the data below.
Each exercise -> pages: Enunciado -> [Grafico] -> Resolucao -> Resultado.
Lines support markup: "# " = blue heading, "= " = red result line.

  python tools/gen_icm.py                 # write the C catalogs
  python tools/gen_icm.py --preview DIR    # also render page PNGs
"""

import argparse
from pathlib import Path

import icm_render


# ----------------------------------------------------------------------------
# Graph builders (return op lists; single source -> C + preview)
# ----------------------------------------------------------------------------

def cube_cell(atoms):
    """Wireframe cubic cell + atoms. atoms: list of (x,y,r) in pixels."""
    # front square and back square (offset up-right), 100 px side
    fx, fy, s = 80, 200, 100
    ox, oy = 40, -40
    f = [(fx, fy - s), (fx + s, fy - s), (fx + s, fy), (fx, fy)]
    b = [(p[0] + ox, p[1] + oy) for p in f]
    ops = []
    for sq in (f, b):
        for i in range(4):
            ops.append(("line", sq[i][0], sq[i][1], sq[(i + 1) % 4][0],
                        sq[(i + 1) % 4][1], "gr"))
    for i in range(4):
        ops.append(("line", f[i][0], f[i][1], b[i][0], b[i][1], "gr"))
    for (x, y, r) in atoms:
        ops.append(("disc", x, y, r, "lt"))
    return ops


def cfc_cell():
    fx, fy, s, ox, oy = 80, 200, 100, 40, -40
    f = [(fx, fy - s), (fx + s, fy - s), (fx + s, fy), (fx, fy)]
    b = [(p[0] + ox, p[1] + oy) for p in f]
    corners = f + b
    # face centers: front, back, and 4 sides (midpoints of opposite corners)
    def mid(p, q):
        return ((p[0] + q[0]) // 2, (p[1] + q[1]) // 2)
    faces = [mid(f[0], f[2]), mid(b[0], b[2]),
             mid(f[0], b[3]), mid(f[1], b[2]),
             mid(f[0], b[1]), mid(f[3], b[2])]
    atoms = [(x, y, 6) for (x, y) in corners] + [(x, y, 6) for (x, y) in faces]
    return cube_cell(atoms)


def ccc_cell():
    fx, fy, s, ox, oy = 80, 200, 100, 40, -40
    f = [(fx, fy - s), (fx + s, fy - s), (fx + s, fy), (fx, fy)]
    b = [(p[0] + ox, p[1] + oy) for p in f]
    corners = f + b
    center = ((fx + fx + s + ox) // 2, (fy - s + fy + oy) // 2)
    atoms = [(x, y, 6) for (x, y) in corners] + [(center[0], center[1], 7)]
    return cube_cell(atoms)


def stress_strain(curves):
    """curves: list of (points, color). points in pixels."""
    ops = [("axes", 55, 56, 295, 205)]
    ops.append(("text", "sig", 30, 50, "gr"))
    ops.append(("text", "eps", 270, 210, "gr"))
    for pts, col in curves:
        for i in range(len(pts) - 1):
            ops.append(("line", pts[i][0], pts[i][1],
                        pts[i + 1][0], pts[i + 1][1], col))
    return ops


def phase_iso():
    """Isomorfo (tipo Cu-Ni): liquidus + solidus + tie line."""
    ops = [("axes", 55, 56, 295, 205)]
    ops.append(("text", "T", 38, 50, "gr"))
    ops.append(("text", "%B", 270, 210, "gr"))
    # liquidus (top) and solidus (bottom), left=puro A (alto T) -> right
    liq = [(55, 70), (130, 95), (210, 130), (285, 175)]
    sol = [(55, 70), (140, 130), (220, 165), (285, 175)]
    for pts, col in ((liq, "b"), (sol, "r")):
        for i in range(len(pts) - 1):
            ops.append(("line", pts[i][0], pts[i][1],
                        pts[i + 1][0], pts[i + 1][1], col))
    # tie line at T (y=120) between solidus(CL? ) ... mark CL, C0, Ca
    ops.append(("dash", 120, 120, 210, 120, "k"))
    ops.append(("dot", 120, 120, "r"))   # C alpha (solidus)
    ops.append(("dot", 210, 120, "b"))   # C L (liquidus)
    ops.append(("dot", 165, 120, "k"))   # C0
    ops.append(("text", "L", 240, 80, "b"))
    ops.append(("text", "a", 90, 175, "r"))
    ops.append(("text", "a+L", 150, 100, "k"))
    return ops


def phase_eutectic():
    """Eutetico (tipo Pb-Sn): dois liquidus + eutetico."""
    ops = [("axes", 55, 56, 295, 205)]
    ops.append(("text", "T", 38, 50, "gr"))
    ops.append(("text", "%Sn", 262, 210, "gr"))
    # left liquidus down to eutectic, right liquidus up
    eut = (190, 150)
    ops.append(("line", 60, 70, eut[0], eut[1], "b"))
    ops.append(("line", eut[0], eut[1], 285, 95, "b"))
    # eutectic isotherm (horizontal)
    ops.append(("line", 95, 150, 250, 150, "k"))
    ops.append(("dot", eut[0], eut[1], "r"))
    # solvus lines
    ops.append(("line", 60, 150, 95, 150, "r"))
    ops.append(("line", 285, 150, 250, 150, "r"))
    ops.append(("text", "L", 150, 90, "b"))
    ops.append(("text", "a", 80, 175, "r"))
    ops.append(("text", "b", 255, 175, "r"))
    ops.append(("text", "E", 196, 140, "k"))
    return ops


def conc_gradient():
    """Perfil de concentracao linear (difusao estacionaria)."""
    ops = [("axes", 55, 56, 295, 205)]
    ops.append(("text", "C", 38, 50, "gr"))
    ops.append(("text", "x", 270, 210, "gr"))
    ops.append(("line", 70, 80, 250, 170, "b"))   # C cai linearmente
    ops.append(("dash", 70, 80, 70, 205, "gr"))
    ops.append(("dash", 250, 170, 250, 205, "gr"))
    ops.append(("text", "CA", 75, 70, "k"))
    ops.append(("text", "CB", 230, 150, "k"))
    ops.append(("text", "dx", 150, 188, "gr"))
    return ops


def arrhenius_line():
    """lnD vs 1/T (reta de Arrhenius)."""
    ops = [("axes", 55, 56, 295, 205)]
    ops.append(("text", "lnD", 30, 50, "gr"))
    ops.append(("text", "1/T", 264, 210, "gr"))
    ops.append(("line", 75, 80, 260, 185, "b"))
    ops.append(("dot", 110, 100, "r"))
    ops.append(("dot", 220, 162, "r"))
    ops.append(("text", "(1/T1,lnD1)", 110, 86, "k"))
    ops.append(("text", "(1/T2,lnD2)", 150, 168, "k"))
    return ops


def fig621():
    """Fig 6.21 (Callister): curva tensao-deformacao de uma liga de aco."""
    ops = [("axes", 55, 56, 295, 205)]
    ops.append(("text", "sig", 30, 50, "gr"))
    ops.append(("text", "eps", 270, 210, "gr"))
    pts = [(55, 205), (78, 108), (102, 90), (172, 82), (238, 102)]
    for i in range(len(pts) - 1):
        ops.append(("line", pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], "b"))
    ops.append(("dot", 78, 108, "r"))    # limite de proporcionalidade (~400)
    ops.append(("dot", 102, 90, "r"))    # escoamento (550)
    ops.append(("dot", 172, 82, "r"))    # LRT (570)
    ops.append(("text", "E", 60, 150, "k"))
    ops.append(("text", "se", 108, 80, "r"))
    ops.append(("text", "LRT", 175, 68, "r"))
    return ops


GRAPHS = {
    "x_est_1": cfc_cell(),
    "x_est_2": ccc_cell(),
    "x_est_3": cfc_cell(),
    "x_den_1": cfc_cell(),
    "x_dif_1": conc_gradient(),
    "x_dif_2": conc_gradient(),
    "x_arr_2": arrhenius_line(),
    "x_dia_1": phase_eutectic(),
    "x_ala_1": phase_iso(),
    "x_mec_1": stress_strain([
        ([(55, 205), (120, 120), (160, 95), (210, 70), (250, 100)], "b"),
        ([(55, 205), (95, 150), (130, 135), (180, 120), (235, 145)], "r"),
    ]),
    "x_mec_3": stress_strain([
        ([(55, 205), (120, 120), (160, 95), (210, 70), (250, 100)], "b"),
    ]),
    "x_gra_1": stress_strain([
        ([(55, 205), (110, 120), (150, 90), (200, 72), (245, 95)], "b"),
    ]),
    "cal_6_9": fig621(),
    "cal_6_25": fig621(),
    "cal_6_27": fig621(),
}


# ----------------------------------------------------------------------------
# Exercise data
# ----------------------------------------------------------------------------

EXERCISES = [
    # ----- Estruturas Cristalinas -----
    {"id": "x_est_1", "topic": "Estruturas", "title": "Ex 1: Vc do Al (CFC)",
     "statement": [
         "O aluminio tem estrutura CFC com",
         "raio atomico R = 0.143 nm.",
         "Calcule o volume Vc da celula",
         "unitaria.",
     ],
     "solution": [
         "# Relacao a-R na CFC:",
         "a = 2 R raiz(2)",
         "# Converter R p/ metros:",
         "R = 0.143e-9 m",
         "a = 2*0.143e-9*1.414 = 4.045e-10 m",
         "# Volume da celula cubica:",
         "Vc = a^3 = (4.045e-10)^3",
         "= Vc = 6.62e-29 m3",
     ],
     "answer": ["Vc = 6.62e-29 m3"], "final": "Vc = 6.62e-29 m3"},

    {"id": "x_est_2", "topic": "Estruturas", "title": "Ex 2: R do V (CCC)",
     "statement": [
         "O vanadio (CCC) tem densidade",
         "rho = 5.96 g/cm3 e A = 50.9 g/mol.",
         "Determine o raio atomico R.",
     ],
     "solution": [
         "# Da densidade isola-se Vc (n=2):",
         "Vc = n A / (rho Na)",
         "Vc = 2*50.9/(5.96*6.022e23)",
         "= 2.838e-23 cm3",
         "# Aresta e raio (CCC):",
         "a = Vc^(1/3) = 3.05e-8 cm",
         "R = a raiz(3)/4",
         "= R = 1.321e-8 cm = 0.1321 nm",
     ],
     "answer": ["R = 0.1321 nm"], "final": "R = 0.1321 nm"},

    {"id": "x_est_3", "topic": "Estruturas", "title": "Ex 3: FEA da CFC",
     "graph": None,
     "statement": [
         "Mostre que o fator de empacotamento",
         "atomico (FEA) da estrutura CFC e",
         "0.74 (4 atomos por celula).",
     ],
     "solution": [
         "# FEA = Vol. atomos / Vol. celula:",
         "n = 4 atomos; Vat = 4*(4/3)pi R^3",
         "# Celula CFC: a = 2R raiz(2)",
         "Vc = a^3 = 16 raiz(2) R^3",
         "FEA = (16/3)pi R^3 / (16 raiz2 R^3)",
         "FEA = pi/(3 raiz2)",
         "= FEA = 0.74",
     ],
     "answer": ["FEA = 0.74"], "final": "FEA(CFC) = 0.74"},

    # ----- Densidade -----
    {"id": "x_den_1", "topic": "Densidade", "title": "Ex 1: Densidade do Al",
     "statement": [
         "Calcule a densidade teorica do",
         "aluminio (CFC): A = 26.982 g/mol,",
         "R = 0.1431 nm, n = 4.",
     ],
     "solution": [
         "# Formula da densidade:",
         "rho = n A / (Vc Na)",
         "# Vc da CFC (R em cm):",
         "R = 1.431e-8 cm; a = 2R raiz2",
         "Vc = a^3 = 6.62e-23 cm3",
         "# Substituir:",
         "rho = 4*26.982/(6.62e-23*6.022e23)",
         "= rho = 2.70 g/cm3",
     ],
     "answer": ["rho = 2.70 g/cm3"], "final": "rho = 2.70 g/cm3"},

    # ----- Difusao (Fick) -----
    {"id": "x_dif_1", "topic": "Difusao", "title": "Ex 1: H em chapa de Pd",
     "statement": [
         "Hidrogenio difunde numa chapa de",
         "Pd de area 0.20 m2. D = 1.0e-8 m2/s,",
         "dC = 1.8 kg/m3 em dx = 5 mm.",
         "Ache a massa por hora.",
     ],
     "solution": [
         "# 1a Lei de Fick (fluxo):",
         "J = D dC/dx",
         "J = 1.0e-8 * 1.8/0.005",
         "= J = 3.6e-6 kg/(m2 s)",
         "# Massa em 1 h (t=3600 s):",
         "M = J A t = 3.6e-6*0.20*3600",
         "= M = 2.592e-3 kg/h",
     ],
     "answer": ["M = 2.592e-3 kg/h"], "final": "M = 2.59e-3 kg/h"},

    {"id": "x_dif_2", "topic": "Difusao", "title": "Ex 2: Profundidade x",
     "statement": [
         "Difusao de N no aco: D = 1.85e-10",
         "m2/s, fluxo J = 1.0e-7 kg/(m2 s).",
         "C cai de 2.0 a 0.5 kg/m3.",
         "Ache a distancia x (perfil linear).",
     ],
     "solution": [
         "# Da 1a Lei de Fick isola-se x:",
         "J = D (C0 - Cx)/x",
         "x = D (C0 - Cx)/J",
         "x = 1.85e-10*(2.0-0.5)/1.0e-7",
         "x = 1.85e-10*1.5/1.0e-7",
         "= x = 2.775e-3 m = 2.775 mm",
     ],
     "answer": ["x = 2.775 mm"], "final": "x = 2.775 mm"},

    # ----- Arrhenius -----
    {"id": "x_arr_1", "topic": "Arrhenius", "title": "Ex 1: D do C no Cr",
     "graph": None,
     "statement": [
         "Q = 111 kJ/mol. D1 = 6.25e-11 m2/s",
         "a 1400 K. Estime D2 a 1100 K.",
         "(Equacao de Arrhenius)",
     ],
     "solution": [
         "# Razao entre dois D (mesmo D0):",
         "ln(D2/D1) = -Q/R (1/T2 - 1/T1)",
         "Q/R = 111000/8.314 = 13351 K",
         "1/1100 - 1/1400 = 1.948e-4",
         "ln(D2/D1) = -13351*1.948e-4=-2.601",
         "D2 = D1 * e^-2.601",
         "= D2 = 4.6e-12 m2/s",
     ],
     "answer": ["D2 = 4.6e-12 m2/s"], "final": "D2 = 4.6e-12 m2/s"},

    {"id": "x_arr_2", "topic": "Arrhenius", "title": "Ex 2: Q e D0 (Fe em Ni)",
     "statement": [
         "Dois pontos: a 1273 K, D=9.4e-16;",
         "a 1473 K, D=2.4e-14 m2/s.",
         "Ache Q e D0 (reta lnD vs 1/T).",
     ],
     "solution": [
         "# Inclinacao da reta lnD vs 1/T:",
         "Q = -R (lnD1 - lnD2)/(1/T1 - 1/T2)",
         "lnD1-lnD2 = ln(9.4e-16/2.4e-14)",
         "= -3.24; 1/1273-1/1473=1.067e-4",
         "Q = -8.314*(-3.24)/1.067e-4",
         "= Q = 252550 J/mol",
         "# D0 pela equacao original:",
         "= D0 = 2.17e-5 m2/s",
     ],
     "answer": ["Q = 252.5 kJ/mol", "D0 = 2.17e-5 m2/s"],
     "final": "Q=252.5 kJ/mol; D0=2.17e-5"},

    # ----- Diagramas de fase -----
    {"id": "x_dia_1", "topic": "Diagramas", "title": "Ex 1: Eutetico Pb-Sn",
     "statement": [
         "No sistema Pb-Sn, identifique o",
         "ponto eutetico (T e composicao) e",
         "a reacao que ocorre nele.",
     ],
     "solution": [
         "# No eutetico o liquido se transforma",
         "em dois solidos ao mesmo tempo:",
         "L -> alpha + beta (resfriando)",
         "# Leitura do diagrama Pb-Sn:",
         "temperatura eutetica = 183 C",
         "= composicao = 61.9 wt% Sn",
     ],
     "answer": ["T = 183 C; 61.9 wt% Sn", "L -> alpha + beta"],
     "final": "Eutetico: 183 C; 61.9% Sn"},

    # ----- Regra da alavanca -----
    {"id": "x_ala_1", "topic": "Alavanca", "title": "Ex 1: Alavanca Cu-Ni",
     "statement": [
         "Liga Cu-Ni com C0 = 35 wt% Ni numa",
         "regiao alpha+L. A linha de amarracao",
         "da CL = 32 e Calpha = 43 wt% Ni.",
         "Ache as fracoes de L e de alpha.",
     ],
     "solution": [
         "# Regra da alavanca (fracao de L):",
         "wL = (Calpha - C0)/(Calpha - CL)",
         "wL = (43 - 35)/(43 - 32)",
         "= wL = 8/11 = 0.727 (72.7%)",
         "# Fracao de solido alpha:",
         "wa = (C0 - CL)/(Calpha - CL)",
         "wa = (35 - 32)/11",
         "= wa = 0.273 (27.3%)",
     ],
     "answer": ["wL = 72.7%; w(alpha) = 27.3%"],
     "final": "wL=72.7%; wa=27.3%"},

    # ----- Propriedades mecanicas -----
    {"id": "x_mec_1", "topic": "Mecanicas", "title": "Ex 1: Modulo E (A e B)",
     "statement": [
         "Curvas tensao-deformacao:",
         "Mat A: 240 MPa a eps = 0.004.",
         "Mat B: 120 MPa a eps = 0.0006.",
         "Compare o modulo de elasticidade E.",
     ],
     "solution": [
         "# E = inclinacao da reta elastica:",
         "E = sigma / epsilon",
         "# Material A:",
         "E_A = 240/0.004 = 60000 MPa = 60 GPa",
         "# Material B:",
         "E_B = 120/0.0006 = 200000 = 200 GPa",
         "= B e mais rigido (maior E)",
     ],
     "answer": ["E_A = 60 GPa; E_B = 200 GPa", "B e mais rigido"],
     "final": "E_A=60; E_B=200 GPa"},

    {"id": "x_mec_2", "topic": "Mecanicas", "title": "Ex 2: Ductilidade %AL",
     "graph": None,
     "statement": [
         "Corpo de prova L0 = 50.8 mm.",
         "Mat A rompe com Lf = 59.182 mm;",
         "Mat B com Lf = 55.88 mm.",
         "Calcule o alongamento percentual.",
     ],
     "solution": [
         "# Ductilidade (% alongamento):",
         "%AL = (Lf - L0)/L0 * 100",
         "# Material A:",
         "%AL = (59.182-50.8)/50.8*100",
         "= 16.5 %",
         "# Material B:",
         "%AL = (55.88-50.8)/50.8*100 = 10 %",
         "= A e mais ductil",
     ],
     "answer": ["A = 16.5%; B = 10%", "A e mais ductil"],
     "final": "A=16.5%; B=10% (A ductil)"},

    {"id": "x_mec_3", "topic": "Mecanicas", "title": "Ex 3: Resiliencia Ur",
     "statement": [
         "Mat A: sigma_e = 280 MPa, E = 60 GPa.",
         "Mat B: sigma_e = 275 MPa, E = 200 GPa.",
         "Calcule e compare a resiliencia Ur.",
     ],
     "solution": [
         "# Resiliencia (area elastica):",
         "Ur = sigma_e^2 / (2 E)",
         "# Material A (E=60000 MPa):",
         "Ur = 280^2/(2*60000) = 0.653 MJ/m3",
         "# Material B (E=200000 MPa):",
         "Ur = 275^2/(2*200000) = 0.189 MJ/m3",
         "= A tem maior resiliencia",
     ],
     "answer": ["Ur(A) = 0.653 MJ/m3", "Ur(B) = 0.189 MJ/m3"],
     "final": "Ur: A=0.653; B=0.189 MJ/m3"},

    # ----- Graficos (leitura) -----
    {"id": "x_gra_1", "topic": "Graficos", "title": "Ex 1: Leitura do grafico",
     "statement": [
         "Do grafico tensao-deformacao de um",
         "aco, extraia: modulo E, limite de",
         "proporcionalidade, tensao de",
         "escoamento (0.2%) e o limite (LRT).",
     ],
     "solution": [
         "# Como ler cada parametro:",
         "E = inclinacao da reta inicial",
         "lim. prop. = fim da reta = 400 MPa",
         "# Escoamento: reta a 0.2% (0.002):",
         "sigma_e ~ 550 MPa",
         "# LRT = pico da curva:",
         "= E=250 GPa; sig_e=550; LRT=570 MPa",
     ],
     "answer": ["E = 250 GPa; sigma_e = 550 MPa", "LRT = 570 MPa"],
     "final": "E=250 GPa; se=550; LRT=570"},

    # ----- Lista Callister (Cap. 6) -----
    {"id": "cal_6_3", "topic": "Callister", "title": "6.3: Deformacao do Al",
     "graph": None,
     "statement": [
         "Corpo de prova de aluminio, secao",
         "reta retangular 10 x 12.7 mm, em",
         "tracao com F = 35500 N (so",
         "elastica). Calcule a deformacao.",
     ],
     "solution": [
         "# Tensao: sigma = F/A",
         "A = 10 x 12.7 = 127 mm2",
         "sigma = 35500/127 = 279.5 MPa",
         "# Deformacao (E_Al = 69 GPa):",
         "epsilon = sigma/E = 279.5/69000",
         "= epsilon = 0.0041",
     ],
     "answer": ["epsilon = 0.0041"], "final": "epsilon = 0.0041"},

    {"id": "cal_6_4", "topic": "Callister", "title": "6.4: Comprimento L0 (Ti)",
     "graph": None,
     "statement": [
         "Liga de titanio, E = 107 GPa,",
         "diametro d = 3.8 mm, tracao",
         "F = 2000 N (so elastica), com",
         "alongamento maximo dl = 0.42 mm.",
         "Ache o comprimento inicial L0.",
     ],
     "solution": [
         "# Tensao: sigma = F/A",
         "A = pi (1.9)^2 = 11.34 mm2",
         "sigma = 2000/11.34 = 176.4 MPa",
         "# Deformacao elastica:",
         "eps = sigma/E = 176.4/107000",
         "= 1.649e-3",
         "# Comprimento: L0 = dl/eps",
         "L0 = 0.42/1.649e-3 = 254.7 mm",
         "= L0 ~ 250 mm (Callister)",
     ],
     "answer": ["L0 = 250 mm"], "final": "L0 = 250 mm"},

    {"id": "cal_6_9", "topic": "Callister", "title": "6.9: Alongamento (aco)",
     "statement": [
         "Liga de aco (curva tensao-deformacao",
         "da Fig.), diametro d = 8.5 mm,",
         "L0 = 75 mm, em tracao com",
         "F = 23500 N. Ache o alongamento dl.",
     ],
     "solution": [
         "# Tensao aplicada: sigma = F/A",
         "A = pi (4.25)^2 = 56.7 mm2",
         "sigma = 23500/56.7 = 414 MPa",
         "# Regiao elastica: ler eps na Fig.",
         "eps ~ 0.0013",
         "# Alongamento: dl = eps * L0",
         "dl = 0.0013 * 75",
         "= dl = 0.10 mm",
     ],
     "answer": ["dl = 0.10 mm"], "final": "dl = 0.10 mm"},

    {"id": "cal_6_25", "topic": "Callister", "title": "6.25: Ler a Fig. (aco)",
     "statement": [
         "A Fig. mostra a curva tensao-",
         "deformacao de uma liga de aco.",
         "Determine: (a) E; (b) limite de",
         "proporcionalidade; (c) escoamento a",
         "0.2%; (d) limite de resistencia LRT.",
     ],
     "solution": [
         "# (a) E = inclinacao da reta inicial",
         "= E = 250 GPa",
         "# (b) fim da reta (lim. prop.):",
         "= 400 MPa",
         "# (c) escoamento (offset de 0.2%):",
         "= sigma_e = 550 MPa",
         "# (d) pico da curva (LRT):",
         "= LRT = 570 MPa",
     ],
     "answer": ["E=250 GPa; lim.prop.=400 MPa", "sigma_e=550 MPa; LRT=570 MPa"],
     "final": "E=250G; se=550; LRT=570 MPa"},

    {"id": "cal_6_27", "topic": "Callister", "title": "6.27: Elastica ou plastica",
     "statement": [
         "Carga F = 44500 N num corpo de prova",
         "cilindrico de aco (Fig.), diametro",
         "d = 10 mm. (a) deformacao elastica ou",
         "plastica? (b) com L0 = 500 mm, ache",
         "o alongamento dl.",
     ],
     "solution": [
         "# Tensao: sigma = F/A",
         "A = pi (5)^2 = 78.54 mm2",
         "sigma = 44500/78.54 = 567 MPa",
         "# (a) 567 > escoamento (550 MPa):",
         "= deformacao PLASTICA",
         "# (b) ler eps na Fig.: eps ~ 0.008",
         "dl = eps * L0 = 0.008 * 500",
         "= dl = 4 mm",
     ],
     "answer": ["(a) plastica (sigma > sigma_e)", "(b) dl = 4 mm"],
     "final": "plastica; dl = 4 mm"},

    {"id": "cal_6_31", "topic": "Callister", "title": "6.31: Ductilidade",
     "graph": None,
     "statement": [
         "Corpo de prova cilindrico: d0 = 12.8",
         "mm, L0 = 50.80 mm. Na fratura:",
         "df = 6.60 mm e Lf = 72.14 mm.",
         "Calcule a ductilidade: %RA e %AL.",
     ],
     "solution": [
         "# Reducao percentual de area (%RA):",
         "%RA = (d0^2 - df^2)/d0^2 * 100",
         "= (12.8^2 - 6.60^2)/12.8^2 * 100",
         "= %RA = 73.4 %",
         "# Alongamento percentual (%AL):",
         "%AL = (Lf - L0)/L0 * 100",
         "= (72.14-50.80)/50.80 * 100",
         "= %AL = 42 %",
     ],
     "answer": ["%RA = 73.4%; %AL = 42%"], "final": "%RA=73.4%; %AL=42%"},
]


TOPIC_ORDER = ["Estruturas", "Densidade", "Difusao", "Arrhenius",
               "Diagramas", "Alavanca", "Mecanicas", "Graficos", "Callister"]


# ----------------------------------------------------------------------------
# Theory (Teoria group)
# ----------------------------------------------------------------------------

TEORIA = [
    {"topic": "Estruturas", "title": "Estruturas cristalinas", "pages": [
        ("Celulas unitarias", "CFC, CCC, HC", [
            "# Relacao aresta a - raio R:",
            "CFC: a = 2 R raiz(2)",
            "CCC: a = 4 R / raiz(3)",
            "HC:  a = 2 R (plano basal)",
            "# Atomos por celula (n):",
            "CFC n=4; CCC n=2",
            "# Fator de empacotamento (FEA):",
            "CFC 0.74; CCC 0.68; HC 0.74",
        ]),
    ]},
    {"topic": "Densidade", "title": "Densidade teorica", "pages": [
        ("Massa especifica", "rho", [
            "# Densidade teorica:",
            "rho = n A / (Vc Na)",
            "n = atomos/celula; A = massa molar",
            "Vc = a^3 ; Na = 6.022e23",
            "# Unidades:",
            "1 nm = 1e-7 cm (p/ g/cm3)",
            "use A em g/mol e R em cm",
        ]),
    ]},
    {"topic": "Difusao", "title": "Difusao (Fick)", "pages": [
        ("1a Lei de Fick", "regime estacionario", [
            "# Fluxo de difusao:",
            "J = D (CA - CB)/dx",
            "# Massa que atravessa:",
            "M = J A t   (t em segundos)",
            "1 h = 3600 s",
            "# Profundidade (perfil linear):",
            "x = D (C0 - Cx)/J",
        ]),
    ]},
    {"topic": "Arrhenius", "title": "Difusao x temperatura", "pages": [
        ("Equacao de Arrhenius", "D(T)", [
            "# Coeficiente de difusao:",
            "D = D0 exp(-Q/(R T))",
            "R = 8.314 J/(mol K); T em Kelvin",
            "T(K) = T(C) + 273",
            "# Dois pontos (D1,T1),(D2,T2):",
            "Q = -R (lnD1-lnD2)/(1/T1-1/T2)",
            "se Q vier em kJ, x1000 -> J",
        ]),
    ]},
    {"topic": "Diagramas", "title": "Diagramas de fase", "pages": [
        ("Linhas e fases", "liquidus/solidus", [
            "# Definicoes:",
            "liquidus: acima so liquido L",
            "solidus: abaixo so solido alpha",
            "# Eutetico:",
            "L -> alpha + beta (ponto fixo)",
            "Pb-Sn: 183 C e 61.9 wt% Sn",
        ]),
    ]},
    {"topic": "Alavanca", "title": "Regra da alavanca", "pages": [
        ("Fracoes de fase", "lever rule", [
            "# Na regiao bifasica alpha + L:",
            "wL = (Ca - C0)/(Ca - CL)",
            "w(alpha) = (C0 - CL)/(Ca - CL)",
            "# C0 = composicao da liga",
            "CL = liquidus; Ca = solidus",
            "soma das fracoes = 1",
        ]),
    ]},
    {"topic": "Mecanicas", "title": "Propriedades mecanicas", "pages": [
        ("Tensao-deformacao", "parametros", [
            "# Modulo de elasticidade:",
            "E = sigma / epsilon (reta inicial)",
            "# Tensao de escoamento sigma_e:",
            "inicio da deformacao permanente",
            "LRT = pico da curva (resistencia)",
            "# Ductilidade e resiliencia:",
            "%AL = (Lf-L0)/L0 *100",
            "Ur = sigma_e^2/(2 E)",
        ]),
    ]},
]


# ----------------------------------------------------------------------------
# Page building
# ----------------------------------------------------------------------------

TEXT_X = 14
TEXT_YS = [62, 82, 102, 122, 142, 162, 182]
MAX_TEXT_LINES = len(TEXT_YS)
COLOR_NAME = {"k": "COL_BLACK", "b": "COL_BLUE", "r": "COL_RED", "gr": "COL_GRAY"}


def c_string(value):
    encoded = value.encode("ascii", "strict").decode("ascii")
    return '"' + encoded.replace("\\", "\\\\").replace('"', '\\"') + '"'


def wrap_text(line, width=37):
    if len(line) <= width:
        return [line]
    words = line.split()
    out, cur = [], ""
    for w in words:
        cand = w if not cur else cur + " " + w
        if len(cand) <= width:
            cur = cand
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out or [""]


def parse_markup(line):
    if line.startswith("# "):
        return line[2:], "b"
    if line.startswith("= "):
        return line[2:], "r"
    return line, "k"


def to_items(raw_lines):
    items = []
    for raw in raw_lines:
        text, color = parse_markup(raw)
        for sub in wrap_text(text):
            items.append((sub, color))
    return items


def safe_id(text):
    return "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def build_pages(ex):
    pages = []

    # Enunciado
    st = to_items(ex["statement"])
    chunks = [st[i:i + MAX_TEXT_LINES] for i in range(0, len(st), MAX_TEXT_LINES)] or [[]]
    for idx, chunk in enumerate(chunks):
        sub = "" if len(chunks) == 1 else "parte %d/%d" % (idx + 1, len(chunks))
        pages.append({"title": "Enunciado", "subtitle": sub, "items": chunk})

    # Grafico (if a graph exists for this id and not explicitly None)
    if ex.get("graph", "auto") is not None and ex["id"] in GRAPHS:
        pages.append({"title": "Grafico", "subtitle": "", "items": [],
                      "body_name": "draw_%s" % ex["id"]})

    # Resolucao
    sol = to_items(ex["solution"])
    chunks = [sol[i:i + MAX_TEXT_LINES] for i in range(0, len(sol), MAX_TEXT_LINES)] or [[]]
    for idx, chunk in enumerate(chunks):
        sub = "passo a passo" if len(chunks) == 1 else "parte %d/%d" % (idx + 1, len(chunks))
        pages.append({"title": "Resolucao", "subtitle": sub, "items": chunk})

    # Resultado
    res = [("Resposta final:", "b")]
    for a in ex["answer"]:
        for sub in wrap_text(a):
            res.append((sub, "r"))
    final = ex.get("final") or ex["answer"][0]
    if len(final) > 36:
        final = "Resposta conferida"
    pages.append({"title": "Resultado", "subtitle": "Final", "items": res,
                  "result": final})
    return pages


def page_lines_xy(page):
    out = []
    for i, (text, color) in enumerate(page.get("items", [])):
        if i >= MAX_TEXT_LINES:
            break
        out.append((text, TEXT_X, TEXT_YS[i], color))
    return out


def result_y_for(n):
    last = TEXT_YS[min(n, MAX_TEXT_LINES) - 1] if n else TEXT_YS[0]
    y = last + 22
    return min(y, 188)


# ----------------------------------------------------------------------------
# C generation
# ----------------------------------------------------------------------------

def text_array_c(name, lines_xy):
    out = ["static const TextLine %s[] = {" % name]
    if not lines_xy:
        out.append('    { "", %d, %d, COL_BLACK },' % (TEXT_X, TEXT_YS[0]))
    for (text, x, y, color) in lines_xy:
        out.append("    { %s, %d, %d, %s }," % (c_string(text), x, y, COLOR_NAME[color]))
    out.append("};")
    return "\n".join(out)


def exercise_c(ex):
    sid = ex["id"]
    pages = build_pages(ex)
    parts = []
    entries = []
    for pidx, page in enumerate(pages):
        lines_xy = page_lines_xy(page)
        arr = "%s_pg%d" % (sid, pidx)
        parts.append(text_array_c(arr, lines_xy))
        body = page.get("body_name") or "0"
        if page.get("result"):
            result = c_string(page["result"])
            ry = result_y_for(len(lines_xy))
        else:
            result, ry = "0", 0
        entries.append("    { %s, %s,\n      %s, COUNT(%s), %s, %d, %s }"
                       % (c_string(page["title"]), c_string(page.get("subtitle", "")),
                          arr, arr, result, ry, body))
    parts.append("static const Page %s_pages[] = {\n%s\n};" % (sid, ",\n".join(entries)))
    return "\n\n".join(parts)


def teoria_pages_c(topic_id, pages):
    parts = []
    entries = []
    for pidx, (title, sub, raw) in enumerate(pages):
        items = to_items(raw)
        lines_xy = []
        for i, (text, color) in enumerate(items[:MAX_TEXT_LINES]):
            lines_xy.append((text, TEXT_X, TEXT_YS[i], color))
        arr = "%s_pg%d" % (topic_id, pidx)
        parts.append(text_array_c(arr, lines_xy))
        entries.append("    { %s, %s,\n      %s, COUNT(%s), 0, 0, 0 }"
                       % (c_string(title), c_string(sub), arr, arr))
    parts.append("static const Page %s_pages[] = {\n%s\n};" % (topic_id, ",\n".join(entries)))
    return "\n\n".join(parts)


def generate_exercicios_c():
    out = ['#include "app.h"', "",
           "/* Generated by tools/gen_icm.py. Do not edit by hand. */", "",
           "#define COUNT(a) ((uint8_t)(sizeof(a) / sizeof((a)[0])))", ""]
    # graph body functions
    for ex in EXERCISES:
        if ex.get("graph", "auto") is not None and ex["id"] in GRAPHS:
            out.append(icm_render.emit_body_c("draw_%s" % ex["id"], GRAPHS[ex["id"]]))
            out.append("")
    # exercises
    for ex in EXERCISES:
        out.append(exercise_c(ex))
        out.append("")
    # exercise arrays per topic
    for topic in TOPIC_ORDER:
        items = [ex for ex in EXERCISES if ex["topic"] == topic]
        arr = "exs_%s" % safe_id(topic)
        out.append("static const Exercise %s[] = {" % arr)
        for ex in items:
            out.append("    { %s, %s_pages, COUNT(%s_pages) },"
                       % (c_string(ex["title"]), ex["id"], ex["id"]))
        out.append("};")
        out.append("")
    out.append("static const Topic exerc_topics[] = {")
    for topic in TOPIC_ORDER:
        arr = "exs_%s" % safe_id(topic)
        out.append("    { %s, %s, COUNT(%s) }," % (c_string(topic), arr, arr))
    out.append("};")
    out.append("")
    out.append("const Group exerc_group = { \"Exercicios\", exerc_topics, COUNT(exerc_topics) };")
    out.append("")
    return "\n".join(out)


def generate_teoria_c():
    out = ['#include "app.h"', "",
           "/* Generated by tools/gen_icm.py. Do not edit by hand. */", "",
           "#define COUNT(a) ((uint8_t)(sizeof(a) / sizeof((a)[0])))", ""]
    for t in TEORIA:
        tid = "teo_%s" % safe_id(t["topic"])
        out.append(teoria_pages_c(tid, t["pages"]))
        out.append("")
    # one exercise (the theory) per topic
    for t in TEORIA:
        tid = "teo_%s" % safe_id(t["topic"])
        out.append("static const Exercise %s_ex[] = {" % tid)
        out.append("    { %s, %s_pages, COUNT(%s_pages) }," % (c_string(t["title"]), tid, tid))
        out.append("};")
        out.append("")
    out.append("static const Topic teoria_topics[] = {")
    for t in TEORIA:
        tid = "teo_%s" % safe_id(t["topic"])
        out.append("    { %s, %s_ex, COUNT(%s_ex) }," % (c_string(t["topic"]), tid, tid))
    out.append("};")
    out.append("")
    out.append("const Group teoria_group = { \"Teoria\", teoria_topics, COUNT(teoria_topics) };")
    out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------------
# Preview
# ----------------------------------------------------------------------------

def render_previews(out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    count = 0
    for ex in EXERCISES:
        pages = build_pages(ex)
        total = len(pages)
        items = [e for e in EXERCISES if e["topic"] == ex["topic"]]
        ex_no = items.index(ex) + 1
        for pidx, page in enumerate(pages):
            lines_xy = page_lines_xy(page)
            view = {"title": page["title"], "subtitle": page.get("subtitle", ""),
                    "lines": lines_xy, "body": None}
            if page.get("body_name"):
                sid = page["body_name"][len("draw_"):]
                view["body"] = GRAPHS.get(sid)
            if page.get("result"):
                view["result"] = page["result"]
                view["result_y"] = result_y_for(len(lines_xy))
            meta = "Ex %02d Pg %d/%d" % (ex_no, pidx + 1, total)
            img = icm_render.render_page(view, topic=ex["topic"], ex_meta=meta,
                                         ex_title=ex["title"])
            img.save(out / ("%s_p%d.png" % (ex["id"], pidx)))
            count += 1
    print("rendered %d page previews to %s" % (count, out))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", metavar="DIR", default=None)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    (root / "src" / "catalog_exercicios.c").write_text(generate_exercicios_c(), encoding="ascii")
    (root / "src" / "catalog_teoria.c").write_text(generate_teoria_c(), encoding="ascii")
    print("generated %d exercises, %d teoria topics" % (len(EXERCISES), len(TEORIA)))

    if args.preview:
        render_previews(args.preview)


if __name__ == "__main__":
    main()
