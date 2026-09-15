import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <header className="layout__header">
        <Link to="/" className="layout__brand">
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
              <button type="button" onClick={logout}>
                Déconnexion
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Connexion</Link>
              <Link to="/register">Inscription</Link>
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
