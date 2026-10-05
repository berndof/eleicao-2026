# Catálogo de fontes

Cada linha é uma fonte de dados, com origem, data de coleta, SHA-256, licença, onde é usada e limitações. A tabela completa está em [`data/fontes/fontes.csv`](../../data/fontes/fontes.csv).

> [!NOTE]
> `status` diz se **conseguimos buscar e conferir** a fonte (`verificada`), só em parte (`parcial`) ou não (`nao_verificada`). `confianca` diz o quanto confiamos no conteúdo.

| Fonte | Publicador | Status | Confiança | Usada em |
|---|---|---|---|---|
| [Auditoria de pesquisas eleitorais contra o registro oficial do TSE (PesqEle)](auditoria_pesquisas.md) | TSE (Dados Abertos) / Análise própria | verificada | alta | data/processed/auditoria_pesquisas.csv; verificação de integridade das pesquisas de 1º e 2 |
| [Diretório de Municípios Brasileiros (TSE, IBGE, SIAFI)](base_dos_dados_municipios.md) | Base dos Dados | verificada | alta | data/external/municipios_chaves.csv; cruzamento entre códigos TSE e IBGE |
| [Expectativas de Mercado (Relatório Focus / Olinda OData)](bcb_focus.md) | Banco Central do Brasil | verificada | alta | data/ledger/observacoes.csv; expectativas point-in-time de inflação, juros, PIB e câmbio |
| [Sistema Gerenciador de Séries Temporais (BCB SGS)](bcb_sgs.md) | Banco Central do Brasil | verificada | alta | data/ledger/observacoes.csv; séries macroeconômicas de conjuntura |
| [Série primária de avaliação, aprovação e rejeição presidencial (Datafolha 2026)](datafolha_aprovacao_rejeicao.md) | Datafolha / G1 / Folha de S.Paulo | verificada | alta | data/external/datafolha_aprovacao_rejeicao.csv; contexto de teto e piso eleitoral de Lula  |
| [Histórico de 1º e 2º turnos presidenciais 2002–2022 (digitado)](historico_2turnos.md) | TSE (votos válidos), digitado à mão | parcial | media | camada 10 (M3): % do líder no 1º e no 2º turno em cada eleição |
| [Indicadores Municipais do Censo Demográfico 2022 (SIDRA/IBGE)](ibge_censo_2022_municipios.md) | IBGE | verificada | alta | data/external/censo2022_mun.csv; análise de perfil sociodemográfico e resíduos do modelo |
| [Malha das 27 UFs (GeoJSON, qualidade mínima)](ibge_malha_ufs.md) | IBGE, API de Malhas v3 | verificada | alta | mapas das figuras (nenhum uso no modelo) |
| [Mercados Regulados de Predição (Kalshi / KXBRPRES-26)](kalshi_eleicao_2026.md) | Kalshi | nao_verificada | baixa | catalogado, nao usado no modelo |
| [Mercados Preditivos da Eleição Presidencial Brasileira (Polymarket)](polymarket_eleicao_2026.md) | Polymarket | verificada | media | data/external/polymarket_mercados_uf.csv e data/ledger/observacoes.csv; apenas calibração  |
| [Pesquisas de transferência de voto Quaest e Datafolha, 02–03/10/2026](transferencia_pesquisas.md) | números vindos de resumos de busca (não da fonte primária) | nao_verificada | baixa | camada 7 (transferência) → M1 |
| [Pesquisas primárias de transferência de votos no 2º turno (Quaest e Datafolha)](transferencia_pesquisas_primaria.md) | Quaest / Datafolha / G1 | verificada | alta | data/external/transferencia_pesquisas_primaria.csv; validação dos parâmetros de migração d |
| [Apuração do 1º turno de 2026 (respostas JSON originais do portal de resultados)](tse_apuracao_2026.md) | TSE (portal de resultados) | verificada | alta | data/interim/mun_2026.csv (coleta anterior, de 23h25 de 04/10, 99,991%); esta coleta está  |
| [Perfil do eleitorado por município (gênero, idade, escolaridade), 2002](tse_perfil_2002.md) | TSE (Dados Abertos) | verificada | alta | data/interim/perfil_2002_mun.csv; tabela municipal em preparação, ainda NÃO entra nos mode |
| [Perfil do eleitorado por município (gênero, idade, escolaridade), 2006](tse_perfil_2006.md) | TSE (Dados Abertos) | verificada | alta | data/interim/perfil_2006_mun.csv; tabela municipal em preparação, ainda NÃO entra nos mode |
| [Perfil do eleitorado por município (gênero, idade, escolaridade), 2010](tse_perfil_2010.md) | TSE (Dados Abertos) | verificada | alta | data/interim/perfil_2010_mun.csv; tabela municipal em preparação, ainda NÃO entra nos mode |
| [Perfil do eleitorado por município (gênero, idade, escolaridade), 2014](tse_perfil_2014.md) | TSE (Dados Abertos) | verificada | alta | data/interim/perfil_2014_mun.csv; tabela municipal em preparação, ainda NÃO entra nos mode |
| [Perfil do eleitorado por município (gênero, idade, escolaridade), 2018](tse_perfil_2018.md) | TSE (Dados Abertos) | verificada | alta | data/interim/perfil_2018_mun.csv; tabela municipal em preparação, ainda NÃO entra nos mode |
| [Perfil do eleitorado por município (gênero, idade, escolaridade), 2022](tse_perfil_2022.md) | TSE (Dados Abertos) | verificada | alta | data/interim/perfil_2022_mun.csv; features de escolaridade, idade e gênero do M1 |
| [Perfil do eleitorado por município (gênero, idade, escolaridade), 2026](tse_perfil_2026.md) | TSE (Dados Abertos) | verificada | alta | data/interim/perfil_2026_mun.csv; features de escolaridade, idade e gênero do M1 |
| [Prefeitos Eleitos nas Eleições Municipais de 2024](tse_prefeitos_2024.md) | TSE (Dados Abertos) | verificada | alta | data/external/prefeitos_2024_mun.csv; indicador de força partidária local e alinhamento po |
| [Registro de pesquisas eleitorais 2026 (TSE) - Presidente, com contratante e pagante](tse_registro_pesquisas_2026.md) | Tribunal Superior Eleitoral (dados abertos) | verificada | alta | auditoria de proveniencia das pesquisas (data/processed/auditoria_pesquisas.csv); nao entr |
| [Votação por candidato × zona × município, todos os cargos, 2002](tse_votos_2002.md) | TSE (Dados Abertos) | verificada | alta | data/interim/pres_2002_mun.csv e pres_2002_t2_mun.csv (filtro Presidente); tabela municipa |
| [Votação por candidato × zona × município, todos os cargos, 2006](tse_votos_2006.md) | TSE (Dados Abertos) | verificada | alta | data/interim/pres_2006_mun.csv e pres_2006_t2_mun.csv (filtro Presidente); tabela municipa |
| [Votação por candidato × zona × município, todos os cargos, 2010](tse_votos_2010.md) | TSE (Dados Abertos) | verificada | alta | data/interim/pres_2010_mun.csv e pres_2010_t2_mun.csv (filtro Presidente); tabela municipa |
| [Votação por candidato × zona × município, todos os cargos, 2014](tse_votos_2014.md) | TSE (Dados Abertos) | verificada | alta | data/interim/pres_2014_mun.csv e pres_2014_t2_mun.csv (filtro Presidente); tabela municipa |
| [Votação por candidato × zona × município, todos os cargos, 2018](tse_votos_2018.md) | TSE (Dados Abertos) | verificada | alta | data/interim/pres_2018_mun.csv e pres_2018_t2_mun.csv (filtro Presidente); tabela municipa |
| [Votação por candidato × zona × município, todos os cargos, 2022](tse_votos_2022.md) | TSE (Dados Abertos) | verificada | alta | data/interim/pres_2022_mun.csv e pres_2022_t2_mun.csv (filtro Presidente); base do M1 (swi |
| [Opinion polling for the 2026 Brazilian presidential election (wikitext)](wikipedia_pesquisas_2026.md) | Wikipédia (EN), contribuidores | parcial | media | data/interim/pesquisas_1turno.csv e pesquisas_2turno.csv: M2 (2º turno), viés do 1º turno  |
