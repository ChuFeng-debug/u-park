import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

/**
 * Garde les routes qui exigent une session ouverte.
 *
 * Le test sur `loading` est indispensable : au premier rendu, la vérification
 * du jeton auprès de l'API n'est pas terminée et `user` vaut encore null.
 * Sans lui, un utilisateur pourtant connecté serait renvoyé vers /login à
 * chaque rafraîchissement de page.
 */
export default function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) return <p>Chargement…</p>;
  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}
