"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Pais } from "@/components/PainelPais";
import { NIVEIS_PADRAO } from "@/lib/constantes";
import { hora, plural } from "@/lib/formatar";
import { type DadosInicio, escolherDados } from "@/lib/inicio";
import type { Status } from "@/lib/status";
import CamadasMapa from "./CamadasMapa";
import Faixa from "./Faixa";
import MapaGlobal from "./MapaGlobal";
import PainelLateral from "./PainelLateral";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

export type Selecao = { tipo: "pais" | "ponto"; id: string };
export type Camadas = { pontos: boolean; rotas: boolean; citacoes: boolean; terremotos: boolean };

export type { DadosInicio };
const ATUALIZAR_A_CADA_MS = 60_000;  // o robô publica a cada 15 minutos; a página pergunta a cada minuto

function lerHash(): Selecao | null {
  const m = /^#(pais|ponto)=([A-Za-z_]{3,40})$/.exec(window.location.hash);
  return m ? { tipo: m[1] as Selecao["tipo"], id: m[2] } : null;
}

/** A página inicial (decisão 0014): o mapa no centro, as camadas à esquerda, o painel à direita e a faixa embaixo.
 * A seleção fica no endereço (#ponto=ormuz, #pais=BRA), para dar para voltar e compartilhar. */
export default function Inicio({ inicial }: { inicial: DadosInicio }) {
  const [dados, setDados] = useState(inicial);
  const [novo, setNovo] = useState(false);  // acabou de chegar dado novo: um sinal discreto
  const geradoRef = useRef(inicial.gerado_em);
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

  // Atualização automática (decisão 0016): pergunta se o robô publicou dados novos; se sim, troca sem recarregar
  useEffect(() => {
    let parado = false;
    async function buscar() {
      if (document.hidden) return;
      try {
        const r = await fetch(`${BASE}/dados/status.json?t=${Date.now()}`, { cache: "no-store" });
        if (!r.ok) return;
        const s = (await r.json()) as Status;
        if (parado || !s.gerado_em || s.gerado_em === geradoRef.current) return;
        geradoRef.current = s.gerado_em;
        setDados(escolherDados(s));
        setNovo(true);
        setTimeout(() => setNovo(false), 4000);
      } catch { /* sem rede: fica com o que tem e tenta de novo */ }
    }
    const id = setInterval(buscar, ATUALIZAR_A_CADA_MS);
    document.addEventListener("visibilitychange", buscar);
    return () => { parado = true; clearInterval(id); document.removeEventListener("visibilitychange", buscar); };
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
        <MapaGlobal paises={dados.paises} niveis={dados.atencao?.niveis ?? NIVEIS_PADRAO} janelaHoras={dados.atencao?.janela_horas ?? 24} semDado={!dados.atencao}
                    pontos={pontos} terremotos={terremotos} lista={lista} camadas={camadas}
                    selecao={selecao} aoSelecionar={selecionar} />
        <CamadasMapa camadas={camadas} mudar={setCamadas} contagens={contagens} />
      </section>
      <PainelLateral dados={dados} selecao={selecao} selecionar={selecionar} porIso={porIso}
                     atualizacao={<p className={`atualizacao ${novo ? "nova" : ""}`} aria-live="polite">
                       <span className="ponto sit-rodando" aria-hidden /> {dados.gerado_em ? `Dados de ${hora(dados.gerado_em)}` : "Sem dado"}
                       {" "}<small>· a página se atualiza sozinha</small></p>} />
      <Faixa itens={dados.faixa ?? []} selecionar={selecionar} />
    </div>
  );
}
