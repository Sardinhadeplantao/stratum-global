"""Arquivo conferido (decisão 0015): o que passou do prazo sai do banco só depois de guardado e conferido.

Uma vez por mês, o workflow `arquivo.yml` (só na main):
1. `--separar PASTA`: grava as notícias com mais de 12 meses (com traduções e ligações às histórias) e o registro de
   leituras com mais de 30 dias, uma linha JSON por registro, comprimida, e o manifesto com a impressão digital
   (SHA-256) de cada arquivo. Nada sai do banco.
2. o workflow publica a pasta num release do GitHub e baixa de volta;
3. `--conferir-e-tirar PASTA --url URL`: confere a impressão digital do que voltou do GitHub, restaura num banco vazio,
   compara cada linha com o banco e só então tira, numa transação que se desfaz inteira se a contagem não bater.

`--restaurar PASTA` devolve um arquivo a um banco (pesquisa ou recuperação), sem repetir o que já está lá.
"""
import argparse
import gzip
import hashlib
import json
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import Date, DateTime, func, select, text, tuple_

from stratum import VERSAO, config, db

FORMATO = 1
PRAZOS = {"documento": timedelta(days=365), "coleta": timedelta(days=30)}
LOTE = 1000
# Pais antes dos filhos (para restaurar); para tirar, a ordem inversa
TABELAS = ["documento", "historia_documento", "traducao", "coleta"]


def _tabela(nome: str):
    return db.md.tables[nome]


def _chave(t):
    return list(t.primary_key.columns)


def _serializar(linha) -> str:
    registro = {k: (v.isoformat() if isinstance(v, date) else v) for k, v in linha.items()}  # datetime é date
    return json.dumps(registro, ensure_ascii=False)


def _ler(t, linha: str) -> dict:
    registro = json.loads(linha)
    for col in t.columns:
        v = registro.get(col.name)
        if v is not None and isinstance(col.type, DateTime):
            registro[col.name] = datetime.fromisoformat(v)
        elif v is not None and isinstance(col.type, Date):
            registro[col.name] = date.fromisoformat(v)
    return registro


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _em_lotes(xs: list, n: int = LOTE):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def hash_curto(h: str) -> int:
    """Os primeiros 60 bits do hash do documento (cabe num BIGINT do PostgreSQL)."""
    return int(h[:15], 16)


def _ids_dos_documentos(c, corte: datetime) -> list[int]:
    """Notícias conhecidas antes do corte. Fica a que é a primeira de uma história que continua numa notícia que fica
    (a ligação não pode apontar para o vazio)."""
    d, ligacao = db.documento.c, db.historia_documento.c
    antigos = set(c.execute(select(d.id).where(d.conhecido_em < corte)).scalars())
    presos = {h for doc, h in c.execute(select(ligacao.documento_id, ligacao.historia_id).where(ligacao.historia_id.in_(
        select(d.id).where(d.conhecido_em < corte)))) if doc not in antigos}
    return sorted(antigos - presos)


def separar(engine, pasta, agora: datetime | None = None, prazos: dict = PRAZOS) -> dict | None:
    """Grava o que passou do prazo e o manifesto. Nada sai do banco. Sem nada a arquivar, não grava nada e devolve
    None. Tudo é lido numa transação só (no PostgreSQL, com foto fixa do banco)."""
    agora = agora or db.agora()
    cortes = {t: agora - p for t, p in prazos.items()}
    postgres = engine.dialect.name == "postgresql"
    with engine.connect().execution_options(**({"isolation_level": "REPEATABLE READ"} if postgres else {})) as c:
        with c.begin():
            ids = _ids_dos_documentos(c, cortes["documento"])
            n_coleta = c.execute(select(func.count()).select_from(db.coleta)
                                 .where(db.coleta.c.iniciada_em < cortes["coleta"])).scalar()
            if not ids and not n_coleta:
                return None
            pasta = Path(pasta)
            pasta.mkdir(parents=True, exist_ok=True)
            consultas = {}
            for nome in ("documento", "historia_documento", "traducao"):
                t = _tabela(nome)
                coluna = t.c.id if nome == "documento" else t.c.documento_id
                consultas[nome] = [select(t).where(coluna.in_(lote)) for lote in _em_lotes(ids)] or [select(t).where(False)]
            consultas["coleta"] = [select(db.coleta).where(db.coleta.c.iniciada_em < cortes["coleta"])]
            tabelas = {}
            for nome in TABELAS:
                t = _tabela(nome)
                caminho = pasta / f"{nome}.jsonl.gz"
                n = 0
                with gzip.open(caminho, "wt", encoding="utf-8") as f:
                    for consulta in consultas[nome]:
                        for linha in c.execute(consulta.order_by(*_chave(t)).execution_options(yield_per=LOTE)).mappings():
                            f.write(_serializar(linha) + "\n")
                            n += 1
                tabelas[nome] = {"linhas": n, "sha256": _sha256(caminho)}
            por_fonte = {}
            for lote in _em_lotes(ids):
                for fonte, n in c.execute(select(db.documento.c.fonte_id, func.count()).where(db.documento.c.id.in_(lote))
                                          .group_by(db.documento.c.fonte_id)):
                    por_fonte[fonte] = por_fonte.get(fonte, 0) + n
            migracao = c.execute(text("select version_num from alembic_version")).scalar()
    manifesto = {"formato": FORMATO, "etiqueta": f"arquivo-{agora:%Y-%m-%d-%H%M}", "versao_robo": VERSAO,
                 "feito_em": agora.isoformat(timespec="seconds") + "Z", "migracao": migracao,
                 "cortes": {t: x.isoformat(timespec="seconds") + "Z" for t, x in cortes.items()},
                 "tabelas": tabelas, "por_fonte": dict(sorted(por_fonte.items()))}
    (pasta / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1), encoding="utf-8")
    (pasta / "LEIAME.md").write_text(_leiame(manifesto), encoding="utf-8")
    return manifesto


def _leiame(m: dict) -> str:
    linhas = "\n".join(f"- `{t}.jsonl.gz`: {x['linhas']} registros" for t, x in m["tabelas"].items())
    return (f"Arquivo do banco do Stratum Global ({m['etiqueta']}, decisão 0015).\n\n"
            f"Notícias conhecidas antes de {m['cortes']['documento']} (com traduções e ligações às histórias) e "
            f"registro de leituras antes de {m['cortes']['coleta']}. Saíram do banco só depois de conferidos.\n\n"
            f"{linhas}\n\nUma linha JSON por registro. Para devolver a um banco: "
            f"`cd jobs && python -m stratum.arquivo --restaurar PASTA`.\n")


def conferir(engine, pasta) -> list[str]:
    """O que voltou do GitHub é o que está no banco? Confere a impressão digital, restaura num banco vazio e compara
    cada linha com o banco. Lista vazia = pode tirar."""
    pasta = Path(pasta)
    m = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
    problemas = []
    if m.get("formato") != FORMATO:
        return [f"formato {m.get('formato')} desconhecido"]
    if m.get("migracao") != db.versao_do_banco(engine):
        return [f"o banco mudou de versão do esquema ({m.get('migracao')} -> {db.versao_do_banco(engine)})"]
    for nome in TABELAS:
        if _sha256(pasta / f"{nome}.jsonl.gz") != m["tabelas"][nome]["sha256"]:
            problemas.append(f"{nome}: a impressão digital não bate com o manifesto")
    if problemas:
        return problemas
    with tempfile.TemporaryDirectory(prefix="stratum-arquivo-") as tmp:
        vazio = db.conectar(f"sqlite:///{tmp}/arquivo.db")
        try:
            db.preparar(vazio)
            restaurar(pasta, vazio)
            with vazio.connect() as cv, engine.connect() as cb:
                for nome in TABELAS:
                    t = _tabela(nome)
                    with gzip.open(pasta / f"{nome}.jsonl.gz", "rt", encoding="utf-8") as f:
                        do_arquivo = f.read().splitlines()
                    if len(do_arquivo) != m["tabelas"][nome]["linhas"]:
                        problemas.append(f"{nome}: o manifesto diz {m['tabelas'][nome]['linhas']} linhas, "
                                         f"o arquivo tem {len(do_arquivo)}")
                        continue
                    chaves = [tuple(json.loads(x)[k.name] for k in _chave(t)) for x in do_arquivo]
                    restaurado = _linhas_por_chave(cv, t, chaves)
                    no_banco = _linhas_por_chave(cb, t, chaves)
                    if restaurado != do_arquivo:
                        problemas.append(f"{nome}: o arquivo não volta idêntico depois de restaurado")
                    if no_banco != do_arquivo:
                        diferentes = sum(1 for a, b in zip(do_arquivo, no_banco) if a != b) + abs(len(no_banco) - len(do_arquivo))
                        problemas.append(f"{nome}: {diferentes} linhas do arquivo diferem do banco")
        finally:
            vazio.dispose()
    return problemas


def _linhas_por_chave(c, t, chaves: list[tuple]) -> list[str]:
    """As linhas com estas chaves, na ordem da chave, serializadas como no arquivo."""
    cols = _chave(t)
    saida = []
    for lote in _em_lotes(chaves):
        filtro = cols[0].in_([k[0] for k in lote]) if len(cols) == 1 else tuple_(*cols).in_(lote)
        saida += [_serializar(x) for x in c.execute(select(t).where(filtro).order_by(*cols)).mappings()]
    return sorted(saida, key=lambda x: tuple(json.loads(x)[k.name] for k in cols))


def tirar(engine, pasta, url: str) -> dict[str, int]:
    """Tira do banco o que o arquivo tem, numa transação só: registra o arquivamento, guarda a impressão curta das
    notícias (regra 3) e apaga os filhos antes dos pais. Se uma contagem não bater, desfaz tudo."""
    pasta = Path(pasta)
    m = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
    agora = db.agora()
    tirados = {}
    with engine.begin() as c:
        chaves = {}
        for nome in TABELAS:
            t = _tabela(nome)
            with gzip.open(pasta / f"{nome}.jsonl.gz", "rt", encoding="utf-8") as f:
                chaves[nome] = [tuple(json.loads(x)[k.name] for k in _chave(t)) for x in f]
        with gzip.open(pasta / "documento.jsonl.gz", "rt", encoding="utf-8") as f:
            curtos = [dict(hash_curto=hash_curto(json.loads(x)["hash"]), arquivado_em=agora) for x in f]
        db.inserir_ignorando_repetidos(c, db.documento_arquivado, curtos, "hash_curto")
        for nome in reversed(TABELAS):
            t = _tabela(nome)
            cols = _chave(t)
            n = 0
            for lote in _em_lotes(chaves[nome]):
                filtro = cols[0].in_([k[0] for k in lote]) if len(cols) == 1 else tuple_(*cols).in_(lote)
                n += c.execute(t.delete().where(filtro)).rowcount
            if n != m["tabelas"][nome]["linhas"]:
                raise ValueError(f"{nome}: o arquivo tem {m['tabelas'][nome]['linhas']} linhas e o banco tirou {n}; "
                                 "nada saiu do banco")
            tirados[nome] = n
        for nome in TABELAS:
            x = m["tabelas"][nome]
            detalhe = json.dumps({"por_fonte": m["por_fonte"]}, ensure_ascii=False) if nome == "documento" else None
            corte = m["cortes"].get(nome, m["cortes"]["documento"])  # traduções e ligações seguem as notícias
            c.execute(db.arquivo.insert().values(
                etiqueta=m["etiqueta"], tabela=nome, corte=datetime.fromisoformat(corte.removesuffix("Z")),
                linhas=x["linhas"], sha256=x["sha256"], url=url, detalhe=detalhe, feito_em=agora))
    return {nome: tirados[nome] for nome in reversed(TABELAS)}


def conferir_e_tirar(engine, pasta, url: str) -> dict[str, int]:
    problemas = conferir(engine, pasta)
    if problemas:
        raise ValueError("o arquivo não confere com o banco; nada saiu do banco: " + "; ".join(problemas))
    return tirar(engine, pasta, url)


def restaurar(pasta, engine) -> dict[str, int]:
    """Devolve um arquivo a um banco: entra só o que não está lá (pela chave). Devolve quantas linhas entraram."""
    pasta = Path(pasta)
    entraram = {}
    with engine.begin() as c:
        for nome in TABELAS:
            t = _tabela(nome)
            antes = c.execute(select(func.count()).select_from(t)).scalar()
            with gzip.open(pasta / f"{nome}.jsonl.gz", "rt", encoding="utf-8") as f:
                linhas = [_ler(t, x) for x in f]
            for lote in _em_lotes(linhas):
                db.inserir_ignorando_repetidos(c, t, lote, [k.name for k in _chave(t)])
            entraram[nome] = c.execute(select(func.count()).select_from(t)).scalar() - antes
            if c.dialect.name == "postgresql" and "id" in t.c and t.c.id.autoincrement is True and entraram[nome]:
                # Os ids vieram do arquivo: o contador do PostgreSQL nunca volta para trás
                c.execute(text(f"select setval(s::regclass, greatest((select coalesce(max(id), 0) + 1 from {t.name}), "
                               f"nextval(s::regclass)), false) from pg_get_serial_sequence('{t.name}', 'id') as s"))
    return entraram


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Arquivo conferido do banco do Stratum Global (decisão 0015).")
    acao = p.add_mutually_exclusive_group(required=True)
    acao.add_argument("--separar", metavar="PASTA", help="grava o que passou do prazo; nada sai do banco")
    acao.add_argument("--conferir-e-tirar", metavar="PASTA", help="confere o que voltou do GitHub e só então tira")
    acao.add_argument("--restaurar", metavar="PASTA", help="devolve um arquivo a um banco, sem repetir")
    p.add_argument("--url", help="endereço do release do GitHub (com --conferir-e-tirar)")
    p.add_argument("--ensaio", action="store_true", help="prazo zero: para conferir o caminho numa branch")
    args = p.parse_args(argv)
    cfg = config.ler()
    if not cfg.banco_permanente:
        print("Sem banco (segredo SUPABASE_SENHA ou DATABASE_URL): nada a fazer.")
        return 1
    try:
        engine = db.conectar(cfg.database_url)
        db.preparar(engine)
    except Exception as exc:  # noqa: BLE001 - a mensagem pode ter dados da conexão (regra 12)
        print(f"Não foi possível abrir o banco ({type(exc).__name__}).")
        return 1
    if args.separar:
        prazos = {t: timedelta(0) for t in PRAZOS} if args.ensaio else PRAZOS
        m = separar(engine, args.separar, prazos=prazos)
        if m is None:
            print("Nada passou do prazo: nenhum arquivo.")
            return 0
        print(f"{m['etiqueta']}: " + ", ".join(f"{t} {x['linhas']}" for t, x in m["tabelas"].items())
              + ". Nada saiu do banco ainda.")
        return 0
    if args.conferir_e_tirar:
        if not args.url:
            print("Falta --url (o release do GitHub onde o arquivo ficou).")
            return 1
        try:
            tirados = conferir_e_tirar(engine, args.conferir_e_tirar, args.url)
        except ValueError as exc:
            print(f"Não tirado: {exc}")
            return 1
        print("Conferido e tirado do banco: " + ", ".join(f"{t} {n}" for t, n in tirados.items()) + f". Arquivo: {args.url}")
        return 0
    entraram = restaurar(args.restaurar, engine)
    print("Restaurado: " + ", ".join(f"{t} {n}" for t, n in entraram.items()) + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
