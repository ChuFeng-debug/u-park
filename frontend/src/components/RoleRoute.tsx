import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

/** Réserve un groupe de routes à certains rôles (le contrôle réel est fait par l'API). */
export default function RoleRoute({ roles }: { roles: string[] }) {
  const { user, loading } = useAuth();

  if (loading) return <p>Chargement…</p>;
  if (!user) return <Navigate to="/login" replace />;
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
