import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

/**
 * Réserve un groupe de routes à certains rôles.
 *
 * Point important pour la soutenance : ce filtrage est purement ergonomique.
 * N'importe qui peut modifier l'état du navigateur pour afficher la page ; la
 * sécurité réelle tient aux dépendances FastAPI côté serveur, qui revérifient
 * le rôle à chaque requête. Ici, on évite simplement à l'utilisateur de
 * naviguer vers un écran qui ne lui renverrait que des erreurs 403.
 */
export default function RoleRoute({ roles }: { roles: string[] }) {
  const { user, loading } = useAuth();

  if (loading) return <p>Chargement…</p>;
  if (!user) return <Navigate to="/login" replace />;
  // Un utilisateur peut cumuler plusieurs rôles : il suffit qu'il en possède
  // un seul parmi ceux autorisés.
  if (!user.roles.some((role) => roles.includes(role))) {
    return (
      <div className="page-message">
        <h1>Accès refusé</h1>
        <p>Cette page est réservée aux profils : {roles.join(", ")}.</p>
      </div>
    );
  }
  return <Outlet />;
}
