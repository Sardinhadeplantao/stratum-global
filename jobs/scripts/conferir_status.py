"""Conferência da rodada: lê o status.json que o site vai mostrar e imprime um resumo com os números reais.

Roda no fim de cada rodada do robô (workflow robo.yml), para conferir cada etapa pelo log do GitHub sem abrir o site:
fontes com falha, notícias, histórias e a leitura de cada série. Só lê; não muda nada.

Uso:  python scripts/conferir_status.py CAMINHO/status.json
"""
import json
import sys

LEITURA = {"ok": "dentro do normal", "nao_confere": "NÃO CONFERE com a fonte oficial", "parada": "parada (dado velho)",
           "historico_curto": "histórico curto", "sem_dado": "sem dado"}


def _n(x, casas=2, sinal=False):
    if x is None:
        return "—"
    return (f"{x:+.{casas}f}" if sinal else f"{x:.{casas}f}").replace(".", ",")


def main(caminho: str) -> int:
    try:
        s = json.load(open(caminho, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Sem status para conferir ({type(exc).__name__}).")
        return 0
    r = s.get("ultima_rodada") or {}
    print(f"Rodada {r.get('id')}: {r.get('situacao')} · banco {s.get('banco')} · robô {s.get('versao_robo')} · "
          f"gerado {s.get('gerado_em')}")
    if s.get("erro_banco"):
        print(f"  {s['erro_banco']}")
    t = s.get("totais") or {}
    print(f"Fontes: {t.get('fontes_ok')} de {t.get('fontes')} funcionando")
    for f in s.get("fontes") or []:
        c = f.get("ultima_coleta") or {}
        if f.get("ativa") and c.get("situacao") != "ok":
            print(f"  FALHOU {f['id']}: {c.get('erro') or 'sem coleta'}")
    h = s.get("contagem_historias") or {}
    print(f"Notícias: {t.get('documentos')} no total, {t.get('documentos_24h')} nas últimas 24h · "
          f"histórias: {h.get('total')} ({h.get('varias_vozes')} com 2 ou mais vozes)")
    m = s.get("mercados")
    if not m:
        print("Mercados: sem dado")
        return 0
    print(f"Mercados ({m['regua']['versao']}): {len(m['series'])} séries, {m['fora_do_normal']} fora do normal, "
          f"{m.get('nao_conferem', 0)} não conferem")
    for x in m["series"]:
        leitura = {"alta": "FORA DO NORMAL: alta", "baixa": "FORA DO NORMAL: queda"}.get(x.get("extremo")) \
            or LEITURA.get(x["situacao"], x["situacao"])
        conf = x.get("conferencia")
        conferida = (f" · {conf['com']} {conf['data']}: {_n(conf['diferenca'], sinal=True)}% "
                     f"{'confere' if conf['confere'] else 'NÃO CONFERE'}") if conf else ""
        print(f"  {x['nome']}: {x.get('data')}{' (em andamento)' if x.get('parcial') else ''} = {x.get('valor')}"
              f" · {_n(x.get('variacao'), sinal=True)}% · percentil {_n(x.get('percentil'), 1)} · {leitura}{conferida}")
        for mu in x.get("mudancas") or []:
            print(f"    mudança: {mu['tipo']} ({mu['sentido']}) desde {mu['desde']}, "
                  f"{mu['taxa_base']['vezes']} vezes em {mu['taxa_base']['anos']} anos")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "../web/public/dados/status.json"))
