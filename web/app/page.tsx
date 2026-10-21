import AvisoAtraso from "@/components/AvisoAtraso";
import Inicio from "@/components/inicio/Inicio";
import { escolherDados } from "@/lib/inicio";
import { lerStatus } from "@/lib/status";

/** A página inicial (decisão 0014): o mapa, os pontos críticos, os mercados e as últimas informações num lugar só.
 * Os dados da montagem aparecem na hora; depois a página se atualiza sozinha (decisão 0016). */
export default function Pagina() {
  const s = lerStatus();
  return (<>
    <AvisoAtraso ate={s.avisar_atraso_apos} gerado={s.gerado_em} />
    <main><Inicio inicial={escolherDados(s)} /></main>
  </>);
}
