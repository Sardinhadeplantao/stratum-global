import { datasDocumento, numero, plural } from "@/lib/formatar";
import type { Status } from "@/lib/status";
import Titulo from "@/components/Titulo";

const PROXIMAS = [
  { fase: "Fase 1", texto: "Notícias agrupadas em eventos, com grau de confirmação e importância" },
  { fase: "Fase 2", texto: "Mercados: moedas, juros, bolsas e commodities, com a reação a cada evento" },
  { fase: "Fase 3", texto: "Briefing da manhã escrito por IA, com a fonte de cada frase" },
  { fase: "Fase 4", texto: "Rotas e estreitos, comércio, sanções, conflitos e calendário" },
  { fase: "Fase 5", texto: "Cadeias industriais, simulação de choque e hipóteses com placar" },
];

const SEM_DADO = <p className="sem-dado-texto">Sem dado nesta atualização.</p>;

export default function Cartoes({ status }: { status: Status }) {
  const medido = status.atencao !== null;  // sem contagem publicada, não há zero: há sem dado
  const janela = status.atencao?.janela_horas ?? 24;
  const topo = status.mais_citados[0];
  const destaque = topo ? status.paises[topo.iso] : null;
  return (
    <section className="cartoes" aria-label="Destaques">
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
        <h2 className="rotulo">Destaque</h2>
        {topo && destaque ? (<>
          <a href={`#pais=${topo.iso}`} className="destaque-pais">{topo.nome}</a>
          <p className="discreto">{plural(topo.citacoes, "notícia", "notícias")} em {janela} h. Aparece aqui por ser o país mais citado, não por escolha.</p>
          <ul className="lista-noticias">
            {destaque.documentos.slice(0, 3).map((d, i) => (
              <li key={i}>
                <Titulo {...d} />
                <div className="discreto">{d.fonte_nome} · {datasDocumento(d.publicado_em, d.conhecido_em)}</div>
              </li>
            ))}
          </ul>
        </>) : !medido ? SEM_DADO : <p>Nenhum país citado na janela.</p>}
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

      <article className="cartao bloco">
        <h2 className="rotulo">Próximas camadas</h2>
        <ul className="proximas">
          {PROXIMAS.map((p) => <li key={p.fase}><span className="fase">{p.fase}</span>{p.texto}</li>)}
        </ul>
      </article>
    </section>
  );
}
