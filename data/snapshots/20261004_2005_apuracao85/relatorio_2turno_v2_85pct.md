# Segundo turno 2026 — Flávio Bolsonaro × Lula: modelo v2 (ensemble)

> Gerado em 04/10/2026 ~20h–21h (apuração do 1º turno em ~85%). Código: `eleicao2026/segundo_turno_v2.py`. Todas as simulações: `eleicao2026/data/sims_2turno.csv` e `sims_2turno_uf.csv`.

## 1. Conclusão

| | Valor |
|---|---:|
| **Probabilidade de Lula vencer o 2º turno (ensemble)** | **17.2%** |
| Probabilidade de Flávio vencer | 82.8% |
| % de Lula nos votos válidos — média | 47.97% |
| % de Lula — mediana (IC 90%) | 47.56% (44.96% a 52.48%) |
| % de Lula — IC 95% | 44.23% a 53.67% |
| Margem Lula − Flávio — mediana (IC 90%) | -5.793.253 (-12.031.357 a 5.935.462) votos |

| Componente | Peso | Lula % (média) | IC 90% de Lula | P(Lula vence) | Margem mediana (votos) |
|---|---:|---:|---:|---:|---:|
| M1 — estrutural (transferência de votos) | 50% | 46.99% | 45.24% a 48.71% | 0.2% | -7.157.263 |
| M2 — pesquisas corrigidas pelo erro do 1º turno | 30% | 48.77% | 44.81% a 52.76% | 30.6% | -2.977.838 |
| M3 — histórico dos 2º turnos | 20% | 49.22% | 43.28% a 55.15% | 39.5% | -2.003.252 |

> **Leitura:** os três métodos independentes apontam **Flávio na frente**, mas com tamanhos diferentes. O estrutural (M1) é o mais favorável a Flávio; as pesquisas corrigidas (M2) e o histórico (M3) dão uma disputa bem mais apertada. A probabilidade final depende dos pesos — veja a seção 8.

## 2. Fontes e o que foi usado

| # | Fonte | O que forneceu | Confiança |
|---|---|---|---|
| 1 | TSE — resultados.tse.jus.br (arquivos oficiais `ele2026/6257`), baixados 04/10/2026 | Apuração por município (5.757), seções e eleitorado apurados | **Alta** (oficial) |
| 2 | TSE — Dados Abertos (`cdn.tse.jus.br/.../votacao_candidato_munzona_2022.zip`, `perfil_eleitorado_2022/2026.zip`) | Votos de Presidente 2022 (1º e 2º turno) por município; perfil do eleitorado | **Alta** (oficial) |
| 3 | Wikipédia (EN) — *Opinion polling for the 2026 Brazilian presidential election* (wikitext, 04/10/2026) | 56 pesquisas de 1º turno e 56 de 2º turno (Lula × Flávio), com link p/ fonte de cada uma | **Média-alta** (compilação com citações; não reconferi cada link) |
| 4 | g1 — *Quaest, 2º turno: Flávio 44%, Lula 42%* (03/10/2026); *Datafolha 2º turno: Lula 47%, Flávio 45%* (CNN Brasil); *Datafolha 2º turno 17/09* (g1) | Originais das pesquisas de 2º turno (citadas pela Wikipédia) | Média (links citados; a página do g1 não carregou para eu ler o texto) |
| 5 | Resultados de busca na web (resumos), consultas de 04/10/2026 — Quaest 3/10 e Datafolha 1–3/10 | Intenção de voto no 2º turno **por eleitorado de cada candidato eliminado** (Renan, Caiado, Cury; Zema/Renan no Datafolha) | **Média-baixa**: resumos de busca, não li as matérias originais; Datafolha e Quaest diferem bastante entre si (por isso uso as duas) |
| 6 | Resultados de busca — rejeição Datafolha (Lula 45% × Flávio 45%) e aprovação (Quaest 3/10: 44% aprova × 49% desaprova; Datafolha 1/10: 48% × 49%) | Contexto: disputa polarizada e equilibrada | Média-baixa (resumos) — **não entra como número no modelo**, só confirma o cenário apertado |
| 7 | Resultados de busca — apoios: Zema planeja apoiar Flávio; Caiado, Cury, Renan e Republicanos sem apoio formal até agora; pacto de união da direita no 2º turno | Contexto qualitativo (entra como incerteza na divisão dos votos) | Média-baixa (resumos) |
| 8 | TSE / histórico (resumos de busca + dados 2022 do próprio TSE) — 1º e 2º turnos 2002–2022 | M3 (histórico). 2022 conferido contra os dados oficiais baixados | Média-alta (2002–2018 conferidos por 1 busca; números batem com os que conheço) |
| 9 | Resultados de busca — erro das pesquisas em 2022 (Datafolha 50×36, Ipec 51×37 vs urna 48,43×43,20) | Contexto: viés pró-Lula em pesquisas de 1º turno também em 2022; no 2º turno de 2022 o erro foi bem menor | Média (resumos) |

> Os números das fontes 5–7 e 9 vieram de resumos de busca (podem conter erros). Os dados 1–3 são verificáveis e sustentam o núcleo do modelo.

## 3. Pesquisas de 2º turno (Lula × Flávio) e correção pelo erro do 1º turno

Erro das pesquisas de 1º turno medido contra a urna (projetada: Lula 44.95%, Flávio 47.19%): **margem +4.2 pp pró-Lula** em média (dp entre institutos 3.1 pp; n=12).

| Instituto | Data (fim) | Lula | Flávio | Branco/NS | Lula % dos válidos (2 cand.) | Erro do 1º turno (margem, pp) |
|---|---|---:|---:|---:|---:|---:|
| Datafolha | 3 Oct | 47.0 | 46.0 | 8.0 | 50.5% | +4.4 |
| Quaest | 2–3 Oct | 42.0 | 44.0 | 14.0 | 48.8% | +4.5 |
| Futura | 2–3 Oct | 45.1 | 48.0 | 6.9 | 48.4% | +0.1 |
| Palver | 30 Sep–3 Oct | 44.0 | 49.0 | 7.0 | 47.3% | -1.8 |
| PoderData | 30 Sep–2 Oct | 46.0 | 46.0 | 8.0 | 50.0% | +3.3 |
| MDA | 29 Sep–2 Oct | 47.0 | 43.0 | 10.0 | 52.2% | +7.9 |
| AtlasIntel | 27 Sep–2 Oct | 47.6 | 47.4 | 5.0 | 50.1% | +5.2 |
| Vox Brasil | 29 Sep–1 Oct | 45.2 | 48.2 | 6.6 | 48.4% | +1.3 |
| Real Time | 26–30 Sep | 45.0 | 46.0 | 9.0 | 49.5% | +6.5 |
| Indexa | 27–29 Sep | 43.0 | 42.0 | 15.0 | 50.6% | +8.1 |
| Ideia | 25–28 Sep | 48.5 | 48.0 | 3.6 | 50.3% | +3.3 |
| Nexus | 25–27 Sep | 46.0 | 44.0 | 9.0 | 51.1% | +7.5 |

- Média ponderada por recência (meia-vida 7 dias): **Lula 49.67%** (bruta, antes da correção).
- Correção: o viés do 1º turno (≈ 4.6 pp de margem em base de dois candidatos) persiste só parcialmente no 2º turno (em 2022 o erro de 2º turno foi ~¼ a ½ do de 1º turno) → **fator 0,4 ± 0,2** → Lula ≈ **48.76%**.

### Erro das pesquisas de 1º turno por instituto (último levantamento, % dos válidos)

| Instituto | Data | Lula (pesq.) | Flávio (pesq.) | Erro Lula | Erro Flávio | Erro de margem |
|---|---|---:|---:|---:|---:|---:|
| Indexa | 27–29 Sep | 45.9% | 40.0% | +0.9 | -7.2 | +8.1 |
| MDA | 29 Sep–2 Oct | 47.8% | 42.2% | +2.9 | -5.0 | +7.9 |
| Nexus | 25–27 Sep | 44.2% | 38.9% | -0.7 | -8.2 | +7.5 |
| Real Time | 26–30 Sep | 45.7% | 41.5% | +0.8 | -5.7 | +6.5 |
| AtlasIntel | 27 Sep–2 Oct | 46.9% | 44.0% | +2.0 | -3.2 | +5.2 |
| Quaest | 2–3 Oct | 46.0% | 43.7% | +1.0 | -3.5 | +4.5 |
| Datafolha | 3 Oct | 45.7% | 43.5% | +0.7 | -3.7 | +4.4 |
| PoderData | 30 Sep–2 Oct | 45.2% | 44.1% | +0.2 | -3.1 | +3.3 |
| Ideia | 25–28 Sep | 40.1% | 39.1% | -4.9 | -8.1 | +3.3 |
| Vox Brasil | 29 Sep–1 Oct | 45.0% | 45.9% | +0.0 | -1.3 | +1.3 |
| Futura | 2–3 Oct | 42.6% | 44.7% | -2.3 | -2.5 | +0.1 |
| Palver | 30 Sep–3 Oct | 43.4% | 47.5% | -1.5 | +0.3 | -1.8 |

## 4. Para onde vão os eleitores dos eliminados (M1)

| Candidato | Votos válidos 1º turno (proj.) | Fonte(s) | → Flávio (% dos válidos) | Declara voto (literal) |
|---|---:|---|---:|---:|
| Escritor Augusto Cury | 3.469.097 | Quaest 34/23 + Datafolha agregado 43/30 | 59.3% | 57% |
| Renan Santos | 2.706.041 | Quaest 60/11 + Datafolha 43/22 | 75.3% | 71% |
| Ronaldo Caiado | 2.617.161 | Quaest 43/19 + Datafolha agregado 43/30 | 64.1% | 62% |
| Zema | 328.672 | Datafolha 48/25 | 65.8% | 73% |
| Samara | 125.049 | suposição: direita/menor | 65.0% | 73% |
| Hertz Dias | 44.153 | suposição: esquerda minoritária | 30.0% | 73% |
| Clariana Barao | 40.101 | suposição: direita/menor | 65.0% | 73% |
| Edmilson Costa | 22.824 | suposição: esquerda minoritária | 30.0% | 73% |
| Veterinário Wilson Grassi | 17.127 | suposição: direita/menor | 65.0% | 73% |
| Rui Costa Pimenta | 15.466 | suposição: esquerda minoritária | 30.0% | 73% |

- Média ponderada: **65.3% para Flávio** (em 2022 os eliminados foram 48.4% para Bolsonaro). Quaest dá mais a Flávio que o Datafolha; uso a média dos dois.
- Comparecimento líquido dos eliminados no 2º turno de 2022: **94.2%**; na simulação varia entre o declarado nas pesquisas e esse valor.
- Inclinação regional (2022, logit relativo ao país; + = mais Flávio): Norte -0.05 | Nordeste -0.24 | Centro-Oeste -0.31 | Sudeste +0.05 | Sul +0.12 | Exterior -0.19.
- Retenção das bases (2022): Lula 100.2%→Lula; Bolsonaro 106.6%→Bolsonaro (efeito de mobilização); erro de validação cruzada da calibração: 0.66 pp por município.

## 5. Modelo histórico (M3)

| Ano | Líder do 1º turno | % líder 1T | % 2º colocado 1T | Líder entre os 2 (1T) | % líder no 2T | Variação |
|---|---|---:|---:|---:|---:|---:|
| 2002 | Lula | 46.44 | 23.20 | 66.7 | 61.27 | -5.4 |
| 2006 | Lula | 48.61 | 41.64 | 53.9 | 60.83 | +7.0 |
| 2010 | Dilma | 46.91 | 32.61 | 59.0 | 56.05 | -2.9 |
| 2014 | Dilma | 41.59 | 33.55 | 55.4 | 51.64 | -3.7 |
| 2018 | Bolsonaro | 46.03 | 29.28 | 61.1 | 55.13 | -6.0 |
| 2022 | Lula | 48.43 | 43.20 | 52.9 | 50.90 | -2.0 |

Regressão: `share do líder no 2T − 50 = 0.66 × (share entre os dois no 1T − 50)`; erro-padrão 4.0 pp (inflado por 2006). Em 2026, Flávio é o líder com 51.2% entre os dois → **Flávio 50.8% / Lula 49.2%**. Limitação: ignora que os eliminados de 2026 são majoritariamente de direita (por isso tem só 20% de peso).

## 6. Resultado por UF (ensemble; % de Lula nos válidos do 2º turno)

| UF | Estado | Região | Válidos 1T (proj.) | Lula 1T | Flávio 1T | **Lula 2T (mediana)** | IC 90% | P(Lula vence na UF) |
|---|---|---|---:|---:|---:|---:|---|---:|
| SP | São Paulo | Sudeste | 24.894.525 | 38.2% | 51.9% | **41.4%** | 38.6% a 46.6% | 1% |
| MG | Minas Gerais | Sudeste | 11.987.859 | 43.1% | 48.4% | **46.0%** | 43.2% a 51.3% | 10% |
| RJ | Rio de Janeiro | Sudeste | 9.362.935 | 40.0% | 52.4% | **42.5%** | 39.7% a 47.8% | 2% |
| BA | Bahia | Nordeste | 8.600.621 | 65.0% | 29.6% | **67.5%** | 64.9% a 71.9% | 100% |
| PR | Paraná | Sul | 6.585.437 | 31.2% | 59.9% | **33.5%** | 30.6% a 38.4% | 0% |
| RS | Rio Grande do Sul | Sul | 6.424.761 | 35.7% | 55.6% | **38.0%** | 35.1% a 43.1% | 0% |
| CE | Ceará | Nordeste | 5.621.652 | 62.3% | 32.1% | **64.7%** | 62.1% a 69.4% | 100% |
| PE | Pernambuco | Nordeste | 5.617.616 | 63.2% | 31.2% | **65.7%** | 63.1% a 70.3% | 100% |
| PA | Pará | Norte | 4.861.523 | 49.3% | 45.0% | **51.2%** | 48.4% a 56.5% | 76% |
| SC | Santa Catarina | Sul | 4.499.966 | 25.1% | 66.6% | **27.0%** | 24.3% a 31.4% | 0% |
| MA | Maranhão | Nordeste | 4.020.201 | 63.3% | 31.5% | **65.6%** | 62.9% a 70.2% | 100% |
| GO | Goiás | Centro-Oeste | 3.833.998 | 30.9% | 53.8% | **36.8%** | 33.4% a 41.9% | 0% |
| PB | Paraíba | Nordeste | 2.514.202 | 61.3% | 33.1% | **63.8%** | 61.1% a 68.5% | 100% |
| ES | Espírito Santo | Sudeste | 2.251.050 | 37.7% | 54.8% | **40.1%** | 37.3% a 45.3% | 1% |
| AM | Amazonas | Norte | 2.168.292 | 47.7% | 45.4% | **50.1%** | 47.1% a 55.4% | 53% |
| PI | Piauí | Nordeste | 2.147.074 | 70.3% | 24.7% | **72.7%** | 70.3% a 76.7% | 100% |
| RN | Rio Grande do Norte | Nordeste | 2.077.080 | 59.4% | 35.1% | **61.7%** | 59.0% a 66.6% | 100% |
| MT | Mato Grosso | Centro-Oeste | 1.994.754 | 29.1% | 65.2% | **30.6%** | 27.8% a 35.4% | 0% |
| AL | Alagoas | Nordeste | 1.840.516 | 54.0% | 41.1% | **55.9%** | 53.0% a 61.1% | 99% |
| DF | Distrito Federal | Centro-Oeste | 1.773.069 | 38.1% | 51.3% | **42.1%** | 38.5% a 47.2% | 1% |
| MS | Mato Grosso do Sul | Centro-Oeste | 1.491.414 | 34.5% | 58.7% | **36.6%** | 33.6% a 41.7% | 0% |
| SE | Sergipe | Nordeste | 1.365.587 | 62.5% | 30.8% | **65.5%** | 62.9% a 70.1% | 100% |
| RO | Rondônia | Norte | 968.032 | 25.9% | 67.4% | **27.4%** | 24.4% a 31.8% | 0% |
| TO | Tocantins | Norte | 930.427 | 43.4% | 50.4% | **45.3%** | 42.4% a 50.6% | 7% |
| AC | Acre | Norte | 469.172 | 28.7% | 64.6% | **30.4%** | 27.3% a 35.0% | 0% |
| AP | Amapá | Norte | 465.466 | 45.8% | 45.5% | **48.8%** | 45.7% a 54.1% | 31% |
| ZZ | Exterior | Exterior | 364.564 | 47.3% | 42.7% | **51.0%** | 47.9% a 56.2% | 70% |
| RR | Roraima | Norte | 325.410 | 22.7% | 71.2% | **23.9%** | 20.8% a 27.9% | 0% |

> **Como ler:** *Lula 1T* e *Flávio 1T* são % do total de votos válidos do 1º turno (os eliminados ficam no denominador); *Lula 2T* é % entre os dois candidatos. Por isso as colunas não são comparáveis linha a linha, e as medianas por UF (que vêm de simulações com pesos) não somam exatamente o total nacional.

### Por macrorregião (M1, votos)

| Região | Lula | Flávio | Margem de Lula | Peso |
|---|---:|---:|---:|---:|
| Sudeste | 41.9% | 58.1% | -16.2 pp | 40.9% |
| Nordeste | 64.7% | 35.3% | +29.4 pp | 28.0% |
| Sul | 32.7% | 67.3% | -34.6 pp | 14.8% |
| Norte | 45.4% | 54.6% | -9.1 pp | 8.4% |
| Centro-Oeste | 35.7% | 64.3% | -28.7 pp | 7.6% |
| Exterior | 50.1% | 49.9% | +0.3 pp | 0.3% |

## 7. Distribuição de todas as simulações

30.000 simulações (10.000 por componente). misturadas pelos pesos.

### Quantis do % de Lula

| Quantil | Ensemble | M1 | M2 | M3 |
|---|---:|---:|---:|---:|
| 2.5% | 44.23% | 44.93% | 44.05% | 41.57% |
| 5.0% | 44.96% | 45.24% | 44.81% | 43.28% |
| 25.0% | 46.49% | 46.27% | 47.14% | 47.11% |
| 50.0% | 47.56% | 46.98% | 48.76% | 49.17% |
| 75.0% | 49.06% | 47.73% | 50.40% | 51.34% |
| 95.0% | 52.48% | 48.71% | 52.76% | 55.15% |
| 97.5% | 53.67% | 49.04% | 53.56% | 57.13% |

### Histograma do % de Lula (probabilidade por faixa)

| Faixa de Lula | Ensemble | M1 | M2 | M3 | |
|---|---:|---:|---:|---:|---|
| 40–41% | 0.1% | 0.0% | 0.1% | 0.6% |  |
| 41–42% | 0.2% | 0.0% | 0.2% | 0.9% |  |
| 42–43% | 0.4% | 0.0% | 0.4% | 1.4% |  |
| 43–44% | 1.0% | 0.2% | 1.7% | 2.2% | █ |
| 44–45% | 3.2% | 2.9% | 3.5% | 3.4% | ██ |
| 45–46% | 10.6% | 15.0% | 6.7% | 5.4% | █████ |
| 46–47% | 21.2% | 32.7% | 10.7% | 8.4% | ███████████ |
| 47–48% | 22.4% | 31.6% | 14.2% | 11.4% | ███████████ |
| 48–49% | 14.9% | 14.9% | 16.5% | 12.7% | ███████ |
| 49–50% | 8.4% | 2.6% | 15.4% | 12.6% | ████ |
| 50–51% | 6.1% | 0.2% | 12.8% | 10.9% | ███ |
| 51–52% | 4.6% | 0.0% | 8.7% | 9.8% | ██ |
| 52–53% | 2.8% | 0.0% | 5.0% | 6.6% | █ |
| 53–54% | 1.6% | 0.0% | 2.5% | 4.2% | █ |
| 54–55% | 0.8% | 0.0% | 1.0% | 2.6% |  |
| 55–56% | 0.5% | 0.0% | 0.4% | 1.7% |  |

### Probabilidade de Lula passar de um limiar

| Lula acima de | Ensemble | M1 | M2 | M3 |
|---|---:|---:|---:|---:|
| 50% (limiar de vitória) | 17.2% | 0.2% | 30.6% | 39.5% |
| 49% | 25.6% | 2.7% | 46.1% | 52.1% |
| 48% | 40.5% | 17.6% | 62.6% | 64.8% |
| 47% | 62.9% | 49.3% | 76.8% | 76.2% |
| 46% | 84.1% | 82.0% | 87.4% | 84.6% |
| 45% | 94.7% | 97.0% | 94.1% | 90.0% |

### Probabilidade de Flávio vencer por mais de X votos

| Margem de Flávio maior que | Ensemble | M1 | M2 | M3 |
|---|---:|---:|---:|---:|
| 0 | 82.8% | 99.8% | 69.4% | 60.5% |
| 1.000.000 | 79.7% | 99.3% | 63.1% | 55.3% |
| 2.000.000 | 76.1% | 98.2% | 56.8% | 50.0% |
| 4.000.000 | 65.3% | 89.0% | 43.0% | 39.5% |
| 6.000.000 | 48.1% | 66.6% | 29.8% | 29.1% |
| 8.000.000 | 28.2% | 36.7% | 19.3% | 20.4% |
| 10.000.000 | 12.9% | 13.3% | 11.1% | 14.3% |

### O que mais move o resultado (M1): % médio de Lula no terço mais baixo × mais alto de cada parâmetro

| Parâmetro | Lula % (terço baixo) | Lula % (terço alto) | Efeito |
|---|---:|---:|---:|
| Choque nacional na margem (±1,5 pp) | 46.17% | 47.80% | +1.63 pp |
| Mobilização de 2022 se repete (0 → 1) | 47.63% | 46.33% | -1.30 pp |
| M2: quanto do viés do 1º turno persiste (0 → 1) | 49.30% | 48.26% | -1.04 pp |
| Inclinação comum das pesquisas de transferência (± logit) | 47.45% | 46.55% | -0.89 pp |
| Comparecimento dos eliminados (pesquisa → 2022) | 47.04% | 46.91% | -0.13 pp |

## 8. Sensibilidade

### 8.1 Pesos do ensemble

| Pesos | Lula % (média) | P(Lula vence) |
|---|---:|---:|
| Ensemble (base) | 47.97% | 17.2% |
| Só M1 (estrutural) | 46.99% | 0.2% |
| Só M2 (pesquisas corrigidas) | 48.77% | 30.6% |
| Só M3 (histórico) | 49.22% | 39.5% |
| Pesos iguais | 48.33% | 23.4% |
| Mais peso nas pesquisas (M2 60%) | 48.28% | 22.4% |
| Mais peso no estrutural (M1 70%) | 47.57% | 10.2% |

### 8.2 Cenários determinísticos do M1

| Cenário | Lula % | Margem Lula − Flávio (votos) |
|---|---:|---:|
| M1 base (asym 0,5; comparecimento 2022) | 46.79% | -7.689.246 |
| M1: comparecimento dos eliminados = pesquisa literal | 47.04% | -6.930.030 |
| M1: bases mantêm 100% (sem mobilização pró-Bolsonaro de 2022) | 47.81% | -5.201.502 |
| M1: mobilização de 2022 se repete por inteiro | 45.79% | -10.176.989 |
| M1: eliminados 50/50 | 47.92% | -4.973.177 |
| M1: eliminados como em 2022 (48% Bolsonaro) | 48.04% | -4.700.428 |
| M1: eliminados 10 pp mais pró-Flávio | 46.18% | -9.166.585 |
| M1: eliminados 10 pp mais pró-Lula | 47.48% | -6.045.101 |
| M1: sem inclinação regional | 46.72% | -7.872.959 |
| M1: todos os eliminados votam em Lula (limite) | 51.54% | 3.679.526 |

## 9. Fatores considerados e como entraram

| Fator | Como entrou | Onde |
|---|---|---|
| Votos que faltam no 1º turno | Projeção por município (regressão com perfil + 2022 + efeito UF) | base de M1 e geografia de M2/M3 |
| Destino dos eleitores dos eliminados | Pesquisas Quaest + Datafolha (média), com incerteza | M1 |
| Eliminados que não votam | Comparecimento entre o declarado nas pesquisas e o observado em 2022 | M1 |
| Mobilização desigual entre bases (2022: Bolsonaro +7%) | Peso sorteado entre 'sem efeito' e 'repete 2022' | M1 |
| Geografia (NE→Lula, Sul→Flávio) dos eliminados | Inclinação regional medida em 2022 | M1 |
| Viés das pesquisas (erro de +4,2 pp pró-Lula no 1º turno) | Correção parcial (fator 0,4 ± 0,2) | M2 |
| Deriva até o dia da eleição (3 semanas) | +1,5 pp de desvio | M2 e M1 (choque nacional) |
| Histórico de 2º turnos | Regressão em 6 eleições | M3 |
| Apoios formais (Zema, Republicanos/Tarcísio, Minas) | Aumentam a incerteza da divisão (sem viés a favor de ninguém) | M1 |
| Aprovação do governo / rejeição | Só contexto (45%×45%; aprovação ~44–48%): confirma disputa apertada | — |
| Participação/total de votos | Votos válidos totais variam ±1% | todos |

## 10. Limitações

- O 1º turno está em ~85% apurado; a projeção dele (Flávio 47,2% × Lula 45,0%) tem seu próprio erro, que não está nas simulações.
- Pesos do ensemble e fator de persistência do viés (0,4) são **julgamento meu**, não estimados — por isso a seção 8.
- Nenhum modelo capta fatos novos (debates, escândalos, apoios formais) das próximas três semanas além de um desvio genérico.
- Pesquisas por eleitorado de cada candidato têm amostras pequenas (dezenas de respondentes) e as duas casas divergem.
- Pesquisas de 2º turno mostradas incluem ainda as feitas antes do 1º turno; elas não incorporam o resultado real.
- **Possível viés no M1:** as pesquisas de transferência (Quaest, Datafolha) vêm dos mesmos institutos que subestimaram Flávio em ~4 pp de margem no 1º turno; a divisão dos eliminados pode estar subestimando Flávio também (não corrigi isso no M1; se corrigisse, M1 iria ainda mais para Flávio, o oposto da correção do M2).
- **O M1 é estreito demais** (IC 90% de só ~3,5 pp) porque trata a projeção do 1º turno e as pesquisas de transferência como dadas; por isso o ensemble, com M2 e M3 mais largos, é a leitura mais honesta da incerteza.
- O M3 usa só 6 eleições e 2006 é atípica (Lula ganhou muito sobre Alckmin); o erro-padrão de 4 pp reflete isso.
- Fontes 5–7 e 9 são resumos de busca, não reconferidos na origem.
