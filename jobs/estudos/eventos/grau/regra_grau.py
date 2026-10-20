"""Grau de confirmação de um evento (proposta grau-0.1). Função pura: documentos do evento + fichas -> grau.

Sem banco, rede ou IA. A ordem de chegada (conhecido_em, id) só pesa nas quase-duplicatas.

Graus, do menor para o maior: pista < relatado < corroborado < oficial.
- oficial: algum documento é ato do próprio órgão (ficha nível 1 ou 2 e atos_proprios "todos", ou "por_titulo"
  com o título dizendo que um órgão da organização agiu).
- corroborado: pelo menos 2 vozes independentes E pelo menos 2 controladores de quem publicou.
- relatado: pelo menos 1 documento de nível 1 a 4.
- pista: só rede social (nível 5).
Contestado: não é produzido nesta versão (motivo na proposta).

Voz de um documento:
- se o texto credita AFP, Reuters ou AP, a voz é a agência (a primeira citada);
- senão, o controlador da fonte (ficha).
Quase-duplicata: a manchete quase igual a uma anterior do evento entra no mesmo "grupo de texto" e não acrescenta
voz nem controlador (vale a do primeiro documento do grupo). Grupos de texto nunca se fundem depois.
"""
import re
import unicodedata

VERSAO = "grau-0.1"
ORDEM = ("pista", "relatado", "corroborado", "oficial")

# Crédito de agência: só formas que não colidem com outra coisa. "AP" sozinho fica de fora (Andhra Pradesh no The Hindu).
CREDITOS = [
    ("afp", re.compile(r"\bAFP\b|Agence France[- ]Presse|\bFrance[- ]Presse\b")),
    ("reuters", re.compile(r"\bReuters\b")),
    ("ap", re.compile(r"Associated Press|\(AP\)")),
]

# Órgãos das Nações Unidas (Carta da ONU e organograma do sistema ONU), para atos_proprios="por_titulo".
ORGAOS_ONU = ("Security Council", "General Assembly", "Secretary-General", "Human Rights Council", "ECOSOC",
              "International Court of Justice", "ICJ", "World Food Programme", "WFP", "UNICEF",
              "World Health Organization", "WHO", "UNHCR", "UNRWA", "OCHA", "IAEA", "UNESCO", "FAO", "UNDP",
              "UNFPA", "IOM", "UN Women", "OHCHR")
# Verbos de ato (decidir, aprovar, publicar). Verbos de fala (says, warns, urges, condemns) não entram de propósito:
# uma fala do órgão sobre um fato de outro não torna o fato oficial.
ATOS = ("adopts", "approves", "passes", "votes", "extends", "renews", "elects", "appoints", "launches", "suspends",
        "halts", "cuts", "ends", "rules", "orders", "issues", "imposes", "lifts", "authorizes", "authorises",
        "allocates", "releases", "declares", "opens", "closes", "establishes", "creates", "admits", "expands")
_ORGAO = "|".join(re.escape(o) for o in sorted(ORGAOS_ONU, key=len, reverse=True))
ATO_ONU = re.compile(rf"^(?:UN |U\.N\. |The )?(?:{_ORGAO})(?:'s)? (?:{'|'.join(ATOS)})\b")

LIMIAR_QUASE_IGUAL = 0.5   # Jaccard de trincas de palavras; no dev, o maior par entre fontes diferentes dá 0,12


def credito_agencia(texto: str) -> str | None:
    """A agência creditada no texto (a que aparece primeiro), ou None."""
    achados = [(m.start(), nome) for nome, padrao in CREDITOS for m in [padrao.search(texto)] if m]
    return min(achados)[1] if achados else None


def ato_proprio(doc: dict, ficha: dict) -> bool:
    if ficha["nivel"] not in (1, 2):
        return False
    if ficha["atos_proprios"] == "todos":
        return True
    if ficha["atos_proprios"] == "por_titulo":
        return bool(ATO_ONU.match(doc["titulo"].strip()))
    return False


def _trincas(doc: dict) -> set:
    texto = doc["titulo"] + ("" if (doc.get("resumo") or "") == doc["titulo"] else " " + (doc.get("resumo") or ""))
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    p = re.findall(r"[a-z0-9]+", texto)
    return {tuple(p[i:i + 3]) for i in range(max(1, len(p) - 2))}


def quase_iguais(a: dict, b: dict) -> bool:
    """Substituto até a regra de quase-duplicatas (MinHash) existir; ela entra no lugar desta função."""
    ta, tb = _trincas(a), _trincas(b)
    return bool(ta and tb) and len(ta & tb) / len(ta | tb) >= LIMIAR_QUASE_IGUAL


def voz(doc: dict, fichas: dict, agencias: dict) -> tuple[str, str]:
    """(voz, controlador de quem publicou)."""
    ficha = fichas[doc["fonte"]]
    agencia = credito_agencia(doc["titulo"] + "\n" + (doc.get("resumo") or ""))
    return (agencias[agencia]["controlador"] if agencia else ficha["controlador"]), ficha["controlador"]


def grau(documentos: list[dict], fichas: dict, agencias: dict, quase=quase_iguais) -> dict:
    """documentos: dicts com id, fonte, titulo, resumo e, se houver, conhecido_em. Devolve o grau e a explicação."""
    docs = sorted(documentos, key=lambda d: (d.get("conhecido_em") or "", d["id"]))
    oficiais = [d["id"] for d in docs if ato_proprio(d, fichas[d["fonte"]])]
    contaveis = [d for d in docs if fichas[d["fonte"]]["nivel"] <= 4]   # rede social nunca conta (regra 4)
    grupos: list[list[dict]] = []
    for d in contaveis:                      # online: entra no primeiro grupo com texto quase igual, ou abre outro
        g = next((g for g in grupos if any(quase(d, x) for x in g)), None)
        g.append(d) if g is not None else grupos.append([d])
    vozes, publicadores = set(), set()
    for g in grupos:
        v, p = voz(g[0], fichas, agencias)
        vozes.add(v)
        publicadores.add(p)
    if oficiais:
        nome = "oficial"
    elif len(vozes) >= 2 and len(publicadores) >= 2:
        nome = "corroborado"
    elif contaveis:
        nome = "relatado"
    else:
        nome = "pista"
    return {"grau": nome, "regra": VERSAO, "vozes": sorted(vozes), "publicadores": sorted(publicadores),
            "oficiais": oficiais, "documentos": len(docs), "grupos_de_texto": len(grupos)}


def subiu(antes: str | None, depois: str) -> bool:
    return antes is None or ORDEM.index(depois) > ORDEM.index(antes)
