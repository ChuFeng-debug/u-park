import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { ROLE_LABEL } from "../utils/format";

/**
 * Ossature commune à toutes les pages : en-tête, zone de contenu, pied de page.
 *
 * Monté comme route parente dans App.tsx, il reste affiché pendant que
 * l'<Outlet /> change de page. L'en-tête n'est donc jamais redessiné d'une
 * navigation à l'autre.
 */
export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  // Le menu s'adapte au profil : un visiteur n'a aucune raison de voir
  // l'entrée « Administration », et inversement.
  const roles = user?.roles ?? [];
  const isAdmin = roles.includes("administrateur");
  const isVisitor = roles.includes("visiteur");

  // Après déconnexion, on quitte la page courante : elle est peut-être
  // protégée, et y rester afficherait une redirection vers /login.
  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="layout">
      <header className="layout__header">
        <Link to="/" className="layout__brand">
          <span className="layout__brand-mark" aria-hidden="true">
            P
          </span>
          U-Park
        </Link>
        {/* NavLink (et non Link) ajoute seul la classe « active » sur l'entrée
            correspondant à l'URL courante. `end` limite la correspondance au
            chemin exact : sans lui, « / » serait actif sur toutes les pages,
            puisque toutes les URL commencent par « / ». */}
        <nav className="layout__nav" aria-label="Navigation principale">
          <NavLink to="/" end>
            Catalogue
          </NavLink>
          {user && <NavLink to="/reservations">Mes réservations</NavLink>}
          {isVisitor && <NavLink to="/demandes">Mes demandes</NavLink>}
          {user && <NavLink to="/incidents">Incidents</NavLink>}
          {isAdmin && <NavLink to="/admin">Administration</NavLink>}
        </nav>
        <div className="layout__auth">
          {user ? (
            <>
              <Link to="/compte" className="layout__user" title="Mon compte">
                {user.prenom_utilisateur}
                <span className="layout__role">
                  {roles.map((role) => ROLE_LABEL[role] ?? role).join(", ")}
                </span>
              </Link>
              <button type="button" className="header-button" onClick={handleLogout}>
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
      <footer className="layout__footer">
        <div className="layout__footer-inner">
          <p className="layout__footer-copy">© 2026 Université Gustave Eiffel</p>
          <Link to="/confidentialite" className="layout__footer-link">
            Données personnelles
          </Link>
        </div>
      </footer>
    </div>
  );
}
