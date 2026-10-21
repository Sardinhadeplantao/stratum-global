import { dia, hora, leituraSerie, valor, variacaoSerie } from "@/lib/formatar";
import type { MercadoResumo } from "@/lib/status";
import Minigrafico from "./Minigrafico";

/** Uma série numa linha: valor, oscilação do dia com a leitura da régua e o último mês (tudo calculado pelo robô). */
export default function LinhaMercado({ s }: { s: MercadoResumo }) {
  const l = leituraSerie(s.situacao, s.extremo);
  const sobe = (s.variacao ?? 0) > 0;
  return (
    <li className="linha-mercado" title={l.texto}>
      <span className="lm-nome">{s.nome}<small>{s.unidade} · {s.parcial ? `hoje, ${hora(s.conhecido_em)}` : dia(s.data).slice(0, 5)}</small></span>
      <span className="lm-valor numero">{valor(s.valor)}</span>
      <span className={`lm-var numero ${s.extremo ? "fora" : ""}`}>
        <span className={`ponto ${l.classe}`} aria-hidden />
        {s.variacao === null || s.variacao === undefined ? "—" : <>{sobe ? "▲" : s.variacao < 0 ? "▼" : "•"} {variacaoSerie(s.variacao, s.medida)}</>}
      </span>
      <Minigrafico valores={s.mes} fora={!!s.extremo} />
    </li>
  );
}
