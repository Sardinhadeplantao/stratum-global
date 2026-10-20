"""Histórias (decisão 0009): notícias da mesma história juntas, por regra; ligação gravada uma vez, nunca reescrita."""
import itertools
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from stratum import db, export, fontes, historias
from stratum.domain import historias as regra

GABARITO = Path(__file__).parent / "gabarito"
T0 = datetime(2026, 10, 20, 12, 0)

# Manchetes sem relação entre si: dão à regra uma janela com vocabulário variado, como num dia real
SOLTAS = [
    ("aljazeera", "Indonesia battles worst forest fires and toxic haze in 11 years"),
    ("bbc_mundo", "Chile's central bank holds interest rates steady"),
    ("dw_mundo", "German parliament debates new pension reform"),
    ("france24", "Kenya marathon runner breaks course record in Chicago"),
    ("the_hindu", "Monsoon floods displace thousands in Assam"),
    ("cgtn_mundo", "China launches new weather satellite from Jiuquan"),
    ("folha_mundo", "Argentina anuncia novo pacote de obras em rodovias"),
    ("tass", "Moscow metro opens three new stations"),
]
SETTLERS = [
    ("bbc_mundo", "Israeli settlers attack Palestinians in West Bank during olive harvest"),
    ("aljazeera", "Israeli settlers continue pogrom amid olive harvest in occupied West Bank"),
]


def _medida(conjunto: str) -> tuple[float, int, int]:
    """Pior precisão (nível de história) nas 3 ordens e quantas histórias com 2+ manchetes ganharam um par."""
    docs = [json.loads(l) for l in open(GABARITO / f"{conjunto}.jsonl", encoding="utf-8")]
    g = json.load(open(GABARITO / f"gabarito_{conjunto}.json", encoding="utf-8"))
    assunto = {i: a["id"] for a in g["assuntos"] for e in a["eventos"] for i in e["ids"]}
    ids = [d["id"] for d in docs]
    embaralhada = list(ids)
    random.Random(1).shuffle(embaralhada)
    piores, com_par = [], []
    multiplas = [[i for i in ids if assunto[i] == a] for a in set(assunto.values())]
    multiplas = [m for m in multiplas if len(m) >= 2]
    for ordem in (sorted(ids), sorted(ids, reverse=True), embaralhada):
        grupos = regra.agrupar(docs, ordem)
        pares = [p for gr in grupos for p in itertools.combinations(gr, 2)]
        piores.append(sum(assunto[a] == assunto[b] for a, b in pares) / len(pares))
        rot = {i: k for k, gr in enumerate(grupos) for i in gr}
        com_par.append(sum(any(rot[x] == rot[y] for x, y in itertools.combinations(m, 2)) for m in multiplas))
    return min(piores), min(com_par), len(multiplas)


def test_referencia_acerto_da_regra_nos_dias_anotados():
    # Medido em 20/10 (jobs/estudos/eventos/LEIAME.md). Se a regra mudar e piorar, este caso avisa.
    for conjunto in ("dev_19out", "teste_16out"):
        precisao, com_par, multiplas = _medida(conjunto)
        assert precisao >= 0.88, conjunto
        assert com_par * 2 >= multiplas * 0.8, conjunto  # pelo menos ~40% das histórias ganham um par


def _inserir(engine, manchetes, inicio=T0, passo=timedelta(minutes=10)):
    ids = []
    with engine.begin() as c:
        db.gravar_fontes(c, fontes.FONTES)
        for k, (fonte, titulo) in enumerate(manchetes):
            quando = inicio + passo * k
            ids.append(c.execute(db.documento.insert().values(
                hash=f"{fonte}-{titulo}", fonte_id=fonte, titulo=titulo, publicado_em=quando, conhecido_em=quando,
                url=f"https://x.example/{k}")).inserted_primary_key[0])
    return ids


def _ligacoes(engine):
    with engine.connect() as c:
        return {r.documento_id: (r.historia_id, r.regra) for r in c.execute(db.historia_documento.select())}


def test_noticias_da_mesma_historia_ficam_juntas(engine):
    ids = _inserir(engine, SOLTAS + SETTLERS)
    r = historias.atualizar(engine, T0 + timedelta(hours=3))
    lig = _ligacoes(engine)
    assert r["documentos"] == len(ids) and set(lig) == set(ids)
    assert lig[ids[-1]][0] == lig[ids[-2]][0] == ids[-2]  # a história tem o id da primeira notícia dela
    assert len({h for h, _ in lig.values()}) == len(SOLTAS) + 1
    assert {v for _, v in lig.values()} == {regra.REGRA}


def test_rodar_de_novo_nao_muda_nada_e_noticia_nova_entra_na_historia(engine):
    ids = _inserir(engine, SOLTAS + SETTLERS[:1])
    historias.atualizar(engine, T0 + timedelta(hours=2))
    antes = _ligacoes(engine)
    assert historias.atualizar(engine, T0 + timedelta(hours=2, minutes=15)) == {"documentos": 0, "historias_novas": 0}
    novo = _inserir(engine, SETTLERS[1:], inicio=T0 + timedelta(hours=2, minutes=30))[0]
    r = historias.atualizar(engine, T0 + timedelta(hours=2, minutes=45))
    depois = _ligacoes(engine)
    assert r == {"documentos": 1, "historias_novas": 0}
    assert {k: v for k, v in depois.items() if k in antes} == antes  # nada reescrito (regra 2)
    assert depois[novo][0] == ids[-1]


def test_historia_antiga_fora_da_janela_nao_recebe_noticia(engine):
    ids = _inserir(engine, SOLTAS + SETTLERS[:1])
    historias.atualizar(engine, T0 + timedelta(hours=2))
    novo = _inserir(engine, SETTLERS[1:], inicio=T0 + timedelta(days=3))[0]
    historias.atualizar(engine, T0 + timedelta(days=3, minutes=5))
    assert _ligacoes(engine)[novo][0] == novo != ids[-1]


def test_vozes_sao_donos_diferentes(engine):
    # TASS e o Ministério das Relações Exteriores da Rússia são o mesmo dono: uma voz só (decisão 0008)
    manchetes = SOLTAS + [
        ("tass", "Russia and Iran sign gas pipeline agreement in Tehran"),
        ("ru_mid", "Russia and Iran sign gas pipeline agreement during Lavrov visit to Tehran"),
        ("bbc_mundo", "Russia and Iran sign gas pipeline agreement in Tehran talks"),
    ]
    _inserir(engine, manchetes)
    historias.atualizar(engine, T0 + timedelta(hours=3))
    lista = historias.recentes(engine, T0 + timedelta(hours=3))
    assert len(lista) == 1
    h = lista[0]
    assert (h["noticias"], h["fontes"], h["vozes"]) == (3, 3, 2)
    assert {p["iso"] for p in h["paises"]} == {"RUS", "IRN"}
    status = export.montar(engine, agora=lambda: T0 + timedelta(hours=3))
    assert status["historias"][0]["vozes"] == 2
    # O painel do país recebe a história pronta (o site não calcula, regra 9)
    assert status["paises"]["IRN"]["historias"] == [{"id": h["id"], "titulo": h["titulo"], "titulo_original": None,
                                                     "noticias": 3, "vozes": 2}]


def test_resumo_do_telegram_mostra_as_historias_com_mais_vozes(engine):
    from stratum import resumo
    _inserir(engine, SOLTAS + [
        ("tass", "Russia and Iran sign gas pipeline agreement in Tehran"),
        ("bbc_mundo", "Russia and Iran sign gas pipeline agreement in Tehran talks"),
    ])
    agora = T0 + timedelta(hours=3)
    historias.atualizar(engine, agora)
    texto = resumo.montar(engine, agora, resumo.horario_devido(agora), None, None)
    assert "Histórias com mais vozes independentes" in texto
    assert "• Russia and Iran sign gas pipeline agreement in Tehran (2 notícias, 2 vozes)" in texto

