import AvisoAtraso from "@/components/AvisoAtraso";
import Cartoes from "@/components/Cartoes";
import Globo from "@/components/Globo";
import HistoriasDoDia from "@/components/HistoriasDoDia";
import Indicadores from "@/components/Indicadores";
import Lateral from "@/components/Lateral";
import { NIVEIS_PADRAO } from "@/lib/constantes";
import { lerStatus } from "@/lib/status";

export default function Inicio() {
  const status = lerStatus();
  const a = status.atencao;
  return (<>
    <AvisoAtraso ate={status.avisar_atraso_apos} gerado={status.gerado_em} />
    <main className="painel-geral">
      <Lateral atual="/" />
      <section className="mapa-bloco bloco" aria-label="Mapa global">
        <Globo paises={status.paises} niveis={a?.niveis ?? NIVEIS_PADRAO} janelaHoras={a?.janela_horas ?? 24} semDado={!a} />
      </section>
      <Indicadores status={status} />
      <HistoriasDoDia historias={(status.historias ?? []).slice(0, 10)} />
      <Cartoes status={status} />
    </main>
  </>);
}
