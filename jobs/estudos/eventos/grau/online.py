"""Esqueleto do caminho online (proposta): manchete -> evento -> grau, só com inserções.

Modelo em memória das três tabelas novas (listas que só crescem), para os casos de referência.
A decisão "esta manchete é do mesmo evento?" vem de fora (`mesmo_evento`), porque é a parte dos outros agentes.
"""
from datetime import datetime, timedelta

import regra_grau

JANELA = timedelta(hours=48)
VERSAO_AGRUPAMENTO = "eventos-teste"


class Banco:
    def __init__(self):
        self.evento: list[dict] = []            # id, regra, primeiro_documento_id, ocorreu_em, conhecido_em, calculado_em
        self.documento_evento: list[dict] = []  # documento_id, evento_id, regra, calculado_em
        self.evento_grau: list[dict] = []       # evento_id, grau, regra, vozes, documento_id, conhecido_em, calculado_em
        self.documentos: dict[int, dict] = {}

    def docs_do_evento(self, evento_id):
        return [self.documentos[l["documento_id"]] for l in self.documento_evento if l["evento_id"] == evento_id]

    def grau_atual(self, evento_id, regra=regra_grau.VERSAO):
        linhas = [g for g in self.evento_grau if g["evento_id"] == evento_id and g["regra"] == regra]
        return linhas[-1]["grau"] if linhas else None


def processar(banco: Banco, novos: list[dict], mesmo_evento, fichas, agencias, agora: datetime) -> None:
    """Uma rodada. novos: documentos ainda sem evento nesta versão da regra, na ordem (conhecido_em, id)."""
    for d in sorted(novos, key=lambda d: (d["conhecido_em"], d["id"])):
        if any(l["documento_id"] == d["id"] and l["regra"] == VERSAO_AGRUPAMENTO for l in banco.documento_evento):
            continue                                         # já agrupado: rodar de novo não muda nada
        banco.documentos[d["id"]] = d
        candidatos = [e for e in banco.evento if e["regra"] == VERSAO_AGRUPAMENTO
                      and any(abs(x["quando"] - d["quando"]) <= JANELA for x in banco.docs_do_evento(e["id"]))]
        alvo = next((e for e in candidatos if mesmo_evento(d, banco.docs_do_evento(e["id"]))), None)
        if alvo is None:
            alvo = dict(id=len(banco.evento) + 1, regra=VERSAO_AGRUPAMENTO, primeiro_documento_id=d["id"],
                        ocorreu_em=d["quando"], conhecido_em=d["conhecido_em"], calculado_em=agora)
            banco.evento.append(alvo)
        banco.documento_evento.append(dict(documento_id=d["id"], evento_id=alvo["id"], regra=VERSAO_AGRUPAMENTO,
                                           calculado_em=agora))
        r = regra_grau.grau(banco.docs_do_evento(alvo["id"]), fichas, agencias)
        if r["grau"] != banco.grau_atual(alvo["id"]):        # só grava quando muda (ou na primeira vez)
            banco.evento_grau.append(dict(evento_id=alvo["id"], grau=r["grau"], regra=r["regra"], vozes=r["vozes"],
                                          documento_id=d["id"], conhecido_em=d["conhecido_em"], calculado_em=agora))


def mudancas_desde(banco: Banco, inicio: datetime) -> list[dict]:
    """Para o resumo: eventos que mudaram de grau desde o último resumo (o primeiro grau não é mudança)."""
    saida = []
    for g in banco.evento_grau:
        if g["calculado_em"] > inicio:
            anteriores = [x for x in banco.evento_grau if x["evento_id"] == g["evento_id"] and x["regra"] == g["regra"]
                          and banco.evento_grau.index(x) < banco.evento_grau.index(g)]
            if anteriores:
                saida.append(dict(evento_id=g["evento_id"], de=anteriores[-1]["grau"], para=g["grau"],
                                  documento_id=g["documento_id"]))
    return saida
