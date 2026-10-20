import fs from "node:fs";
import path from "node:path";

/** Formato do public/dados/status.json gravado pelo robô (jobs/stratum/export.py, versão 2). */
export type Coleta = { em: string | null; situacao: string; itens_lidos: number; itens_novos: number; erro: string | null };
export type Fonte = {
  id: string; nome: string; tipo: string; pais: string | null; pais_nome?: string | null; idioma: string | null; url: string;
  criterio: string | null; ativa: boolean; ultima_coleta: Coleta | null; documentos: number; documentos_24h: number;
  /** Ficha da fonte (decisão 0008) */
  nivel?: number | null; controle?: string | null; controlador_nome?: string | null; controlador_fontes?: string[];
};
export type PaisCitado = { iso: string; nome: string };
export type Documento = {
  titulo: string; url: string | null; fonte: string; fonte_nome: string; fonte_tipo?: string | null; fonte_pais?: string | null;
  fonte_pais_nome?: string | null; publicado_em: string | null; conhecido_em: string | null; paises?: PaisCitado[];
};
export type Atencao = {
  regra: string; janela_horas: number; inicio: string; fim: string; niveis: number[]; documentos: number;
  documentos_com_pais: number; oficiais: number; paises_citados: number; ignorados: string[];
};
export type HistoriaResumo = { id: number; titulo: string; noticias: number; vozes: number };
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
  titulo: string; url: string | null; fonte: string; fonte_nome: string; publicado_em: string | null; conhecido_em: string | null;
};
export type Historia = {
  id: number; titulo: string; noticias: number; fontes: number; vozes: number; ultima: string | null;
  paises: PaisCitado[]; documentos: DocumentoHistoria[];
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
  regra_historias?: { versao: string; limiar: number; janela_horas: number } | null;
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
  versao_formato: 2, versao_robo: null, gerado_em: null, avisar_atraso_apos: null, agendador: null, copia: null, historias: [], regra_historias: null, banco: null, erro_banco: null, ultima_rodada: null,
  rodadas_recentes: [], totais: { documentos: 0, documentos_24h: 0, fontes: 0, fontes_ok: 0 }, fontes: [], ultimos_documentos: [],
  atencao: null, paises: {}, mais_citados: [], origem_fontes: [],
};

/** Lido na hora de montar o site. Sem arquivo (robô ainda não rodou), devolve o estado vazio. */
export function lerStatus(): Status {
  const arquivo = path.join(process.cwd(), "public", "dados", "status.json");
  if (!fs.existsSync(arquivo)) return VAZIO;
  return { ...VAZIO, ...JSON.parse(fs.readFileSync(arquivo, "utf8")) };
}
