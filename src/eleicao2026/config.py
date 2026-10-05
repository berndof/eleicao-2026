"""Configuração central: caminhos, constantes e dicionários usados por todo o pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"                # insumos pesados baixados do TSE (ignorados pelo git)
EXTERNAL = DATA / "external"      # insumos pequenos de terceiros (malha IBGE, wikitext de pesquisas)
INTERIM = DATA / "interim"        # tabelas intermediárias (por município)
PROCESSED = DATA / "processed"    # saídas finais, versionadas
SNAPSHOTS = DATA / "snapshots"    # fotografias de execuções anteriores (usadas no backtest)
FIGURES = ROOT / "figures"
DOCS = ROOT / "docs"

# --- TSE ------------------------------------------------------------------------------------
# Eleição ordinária 2026, 1º turno = código 6257 (portal resultados.tse.jus.br)
TSE_ELE = "6257"
TSE_BASE = f"https://resultados.tse.jus.br/oficial/ele2026/{TSE_ELE}"
TSE_CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"
UA = {"User-Agent": "Mozilla/5.0 (pesquisa academica; github.com/berndof/eleicao-2026)"}

# Snapshot de referência: projeção feita com ~85% apurado, em 04/10/2026 às ~20h
SNAPSHOT_85 = SNAPSHOTS / "20261004_2005_apuracao85"

# --- Candidatos (nome de urna, como no TSE) ---------------------------------------------------
LULA, FLAV = "LULA", "FLAVIO BOLSONARO"
BOLSONARO_2022 = "JAIR BOLSONARO"

# --- Geografia -------------------------------------------------------------------------------
REG = {
    "Norte": "ac ap am pa ro rr to",
    "Nordeste": "al ba ce ma pb pe pi rn se",
    "Centro-Oeste": "df go ms mt",
    "Sudeste": "es mg rj sp",
    "Sul": "pr rs sc",
    "Exterior": "zz",
}
UF2REG = {u: r for r, us in REG.items() for u in us.split()}
UFN = {"ac": "Acre", "al": "Alagoas", "am": "Amazonas", "ap": "Amapá", "ba": "Bahia", "ce": "Ceará",
       "df": "Distrito Federal", "es": "Espírito Santo", "go": "Goiás", "ma": "Maranhão",
       "mg": "Minas Gerais", "ms": "Mato Grosso do Sul", "mt": "Mato Grosso", "pa": "Pará",
       "pb": "Paraíba", "pe": "Pernambuco", "pi": "Piauí", "pr": "Paraná", "rj": "Rio de Janeiro",
       "rn": "Rio Grande do Norte", "ro": "Rondônia", "rr": "Roraima", "rs": "Rio Grande do Sul",
       "sc": "Santa Catarina", "se": "Sergipe", "sp": "São Paulo", "to": "Tocantins", "zz": "Exterior"}
# código IBGE de cada UF (para casar com a malha do IBGE)
UF_IBGE = {"ro": 11, "ac": 12, "am": 13, "rr": 14, "pa": 15, "ap": 16, "to": 17, "ma": 21, "pi": 22,
           "ce": 23, "rn": 24, "pb": 25, "pe": 26, "al": 27, "se": 28, "ba": 29, "mg": 31, "es": 32,
           "rj": 33, "sp": 35, "pr": 41, "sc": 42, "rs": 43, "ms": 50, "mt": 51, "go": 52, "df": 53}

# Cores consistentes em todos os gráficos
COR = {"lula": "#c1272d", "flavio": "#1f5fa8", "outros": "#8a8a8a", "neutro": "#444444",
       "M1": "#2a9d8f", "M2": "#e9a23b", "M3": "#7b5ea7", "ens": "#222222"}
