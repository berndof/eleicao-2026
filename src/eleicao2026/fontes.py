#!/usr/bin/env python3
"""Catálogo de fontes: junta as entradas de `data/fontes/entradas/*.json` em uma tabela e em páginas.

Cada fonte tem uma entrada JSON (as do TSE/Wikipédia/IBGE já usadas pelo pipeline são geradas aqui, a
partir dos próprios arquivos, com tamanho e SHA-256 calculados na hora; as demais são gravadas pelos
coletores novos). Este módulo só lê e organiza, nunca baixa nada.

Gera:
  data/fontes/entradas/<id>.json   (apenas as das fontes já existentes; `--existentes`)
  data/fontes/fontes.csv           tabela única (todas as fontes)
  docs/fontes/<id>.md              uma página por fonte
  docs/fontes/README.md            índice navegável

Uso: python -m eleicao2026.fontes [--existentes] [--montar]   (sem opções faz as duas coisas)
"""
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from eleicao2026 import config as C
from eleicao2026.ledger import sha256_arquivo

ENTRADAS = C.DATA / "fontes" / "entradas"
TABELA = C.DATA / "fontes" / "fontes.csv"
PAGINAS = C.DOCS / "fontes"

CAMPOS = ["id", "nome", "publicador", "url_origem", "url_landing", "coletado_em", "sha256",
          "tamanho_bytes", "licenca", "granularidade", "periodo", "confianca", "status",
          "camada", "usado_em", "limitacoes", "arquivo_local", "url_copia"]

CDN = C.TSE_CDN
RELEASE = "https://github.com/berndof/eleicao-2026/releases/download/dados-brutos-2026-10-04"
CKAN = "https://dadosabertos.tse.jus.br/dataset"
LIC_TSE = "CC-BY (campo license_id do CKAN dos Dados Abertos do TSE, conferido em 05/10/2026)"


def _mtime(caminho):
    return datetime.fromtimestamp(Path(caminho).stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _arquivo(caminho):
    p = Path(caminho)
    if not p.exists():
        return {"sha256": "", "tamanho_bytes": "", "coletado_em": ""}
    return {"sha256": sha256_arquivo(p), "tamanho_bytes": p.stat().st_size, "coletado_em": _mtime(p)}


def existentes():
    """Entradas das fontes que o pipeline já usa. Os campos de arquivo vêm do próprio arquivo local."""
    ent = []
    for ano in (2002, 2006, 2010, 2014, 2018, 2022):
        arq = C.RAW / f"votacao_candidato_munzona_{ano}.zip"
        e = {
            "id": f"tse_votos_{ano}",
            "nome": f"Votação por candidato × zona × município, todos os cargos, {ano}",
            "publicador": "TSE (Dados Abertos)",
            "url_origem": f"{CDN}/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip",
            "url_landing": f"{CKAN}/resultados-{ano}",
            "licenca": LIC_TSE, "granularidade": "zona eleitoral × município × candidato",
            "periodo": f"eleição de {ano}", "confianca": "alta", "status": "verificada",
            "camada": "1 (dados brutos) → 2 (tabelas municipais)",
            "usado_em": (f"data/interim/pres_{ano}_mun.csv e pres_{ano}_t2_mun.csv (filtro Presidente); "
                         + ("base do M1 (swing 2022→2026)" if ano == 2022
                            else "tabela municipal em preparação; ainda NÃO entra nos modelos publicados "
                                 "(o M3 usa só o histórico nacional digitado, historico_2turnos)")),
            "limitacoes": "Contém todos os cargos; só Presidente é usado. Votos nominais, sem brancos e nulos. "
                          "Formato de colunas varia entre anos (2014 tem menos colunas).",
            "arquivo_local": f"data/raw/{arq.name}",
            "url_copia": f"{RELEASE}/{arq.name}" if ano in (2022,) else "",
        }
        e.update(_arquivo(arq))
        ent.append(e)
    for ano in (2002, 2006, 2010, 2014, 2018, 2022, 2026):
        arq = C.RAW / f"perfil_eleitorado_{ano}.zip"
        e = {
            "id": f"tse_perfil_{ano}",
            "nome": f"Perfil do eleitorado por município (gênero, idade, escolaridade), {ano}",
            "publicador": "TSE (Dados Abertos)",
            "url_origem": f"{CDN}/perfil_eleitorado/perfil_eleitorado_{ano}.zip",
            "url_landing": f"{CKAN}/eleitorado-{ano}",
            "licenca": LIC_TSE, "granularidade": "município × gênero × faixa etária × escolaridade",
            "periodo": f"eleitorado de {ano}", "confianca": "alta", "status": "verificada",
            "camada": "1 (dados brutos) → 3 (features)",
            "usado_em": (f"data/interim/perfil_{ano}_mun.csv; features de escolaridade, idade e gênero do M1"
                         if ano in (2022, 2026) else
                         f"data/interim/perfil_{ano}_mun.csv; tabela municipal em preparação, "
                         "ainda NÃO entra nos modelos publicados"),
            "limitacoes": ("Em 2002 e 2006 a faixa etária vem como código -3 (não informada): 'jovem' e 'idoso' "
                           "não devem ser usados nesses anos." if ano in (2002, 2006) else
                           "Perfil de quem pode votar, não de quem votou."),
            "arquivo_local": f"data/raw/{arq.name}",
            "url_copia": f"{RELEASE}/{arq.name}" if ano in (2022, 2026) else "",
        }
        e.update(_arquivo(arq))
        ent.append(e)

    tar = C.RAW / "tse_apuracao_20261005.tar.gz"
    e = {
        "id": "tse_apuracao_2026",
        "nome": "Apuração do 1º turno de 2026 (respostas JSON originais do portal de resultados)",
        "publicador": "TSE (portal de resultados)",
        "url_origem": C.TSE_BASE, "url_landing": "https://resultados.tse.jus.br",
        "licenca": "nao_verificada (portal de resultados; os Dados Abertos do TSE são CC-BY)",
        "granularidade": "município (5.757 respostas, mais a nacional e a configuração)",
        "periodo": "coleta de 05/10/2026 00:11, 99,997% das seções",
        "confianca": "alta", "status": "verificada",
        "camada": "1 (dados brutos) → 2 (tabelas municipais)",
        "usado_em": "data/interim/mun_2026.csv (coleta anterior, de 23h25 de 04/10, 99,991%); esta coleta está em "
                    "data/snapshots/20261005_apuracao_final/. Base do M1 e do backtest",
        "limitacoes": "Os modelos publicados usam a coleta de 04/10, não esta; a diferença é de ~0,006% do eleitorado.",
        "arquivo_local": "data/raw/tse_apuracao_20261005.tar.gz",
        "url_copia": f"{RELEASE}/tse_apuracao_20261005.tar.gz",
    }
    e.update(_arquivo(tar))
    ent.append(e)

    wk = C.EXTERNAL / "wikipedia_pesquisas_2026.wikitext"
    rev = C.EXTERNAL / "wikipedia_pesquisas_2026.revisao.json"
    e = {
        "id": "wikipedia_pesquisas_2026",
        "nome": "Opinion polling for the 2026 Brazilian presidential election (wikitext)",
        "publicador": "Wikipédia (EN), contribuidores",
        "url_origem": "https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election",
        "url_landing": "https://en.wikipedia.org/wiki/Opinion_polling_for_the_2026_Brazilian_presidential_election",
        "licenca": "CC BY-SA (rodapé da Wikipédia)", "granularidade": "pesquisa (instituto × período de campo)",
        "periodo": "pesquisas de 2025 e 2026 até 04/10/2026", "confianca": "media", "status": "parcial",
        "camada": "1 (dados brutos) → 7 (pesquisas)",
        "usado_em": "data/interim/pesquisas_1turno.csv e pesquisas_2turno.csv: M2 (2º turno), viés do 1º turno (camada 6)",
        "limitacoes": "Fonte secundária e editável por qualquer pessoa. Cada pesquisa deve ser auditada contra o registro do "
                      "TSE (data/processed/auditoria_pesquisas.csv). Sem coluna de método ou contratante.",
        "arquivo_local": "data/external/wikipedia_pesquisas_2026.wikitext", "url_copia": "",
    }
    e.update(_arquivo(wk))
    if rev.exists():
        r = json.loads(rev.read_text(encoding="utf-8"))
        e["url_origem"] = r.get("permalink") or e["url_origem"]
        e["periodo"] += f" (revisão {r.get('oldid')}, {r.get('timestamp')}, correspondência: {r.get('match', '?')})"
        if r.get("match") not in ("exata", "exact", True):
            e["limitacoes"] += " Revisão exata não confirmada; ver o .revisao.json."
    else:
        e["limitacoes"] += " ID da revisão ainda não registrado."
    ent.append(e)

    for id_, nome, arq, org, land, lic, gran, per, conf, st, usado, lim in [
        ("historico_2turnos", "Histórico de 1º e 2º turnos presidenciais 2002–2022 (digitado)",
         "historico_2turnos.csv", "TSE (votos válidos), digitado à mão",
         "https://resultados.tse.jus.br", "nao_verificada", "nacional", "2002–2022", "media", "parcial",
         "camada 10 (M3): % do líder no 1º e no 2º turno em cada eleição",
         "Digitado, mas data/interim/pres_candidatos.csv, gerado dos dados abertos do TSE, reproduz os números ao centésimo."),
        ("transferencia_pesquisas", "Pesquisas de transferência de voto Quaest e Datafolha, 02–03/10/2026",
         "transferencia_pesquisas.csv", "números vindos de resumos de busca (não da fonte primária)",
         "", "nao_verificada", "por eleitorado de candidato eliminado", "02–03/10/2026", "baixa", "nao_verificada",
         "camada 7 (transferência) → M1",
         "Resumos de busca já erraram em outros casos. Em substituição pela fonte primária "
         "(transferencia_pesquisas_primaria.csv)."),
        ("ibge_malha_ufs", "Malha das 27 UFs (GeoJSON, qualidade mínima)", "ufs_ibge.geojson",
         "IBGE, API de Malhas v3", "https://servicodados.ibge.gov.br/api/docs/malhas",
         "nao_verificada (dado público do IBGE)", "UF", "2022", "alta", "verificada",
         "mapas das figuras (nenhum uso no modelo)", "Qualidade mínima: só para desenhar mapas."),
    ]:
        arq = C.EXTERNAL / arq
        e = {"id": id_, "nome": nome, "publicador": org, "url_origem": land, "url_landing": land,
             "licenca": lic, "granularidade": gran, "periodo": per, "confianca": conf, "status": st,
             "camada": "—", "usado_em": usado, "limitacoes": lim,
             "arquivo_local": str(arq.relative_to(C.ROOT)), "url_copia": ""}
        e.update(_arquivo(arq))
        ent.append(e)
    return ent


def gravar_existentes():
    ENTRADAS.mkdir(parents=True, exist_ok=True)
    n = 0
    for e in existentes():
        (ENTRADAS / f"{e['id']}.json").write_text(json.dumps(e, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        n += 1
    return n


def ler_entradas():
    out = []
    for p in sorted(ENTRADAS.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        d.setdefault("id", p.stem)
        out.append(d)
    return out


def _texto(v):
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return "" if v is None else str(v)


def montar():
    ent = ler_entradas()
    TABELA.parent.mkdir(parents=True, exist_ok=True)
    extras = sorted({k for e in ent for k in e} - set(CAMPOS))
    with open(TABELA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS + extras)
        w.writeheader()
        for e in ent:
            w.writerow({k: _texto(e.get(k)) for k in CAMPOS + extras})
    PAGINAS.mkdir(parents=True, exist_ok=True)
    for e in ent:
        (PAGINAS / f"{e['id']}.md").write_text(pagina(e, extras), encoding="utf-8")
    (PAGINAS / "README.md").write_text(indice(ent), encoding="utf-8")
    return len(ent)


def _link(url):
    return f"[{url}]({url})" if str(url).startswith("http") else (url or "—")


def pagina(e, extras=()):
    sha = _texto(e.get("sha256")) or "—"
    linhas = [f"# {e.get('nome', e['id'])}", "", f"`{e['id']}` · status: **{e.get('status', '—')}** · confiança: **{e.get('confianca', '—')}**", "",
              "| Campo | Valor |", "|---|---|"]
    rot = [("publicador", "Publicador"), ("url_origem", "Origem"), ("url_landing", "Página da fonte"),
           ("url_copia", "Cópia neste projeto (release)"), ("arquivo_local", "Arquivo local"),
           ("coletado_em", "Coletado em (UTC)"), ("tamanho_bytes", "Tamanho (bytes)"),
           ("licenca", "Licença"), ("granularidade", "Granularidade"), ("periodo", "Período"),
           ("camada", "Camada da análise")]
    for k, r in rot:
        v = _texto(e.get(k))
        linhas.append(f"| {r} | {_link(v) if k.startswith('url_') else (v or '—')} |")
    linhas.append(f"| SHA-256 | `{sha}` |" if sha != "—" else "| SHA-256 | — |")
    for k in extras:
        if e.get(k):
            linhas.append(f"| {k} | {_texto(e.get(k))} |")
    linhas += ["", "## Onde é usada", "", _texto(e.get("usado_em")) or "—", "",
               "## Limitações", "", _texto(e.get("limitacoes")) or "—", ""]
    if sha != "—" and e.get("arquivo_local"):
        linhas += ["## Como conferir", "", "```bash", f"sha256sum {e['arquivo_local']}", "```", ""]
    return "\n".join(linhas)


def indice(ent):
    linhas = ["# Catálogo de fontes", "",
              "Cada linha é uma fonte de dados, com origem, data de coleta, SHA-256, licença, onde é usada e limitações. "
              "A tabela completa está em [`data/fontes/fontes.csv`](../../data/fontes/fontes.csv).", "",
              "> [!NOTE]", "> `status` diz se **conseguimos buscar e conferir** a fonte (`verificada`), só em parte "
              "(`parcial`) ou não (`nao_verificada`). `confianca` diz o quanto confiamos no conteúdo.", "",
              "| Fonte | Publicador | Status | Confiança | Usada em |", "|---|---|---|---|---|"]
    for e in ent:
        linhas.append(f"| [{e.get('nome', e['id'])}]({e['id']}.md) | {_texto(e.get('publicador'))} | "
                      f"{_texto(e.get('status'))} | {_texto(e.get('confianca'))} | "
                      f"{_texto(e.get('usado_em'))[:90]} |")
    linhas.append("")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--existentes", action="store_true", help="gera as entradas das fontes já usadas")
    ap.add_argument("--montar", action="store_true", help="monta fontes.csv e docs/fontes/")
    a = ap.parse_args()
    tudo = not (a.existentes or a.montar)
    if a.existentes or tudo:
        print(f"{gravar_existentes()} entradas de fontes existentes gravadas")
    if a.montar or tudo:
        print(f"{montar()} fontes no catálogo")


if __name__ == "__main__":
    main()
