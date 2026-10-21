import fs from "node:fs";
import path from "node:path";
import type { Conferencia, Mudanca } from "./formatar";

/** Formato do public/dados/status.json gravado pelo robô (jobs/stratum/export.py, versão 2). */
export type Coleta = { em: string | null; situacao: string; itens_lidos: number; itens_novos: number; erro: string | null };
export type Fonte = {
  id: string; nome: string; tipo: string; pais: string | null; pais_nome?: string | null; idioma: string | null; url: string;
  criterio: string | null; ativa: boolean; ultima_coleta: Coleta | null; documentos: number; documentos_24h: number;
  /** Fonte de dados (decisão 0011): quantas observações guardadas */
  observacoes?: number;
  /** Ficha da fonte (decisão 0008) */
  nivel?: number | null; controle?: string | null; controlador_nome?: string | null; controlador_fontes?: string[];
};
export type PaisCitado = { iso: string; nome: string };
export type Documento = {
  titulo: string; titulo_original?: string | null; url: string | null; fonte: string; fonte_nome: string;
  fonte_tipo?: string | null; fonte_pais?: string | null;
  /** Quem é dono da fonte (ficha, decisão 0008): estatal | publico | privado | multilateral */
  fonte_controle?: string | null;
  fonte_pais_nome?: string | null; publicado_em: string | null; conhecido_em: string | null; paises?: PaisCitado[];
};
export type Atencao = {
  regra: string; janela_horas: number; inicio: string; fim: string; niveis: number[]; documentos: number;
  documentos_com_pais: number; oficiais: number; paises_citados: number; ignorados: string[];
};
export type HistoriaResumo = { id: number; titulo: string; titulo_original?: string | null; noticias: number; vozes: number };
export type PaisAtencao = { nome: string; citacoes: number; nivel: number; documentos: Documento[]; historias?: HistoriaResumo[] };
export type MaisCitado = { iso: string; nome: string; citacoes: number; proporcao: number };
export type Origem = { pais: string | null; nome: string; documentos: number; proporcao: number };
/** Agendador do Supabase (decisão 0004). O texto vem pronto do robô. */
export type Agendador = {
  situacao: "ok" | "aguardando" | "vence_logo" | "falhando" | "token_invalido" | "erro" | "sem_token" | "sem_banco";
  texto: string; erro: string | null; ultima_chamada: string | null; resposta: number | null;
  token_vence_em: string | null; dias_para_vencer: number | null;
};
/** Cópia semanal do banco (decisão 0007). O texto vem pronto do robô. */
export type Copia = { situacao: "ok" | "atrasada" | "nenhuma" | "sem_dado"; texto: string; ultima: string | null };
/** Histórias (decisão 0009): notícias da mesma história juntas por regra. Vozes = donos diferentes; é cobertura, não confirmação. */
export type DocumentoHistoria = {
  titulo: string; titulo_original?: string | null; url: string | null; fonte: string; fonte_nome: string;
  publicado_em: string | null; conhecido_em: string | null;
};
export type Historia = {
  id: number; titulo: string; titulo_original?: string | null; noticias: number; fontes: number; vozes: number; ultima: string | null;
  paises: PaisCitado[]; documentos: DocumentoHistoria[];
  /** A primeira notícia: o começo do evento (decisão 0017) */
  inicio?: string | null;
  /** Pontos críticos citados nos títulos */
  pontos?: string[];
  reacao?: Reacao | null;
};
/** Reação do mercado a um evento (decisão 0017): a régua de sempre no dia do evento e no pregão seguinte, a variação
 * desde o evento e a taxa-base. Coincidência no tempo, não causa. Tudo vem pronto do robô. */
export type DiaReacao = {
  data: string; variacao: number | null; percentil: number | null; extremo: "alta" | "baixa" | null; situacao: string; parcial: boolean;
};
export type AtivoReacao = {
  id: string; simbolo: string; nome: string; medida: string; grupo: string | null;
  por: { tipo: "ponto" | "pais"; id: string; nome: string };
  base: { data: string; valor: number } | null; dias: DiaReacao[]; extremo: "alta" | "baixa" | null;
  desde: number | null; ate: string | null; parcial: boolean;
};
export type Reacao = {
  regra: string; inicio: string; dia: string; situacao: "fora_do_normal" | "normal" | "aguardando" | "sem_ativo";
  fora: number; ativos: AtivoReacao[]; taxa_base: { pct: number; periodos: number; dias: number; anos: number } | null;
};
/** Séries de mercado lidas pela régua única (decisão 0011). Tudo vem calculado do robô; o site só mostra. */
export type Serie = {
  /** No padrão do mercado: USD/BRL, EUR/USD, DXY, US10Y, S&P 500 (decisão 0016) */
  id: string; simbolo?: string; nome: string; unidade: string; pais: string | null; codigo: string; fonte: string; fonte_nome: string;
  /** variacao_pct (preço, em %) ou diferenca (juros, em pontos percentuais) */
  medida: string;
  /** moedas | juros | bolsas | commodities | cripto (decisão 0013) */
  grupo: string | null;
  /** Só bolsas: americas | europa_africa | asia_pacifico (decisão 0014) */
  regiao?: string | null;
  /** Cotações dos últimos 30 dias, para o minigráfico (decisão 0014) */
  mes?: number[];
  conhecido_em: string | null; situacao: "ok" | "nao_confere" | "troca_de_contrato" | "parada" | "historico_curto" | "sem_dado";
  data: string | null;
  /** Dia em andamento (decisão 0012): a oscilação do dia, ainda não fechada */
  parcial: boolean;
  /** É verdade? Cotação de mercado comparada com a conta pela fonte oficial (decisão 0012) */
  conferir: boolean; conferencia: Conferencia | null;
  valor: number | null; variacao: number | null; percentil: number | null; extremo: "alta" | "baixa" | null;
  pontuacao: number | null; faixa: [number, number] | null; historico: number; mudancas: Mudanca[];
};
export type Mercados = {
  regua: { versao: string; janela_anos: number; minimo: Record<string, number>; extremo: number; persistencia: number;
    ritmo_pontos: number; ritmo_extremo: number };
  validade_dias: Record<string, number>; confere_ate_pct: number; series: Serie[]; fora_do_normal: number; nao_conferem: number;
  /** Ids das séries de cada país (moeda, juros, bolsa), para o painel do país */
  por_pais?: Record<string, string[]>;
  /** Quadros de destaque: lista fixa, escrita no robô (decisão 0014) */
  destaques?: { id: string; rotulo: string }[];
  /** Quantas sobem, caem ou ficam iguais no último dia (só leitura ok), com a proporção pronta */
  amplitude?: Amplitude;
};
export type Contagem = { sobem: number; caem: number; estaveis: number };
export type Amplitude = Contagem & { proporcao_sobem: number | null; por_grupo: Record<string, Contagem> };
/** Resumo de uma série nos painéis (a leitura completa está em mercados.series). */
export type MercadoResumo = Pick<Serie, "id" | "simbolo" | "nome" | "unidade" | "medida" | "data" | "valor" | "variacao" | "percentil"
  | "extremo" | "situacao" | "parcial" | "conhecido_em" | "mes">;
/** Ponto crítico do mapa (decisão 0014): estado por regra, com o contexto e as fontes. */
export type Ponto = {
  id: string; nome: string; lon: number; lat: number; estado: "critico" | "em_pauta" | "sem_pauta";
  noticias: number; vozes: number; com_acao: number;
  margens: PaisCitado[]; fatos: { texto: string; periodo: string; fonte: string; url: string }[];
  mercados: MercadoResumo[]; documentos: (Documento & { acao: boolean })[];
  /** A primeira notícia das últimas 24 horas que cita o ponto, e a reação do mercado desde ela (decisão 0017) */
  inicio?: string | null; reacao?: Reacao | null;
};
export type Terremoto = {
  id: string; titulo: string; url: string | null; magnitude: number | null; lat: number; lon: number;
  ocorreu_em: string | null; conhecido_em: string | null; fonte: string;
};
/** Item da faixa de baixo: o robô escolhe e ordena; o site só mostra. */
export type ItemFaixa = {
  tipo: "ponto" | "mercado" | "terremoto" | "noticia"; texto: string; id?: string; detalhe?: string; url?: string | null;
  fonte?: string; quando?: string | null; variacao?: number | null; medida?: string; extremo?: string | null; parcial?: boolean;
};
export type Status = {
  versao_formato: number;
  versao_robo: string | null;
  gerado_em: string | null;
  avisar_atraso_apos?: string | null;
  banco: "permanente" | "temporario" | "erro" | null;
  erro_banco: string | null;
  agendador?: Agendador | null;
  copia?: Copia | null;
  /** Arquivo conferido (decisão 0015): notícias que saíram do banco para o GitHub, com o último arquivamento */
  arquivo?: { documentos: number; ultimo: { etiqueta: string; url: string; corte: string | null; feito_em: string | null } | null } | null;
  historias?: Historia[];
  /** Contagem pronta das histórias das últimas 24 horas (o site não conta, regra 9) */
  contagem_historias?: { total: number; varias_vozes: number } | null;
  /** Tradução automática dos títulos (decisão 0010), com a contagem pronta */
  traducao?: { modelo: string; traduzidos: number; na_fila: number; por_rodada: number } | null;
  regra_historias?: { versao: string; limiar: number; janela_horas: number } | null;
  mercados?: Mercados | null;
  pontos?: { regra: string; lista: Ponto[]; criticos: number; em_pauta: number } | null;
  terremotos?: Terremoto[];
  faixa?: ItemFaixa[];
  ultima_rodada: { id: number; iniciada_em: string | null; terminada_em: string | null; situacao: string } | null;
  rodadas_recentes: { iniciada_em: string | null; situacao: string }[];
  totais: { documentos: number; documentos_24h: number; fontes: number; fontes_ok: number };
  fontes: Fonte[];
  ultimos_documentos: Documento[];
  atencao: Atencao | null;
  paises: Record<string, PaisAtencao>;
  mais_citados: MaisCitado[];
  origem_fontes: Origem[];
};

const VAZIO: Status = {
  versao_formato: 2, versao_robo: null, gerado_em: null, avisar_atraso_apos: null, agendador: null, copia: null, historias: [], contagem_historias: null, traducao: null, regra_historias: null, mercados: null, pontos: null, terremotos: [], faixa: [], banco: null, erro_banco: null, ultima_rodada: null,
  rodadas_recentes: [], totais: { documentos: 0, documentos_24h: 0, fontes: 0, fontes_ok: 0 }, fontes: [], ultimos_documentos: [],
  atencao: null, paises: {}, mais_citados: [], origem_fontes: [],
};

/** Lido na hora de montar o site. Sem arquivo (robô ainda não rodou), devolve o estado vazio. */
export function lerStatus(): Status {
  const arquivo = path.join(process.cwd(), "public", "dados", "status.json");
  if (!fs.existsSync(arquivo)) return VAZIO;
  return { ...VAZIO, ...JSON.parse(fs.readFileSync(arquivo, "utf8")) };
}
