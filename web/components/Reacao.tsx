import { dataHora, dia, situacaoReacao, textoTaxaBase, variacaoSerie } from "@/lib/formatar";
import type { Reacao as TipoReacao } from "@/lib/status";

/** A reação do mercado a um evento (decisão 0017): os ativos ligados, o dia do evento e o pregão seguinte pela régua de
 * sempre, a variação desde o evento e a taxa-base. Tudo vem pronto do robô (regra 9). `compacta`: uma linha, para listas. */
export default function Reacao({ r, compacta = false }: { r: TipoReacao | null | undefined; compacta?: boolean }) {
  if (!r) return null;
  const sit = situacaoReacao(r.situacao);
  if (compacta) {
    if (r.situacao === "sem_ativo") return null;
    const fora = r.ativos.filter((a) => a.extremo);
    return (
      <div className="reacao-linha">
        <span className={`ponto ${sit.classe}`} aria-hidden /> Mercados:{" "}
        {fora.length > 0 ? fora.slice(0, 2).map((a, i) => {
          const d = a.dias.find((x) => x.extremo);
          return <span key={a.id}>{i > 0 && ", "}<b>{a.simbolo}</b> {variacaoSerie(d?.variacao, a.medida)}{d?.parcial ? " hoje" : ""}</span>;
        }) : r.situacao === "normal" ? `${r.ativos.length === 1 ? "o ativo ligado está" : `os ${r.ativos.length} ativos ligados estão`} dentro do normal`
          : "ainda sem pregão desde o evento"}
        {fora.length > 0 && <> fora do normal{r.taxa_base && <small className="discreto"> (acontece em {r.taxa_base.pct}% dos períodos de {r.taxa_base.dias} pregões)</small>}</>}
      </div>
    );
  }
  return (
    <div className="reacao">
      <p className="reacao-topo"><span className={`ponto ${sit.classe}`} aria-hidden /> <b>{sit.texto}</b></p>
      <p className="discreto reacao-desde">Desde a 1ª notícia, {dataHora(r.inicio)}</p>
      {r.ativos.length > 0 && (
        <>
          <div className="ra-cabecalho discreto" aria-hidden><span>Ativo</span><span>Dia do evento e o seguinte</span><span>Desde o evento</span></div>
          <ul className="reacao-ativos">
            {r.ativos.map((a) => (
              <li key={a.id}>
                <span className="ra-nome"><b>{a.simbolo}</b><small className="discreto">por {a.por.nome}</small></span>
                <span className="ra-dias">
                  {a.dias.length === 0 ? <small className="discreto">sem pregão</small> : a.dias.map((d) => (
                    <span key={d.data} className={`ra-dia numero ${d.extremo ? "fora" : ""}`}
                          title={d.percentil === null ? "Sem leitura da régua neste dia"
                            : `Percentil ${d.percentil.toLocaleString("pt-BR")} dos últimos 5 anos${d.extremo ? ": fora do normal" : ""}`}>
                      <small>{d.parcial ? "hoje" : dia(d.data).slice(0, 5)}</small> {variacaoSerie(d.variacao, a.medida)}
                    </span>
                  ))}
                </span>
                <span className="ra-desde numero" title={a.troca_de_contrato ? "Troca de contrato futuro no período: os preços são de contratos diferentes"
                  : a.base ? `Do fechamento de ${dia(a.base.data)} até o último valor${a.parcial ? " (dia em andamento)" : ""}` : "Sem fechamento antes do evento"}>
                  {a.troca_de_contrato ? <small className="discreto">troca de contrato</small> : variacaoSerie(a.desde, a.medida)}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="discreto nota-reacao">
        {r.ativos.length > 0 && <>{textoTaxaBase(r.taxa_base, r.ativos.length)} </>}
        Coincidência no tempo, não causa: o preço reage a muita coisa ao mesmo tempo.
      </p>
    </div>
  );
}
