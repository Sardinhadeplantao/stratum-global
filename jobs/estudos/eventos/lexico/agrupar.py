"""Agrupamento ONLINE de manchetes em eventos, abordagem LÉXICA (fase 1, experimento).

Como funciona, em português simples:

1. Cada manchete vira um "saco de palavras" do TÍTULO: minúsculas, sem acento, sem palavras vazias
   (artigos, preposições, verbos de fala como "says"/"diz", dias e meses), números escritos viram algarismos
   ("four" -> "4", "2.400" -> "2400") e cada palavra é cortada nas 5 primeiras letras ("protests" e
   "protestos" viram "prote"; "França" e "France" viram "franc"). O corte serve de radical simples e ajuda
   a casar português com inglês em nomes e palavras parecidas.
2. Os países que a regra de países já marcou entram como termos extras ("@FRA"), com peso 0,5.
3. Cada termo pesa pelo IDF da JANELA (todas as manchetes passadas a agrupar(); em produção, as dos
   últimos 2 dias): palavra que aparece em muitas manchetes do dia (França, Rubio, protestos) pesa pouco;
   palavra rara (endossa, incêndio, base militar) pesa muito. Fórmula: ln((N+1)/(df+1)) + 1.
4. As manchetes chegam uma a uma. Cada grupo guarda a soma dos vetores dos seus membros (o centro).
   A manchete nova entra no grupo cujo centro é mais parecido (cosseno), se passar no limiar:
   - 0,46 para formar par com uma manchete sozinha (prova mais forte para criar um evento);
   - 0,38 para entrar num grupo que já tem 2 ou mais (o centro de várias manchetes é mais confiável).
   Trava: se a manchete e um membro têm países marcados e nenhum em comum, não entra.
   Se nenhum grupo passa, abre um grupo novo. Nada é movido depois; grupos nunca se fundem (regra 2).

O resumo (trecho do RSS) NÃO entra: medido no dev, ele piora (o trecho costuma citar eventos vizinhos).
Sem dependências fora da biblioteca padrão do Python.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

CONFIG = {
    "versao": "lexico-0.1",
    "corte": 5,                 # letras mantidas de cada palavra (radical simples, casa cognatos pt/en)
    "peso_titulo": 1.0,         # peso das palavras do título (binário: a palavra está ou não está)
    "peso_resumo": 0.0,         # peso das palavras do resumo (0 = não usa; medido: piora)
    "peso_pais": 0.5,           # peso de cada país marcado pela regra de países (termo "@ISO3")
    "idf": "janela",            # "janela": IDF sobre todas as manchetes passadas a agrupar() (em produção, 2 dias);
                                # "incremental": só as que já chegaram (mede o pior caso, janela vazia)
    "limiar_par": 0.46,         # cosseno mínimo para juntar com um grupo de 1 manchete
    "limiar_grupo": 0.38,       # cosseno mínimo (contra o centro) para entrar num grupo de 2 ou mais
    "trava_pais": True,         # países marcados nos dois e nenhum em comum = não junta
}

# ----------------------------------------------------------------- listas gerais (nada tirado das manchetes)
STOP_EN = set("""
a about above after again against all am among an and any are aren as at be because been before being below between
both but by can cannot could did do does doing down during each either else ever every few for from further had has
have having he her here hers herself him himself his how however i if in into is isn it its itself just let like may
me might more most much must my myself no nor not now of off on once only or other others our ours ourselves out
over own per same shall she should since so some such than that the their theirs them themselves then there these
they this those though through thus to too toward towards under until up upon us very via was we were what whatever
when where whether which while who whom whose why will with within without would yet you your yours amid amidst
despite onto beyond across along around behind beside besides near next still even already soon ago back also
""".split())
STOP_PT = set("""
a ao aos aquela aquelas aquele aqueles aquilo as ate com como contra da das de dela delas dele deles depois do dos e
ela elas ele eles em entre era eram essa essas esse esses esta estao estas este estes eu foi foram ha isso isto ja la
lhe lhes mais mas me mesmo meu minha muito na nas nem no nos nossa nosso num numa o os ou para pela pelas pelo pelos
por qual quando que quem se sem ser seu seus sob sobre sua suas tambem te tem ter teu tua um uma uns umas voce apos
ante perante desde durante mediante segundo conforme enquanto onde porque pois ainda apenas cerca quase sao seria
sera estar estava esteve vai vao nesta neste nessa nesse deste desta
""".split())
# verbos de fala e palavras de formato de notícia (servem a qualquer redação)
FALA = set("""
say says said saying tell tells told claim claims claimed according report reports reported reportedly stated
statement add adds added note notes noted insist insists insisted watch live video analysis explained explainer
opinion interview podcast update updates breaking photos agency media newspaper source sources
diz dizem disse afirma afirmou declara declarou informa informou segundo
""".split())
TEMPO = set("""
monday tuesday wednesday thursday friday saturday sunday today yesterday tomorrow tonight morning evening night
january february march april may june july august september october november december
week weekend day days month months year years hour hours time earlier later
segunda terca quarta quinta sexta sabado domingo feira hoje ontem amanha manha tarde noite
janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro
semana dia dias mes meses ano anos hora horas
""".split())
NUMEROS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "dozen": "12", "hundred": "100", "thousand": "1000",
    "um": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4", "cinco": "5", "seis": "6", "sete": "7",
    "oito": "8", "nove": "9", "dez": "10", "onze": "11", "doze": "12", "mil": "1000", "cem": "100",
}

_INVISIVEIS = dict.fromkeys(map(ord, "​‌‍‎‏⁠﻿­"), None)
_TOKEN = re.compile(r"\d+(?:[.,]\d+)*|[^\W\d_]+")
_MILHAR = re.compile(r"^\d{1,3}(?:[.,]\d{3})+$")


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def termos_texto(texto: str, corte: int) -> list[str]:
    """Palavras normalizadas de um texto (título ou resumo), na ordem."""
    texto = (texto or "").translate(_INVISIVEIS).replace("’", "'").replace("‘", "'")
    texto = re.sub(r"'s\b", "", texto)
    out = []
    for bruto in _TOKEN.findall(texto):
        if bruto[0].isdigit():
            out.append(re.sub(r"[.,]", "", bruto) if _MILHAR.match(bruto) else bruto.replace(",", "."))
            continue
        w = _sem_acento(bruto.lower())
        if w in NUMEROS:
            out.append(NUMEROS[w])
        elif len(w) >= 2 and w not in STOP_EN and w not in STOP_PT and w not in FALA and w not in TEMPO:
            out.append(w[:corte])
    return out


def pesos_doc(doc: dict, cfg: dict) -> tuple[dict[str, float], set[str]]:
    """Peso bruto (antes do IDF) de cada termo da manchete e o conjunto de termos do texto inteiro.

    O texto inteiro (título + resumo + países) serve só para contar em quantas manchetes cada termo aparece (df):
    mais texto dá uma estimativa melhor de quão comum a palavra está na janela.
    """
    titulo = doc.get("titulo") or ""
    resumo = doc.get("resumo") or ""
    p: dict[str, float] = {}
    todos: set[str] = set()
    if resumo.strip() and resumo.strip() != titulo.strip():
        for t in termos_texto(resumo, cfg["corte"]):
            todos.add(t)
            if cfg["peso_resumo"] > 0:
                p[t] = cfg["peso_resumo"]
    for t in termos_texto(titulo, cfg["corte"]):
        todos.add(t)
        p[t] = cfg["peso_titulo"]
    for iso in doc.get("paises") or []:
        todos.add("@" + iso)
        if cfg["peso_pais"] > 0:
            p["@" + iso] = cfg["peso_pais"]
    return p, todos


def idf_janela(textos: dict[int, set[str]]) -> dict[str, float]:
    """IDF da janela: ln((N+1)/(df+1)) + 1, com df contado no texto inteiro de cada manchete."""
    df = Counter()
    for s in textos.values():
        df.update(s)
    n = len(textos)
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}


def vetor(p: dict[str, float], idf: dict[str, float]) -> dict[str, float]:
    v = {t: w * idf[t] for t, w in p.items()}
    norma = math.sqrt(sum(x * x for x in v.values())) or 1.0
    return {t: x / norma for t, x in v.items()}


def _paises_ok(a: set, b: set) -> bool:
    return not (a and b and not (a & b))


def agrupar(docs: list[dict], ordem: list[int] | None = None, config: dict | None = None) -> list[list[int]]:
    """Agrupa as manchetes na ordem de chegada. Devolve a lista de grupos (listas de ids, na ordem de entrada).

    docs: dicts com id, fonte, titulo, resumo, paises. ordem: ids na ordem de chegada (None = ids crescentes).
    O IDF usa todas as manchetes de docs (a janela), ou, com config {"idf": "incremental"}, só as que já
    chegaram (pior caso: janela começando vazia). Não lê nenhum arquivo.
    """
    cfg = {**CONFIG, **(config or {})}
    por_id = {d["id"]: d for d in docs}
    ordem = list(ordem) if ordem is not None else sorted(por_id)
    pesos, textos = {}, {}
    for i in ordem:
        pesos[i], textos[i] = pesos_doc(por_id[i], cfg)
    incremental = cfg["idf"] == "incremental"
    if incremental:
        df, n = Counter(), 0
    else:
        idf = idf_janela(textos)
        vet = {i: vetor(pesos[i], idf) for i in ordem}
    paises = {i: set(por_id[i].get("paises") or []) for i in ordem}

    grupos: list[list[int]] = []
    somas: list[dict[str, float]] = []          # centro de cada grupo (soma dos vetores dos membros)
    normas: list[float] = []
    indice: dict[str, set[int]] = {}             # termo -> grupos que o contêm (só para achar candidatos rápido)
    for i in ordem:
        if incremental:  # IDF com as manchetes que já chegaram, inclusive esta; centros refeitos com ele
            df.update(textos[i])
            n += 1
            idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}
            vi = vetor(pesos[i], idf)
        else:
            vi = vet[i]
        candidatos = set()
        for t in vi:
            candidatos |= indice.get(t, set())
        melhor, folga_melhor = None, 0.0
        for g in sorted(candidatos):
            membros = grupos[g]
            if cfg["trava_pais"] and not all(_paises_ok(paises[i], paises[j]) for j in membros):
                continue
            if incremental:
                soma = Counter()
                for j in membros:
                    soma.update(vetor(pesos[j], idf))
                norma = math.sqrt(sum(x * x for x in soma.values())) or 1.0
                s = sum(x * soma[t] for t, x in vi.items() if t in soma) / norma
            else:
                soma = somas[g]
                s = sum(x * soma[t] for t, x in vi.items() if t in soma) / normas[g]
            limiar = cfg["limiar_par"] if len(membros) == 1 else cfg["limiar_grupo"]
            folga = s - limiar
            if folga >= 0 and (melhor is None or folga > folga_melhor):
                melhor, folga_melhor = g, folga
        if melhor is None:
            grupos.append([i])
            somas.append(dict(vi))
            normas.append(math.sqrt(sum(x * x for x in vi.values())) or 1.0)
            melhor = len(grupos) - 1
        else:
            grupos[melhor].append(i)
            soma = somas[melhor]
            for t, x in vi.items():
                soma[t] = soma.get(t, 0.0) + x
            normas[melhor] = math.sqrt(sum(x * x for x in soma.values())) or 1.0
        for t in vi:
            indice.setdefault(t, set()).add(melhor)
    return grupos
