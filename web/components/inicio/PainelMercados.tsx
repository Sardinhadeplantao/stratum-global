import Link from "next/link";
import { GRUPOS_SERIES, hora, leituraSerie, numero, REGIOES_BOLSA, valor, variacaoSerie } from "@/lib/formatar";
import type { Amplitude, Contagem, Mercados, Serie } from "@/lib/status";
import LinhaMercado from "./LinhaMercado";

/** A aba Mercados: os quadros de destaque, quantas sobem e caem, e todas as séries por grupo (bolsas por região). */
export default function PainelMercados({ mercados }: { mercados: Mercados | null | undefined }) {
  const series = mercados?.series ?? [];
  if (series.length === 0) return <p className="sem-dado-texto">Sem dado nesta atualização.</p>;
  const porId = new Map(series.map((s) => [s.id, s]));
  return (<>
    <ul className="quadros" aria-label="Destaques">
      {(mercados?.destaques ?? []).map((d) => {
        const s = porId.get(d.id);
        return s ? <Quadro key={d.id} rotulo={d.rotulo} s={s} /> : null;
      })}
    </ul>
    {mercados?.amplitude && <BarraAmplitude a={mercados.amplitude} />}
    <p className="discreto nota-aba">Oscilação do dia: variação desde o fechamento anterior; &quot;hoje&quot; é o dia em andamento.
      Dourado = fora do normal para a própria série. O gráfico é o último mês. <Link href="/metodo/#regua">Como a régua funciona</Link></p>
    {GRUPOS_SERIES.map(([grupo, titulo]) => {
      const doGrupo = series.filter((s) => (s.grupo ?? "moedas") === grupo);
      if (doGrupo.length === 0) return null;
      return (
        <section key={grupo}>
          <h3>{titulo} <ContagemGrupo c={mercados?.amplitude?.por_grupo?.[grupo]} /></h3>
          {grupo !== "bolsas" ? <ul className="lista-mercados">{doGrupo.map((s) => <LinhaMercado key={s.id} s={s} />)}</ul>
            : REGIOES_BOLSA.map(([regiao, nome]) => {
              const daRegiao = doGrupo.filter((s) => s.regiao === regiao);
              return daRegiao.length === 0 ? null : (
                <div key={regiao}>
                  <h4 className="subgrupo">{nome}</h4>
                  <ul className="lista-mercados">{daRegiao.map((s) => <LinhaMercado key={s.id} s={s} />)}</ul>
                </div>
              );
            })}
        </section>
      );
    })}
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
