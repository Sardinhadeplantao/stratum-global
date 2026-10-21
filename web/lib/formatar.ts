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

export function classeCopia(s: string | null | undefined): string {
  if (s === "ok") return "sit-ok";
  if (s === "atrasada" || s === "nenhuma") return "sit-falhou";
  return "sem-dado";  // não conferida nesta rodada: cinza
}

const CONTROLES: Record<string, string> = { privado: "Privado", publico: "Público", estatal: "Estatal", multilateral: "Multilateral" };

/** Tipo de controle da fonte (decisão 0008); sem ficha, travessão. */
export function controleFonte(c: string | null | undefined): string {
  return c ? CONTROLES[c] ?? c : "—";
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

/** "2026-10-16" (dia da cotação, sem hora) -> "16/10/2026", sem passar por fuso. */
export function dia(iso: string | null | undefined): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso ?? "");
  return m ? `${m[3]}/${m[2]}/${m[1]}` : "—";
}

/** Valor como a fonte publicou, com até 4 casas. */
export function valor(n: number | null | undefined): string {
  return n === null || n === undefined ? "—" : n.toLocaleString("pt-BR", { maximumFractionDigits: 4 });
}

/** Variação já calculada pelo robô: "+0,45%". */
export function variacao(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return `${n > 0 ? "+" : ""}${n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`;
}

/** Os grupos de séries, na ordem da tela (decisão 0013). */
export const GRUPOS_SERIES: [string, string][] = [
  ["moedas", "Moedas"], ["juros", "Juros de 10 anos"], ["bolsas", "Bolsas"], ["commodities", "Commodities"], ["cripto", "Cripto"],
];

/** Variação na unidade da medida: preço em % ("+0,45%"), juros em pontos percentuais ("+0,10 p.p."). */
export function variacaoSerie(n: number | null | undefined, medida: string | null | undefined): string {
  if (medida !== "diferenca" || n === null || n === undefined) return variacao(n);
  return `${n > 0 ? "+" : ""}${n.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} p.p.`;
}

/** Leitura da régua (decisão 0011). Cor só para estado medido: fora do normal (os dois lados com a mesma cor),
 *  dentro do normal; parada, histórico curto e sem dado ficam cinza. */
export function leituraSerie(situacao: string | null | undefined, extremo: string | null | undefined): { texto: string; classe: string } {
  if (situacao === "ok" && extremo === "alta") return { texto: "Fora do normal: alta", classe: "sit-fora" };
  if (situacao === "ok" && extremo === "baixa") return { texto: "Fora do normal: queda", classe: "sit-fora" };
  if (situacao === "ok") return { texto: "Dentro do normal", classe: "sit-normal" };
  if (situacao === "nao_confere") return { texto: "Não confere com a fonte oficial", classe: "sit-falhou" };
  if (situacao === "troca_de_contrato") return { texto: "Troca de contrato: a variação de hoje não mede o mercado", classe: "sem-dado" };
  if (situacao === "parada") return { texto: "Parada (dado velho)", classe: "sem-dado" };
  if (situacao === "historico_curto") return { texto: "Histórico curto", classe: "sem-dado" };
  return { texto: "Sem dado", classe: "sem-dado" };
}

export type Conferencia = { com: string; data: string; oficial: number; diferenca: number; confere: boolean };

/** "Confere com o BCE em 20/10/2026 (diferença de -0,12%)". O robô já decidiu se confere. */
export function textoConferencia(c: Conferencia | null | undefined, conferir: boolean | undefined): string | null {
  if (!c) return conferir ? "Ainda sem dia em comum com a fonte oficial para conferir." : null;
  const diferenca = variacao(c.diferenca);
  return c.confere ? `Confere com o ${c.com} em ${dia(c.data)} (diferença de ${diferenca}).`
    : `Não confere com o ${c.com} em ${dia(c.data)}: diferença de ${diferenca}.`;
}

/** Estado de um ponto crítico (decisão 0014), decidido pelo robô. A cor é do estado medido pela regra. */
export function estadoPonto(estado: string | null | undefined): { texto: string; classe: string; explica: string } {
  if (estado === "critico") return { texto: "Crítico", classe: "estado-critico",
    explica: "Notícias de pelo menos duas vozes independentes citam o ponto, e alguma fala de ação (ataque, míssil, mina, apreensão, bloqueio)." };
  if (estado === "em_pauta") return { texto: "Em pauta", classe: "estado-pauta",
    explica: "Alguma notícia das últimas 24 horas cita o ponto." };
  if (estado === "sem_pauta") return { texto: "Sem pauta", classe: "estado-calmo",
    explica: "Nenhuma notícia das últimas 24 horas cita o ponto." };
  return { texto: "Sem dado", classe: "sem-dado", explica: "O robô não publicou o estado nesta atualização." };
}

/** "M 6,3" */
export function magnitude(m: number | null | undefined): string {
  return m === null || m === undefined ? "M ?" : `M ${m.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}`;
}

export type Mudanca = { tipo: string; sentido: string; desde: string; taxa_base: { vezes: number; anos: number } };

/** "Alta fora do normal por dias seguidos, desde 15/10/2026. Nos 5 anos anteriores: 3 vezes." */
export function textoMudanca(m: Mudanca): string {
  const oque = m.tipo === "quebra_de_ritmo" ? "Agitação fora do normal"
    : `${m.sentido === "alta" ? "Alta" : "Queda"} fora do normal por dias seguidos`;
  const anos = m.taxa_base.anos.toLocaleString("pt-BR");
  return `${oque}, desde ${dia(m.desde)}. Nos ${anos} anos anteriores: ${plural(m.taxa_base.vezes, "vez", "vezes")}.`;
}

/** As regiões das bolsas, na ordem da tela (decisão 0014; a região de cada bolsa vem do robô). */
export const REGIOES_BOLSA: [string, string][] = [
  ["americas", "Américas"], ["europa_africa", "Europa, Oriente Médio e África"], ["asia_pacifico", "Ásia e Pacífico"],
];

const DONO: Record<string, string> = { estatal: "estatal", publico: "pública", privado: "privada", multilateral: "multilateral" };

/** Quem fala, ao lado de cada notícia: "imprensa estatal · Rússia", "oficial · EUA" (ficha da fonte, decisão 0008). */
export function donoFonte(tipo: string | null | undefined, controle: string | null | undefined, pais: string | null | undefined): string {
  const dono = controle ? DONO[controle] ?? controle : null;
  const quem = tipo === "oficial" ? (controle === "multilateral" ? "oficial multilateral" : "oficial")
    : dono ? `imprensa ${dono}` : tipo === "imprensa" ? "imprensa" : null;
  return [quem, pais].filter(Boolean).join(" · ");
}

/** Os pontos do minigráfico (SVG). Só desenha os valores que o robô mandou; menos de 2, nada. */
export function linhaMinigrafico(valores: number[] | null | undefined, largura: number, altura: number): string | null {
  if (!valores || valores.length < 2) return null;
  const min = Math.min(...valores), max = Math.max(...valores);
  const passo = largura / (valores.length - 1);
  return valores.map((v, i) => {
    const y = max === min ? altura / 2 : altura - ((v - min) / (max - min)) * altura;
    return `${(i * passo).toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}
