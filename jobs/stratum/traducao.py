"""Títulos em português do Brasil, por tradução automática gratuita (Argos, modelo inglês → português do Brasil).

Roda no próprio GitHub Actions, sem API paga e sem chave (regra 11). A tradução só lê e traduz (regra 7): a regra de
países e as histórias usam o título original. Cada tradução é gravada uma vez, com o modelo que a fez, e nunca é
reescrita (regra 2). Se o modelo não baixar ou falhar, o site e o resumo mostram o título original.
"""
import os
import zipfile
from datetime import datetime
from pathlib import Path

import requests
from sqlalchemy import select

from stratum import db

MODELO = "argos-en_pb-1.9"
MODELO_URL = "https://argos-net.com/v1/translate-en_pb-1_9.argosmodel"
IDIOMA = "pt"
POR_RODADA = 800               # a primeira rodada traduz o acervo em partes, sem estourar o tempo da rodada


def _pasta() -> Path:
    return Path(os.environ.get("STRATUM_MODELOS") or Path.home() / ".cache" / "stratum")


def baixar_modelo(pasta: Path | None = None) -> Path:
    """Baixa e abre o modelo uma vez (o workflow guarda a pasta em cache). Devolve a pasta com model/ e o sentencepiece."""
    pasta = (pasta or _pasta()) / MODELO
    if not (pasta / "pronto").exists():
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo = pasta / "modelo.zip"
        with requests.get(MODELO_URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(arquivo, "wb") as f:
                for parte in r.iter_content(1 << 20):
                    f.write(parte)
        with zipfile.ZipFile(arquivo) as z:
            z.extractall(pasta)
        arquivo.unlink()
        (pasta / "pronto").write_text(MODELO)
    raiz = next(p.parent for p in pasta.rglob("sentencepiece.model"))
    return raiz


class Tradutor:
    """Tradução por CTranslate2 e SentencePiece, os mesmos pedaços que o Argos usa por dentro."""

    def __init__(self, raiz: Path):
        import ctranslate2
        import sentencepiece

        self.modelo = ctranslate2.Translator(str(raiz / "model"), device="cpu", compute_type="int8")
        self.pedacos = sentencepiece.SentencePieceProcessor(model_file=str(raiz / "sentencepiece.model"))

    def __call__(self, textos: list[str]) -> list[str]:
        entrada = [self.pedacos.encode(t, out_type=str) for t in textos]
        # Os mesmos parâmetros do Argos (beam 4, palavra desconhecida copiada do original)
        saida = self.modelo.translate_batch(entrada, beam_size=4, replace_unknowns=True, length_penalty=0.2,
                                            max_batch_size=32, max_decoding_length=200)
        return [juntar(r.hypotheses[0], t) for r, t in zip(saida, textos)]


def juntar(pedacos: list[str], original: str) -> str:
    """Junta os pedaços como o Argos faz. Tira o ponto final que o modelo põe em manchete que não tinha ponto."""
    texto = "".join(pedacos).replace("▁", " ").strip()
    if texto.endswith(".") and not original.rstrip().endswith("."):
        texto = texto[:-1].rstrip()
    return texto


def pendentes(engine, limite: int = POR_RODADA) -> list[dict]:
    """Títulos ainda sem tradução, dos mais recentes para os mais antigos (o que aparece no site vem primeiro)."""
    d, f, t = db.documento, db.fonte, db.traducao
    with engine.connect() as c:
        return [dict(r) for r in c.execute(
            select(d.c.id, d.c.titulo)
            .join(f, f.c.id == d.c.fonte_id)
            .outerjoin(t, (t.c.documento_id == d.c.id) & (t.c.campo == "titulo") & (t.c.idioma == IDIOMA))
            .where(t.c.documento_id.is_(None), f.c.idioma.is_not(None), f.c.idioma != IDIOMA)
            .order_by(d.c.conhecido_em.desc(), d.c.id.desc()).limit(limite)).mappings()]


def atualizar(engine, agora: datetime, traduzir=None) -> dict:
    """Traduz os títulos pendentes e grava. `traduzir` (lista de textos -> lista de textos) é trocável nos testes."""
    lista = pendentes(engine)
    if not lista:
        return {"traduzidos": 0, "exemplos": []}
    traduzir = traduzir or Tradutor(baixar_modelo())
    textos = traduzir([x["titulo"] for x in lista])
    linhas = [dict(documento_id=x["id"], campo="titulo", idioma=IDIOMA, texto=texto, modelo=MODELO, conhecido_em=agora)
              for x, texto in zip(lista, textos) if texto]
    with engine.begin() as c:
        db.inserir_ignorando_repetidos(c, db.traducao, linhas, ["documento_id", "campo", "idioma"])
    return {"traduzidos": len(linhas), "exemplos": [(x["titulo"], t) for x, t in list(zip(lista, textos))[:3]]}


def titulos(conexao, ids) -> dict[int, str]:
    """{id do documento: título em português}, para quem tem tradução."""
    ids = list(ids)
    saida: dict[int, str] = {}
    t = db.traducao
    for i in range(0, len(ids), 500):
        for r in conexao.execute(select(t.c.documento_id, t.c.texto).where(
                t.c.documento_id.in_(ids[i:i + 500]), t.c.campo == "titulo", t.c.idioma == IDIOMA)):
            saida[r.documento_id] = r.texto
    return saida
