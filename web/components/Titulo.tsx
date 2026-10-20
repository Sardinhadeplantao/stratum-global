import Link from "next/link";

/** Título de notícia ou história: em português quando houve tradução automática (decisão 0010), com o original ao
 * passar o mouse. `url` leva à notícia original, na fonte; `href`, a uma página do próprio Stratum. */
type Props = { titulo: string; titulo_original?: string | null; url?: string | null; href?: string; className?: string };

export default function Titulo({ titulo, titulo_original, url, href, className }: Props) {
  const dica = titulo_original ? `Original: ${titulo_original}` : undefined;
  return (<span>
    {href ? <Link href={href} className={className} title={dica}>{titulo}</Link>
      : url ? <a href={url} target="_blank" rel="noreferrer" className={className} title={dica}>{titulo}</a>
      : <span className={className} title={dica}>{titulo}</span>}
    {titulo_original && <span className="traduzido" title={dica}> (tradução automática)</span>}
  </span>);
}
