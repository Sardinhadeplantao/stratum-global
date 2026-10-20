"""Cópia semanal do banco (decisão 0007).

O Supabase gratuito não faz cópia de segurança, e o banco só recebe inserções (regra 2). Uma vez por semana, o
workflow `copia.yml` copia as tabelas do projeto para arquivos (uma linha JSON por registro, comprimida), restaura a
cópia num banco vazio e confere que ela volta idêntica. A cópia fica no GitHub, pública como o repositório: só entram
as tabelas do projeto (`db.md`). O cofre, o pg_cron e o pg_net ficam de fora.

O manifesto da cópia traz o tamanho do banco e de cada tabela: é a medida para a decisão de retenção (fase 1).

Uso:  python -m stratum.copia --saida PASTA        copia o banco e testa a restauração
      python -m stratum.copia --restaurar PASTA    recria tudo num banco vazio (por exemplo, um Supabase novo)
"""
import argparse
import gzip
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import DateTime, func, select, text

from stratum import VERSAO, config, db

FORMATO = 1
ARTEFATO = "copia-banco"                 # nome do artefato no GitHub (o robô procura por ele)
PRAZO = timedelta(days=8)                # uma por semana, com um dia de folga
LOTE = 1000

TEXTOS = {
    "ok": "em dia",
    "atrasada": "atrasada: o normal é uma por semana",
    "nenhuma": "nenhuma cópia feita ainda",
    "sem_dado": "não conferida nesta rodada",
}


def tabelas():
    """Só as tabelas do projeto, na ordem em que podem ser inseridas (pais antes dos filhos)."""
    return list(db.md.sorted_tables)


def _iso(d: datetime | None) -> str | None:
    return d.isoformat(timespec="seconds") + "Z" if d else None


def exportar(engine, pasta) -> dict:
    """Grava cada tabela em `<tabela>.jsonl.gz` e o `manifesto.json`. Devolve o manifesto.

    Tudo é lido numa transação só (no PostgreSQL, com foto fixa do banco), então uma rodada do robô gravando ao mesmo
    tempo não deixa a cópia pela metade."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    manifesto = {"formato": FORMATO, "versao_robo": VERSAO, "feita_em": _iso(db.agora()), "tabelas": {}}
    postgres = engine.dialect.name == "postgresql"
    with engine.connect().execution_options(**({"isolation_level": "REPEATABLE READ"} if postgres else {})) as c:
        with c.begin():
            manifesto["migracao"] = c.execute(text("select version_num from alembic_version")).scalar()
            for t in tabelas():
                n = 0
                consulta = select(t).order_by(*t.primary_key.columns).execution_options(yield_per=LOTE)
                with gzip.open(pasta / f"{t.name}.jsonl.gz", "wt", encoding="utf-8") as f:
                    for linha in c.execute(consulta).mappings():
                        registro = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in linha.items()}
                        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
                        n += 1
                manifesto["tabelas"][t.name] = {"linhas": n}
            if postgres:  # o limite do plano gratuito é sobre o banco inteiro (500 MB)
                manifesto["tamanho_banco_mb"] = round(
                    c.execute(text("select pg_database_size(current_database())")).scalar() / 2**20, 1)
                for t in tabelas():
                    manifesto["tabelas"][t.name]["tamanho_mb"] = round(c.execute(
                        text("select pg_total_relation_size(cast(:t as regclass))"), {"t": t.name}).scalar() / 2**20, 2)
    (pasta / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifesto


def restaurar(pasta, engine) -> dict[str, int]:
    """Recria o banco a partir de uma cópia. Só num banco vazio: nada é sobrescrito (regra 2).

    As tabelas sobem pelas migrações só até a versão do esquema da cópia, os registros entram e só então o banco sobe
    até a versão do código. Assim, uma cópia feita antes de uma migração continua restaurável. Cópia de uma versão
    que o código não conhece é recusada, para nenhuma coluna se perder em silêncio. Devolve as linhas por tabela."""
    pasta = Path(pasta)
    manifesto = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
    versao = manifesto.get("migracao")
    if versao not in db.versoes_do_esquema():
        raise ValueError(f"a cópia é da versão {versao} do esquema, que este código não conhece; "
                         f"restaure com o código da versão {manifesto.get('versao_robo')} do robô ou mais nova")
    por_nome = {t.name: t for t in tabelas()}
    desconhecidas = sorted(set(manifesto["tabelas"]) - set(por_nome))
    if desconhecidas:
        raise ValueError(f"a cópia tem tabelas que este código não conhece ({', '.join(desconhecidas)})")
    no_banco = db.versao_do_banco(engine)
    if no_banco not in (None, versao):
        raise ValueError(f"o banco de destino já foi preparado na versão {no_banco} do esquema; use um banco novo")
    db.preparar(engine, ate=versao)
    contagens = {}
    da_copia = [t for t in tabelas() if t.name in manifesto["tabelas"]]  # pais antes dos filhos
    with engine.begin() as c:
        ocupadas = [t.name for t in da_copia if c.execute(select(func.count()).select_from(t)).scalar()]
        if ocupadas:
            raise ValueError(f"o banco de destino não está vazio ({', '.join(ocupadas)})")
        for t in da_copia:
            colunas = set(t.c.keys())
            datas = [col.name for col in t.columns if isinstance(col.type, DateTime)]
            lote, n = [], 0
            with gzip.open(pasta / f"{t.name}.jsonl.gz", "rt", encoding="utf-8") as f:
                for linha in f:
                    registro = json.loads(linha)
                    if extras := set(registro) - colunas:
                        raise ValueError(f"{t.name}: a cópia tem colunas que este código não conhece "
                                         f"({', '.join(sorted(extras))})")
                    for k in datas:
                        if registro.get(k) is not None:
                            registro[k] = datetime.fromisoformat(registro[k])
                    lote.append(registro)
                    n += 1
                    if len(lote) == LOTE:
                        c.execute(t.insert(), lote)
                        lote = []
            if lote:
                c.execute(t.insert(), lote)
            if n != manifesto["tabelas"][t.name]["linhas"]:  # desfaz tudo: a transação não termina
                raise ValueError(f"{t.name}: a cópia diz {manifesto['tabelas'][t.name]['linhas']} linhas, "
                                 f"o arquivo tem {n}")
            contagens[t.name] = n
            if c.dialect.name == "postgresql" and "id" in t.c and t.c.id.autoincrement is True:
                # Os ids vieram da cópia: o contador do PostgreSQL precisa continuar depois do maior
                c.execute(text(f"select setval(pg_get_serial_sequence('{t.name}', 'id'), "
                               f"coalesce((select max(id) from {t.name}), 0) + 1, false)"))
    db.preparar(engine)  # agora sim, até a versão do código
    return contagens


def diferencas(pasta_a, pasta_b) -> list[str]:
    """Compara duas cópias tabela por tabela, linha por linha. Lista vazia = idênticas."""
    saida = []
    for t in tabelas():
        with gzip.open(Path(pasta_a) / f"{t.name}.jsonl.gz", "rt", encoding="utf-8") as a, \
                gzip.open(Path(pasta_b) / f"{t.name}.jsonl.gz", "rt", encoding="utf-8") as b:
            la, lb = a.read().splitlines(), b.read().splitlines()
        if la != lb:
            primeira = next((i for i, (x, y) in enumerate(zip(la, lb)) if x != y), min(len(la), len(lb)))
            saida.append(f"{t.name}: {len(la)} linhas na cópia, {len(lb)} na restauração, primeira diferença na linha "
                         f"{primeira + 1}")
    return saida


def testar_restauracao(pasta) -> list[str]:
    """Restaura a cópia num SQLite vazio, copia de novo e compara. Lista vazia = a cópia volta idêntica."""
    with tempfile.TemporaryDirectory(prefix="stratum-restauracao-") as tmp:
        engine = db.conectar(f"sqlite:///{tmp}/restaurado.db")
        try:
            restaurar(pasta, engine)
            exportar(engine, Path(tmp) / "de-novo")
            return diferencas(pasta, Path(tmp) / "de-novo")
        finally:
            engine.dispose()


def situacao(ultima: str | None, agora: datetime) -> dict:
    """Estado da cópia para o status.json e o resumo.

    `ultima` vem do workflow do robô (variável STRATUM_ULTIMA_COPIA): a data da cópia mais recente no GitHub,
    texto vazio se não há nenhuma, ou ausente (None) se não deu para conferir."""
    if ultima is None:
        estado, quando = "sem_dado", None
    elif not ultima.strip() or ultima.strip() == "null":
        estado, quando = "nenhuma", None
    else:
        try:
            quando = datetime.fromisoformat(ultima.strip().replace("Z", "+00:00"))
        except ValueError:
            estado, quando = "sem_dado", None
        else:
            if quando.tzinfo is not None:
                quando = quando.astimezone(timezone.utc).replace(tzinfo=None)
            estado = "ok" if agora - quando <= PRAZO else "atrasada"
    return {"situacao": estado, "texto": TEXTOS[estado], "ultima": _iso(quando)}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Copia o banco do Stratum Global e testa a restauração.")
    acao = p.add_mutually_exclusive_group(required=True)
    acao.add_argument("--saida", help="pasta onde gravar a cópia")
    acao.add_argument("--restaurar", help="pasta de uma cópia, para recriar tudo num banco vazio")
    args = p.parse_args(argv)
    cfg = config.ler()
    if not cfg.banco_permanente:
        print("Sem banco permanente (segredo SUPABASE_SENHA): nada a " + ("restaurar." if args.restaurar else "copiar."))
        return 1
    if args.restaurar:
        try:
            contagens = restaurar(args.restaurar, db.conectar(cfg.database_url))
        except ValueError as exc:  # banco de destino com dados: recusa, nunca sobrescreve
            print(f"Restauração recusada: {exc}.")
            return 1
        except Exception as exc:  # só o tipo (regra 12)
            print(f"Não foi possível restaurar ({type(exc).__name__}).")
            return 1
        print("Restaurado: " + ", ".join(f"{nome} {n}" for nome, n in contagens.items()) + ".")
        return 0
    try:
        engine = db.conectar(cfg.database_url)
        manifesto = exportar(engine, args.saida)
    except Exception as exc:  # a mensagem pode conter dados da conexão: só o tipo (regra 12)
        print(f"Não foi possível copiar o banco ({type(exc).__name__}).")
        return 1
    for nome, info in manifesto["tabelas"].items():
        tamanho = f", {info['tamanho_mb']} MB" if "tamanho_mb" in info else ""
        print(f"{nome}: {info['linhas']} linhas{tamanho}")
    if "tamanho_banco_mb" in manifesto:
        print(f"Banco inteiro: {manifesto['tamanho_banco_mb']} MB de 500 MB do plano gratuito.")
    problemas = testar_restauracao(args.saida)
    if problemas:
        print("A cópia NÃO volta idêntica:")
        for linha in problemas:
            print(f"  {linha}")
        return 1
    print("Restauração testada: a cópia volta idêntica.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
