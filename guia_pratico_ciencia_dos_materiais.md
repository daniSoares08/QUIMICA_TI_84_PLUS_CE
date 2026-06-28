# Guia Prático de Resolução: Introdução à Ciência dos Materiais

## Sumário

1. [Estruturas Cristalinas Metálicas: Fundamentos e Geometria](#1-estruturas-cristalinas-metálicas-fundamentos-e-geometria)
2. [Cálculo de Densidade Teórica](#2-cálculo-de-densidade-teórica)
3. [Difusão em Sólidos: Regime Estacionário](#3-difusão-em-sólidos-regime-estacionário)
4. [Influência da Temperatura na Difusão](#4-influência-da-temperatura-na-difusão)
5. [Análise de Diagramas de Fase e Solubilidade](#5-análise-de-diagramas-de-fase-e-solubilidade)
6. [Propriedades Mecânicas: Análise de Gráficos](#6-propriedades-mecânicas-análise-de-gráficos)
7. [Apêndice: Classificação e Ligações Químicas](#7-apêndice-classificação-e-ligações-químicas)

---

# 1. Estruturas Cristalinas Metálicas: Fundamentos e Geometria

A organização atômica define as propriedades macroscópicas dos metais. Use as relações geométricas abaixo para realizar cálculos de rede cristalina.

## 1.1 Tabela Comparativa de Células Unitárias

A estrutura **Hexagonal Compacta (HC)** diferencia-se das estruturas cúbicas por possuir uma sequência de empacotamento de três planos: dois basais e um intermediário.

| Característica | Cúbica de Face Centrada (CFC) | Cúbica de Corpo Centrado (CCC) | Hexagonal Compacta (HC) |
|---|---:|---:|---:|
| Número de coordenação | 12 | 8 | 12 |
| Relação entre parâmetro de rede $a$ e raio atômico $R$ | $a = 2R\sqrt{2}$ | $a = \dfrac{4R}{\sqrt{3}}$ | $a = 2R$ no plano basal |
| Fator de empacotamento atômico (FEA) | 0,74 | 0,68 | 0,74 |

## 1.2 Cálculo de Volume da Célula Unitária $V_c$

Para estruturas cúbicas, o volume da célula unitária é:

$$
V_c = a^3
$$

### Passo a passo

1. **Identifique a estrutura cristalina.**  
   Substitua $a$ pela relação específica em função do raio atômico $R$.

   - Para **CFC**:

     $$
     V_c = \left(2R\sqrt{2}\right)^3
     $$

   - Para **CCC**:

     $$
     V_c = \left(\frac{4R}{\sqrt{3}}\right)^3
     $$

2. **Preste atenção nas unidades.**  
   Se a massa atômica estiver em $g/mol$, converta o raio $R$ para **centímetros** para que o volume fique em $cm^3$.

   Isso deixa a conta compatível para calcular densidade em $g/cm^3$.

## 1.3 Roteiro para Identificação de Estrutura Cristalina

Quando o problema fornece densidade $\rho$, raio atômico $R$ e peso atômico $A$, mas não informa a estrutura cristalina:

1. **Isole $n$ na fórmula da densidade.**

   $$
   n = \frac{\rho \cdot V_c \cdot N_A}{A}
   $$

2. **Calcule usando um modelo de estrutura.**  
   Use o $V_c$ correspondente a uma das estruturas, por exemplo CFC ou CCC.

3. **Analise o resultado.**

   - Se $n \approx 4$, a estrutura provavelmente é **CFC**.
   - Se $n \approx 2$, a estrutura provavelmente é **CCC**.

---

# 2. Cálculo de Densidade Teórica

Também chamada de **massa específica teórica**, a densidade pode ser prevista a partir dos dados atômicos e da estrutura cristalina.

## 2.1 Aplicação da Fórmula Progressiva

A equação fundamental é:

$$
\rho = \frac{n \cdot A}{V_c \cdot N_A}
$$

Onde:

| Símbolo | Significado |
|---|---|
| $\rho$ | Densidade teórica |
| $n$ | Número de átomos por célula unitária |
| $A$ | Peso atômico, geralmente em $g/mol$ |
| $V_c$ | Volume da célula unitária |
| $N_A$ | Constante de Avogadro: $6{,}022 \times 10^{23}$ átomos/mol |

Valores comuns de $n$:

| Estrutura | Átomos por célula unitária |
|---|---:|
| CFC | 4 |
| CCC | 2 |

## 2.2 Lista de Verificação de Unidades

Antes de sair fazendo conta igual um condenado, confira as unidades. Essa parte costuma ferrar a questão inteira.

- [ ] **Nanômetros para centímetros:** multiplicar por $10^{-7}$.

  Exemplo:

  $$
  0{,}143\ nm = 1{,}43 \times 10^{-8}\ cm
  $$

- [ ] **Nanômetros para metros:** multiplicar por $10^{-9}$.

- [ ] **Resultado final:** verificar se a densidade está em $g/cm^3$ ou $kg/m^3$.

---

# 3. Difusão em Sólidos: Regime Estacionário

## 3.1 Procedimento para Fluxo e Massa — 1ª Lei de Fick

Para determinar a massa $M$ que atravessa uma chapa de área $A$ durante um tempo $t$:

### 1. Calcule o fluxo $J$

$$
J = -D \frac{C_A - C_B}{\Delta x}
$$

Onde:

| Símbolo | Significado |
|---|---|
| $J$ | Fluxo de difusão |
| $D$ | Coeficiente de difusão |
| $C_A$ e $C_B$ | Concentrações em dois pontos |
| $\Delta x$ | Espessura ou distância entre os pontos |

### 2. Converta o tempo

Se $D$ estiver em $m^2/s$, o tempo precisa estar em **segundos**.

$$
1\ h = 3600\ s
$$

### 3. Calcule a massa transportada

$$
M = J \cdot A \cdot t
$$

## 3.2 Determinação de Profundidade de Concentração $x$

Se o perfil de concentração for linear, use o gradiente para encontrar a profundidade onde a concentração atinge um valor $C_x$.

### 1. Determine o gradiente

$$
G = \frac{C_{alta} - C_{baixa}}{espessura}
$$

### 2. Use a equação da reta para isolar $x$

$$
x = \frac{C_{alta} - C_x}{G}
$$

### Exemplo conceitual

Para encontrar onde a concentração cai de $2{,}0$ para $0{,}5\ kg/m^3$ com um gradiente conhecido, use a diferença de concentração dividida pela taxa de queda.

---

# 4. Influência da Temperatura na Difusão

## 4.1 Cálculo do Coeficiente de Difusão $D$

Use a Equação de Arrhenius:

$$
D = D_0 \exp\left(-\frac{Q_d}{RT}\right)
$$

Onde:

| Símbolo | Significado |
|---|---|
| $D$ | Coeficiente de difusão |
| $D_0$ | Fator pré-exponencial |
| $Q_d$ | Energia de ativação para difusão |
| $R$ | Constante dos gases: $8{,}314\ J/(mol \cdot K)$ |
| $T$ | Temperatura absoluta em Kelvin |

### Alertas críticos

- Se $Q_d$ vier em $kJ/mol$, multiplique por $10^3$ para converter para $J/mol$.

  $$
  1\ kJ = 1000\ J
  $$

- A constante $R = 8{,}314\ J/(mol \cdot K)$ exige que $Q_d$ esteja em **Joules**.

- A temperatura sempre deve estar em Kelvin:

  $$
  T(K) = T(^\circ C) + 273
  $$

## 4.2 Roteiro para Determinação de $Q_d$ e $D_0$

Quando forem dados dois pontos, $(D_1, T_1)$ e $(D_2, T_2)$:

### 1. Isole $Q_d$

$$
Q_d = -R \frac{\ln D_1 - \ln D_2}{\frac{1}{T_1} - \frac{1}{T_2}}
$$

### 2. Isole $D_0$

Depois de obter $Q_d$, use a equação original e isole $D_0$:

$$
D_0 = \frac{D_1}{\exp\left(-\frac{Q_d}{RT_1}\right)}
$$

---

# 5. Análise de Diagramas de Fase e Solubilidade

## 5.1 Definições e Localização

| Termo | Definição |
|---|---|
| Fase | Porção homogênea do sistema com características físicas e químicas uniformes |
| Linha liquidus | Fronteira acima da qual existe apenas fase líquida $L$ |
| Linha solidus | Fronteira abaixo da qual existe apenas fase sólida $\alpha$ |

## 5.2 Regra da Alavanca — Lever Rule com Termos $R$ e $S$

Ao analisar um ponto $C_0$ em uma região bifásica $\alpha + L$:

### 1. Trace a linha de amarração

Trace uma linha horizontal na temperatura $T$ que toque as duas fases.

### 2. Identifique os segmentos

- $R$: segmento à esquerda, entre $C_L$ e $C_0$.
- $S$: segmento à direita, entre $C_0$ e $C_\alpha$.

### 3. Aplique as fórmulas

#### Fração de líquido

$$
w_L = \frac{S}{R+S} = \frac{C_\alpha - C_0}{C_\alpha - C_L}
$$

#### Fração de sólido

$$
w_\alpha = \frac{R}{R+S} = \frac{C_0 - C_L}{C_\alpha - C_L}
$$

---

# 6. Propriedades Mecânicas: Análise de Gráficos

## 6.1 Extração de Parâmetros

| Parâmetro | Como identificar no gráfico | Fórmula / observação |
|---|---|---|
| Módulo de elasticidade $E$ | Inclinação da reta inicial | $E = \dfrac{\sigma}{\epsilon}$ |
| Tensão de escoamento $\sigma_e$ | Início da deformação permanente | Ponto onde o material começa a deformar plasticamente |
| Limite de resistência $\sigma_{LRT}$ | Maior valor de tensão no gráfico | Pico do gráfico tensão × deformação |

## 6.2 Cálculos de Resiliência e Ductilidade

### Ductilidade — percentual de alongamento

$$
\%AL = \frac{l_f - l_0}{l_0} \times 100
$$

Onde:

| Símbolo | Significado |
|---|---|
| $l_0$ | Comprimento inicial |
| $l_f$ | Comprimento final |

### Resiliência $U_r$

A resiliência é a área da região elástica do gráfico tensão × deformação.

Você pode calcular por:

$$
U_r = \frac{\sigma_e^2}{2E}
$$

ou:

$$
U_r = \frac{\sigma_e \cdot \epsilon_e}{2}
$$

## 6.3 Estudo de Caso MateriaCraft: Cabos de Aço

Para selecionar o material de um cabo de aço sujeito a $150\ MPa$ com deformação elástica máxima de $1{,}0 \times 10^{-3}$:

### 1. Calcule o módulo necessário

$$
E_{alvo} = \frac{150\ MPa}{1{,}0 \times 10^{-3}}
$$

$$
E_{alvo} = 150.000\ MPa = 150\ GPa
$$

### 2. Decida o material adequado

O material escolhido deve possuir:

- $E \geq 150\ GPa$
- $\sigma_e > 150\ MPa$

Assim, o cabo não ultrapassa a deformação elástica máxima e evita deformação plástica permanente.

---

# 7. Apêndice: Classificação e Ligações Químicas

## 7.1 Tabela de Referência — Caso MateriaCraft: Lanterna

| Componente | Classe de material | Ligação predominante | Interação eletrônica |
|---|---|---|---|
| Corpo | Metal | Metálica | Mar de elétrons livres |
| Pegada | Polímero | Covalente | Compartilhamento de elétrons |
| Lente | Vidro / Cerâmica | Iônica / Covalente | Doação e/ou compartilhamento |

## 7.2 Diferenciação Estrutural

### Materiais cristalinos

São materiais que possuem ordem atômica de longo alcance.

Exemplos comuns:

- Metais
- Algumas cerâmicas

### Materiais amorfos

São materiais que não possuem ordem atômica de longo alcance.

Exemplo importante:

- Vidros

### Destaque sobre vidros

Os vidros são classificados como **líquidos super-resfriados**, pois mantêm o desarranjo atômico característico do estado líquido mesmo em temperatura ambiente.
