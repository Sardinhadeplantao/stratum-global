"use client";
import type { Camadas } from "./Inicio";

const ITENS: { id: keyof Camadas; nome: string }[] = [
  { id: "pontos", nome: "Pontos críticos" },
  { id: "rotas", nome: "Rotas marítimas" },
  { id: "citacoes", nome: "Países nas notícias" },
  { id: "terremotos", nome: "Terremotos" },
];

/** Camadas do mapa, cada uma com a contagem pronta (o robô conta; aqui só se mostra). */
export default function CamadasMapa({ camadas, mudar, contagens }: {
  camadas: Camadas; mudar: (c: Camadas) => void; contagens: Record<keyof Camadas, string>;
}) {
  return (
    <div className="camadas-mapa" role="group" aria-label="Camadas do mapa">
      <span className="rotulo">Camadas</span>
      <ul>
        {ITENS.map((c) => (
          <li key={c.id}>
            <button type="button" role="switch" aria-checked={camadas[c.id]} className={`camada ${camadas[c.id] ? "ligada" : ""}`}
                    onClick={() => mudar({ ...camadas, [c.id]: !camadas[c.id] })}>
              <span className="chave" aria-hidden><i /></span>
              <span className="camada-nome">{c.nome}<small>{contagens[c.id]}</small></span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
