"""Resumo no Telegram 3 vezes ao dia: 7:30, 12:00 e 19:00 no horário de Brasília (decisão 0005).

Fora desses horários o Telegram não manda nada. Quem manda é a primeira rodada depois do horário; se ela atrasar
mais de 3 horas, aquele resumo é pulado e o seguinte cobre o período inteiro. Cada resumo enviado fica gravado
(tabela `resumo`), então nunca sai em dobro. Conteúdo por regra, sem IA.
"""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select

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


def _citacoes(docs: list[dict], por_fonte: dict, dicionario) -> tuple[dict[str, int], dict[str, list[dict]]]:
    """Notícias por país e as candidatas a destaque de cada país: primeiro as que têm o país no título
    (a notícia é sobre ele), depois as que só o citam no resumo; em cada grupo, da mais recente para a mais antiga."""
    contagem: dict[str, int] = {}
    do_pais: dict[str, list[dict]] = {}
    for d in sorted(docs, key=lambda d: (d["quando"], d["id"]), reverse=True):
        if (por_fonte.get(d["fonte_id"]) or {}).get("tipo") in export.NAO_CONTA:
            continue  # rede social nunca entra em conta (regra 4)
        for iso in paises.citados(f"{d['titulo']}\n{d['resumo'] or ''}", dicionario):
            contagem[iso] = contagem.get(iso, 0) + 1
            do_pais.setdefault(iso, []).append(d)
    for iso, lista in do_pais.items():
        no_titulo = [d for d in lista if iso in paises.citados(d["titulo"], dicionario)]
        do_pais[iso] = no_titulo + [d for d in lista if d not in no_titulo]
    return contagem, do_pais


def _hora(d: datetime) -> str:
    """'19/10 7:30' no horário de Brasília."""
    x = _local(d)
    return f"{x.day:02d}/{x.month:02d} {x.hour}:{x.minute:02d}"


def montar(engine, agora: datetime, horario: datetime, linha_agendador: str | None, site: str | None,
           copia: dict | None = None) -> str:
    """O texto do resumo.

    O período é pelo momento em que o robô soube da notícia (conhecido_em): cada notícia entra em um resumo só,
    mesmo a de uma fonte que volta depois de cair. Notícia com data da fonte de mais de 24 horas antes do período
    fica de fora (uma fonte que volta depois de dias não despeja notícia velha no resumo)."""
    with engine.connect() as c:
        anterior = c.execute(select(func.max(db.resumo.c.enviado_em))
                             .where(db.resumo.c.situacao == "enviado")).scalar()
        inicio = anterior or agora - PRIMEIRO_PERIODO
        antes_inicio = inicio - (agora - inicio)
        docs = [dict(d, quando=export.quando(d)) for d in c.execute(
            select(db.documento).where(db.documento.c.conhecido_em > antes_inicio,
                                       db.documento.c.conhecido_em <= agora)).mappings()]
        fontes = {f["id"]: f for f in c.execute(select(db.fonte)).mappings()}
        # Falhas desde o último resumo, não só as desta rodada: uma queda no meio do período também aparece
        coletas = c.execute(select(db.coleta.c.fonte_id, func.count(),
                                   func.sum(case((db.coleta.c.situacao == "falhou", 1), else_=0)),
                                   func.max(case((db.coleta.c.situacao == "falhou", db.coleta.c.erro))))
                            .where(db.coleta.c.iniciada_em > inicio).group_by(db.coleta.c.fonte_id)).all()
    dicionario = paises.carregar()
    periodo = [d for d in docs if d["conhecido_em"] > inicio and d["quando"] >= inicio - timedelta(hours=24)]
    periodo_anterior = [d for d in docs if d["conhecido_em"] <= inicio]
    contagem, do_pais = _citacoes(periodo, fontes, dicionario)
    contagem_antes, _ = _citacoes(periodo_anterior, fontes, dicionario)
    contaveis = [d for d in periodo if (fontes.get(d["fonte_id"]) or {}).get("tipo") not in export.NAO_CONTA]

    h = _local(horario)
    linhas = [f"Stratum Global · resumo das {h.hour}:{h.minute:02d} ({h.day:02d}/{h.month:02d})"]
    if not contaveis:
        linhas.append(f"Nenhuma notícia nova desde {_hora(inicio)}.")
    else:
        n_fontes = len({d["fonte_id"] for d in contaveis})
        linhas.append(f"Desde {_hora(inicio)}: {_plural(len(contaveis), 'notícia', 'notícias')} de "
                      f"{_plural(n_fontes, 'fonte', 'fontes')}, {_plural(len(contagem), 'país citado', 'países citados')}.")
        ranking = sorted(contagem.items(),
                         key=lambda kv: (-kv[1], export.ordem_alfabetica(dicionario.nome(kv[0]) or kv[0]), kv[0]))
        if ranking:
            linhas += ["", f"Mais citados (entre parênteses, quantas notícias de {_hora(antes_inicio)} a {_hora(inicio)}):"]
            for i, (iso, n) in enumerate(ranking[:MAIS_CITADOS], 1):
                linhas.append(f"{i}. {dicionario.nome(iso) or iso}: {n} ({contagem_antes.get(iso, 0)})")
            usados: set[int] = set()
            destaques = []
            for iso, _ in ranking:
                if len(destaques) == DESTAQUES:
                    break
                d = next((x for x in do_pais[iso] if x["id"] not in usados), None)
                if d is None:
                    continue
                usados.add(d["id"])
                fonte = (fontes.get(d["fonte_id"]) or {}).get("nome", d["fonte_id"])
                destaques.append(f"• {dicionario.nome(iso) or iso}: {d['titulo']} ({fonte})" + (f"\n  {d['url']}" if d["url"] else ""))
            linhas += ["", "Destaques (a notícia mais recente com o país no título):", *destaques]
    problemas = []
    for fonte_id, total, falhou, erro in sorted(coletas, key=lambda x: x[0]):
        if falhou:
            nome = (fontes.get(fonte_id) or {}).get("nome", fonte_id)
            problemas.append(f"• {nome}: falhou em {falhou} de {_plural(total, 'coleta', 'coletas')}"
                             + (f" ({str(erro).rstrip('.')})" if erro else "") + ".")
    if problemas:
        problemas.insert(0, "Fontes com problema desde o último resumo:")
    if linha_agendador:
        problemas.append(f"Agendador: {linha_agendador}.")
    if copia and copia["situacao"] in ("atrasada", "nenhuma"):  # cópia semanal do banco (decisão 0007)
        problemas.append(f"Cópia do banco: {copia['texto']}"
                         + (f" (a última é de {_hora(datetime.fromisoformat(copia['ultima'].rstrip('Z')))})"
                            if copia["ultima"] else "") + ".")
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


def talvez_enviar(engine, agora: datetime, linha_agendador: str | None, repositorio: str | None,
                  telegram_configurado: bool, enviar, banco_permanente: bool = True, copia: dict | None = None) -> str:
    """Manda o resumo se for a hora.
    Devolve o que aconteceu: sem_banco | fora_do_horario | enviado | sem_telegram | falhou."""
    if not banco_permanente:
        return "sem_banco"  # banco temporário não lembra do resumo anterior: mandaria um a cada rodada
    horario = pendente(engine, agora)
    if horario is None:
        return "fora_do_horario"
    texto = montar(engine, agora, horario, linha_agendador, site_do_repositorio(repositorio), copia)
    if not telegram_configurado:
        registrar(engine, horario, agora, "sem_telegram", texto)
        return "sem_telegram"
    if not enviar(texto):
        return "falhou"  # nada gravado: a próxima rodada tenta de novo, dentro das 3 horas
    registrar(engine, horario, agora, "enviado", texto)
    return "enviado"
