import type { Status } from "./status";

/** Os dados que a página inicial usa (o status.json inteiro tem mais coisa, que fica nas outras telas). */
export type DadosInicio = Pick<Status, "gerado_em" | "paises" | "atencao" | "pontos" | "terremotos" | "faixa" | "mercados"
  | "historias" | "ultimos_documentos" | "contagem_historias" | "mais_citados" | "origem_fontes" | "totais" | "ultima_rodada"
  | "banco">;

/** Usada na montagem do site e a cada atualização automática da página (decisão 0016). */
export function escolherDados(s: Status): DadosInicio {
  return {
    gerado_em: s.gerado_em, paises: s.paises ?? {}, atencao: s.atencao, pontos: s.pontos, terremotos: s.terremotos ?? [],
    faixa: s.faixa ?? [], mercados: s.mercados, historias: s.historias ?? [], ultimos_documentos: s.ultimos_documentos ?? [],
    contagem_historias: s.contagem_historias, mais_citados: s.mais_citados ?? [], origem_fontes: s.origem_fontes ?? [],
    totais: s.totais, ultima_rodada: s.ultima_rodada, banco: s.banco,
  };
}
