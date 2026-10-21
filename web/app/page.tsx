import AvisoAtraso from "@/components/AvisoAtraso";
import Inicio from "@/components/inicio/Inicio";
import { NIVEIS_PADRAO } from "@/lib/constantes";
import { lerStatus } from "@/lib/status";

/** A página inicial (decisão 0014): o mapa, os pontos críticos, os mercados e as últimas informações num lugar só. */
export default function Pagina() {
  const s = lerStatus();
  const dados = {
    paises: s.paises, atencao: s.atencao, pontos: s.pontos, terremotos: s.terremotos, faixa: s.faixa, mercados: s.mercados,
    historias: s.historias, ultimos_documentos: s.ultimos_documentos, contagem_historias: s.contagem_historias,
    mais_citados: s.mais_citados, origem_fontes: s.origem_fontes, totais: s.totais, ultima_rodada: s.ultima_rodada, banco: s.banco,
  };
  return (<>
    <AvisoAtraso ate={s.avisar_atraso_apos} gerado={s.gerado_em} />
    <main><Inicio dados={dados} niveis={s.atencao?.niveis ?? NIVEIS_PADRAO} /></main>
  </>);
}
