# Guia de bolso — CEdev (TI-84 Plus CE)

## Construindo apps confiáveis com `graphx` + `keypadc`

Este documento resume o que fazer e o que evitar ao criar programas em C para a TI-84 Plus CE usando CEdev. É baseado nas lições aprendidas: tela preta com "riscos", teclas que não respondiam, ON que não saía, e erros de memória.

---

## 0) Filosofia geral

* **Comece simples**: apenas `graphx` e `keypadc`.
* **Fundo branco + texto preto**, 8×8 (40 colunas × 30 linhas de texto).
* **ASCII puro** (nada de UTF-8: `xbar`, `ybar`, `Sum`, etc.).
* **Teclado “padrão”**: `kb_DisableOnLatch()` ao iniciar, `kb_Scan()` em todo loop, e **ON sai do app** sempre.
* **Double buffer corretamente inicializado** + limpeza dos **dois buffers**.
* **Memória**: evite `printf/sprintf` e `pow()` quando puder; use constantes menores.

---

## 1) Estrutura de projeto

```
project/
├─ src/
│  ├─ app.h          // tipos, constantes e protótipos compartilhados
│  ├─ main.c         // navegação, loops e roteamento de telas
│  ├─ ui.c           // inicialização, teclado, desenho comum
│  ├─ formulas.c     // catálogo opcional de fórmulas/telas fixas
│  └─ catalog_*.c    // conteúdos por assunto, lote ou módulo
├─ tools/
│  ├─ audit_strings.py
│  ├─ render_pdf.py
│  └─ preview/render helpers opcionais
└─ Makefile
```

Para protótipos mínimos, `src/main.c` sozinho funciona. Quando o app passa de
algumas telas, divida cedo: a navegação fica em `main.c`, os componentes
visuais em `ui.c`, os tipos em um `.h`, e os catálogos em arquivos separados.
Isso evita arquivos gigantes, facilita revisão e permite gerar catálogos por
script sem tocar no loop principal.

### Makefile mínimo (recomendado)

```make
NAME = MEUAPP
DESCRIPTION = "App CEdev"
COMPRESSED = YES
ARCHIVED = YES

SRC = src/main.c src/ui.c src/formulas.c src/catalog.c

CFLAGS = -Wall -Wextra -Oz
LDFLAGS = -lgraphx -lkeypadc -lm

include $(shell cedev-config --makefile)
```

* **COMPRESSED=YES** e **ARCHIVED=YES** ajudam a caber na RAM.
* Só as libs necessárias: `graphx` (tela), `keypadc` (teclado), `m` (math).
* Declare no `.h` apenas o que outros arquivos precisam usar; deixe helpers
  internos como `static` dentro do `.c`.
* Para dados grandes ou gerados, prefira vários catálogos pequenos
  (`catalog_cap01.c`, `catalog_provas.c`) e liste todos no `SRC`.

---

## 2) Inicialização de vídeo correta

**Regra de ouro**: nunca chamar `gfx_SwapDraw()` antes de **habilitar o draw buffer** e **limpar ambos os buffers**.

```c
gfx_Begin();
gfx_SetDrawBuffer();      // habilita duplo buffer

// limpa os DOIS buffers e volta ao draw buffer
gfx_FillScreen(255); gfx_SwapDraw();
gfx_FillScreen(255); gfx_SwapDraw();
gfx_SetDrawBuffer();
gfx_FillScreen(255);

gfx_SetTextFGColor(0);    // texto preto
gfx_SetTextScale(1,1);
```

Se você ver “riscos” ou lixo na tela, é quase sempre falta dessa sequência.

---

## 3) Saída imediata com ON (sempre)

* ON **não** vem na matriz `kb_Data[]`; leia com `kb_On`.
* Desative o *latch* no início (evita que a ON fique “presa” de uso anterior).

```c
#include <keypadc.h>

int main(void) {
  kb_DisableOnLatch();
  kb_Scan(); // primeira varredura

  gfx_Begin(); /* ... */

  for(;;){
    // loop principal
    kb_Scan();
    if (kb_On) { gfx_End(); return 0; } // sai sempre
  }
}
```

**Dica**: encapsule num helper e chame em todos os loops/bloqueios:

```c
static inline void check_on_exit(void){
    kb_Scan();
    if (kb_On){ gfx_End(); exit(0); }
}
```

---

## 4) Leitura de teclas “do jeito certo”

Prefira as **teclas longas** (`kb_KeyX`) com `kb_IsDown()` e implemente **detecção de borda** (press-once) para evitar repetição involuntária.

```c
// "Press once" para uma kb_Key específica
static uint8_t pressed_once(kb_lkey_t key){
    static uint8_t prev[256]; // simples e suficiente
    uint8_t down = kb_IsDown(key) ? 1 : 0;
    uint8_t edge = (down && !prev[key]);
    prev[key] = down;
    return edge;
}

// Exemplo de menu:
for(;;){
  check_on_exit(); kb_Scan();
  if (pressed_once(kb_Key1)) { /* opção 1 */ }
  if (pressed_once(kb_Key2)) { /* opção 2 */ }
  if (pressed_once(kb_Key0)) { /* voltar */   }
}
```

**Não** confie em mapear grupos/bits manualmente (ex.: `kb_Data[7] & ...`) a não ser que você saiba exatamente o que está fazendo — foi por isso que só “2” e “3” funcionavam.

---

## 5) Texto e layout (40 colunas × 30 linhas)

A fonte default do `graphx` é 8×8. Adote 40 colunas (320 px / 8) e crie um **print truncado**:

```c
#define COLS 40

static void prnXY(const char *s, int x, int y){
    char buf[COLS+1]; int i=0;
    while (s[i] && i<COLS) buf[i]=s[i], i++;
    buf[i]='\0';
    gfx_PrintStringXY(buf, x, y);
}
static void prn(int y, const char *s){ prnXY(s, 2, y); }
```

* **ASCII puro**: nada de `Σ`, `x̄`, `°` (UTF-8 vira lixo). Use `Sum`, `xbar`, `deg`, etc.
* Padrão visual fixo: **fundo branco**, **texto preto**.

---

## 6) Entrada numérica robusta (um valor por vez)

Evite `os_GetCSC`. Use uma **caixa de entrada** com teclado numérico (`0..9`, `.` e `-`), `ENTER` para confirmar e `CLEAR` para apagar:

```c
static void input_line(char *buf, int maxlen, const char *prompt){
    int idx=0; buf[0]='\0';
    for(;;){
        check_on_exit(); kb_Scan();

        gfx_FillScreen(255); gfx_SetTextFGColor(0);
        prn(2, prompt);
        prnXY(buf, 2, 18);
        prn(78, "ENTER=ok  CLEAR=apaga  ON=sair");
        gfx_SwapDraw();

        if (pressed_once(kb_KeyEnter)) { buf[idx]='\0'; return; }
        if (pressed_once(kb_KeyClear)) { if (idx>0){ idx--; buf[idx]='\0'; } }

        // dígitos e pontuação
        if (pressed_once(kb_Key0) && idx<maxlen-1) buf[idx++]='0';
        /* ... 1..9 ... */
        if (pressed_once(kb_KeyDecPnt) && idx<maxlen-1) buf[idx++]='.';
        if (pressed_once(kb_KeyChs)    && idx<maxlen-1) buf[idx++]='-';
        buf[idx] = '\0';

        delay(10);
    }
}
```

Depois, **parse** para `int`/`double` (ou escreva um parser leve para `float` se quiser economizar memória).

---

## 7) Arquitetura de telas

Para apps simples, siga um **fluxo fixo**:

1. **Tela de construção** dos dados (perguntas **um valor por vez**).
2. **Menu principal** com opções numeradas (1..4, 0=voltar).
3. Telas de **relatório passo a passo** (centróide, inércia…).

Estruture como funções:

```c
static void tela_construir(void);
static void tela_menu(void);
static void tela_centroide_passoapasso(void);
static void tela_inercia_passoapasso(void);

int main(void){
  /* init */
  for(;;){
     tela_construir();
     tela_menu();
  }
}
```

Para apps com muito conteúdo, use navegação **orientada por dados**. O loop de
tela fica genérico, e os catálogos só preenchem arrays:

```c
typedef void (*body_draw_fn)(void);

typedef struct {
    const char *text;
    int x, y;
    uint8_t color;
} TextLine;

typedef struct {
    const char *title;
    const char *subtitle;
    const TextLine *lines;
    uint8_t line_count;
    const char *result;
    uint8_t result_y;
    body_draw_fn body;
} PageTemplate;

typedef struct {
    const char *title;
    const PageTemplate *pages;
    uint8_t page_count;
} ScreenItem;

typedef struct {
    const char *title;
    const ScreenItem *items;
    uint8_t count;
    const ScreenItem *extra_items;
    uint8_t extra_count;
} ScreenGroup;

typedef struct {
    const char *title;
    uint8_t kind;
    uint8_t index;
} MenuItem;
```

Padrão recomendado:

* `MenuItem` é o menu principal: cada item aponta para um tipo (`MENU_GROUP`,
  `MENU_FORMULA`, `MENU_TOOL`, etc.) e um índice.
* `ScreenGroup` é o submenu: uma lista de itens do mesmo assunto, capítulo ou
  ferramenta.
* `ScreenItem` é uma entrada final: contém uma ou mais páginas.
* `PageTemplate` descreve uma página: título, subtítulo, linhas de texto,
  resultado opcional e uma função `body` para desenho ou gráfico.
* `extra_items/extra_count` é útil quando um assunto tem um catálogo principal
  e um catálogo complementar sem duplicar o loop.

O loop de submenu deve ser sempre igual:

```c
static void group_loop(const ScreenGroup *group) {
    uint8_t item = 0, page = 0;
    bool redraw = true;

    wait_key_release();
    while (1) {
        const ScreenItem *cur = item_at(group, item);

        check_on_exit();
        kb_Scan();

        if (redraw) {
            draw_header(cur->title, page, cur->page_count);
            draw_page_template(&cur->pages[page]);
            draw_footer();
            gfx_SwapDraw();
            redraw = false;
        }

        if (pressed_once(kb_KeyClear)) return;
        if (pressed_once(kb_KeyDown) && item + 1 < group_count(group)) {
            item++; page = 0; redraw = true;
        }
        if (pressed_once(kb_KeyUp) && item > 0) {
            item--; page = 0; redraw = true;
        }
        if (pressed_once(kb_KeyRight) && page + 1 < cur->page_count) {
            page++; redraw = true;
        }
        if (pressed_once(kb_KeyLeft) && page > 0) {
            page--; redraw = true;
        }
        delay(15);
    }
}
```

Esse formato facilita criar novos apps: para adicionar uma área nova, você
cria um array de páginas, coloca em um `ScreenGroup` e registra um `MenuItem`.
O menu, as teclas e a paginação não precisam ser reescritos.

---

## 8) Cálculos (padrões úteis)

* **Centroides compostos**: usar soma ponderada com **área negativa** para recortes.

  * `xbar = Sum(Ai*xi) / Sum(Ai)`, `ybar = Sum(Ai*yi) / Sum(Ai)`.
* **Inércia Ix** sobre LN em `ybar`:
  `Ix = Sum( Ixc + A * dy^2 )`, com `Ixc = b*h^3/12`, `dy = abs(yi - ybar)`.

**Dicas de performance/memória**

* Para potências pequenas, **evite `pow`**: use `h*h*h`.
* Se der **Erro: Memória**, reduza limites (`MAX_*`), remova `stdio` pesado (`sprintf/printf`) e use prints fixos (ex.: `print_fix3`).
* Prefira `float` quando a precisão for suficiente.

---

## 9) Tratando **Erro: Memória** (e prevenindo)

Quando o SO mostra “**ERRO: MEMÓRIA**”:

1. **MEM → 2: Mem Mgmt/Del...**

   * Apague listas/matrizes/strings grandes.
   * Deixe programas C **ARCHIVED** (aperta ENTER para alternar).
2. **MEM → 8: Garbage Collect** (se disponível) → **Yes**.
3. **MEM → 7: Reset → 1: All RAM → 2: Reset** (apaga apenas RAM).
4. Se necessário, **botão RESET** atrás (segure **CLEAR** ao reset para “Mem Cleared”).

**No código/Makefile**:

* `COMPRESSED=YES`, `ARCHIVED=YES`.
* Use **só** `-lgraphx -lkeypadc -lm`.
* Evite `printf/sprintf`; use prints simples.
* Tenha arrays estáticos com limites **realistas**.

---

## 10) Mensagens e relatórios “limpos”

* Use **linhas curtas** e padronizadas:

  * “ENTER=proximo  CLEAR=voltar  ON=sair”
  * “N materiais (0..12):”
  * “x0 (canto inf.):”
* Sempre **mostre o que foi calculado**: somas, parciais e resultado.
* Para valores numéricos, decida:

  * **conveniência** (`sprintf("%.3f")`) ou
  * **leveza** (impressor fixo com N casas).

**Impressor leve com 3 casas (exemplo)**

```c
static void print_fix3(const char *label, double v, int y){
    /* converte v para "label <esp> sss.ddd" (3 casas) */
    char line[COLS+1]; int i=0;
    int neg = (v<0); if (neg) v=-v;
    long ip = (long)v;
    long fp = (long)((v - (double)ip) * 1000.0 + 0.5);
    if (fp >= 1000) { ip += 1; fp -= 1000; }
    // label
    for (int k=0; label[k] && i<COLS; ++k) line[i++]=label[k];
    if (i<COLS) line[i++]=' ';
    if (neg && i<COLS) line[i++]='-';
    // inteiro
    char tmp[16]; int t=0; if (ip==0) tmp[t++]='0';
    while (ip>0 && t<15) { tmp[t++]='0'+(ip%10); ip/=10; }
    while (t && i<COLS) line[i++]=tmp[--t];
    if (i<COLS) line[i++]='.';
    if (i<COLS) line[i++]='0'+(fp/100)%10;
    if (i<COLS) line[i++]='0'+(fp/10)%10;
    if (i<COLS) line[i++]='0'+(fp%10);
    line[i]='\0';
    prn(y, line);
}
```

---

## 11) Opções de fonte (opcional)

* `graphx` → fonte 8×8 **ASCII**. Não tem Σ, frações compostas ou “x̄”.
* **fontlibc** (opcional) permite:

  * **Auto-wrap**, janelas de texto, cores;
  * Usar **font packs** (ex.: `DRSANS.8xv`);
  * Incluir glifos como ½, ¼, ¾, ², ³ via CP-1252;
  * **Custo**: appvar a mais, mais RAM.

**Quando usar**: apenas se precisar muito de layout de texto avançado. Para apps técnicos focados em cálculo, **ASCII + graphx** é mais leve e robusto.

---

## 12) Padrão de código/base (template)

```c
#include <graphx.h>
#include <keypadc.h>
#include <stdlib.h>
#include <string.h>

/* === config e helpers === */
#define COLS 40
static inline void check_on_exit(void){ kb_Scan(); if (kb_On){ gfx_End(); exit(0);} }
static void screen_init_white(void){
  gfx_Begin(); gfx_SetDrawBuffer();
  gfx_FillScreen(255); gfx_SwapDraw();
  gfx_FillScreen(255); gfx_SwapDraw();
  gfx_SetDrawBuffer(); gfx_FillScreen(255);
  gfx_SetTextFGColor(0); gfx_SetTextScale(1,1);
}
static void prnXY(const char*s,int x,int y){ char b[COLS+1]; int i=0; while(s[i]&&i<COLS)b[i]=s[i++]; b[i]='\0'; gfx_PrintStringXY(b,x,y); }
static void prn(int y,const char*s){ prnXY(s,2,y); }
static uint8_t pressed_once(kb_lkey_t k){ static uint8_t p[256]; uint8_t d=kb_IsDown(k)?1:0, e=d&&!p[k]; p[k]=d; return e; }

/* === suas telas === */
static void tela_construir(void){ /* ... */ }
static void tela_menu(void){ /* ... */ }

/* === main === */
int main(void){
  kb_DisableOnLatch(); kb_Scan();
  screen_init_white();
  for(;;){ tela_construir(); tela_menu(); }
  gfx_End(); return 0;
}
```

---

## 13) Renderização e validação visual no PC

Quando o app tem muitas páginas, desenhos ou submenus, vale criar uma ferramenta
em `tools/` para renderizar a tela da calculadora no computador antes de
compilar. O alvo é sempre uma imagem **320×240**, com a mesma paleta, fonte
8×8 aproximada e geometria dos helpers em `ui.c`.

O padrão mais confiável é manter uma **fonte única de desenho**:

```python
ops = [
    ("vsrc_v", 50, 90, 170, "12V"),
    ("res_h", 50, 90, 130, "4"),
    ("res_v", 130, 90, 170, "6"),
    ("wire", 50, 170, 130, 170),
    ("lbl", "vo", 150, 118),
]
```

Essa lista de operações pode alimentar duas saídas:

1. **Emissão C**: gera uma função `draw_exemplo(void)` com chamadas
   `draw_voltage_source`, `draw_res_h`, `draw_wire`, etc.
2. **Preview PNG**: desenha a mesma página com `Pillow`, espelhando os helpers
   do `ui.c`.

Exemplo de comando:

```bash
python tools/generate_catalog.py --preview previews
```

Checklist para a ferramenta de preview:

* Gerar PNGs com exatamente `320x240`.
* Desenhar cabeçalho, rodapé, título, linhas de texto, caixa de resultado e
  corpo gráfico.
* Usar a mesma geometria do `ui.c`: tamanho dos resistores, fontes, nós,
  textos, setas e componentes dependentes.
* Detectar cedo textos longos, elementos fora da tela e sobreposição grosseira.
* Nunca embutir o PNG no `.8xp`; o PNG é só validação no PC.

Esse fluxo reduz muito tentativa e erro: primeiro valide visualmente os PNGs,
depois rode auditoria de strings, compile e só então envie o `.8xp`.

---

## 14) Ferramentas auxiliares recomendadas

Mantenha scripts pequenos em `tools/` para automatizar verificações repetitivas:

* `audit_strings.py`: confere ASCII, tamanho máximo de strings C e textos que
  podem estourar 40 colunas.
* `render_pdf.py`: renderiza páginas de PDF para PNG e, quando possível, extrai
  texto para conferência.
* `cv_render.py` ou equivalente: espelha primitivas `graphx` em Python e gera
  previews 320×240.
* `generate_catalog.py`: transforma dados estruturados em `.c`, manifesto e
  previews.

Dependências úteis no PC/WSL:

```text
Pillow        // render PNG e validação visual
pypdfium2     // renderização de PDF
pdfplumber    // extração de texto/tabelas quando o PDF permite
pytesseract   // OCR opcional para PDF escaneado
```

Validação mínima antes de entregar:

```bash
python tools/audit_strings.py
python tools/generate_catalog.py --preview previews
make clean
make
```

Se o CEdev gerar vários `.8xv` sem isso ser intencional, o app provavelmente
ficou grande demais ou está embutindo dados pesados. Para visualizadores e apps
de cálculo, prefira redesenhar com primitivas `graphx` em vez de guardar imagens
na calculadora.

---

## 15) Depuração — tabela de sintomas

| Sintoma                     | Causa provável                                 | Correção                                                                             |
| --------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------ |
| “Barras”/lixo na tela       | `SwapDraw` sem `SetDrawBuffer`, VRAM não limpa | Siga a sequência de limpeza dos **dois buffers** ao iniciar                          |
| ON não sai                  | Não checou `kb_On` / latch preso               | Use `kb_DisableOnLatch()` e `kb_On` em todos os loops                                |
| Só algumas teclas funcionam | Leitura por grupo/bit errada                   | Use `kb_IsDown(kb_KeyX)` e `pressed_once()`                                          |
| “ERRO: MEMÓRIA” ao abrir    | RAM insuficiente / binário grande              | GC + Reset RAM; compile com COMPRESSED/ARCHIVED; remova `printf/pow`; reduza limites |
| Caracteres “estranhos”      | UTF-8                                          | Use **ASCII** (ex.: `xbar`, `deg`)                                                   |
| Página cortada no preview   | Coordenadas fora de 320×240                    | Ajuste geometria no helper e renderize novamente                                     |
| Preview diferente da TI     | Helper Python divergiu do `ui.c`               | Atualize o renderizador sempre que mudar `ui.c`                                      |

---

## 16) Checklist antes de compilar

* [ ] `gfx_SetDrawBuffer()` chamado **antes** do primeiro `gfx_SwapDraw()`.
* [ ] Limpeza dos **dois buffers** no início.
* [ ] `kb_DisableOnLatch()` no `main`, **ON** tratado.
* [ ] Entrada numérica `input_line()` com `ENTER`/`CLEAR`.
* [ ] Prints truncados a **40 colunas**.
* [ ] Makefile **COMPRESSED=YES**, **ARCHIVED=YES**, só `-lgraphx -lkeypadc -lm`.
* [ ] Sem UTF-8.
* [ ] Limites estáticos **realistas** (ex.: `MAX_RECT`).
* [ ] Catálogos grandes divididos em arquivos separados.
* [ ] Submenus testados com `UP/DOWN`, `ENTER`, `CLEAR`, `LEFT/RIGHT`.
* [ ] Previews 320×240 gerados quando houver desenhos ou muitas páginas.
* [ ] Nenhum PNG/PDF embutido no app, salvo se for uma decisão consciente.

---

## 17) Padrão de UX (recomendado)

* Sempre mostre uma **faixa de ajuda**:
  `ENTER=proximo  CLEAR=voltar  ON=sair`
* Em relatórios passo a passo, **pare** a cada item e aceite `ENTER` (avança) ou `CLEAR` (volta).
* Um valor por tela: **um prompt por vez**.

---

## 18) Quando precisar de persistência (extra)

* Use `fileioc` (AppVars) para salvar/carregar dados.
* **Atenção à RAM**: serialize estruturas de forma compacta (ex.: `uint16_t`/`float` onde couber).

---

## 19) Arquitetura recomendada: runtime fixo + gerador de conteúdo

Padrão validado em produção (apps grandes de exercícios/teoria). Separe **duas
camadas**:

1. **Runtime do app** (`main.c`, `ui.c`, `app.h`): navegação, leitura de teclado
   e **primitivas de desenho**. Muda pouco; **não** altere a lógica dele quando
   só quer mudar conteúdo. No máximo **adicione** primitivas novas e
   autocontidas.
2. **Conteúdo gerado** (`src/*_catalog.c` ou `src/exercises.c`): **GERADO** por
   um script Python em `tools/`. **Nunca edite o `.c` gerado à mão** — edite os
   dados no gerador e rode-o de novo.

### Modelo de páginas (reaproveitável)

Use structs simples e genéricas:

```c
typedef struct { const char *text; int x; int y; uint8_t color; } TextLine;
typedef struct { const char *title, *subtitle;
                 const TextLine *lines; uint8_t line_count;
                 const char *result; uint8_t result_y;
                 void (*body)(void); } Page;       /* body = desenho opcional */
typedef struct { const char *title; const Page *pages; uint8_t page_count; } Exercise;
typedef struct { const char *name; const Exercise *items; uint8_t count; } Topic;
```

Hierarquia de navegação: **Assunto/Tópico → Exercício → Página**. Convenção de
teclas que funciona bem: `UP/DOWN` troca o **exercício**, `</>` (LEFT/RIGHT)
troca a **página**, `CLEAR` volta ao menu, `ON` sai.

Cada exercício vira várias páginas, ex.: **Enunciado → (Desenho/Gráfico) →
Resolução (passo a passo) → Resultado** (caixa azul com a resposta). Decida a
ordem por app — quando o desenho é o objeto de estudo, vale colocá-lo primeiro.

### Geração de texto

* O gerador guarda as linhas como strings com **marcação leve** e converte em
  cor na hora de emitir o C: `# ` → título (azul), `= ` → resultado (vermelho),
  resto preto. Assim a `TextLine.color` já sai pronta.
* **Quebra** automática em ~37 caracteres e **paginação** em ~7 linhas por
  página (y de 62 a 182, passo 20; rodapé em 224). Sobrou? Vira "parte 1/2".
* A caixa de resultado leva um resumo curto (<= ~34 chars) centralizado.

---

## 20) Desenhos e gráficos: "ops" como fonte única (C + preview)

A técnica mais confiável para qualquer figura (circuito, gráfico cartesiano,
diagrama, célula cristalina): descreva o desenho como uma **lista de operações**
(tuplas). A **mesma lista** alimenta duas saídas, garantindo que o preview no PC
seja idêntico à calculadora:

1. **Emissão C** — cada op vira uma chamada a um helper de `ui.c`.
2. **Preview PIL** — um renderizador Python espelha **a mesma geometria** dos
   helpers e gera um PNG 320×240.

```python
# exemplo generico de figura como ops
[ ("axes", 55, 56, 295, 205),
  ("line", 55, 205, 120, 110, "b"),    # trecho de curva
  ("line", 120, 110, 210, 90, "b"),
  ("dot", 120, 110, "r"),              # ponto marcado
  ("text", "ponto", 124, 100, "k") ]
```

### Conjunto mínimo de primitivas (serve para quase tudo)

Defina poucas primitivas em `ui.c` e espelhe **com geometria idêntica** no
renderizador Python:

* `line(x1,y1,x2,y2,cor)` e `dash(...)` (linha tracejada, p/ projeções/amarração);
* `dot(x,y,cor)` (ponto cheio pequeno), `circ`/`disc` (círculo vazado/cheio — átomos, fontes);
* `text(s,x,y,cor)`;
* `axes(x0,y0,x1,y1)` (eixos com setas).

Componentes "ricos" (resistor, fonte, caixa) são **composições** dessas
primitivas — encapsule cada um num helper próprio (ex.: `draw_res_h`).

### Regras de geometria (evita os sintomas da seção 13/15)

* **Orçamento de tela**: mantenha tudo dentro de ~`x[30..305]`, `y[58..205]`
  (abaixo do bloco de título, acima do rodapé em 224).
* **Texto**: fonte 8×8; calcule largura como `8*len(s)` para prever colisões.
* **Curvas/diagramas**: são polilinhas (sequência de `line`). Marque pontos-chave
  com `dot` + `text`. Eixos com `axes`.
* **Diagonais e formas não-axiais** (pontes Wheatstone, triângulos delta,
  ligações cruzadas): ou desenhe como **linha diagonal simples** (com um vão e um
  rótulo, sugerindo um elemento), ou **redesenhe uma versão equivalente** alinhada
  aos eixos (eletricamente/topologicamente idêntica) e explique a simplificação
  na resolução.

### Adicionando uma primitiva nova

Quando faltar um símbolo (ex.: fonte controlada/diamante): adicione **uma função
pequena e autocontida** em `ui.c` (sem mexer no que já existe), declare o
protótipo no header, **espelhe-a no renderizador Python** e registre o op no
mapa `op -> C`. Só então ela aparece no preview.

---

## 21) Extraindo enunciados e figuras de PDFs/imagens

* O leitor de PDF embutido pode exigir `poppler` (`pdftoppm`), nem sempre
  presente. Alternativa robusta: **rasterizar com `pypdfium2`**:
  `pdfium.PdfDocument(src)[i].render(scale=2.2).to_pil().save(...)`.
* Páginas densas: **recorte por região** (coluna/figura) e amplie antes de ler —
  a redução da página inteira perde texto pequeno e detalhe de figura.
* Cuidados comuns: **deriva** (suas estimativas fracionárias de recorte erram
  alguns %, itere); **faixas de marca d'água** no meio da página obscurecem
  figuras (as linhas pretas ainda aparecem sob o cinza; recorte ao redor).
* **Re-derive sempre as respostas.** Manifestos gerados, notas `.md` e até
  "gabaritos" de origem contêm erros. Confira contra a resposta publicada
  oficial quando existir.

---

## 22) Delegando subtarefas ao Codex

O Codex CLI (`codex exec`) ajuda a **descarregar subtarefas pequenas e
isoladas**. Comando recomendado:

```bash
codex exec --cd . --sandbox read-only --skip-git-repo-check \
  --output-last-message .ai-tasks/codex-result.md "<prompt autocontido>"
```

(Use `--sandbox workspace-write` só se ele precisar escrever arquivos.)

**Bons usos** (entregue tudo no prompt, em texto — netlist/fórmulas/dados):

* Conferir aritmética e **resolver sistemas** (ex.: análise nodal/malhas) de forma
  independente.
* Verificar uma redução série/paralelo ou um cálculo numérico.
* Gerar um **patch localizado** ou revisar um trecho isolado.

**Não delegue**: nada que exija contexto global do projeto; **leitura visual
pesada** (o Codex CLI não lê imagens bem — faça você mesmo); decisões
arquiteturais; mudanças em muitos módulos.

**Ressalva**: o Codex também erra contas em expressões aninhadas. Trate-o como
**conferência secundária** — confie na resposta oficial publicada e na sua
derivação auto-consistente acima de qualquer ferramenta isolada. Veja o
resultado com `... 2>&1 | tail` ou lendo `.ai-tasks/codex-result.md`.

---

## 23) Fluxo completo de uma alteração de conteúdo

```bash
# 1) editar os DADOS no gerador (tools/gen_*.py): enunciado, ops do desenho, resolucao
# 2) gerar o C + previews PNG e conferir o layout (sem calculadora)
python tools/gen_catalog.py --preview /tmp/preview
# 3) auditar strings (ASCII + <= 39 chars) e compilar
python tools/audit_strings.py
export PATH="/c/CEdev/bin:$PATH" && /c/CEdev/bin/make.exe clean && /c/CEdev/bin/make.exe
```

Olhe os PNGs antes de mandar o `.8xp`: nada fora da tela, cobrindo texto ou
sobreposto. Esse ciclo (preview → auditoria → build) evita reinícios da
calculadora por desenhos quebrados.

---

### Conclusão

Seguindo este checklist (inicialização correta de vídeo, teclado pelo `kb_IsDown`, ON sempre funcional, ASCII, prints de 40 colunas e disciplina de memória), **qualquer** app de cálculo para a TI-84 Plus CE rodará limpo e previsível.
Guarde este arquivo como **padrão de projeto** e copie o **template** e os **helpers** em novos programas.
