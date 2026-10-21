"use client";
import { useEffect, useMemo, useState } from "react";
import type { Pais } from "@/components/PainelPais";
import { plural } from "@/lib/formatar";
import type { Status } from "@/lib/status";
import CamadasMapa from "./CamadasMapa";
import Faixa from "./Faixa";
import MapaGlobal from "./MapaGlobal";
import PainelLateral from "./PainelLateral";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export type Selecao = { tipo: "pais" | "ponto"; id: string };
export type Camadas = { pontos: boolean; rotas: boolean; citacoes: boolean; terremotos: boolean };

/** Os dados que a página inicial usa (o status.json inteiro tem mais coisa, que fica nas outras telas). */
export type DadosInicio = Pick<Status, "paises" | "atencao" | "pontos" | "terremotos" | "faixa" | "mercados" | "historias"
  | "ultimos_documentos" | "contagem_historias" | "mais_citados" | "origem_fontes" | "totais" | "ultima_rodada" | "banco">;

function lerHash(): Selecao | null {
  const m = /^#(pais|ponto)=([A-Za-z_]{3,40})$/.exec(window.location.hash);
  return m ? { tipo: m[1] as Selecao["tipo"], id: m[2] } : null;
}

/** A página inicial (decisão 0014): o mapa no centro, as camadas à esquerda, o painel à direita e a faixa embaixo.
 * A seleção fica no endereço (#ponto=ormuz, #pais=BRA), para dar para voltar e compartilhar. */
export default function Inicio({ dados, niveis }: { dados: DadosInicio; niveis: number[] }) {
  const [selecao, setSelecao] = useState<Selecao | null>(null);
  const [camadas, setCamadas] = useState<Camadas>({ pontos: true, rotas: true, citacoes: true, terremotos: true });
  const [lista, setLista] = useState<Pais[]>([]);

  useEffect(() => {
    fetch(`${BASE}/geo/paises.geojson`).then((r) => r.json())
      .then((geo) => setLista(geo.features.map((f: { properties: Pais }) => f.properties))).catch(() => setLista([]));
    setSelecao(lerHash());
    const aoMudar = () => setSelecao(lerHash());
    window.addEventListener("hashchange", aoMudar);
    return () => window.removeEventListener("hashchange", aoMudar);
  }, []);
  const porIso = useMemo(() => new Map(lista.map((p) => [p.iso, p])), [lista]);

  function selecionar(s: Selecao | null) {
    setSelecao(s);
    const hash = s ? `#${s.tipo}=${s.id}` : "";
    if (window.location.hash !== hash) history.replaceState(null, "", hash || window.location.pathname + window.location.search);
    // No celular o painel fica embaixo do mapa: leva a pessoa até o contexto do que ela escolheu
    if (s && window.matchMedia("(max-width: 760px)").matches) document.querySelector(".painel-lateral")?.scrollIntoView({ behavior: "smooth" });
  }

  const pontos = dados.pontos?.lista ?? [];
  const terremotos = dados.terremotos ?? [];
  const contagens = {
    pontos: dados.pontos ? `${plural(dados.pontos.criticos, "crítico", "críticos")} · ${dados.pontos.em_pauta} em pauta` : "sem dado",
    citacoes: dados.atencao ? `${dados.atencao.paises_citados} países` : "sem dado",
    terremotos: `${terremotos.length} em 24 h`,
    rotas: "traçado esquemático",
  };
  return (
    <div className="inicio">
      <section className="inicio-mapa" aria-label="Mapa global">
        <MapaGlobal paises={dados.paises} niveis={niveis} janelaHoras={dados.atencao?.janela_horas ?? 24} semDado={!dados.atencao}
                    pontos={pontos} terremotos={terremotos} lista={lista} camadas={camadas}
                    selecao={selecao} aoSelecionar={selecionar} />
        <CamadasMapa camadas={camadas} mudar={setCamadas} contagens={contagens} />
      </section>
      <PainelLateral dados={dados} selecao={selecao} selecionar={selecionar} porIso={porIso} />
      <Faixa itens={dados.faixa ?? []} selecionar={selecionar} />
    </div>
  );
}
