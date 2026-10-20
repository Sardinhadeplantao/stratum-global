import Link from "next/link";
import { diaHora, plural } from "@/lib/formatar";
import type { Historia } from "@/lib/status";
import Titulo from "@/components/Titulo";

/** As histórias das últimas 24 horas, na ordem do robô: mais vozes independentes primeiro (decisão 0009). */
export default function HistoriasDoDia({ historias }: { historias: Historia[] }) {
  return (
    <section className="coluna-historias bloco" aria-labelledby="titulo-historias">
      <div className="bloco-topo">
        <h2 id="titulo-historias" className="rotulo">Histórias do dia</h2>
        <Link href="/historias/" className="ver-todas">Todas as histórias</Link>
      </div>
      <p className="discreto nota-bloco">
        Primeiro as que mais donos diferentes estão cobrindo. Mais vozes é cobertura, não confirmação.
      </p>
      {historias.length === 0 ? (
        <p className="sem-dado-texto">Nenhuma história com mais de uma notícia nas últimas 24 horas.</p>
      ) : (
        <ol className="feed">
          {historias.map((h) => (
            <li key={h.id}>
              <div className="feed-meta">
                <span className="selo">{plural(h.vozes, "voz", "vozes")}</span>
                <span>{plural(h.noticias, "notícia", "notícias")}</span>
                <span className="discreto">última {diaHora(h.ultima)}</span>
              </div>
              <Titulo titulo={h.titulo} titulo_original={h.titulo_original} href={`/historias/#h${h.id}`} className="feed-titulo" />
              {h.paises.length > 0 && (
                <div className="feed-paises">
                  {h.paises.slice(0, 4).map((p) => <a key={p.iso} href={`#pais=${p.iso}`} className="chip">{p.nome}</a>)}
                  {h.paises.length > 4 && <span className="discreto">+{h.paises.length - 4}</span>}
                </div>
              )}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
