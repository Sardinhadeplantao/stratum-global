import type { ReactNode } from "react";
import Link from "next/link";
import Relogio from "@/components/Relogio";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";

export const metadata = {
  title: "Stratum Global",
  description: "Geopolítica e mercados globais: o que está acontecendo no mundo, com fonte, e o que se mede a respeito.",
  robots: { index: false, follow: false }, // uso pessoal por enquanto
};

function Marca() {
  return (
    <svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true" className="marca-icone">
      <circle cx="16" cy="16" r="13" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <ellipse cx="16" cy="16" rx="6" ry="13" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M3.5 12h25M3.5 20h25" stroke="currentColor" strokeWidth="1.2" fill="none" />
    </svg>
  );
}

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <header className="topo">
          <Link href="/" className="marca"><Marca /><span>Stratum Global</span></Link>
          <nav className="topo-nav" aria-label="Seções">
            <Link href="/">Mapa</Link>
            <Link href="/historias/">Histórias</Link>
            <Link href="/metodo/">Método</Link>
          </nav>
          <Relogio />
        </header>
        {children}
      </body>
    </html>
  );
}
