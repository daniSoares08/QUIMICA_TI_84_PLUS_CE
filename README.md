# AICM - Introducao a Ciencia dos Materiais (TI-84 Plus CE)

App de teoria e exercicios resolvidos de ICM (nome do programa na calculadora:
**AICM**), construido como o CircuitViewer3: menus fixos, paginas curtas e
graficos/desenhos feitos com primitivas `graphx` (sem imagens do PDF no `.8xp`).

## Navegacao

- Menu principal: `1. Teoria` / `2. Exercicios` (UP/DOWN, ENTER; ou teclas 1/2).
- No bloco: `UP/DOWN` muda o exercicio; `</>` (LEFT/RIGHT) muda a pagina.
- `CLEAR` volta; `ON` sai.

Cada exercicio segue: **Enunciado -> Grafico (quando ha) -> Resolucao
(passo a passo) -> Resultado** (caixa com a resposta).

## Conteudo

Topicos (Exercicios): Estruturas, Densidade, Difusao, Arrhenius, Diagramas,
Alavanca (regra da alavanca), Mecanicas, Graficos e Callister (lista do Cap. 6
de Propriedades Mecanicas: 6.3, 6.4, 6.9, 6.25, 6.27, 6.31). Cada exercicio tem enunciado,
resolucao passo a passo (formula -> valores -> resposta com unidade) e, quando
o assunto pede, um grafico desenhado:

- celula CFC / CCC (estruturas cristalinas e densidade),
- perfil de concentracao (difusao, 1a Lei de Fick),
- reta de Arrhenius (lnD x 1/T),
- diagrama de fases isomorfo (Cu-Ni) com linha de amarracao,
- diagrama eutetico (Pb-Sn),
- curvas tensao-deformacao (propriedades mecanicas).

Teoria: um resumo de formulas por topico (extraido do guia pratico).

## Estrutura do codigo

- `src/main.c`: navegacao (Topico -> Exercicio -> Pagina).
- `src/ui.c`: tela, menus e primitivas de desenho (`g_line`, `g_dash`,
  `g_dot`, `g_circ`, `g_disc`, `g_text`, `g_axes`).
- `src/app.h`: tipos (`TextLine`, `Page`, `Exercise`, `Topic`, `Group`).
- `src/catalog_exercicios.c` e `src/catalog_teoria.c`: **GERADOS** por
  `tools/gen_icm.py`. Nao editar a mao.
- `tools/gen_icm.py`: dados (enunciado, grafico como lista de "ops", resolucao)
  + geracao do C.
- `tools/icm_render.py`: espelha `ui.c`; renderiza cada pagina em PNG 320x240
  (`--preview DIR`) para conferir layout sem a calculadora.
- `tools/audit_strings.py`: confere ASCII e strings <= 39 chars.

## Fluxo para alterar/adicionar exercicios

```bash
# 1) editar tools/gen_icm.py (EXERCISES / GRAPHS / TEORIA)
# 2) gerar os catalogos C + previews PNG
python tools/gen_icm.py --preview /tmp/icm_preview
# 3) compilar (CEdev em C:\CEdev)
export PATH="/c/CEdev/bin:$PATH"
/c/CEdev/bin/make.exe clean && /c/CEdev/bin/make.exe
```

Saida: `bin/AICM.8xp` (sem AppVars `.8xv`). Confira os PNGs do preview antes de
mandar para a calculadora: nada deve sair da tela, cobrir texto ou se sobrepor.
ASCII puro (sem acentos), strings C <= 39 chars. Respostas conferidas a mao.
