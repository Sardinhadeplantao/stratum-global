"use client";
import { useState } from "react";
import Link from "next/link";
import { hora, leituraSerie, numero, REGIOES_BOLSA, valor, variacaoSerie } from "@/lib/formatar";
import type { Amplitude, Contagem, Mercados, Serie } from "@/lib/status";
import LinhaMercado from "./LinhaMercado";

type Categoria = "todos" | "bolsas" | "juros" | "moedas" | "commodities" | "cripto";
const CATEGORIAS: [Categoria, string][] = [
  ["todos", "Todos"], ["bolsas", "Bolsas"], ["juros", "Juros"], ["moedas", "Moedas"], ["commodities", "Commodities"],
  ["cripto", "Cripto"],
];

/** Subgrupos de cada categoria (decisão 0016). Cada um: título e quais séries entram. */
function subgrupos(grupo: string, series: Serie[]): [string, Serie[]][] {
  const doGrupo = series.filter((s) => (s.grupo ?? "moedas") === grupo);
  if (grupo === "bolsas") return REGIOES_BOLSA.map(([r, nome]) => [nome, doGrupo.filter((s) => s.regiao === r)]);
  if (grupo === "moedas") return [
    ["Contra o dólar · mercado, conferido com o BCE", doGrupo.filter((s) => s.fonte === "yahoo_cambio")],
    ["Contra o euro · oficial (BCE), fechamento do dia", doGrupo.filter((s) => s.fonte !== "yahoo_cambio")],
  ];
  if (grupo === "juros") return [["Títulos de 10 anos · fontes oficiais", doGrupo]];
  return [["", doGrupo]];
}

/** A aba Mercados: os quadros de destaque, quantas sobem e caem e as séries por categoria, uma linha por ativo. */
export default function PainelMercados({ mercados }: { mercados: Mercados | null | undefined }) {
  const [categoria, setCategoria] = useState<Categoria>("todos");
  const series = mercados?.series ?? [];
  if (series.length === 0) return <p className="sem-dado-texto">Sem dado nesta atualização.</p>;
  const porId = new Map(series.map((s) => [s.id, s]));
  const grupos = categoria === "todos" ? ["bolsas", "juros", "moedas", "commodities", "cripto"] : [categoria];
  return (<>
    <ul className="quadros" aria-label="Destaques">
      {(mercados?.destaques ?? []).map((d) => {
        const s = porId.get(d.id);
        return s ? <Quadro key={d.id} rotulo={d.rotulo} s={s} /> : null;
      })}
    </ul>
    {mercados?.amplitude && <BarraAmplitude a={mercados.amplitude} />}
    <div className="categorias" role="tablist" aria-label="Categoria">
      {CATEGORIAS.map(([id, nome]) => (
        <button key={id} type="button" role="tab" aria-selected={categoria === id} className={categoria === id ? "filtro ativo" : "filtro"}
                onClick={() => setCategoria(id)}>{nome}</button>
      ))}
    </div>
    <div className="lm-cabecalho" aria-hidden><span>Ativo</span><span>Último</span><span>Dia</span><span>1 mês</span></div>
    {grupos.map((grupo) => (
      <section key={grupo} className="grupo-mercado">
        <h3>{CATEGORIAS.find(([id]) => id === grupo)?.[1]} <ContagemGrupo c={mercados?.amplitude?.por_grupo?.[grupo]} /></h3>
        {subgrupos(grupo, series).map(([titulo, lista]) => lista.length === 0 ? null : (
          <div key={titulo || grupo}>
            {titulo && <h4 className="subgrupo">{titulo}</h4>}
            <ul className="lista-mercados">{lista.map((s) => <LinhaMercado key={s.id} s={s} />)}</ul>
          </div>
        ))}
      </section>
    ))}
    <p className="discreto nota-aba">Dia: variação desde o fechamento anterior. Sem data ao lado do nome, é o dia em andamento,
      lido a cada 15 minutos. Dourado = fora do normal para a própria série; clique numa linha para ver a leitura.{" "}
      <Link href="/metodo/#regua">Como a régua funciona</Link></p>
  </>);
}

function Quadro({ rotulo, s }: { rotulo: string; s: Serie }) {
  const l = leituraSerie(s.situacao, s.extremo);
  return (
    <li className={`quadro ${s.extremo ? "fora" : ""}`} title={`${s.nome}: ${l.texto}`}>
      <span className="quadro-rotulo">{rotulo}</span>
      <strong className="numero">{valor(s.valor)}</strong>
      <span className="quadro-var numero">{variacaoSerie(s.variacao, s.medida)}{s.parcial ? <small> · {hora(s.conhecido_em)}</small> : null}</span>
    </li>
  );
}

function BarraAmplitude({ a }: { a: Amplitude }) {
  if (a.proporcao_sobem === null) return null;
  return (
    <div className="amplitude" aria-label="Quantas séries sobem e quantas caem">
      <div className="amplitude-texto">
        <span>▲ {numero(a.sobem)} sobem</span>
        <span className="discreto">{a.estaveis > 0 ? `${numero(a.estaveis)} iguais · ` : ""}só séries com leitura confiável</span>
        <span>{numero(a.caem)} caem ▼</span>
      </div>
      <span className="amplitude-barra"><i style={{ width: `${a.proporcao_sobem * 100}%` }} /></span>
    </div>
  );
}

function ContagemGrupo({ c }: { c?: Contagem }) {
  if (!c || c.sobem + c.caem + c.estaveis === 0) return null;
  return <small className="discreto">{c.sobem} ▲ · {c.caem} ▼</small>;
}
