"use client";
import { type ReactNode, useState } from "react";
import Link from "next/link";
import PainelPais, { type Pais } from "@/components/PainelPais";
import Reacao from "@/components/Reacao";
import Titulo from "@/components/Titulo";
import { diaHora, estadoPonto, magnitude, numero, plural, situacao } from "@/lib/formatar";
import type { DadosInicio, Selecao } from "./Inicio";
import LinhaMercado from "./LinhaMercado";
import PainelMercados from "./PainelMercados";
import PainelNoticias from "./PainelNoticias";
import PainelPonto from "./PainelPonto";

type Aba = "agora" | "mercados" | "noticias";
const ABAS: [Aba, string][] = [["agora", "Agora"], ["mercados", "Mercados"], ["noticias", "Notícias"]];

/** O painel da direita: com algo selecionado, o contexto dele; sem seleção, as abas. */
export default function PainelLateral({ dados, selecao, selecionar, porIso, atualizacao }: {
  dados: DadosInicio; selecao: Selecao | null; selecionar: (s: Selecao | null) => void; porIso: Map<string, Pais>;
  atualizacao?: ReactNode;
}) {
  const [aba, setAba] = useState<Aba>("agora");
  const pontos = dados.pontos?.lista ?? [];
  const series = dados.mercados?.series ?? [];
  const porId = new Map(series.map((s) => [s.id, s]));

  if (selecao?.tipo === "ponto") {
    const p = pontos.find((x) => x.id === selecao.id);
    if (p) return <aside className="painel-lateral"><PainelPonto ponto={p} voltar={() => selecionar(null)} selecionar={selecionar} /></aside>;
  }
  if (selecao?.tipo === "pais") {
    const pais = porIso.get(selecao.id);
    if (pais) {
      const mercados = (dados.mercados?.por_pais?.[pais.iso] ?? []).map((id) => porId.get(id)).filter((s) => s !== undefined);
      return (
        <aside className="painel-lateral">
          <PainelPais pais={pais} atencao={dados.paises[pais.iso] ?? null} janelaHoras={dados.atencao?.janela_horas ?? 24}
                      semDado={!dados.atencao} fechar={() => selecionar(null)} mercados={mercados}
                      pontos={pontos.filter((p) => p.margens.some((m) => m.iso === pais.iso))} selecionar={selecionar} />
        </aside>
      );
    }
  }

  const fora = series.filter((s) => s.extremo || s.situacao === "nao_confere" || s.situacao === "troca_de_contrato");
  return (
    <aside className="painel-lateral">
      <div className="abas" role="tablist" aria-label="Painel">
        {ABAS.map(([id, nome]) => (
          <button key={id} type="button" role="tab" aria-selected={aba === id} className={aba === id ? "aba ativa" : "aba"}
                  onClick={() => setAba(id)}>{nome}</button>
        ))}
      </div>
      {atualizacao}
      <div className="aba-corpo">
        {aba === "agora" && (<>
          <Alertas dados={dados} />
          <section>
            <h3>Pontos críticos <small className="discreto">(últimas 24 h)</small></h3>
            {pontos.length === 0 ? <p className="sem-dado-texto">Sem dado nesta atualização.</p> : (
              <ul className="lista-pontos">
                {pontos.map((p) => {
                  const e = estadoPonto(p.estado);
                  return (
                    <li key={p.id}>
                      <button type="button" onClick={() => selecionar({ tipo: "ponto", id: p.id })}>
                        <span className={`selo-estado ${e.classe}`}>{e.texto}</span>
                        <span className="lp-nome">{p.nome}</span>
                        <small className="discreto">{p.noticias > 0 ? `${plural(p.noticias, "notícia", "notícias")} · ${plural(p.vozes, "voz", "vozes")}` : "—"}</small>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
          <section>
            <h3>Mercados fora do normal</h3>
            {series.length === 0 ? <p className="sem-dado-texto">Sem dado nesta atualização.</p>
              : fora.length === 0 ? <p className="discreto">Nenhuma das {series.length} séries está fora do normal agora.</p>
              : <ul className="lista-mercados">{fora.map((s) => <LinhaMercado key={s.id} s={s} />)}</ul>}
            <p className="discreto nota-aba">Fora do normal = variação do dia entre as 5% maiores ou menores dos últimos 5 anos da
              própria série. <button type="button" className="link" onClick={() => setAba("mercados")}>Ver todos os mercados</button></p>
          </section>
          <section>
            <h3>Histórias com mais vozes</h3>
            {(dados.historias ?? []).length === 0 ? <p className="sem-dado-texto">Sem histórias nesta atualização.</p> : (
              <ul className="lista-noticias">
                {(dados.historias ?? []).slice(0, 6).map((h) => (
                  <li key={h.id}>
                    <Titulo titulo={h.titulo} titulo_original={h.titulo_original} href={`/historias/#h${h.id}`} />
                    <div className="discreto">
                      {plural(h.vozes, "voz independente", "vozes independentes")} · {plural(h.noticias, "notícia", "notícias")}
                      {h.paises.length > 0 && <> · {h.paises.slice(0, 3).map((p, i) => (
                        <span key={p.iso}>{i > 0 && ", "}<button type="button" className="link" onClick={() => selecionar({ tipo: "pais", id: p.iso })}>{p.nome}</button></span>
                      ))}</>}
                    </div>
                    <Reacao r={h.reacao} compacta />
                  </li>
                ))}
              </ul>
            )}
            <Link href="/historias/" className="discreto">Todas as histórias →</Link>
          </section>
          <Rodada dados={dados} />
        </>)}
        {aba === "mercados" && <PainelMercados mercados={dados.mercados} />}
        {aba === "noticias" && <PainelNoticias dados={dados} selecionar={selecionar} />}
      </div>
    </aside>
  );
}

/** Os alertas do momento, contados pelo robô. Cor só quando há o estado medido; zero fica neutro, sem dado fica cinza. */
function Alertas({ dados }: { dados: DadosInicio }) {
  const p = dados.pontos;
  const m = dados.mercados;
  const forte = (dados.terremotos ?? [])[0];  // o robô manda do mais forte para o mais fraco
  const itens = [
    { rotulo: "Pontos críticos", valor: p ? numero(p.criticos) : "—", classe: p && p.criticos > 0 ? "alerta-critico" : "" },
    { rotulo: "Em pauta", valor: p ? numero(p.em_pauta) : "—", classe: p && p.em_pauta > 0 ? "alerta-pauta" : "" },
    { rotulo: "Mercados fora do normal", valor: m ? numero(m.fora_do_normal) : "—", classe: m && m.fora_do_normal > 0 ? "alerta-pauta" : "" },
    { rotulo: "Terremoto mais forte (24 h)", valor: dados.terremotos ? (forte ? magnitude(forte.magnitude) : "nenhum") : "—",
      classe: forte ? "alerta-terremoto" : "" },
  ];
  return (
    <ul className="alertas" aria-label="Alertas do momento">
      {itens.map((i) => (
        <li key={i.rotulo} className={`${i.classe} ${i.valor === "—" ? "sem-dado-bloco" : ""}`}>
          <strong>{i.valor}</strong><span>{i.rotulo}</span>
        </li>
      ))}
    </ul>
  );
}

/** De onde vêm os números: a rodada, as fontes funcionando e o tamanho do noticiário. */
function Rodada({ dados }: { dados: DadosInicio }) {
  const r = dados.ultima_rodada;
  const a = dados.atencao;
  return (
    <p className="rodada-rodape discreto">
      <span className={`ponto ${situacao(r?.situacao).classe}`} aria-hidden />{" "}
      {r ? <>Fontes funcionando: {dados.totais.fontes_ok} de {dados.totais.fontes} · última rodada {diaHora(r.iniciada_em)}</>
        : dados.banco === "erro" ? "O banco não abriu nesta rodada" : "O robô ainda não rodou"}
      {a && <> · {plural(a.documentos, "notícia", "notícias")} e {plural(a.paises_citados, "país citado", "países citados")} em {a.janela_horas} h</>}
      {" · "}<Link href="/metodo/">De onde vem cada número</Link>
    </p>
  );
}
