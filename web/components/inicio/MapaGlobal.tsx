"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ExpressionSpecification, GeoJSONSource, Map as Mapa, Marker, StyleSpecification } from "maplibre-gl";
import type { Pais } from "@/components/PainelPais";
import { estadoPonto, faixas, magnitude } from "@/lib/formatar";
import type { PaisAtencao, Ponto, Terremoto } from "@/lib/status";
import type { Camadas, Selecao } from "./Inicio";

const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

/** Cor por nível de citações (calculado pelo robô). Nível 0 = medido e nenhuma notícia: o azul mais escuro. */
export const CORES_NIVEL = ["#1b2c44", "#1f4f78", "#2a74aa", "#3f9bd2", "#94d3f3"];
const COR_NEUTRA = "#1b2c44";  // camada de citações desligada: países numa cor só
const COR_SEM_DADO = "#5d6779"; // cinza: o robô não publicou contagem (mesma cor de --sem-dado)
const PREENCHIMENTO: ExpressionSpecification = [
  "match", ["coalesce", ["feature-state", "nivel"], 0],
  1, CORES_NIVEL[1], 2, CORES_NIVEL[2], 3, CORES_NIVEL[3], 4, CORES_NIVEL[4], CORES_NIVEL[0],
];

function geoTerremotos(lista: Terremoto[]) {
  return {
    type: "FeatureCollection" as const,
    features: lista.map((t) => ({
      type: "Feature" as const, properties: { titulo: t.titulo, magnitude: t.magnitude ?? 4.5 },
      geometry: { type: "Point" as const, coordinates: [t.lon, t.lat] },
    })),
  };
}

function estilo(plano: boolean, semDado: boolean, terremotos: Terremoto[]): StyleSpecification {
  return {
    version: 8,
    projection: { type: plano ? "mercator" : "globe" },
    sources: {
      paises: { type: "geojson", data: `${BASE}/geo/paises.geojson`, promoteId: "iso" },
      rotas: { type: "geojson", data: `${BASE}/geo/rotas.geojson` },
      terremotos: { type: "geojson", data: geoTerremotos(terremotos) },
    },
    layers: [
      { id: "oceano", type: "background", paint: { "background-color": "#071321" } },
      { id: "paises", type: "fill", source: "paises", paint: { "fill-color": semDado ? COR_SEM_DADO : PREENCHIMENTO } },
      { id: "fronteiras", type: "line", source: "paises", paint: { "line-color": "#41557a", "line-width": 0.5 } },
      {
        id: "selecao", type: "line", source: "paises",
        paint: { "line-color": "#f5c451", "line-width": ["case", ["boolean", ["feature-state", "selecionado"], false], 2, 0] },
      },
      {
        id: "rotas", type: "line", source: "rotas",
        paint: { "line-color": "#5fa8e8", "line-width": 1.3, "line-opacity": 0.55, "line-dasharray": [2, 2] },
      },
      {
        id: "terremotos", type: "circle", source: "terremotos",
        paint: {
          "circle-color": "#b48cff", "circle-opacity": 0.55, "circle-stroke-color": "#d9c6ff", "circle-stroke-width": 1,
          "circle-radius": ["interpolate", ["linear"], ["get", "magnitude"], 4.5, 3, 6, 6, 7.5, 11],
        },
      },
    ],
    sky: { "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 5, 1, 7, 0] },
  };
}

/** Siglas e nomes populares que a busca deve entender (o mapa só tem o nome oficial em português e inglês). */
const APELIDOS: Record<string, string> = {
  eua: "USA", us: "USA", usa: "USA", uk: "GBR", inglaterra: "GBR", "gra-bretanha": "GBR", uae: "ARE", eau: "ARE",
  holanda: "NLD", birmania: "MMR",
};
const semAcento = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

type Props = {
  paises: Record<string, PaisAtencao>; niveis: number[]; janelaHoras: number; semDado: boolean;
  pontos: Ponto[]; terremotos: Terremoto[]; lista: Pais[]; camadas: Camadas;
  selecao: Selecao | null; aoSelecionar: (s: Selecao | null) => void;
};

export default function MapaGlobal({ paises, niveis, janelaHoras, semDado, pontos, terremotos, lista, camadas, selecao, aoSelecionar }: Props) {
  const caixa = useRef<HTMLDivElement>(null);
  const mapaRef = useRef<Mapa | null>(null);
  const marcadores = useRef<Marker[]>([]);
  const selecionadoRef = useRef<string | null>(null);
  const aoSelecionarRef = useRef(aoSelecionar);
  aoSelecionarRef.current = aoSelecionar;
  const camadasRef = useRef(camadas);
  camadasRef.current = camadas;
  const [sobre, setSobre] = useState<string | null>(null);
  const [busca, setBusca] = useState("");
  const [erro, setErro] = useState(false);
  const [plano, setPlano] = useState<boolean | null>(null);  // null até o mapa abrir (no celular começa plano)
  const porIso = useMemo(() => new Map(lista.map((i) => [i.iso, i])), [lista]);

  function aplicarCamadas(mapa: Mapa, c: Camadas) {
    const ver = (ligada: boolean) => (ligada ? "visible" : "none");
    mapa.setPaintProperty("paises", "fill-color", semDado ? COR_SEM_DADO : c.citacoes ? PREENCHIMENTO : COR_NEUTRA);
    mapa.setLayoutProperty("rotas", "visibility", ver(c.rotas));
    mapa.setLayoutProperty("terremotos", "visibility", ver(c.terremotos));
    for (const m of marcadores.current) m.getElement().style.display = c.pontos ? "" : "none";
  }

  // Os dados mudam a cada atualização automática (decisão 0016): o mapa é criado uma vez só e os dados entram por
  // referência, sem recriar o mapa nem mexer na posição que a pessoa escolheu
  const dadosRef = useRef({ paises, semDado, janelaHoras, pontos });
  dadosRef.current = { paises, semDado, janelaHoras, pontos };
  const maplibreRef = useRef<typeof import("maplibre-gl") | null>(null);
  const [carregado, setCarregado] = useState(false);

  useEffect(() => {
    let cancelado = false;
    import("maplibre-gl").then((maplibregl) => {
      if (cancelado || !caixa.current) return;
      maplibreRef.current = maplibregl;
      maplibregl.setWorkerUrl(`${location.origin}${BASE}/maplibre/maplibre-gl-worker.mjs?v=${maplibregl.getVersion()}`);
      const plano = window.matchMedia("(max-width: 760px)").matches;
      setPlano(plano);
      const mapa = new maplibregl.Map({
        container: caixa.current,
        style: estilo(plano, dadosRef.current.semDado, terremotos),
        center: plano ? [35, 22] : [48, 22],
        zoom: plano ? Math.max(Math.log2(caixa.current.clientWidth / 512), 0) : 2,
        attributionControl: { compact: true, customAttribution: "Fronteiras: Natural Earth · Rotas: traçado esquemático" },
      });
      mapaRef.current = mapa;
      mapa.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      mapa.on("error", (e) => { if (String(e.error?.message ?? "").includes("paises")) setErro(true); });
      mapa.on("load", () => setCarregado(true));
      mapa.on("mousemove", (e) => {
        const f = mapa.queryRenderedFeatures(e.point, { layers: ["terremotos", "rotas", "paises"] })[0];
        mapa.getCanvas().style.cursor = f && f.layer.id === "paises" ? "pointer" : "";
        if (!f) return setSobre(null);
        if (f.layer.id === "terremotos") return setSobre(`${magnitude(Number(f.properties.magnitude))} · ${f.properties.titulo}`);
        if (f.layer.id === "rotas") return setSobre(`${f.properties.nome} (traçado esquemático)`);
        const { paises: p, semDado: sd, janelaHoras: jh } = dadosRef.current;
        const iso = String(f.properties.iso ?? "");
        const n = p[iso]?.citacoes ?? 0;
        setSobre(`${f.properties.nome}${sd ? " · sem dado" : ` · ${n} ${n === 1 ? "notícia" : "notícias"} em ${jh} h`}`);
      });
      mapa.on("mouseout", () => setSobre(null));
      mapa.on("click", (e) => {
        const f = mapa.queryRenderedFeatures(e.point, { layers: ["paises"] })[0];
        aoSelecionarRef.current(f ? { tipo: "pais", id: String(f.id) } : null);
      });
    }).catch(() => setErro(true));
    return () => {
      cancelado = true;
      marcadores.current.forEach((m) => m.remove());
      marcadores.current = [];
      mapaRef.current?.remove();
      mapaRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Citações de cada país (o nível vem do robô)
  useEffect(() => {
    const mapa = mapaRef.current;
    if (!mapa || !carregado) return;
    mapa.removeFeatureState({ source: "paises" });
    for (const [iso, p] of Object.entries(paises)) mapa.setFeatureState({ source: "paises", id: iso }, { nivel: p.nivel });
    if (selecionadoRef.current) mapa.setFeatureState({ source: "paises", id: selecionadoRef.current }, { selecionado: true });
    aplicarCamadas(mapa, camadasRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paises, semDado, carregado]);

  // Pontos críticos: marcadores com o nome e a cor do estado medido pela regra (o robô decide o estado)
  useEffect(() => {
    const mapa = mapaRef.current;
    const maplibregl = maplibreRef.current;
    if (!mapa || !maplibregl || !carregado) return;
    marcadores.current.forEach((m) => m.remove());
    marcadores.current = pontos.map((p) => {
      const el = document.createElement("button");
      el.type = "button";
      el.className = `marcador ${estadoPonto(p.estado).classe}`;
      el.title = `${p.nome}: ${estadoPonto(p.estado).texto}`;
      el.dataset.ponto = p.id;
      el.innerHTML = `<i></i><span></span>`;
      (el.querySelector("span") as HTMLSpanElement).textContent = p.nome.split(" (")[0];
      el.addEventListener("click", (ev) => { ev.stopPropagation(); aoSelecionarRef.current({ tipo: "ponto", id: p.id }); });
      return new maplibregl.Marker({ element: el, anchor: "left" }).setLngLat([p.lon, p.lat]).addTo(mapa);
    });
    aplicarCamadas(mapa, camadasRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pontos, carregado]);

  useEffect(() => {
    const mapa = mapaRef.current;
    if (mapa?.isStyleLoaded()) aplicarCamadas(mapa, camadas);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camadas]);

  // Seleção: contorna o país e leva o mapa até ele ou até o ponto, sem ficar embaixo do painel
  useEffect(() => {
    const mapa = mapaRef.current;
    if (!mapa) return;
    const iso = selecao?.tipo === "pais" ? selecao.id : null;
    if (selecionadoRef.current) mapa.setFeatureState({ source: "paises", id: selecionadoRef.current }, { selecionado: false });
    selecionadoRef.current = iso;
    if (iso) mapa.setFeatureState({ source: "paises", id: iso }, { selecionado: true });
    const alvo = selecao?.tipo === "pais" ? porIso.get(selecao.id)?.centro
      : selecao?.tipo === "ponto" ? (() => { const p = pontos.find((x) => x.id === selecao.id); return p ? [p.lon, p.lat] : null; })()
      : null;
    if (alvo) mapa.flyTo({ center: alvo as [number, number], zoom: Math.max(mapa.getZoom(), selecao?.tipo === "ponto" ? 3.2 : 2.6) });
    for (const m of marcadores.current) {
      m.getElement().classList.toggle("ativo", selecao?.tipo === "ponto" && m.getElement().dataset.ponto === selecao.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selecao, porIso]);

  // Dados novos de terremotos sem recriar o mapa
  useEffect(() => {
    const fonte = mapaRef.current?.getSource("terremotos") as GeoJSONSource | undefined;
    fonte?.setData(geoTerremotos(terremotos));
  }, [terremotos]);

  const sugestoes = useMemo(() => {
    const q = semAcento(busca.trim());
    if (q.length < 2) return [];
    const doPonto = pontos.filter((p) => semAcento(p.nome).includes(q)).map((p) => ({ tipo: "ponto" as const, id: p.id, nome: p.nome }));
    const apelido = porIso.get(APELIDOS[q] ?? "");
    const achados = lista.filter((i) => semAcento(i.nome).includes(q) || semAcento(i.nome_en).includes(q) || i.iso.toLowerCase() === q)
      .sort((a, b) => Number(!semAcento(a.nome).startsWith(q)) - Number(!semAcento(b.nome).startsWith(q)) || a.nome.localeCompare(b.nome));
    const doPais = (apelido ? [apelido, ...achados.filter((i) => i !== apelido)] : achados)
      .map((i) => ({ tipo: "pais" as const, id: i.iso, nome: i.nome }));
    return [...doPonto, ...doPais].slice(0, 7);
  }, [busca, lista, porIso, pontos]);

  function projetar(paraPlano: boolean) {
    setPlano(paraPlano);
    mapaRef.current?.setProjection({ type: paraPlano ? "mercator" : "globe" });
  }

  function escolher(s: Selecao) {
    setBusca("");
    aoSelecionar(s);
  }

  const medido = camadas.citacoes && !semDado;
  return (
    <div className="globo">
      <div ref={caixa} className="globo-mapa" aria-label="Globo. Clique num país ou num ponto crítico para ver o contexto." />
      <div className="globo-busca">
        <input type="search" value={busca} placeholder="Buscar país ou ponto crítico…" aria-label="Buscar país ou ponto crítico"
               onChange={(e) => setBusca(e.target.value)}
               onKeyDown={(e) => { if (e.key === "Enter" && sugestoes[0]) escolher({ tipo: sugestoes[0].tipo, id: sugestoes[0].id }); }} />
        {sugestoes.length > 0 && (
          <ul className="sugestoes">
            {sugestoes.map((s) => (
              <li key={`${s.tipo}-${s.id}`}>
                <button type="button" onClick={() => escolher({ tipo: s.tipo, id: s.id })}>
                  {s.nome} <span className="discreto">{s.tipo === "ponto" ? "ponto crítico" : s.id}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="legenda" aria-label="Legenda">
        {camadas.pontos && (
          <div className="legenda-faixas">
            <span><i className="marca-legenda estado-critico" />Crítico</span>
            <span><i className="marca-legenda estado-pauta" />Em pauta</span>
            <span><i className="marca-legenda estado-calmo" />Sem pauta</span>
          </div>
        )}
        <div className="legenda-faixas">
          {medido ? (<>
            <span className="discreto">Notícias que citam o país ({janelaHoras} h):</span>
            <span><i style={{ background: CORES_NIVEL[0] }} />0</span>
            {faixas(niveis).map((r, i) => <span key={r}><i style={{ background: CORES_NIVEL[i + 1] }} />{r}</span>)}
          </>) : semDado ? <span><i style={{ background: COR_SEM_DADO }} />Sem dado: o robô não publicou a contagem</span> : null}
        </div>
        {(camadas.terremotos || camadas.rotas) && (
          <div className="legenda-faixas">
            {camadas.terremotos && <span><i className="marca-legenda terremoto" />Terremoto 4,5+ (24 h)</span>}
            {camadas.rotas && <span><i className="marca-legenda rota" />Rota (esquemática)</span>}
          </div>
        )}
      </div>
      {plano !== null && (
        <div className="projecao" role="group" aria-label="Forma do mapa">
          <button type="button" aria-pressed={!plano} className={!plano ? "ativo" : ""} onClick={() => projetar(false)}>Globo</button>
          <button type="button" aria-pressed={plano} className={plano ? "ativo" : ""} onClick={() => projetar(true)}>Plano</button>
        </div>
      )}
      {sobre && <div className="globo-dica">{sobre}</div>}
      {erro && <div className="globo-erro">Não foi possível carregar o mapa. Recarregue a página.</div>}
    </div>
  );
}
