import Link from "next/link";
import { continente, datasDocumento, estadoPonto, plural } from "@/lib/formatar";
import type { MercadoResumo, PaisAtencao, Ponto } from "@/lib/status";
import Titulo from "@/components/Titulo";
import type { Selecao } from "@/components/inicio/Inicio";
import LinhaMercado from "@/components/inicio/LinhaMercado";

/** Propriedades de cada país em public/geo/paises.geojson (gerado por jobs/scripts/preparar_paises.py). */
export type Pais = {
  iso: string; iso_oficial: boolean; iso2: string | null; nome: string; nome_en: string;
  wikidata: string | null; continente: string | null; regiao: string | null; centro?: [number, number] | null;
};

type Props = {
  pais: Pais; atencao: PaisAtencao | null; janelaHoras: number; semDado: boolean; fechar: () => void;
  mercados: MercadoResumo[]; pontos: Ponto[]; selecionar: (s: Selecao) => void;
};

/** Contexto de um país no painel da direita: as notícias que o citam, as histórias, os mercados dele e os pontos
 * críticos nas suas margens. Tudo vem pronto do robô. */
export default function PainelPais({ pais, atencao, janelaHoras, semDado, fechar, mercados, pontos, selecionar }: Props) {
  return (
    <div className="detalhe" aria-label={`Contexto: ${pais.nome}`}>
      <div className="painel-topo">
        <div>
          <button type="button" className="link voltar" onClick={fechar}>← Voltar</button>
          <h2>{pais.nome}</h2>
          {pais.nome_en && pais.nome_en !== pais.nome && <p className="discreto">{pais.nome_en}</p>}
        </div>
      </div>

      <section>
        <h3>Nas últimas {janelaHoras} horas</h3>
        {semDado ? (
          <p className="sem-dado-texto">Sem dado nesta atualização: o robô não publicou a contagem.</p>
        ) : atencao ? (<>
          <p className="destaque-numero">{plural(atencao.citacoes, "notícia cita", "notícias citam")} este país</p>
          <ul className="lista-noticias">
            {atencao.documentos.map((d, i) => (
              <li key={i}>
                <Titulo {...d} />
                <div className="discreto">{d.fonte_nome} · {datasDocumento(d.publicado_em, d.conhecido_em)}</div>
              </li>
            ))}
          </ul>
          {atencao.citacoes > atencao.documentos.length && (
            <p className="discreto">Mostrando as {atencao.documentos.length} mais recentes.</p>
          )}
        </>) : (
          <p>Nenhuma notícia das fontes acompanhadas cita este país nas últimas {janelaHoras} horas.</p>
        )}
      </section>

      {pontos.length > 0 && (
        <section>
          <h3>Pontos críticos nas margens</h3>
          <ul className="lista-pontos">
            {pontos.map((p) => {
              const e = estadoPonto(p.estado);
              return (
                <li key={p.id}>
                  <button type="button" onClick={() => selecionar({ tipo: "ponto", id: p.id })}>
                    <span className={`selo-estado ${e.classe}`}>{e.texto}</span>
                    <span className="lp-nome">{p.nome}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <section>
        <h3>Mercados do país</h3>
        {mercados.length === 0 ? <p className="sem-dado-texto">Nenhuma série acompanhada deste país.</p> : (<>
          <ul className="lista-mercados">{mercados.map((s) => <LinhaMercado key={s.id} s={s} />)}</ul>
          <p className="discreto">Oscilação do dia ao lado das notícias do mesmo período: coincidência no tempo, não causa.</p>
        </>)}
      </section>

      {!semDado && atencao?.historias && atencao.historias.length > 0 && (
        <section>
          <h3>Histórias com este país</h3>
          <ul className="lista-noticias">
            {atencao.historias.map((h) => (
              <li key={h.id}>
                <Link href={`/historias/#h${h.id}`} title={h.titulo_original ? `Original: ${h.titulo_original}` : undefined}>{h.titulo}</Link>
                <div className="discreto">
                  {plural(h.noticias, "notícia", "notícias")} · {plural(h.vozes, "voz independente", "vozes independentes")}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <dl className="codigos">
        <dt>{pais.iso_oficial ? "ISO 3166" : "Código"}</dt>
        <dd>
          {pais.iso}{pais.iso2 ? ` · ${pais.iso2}` : ""}
          {!pais.iso_oficial && <span className="discreto"> (sem código ISO; código do Natural Earth)</span>}
        </dd>
        {pais.continente && (<><dt>Continente</dt><dd>{continente(pais.continente)}</dd></>)}
        {pais.wikidata && (<>
          <dt>Wikidata</dt>
          <dd><a href={`https://www.wikidata.org/wiki/${pais.wikidata}`} target="_blank" rel="noreferrer">{pais.wikidata}</a></dd>
        </>)}
      </dl>
    </div>
  );
}
