import { diaHora, numero, plural, situacao } from "@/lib/formatar";
import type { Status } from "@/lib/status";

type Indicador = { rotulo: string; valor: string; detalhe: string; semDado?: boolean; classe?: string };

/** Só números medidos. O que ainda não é medido aparece em cinza, com a fase em que entra. */
export default function Indicadores({ status }: { status: Status }) {
  const a = status.atencao;
  const rodada = status.ultima_rodada;
  const h = status.contagem_historias;
  const lista: Indicador[] = [
    { rotulo: `Notícias em ${a?.janela_horas ?? 24} h`, valor: a ? numero(a.documentos) : "—",
      detalhe: "publicadas pelas fontes acompanhadas", semDado: !a },
    { rotulo: "Países citados", valor: a ? numero(a.paises_citados) : "—",
      detalhe: a ? `${plural(a.documentos_com_pais, "notícia cita", "notícias citam")} algum país` : "sem dado", semDado: !a },
    { rotulo: `Documentos oficiais em ${a?.janela_horas ?? 24} h`, valor: a ? numero(a.oficiais) : "—",
      detalhe: "das fontes oficiais da lista (veja Método)", semDado: !a },
    { rotulo: "Fontes funcionando", valor: rodada ? `${status.totais.fontes_ok} de ${status.totais.fontes}` : "—",
      detalhe: rodada ? `última rodada em ${diaHora(rodada.iniciada_em)}`
        : status.banco === "erro" ? "o banco não abriu nesta rodada" : "o robô ainda não rodou",
      classe: situacao(rodada?.situacao).classe, semDado: !rodada },
    { rotulo: "Histórias em 24 h", valor: h ? numero(h.total) : "—",
      detalhe: h ? `${numero(h.varias_vozes)} com 2 ou mais vozes independentes` : "sem dado", semDado: !h },
  ];
  return (
    <section className="indicadores" aria-label="Indicadores">
      {lista.map((i) => (
        <div key={i.rotulo} className={`indicador bloco ${i.semDado ? "sem-dado-bloco" : ""}`}>
          <span className="rotulo">{i.classe && <span className={`ponto ${i.classe}`} aria-hidden />}{i.rotulo}</span>
          <strong>{i.valor}</strong>
          <span className="discreto">{i.detalhe}</span>
        </div>
      ))}
    </section>
  );
}
