import { Link, NavLink, useNavigate } from "react-router-dom";
import type { PropsWithChildren } from "react";
import { useUser } from "@/context/UserContext";

export function AppShell({ children }: PropsWithChildren) {
  const navigate = useNavigate();
  const { currentUser, setCurrentUser } = useUser();

  const handleLogout = () => {
    setCurrentUser(null);
    void navigate("/", { replace: true });
  };

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
        <div className="user-actions">
          <div className="user-pill">
            {currentUser ? `${currentUser.username} · ${currentUser.role}` : "No user selected"}
          </div>
          {currentUser ? (
            <button type="button" className="button button--ghost" onClick={handleLogout}>
              Cerrar sesion
            </button>
          ) : null}
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
