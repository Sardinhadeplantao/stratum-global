"""Resumo no Telegram 3 vezes ao dia: 7:30, 12:00 e 19:00 no horário de Brasília (decisão 0005).

Fora desses horários o Telegram não manda nada. Quem manda é a primeira rodada depois do horário; se ela atrasar
mais de 3 horas, aquele resumo é pulado e o seguinte cobre o período inteiro. Cada resumo enviado fica gravado
(tabela `resumo`), então nunca sai em dobro. Conteúdo por regra, sem IA.
"""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from stratum import db, export
from stratum.domain import paises

FUSO = ZoneInfo("America/Sao_Paulo")
HORARIOS = (time(7, 30), time(12, 0), time(19, 0))
ATRASO_MAXIMO = timedelta(hours=3)
PRIMEIRO_PERIODO = timedelta(hours=12)   # sem resumo anterior: as últimas 12 horas
MAIS_CITADOS = 5
DESTAQUES = 3
LIMITE_TELEGRAM = 4000                   # o Telegram aceita até 4096 caracteres


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _local(d: datetime) -> datetime:
    return d.replace(tzinfo=timezone.utc).astimezone(FUSO)


def _utc(d: datetime) -> datetime:
    return d.astimezone(timezone.utc).replace(tzinfo=None)


def horario_devido(agora: datetime) -> datetime:
    """O horário de resumo mais recente que já passou (UTC, sem fuso, como as outras datas do banco)."""
    local = _local(agora)
    passados = [datetime.combine(local.date() - timedelta(days=d), h, tzinfo=FUSO)
                for d in (0, 1) for h in HORARIOS]
    return _utc(max(p for p in passados if p <= local))


def pendente(engine, agora: datetime) -> datetime | None:
    """O horário cujo resumo deve sair agora, ou None (já saiu, ou passou da hora)."""
    horario = horario_devido(agora)
    if agora - horario > ATRASO_MAXIMO:
        return None
    with engine.connect() as c:
        ja_saiu = c.execute(select(db.resumo.c.id).where(db.resumo.c.horario == horario)).first()
    return None if ja_saiu else horario


def _citacoes(docs: list[dict], por_fonte: dict, dicionario) -> tuple[dict[str, int], dict[str, dict]]:
    """Notícias por país e a mais recente de cada país (docs já vêm do mais recente para o mais antigo)."""
    contagem: dict[str, int] = {}
    recente: dict[str, dict] = {}
    for d in docs:
        if (por_fonte.get(d["fonte_id"]) or {}).get("tipo") in export.NAO_CONTA:
            continue  # rede social nunca entra em conta (regra 4)
        for iso in paises.citados(f"{d['titulo']}\n{d['resumo'] or ''}", dicionario):
            contagem[iso] = contagem.get(iso, 0) + 1
            recente.setdefault(iso, d)
    return contagem, recente


def montar(engine, agora: datetime, horario: datetime, falhas: list[str], linha_agendador: str | None,
           site: str | None) -> str:
    """O texto do resumo. falhas: nomes das fontes com problema nesta rodada, com o motivo."""
    with engine.connect() as c:
        anterior = c.execute(select(func.max(db.resumo.c.enviado_em))
                             .where(db.resumo.c.situacao == "enviado")).scalar()
        inicio = anterior or agora - PRIMEIRO_PERIODO
        antes_inicio = inicio - (agora - inicio)
        docs = export.documentos_desde(c, antes_inicio)
        fontes = {f["id"]: f for f in c.execute(select(db.fonte)).mappings()}
    dicionario = paises.carregar()
    periodo = [d for d in docs if inicio <= d["quando"] <= agora]
    periodo_anterior = [d for d in docs if d["quando"] < inicio]
    contagem, recente = _citacoes(periodo, fontes, dicionario)
    contagem_antes, _ = _citacoes(periodo_anterior, fontes, dicionario)
    contaveis = [d for d in periodo if (fontes.get(d["fonte_id"]) or {}).get("tipo") not in export.NAO_CONTA]

    h = _local(horario)
    linhas = [f"Stratum Global · resumo das {h:%H:%M} ({h:%d/%m})".replace("07:30", "7:30")]
    if not contaveis:
        linhas.append(f"Nenhuma notícia nova desde {_local(inicio):%d/%m %H:%M}.")
    else:
        n_fontes = len({d["fonte_id"] for d in contaveis})
        linhas.append(f"Desde {_local(inicio):%d/%m %H:%M}: {_plural(len(contaveis), 'notícia', 'notícias')} de "
                      f"{_plural(n_fontes, 'fonte', 'fontes')}, {_plural(len(contagem), 'país citado', 'países citados')}.")
        ranking = sorted(contagem.items(), key=lambda kv: (-kv[1], export.ordem_alfabetica(dicionario.nome(kv[0]) or kv[0]), kv[0]))
        if ranking:
            linhas += ["", "Mais citados (entre parênteses, no período anterior de mesma duração):"]
            for i, (iso, n) in enumerate(ranking[:MAIS_CITADOS], 1):
                linhas.append(f"{i}. {dicionario.nome(iso) or iso}: {n} ({contagem_antes.get(iso, 0)})")
            usados: set[int] = set()
            destaques = []
            for iso, _ in ranking:
                if len(destaques) == DESTAQUES:
                    break
                d = recente[iso]
                if d["id"] in usados:
                    continue
                usados.add(d["id"])
                fonte = (fontes.get(d["fonte_id"]) or {}).get("nome", d["fonte_id"])
                destaques.append(f"• {dicionario.nome(iso) or iso}: {d['titulo']} ({fonte})" + (f"\n  {d['url']}" if d["url"] else ""))
            linhas += ["", "A notícia mais recente de cada um dos mais citados:", *destaques]
    problemas = []
    if falhas:
        problemas.append("Fontes com problema: " + "; ".join(falhas) + ".")
    if linha_agendador:
        problemas.append(f"Agendador: {linha_agendador}.")
    if problemas:
        linhas += ["", *problemas]
    if site:
        linhas += ["", f"Mapa e todas as notícias: {site}"]
    texto = "\n".join(linhas)
    return texto if len(texto) <= LIMITE_TELEGRAM else texto[:LIMITE_TELEGRAM - 1] + "…"


def registrar(engine, horario: datetime, agora: datetime, situacao: str, texto: str) -> None:
    with engine.begin() as c:
        db.inserir_ignorando_repetidos(c, db.resumo, [dict(horario=horario, enviado_em=agora, situacao=situacao,
                                                           texto=texto)], "horario")


def site_do_repositorio(repositorio: str | None) -> str | None:
    """'Dono/nome' -> endereço do GitHub Pages."""
    if not repositorio or "/" not in repositorio:
        return None
    dono, nome = repositorio.split("/", 1)
    return f"https://{dono.lower()}.github.io/{nome}/"


def talvez_enviar(engine, agora: datetime, falhas: list[str], linha_agendador: str | None, repositorio: str | None,
                  telegram_configurado: bool, enviar) -> str:
    """Manda o resumo se for a hora. Devolve o que aconteceu: fora_do_horario | enviado | sem_telegram | falhou."""
    horario = pendente(engine, agora)
    if horario is None:
        return "fora_do_horario"
    texto = montar(engine, agora, horario, falhas, linha_agendador, site_do_repositorio(repositorio))
    if not telegram_configurado:
        registrar(engine, horario, agora, "sem_telegram", texto)
        return "sem_telegram"
    if not enviar(texto):
        return "falhou"  # nada gravado: a próxima rodada tenta de novo, dentro das 3 horas
    registrar(engine, horario, agora, "enviado", texto)
    return "enviado"
