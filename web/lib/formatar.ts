/** Formatação para a tela. Só apresenta o que o robô gravou; nenhuma conta sobre os dados. */

const FUSO = "America/Sao_Paulo";
const DATA_HORA = new Intl.DateTimeFormat("pt-BR", {
  timeZone: FUSO, day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
});
const DIA_HORA = new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
const HORA = new Intl.DateTimeFormat("pt-BR", { timeZone: FUSO, hour: "2-digit", minute: "2-digit" });

function data(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "16/10/2026, 07:30" no horário de Brasília. Sem data, um traço. */
export function dataHora(iso: string | null | undefined): string {
  const d = data(iso);
  return d ? DATA_HORA.format(d) : "—";
}

/** "16/10, 07:30": para listas, onde o ano só ocupa espaço. */
export function diaHora(iso: string | null | undefined): string {
  const d = data(iso);
  return d ? DIA_HORA.format(d) : "—";
}

/**
 * As duas datas de uma notícia (regra 1): quando a fonte publicou e quando o robô soube.
 * Sem data da fonte, diz isso em vez de pôr a hora da coleta no lugar.
 */
export function datasDocumento(publicado: string | null | undefined, conhecido: string | null | undefined): string {
  const fonte = data(publicado) ? `publicado ${diaHora(publicado)}` : "sem data da fonte";
  return `${fonte} · coletado ${diaHora(conhecido)}`;
}

/** "07:30" no horário de Brasília. */
export function hora(iso: string | null | undefined): string {
  const d = data(iso);
  return d ? HORA.format(d) : "—";
}

const CONTINENTES: Record<string, string> = {
  Africa: "África", Antarctica: "Antártida", Asia: "Ásia", Europe: "Europa", "North America": "América do Norte",
  Oceania: "Oceania", "Seven seas (open ocean)": "Oceano", "South America": "América do Sul",
};

export function continente(nome: string | null | undefined): string {
  return nome ? CONTINENTES[nome] ?? nome : "—";
}

export type Situacao = "ok" | "parcial" | "falhou" | "rodando";

const SITUACOES: Record<Situacao, string> = { ok: "Funcionando", parcial: "Parcial", falhou: "Falhou", rodando: "Rodando" };

export function situacao(s: string | null | undefined): { texto: string; classe: string } {
  if (!s || !(s in SITUACOES)) return { texto: "Sem dado", classe: "sem-dado" };
  return { texto: SITUACOES[s as Situacao], classe: `sit-${s}` };
}

/** Cor do ponto do agendador: verde funcionando, amarelo atenção, vermelho falha, cinza sem dado. */
export function classeAgendador(s: string | null | undefined): string {
  if (s === "ok") return "sit-ok";  // "aguardando" ainda não mediu nada: cinza
  if (s === "vence_logo" || s === "sem_token") return "sit-parcial";
  if (s === "falhando" || s === "token_invalido" || s === "erro") return "sit-falhou";
  return "sem-dado";
}

const TIPOS: Record<string, string> = { oficial: "Oficial", imprensa: "Imprensa", dados: "Dados", social: "Rede social (pista)" };

export function tipoFonte(t: string | null | undefined): string {
  return t ? TIPOS[t] ?? t : "—";
}

export function numero(n: number): string {
  return n.toLocaleString("pt-BR");
}

/** Faixas da legenda a partir dos limites publicados pelo robô: [1, 3, 10, 30] -> "1–2", "3–9", "10–29", "30+". */
export function faixas(limites: number[]): string[] {
  return limites.map((l, i) => {
    const proximo = limites[i + 1];
    if (proximo === undefined) return `${l}+`;
    return proximo - 1 === l ? `${l}` : `${l}–${proximo - 1}`;
  });
}

export function plural(n: number, singular: string, plural: string): string {
  return `${numero(n)} ${n === 1 ? singular : plural}`;
}
