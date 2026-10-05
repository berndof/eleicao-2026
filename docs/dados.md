# Dicionário de dados

Estrutura de `data/`:

| Pasta | Conteúdo | Versionada? |
|---|---|---|
| `data/raw/` | brutos do TSE (votos 2022 e perfil do eleitorado, ~1,1 GB; JSON originais da apuração) | não no git; **publicados na [release de dados brutos](https://github.com/berndof/eleicao-2026/releases/tag/dados-brutos-2026-10-04)** (`make fetch-raw` baixa e confere) |
| `data/external/` | insumos pequenos de terceiros: malha de UFs do IBGE, wikitext das pesquisas, histórico de 2º turnos, pesquisas de transferência | sim |
| `data/interim/` | tabelas por município geradas a partir dos insumos (apuração 2026, votos 2022, perfil, pesquisas extraídas) | sim |
| `data/processed/` | resultados finais do modelo (usados no artigo e nas figuras) | sim |
| `data/snapshots/` | fotografia dos arquivos gerados em 04/10/2026 ~20h, com ~85% apurado (base do backtest) | sim |

## Dados brutos

Os arquivos brutos (exatamente como o TSE publicou) são pesados demais para o git; estão numa **release do GitHub**, com somas de verificação:

| Arquivo | Tamanho | O que é | Origem |
|---|---:|---|---|
| `votacao_candidato_munzona_2022.zip` | 642 MB | votos por candidato × zona × município, todos os cargos de 2022 | [download direto](https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2022.zip) |
| `perfil_eleitorado_2022.zip` | 77 MB | eleitorado 2022 por município × gênero × idade × escolaridade | [download direto](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2022.zip) |
| `perfil_eleitorado_2026.zip` | 408 MB | idem, 2026 | [download direto](https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_2026.zip) |
| `tse_apuracao_20261005.tar.gz` | 2,7 MB | as **5.759 respostas JSON originais** do portal de resultados (5.757 municípios + nacional + configuração), coletadas às 00:11 de 05/10/2026 (99,997% das seções) | `resultados.tse.jus.br` |
| `SHA256SUMS.txt` | | somas SHA-256 dos arquivos acima | |

```bash
make fetch-raw     # baixa tudo de data/raw/ da release e confere o SHA-256
make data          # (alternativa) baixa direto do TSE e gera as tabelas por município
```

> [!NOTE]
> O `tse_apuracao_20261005.tar.gz` é de uma coleta **posterior** à que gerou `data/interim/mun_2026.csv` (23h25 de 04/10, 99,991%). A coleta de 05/10 também está convertida em `data/snapshots/20261005_apuracao_final/mun_2026.csv`, e as duas diferem em ~0,006% do eleitorado. Os modelos publicados usam a de 04/10; a diferença é desprezível para os resultados.

Os dados do TSE são públicos (Dados Abertos); mantenha a atribuição ao TSE. Os JSON podem ser relidos com `python -m eleicao2026.collect.tse_apuracao --save-raw ...` (que também grava os brutos).

## `data/external/`

| Arquivo | Descrição |
|---|---|
| `ufs_ibge.geojson` | Malha das 27 UFs (IBGE, API de Malhas v3, qualidade mínima). Usada só para os mapas. |
| `municipios_chaves.csv` | De-para de chaves municipais para 5.571 municípios: TSE (`cd`), IBGE-7, IBGE-6, SIAFI/RFB, nome e UF (100% de junção com dados de apuração). |
| `censo2022_mun.csv`, `censo2022_dicionario.csv` | Variáveis socioeconômicas e demográficas do **Censo 2022** (IBGE SIDRA): religião (% evangélica, católica, sem religião), renda per capita média/mediana, raça e urbanização. |
| `prefeitos_2024_mun.csv` | Partido e votação dos prefeitos eleitos em 2024 (TSE Dados Abertos) em 5.552 municípios. |
| `registro_pesquisas_presidente_2026.csv` | Registro oficial de pesquisas presidenciais no TSE (PesqEle 2026): número de protocolo, empresa, CNPJ, datas, custo declarado, amostra e contratante. |
| `transferencia_pesquisas_primaria.csv` | Votos de 2º turno dos eliminados conferidos diretamente nos relatórios e publicações primárias (Quaest e Datafolha). |
| `datafolha_aprovacao_rejeicao.csv` | Séries temporais primárias de avaliação de governo e rejeição de candidatos registradas pelo Datafolha ao longo de 2025–2026. |
| `economia_resumo.csv` | Resumo dos principais indicadores macroeconômicos (BCB SGS e Focus): IPCA, Selic, Câmbio, PIB, desemprego PNAD e IBC-Br. |
| `polymarket_mercados_uf.csv` | Cotações e resoluções dos mercados estaduais e nacional no Polymarket. |
| `wikipedia_pesquisas_2026.wikitext`, `wikipedia_pesquisas_2026.revisao.json` | Wikitext bruto com fixação de procedência (oldid `1378579188` no MediaWiki). |
| `historico_2turnos.csv` | 1º e 2º turnos presidenciais 2002–2022: líder e segundo colocado do 1T, % de cada um e % do líder no 2T (votos válidos, TSE). |
| `transferencia_pesquisas.csv` | Pesquisas Quaest e Datafolha de 02–03/10/2026 sobre o voto no 2º turno **por eleitorado de cada candidato eliminado** (versão preliminar). |

## `data/ledger/`

| Arquivo | Descrição |
|---|---|
| `observacoes.csv` | Livro-razão (*ledger*) estruturado append-only com mais de 4.000 observações de séries temporais econômicas e mercados preditivos. Registra explicitamente o período de referência, a data de divulgação (`divulgado_em`) e data de coleta (`coletado_em`), impedindo vazamento temporal em backtests. |

## `data/interim/`

| Arquivo | Chave | Descrição |
|---|---|---|
| `mun_2026.csv` | `uf`, `cd` | Apuração do 1º turno 2026 por município (TSE): `ts`/`st` seções totais/apuradas, `te`/`est` eleitorado total/apurado, `vv` votos válidos, `vb` brancos, `vn` nulos, `hg` hora de geração do arquivo do TSE e uma coluna `v_<CANDIDATO>` por candidato. |
| `pres_AAAA_mun.csv`, `pres_AAAA_t2_mun.csv` (AAAA = 2002, 2006, 2010, 2014, 2018, 2022) | `uf`, `cd` | Votos nominais de Presidente por município (1º e 2º turno). 2002–2018 vêm de `make data-historico`. |
| `perfil_AAAA_mun.csv` (2002–2018, 2022, 2026) | `uf`, `cd` | Eleitorado por município: `tot` total, `fem` mulheres, `sup` superior completo, `analf` analfabetos/lê-e-escreve, `fund_inc` fundamental incompleto, `jovem` 16–24 anos, `idoso` 60+. **Em 2002 e 2006 o TSE não informa a faixa etária (código `-3`): `jovem` e `idoso` são 0 nesses anos e não devem ser usados.** |
| `pres_candidatos.csv` | `ano`, `turno`, `candidato` | **Todos** os candidatos a Presidente de 2002 a 2022: nome, partido, situação, votos nominais no Brasil e `pct_validos`. Gerado dos dados abertos do TSE; reproduz, ao centésimo, os números de `historico_2turnos.csv` (digitado à mão) nos seis anos. |
| `projecao_mun.csv` | `uf`, `cd` | Projeção do 1º turno: votos válidos apurados, votos faltantes estimados e share projetado de Lula e Flávio nos votos faltantes. |
| `pesquisas_1turno.csv`, `pesquisas_2turno.csv` | — | Pesquisas extraídas da Wikipédia (1º turno: 56; 2º turno: 56). `data_fim` em ISO 8601; valores em % como divulgados. A linha "Results" da página (o resultado da urna) **não** é incluída. |

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
| `influencia_2turno.csv`, `influencia_1turno.csv` | Cada pesquisa de 2º / 1º turno: se entra no modelo (e se não, por quê), peso e efeito de removê-la (método leave-one-out). Ver [pesquisas.pt.md](pesquisas.pt.md). |
| `influencia_transf.csv`, `influencia_historico.csv` | Idem para as pesquisas de transferência (por candidato eliminado) e para cada eleição histórica. |
| `influencia.json` | Resumo: forma fechada do M2/M3 × simulado, cenários de hipótese. |
| `exemplo_municipio.json`, `exemplo_uf.json`, `m1_decomposicao.json` | Números dos exemplos "passo a passo" de [camadas.pt.md](camadas.pt.md) (Caruaru, Minas Gerais, decomposição nacional do M1). |
| `auditoria_pesquisas.csv` | Auditoria completa das 112 pesquisas eleitorais (1T e 2T): correspondência exata com o registro do TSE PesqEle, protocolo oficial, divergências de tamanho amostral, custos e empresas contratantes/pagantes. |
| `calibracao_shrinkage.json` | Calibração empírica ex-post do hiperparâmetro de encolhimento $K_{\text{shrink}}$ e corte de apuração contra a apuração final 100%. |
| `resumo_v2_m1.json` | Simulações do modelo estrutural V2 incorporando o Censo 2022 (religião e renda) e Prefeitos 2024 (máquina municipal). |
| `resumo_v2_m2.json` | Síntese de pesquisas V2 com pesos individuais calibrados pelo erro do 1T auditado no TSE e tamanho amostral. |
| `comparativo_modelos_v1_v2.json` | Tabela lado a lado comparando V1 baseline e V2, com pesos de mínima variância de Markowitz para o ensemble. |
| `backtest_1turno_v2.json` | Backtest ex-post no snapshot das 20h comparando o parcial puro contra as projeções V1 e V2. |

> Todas as 29 fontes primárias e secundárias do projeto estão catalogadas com fichas individuais de metadados, links diretos, somas SHA-256 e licenças em [docs/fontes/](fontes/).

## Como as simulações devem ser lidas

* Cada linha de `sims_2turno.csv` é **um cenário possível**, não uma previsão pontual.
* Estatísticas do ensemble = médias **ponderadas por `peso`** (M1 50%, M2 30%, M3 20%). Esses pesos são julgamento do autor, não estimados — veja a sensibilidade em `resumo_2turno.json` → `sensibilidade_pesos`.
* `lula_pct` é a % de Lula nos votos **válidos do 2º turno** (só Lula e Flávio).
