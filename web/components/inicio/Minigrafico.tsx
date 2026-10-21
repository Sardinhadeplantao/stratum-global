import { linhaMinigrafico } from "@/lib/formatar";

/** O último mês da série (os valores vêm do robô). Sem cor de alta ou queda: dourado só quando a régua diz que o dia
 * está fora do normal. */
export default function Minigrafico({ valores, fora }: { valores?: number[] | null; fora?: boolean }) {
  const pontos = linhaMinigrafico(valores, 56, 18);
  if (!pontos) return <span className="minigrafico vazio" aria-hidden />;
  return (
    <svg className={`minigrafico ${fora ? "fora" : ""}`} viewBox="-1 -1 58 20" width="56" height="20" aria-hidden>
      <polyline points={pontos} fill="none" strokeWidth="1.3" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
