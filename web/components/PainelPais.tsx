import Link from "next/link";
import { continente, datasDocumento, plural } from "@/lib/formatar";
import type { PaisAtencao } from "@/lib/status";

/** Propriedades de cada país em public/geo/paises.geojson (gerado por jobs/scripts/preparar_paises.py). */
export type Pais = {
  iso: string; iso_oficial: boolean; iso2: string | null; nome: string; nome_en: string;
  wikidata: string | null; continente: string | null; regiao: string | null; centro?: [number, number] | null;
};

type Props = { pais: Pais; atencao: PaisAtencao | null; janelaHoras: number; semDado: boolean; fechar: () => void };

export default function PainelPais({ pais, atencao, janelaHoras, semDado, fechar }: Props) {
  return (
    <aside className="painel" aria-label={`Painel de ${pais.nome}`}>
      <div className="painel-topo">
        <div>
          <h2>{pais.nome}</h2>
          {pais.nome_en && pais.nome_en !== pais.nome && <p className="discreto">{pais.nome_en}</p>}
        </div>
        <button onClick={fechar} className="fechar" aria-label="Fechar painel">×</button>
      </div>

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

      <section>
        <h3>Nas últimas {janelaHoras} horas</h3>
        {semDado ? (
          <p className="sem-dado-texto">Sem dado nesta atualização: o robô não publicou a contagem.</p>
        ) : atencao ? (<>
          <p className="destaque-numero">{plural(atencao.citacoes, "notícia cita", "notícias citam")} este país</p>
          <ul className="lista-noticias">
            {atencao.documentos.map((d, i) => (
              <li key={i}>
                {d.url ? <a href={d.url} target="_blank" rel="noreferrer">{d.titulo}</a> : d.titulo}
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
      {!semDado && atencao?.historias && atencao.historias.length > 0 && (
        <section>
          <h3>Histórias com este país</h3>
          <ul className="lista-noticias">
            {atencao.historias.map((h) => (
              <li key={h.id}>
                <Link href={`/historias/#h${h.id}`}>{h.titulo}</Link>
                <div className="discreto">
                  {plural(h.noticias, "notícia", "notícias")} · {plural(h.vozes, "voz independente", "vozes independentes")}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
      <section>
        <h3>Mercados</h3>
        <p className="sem-dado-texto">Sem medição ainda. Moeda, juros e bolsa do país entram na fase 2.</p>
      </section>
    </aside>
  );
}
