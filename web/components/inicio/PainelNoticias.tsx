"use client";
import { useState } from "react";
import Link from "next/link";
import Titulo from "@/components/Titulo";
import { datasDocumento, donoFonte, numero, plural } from "@/lib/formatar";
import type { DadosInicio, Selecao } from "./Inicio";

type Filtro = "todas" | "imprensa" | "oficial";
const FILTROS: [Filtro, string][] = [["todas", "Todas"], ["imprensa", "Imprensa"], ["oficial", "Oficiais"]];
const semAcento = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/** A aba Notícias: as últimas manchetes com quem fala (dono e país da fonte), filtro por tipo e busca; depois, os países
 * mais citados e quem está falando. A busca e o filtro só escondem itens da lista que o robô mandou. */
export default function PainelNoticias({ dados, selecionar }: { dados: DadosInicio; selecionar: (s: Selecao) => void }) {
  const [filtro, setFiltro] = useState<Filtro>("todas");
  const [busca, setBusca] = useState("");
  const q = semAcento(busca.trim());
  const docs = (dados.ultimos_documentos ?? []).filter((d) => (filtro === "todas" || d.fonte_tipo === filtro)
    && (!q || semAcento(`${d.titulo} ${d.titulo_original ?? ""} ${d.fonte_nome} ${(d.paises ?? []).map((p) => p.nome).join(" ")}`).includes(q)));
  const janela = dados.atencao?.janela_horas ?? 24;
  return (<>
    <div className="busca-noticias">
      <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)} placeholder="Buscar nas manchetes, fontes e países…"
             aria-label="Buscar nas últimas manchetes" />
      <div className="filtros" role="group" aria-label="Tipo de fonte">
        {FILTROS.map(([id, nome]) => (
          <button key={id} type="button" className={filtro === id ? "filtro ativo" : "filtro"} aria-pressed={filtro === id}
                  onClick={() => setFiltro(id)}>{nome}</button>
        ))}
      </div>
    </div>
    {(dados.historias ?? []).length > 0 && (
      <div className="temas" aria-label="Histórias com mais vozes">
        {(dados.historias ?? []).slice(0, 8).map((h) => (
          <Link key={h.id} href={`/historias/#h${h.id}`} className="chip" title={`${h.titulo} · ${plural(h.vozes, "voz", "vozes")}`}>
            <span>{h.titulo}</span> <b>{h.vozes}</b>
          </Link>
        ))}
      </div>
    )}

    <section>
      <h3>Últimas manchetes</h3>
      {docs.length === 0 ? <p className="sem-dado-texto">{busca || filtro !== "todas" ? "Nada encontrado entre as últimas manchetes." : "Sem notícias nesta atualização."}</p> : (
        <ul className="lista-noticias cartoes-noticia">
          {docs.map((d, i) => (
            <li key={i}>
              <div className="quem-fala"><b>{d.fonte_nome}</b> {donoFonte(d.fonte_tipo, d.fonte_controle, d.fonte_pais_nome)}</div>
              <Titulo {...d} />
              <div className="discreto">{datasDocumento(d.publicado_em, d.conhecido_em)}</div>
              {d.paises && d.paises.length > 0 && (
                <div className="feed-paises">
                  {d.paises.map((p) => (
                    <button key={p.iso} type="button" className="chip" onClick={() => selecionar({ tipo: "pais", id: p.iso })}>{p.nome}</button>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>

    <section>
      <h3>Países mais citados <small className="discreto">({janela} h)</small></h3>
      {!dados.atencao ? <p className="sem-dado-texto">Sem dado nesta atualização.</p>
        : dados.mais_citados.length === 0 ? <p className="discreto">Nenhum país citado na janela.</p> : (
        <ol className="barras">
          {dados.mais_citados.slice(0, 8).map((p) => (
            <li key={p.iso}>
              <button type="button" className="link" onClick={() => selecionar({ tipo: "pais", id: p.iso })}>{p.nome}</button>
              <span className="barra"><i style={{ width: `${Math.max(p.proporcao * 100, 2)}%` }} /></span>
              <span className="numero">{numero(p.citacoes)}</span>
            </li>
          ))}
        </ol>
      )}
    </section>

    <section>
      <h3>Quem está falando</h3>
      <p className="discreto">Notícias em {janela} h pelo país de cada fonte: mostra quanto as fontes de cada país publicam, não quem
        pauta o assunto.</p>
      {!dados.atencao ? <p className="sem-dado-texto">Sem dado nesta atualização.</p> : (
        <ol className="barras">
          {dados.origem_fontes.map((o) => (
            <li key={o.pais ?? "internacional"}>
              <span>{o.nome}</span>
              <span className="barra barra-neutra"><i style={{ width: `${Math.max(o.proporcao * 100, 2)}%` }} /></span>
              <span className="numero">{numero(o.documentos)}</span>
            </li>
          ))}
        </ol>
      )}
      <p className="discreto nota-aba">{dados.atencao ? `${plural(dados.atencao.documentos, "notícia", "notícias")} em ${janela} h, ` : ""}
        das fontes da lista. <Link href="/metodo/">Fontes e critérios</Link></p>
    </section>
  </>);
}
