import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <header className="layout__header">
        <Link to="/" className="layout__brand">
          <span className="layout__brand-mark">P</span>
          U-Park
        </Link>
        <nav className="layout__nav">
          <NavLink to="/">Catalogue</NavLink>
          {user && <NavLink to="/reservations">Mes réservations</NavLink>}
        </nav>
        <div className="layout__auth">
          {user ? (
            <>
              <span>
                {user.prenom_utilisateur} ({user.roles.join(", ")})
              </span>
              <button type="button" className="header-button" onClick={logout}>
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="header-button">
                Connexion
              </Link>
              <Link to="/register" className="header-button header-button--accent">
                Inscription
              </Link>
            </>
          )}
        </div>
      </header>
      <main className="layout__content">
        <Outlet />
      </main>
    </div>
  );
}
