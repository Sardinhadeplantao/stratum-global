import fs from "node:fs";
import path from "node:path";
import type { Mudanca } from "./formatar";

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
};
/** Séries de mercado lidas pela régua única (decisão 0011). Tudo vem calculado do robô; o site só mostra. */
export type Serie = {
  id: string; nome: string; unidade: string; pais: string | null; codigo: string; fonte: string; fonte_nome: string;
  conhecido_em: string | null; situacao: "ok" | "parada" | "historico_curto" | "sem_dado"; data: string | null;
  valor: number | null; variacao: number | null; percentil: number | null; extremo: "alta" | "baixa" | null;
  pontuacao: number | null; faixa: [number, number] | null; historico: number; mudancas: Mudanca[];
};
export type Mercados = {
  regua: { versao: string; janela_anos: number; minimo: Record<string, number>; extremo: number; persistencia: number;
    ritmo_pontos: number; ritmo_extremo: number };
  validade_dias: Record<string, number>; series: Serie[]; fora_do_normal: number;
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
  historias?: Historia[];
  /** Contagem pronta das histórias das últimas 24 horas (o site não conta, regra 9) */
  contagem_historias?: { total: number; varias_vozes: number } | null;
  /** Tradução automática dos títulos (decisão 0010), com a contagem pronta */
  traducao?: { modelo: string; traduzidos: number; na_fila: number; por_rodada: number } | null;
  regra_historias?: { versao: string; limiar: number; janela_horas: number } | null;
  mercados?: Mercados | null;
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
  versao_formato: 2, versao_robo: null, gerado_em: null, avisar_atraso_apos: null, agendador: null, copia: null, historias: [], contagem_historias: null, traducao: null, regra_historias: null, mercados: null, banco: null, erro_banco: null, ultima_rodada: null,
  rodadas_recentes: [], totais: { documentos: 0, documentos_24h: 0, fontes: 0, fontes_ok: 0 }, fontes: [], ultimos_documentos: [],
  atencao: null, paises: {}, mais_citados: [], origem_fontes: [],
};

/** Lido na hora de montar o site. Sem arquivo (robô ainda não rodou), devolve o estado vazio. */
export function lerStatus(): Status {
  const arquivo = path.join(process.cwd(), "public", "dados", "status.json");
  if (!fs.existsSync(arquivo)) return VAZIO;
  return { ...VAZIO, ...JSON.parse(fs.readFileSync(arquivo, "utf8")) };
}
