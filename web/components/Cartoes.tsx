import Atualizacoes from "@/components/Atualizacoes";
import { numero } from "@/lib/formatar";
import type { Status } from "@/lib/status";

const SEM_DADO = <p className="sem-dado-texto">Sem dado nesta atualização.</p>;

export default function Cartoes({ status }: { status: Status }) {
  const medido = status.atencao !== null;  // sem contagem publicada, não há zero: há sem dado
  const janela = status.atencao?.janela_horas ?? 24;
  return (
    <section className="cartoes" aria-label="Destaques">
      <Atualizacoes documentos={status.ultimos_documentos.slice(0, 12)} />

      <article className="cartao bloco">
        <h2 className="rotulo">Mais citados em {janela} h</h2>
        {!medido ? SEM_DADO : status.mais_citados.length === 0 ? <p>Nenhum país citado na janela.</p> : (
          <ol className="barras">
            {status.mais_citados.map((p) => (
              <li key={p.iso}>
                <a href={`#pais=${p.iso}`}>{p.nome}</a>
                <span className="barra"><i style={{ width: `${Math.max(p.proporcao * 100, 2)}%` }} /></span>
                <span className="numero">{numero(p.citacoes)}</span>
              </li>
            ))}
          </ol>
        )}
      </article>

      <article className="cartao bloco">
        <h2 className="rotulo">Quem está falando</h2>
        <p className="discreto">
          Notícias em {janela} h pelo país de cada fonte (a lista está em Método; algumas fontes são oficiais). A barra
          mostra quanto as fontes de cada país publicam, não quem pauta o assunto.
        </p>
        {!medido ? SEM_DADO : status.origem_fontes.length === 0 ? <p>Nenhuma notícia na janela.</p> : (
          <ol className="barras">
            {status.origem_fontes.map((o) => (
              <li key={o.pais ?? "internacional"}>
                <span>{o.nome}</span>
                <span className="barra barra-neutra"><i style={{ width: `${Math.max(o.proporcao * 100, 2)}%` }} /></span>
                <span className="numero">{numero(o.documentos)}</span>
              </li>
            ))}
          </ol>
        )}
      </article>
    </section>
  );
}
