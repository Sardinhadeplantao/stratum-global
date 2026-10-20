import Link from "next/link";
import Camadas from "./Camadas";

const SECOES: { nome: string; href?: string; fase?: string }[] = [
  { nome: "Mapa global", href: "/" },
  { nome: "Histórias", href: "/historias/" },
  { nome: "Mercados", fase: "fase 2" },
  { nome: "Calendário geopolítico", fase: "fase 4" },
  { nome: "Cadeias industriais", fase: "fase 5" },
  { nome: "Hipóteses e placar", fase: "fase 5" },
  { nome: "Método e fontes", href: "/metodo/" },
];

export default function Lateral({ atual }: { atual: string }) {
  return (
    <aside className="lateral" aria-label="Navegação">
      <nav>
        <ul className="secoes">
          {SECOES.map((s) => (
            <li key={s.nome} className={s.href === atual ? "atual" : s.href ? "" : "futura"}>
              {s.href ? <Link href={s.href}>{s.nome}</Link> : <span>{s.nome}</span>}
              {s.fase && <span className="fase">{s.fase}</span>}
            </li>
          ))}
        </ul>
      </nav>
      <h2 className="rotulo">Camadas do mapa</h2>
      <Camadas />
      <Link href="/metodo/" className="cartao-entenda">
        <strong>Entenda de onde vem cada número.</strong>
        <span>Fontes, regras e o que ainda não é medido.</span>
      </Link>
    </aside>
  );
}
