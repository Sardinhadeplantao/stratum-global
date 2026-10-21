import Reacao from "@/components/Reacao";
import Titulo from "@/components/Titulo";
import { datasDocumento, dia, estadoPonto, leituraSerie, media, percentualInteiro, plural, textoMudanca } from "@/lib/formatar";
import type { Navios, Ponto } from "@/lib/status";
import type { Selecao } from "./Inicio";
import LinhaMercado from "./LinhaMercado";
import Minigrafico from "./Minigrafico";

/** Contexto de um ponto crítico (decisão 0014): o estado pela regra, por que importa (com fonte e período), quem está
 * nas margens, os mercados ligados e as notícias que o citam. */
export default function PainelPonto({ ponto, voltar, selecionar }: {
  ponto: Ponto; voltar: () => void; selecionar: (s: Selecao) => void;
}) {
  const e = estadoPonto(ponto.estado);
  return (
    <div className="detalhe" aria-label={`Contexto: ${ponto.nome}`}>
      <div className="painel-topo">
        <div>
          <button type="button" className="link voltar" onClick={voltar}>← Voltar</button>
          <h2>{ponto.nome}</h2>
          <span className={`selo-estado ${e.classe}`}>{e.texto}</span>
        </div>
      </div>
      <p className="discreto">{e.explica}</p>
      <p className="destaque-numero">
        {ponto.noticias > 0 ? <>{plural(ponto.noticias, "notícia cita", "notícias citam")} o ponto nas últimas 24 horas,
          de {plural(ponto.vozes, "voz independente", "vozes independentes")}</> : "Nenhuma notícia cita o ponto nas últimas 24 horas."}
      </p>

      <section>
        <h3>Por que importa</h3>
        {ponto.fatos.length === 0 ? <p className="sem-dado-texto">Ainda sem número com fonte conferida para este ponto.</p> : (
          <ul className="lista-fatos">
            {ponto.fatos.map((f, i) => (
              <li key={i}>{f.texto}. <span className="discreto">({f.periodo}; <a href={f.url} target="_blank" rel="noreferrer">{f.fonte}</a>)</span></li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3>Nas margens</h3>
        <div className="feed-paises">
          {ponto.margens.map((m) => (
            <button key={m.iso} type="button" className="chip" onClick={() => selecionar({ tipo: "pais", id: m.iso })}>{m.nome}</button>
          ))}
        </div>
      </section>

      <section>
        <h3>Navios no estreito</h3>
        {(ponto.navios ?? []).length === 0 ? <p className="sem-dado-texto">Sem dado do PortWatch nesta atualização.</p>
          : <ul className="lista-navios">{ponto.navios!.map((n) => <LinhaNavios key={n.id} n={n} />)}</ul>}
        {ponto.portwatch_nota && <p className="discreto">{ponto.portwatch_nota}</p>}
        <p className="discreto">
          Fonte: <a href="https://portwatch.imf.org/" target="_blank" rel="noreferrer">FMI, PortWatch</a>, atualizado uma vez
          por semana; a média de 7 dias é conta do Stratum. Conta os navios pelo sinal (AIS) que eles transmitem: navio com
          o sinal desligado não aparece.
        </p>
      </section>

      <section>
        <h3>Mercados ligados</h3>
        {ponto.mercados.length === 0 ? <p className="sem-dado-texto">Sem série ligada nesta atualização.</p>
          : <ul className="lista-mercados">{ponto.mercados.map((s) => <LinhaMercado key={s.id} s={s} />)}</ul>}
        {ponto.reacao ? <><h4>Reação desde a primeira notícia das últimas 24 horas</h4><Reacao r={ponto.reacao} /></>
          : <p className="discreto">Coincidência no tempo, não causa: o preço reage a muita coisa ao mesmo tempo.</p>}
      </section>

      <section>
        <h3>Notícias que citam o ponto</h3>
        {ponto.documentos.length === 0 ? <p className="discreto">Nenhuma nas últimas 24 horas.</p> : (
          <ul className="lista-noticias">
            {ponto.documentos.map((d, i) => (
              <li key={i}>
                {d.acao && <span className="selo-acao">ação</span>} <Titulo {...d} />
                <div className="discreto">{d.fonte_nome} · {datasDocumento(d.publicado_em, d.conhecido_em)}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h3>Atores e incentivos</h3>
        <p className="sem-dado-texto">Próxima etapa: quem disputa o ponto e o que cada um declarou querer, sempre com o documento
          citado. É análise, por isso entra com regra própria (decisão 0014).</p>
      </section>
    </div>
  );
}

/** Navios por dia (decisão 0018): a média de 7 dias pela régua, um ano antes e o último ano no minigráfico. */
function LinhaNavios({ n }: { n: Navios }) {
  const l = leituraSerie(n.situacao, n.extremo);
  return (
    <li>
      <div className="nv-linha">
        <span className="nv-nome"><b>{n.simbolo}</b><small className="discreto">por dia, média de 7 dias{n.data ? ` até ${dia(n.data).slice(0, 5)}` : ""}</small></span>
        <span className={`nv-valor numero ${n.extremo ? "fora" : ""}`}>{media(n.media_7d)}</span>
        <Minigrafico valores={n.ano} fora={!!n.extremo} />
      </div>
      <p className="nv-detalhe">
        <span className={`ponto ${l.classe}`} aria-hidden /> {l.texto}
        {n.percentil !== null && <> (percentil {n.percentil.toLocaleString("pt-BR")} dos últimos 5 anos)</>}
        {n.um_ano_antes !== null && <> · um ano antes: {media(n.um_ano_antes)} ({percentualInteiro(n.contra_um_ano)})</>}
        {n.faixa && <> · normal: {media(n.faixa[0])} a {media(n.faixa[1])}</>}
      </p>
      {n.mudancas.map((m, i) => <p key={i} className="nv-detalhe discreto">{textoMudanca(m)}</p>)}
    </li>
  );
}
