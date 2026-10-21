import Titulo from "@/components/Titulo";
import { datasDocumento, estadoPonto, plural } from "@/lib/formatar";
import type { Ponto } from "@/lib/status";
import type { Selecao } from "./Inicio";
import LinhaMercado from "./LinhaMercado";

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
        <h3>Mercados ligados</h3>
        {ponto.mercados.length === 0 ? <p className="sem-dado-texto">Sem série ligada nesta atualização.</p>
          : <ul className="lista-mercados">{ponto.mercados.map((s) => <LinhaMercado key={s.id} s={s} />)}</ul>}
        <p className="discreto">Coincidência no tempo, não causa: o preço reage a muita coisa ao mesmo tempo.</p>
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
