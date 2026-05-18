import { Link, NavLink } from "react-router-dom";
import type { PropsWithChildren } from "react";
import { useUser } from "@/context/UserContext";

export function AppShell({ children }: PropsWithChildren) {
  const { currentUser } = useUser();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <Link to="/" className="brand-link">
            Pepe Grillo
          </Link>
          <span className="brand-caption">Registro y chat asistido</span>
        </div>
        <nav className="nav-actions" aria-label="Main navigation">
          <NavLink to="/" className="pill-link">
            Registrar
          </NavLink>
          <NavLink to="/chat" className="pill-link pill-link--solid">
            Chat
          </NavLink>
        </nav>
        <div className="user-pill">
          {currentUser ? `${currentUser.username} · ${currentUser.role}` : "No user selected"}
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
