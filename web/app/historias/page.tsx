import AvisoAtraso from "@/components/AvisoAtraso";
import { dataHora, datasDocumento, plural } from "@/lib/formatar";
import { lerStatus } from "@/lib/status";

export const metadata = { title: "Histórias · Stratum Global" };

export default function Historias() {
  const s = lerStatus();
  const lista = s.historias ?? [];
  return (<>
    <AvisoAtraso ate={s.avisar_atraso_apos} gerado={s.gerado_em} />
    <main className="pagina">
      <h1>Histórias</h1>
      <p className="lead">
        Notícias da mesma história, juntas por uma regra, com alguma notícia nas últimas 24 horas. Mais vozes quer dizer
        mais donos diferentes publicando: é cobertura, não confirmação. Como a regra é feita, está na tela Método.
      </p>
      {lista.length === 0 ? (
        <p className="sem-dado-texto">Nenhuma história com mais de uma notícia nas últimas 24 horas.</p>
      ) : lista.map((h) => (
        <section key={h.id} id={`h${h.id}`}>
          <h2>{h.titulo}</h2>
          <p className="discreto">
            {plural(h.noticias, "notícia", "notícias")} de {plural(h.fontes, "fonte", "fontes")} ·{" "}
            <b>{plural(h.vozes, "voz independente", "vozes independentes")}</b> · última em {dataHora(h.ultima)}
            {h.paises.length > 0 && <> · {h.paises.map((p) => p.nome).join(", ")}</>}
          </p>
          <details>
            <summary>Ver as notícias</summary>
            <ul className="regras">
              {h.documentos.map((d, i) => (
                <li key={i}>
                  {d.url ? <a href={d.url} target="_blank" rel="noreferrer">{d.titulo}</a> : d.titulo}{" "}
                  <span className="discreto">({d.fonte_nome} · {datasDocumento(d.publicado_em, d.conhecido_em)})</span>
                </li>
              ))}
            </ul>
          </details>
        </section>
      ))}
    </main>
  </>);
}
