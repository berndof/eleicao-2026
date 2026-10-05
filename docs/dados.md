# Dicionário de dados

Estrutura de `data/`:

| Pasta | Conteúdo | Versionada? |
|---|---|---|
| `data/raw/` | zips do TSE (votos 2022 e perfil do eleitorado, ~1,1 GB) | não (`make data` baixa de novo) |
| `data/external/` | insumos pequenos de terceiros: malha de UFs do IBGE, wikitext das pesquisas, histórico de 2º turnos, pesquisas de transferência | sim |
| `data/interim/` | tabelas por município geradas a partir dos insumos (apuração 2026, votos 2022, perfil, pesquisas extraídas) | sim |
| `data/processed/` | resultados finais do modelo (usados no artigo e nas figuras) | sim |
| `data/snapshots/` | fotografia dos arquivos gerados em 04/10/2026 ~20h, com ~85% apurado (base do backtest) | sim |

## `data/external/`

| Arquivo | Descrição |
|---|---|
| `ufs_ibge.geojson` | Malha das 27 UFs (IBGE, API de Malhas v3, qualidade mínima). Usada só para os mapas. |
| `wikipedia_pesquisas_2026.wikitext` | Wikitext bruto de *Opinion polling for the 2026 Brazilian presidential election* (Wikipédia EN), baixado em 04/10/2026. CC BY-SA. |
| `historico_2turnos.csv` | 1º e 2º turnos presidenciais 2002–2022: líder e segundo colocado do 1T, % de cada um e % do líder no 2T (votos válidos, TSE). |
| `transferencia_pesquisas.csv` | Pesquisas Quaest e Datafolha de 02–03/10/2026 sobre o voto no 2º turno **por eleitorado de cada candidato eliminado**. Números vindos de resumos de busca (confiança média-baixa; ver coluna `confianca`). |

## `data/interim/`

| Arquivo | Chave | Descrição |
|---|---|---|
| `mun_2026.csv` | `uf`, `cd` | Apuração do 1º turno 2026 por município (TSE): `ts`/`st` seções totais/apuradas, `te`/`est` eleitorado total/apurado, `vv` votos válidos, `vb` brancos, `vn` nulos, `hg` hora de geração do arquivo do TSE e uma coluna `v_<CANDIDATO>` por candidato. |
| `pres_2022_mun.csv`, `pres_2022_t2_mun.csv` | `uf`, `cd` | Votos nominais de Presidente 2022 por município (1º e 2º turno). |
| `perfil_2022_mun.csv`, `perfil_2026_mun.csv` | `uf`, `cd` | Eleitorado por município: `tot` total, `fem` mulheres, `sup` superior completo, `analf` analfabetos/lê-e-escreve, `fund_inc` fundamental incompleto, `jovem` 16–24 anos, `idoso` 60+. |
| `projecao_mun.csv` | `uf`, `cd` | Projeção do 1º turno: votos válidos apurados, votos faltantes estimados e share projetado de Lula e Flávio nos votos faltantes. |
| `pesquisas_1turno.csv`, `pesquisas_2turno.csv` | — | Pesquisas extraídas da Wikipédia. `data_fim` em ISO 8601; valores em % como divulgados. |

Códigos: `cd` é o código do município **no TSE** (não é o código IBGE). `zz` = exterior.

## `data/processed/`

| Arquivo | Descrição |
|---|---|
| `apuracao_meta.json` | Carimbo do arquivo do TSE usado, % de seções/eleitorado apurados, totais nacionais e votos por candidato. |
| `resultado_1turno_uf.csv` | Resultado do 1º turno por UF: válidos, Lula, Flávio, outros, shares e margem em p.p. |
| `resultado_1turno_uf_candidato.csv` | Idem, formato longo (uma linha por UF × candidato). |
| `projecao_1turno_uf.csv`, `projecao_1turno_nacional.json`, `projecao_1turno_coeficientes.csv` | Saída do modelo de 1º turno executado sobre a apuração atual (com ~100% apurado, a "projeção" praticamente reproduz a apuração). |
| `backtest_1turno_uf.csv`, `backtest_1turno.json` | Backtest: parcial (85%) × projeção (85%) × resultado final, por UF e nacional, com erros. |
| `sims_2turno.csv` | 30.000 simulações do 2º turno (10.000 por componente M1/M2/M3): `peso` (para o ensemble), `lula_pct`, margem em votos, e os parâmetros sorteados em cada simulação. |
| `sims_2turno_uf.csv` | % de Lula em cada UF em cada simulação. |
| `tabela_uf_2turno.csv` | Resumo por UF (mediana e IC 90% da % de Lula; P(Lula vence na UF)). |
| `resumo_2turno.json` | Todas as estatísticas usadas no artigo e nas figuras (quantis, limiares, sensibilidade, tornado, cenários, etc.). |

## Como as simulações devem ser lidas

* Cada linha de `sims_2turno.csv` é **um cenário possível**, não uma previsão pontual.
* Estatísticas do ensemble = médias **ponderadas por `peso`** (M1 50%, M2 30%, M3 20%). Esses pesos são julgamento do autor, não estimados — veja a sensibilidade em `resumo_2turno.json` → `sensibilidade_pesos`.
* `lula_pct` é a % de Lula nos votos **válidos do 2º turno** (só Lula e Flávio).
