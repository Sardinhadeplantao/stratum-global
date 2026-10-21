"use client";
import { diaHora, variacaoSerie } from "@/lib/formatar";
import type { ItemFaixa } from "@/lib/status";
import type { Selecao } from "./Inicio";

/** A faixa de baixo: o robô escolhe e ordena os itens (pontos críticos, mercados fora do normal, terremotos fortes e
 * as últimas notícias). Para sozinha ao passar o mouse; sem animação para quem pediu menos movimento. */
export default function Faixa({ itens, selecionar }: { itens: ItemFaixa[]; selecionar: (s: Selecao) => void }) {
  if (itens.length === 0) return <div className="faixa"><span className="sem-dado-texto faixa-vazia">Sem itens nesta atualização.</span></div>;
  const conteudo = (chave: string) => itens.map((i, n) => (
    <span key={`${chave}-${n}`} className={`faixa-item faixa-${i.tipo}`}>
      {i.tipo === "ponto" && i.id ? (
        <button type="button" onClick={() => selecionar({ tipo: "ponto", id: i.id! })}><b>●</b> {i.texto}<small> {i.detalhe}</small></button>
      ) : i.tipo === "mercado" ? (
        <><b>{(i.variacao ?? 0) > 0 ? "▲" : "▼"}</b> {i.texto} {variacaoSerie(i.variacao, i.medida)}
          <small> fora do normal{i.parcial ? " · hoje" : ""}</small></>
      ) : i.url ? (
        <a href={i.url} target="_blank" rel="noreferrer">
          {i.tipo === "terremoto" ? <b>◉</b> : <small>{i.fonte} · {diaHora(i.quando).slice(-5)}</small>} {i.texto}
        </a>
      ) : <span>{i.texto}</span>}
    </span>
  ));
  return (
    <div className="faixa" aria-label="Últimas informações">
      <span className="faixa-rotulo">Agora</span>
      <div className="faixa-trilho">
        <div className="faixa-conteudo" style={{ animationDuration: `${Math.max(itens.length * 6, 40)}s` }}>{conteudo("a")}<span aria-hidden className="faixa-copia">{conteudo("b")}</span></div>
      </div>
    </div>
  );
}
