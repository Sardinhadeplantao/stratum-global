"""Agrupamento ONLINE de manchetes em eventos pela ASSINATURA DE ENTIDADES (fase 1, experimento).

Como funciona, em português simples:

1. Cada manchete vira uma "assinatura": a lista do que ela cita.
   - P: países (a regra de países do repositório, stratum.domain.paises; "Kiev", "Ukrainian" e "Ucrânia" dão UKR);
   - N: nomes próprios (palavra com maiúscula fora do começo da frase, ou sigla), cortados nas 5 primeiras letras
     para casar grafias ("Zelensky" = "Zelenskyy", "Akhlaghi" = "Akhlaqi"); a primeira palavra da frase só conta como
     nome se nunca foi vista em minúscula nas manchetes que já chegaram;
   - Q: números (2,400 = 2.400 = 2400; "four" = 4), sem anos e sem dias do mês;
   - A: palavras de ação gerais (ataque, protesto, prisão, morte, eleição, sanção...), em inglês e português,
     agrupadas por conceito: é o que liga a Folha às fontes em inglês junto com nomes, países e números;
   - L: as demais palavras de conteúdo (sem palavras vazias, cargos, dias e meses), sem radical.
   Cada traço guarda se está no título ("t") ou só no resumo ("r").
2. A nota entre duas manchetes é a soma, nos traços em comum, de: peso do tipo x raridade x lugar.
   - raridade = ln((N+1)/(df+1)) / ln(N+1), onde N é o número de manchetes da janela até agora e df quantas delas têm
     o traço. Vai de 0 (está em todas) a 1 (só nesta). Dividir por ln(N+1) deixa a nota na mesma escala no começo
     do dia (poucas manchetes) e depois (muitas), sem precisar de outro limiar;
   - lugar = 1 se o traço está no título das duas, PESO_RESUMO se está no título de uma e no resumo da outra, e
     PESO_RESUMO_RESUMO (0) se só está nos dois resumos.
3. Trava de países: se as duas têm país no título e nenhum em comum, não juntam.
4. A manchete que chega entra no grupo da manchete mais parecida, se a nota passar do LIMIAR; senão abre um grupo
   novo. Nada é movido depois e grupos nunca se fundem (regra 2). Só manchetes da janela (JANELA_HORAS) contam, quando
   a manchete traz data (conhecido_em ou publicado_em); o gabarito não tem data, então lá a janela é o dia todo.

Sem IA, sem rede, só a biblioteca padrão do Python e a regra de países do repositório.
"""
from __future__ import annotations

import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta

sys.path.insert(0, "/home/user/apex-trading-streamlit/jobs")
from stratum.domain import paises  # noqa: E402

CONFIG = {
    # peso de cada tipo de traço (o nome próprio é a referência, 1)
    "peso_pais": 0.5,          # país é comum (EUA, Rússia...): vale metade de um nome
    "peso_nome": 1.0,
    "peso_numero": 1.0,        # número repetido (2.400 presos) é tão específico quanto um nome
    "peso_acao": 0.5,          # o conceito de ação repete a palavra (que já conta como L), por isso metade
    "peso_palavra": 1.0,       # palavra comum de conteúdo
    "peso_resumo": 0.3,        # traço no título de uma e só no resumo da outra (o resumo traz contexto de outros fatos)
    "peso_resumo_resumo": 0.0, # traço só nos dois resumos: não conta
    "nome_prefixo": 5,         # nomes de 6+ letras comparados pelas 5 primeiras ("Zelensky" = "Zelenskyy")
    "palavra_prefixo": 0,      # 0 = palavra inteira; k = compara palavras pelas k primeiras letras (variante)
    "limiar": 2.2,             # nota mínima para entrar num grupo (escolhido no dev; ver notas.md)
    "trava_pais": True,        # países no título das duas e nenhum em comum: não junta
    "janela_horas": 48,        # só compara com manchetes das últimas 48 h (quando há data)
}

# ---------------------------------------------------------------- listas gerais (nenhum nome tirado das manchetes)
INVISIVEIS = dict.fromkeys(map(ord, "​‌‍‎‏⁠﻿­"), None)

# Palavras vazias (inglês e português), verbos de fala e rótulos de formato ("watch", "live", "explained")
VAZIAS = set("""
a about above after again against all also am among an and any are as at be because been before being below between
both but by can could did do does doing down during each few for from further had has have having he her here hers him
his how i if in into is it its just more most my no nor not now of off on once only or other our out over own same she
should so some such than that the their them then there these they this those through to too under until up very was
we were what when where which while who whom why will with would you your amid despite across along around near next
still even already ago back new latest nearly almost several many least per via it's s
says said say tells told according report reports reported claims claim urges urged calls called asks asked
how what why who watch live explained analysis opinion review press brief graphics poll diary inside
a o os as um uma uns umas de da das do dos em na nas no nos por pela pelas pelo pelos para com sem sob sobre entre
e ou mas que se ao aos à às após ante até contra desde durante perante como mais menos muito já ainda também
diz dizem disse afirma afirmou segundo conforme nesta neste nesse nessa este esta esse essa isso isto
""".split())

# Com maiúscula, mas não identificam um acontecimento: cargos, tratamentos, dias, meses, divisões administrativas
NAO_NOMES = set("""
president presidents prime minister ministers ministry premier king queen prince chancellor secretary spokesman
spokeswoman spokesperson foreign interior defence defense state deputy chief leader head general mr mrs ms dr sir
government parliament senator lawmaker mp pm fm governor mayor ambassador envoy official officials
region regions province oblast district
monday tuesday wednesday thursday friday saturday sunday january february march april may june july august september
october november december
presidente premie primeiro chefe ministro ministra ministerio chanceler secretario porta voz governo parlamento senador
deputado governador prefeito embaixador
segunda terca quarta quinta sexta sabado domingo feira janeiro fevereiro marco abril maio junho julho agosto setembro
outubro novembro dezembro
""".split())

MESES = set("""january february march april may june july august september october november december
janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro
jan feb mar apr jun jul aug sep sept oct nov dec""".split())

NUMEROS_ESCRITOS = {
    "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "dozen": 12, "hundred": 100, "thousand": 1000,
    "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10,
    "doze": 12, "cem": 100, "mil": 1000,
}
MULTIPLICADORES = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "mil": 1e3, "milhao": 1e6, "milhoes": 1e6,
                   "bilhao": 1e9, "bilhoes": 1e9, "mln": 1e6, "bln": 1e9, "m": 1e6, "bn": 1e9}

# Conceitos de ação: tipos de acontecimento comuns no noticiário (como nas listas ACLED/CAMEO), inglês e português.
# Palavra terminada em * vale como começo de palavra; as outras, só a forma exata (sem acento, minúscula).
ACOES = {
    "ataque": "attack* strike strikes struck raid raids assault* bomb bombs bombing* shelling airstrike* ataque* "
              "atacou atacam bombarde* ofensiva pound pounds pounded",
    "protesto": "protest* riot riots rioting rioters unrest demonstration* demonstrator* rally rallies clash clashes "
                "protesto* manifesta* disturbio* tumulto*",
    "prisao": "arrest* detain* detention* jail jailed custody preso presos presa presas prisao prisoes prende* "
              "detido* detida*",
    "morte": "kill killed kills killing* dead death deaths die dies died deadly fatal* morto mortos morta mortas "
             "morte mortes matou matam morre* morreu",
    "ferido": "injur* wound wounded hurt ferido* ferida*",
    "incendio": "fire fires blaze* flame flames burn burns burned burning incendio* chamas fogo",
    "eleicao": "election* elect elected vote votes voter* poll polls polling ballot* runoff run-off eleicao eleicoes "
               "eleito* voto votos votacao pleito turno",
    "sancao": "sanction* embargo* tariff* sancao sancoes tarifa*",
    "renuncia": "resign* renuncia* demissao",
    "encontro": "meet meets meeting* met talks summit* visit visits visiting visited cupula reuniao reunioes "
                "encontro* visita*",
    "acordo": "deal deals agreement* accord accords treaty ceasefire truce acordo* tregua cessar-fogo",
    "apoio": "endorse* apoio apoia",
    "ameaca": "threat threats threaten* warn warns warned warning* ameaca* alerta*",
    "toque": "curfew curfews recolher",
    "ajuda": "aid humanitarian ajuda*",
    "acidente": "crash crashes crashed collision* accident* capsize* derail* acidente* naufragio*",
    "explosao": "explosion* explode* blast blasts explosao explosoes",
    "justica": "trial verdict court convict* sentence* sentenced julgamento condenad* tribunal",
    "nomeacao": "nominat* nominee* appoint* nomeia nomeou indicado*",
    "pouso": "landing pouso",
    "desastre": "earthquake* flood flooding floods storm storms hurricane* typhoon* cyclone* tsunami terremoto* "
                "enchente* tempestade* furacao",
    "condena": "condemn* denounc* condena*",
    "acusa": "accuse* accusing blame* blamed acusa* culpa*",
    "paz": "peace negotiation* paz negociacao negociacoes",
    "tiro": "shooting* gunmen gunman gunfire tiroteio* baleado*",
    "migrante": "migrant* refugee* asylum migrante* refugiado*",
    "missil": "missile* missil misseis",
    "drone": "drone drones",
    "execucao": "execute executed execution* executado* execucao",
}
_EXATAS: dict[str, str] = {}
VAZIAS = {"".join(ch for ch in unicodedata.normalize("NFKD", p) if not unicodedata.combining(ch)) for p in VAZIAS}
_PREFIXOS: list[tuple[str, str]] = []
for _c, _ps in ACOES.items():
    for _p in _ps.split():
        if _p.endswith("*"):
            _PREFIXOS.append((_p[:-1], _c))
        else:
            _EXATAS[_p] = _c
_PREFIXOS.sort(key=lambda x: -len(x[0]))

TOKEN = re.compile(r"\d[\d.,]*\d|\d|[^\W\d_]+(?:[-'][^\W\d_0-9]+)*(?:-\d+)?|[A-Z][\w]*-\d+", re.UNICODE)


# ---------------------------------------------------------------- assinatura
def _sem_acento(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))


def _norm(tok: str) -> str:
    t = _sem_acento(tok.lower())
    t = re.sub(r"'s$|'$", "", t)
    return t.strip("-'.")


def _acao(n: str) -> str | None:
    if n in _EXATAS:
        return _EXATAS[n]
    for p, c in _PREFIXOS:
        if n.startswith(p):
            return c
    return None


def _limpar(texto: str | None) -> str:
    t = (texto or "").translate(INVISIVEIS)
    t = re.sub(r"\(\d{1,2}\)", " ", t)          # "domingo (18)" na Folha: é data, não quantidade
    return t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')


def _segmentos(texto: str) -> list[str]:
    """Pedaços que começam como frase: frases do resumo e partes do título separadas por ':', ' — ' ou ' | '."""
    partes = re.split(r"(?<=[.!?])\s+(?=[\"'A-ZÀ-Ý])|:\s+|\s+[—–|-]\s+|\s*\|\s*", texto)
    return [p for p in partes if p and p.strip()]


def _numero(tok: str) -> float | None:
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", tok):        # 2,400 / 2.400 / 500,000
        return float(re.sub(r"[.,]", "", tok))
    if re.fullmatch(r"\d+([.,]\d+)?", tok):
        return float(tok.replace(",", "."))
    return None


def minusculas(doc: dict) -> set[str]:
    """Palavras que aparecem em minúscula na manchete (vocabulário comum, para a regra da primeira palavra)."""
    out = set()
    for texto in (_limpar(doc.get("titulo")), _limpar(doc.get("resumo"))):
        for tok in TOKEN.findall(texto):
            if tok[0].islower():
                out.add(_norm(tok))
    return out


def assinatura(doc: dict, vocab_minusculo, cfg: dict | None = None) -> dict[str, str]:
    """{traço: lugar} de uma manchete; lugar é "t" (título) ou "r" (só no resumo)."""
    cfg = cfg or CONFIG
    dic = paises.carregar()
    sig: dict[str, str] = {}

    def por(k: str, lugar: str) -> None:
        if sig.get(k) != "t":
            sig[k] = lugar

    titulo = _limpar(doc.get("titulo"))
    resumo = _limpar(doc.get("resumo")).strip()
    textos = [("t", titulo)]
    if resumo and resumo != titulo.strip():
        if not re.search(r"[.!?\"')\]]$", resumo):      # resumo cortado: a última palavra pode estar pela metade
            resumo = re.sub(r"\s*\S+$", "", resumo)
        textos.append(("r", resumo))

    for lugar, texto in textos:
        for _termo, iso in paises.encontrados(texto, dic):
            if iso:
                por("P:" + iso, lugar)
        sem_paises = dic.padrao.sub(" § ", texto)        # o termo de país vira P:, não N:
        for seg in _segmentos(sem_paises):
            toks = TOKEN.findall(seg)
            anterior = None
            for i, tok in enumerate(toks):
                n = _norm(tok)
                if not n:
                    continue
                v = _numero(tok)
                if v is not None:
                    seguinte = _norm(toks[i + 1]) if i + 1 < len(toks) else ""
                    antes = _norm(toks[i - 1]) if i > 0 else ""
                    ano = 1900 <= v <= 2100 and "." not in tok and "," not in tok
                    dia = (antes in MESES or seguinte in MESES) and v <= 31
                    if not ano and not dia:
                        if seguinte in MULTIPLICADORES:
                            v *= MULTIPLICADORES[seguinte]
                        por("Q:%g" % v, lugar)
                    anterior = n
                    continue
                if n in NUMEROS_ESCRITOS:
                    por("Q:%g" % NUMEROS_ESCRITOS[n], lugar)
                inicial = anterior is None
                anterior = n
                if n in VAZIAS or n in NAO_NOMES:
                    continue
                sigla = len(tok) >= 2 and tok.replace("-", "").isupper() and tok.replace("-", "").isalpha()
                c = _acao(n)
                if c and not sigla:
                    por("A:" + c, lugar)
                nome = sigla or (tok[0].isupper() and not inicial)
                if tok[0].isupper() and inicial and not sigla and not c and n not in vocab_minusculo:
                    nome = True          # primeira palavra da frase: é nome se nunca apareceu em minúscula
                if nome:
                    k = cfg["nome_prefixo"]
                    por("N:" + (n[:k] if len(n) > k and n.isalpha() else n), lugar)
                else:
                    k = cfg["palavra_prefixo"]
                    por("L:" + (n[:k] if k else n), lugar)
    return sig


# ---------------------------------------------------------------- nota entre duas manchetes
def _peso_tipo(cfg: dict) -> dict[str, float]:
    return {"P": cfg["peso_pais"], "N": cfg["peso_nome"], "Q": cfg["peso_numero"], "A": cfg["peso_acao"],
            "L": cfg["peso_palavra"]}


def nota(sa: dict, sb: dict, df: Counter, n: int, cfg: dict, pesos: dict | None = None) -> float:
    """Soma, nos traços em comum, de peso do tipo x raridade na janela x lugar. 0 se a trava de países bloqueia."""
    if cfg["trava_pais"]:
        pa = {f for f, l in sa.items() if f[0] == "P" and l == "t"}
        pb = {f for f, l in sb.items() if f[0] == "P" and l == "t"}
        if pa and pb and not (pa & pb):
            return 0.0
    pesos = pesos or _peso_tipo(cfg)
    log_n = math.log(n + 1)
    if log_n <= 0:
        return 0.0
    s = 0.0
    for f in sa.keys() & sb.keys():
        base = pesos.get(f[0], 0.0)
        raridade = math.log((n + 1) / (df[f] + 1)) / log_n
        if base <= 0 or raridade <= 0:
            continue
        la, lb = sa[f], sb[f]
        lugar = 1.0 if la == lb == "t" else (cfg["peso_resumo_resumo"] if la == lb == "r" else cfg["peso_resumo"])
        s += base * raridade * lugar
    return s


def _quando(doc: dict) -> datetime | None:
    for campo in ("conhecido_em", "publicado_em"):
        v = doc.get(campo)
        if isinstance(v, datetime):
            return v
        if isinstance(v, str) and v:
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                pass
    return None


# ---------------------------------------------------------------- agrupamento online
def agrupar(docs: list[dict], ordem: list[int] | None = None, cfg: dict | None = None) -> list[list[int]]:
    """Agrupa as manchetes na ordem de chegada (ordem = lista de ids; None = ids crescentes).

    Cada manchete entra no grupo da manchete já chegada mais parecida (nota >= limiar) ou abre um grupo novo.
    Nada é movido depois e grupos nunca se fundem. Devolve os grupos (listas de ids, na ordem de chegada).
    """
    cfg = dict(CONFIG, **(cfg or {}))
    pesos = _peso_tipo(cfg)
    por_id = {d["id"]: d for d in docs}
    ordem = list(ordem) if ordem is not None else sorted(por_id)
    janela = timedelta(hours=cfg["janela_horas"])

    vocab: Counter = Counter()    # palavras vistas em minúscula nas manchetes da janela (em quantas)
    minusc: dict[int, set] = {}
    df: Counter = Counter()       # em quantas manchetes da janela cada traço aparece
    sigs: dict[int, dict] = {}
    indice: dict[str, set[int]] = defaultdict(set)   # traço -> manchetes da janela que o têm
    na_janela: deque = deque()    # (quando, id), para tirar da janela as manchetes antigas
    grupo_de: dict[int, int] = {}
    chegada: dict[int, int] = {}  # posição de chegada, para desempatar notas iguais
    grupos: list[list[int]] = []

    for i in ordem:
        d = por_id[i]
        agora = _quando(d)
        if agora is not None:
            while na_janela and na_janela[0][0] is not None and na_janela[0][0] < agora - janela:
                _, velho = na_janela.popleft()
                for f in sigs[velho]:
                    df[f] -= 1
                    indice[f].discard(velho)
                for w in minusc.pop(velho):
                    vocab[w] -= 1
                    if vocab[w] <= 0:
                        del vocab[w]
        minusc[i] = minusculas(d)
        vocab.update(minusc[i])
        sig = assinatura(d, vocab, cfg)
        sigs[i] = sig
        df.update(sig.keys())
        n = len(na_janela) + 1

        candidatos = set()
        for f in sig:
            if f[0] != "P":                 # país sozinho não traz candidato (há centenas por país)
                candidatos |= indice[f]
        melhor, melhor_nota = None, 0.0
        for e in candidatos:
            s = nota(sig, sigs[e], df, n, cfg, pesos)
            # empate: fica com a manchete que chegou antes (resultado não depende da ordem do conjunto)
            if s >= cfg["limiar"] and (s > melhor_nota or (s == melhor_nota and melhor is not None
                                                            and chegada[e] < chegada[melhor])):
                melhor, melhor_nota = e, s
        if melhor is None:
            grupo_de[i] = len(grupos)
            grupos.append([i])
        else:
            grupo_de[i] = grupo_de[melhor]
            grupos[grupo_de[melhor]].append(i)
        for f in sig:
            indice[f].add(i)
        na_janela.append((agora, i))
        chegada[i] = len(chegada)
    return grupos
