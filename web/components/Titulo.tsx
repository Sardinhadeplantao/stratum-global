/** Título de notícia: em português quando houve tradução automática (decisão 0010), com o original ao passar o mouse.
 * O link leva sempre à notícia original, na fonte. */
type Props = { titulo: string; titulo_original?: string | null; url?: string | null; className?: string };

export default function Titulo({ titulo, titulo_original, url, className }: Props) {
  const dica = titulo_original ? `Original: ${titulo_original}` : undefined;
  return (<>
    {url ? <a href={url} target="_blank" rel="noreferrer" className={className} title={dica}>{titulo}</a>
      : <span className={className} title={dica}>{titulo}</span>}
    {titulo_original && <span className="traduzido" title={dica}> (tradução automática)</span>}
  </>);
}
