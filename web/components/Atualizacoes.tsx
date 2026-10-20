import Link from "next/link";
import { datasDocumento, tipoFonte } from "@/lib/formatar";
import type { Documento } from "@/lib/status";
import Titulo from "@/components/Titulo";

/** As notícias mais recentes das fontes, com os países que cada uma cita (regra de dicionário do robô). */
export default function Atualizacoes({ documentos }: { documentos: Documento[] }) {
  return (
    <section className="atualizacoes bloco" aria-labelledby="titulo-atualizacoes">
      <div className="bloco-topo">
        <h2 id="titulo-atualizacoes" className="rotulo">Últimas atualizações</h2>
        <Link href="/metodo/#documentos" className="ver-todas">Mais notícias</Link>
      </div>
      {documentos.length === 0 ? <p className="sem-dado-texto">Sem dado nesta atualização.</p> : (
        <ol className="feed">
          {documentos.map((d, i) => (
            <li key={i}>
              <div className="feed-meta">
                <span className="selo">{tipoFonte(d.fonte_tipo)}</span>
                <span>{d.fonte_nome}</span>
                <span className="discreto">{datasDocumento(d.publicado_em, d.conhecido_em)}</span>
              </div>
              <Titulo {...d} className="feed-titulo" />
              {d.paises && d.paises.length > 0 && (
                <div className="feed-paises">
                  {d.paises.slice(0, 4).map((p) => <a key={p.iso} href={`#pais=${p.iso}`} className="chip">{p.nome}</a>)}
                  {d.paises.length > 4 && <span className="discreto">+{d.paises.length - 4}</span>}
                </div>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
