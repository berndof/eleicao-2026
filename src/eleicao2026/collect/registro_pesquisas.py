#!/usr/bin/env python3
"""Coleta o registro de pesquisas eleitorais 2026 do TSE (Presidente) e junta contratante/pagante.

Fonte primária: dados abertos do TSE, conjunto "Pesquisas Eleitorais - 2026"
  https://dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026
Arquivos (CDN do TSE, ZIP com CSV ';' em latin-1, texto longo entre aspas):
  pesquisa_eleitoral_2026.zip   uma linha por registro (NR_PROTOCOLO_REGISTRO) e abrangência
  pesquisa_contratante_2026.zip uma linha por (protocolo, contratante): nome, CPF/CNPJ, valor pago
  pesquisa_pagante_2026.zip     uma linha por (protocolo, contratante): pagante e origem do recurso
As duas tabelas auxiliares casam com a principal por NR_PROTOCOLO_REGISTRO (e entre si por
(NR_PROTOCOLO_REGISTRO, CD_CONTRATANTE)). Os arquivos são regenerados diariamente: por isso o
carimbo de coleta e o `Last-Modified` do servidor ficam registrados.

Gera:
  data/raw/tse_pesquisas_2026/*.zip           bytes originais (git-ignorado) + manifesto.json (sha256, tamanho,
                                              URL, coletado_em, Last-Modified) + ckan_package_show.json
  data/external/registro_pesquisas_presidente_2026.csv   um registro por protocolo com DS_CARGO ~ 'Presidente'
  data/external/registro_pesquisas_presidente_2026.meta.json
  data/fontes/entradas/tse_registro_pesquisas_2026.json   entrada de catálogo

Privacidade: nada de pessoa física é gravado. Contratante/pagante com CPF (11 dígitos) vira a categoria
`pessoa_fisica`; o estatístico responsável (nome/CONRE) não é copiado; só entram pessoas jurídicas.
A margem de erro vem do TEXTO do plano amostral (regex); sem texto reconhecível fica vazia, com
`margem_origem` = 'ausente'. O texto completo da metodologia não é copiado (só o tamanho).

Uso: python -m eleicao2026.collect.registro_pesquisas [--no-download]
Somente biblioteca padrão.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import zipfile
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from eleicao2026 import config as C

DATASET = "https://dadosabertos.tse.jus.br/dataset/pesquisas-eleitorais-2026"
CKAN = "https://dadosabertos.tse.jus.br/api/3/action/package_show?id=pesquisas-eleitorais-2026"
BASE = C.TSE_CDN + "/pesquisa_eleitoral"
ARQUIVOS = {  # nome do zip -> CSV nacional dentro do zip
    "pesquisa_eleitoral_2026": "pesquisa_eleitoral_2026_BRASIL.csv",
    "pesquisa_contratante_2026": "pesquisa_contratante_2026_BRASIL.csv",
    "pesquisa_pagante_2026": "pesquisa_pagante_2026_BRASIL.csv",
}
FONTE_ID = "tse_registro_pesquisas_2026"
RAW_DIR = C.RAW / "tse_pesquisas_2026"
MANIFESTO = RAW_DIR / "manifesto.json"
SAIDA = C.EXTERNAL / "registro_pesquisas_presidente_2026.csv"
META = C.EXTERNAL / "registro_pesquisas_presidente_2026.meta.json"
ENTRADA = C.DATA / "fontes" / "entradas" / f"{FONTE_ID}.json"

COLUNAS = ["protocolo", "uf", "empresa", "empresa_fantasia", "cnpj", "pesquisa_propria", "data_registro",
           "data_inicio", "data_fim", "data_divulgacao", "amostra", "custo", "margem_erro_pp", "margem_origem",
           "margem_teorica_aas_pp", "abrangencia_texto", "plano_amostral_len", "metodologia_len",
           "contratantes", "pagantes", "origem_recurso", "tse_dt_geracao"]

# número seguido (opcionalmente de um "(dois vírgula dois)") de %, "pontos", "p.p." ou "pp"
_NUM = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:\([^)]{0,60}\))?\s*(?:%|pontos?\b|p\.\s?p\.?|pp\b)", re.I)


def agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def escrever_entrada(entrada, caminho=None):
    """Grava uma entrada de catálogo (JSON) com as chaves obrigatórias, sem sobrescrever nada além do próprio id."""
    chaves = ["id", "nome", "publicador", "url_origem", "url_landing", "coletado_em", "sha256", "tamanho_bytes",
              "licenca", "granularidade", "periodo", "confianca", "status", "usado_em", "limitacoes"]
    faltam = [k for k in chaves if k not in entrada]
    if faltam:
        raise ValueError(f"entrada de catálogo sem chaves: {faltam}")
    caminho = caminho or (C.DATA / "fontes" / "entradas" / f"{entrada['id']}.json")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps({k: entrada[k] for k in chaves} | {k: v for k, v in entrada.items()
                                                                       if k not in chaves},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho


# --- parsing --------------------------------------------------------------------------------------
def nulo(v):
    """'#NULO#' (em branco no banco do TSE) e '-1' viram vazio."""
    v = (v or "").strip()
    return "" if v in ("#NULO#", "#NE#", "-1", "-3") else v


def data_iso(v):
    """'2026-09-12 00:00:00' -> '2026-09-12'; vazio se nulo."""
    v = nulo(v)
    return v[:10]


def valor_br(v):
    """'12000,00' -> '12000.00'."""
    v = nulo(v)
    return v.replace(".", "").replace(",", ".") if v else ""


def margem_do_texto(texto):
    """Extrai a margem de erro (pontos percentuais) citada no plano amostral. None se não houver.

    Procura a palavra 'margem' e o primeiro número seguido de %/pontos nos 300 caracteres seguintes,
    ignorando valores fora de (0, 15] (p.ex. nível de confiança de 95%).
    """
    for m in re.finditer(r"margem", texto or "", re.I):
        for n in _NUM.finditer(texto[m.start():m.start() + 300]):
            v = float(n.group(1).replace(",", "."))
            if 0 < v <= 15:
                return v
    return None


def margem_teorica(n):
    """Margem de erro da amostragem aleatória simples (95%, p=0,5), em pp: 98/sqrt(n). Derivada, NÃO é do TSE."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ""
    return f"{98 / math.sqrt(n):.2f}" if n > 0 else ""


def abrangencia(texto):
    """Trecho (até 120 caracteres) da frase do plano amostral que fala do 'universo'; vazio se não houver."""
    m = re.search(r"universo[^.\r\n]{0,200}", texto or "", re.I)
    return re.sub(r"\s+", " ", m.group(0)).strip()[:120] if m else ""


def eh_pessoa_fisica(doc):
    return len(re.sub(r"\D", "", doc or "")) == 11


def ler_csv_zip(zbytes, nome_csv):
    csv.field_size_limit(10 ** 9)
    with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
        with z.open(nome_csv) as f:
            return list(csv.DictReader(io.TextIOWrapper(f, encoding="latin-1", newline=""), delimiter=";"))


def montar(registro, contratantes, pagantes):
    """Junta as três tabelas (listas de dict) e devolve as linhas de Presidente prontas para o CSV."""
    contr = {}
    for r in contratantes:
        contr.setdefault(r["NR_PROTOCOLO_REGISTRO"], []).append(r)
    pag = {(r["NR_PROTOCOLO_REGISTRO"], r["CD_CONTRATANTE"]): r for r in pagantes}
    out = []
    for r in registro:
        if "presidente" not in r["DS_CARGO"].lower():
            continue
        p = r["NR_PROTOCOLO_REGISTRO"]
        nomes_c, nomes_p, origens = [], [], []
        for c in contr.get(p, []):
            g = pag.get((p, c["CD_CONTRATANTE"]))
            nomes_c.append("pessoa_fisica" if eh_pessoa_fisica(c["NR_CPF_CNPJ_CONTRATANTE"])
                           else nulo(c["NM_CONTRATANTE"]))
            if g:
                nomes_p.append("pessoa_fisica" if eh_pessoa_fisica(g["NR_CPF_CNPJ_PAGANTE"])
                               else nulo(g["NM_PAGANTE"]))
                origens.append(nulo(g["DS_ORIGEM_RECURSO"]) or c.get("ST_CONTRATANTE_PAGANTE", ""))
        plano = r["DS_PLANO_AMOSTRAL"]
        mg = margem_do_texto(plano)
        out.append(dict(
            protocolo=p, uf=r["SG_UF"], empresa=nulo(r["NM_EMPRESA"]), empresa_fantasia=nulo(r["NM_EMPRESA_FANTASIA"]),
            cnpj=nulo(r["NR_CNPJ_EMPRESA"]), pesquisa_propria=r["ST_PESQUISA_PROPRIA"],
            data_registro=nulo(r["DT_REGISTRO"])[:10], data_inicio=data_iso(r["DT_INICIO_PESQUISA"]),
            data_fim=data_iso(r["DT_FIM_PESQUISA"]), data_divulgacao=data_iso(r["DT_DIVULGACAO"]),
            amostra=nulo(r["QT_ENTREVISTADO"]), custo=valor_br(r["VR_PESQUISA"]),
            margem_erro_pp="" if mg is None else f"{mg:g}", margem_origem="ausente" if mg is None else "texto",
            margem_teorica_aas_pp=margem_teorica(nulo(r["QT_ENTREVISTADO"])), abrangencia_texto=abrangencia(plano),
            plano_amostral_len=len(plano), metodologia_len=len(r["DS_METODOLOGIA_PESQUISA"]),
            contratantes=" | ".join(nomes_c), pagantes=" | ".join(nomes_p), origem_recurso=" | ".join(origens),
            tse_dt_geracao=f"{r['DT_GERACAO']} {r['HH_GERACAO']}"))
    return out


# --- download ---------------------------------------------------------------------------------------
def baixar():
    """Baixa os 3 ZIPs e o package_show do CKAN, guardando os bytes originais e o manifesto."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    itens = {}
    alvos = [(n + ".zip", f"{BASE}/{n}.zip") for n in ARQUIVOS] + [("ckan_package_show.json", CKAN)]
    for nome, url in alvos:
        with urlopen(Request(url, headers=C.UA), timeout=120) as r:
            corpo = r.read()
            lm = r.headers.get("Last-Modified", "")
        (RAW_DIR / nome).write_bytes(corpo)
        itens[nome] = dict(url=url, sha256=sha256_bytes(corpo), tamanho_bytes=len(corpo), coletado_em=agora(),
                           last_modified=lm)
        print(f"{nome}: {len(corpo)/1e3:.0f} kB  Last-Modified={lm or '-'}", file=sys.stderr)
    MANIFESTO.write_text(json.dumps(itens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return itens


def extrair():
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    tabelas = {n: ler_csv_zip((RAW_DIR / (n + ".zip")).read_bytes(), csv_) for n, csv_ in ARQUIVOS.items()}
    linhas = montar(tabelas["pesquisa_eleitoral_2026"], tabelas["pesquisa_contratante_2026"],
                    tabelas["pesquisa_pagante_2026"])
    linhas.sort(key=lambda r: (r["data_fim"], r["protocolo"]))
    C.EXTERNAL.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)
    zp = manifesto["pesquisa_eleitoral_2026.zip"]
    ckan = json.loads((RAW_DIR / "ckan_package_show.json").read_text(encoding="utf-8"))["result"]
    meta = dict(
        fonte_id=FONTE_ID, dataset=DATASET, licenca_ckan=ckan.get("license_title"),
        arquivos={k: v for k, v in manifesto.items()},
        n_registros_total=len(tabelas["pesquisa_eleitoral_2026"]), n_presidente=len(linhas),
        n_com_margem_texto=sum(r["margem_origem"] == "texto" for r in linhas),
        n_pessoa_fisica_contratante=sum("pessoa_fisica" in r["contratantes"] for r in linhas),
        tse_dt_geracao=linhas[0]["tse_dt_geracao"] if linhas else "",
        nota="O TSE regenera os arquivos diariamente; esta é a fotografia de coletado_em.")
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    escrever_entrada(dict(
        id=FONTE_ID, nome="Registro de pesquisas eleitorais 2026 (TSE) - Presidente, com contratante e pagante",
        publicador="Tribunal Superior Eleitoral (dados abertos)", url_origem=zp["url"], url_landing=DATASET,
        coletado_em=zp["coletado_em"], sha256=zp["sha256"], tamanho_bytes=zp["tamanho_bytes"],
        licenca=f"{ckan.get('license_title')} (campo license_id='{ckan.get('license_id')}' do CKAN, lido em "
                f"{CKAN})",
        granularidade="uma linha por protocolo de registro de pesquisa; sem resultados (só metadados do registro)",
        periodo=f"registros com fim de campo de {linhas[0]['data_fim']} a {linhas[-1]['data_fim']}",
        confianca="alta", status="verificada", usado_em="auditoria de proveniencia das pesquisas "
        "(data/processed/auditoria_pesquisas.csv); nao entra no modelo",
        limitacoes="Registro, nao resultado: nao traz percentuais. Arquivos regenerados diariamente (ver "
                   "Last-Modified no manifesto). Varios registros 'Presidente' sao de universos estaduais. "
                   "Margem de erro extraida por regex do texto livre (ausente em parte dos registros). "
                   "Contratante/pagante pessoa fisica reduzido a categoria. Outros ZIPs do dataset (notas "
                   "fiscais, questionarios, bairro/municipio, PDF) nao foram coletados."))
    print(f"{len(linhas)} registros de Presidente -> {SAIDA}  (margem do texto em {meta['n_com_margem_texto']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-download", action="store_true", help="usa os ZIPs já salvos em data/raw/tse_pesquisas_2026/")
    a = ap.parse_args()
    if not a.no_download:
        baixar()
    extrair()


if __name__ == "__main__":
    main()
