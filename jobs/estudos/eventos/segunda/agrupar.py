"""Segunda tentativa (20/10): a regra de entidades + a regra da fala atribuída.

Fala atribuída: agências como a TASS dividem uma entrevista em várias notas, cada uma terminando com quem falou
("... — deputy PM Novak", "... — Russian presidential adviser"). Duas notas da MESMA fonte, na janela, com o mesmo
autor da fala no fim do título, são o mesmo acontecimento (diretriz do gabarito: mesmo falante, mesmo dia, uma
declaração). Só vale dentro da mesma fonte: entre fontes, "Trump says X" e "Trump says Y" são falas diferentes.
"""
import importlib.util
import re
from pathlib import Path

# A regra de entidades tem o mesmo nome de arquivo (agrupar.py): carrega pelo caminho
_esp = importlib.util.spec_from_file_location("entidades_agrupar", Path(__file__).resolve().parent.parent / "entidades" / "agrupar.py")
ent = importlib.util.module_from_spec(_esp)
_esp.loader.exec_module(ent)

# "... — Novak", "... - deputy PM Novak", "..., says Lavrov" no fim do título
_TRAVESSAO = re.compile(r"\s[—–-]\s+([^—–-]{2,60})$")
GENERICOS = set("source sources expert experts analyst analysts media diplomat diplomats official officials envoy "
                "report reports spokesperson spokesman newspaper agency".split())
_DICIONARIO = ent.paises.carregar()
_DIZ = re.compile(r",\s+(?:says|said|tells|told)\s+([^,]{2,60})$", re.I)


def falante(titulo: str) -> str | None:
    t = ent._limpar(titulo).strip()
    m = _TRAVESSAO.search(t) or _DIZ.search(t)
    if not m:
        return None
    s = ent._sem_acento(m.group(1)).lower().replace("adviser", "advisor")
    s = re.sub(r"\b(says|said|told|tells|reports?|claims?)\b", " ", s)
    palavras = re.findall(r"[a-z]+", s)
    if not palavras or len(palavras) > 6:
        return None
    if set(palavras) <= GENERICOS:
        return None  # "— source", "— experts": quem falou não está dito
    # Nome próprio que não é país nem nacionalidade ("Russian" não é nome de pessoa)
    nomes = [w for w in re.findall(r"[A-Z][a-z]+", m.group(1))
             if w.lower() not in ent.NAO_NOMES and not ent.paises.citados(w, _DICIONARIO)]
    # Com nome próprio, o falante é o último nome ("Novak"); sem nome, o cargo inteiro ("russian presidential advisor")
    return nomes[-1].lower() if nomes else " ".join(palavras)


def agrupar(docs, ordem=None, cfg=None):
    """Primeiro a regra de entidades; a manchete que ela deixou sozinha entra no grupo de uma manchete anterior da
    mesma fonte com o mesmo falante atribuído. Online e sem mover nada, como a regra de entidades."""
    por_id = {d["id"]: d for d in docs}
    ordem = list(ordem) if ordem is not None else sorted(por_id)
    base = ent.agrupar(docs, ordem, cfg)
    grupo_de = {i: k for k, g in enumerate(base) for i in g}
    # Reconstrói na ordem de chegada, juntando por falante só quem a regra de entidades deixou sozinho
    vistos_falante: dict[tuple, int] = {}
    novo_grupo: dict[int, int] = {}
    grupos: list[list[int]] = []
    for i in ordem:
        g = grupo_de[i]
        if len(base[g]) > 1 or g in novo_grupo:
            if g not in novo_grupo:
                novo_grupo[g] = len(grupos)
                grupos.append([])
            grupos[novo_grupo[g]].append(i)
            alvo = novo_grupo[g]
        else:
            chave = (por_id[i]["fonte"], falante(por_id[i]["titulo"]))
            if chave[1] and chave in vistos_falante:
                alvo = vistos_falante[chave]
                grupos[alvo].append(i)
            else:
                alvo = len(grupos)
                grupos.append([i])
            novo_grupo[g] = alvo
        f = falante(por_id[i]["titulo"])
        if f:
            vistos_falante.setdefault((por_id[i]["fonte"], f), alvo)
    return grupos
