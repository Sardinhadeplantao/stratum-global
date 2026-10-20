"""Medida comum do agrupamento em eventos contra o gabarito (fase 1).

Uso como biblioteca:
    from avaliar import carregar, medir
    docs, gold = carregar("dev_19out")      # docs: lista de dicts (id, fonte, titulo, resumo, paises)
    grupos = [[1, 7], [2], ...]             # cada manchete em exatamente um grupo
    print(medir(grupos, gold))

Uso pela linha de comando (um grupo por linha, ids separados por espaço):
    python avaliar.py dev_19out grupos.txt

O conjunto teste_16out só é medido com --teste (ninguém ajusta regra olhando o teste).
"""
import itertools
import json
import sys
from pathlib import Path

GABARITO = Path("/home/user/apex-trading-streamlit/jobs/tests/gabarito")
# Idioma de cada fonte do gabarito (fontes.py): só a Folha não é em inglês
IDIOMA = {"folha_mundo": "pt"}


def carregar(conjunto: str, permitir_teste: bool = False):
    if conjunto.startswith("teste") and not permitir_teste:
        raise SystemExit("O conjunto de teste só é medido no fim, com a regra congelada (use permitir_teste=True).")
    docs = [json.loads(l) for l in open(GABARITO / f"{conjunto}.jsonl", encoding="utf-8")]
    g = json.load(open(GABARITO / f"gabarito_{conjunto}.json", encoding="utf-8"))
    evento, assunto, tipo = {}, {}, {}
    for a in g["assuntos"]:
        for e in a["eventos"]:
            for i in e["ids"]:
                evento[i], assunto[i], tipo[i] = e["id"], a["id"], e["tipo"]
    assert set(evento) == {d["id"] for d in docs}, "gabarito e manchetes não batem"
    return docs, {"evento": evento, "assunto": assunto, "tipo": tipo, "duvidas": g.get("duvidas", [])}


def _rotulos(grupos):
    r = {}
    for k, grupo in enumerate(grupos):
        for i in grupo:
            if i in r:
                raise ValueError(f"manchete {i} em dois grupos")
            r[i] = k
    return r


def _pares(rotulo):
    por = {}
    for i, k in rotulo.items():
        por.setdefault(k, []).append(i)
    return {tuple(sorted(p)) for g in por.values() for p in itertools.combinations(g, 2)}


def medir(grupos, gold, docs=None) -> dict:
    """Precisão e cobertura dos pares juntados (a meta da fase 1), B-cubed e a linha de base 'nada juntado'."""
    pred = _rotulos(grupos)
    ref = gold["evento"]
    if set(pred) != set(ref):
        faltam = sorted(set(ref) - set(pred))[:10]
        sobram = sorted(set(pred) - set(ref))[:10]
        raise ValueError(f"grupos não cobrem as manchetes (faltam {faltam}, sobram {sobram})")
    pp, pr = _pares(pred), _pares(ref)
    certos = pp & pr
    precisao = len(certos) / len(pp) if pp else 1.0
    cobertura = len(certos) / len(pr) if pr else 1.0
    f = 2 * precisao * cobertura / (precisao + cobertura) if precisao + cobertura else 0.0

    def bcubed(a, b):
        ga, gb = {}, {}
        for i in a:
            ga.setdefault(a[i], set()).add(i)
            gb.setdefault(b[i], set()).add(i)
        p = sum(len(ga[a[i]] & gb[b[i]]) / len(ga[a[i]]) for i in a) / len(a)
        r = sum(len(ga[a[i]] & gb[b[i]]) / len(gb[b[i]]) for i in a) / len(a)
        return p, r, 2 * p * r / (p + r)

    # Eventos de 2 ou mais manchetes em que o agrupamento juntou ao menos duas delas (meta da fase 1)
    por_evento = {}
    for i, e in ref.items():
        por_evento.setdefault(e, []).append(i)
    multiplos = [ids for ids in por_evento.values() if len(ids) >= 2]
    com_par = sum(1 for ids in multiplos if any(pred[x] == pred[y] for x, y in itertools.combinations(ids, 2)))

    bp, br, bf = bcubed(pred, ref)
    _, _, base = bcubed({i: i for i in ref}, ref)
    out = {
        "pares_juntados": len(pp), "pares_certos": len(certos), "pares_gabarito": len(pr),
        "precisao_pares": round(precisao, 3), "cobertura_pares": round(cobertura, 3), "f_pares": round(f, 3),
        "bcubed_p": round(bp, 3), "bcubed_r": round(br, 3), "bcubed_f": round(bf, 3),
        "bcubed_f_nada_juntado": round(base, 3), "grupos": len(set(pred.values())),
        "eventos_multiplos": len(multiplos), "eventos_com_par_juntado": com_par,
        "meta_atingida": precisao >= 0.90 and cobertura >= 0.60 and com_par * 2 >= len(multiplos),
    }
    if docs is not None:
        fonte = {d["id"]: d["fonte"] for d in docs}
        mesma = [p for p in pr if fonte[p[0]] == fonte[p[1]]]
        idioma = [p for p in pr if IDIOMA.get(fonte[p[0]], "en") != IDIOMA.get(fonte[p[1]], "en")]
        out["cobertura_mesma_fonte"] = round(len([p for p in mesma if p in pp]) / len(mesma), 3) if mesma else None
        out["cobertura_fontes_diferentes"] = round(
            len([p for p in pr - set(mesma) if p in pp]) / len(pr - set(mesma)), 3) if pr - set(mesma) else None
        out["cobertura_entre_idiomas"] = round(len([p for p in idioma if p in pp]) / len(idioma), 3) if idioma else None
        out["erros_juntou"] = sorted(pp - pr)[:40]
        out["erros_separou"] = sorted(pr - pp)[:40]
    return out


if __name__ == "__main__":
    teste = "--teste" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--teste"]
    docs, gold = carregar(args[0], permitir_teste=teste)
    grupos = [[int(x) for x in l.split()] for l in open(args[1]) if l.strip()]
    print(json.dumps(medir(grupos, gold, docs), ensure_ascii=False, indent=1))
