import AvisoAtraso from "@/components/AvisoAtraso";
import { classeAgendador, classeCopia, controleFonte, dataHora, dia, faixas, leituraSerie, numero, plural, situacao, textoMudanca, tipoFonte, valor, variacao } from "@/lib/formatar";
import { lerStatus, type Fonte } from "@/lib/status";
import Titulo from "@/components/Titulo";

export const metadata = { title: "Método · Stratum Global" };

const BANCO: Record<string, string> = {
  permanente: "Permanente (Supabase). O que o robô coleta fica guardado.",
  temporario: "Temporário. O banco ainda não foi configurado: cada rodada começa do zero e nada fica guardado.",
  erro: "O robô não conseguiu abrir o banco nesta rodada.",
};

/** Fontes com o mesmo critério aparecem juntas, para o critério não se repetir em cada linha. */
function agruparCriterios(fontes: Fonte[]): [string, string[]][] {
  const grupos = new Map<string, string[]>();
  for (const f of fontes) {
    if (f.criterio) grupos.set(f.criterio, [...(grupos.get(f.criterio) ?? []), f.nome]);
  }
  return [...grupos.entries()];
}

export default function Metodo() {
  const s = lerStatus();
  const rodada = s.ultima_rodada;
  const sit = situacao(rodada?.situacao);
  const a = s.atencao;
  const semBanco = s.banco === "erro";
  const SEM_BANCO = "Sem dado nesta atualização: o banco não abriu.";
  const criterios = agruparCriterios(s.fontes.filter((f) => f.ativa));
  const m = s.mercados;
  const nomeFonte = Object.fromEntries(s.fontes.map((f) => [f.id, f.nome]));
  return (<>
    <AvisoAtraso ate={s.avisar_atraso_apos} gerado={s.gerado_em} />
    <main className="pagina">
      <h1>Método</h1>
      <p className="lead">Posso confiar? Esta página mostra como o Stratum Global funciona, o que ele mede e o que ainda não mede.</p>

      <section>
        <h2>Regra de ouro</h2>
        <p>
          O Stratum Global não prevê o futuro: mostra o que está acontecendo, com fonte, e as forças que podem moldar o
          que vem depois. Ele <b>não</b> prevê guerra, eleição ou preço, <b>não</b> recomenda compra ou venda e{" "}
          <b>não</b> apresenta opinião como dado.
        </p>
      </section>

      <section>
        <h2>Regras</h2>
        <ul className="regras">
          <li><b>Toda informação tem fonte e duas datas:</b> quando a fonte publicou (se ela informa) e quando o sistema soube.</li>
          <li><b>Nada é apagado nem reescrito.</b> Correção vira registro novo.</li>
          <li><b>Notícias da mesma história aparecem juntas</b> (página Histórias), com quantos donos diferentes as publicaram.
            Isso é cobertura, não confirmação: o grau de confirmação de cada fato ainda não existe. Rede social é só pista, nunca fato.</li>
          <li><b>Fontes entram por critério escrito,</b> não por parecerem interessantes.</li>
          <li><b>Regra decide; IA só lê, resume e traduz.</b> O sistema funciona sem IA.</li>
          <li><b>Preço é contexto:</b> nunca ordena eventos nem dispara aviso sozinho.</li>
          <li><b>O site não calcula:</b> mostra o que o robô gravou. Cinza quer dizer sem dado.</li>
        </ul>
        <h3>Versões em vigor</h3>
        <dl className="resumo">
          <dt>Citação de países</dt><dd>{a?.regra ?? "sem dado"} (regra de dicionário, sem IA)</dd>
          <dt>Histórias</dt><dd>{s.regra_historias?.versao ?? "sem dado"} (regra de palavras em comum, sem IA)</dd>
          <dt>Tradução dos títulos</dt><dd>{s.traducao?.modelo ?? "sem dado"} (tradução automática gratuita; só traduz, não decide)</dd>
          <dt>Régua dos mercados</dt><dd>{m?.regua.versao ?? "sem dado"} (percentil contra o próprio histórico, sem IA)</dd>
        </dl>
      </section>

      <section>
        <h2>Como juntamos as histórias</h2>
        <p>
          Cada notícia vira uma lista do que ela cita: países, nomes próprios, números e palavras de ação (ataque,
          protesto, sanção). Quando uma notícia nova tem bastante em comum com uma das últimas{" "}
          {s.regra_historias?.janela_horas ?? 48} horas, ela entra na história daquela; senão, abre uma história nova.
          O que é raro naquele dia vale mais que o que é comum. Nada é movido depois.
        </p>
        <ul className="regras">
          <li><b>Regra {s.regra_historias?.versao ?? "—"}</b>, sem IA. Medida em dois dias de notícias anotados pelo Claude:
            das notícias que ela junta, de 88% a 100% são mesmo da mesma história.</li>
          <li><b>Ela junta pouco.</b> Prefere deixar separado a juntar errado, então uma história grande pode aparecer em
            pedaços.</li>
          <li><b>Mesma história não é mesmo fato.</b> &quot;Trump aprova a execução&quot; e &quot;Trump cancela a transmissão da execução&quot;
            são a mesma história e fatos diferentes. Por isso ainda não há selo de &quot;confirmado&quot;.</li>
          <li><b>Vozes independentes</b> são donos diferentes: dois veículos do mesmo Estado ou do mesmo grupo contam como uma
            voz (veja &quot;Quem controla cada fonte&quot;).</li>
        </ul>
      </section>

      <section>
        <h2>Títulos em português</h2>
        <p>
          Manchetes de fontes em outras línguas aparecem traduzidas por um programa gratuito (Argos), que roda junto com
          o robô, sem IA paga. O título original nunca muda: a contagem de países e as histórias usam o original, e todo
          título traduzido leva a marca &quot;(tradução automática)&quot;, com o original ao passar o mouse (na página
          Histórias, escrito embaixo).
        </p>
        <ul className="regras">
          <li><b>Tradução automática erra.</b> Exemplos vistos: &quot;mine&quot; (mina) virou &quot;meu&quot;; &quot;massive&quot; sumiu de
            &quot;massive police deployment&quot;. Na dúvida, vale o original.</li>
          {s.traducao ? (
            <li><b>{plural(s.traducao.traduzidos, "título traduzido", "títulos traduzidos")}</b>
              {s.traducao.na_fila > 0
                ? <>; {plural(s.traducao.na_fila, "espera", "esperam")} a vez (até {numero(s.traducao.por_rodada)} por rodada,
                    das mais novas para as mais antigas). Enquanto isso, aparecem em inglês.</>
                : "; nenhum na fila."}</li>
          ) : <li className="sem-dado-texto">Sem dado nesta atualização.</li>}
        </ul>
      </section>

      <section>
        <h2>Como contamos as citações de países</h2>
        <p>
          O globo pinta cada país pela quantidade de notícias que o citam, entre as publicadas nas últimas{" "}
          {a?.janela_horas ?? 24} horas pelas fontes acompanhadas. Uma notícia cita um país quando o título ou o resumo traz:
        </p>
        <ul className="regras">
          <li>o nome dele, em inglês ou português;</li>
          <li>o gentílico (<i>Russian</i>, <i>russo</i>; em português, só dos países mais presentes no noticiário);</li>
          <li>a capital, um estado dos EUA ou uma cidade que só existe naquele país (<i>Oregon</i>, <i>Áden</i>);</li>
          <li>uma sigla aceita (US, UK, EUA, UAE);</li>
          <li>ou uma referência direta ao governo (Kremlin, Casa Branca).</li>
        </ul>
        <p>Cuidados da regra:</p>
        <ul className="regras">
          <li>Cada notícia conta uma vez por país, mesmo que cite o país várias vezes.</li>
          <li>Diferencia maiúsculas: <i>Turkey</i> é país, <i>turkey</i> não. Nome dentro de outra palavra não conta (<i>Niger</i> em <i>Nigeria</i>).</li>
          <li>O termo mais longo vence: <i>Papua New Guinea</i> não conta Guiné; <i>South Americans</i> não conta os Estados Unidos.</li>
          <li>Sedes internacionais não contam o país: <i>Bruxelas</i> quase sempre quer dizer a União Europeia, e <i>Haia</i>, os tribunais.</li>
          <li>Nomes de pessoas não contam: uma notícia que só fala de Netanyahu não conta Israel.</li>
          <li>Notícias de rede social nunca entram na conta (são pista, não fato).</li>
          <li>Citação mede a atenção das fontes acompanhadas, não importância nem gravidade.</li>
          <li>A regra pode errar. Toda contagem leva às notícias, para conferir.</li>
        </ul>
        {a && (
          <dl className="resumo">
            <dt>Versão da regra</dt><dd>{a.regra}</dd>
            <dt>Faixas de cor</dt><dd>{faixas(a.niveis).join(" · ")} notícias</dd>
            <dt>Nesta rodada</dt>
            <dd>
              {plural(a.documentos, "notícia", "notícias")} na janela, {numero(a.documentos_com_pais)} com algum país,{" "}
              {plural(a.paises_citados, "país citado", "países citados")}
            </dd>
            <dt>Termos ignorados</dt><dd>{a.ignorados.join(", ")} (apontam para mais de um lugar, para uma pessoa ou para uma sede internacional)</dd>
          </dl>
        )}
      </section>

      <section id="regua">
        <h2>Mercados: a régua única</h2>
        <p>
          Cada série é comparada só com o próprio passado. O robô pega a variação de hoje (desde a cotação anterior) e vê
          em que posição ela fica entre as variações dos {m?.regua.janela_anos ?? 5} anos anteriores: é o percentil.
          Percentil 97 quer dizer que 97% das variações desses anos foram menores. Os parâmetros são os mesmos para todas
          as séries e foram fixados antes do primeiro dado (decisão 0011).
        </p>
        {m ? (
          <dl className="resumo">
            <dt>Versão</dt><dd>{m.regua.versao}</dd>
            <dt>Medida</dt><dd>Variação em % desde a cotação anterior (fim de semana e feriado não contam)</dd>
            <dt>Histórico</dt><dd>As variações dos {m.regua.janela_anos} anos anteriores, sem o próprio dia e sem nada depois dele</dd>
            <dt>Fora do normal</dt><dd>Percentil até {m.regua.extremo} (queda) ou a partir de {100 - m.regua.extremo} (alta)</dd>
            <dt>Mínimo</dt><dd>{numero(m.regua.minimo.diaria)} cotações no histórico; abaixo disso, &quot;histórico curto&quot;, sem leitura</dd>
            <dt>Mudança</dt><dd>{m.regua.persistencia} dias seguidos fora do normal do mesmo lado; ou a agitação (das últimas{" "}
              {m.regua.ritmo_pontos} variações) no percentil {m.regua.ritmo_extremo} ou mais. Cada mudança diz quantas vezes
              já aconteceu nos 5 anos anteriores.</dd>
            <dt>Validade</dt><dd>{Object.entries(m.validade_dias).map(([f, d]) => `${nomeFonte[f] ?? f}: ${d} dias`).join(" · ")}.
              Passou disso, a série fica parada (cinza)</dd>
            <dt>Revisão</dt><dd>Valor corrigido pela fonte entra como registro novo; o antigo fica</dd>
          </dl>
        ) : <p className="sem-dado-texto">Sem dado nesta atualização.</p>}
        <ul className="regras">
          <li><b>Preço é contexto.</b> A régua não manda aviso, não ordena notícias e não prevê nada. Alta e queda fora do
            normal têm a mesma cor: a cor não diz se é bom ou ruim.</li>
          <li><b>O nome diz o sentido:</b> &quot;Euro em reais&quot; sobe quando o euro fica mais caro. Cada valor aparece como a
            fonte publicou, sem conta.</li>
          <li><b>A lista é ordenada pela distância do normal</b> (em desvios medianos), nunca pelo preço ou pelo nome.</li>
        </ul>
        {m && m.series.length > 0 && (
          <div className="tabela-rolagem">
            <table>
              <thead>
                <tr><th>Série</th><th>Dia</th><th className="numero">Valor</th><th className="numero">Variação</th>
                  <th className="numero">Percentil</th><th className="numero">Faixa normal</th><th>Leitura</th></tr>
              </thead>
              <tbody>
                {m.series.map((x) => {
                  const l = leituraSerie(x.situacao, x.extremo);
                  return (
                    <tr key={x.id}>
                      <td>{x.nome}<div className="discreto">{x.unidade} · {x.fonte_nome}</div></td>
                      <td>{dia(x.data)}</td>
                      <td className="numero">{valor(x.valor)}</td>
                      <td className="numero">{variacao(x.variacao)}</td>
                      <td className="numero">{x.percentil === null ? "—" : x.percentil.toLocaleString("pt-BR")}</td>
                      <td className="numero">{x.faixa ? `${variacao(x.faixa[0])} a ${variacao(x.faixa[1])}` : "—"}</td>
                      <td>
                        <span className={`ponto ${l.classe}`} aria-hidden /> {l.texto}
                        {x.mudancas.map((mu, i) => <div key={i} className="discreto">{textoMudanca(mu)}</div>)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section>
        <h2>Saúde do robô</h2>
        {s.erro_banco && <p className="alerta">{s.erro_banco}</p>}
        <dl className="resumo">
          <dt>Última rodada</dt>
          <dd><span className={`ponto ${sit.classe}`} aria-hidden /> {sit.texto} · {dataHora(rodada?.iniciada_em)} (Brasília)</dd>
          <dt>Banco</dt><dd>{s.banco ? BANCO[s.banco] : "—"}</dd>
          <dt>Agendador</dt>
          <dd>
            {s.agendador ? (<>
              <span className={`ponto ${classeAgendador(s.agendador.situacao)}`} aria-hidden />{" "}
              {s.agendador.texto.charAt(0).toUpperCase() + s.agendador.texto.slice(1)}.
              {s.agendador.ultima_chamada && <> Última chamada: {dataHora(s.agendador.ultima_chamada)}.</>}
              {s.agendador.token_vence_em && <> O token vence em {dataHora(s.agendador.token_vence_em)}.</>}
            </>) : <span className="sem-dado-texto">—</span>}
          </dd>
          <dt>Cópia do banco</dt>
          <dd>
            {s.copia ? (<>
              <span className={`ponto ${classeCopia(s.copia.situacao)}`} aria-hidden />{" "}
              {s.copia.texto.charAt(0).toUpperCase() + s.copia.texto.slice(1)}.
              {s.copia.ultima && <> Última: {dataHora(s.copia.ultima)}.</>} Uma por semana, guardada no GitHub por 90 dias,
              com a restauração testada.
            </>) : <span className="sem-dado-texto">—</span>}
          </dd>
          <dt>Telegram</dt><dd>Um resumo às 7:30, 12:00 e 19:00 (Brasília). Problemas entram no resumo seguinte.</dd>
          <dt>Fontes funcionando</dt>
          <dd>{rodada ? `${s.totais.fontes_ok} de ${s.totais.fontes}` : <span className="sem-dado-texto">—</span>}</dd>
          <dt>Documentos</dt>
          <dd>
            {semBanco ? <span className="sem-dado-texto">—</span>
              : <>{numero(s.totais.documentos)} no total · {numero(s.totais.documentos_24h)} coletados nas últimas 24h</>}
          </dd>
          <dt>Versão do robô</dt><dd>{s.versao_robo ?? "—"}</dd>
        </dl>
        {s.rodadas_recentes.length > 0 && (
          <div className="rodadas" aria-label="Rodadas recentes, da mais nova para a mais antiga">
            {s.rodadas_recentes.map((r, i) => {
              const x = situacao(r.situacao);
              return <span key={i} className={`quadrado ${x.classe}`} title={`${dataHora(r.iniciada_em)}: ${x.texto}`} />;
            })}
          </div>
        )}
      </section>

      <section>
        <h2>Fontes</h2>
        {s.fontes.length === 0 ? <p className="sem-dado-texto">{semBanco ? SEM_BANCO : "O robô ainda não rodou."}</p> : (
          <div className="tabela-rolagem">
            <table>
              <thead>
                <tr><th>Fonte</th><th>Tipo</th><th>País</th><th>Última coleta</th><th>Situação</th><th>Novos</th><th>24h</th><th>Total</th></tr>
              </thead>
              <tbody>
                {s.fontes.filter((f) => f.ativa).map((f) => {
                  const c = f.ultima_coleta;
                  const x = situacao(c?.situacao);
                  return (
                    <tr key={f.id}>
                      <td><a href={f.url} target="_blank" rel="noreferrer">{f.nome}</a></td>
                      <td>{tipoFonte(f.tipo)}</td>
                      <td>{f.pais_nome ?? f.pais ?? "Internacional"}</td>
                      <td>{dataHora(c?.em)}</td>
                      <td><span className={`ponto ${x.classe}`} aria-hidden /> {x.texto}{c?.erro && <div className="erro">{c.erro}</div>}</td>
                      <td>{c ? numero(c.itens_novos) : "—"}</td>
                      <td>{f.tipo === "dados" ? "—" : numero(f.documentos_24h)}</td>
                      <td>{f.tipo === "dados" ? `${numero(f.observacoes ?? 0)} cotações` : numero(f.documentos)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {s.fontes.some((f) => f.ativa && f.controle) && (<>
          <h3>Quem controla cada fonte</h3>
          <p className="discreto">
            Duas notícias só se confirmam se vierem de donos diferentes: dois veículos do mesmo Estado ou do mesmo grupo
            contam como uma voz só. Público = dinheiro do Estado, com independência editorial escrita em lei ou carta;
            estatal = dirigido pelo governo ou partido.
          </p>
          <div className="tabela-rolagem">
            <table>
              <thead><tr><th>Fonte</th><th>Controle</th><th>Quem controla</th><th>Onde está escrito</th></tr></thead>
              <tbody>
                {s.fontes.filter((f) => f.ativa).map((f) => (
                  <tr key={f.id}>
                    <td>{f.nome}</td>
                    <td>{controleFonte(f.controle)}</td>
                    <td>{f.controlador_nome ?? "—"}</td>
                    <td>{(f.controlador_fontes ?? []).map((u, i) => (
                      <span key={u}>{i > 0 && " · "}<a href={u} target="_blank" rel="noreferrer">{new URL(u).hostname.replace(/^www\./, "")}</a></span>
                    ))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>)}
        {criterios.length > 0 && (<>
          <h3>Por que cada fonte está na lista</h3>
          <ul className="regras">
            {criterios.map(([criterio, nomes]) => <li key={criterio}>{criterio} <span className="discreto">({nomes.join(", ")})</span></li>)}
          </ul>
        </>)}
      </section>

      <section id="documentos">
        <h2>{s.ultimos_documentos.length > 1 ? `As ${s.ultimos_documentos.length} notícias mais recentes` : "Notícias mais recentes"}</h2>
        <p className="discreto">Ainda soltas: a organização em eventos, com grau de confirmação, começa na fase 1.</p>
        {s.ultimos_documentos.length === 0 ? <p className="sem-dado-texto">{semBanco ? SEM_BANCO : "Nenhum documento ainda."}</p> : (
          <ul className="documentos">
            {s.ultimos_documentos.map((d, i) => (
              <li key={i}>
                <Titulo {...d} />
                <div className="discreto">
                  {d.fonte_nome} · {d.publicado_em ? `publicado ${dataHora(d.publicado_em)}` : "sem data da fonte"} · coletado {dataHora(d.conhecido_em)}
                  {d.paises && d.paises.length > 0 && <> · cita {d.paises.map((p) => p.nome).join(", ")}</>}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Palavras desta tela</h2>
        <dl className="resumo">
          <dt>História</dt><dd>Notícias sobre o mesmo assunto, juntas por regra. Não quer dizer que todas contam o mesmo fato.</dd>
          <dt>Voz independente</dt><dd>Um dono diferente (Estado, grupo de mídia ou organização). Mais vozes é mais
            cobertura, não prova.</dd>
          <dt>Fonte oficial</dt><dd>Governo ou organismo internacional falando do próprio ato (sanção, nota, decisão).</dd>
          <dt>Citação</dt><dd>Uma notícia que traz o nome, o gentílico, a capital ou a sigla de um país no título ou no resumo.</dd>
          <dt>Publicado e coletado</dt><dd>Quando a fonte publicou e quando o Stratum Global soube. As duas datas aparecem
            sempre.</dd>
          <dt>Sem dado (cinza)</dt><dd>Não foi medido nesta atualização. É diferente de zero.</dd>
          <dt>Tradução automática</dt><dd>Título traduzido por programa; o original vale mais.</dd>
          <dt>Percentil</dt><dd>A posição de um número entre os do próprio passado, de 0 a 100.</dd>
          <dt>Fora do normal</dt><dd>Variação entre as 5% maiores ou as 5% menores dos 5 anos anteriores daquela série.</dd>
        </dl>
      </section>

      <section>
        <h2>O que ainda não é medido</h2>
        <ul className="regras">
          <li>Grau de confirmação de cada fato (pista, relatado, corroborado, oficial, contestado) e importância: próxima
            etapa da fase 1, depois das histórias.</li>
          <li>Redes sociais (X e outras): ainda não são lidas. Quando entrarem, serão pista, nunca fato.</li>
          <li>Mercados: as moedas já entram (régua acima). Juros, bolsas por país, commodities e cripto, e a tela Mercados
            com os eventos do mesmo período (coincidência no tempo, não causa), vêm nas próximas etapas da fase 2.</li>
          <li>Comércio, navios nos estreitos, sanções e conflito como séries: fase 4.</li>
          <li>Cadeias, exposição e hipóteses: fase 5.</li>
        </ul>
      </section>

      <p className="discreto rodape">
        Status gerado em {dataHora(s.gerado_em)}. Fronteiras: <a href="https://www.naturalearthdata.com/" target="_blank" rel="noreferrer">Natural Earth</a> (domínio
        público). Termos e nomes de países: derivados de{" "}
        <a href="https://github.com/mledoze/countries" target="_blank" rel="noreferrer">mledoze/countries</a>, sob a licença{" "}
        <a href="https://opendatacommons.org/licenses/odbl/1.0/" target="_blank" rel="noreferrer">ODbL 1.0</a>; o arquivo derivado
        (jobs/stratum/dados/nomes_paises.json) fica sob a mesma licença.
        Informação de contexto; não é recomendação de investimento.
      </p>
    </main>
  </>);
}
