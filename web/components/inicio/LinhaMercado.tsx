"use client";
import { useState } from "react";
import Link from "next/link";
import { dia, hora, leituraSerie, textoConferencia, textoMudanca, valor, variacao, variacaoSerie } from "@/lib/formatar";
import type { MercadoResumo, Serie } from "@/lib/status";
import Minigrafico from "./Minigrafico";

/** Uma série numa linha (decisão 0016): símbolo no padrão do mercado com a descrição ao lado, último valor, oscilação
 * do dia com a leitura da régua e o último mês. Ao clicar, abre a leitura completa. Tudo calculado pelo robô. */
export default function LinhaMercado({ s }: { s: MercadoResumo & Partial<Serie> }) {
  const [aberta, setAberta] = useState(false);
  const l = leituraSerie(s.situacao, s.extremo);
  const sobe = (s.variacao ?? 0) > 0;
  return (
    <li className={`linha-mercado ${aberta ? "aberta" : ""}`}>
      <button type="button" className="lm-linha" aria-expanded={aberta} title={l.texto} onClick={() => setAberta(!aberta)}>
        <span className="lm-nome">
          <b className="lm-sim">{s.simbolo ?? s.nome}</b>
          {!s.parcial && s.data && <small className="lm-data" title="Último fechamento (sem dia em andamento)">{dia(s.data).slice(0, 5)}</small>}
          <small className="lm-desc">{s.simbolo ? s.nome : s.unidade}</small>
        </span>
        <span className="lm-valor numero">{valor(s.valor)}</span>
        <span className={`lm-var numero ${s.extremo ? "fora" : ""}`}>
          <span className={`ponto ${l.classe}`} aria-hidden />
          {s.variacao === null || s.variacao === undefined ? "—" : <>{sobe ? "▲" : s.variacao < 0 ? "▼" : "•"} {variacaoSerie(s.variacao, s.medida)}</>}
        </span>
        <Minigrafico valores={s.mes} fora={!!s.extremo} />
      </button>
      {aberta && (
        <div className="lm-detalhe">
          <p><b>{l.texto}.</b> {s.nome}, {s.unidade}.</p>
          {s.percentil !== null && s.percentil !== undefined && (
            <p>A variação do dia está no percentil {s.percentil.toLocaleString("pt-BR")} dos últimos 5 anos da própria série
              {s.faixa ? <> (normal: de {variacaoSerie(s.faixa[0], s.medida)} a {variacaoSerie(s.faixa[1], s.medida)})</> : null}.</p>
          )}
          {textoConferencia(s.conferencia, s.conferir) && <p>{textoConferencia(s.conferencia, s.conferir)}</p>}
          {(s.mudancas ?? []).map((m, i) => <p key={i}>{textoMudanca(m)}</p>)}
          <p className="discreto">
            {s.parcial ? `Dia em andamento, lido às ${hora(s.conhecido_em)} (Brasília)` : s.data ? `Fechamento de ${dia(s.data)}` : "Sem leitura"}
            {s.fonte_nome ? ` · ${s.fonte_nome}` : ""} · <Link href="/metodo/#regua">Como a régua funciona</Link>
            {s.situacao === "troca_de_contrato" && <> · No dia da troca de contrato o preço salta sem o mercado mudar ({variacao(s.variacao)}).</>}
          </p>
        </div>
      )}
    </li>
  );
}
