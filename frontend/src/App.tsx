import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleRoute from "./components/RoleRoute";
import CataloguePage from "./pages/CataloguePage";
import ComptePage from "./pages/ComptePage";
import ConfidentialitePage from "./pages/ConfidentialitePage";
import IncidentsPage from "./pages/IncidentsPage";
import LoginPage from "./pages/LoginPage";
import MesDemandesPage from "./pages/MesDemandesPage";
import RegisterPage from "./pages/RegisterPage";
import ReservationsPage from "./pages/ReservationsPage";
import AdminLayout from "./pages/admin/AdminLayout";
import DashboardPage from "./pages/admin/DashboardPage";
import DemandesPage from "./pages/admin/DemandesPage";
import IncidentsAdminPage from "./pages/admin/IncidentsPage";
import JournalPage from "./pages/admin/JournalPage";
import ReglesPage from "./pages/admin/ReglesPage";
import ReservationsAdminPage from "./pages/admin/ReservationsAdminPage";
import UtilisateursPage from "./pages/admin/UtilisateursPage";
import ZonesPage from "./pages/admin/ZonesPage";

/**
 * Plan de routage de l'application.
 *
 * Les routes sont imbriquées dans des « routes de garde » sans chemin propre,
 * qui ne servent qu'à filtrer l'accès et à rendre un <Outlet /> :
 *   Layout         → en-tête + pied de page communs à toutes les pages
 *   ProtectedRoute → exige un utilisateur connecté, quel que soit son rôle
 *   RoleRoute      → exige en plus un rôle précis (visiteur, administrateur)
 *
 * L'intérêt de cette imbrication est qu'une page n'a aucune vérification de
 * droits à faire elle-même : sa simple position dans l'arbre la protège.
 */
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<CataloguePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/confidentialite" element={<ConfidentialitePage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/reservations" element={<ReservationsPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/compte" element={<ComptePage />} />
        </Route>
        <Route element={<RoleRoute roles={["visiteur"]} />}>
          <Route path="/demandes" element={<MesDemandesPage />} />
        </Route>
        <Route element={<RoleRoute roles={["administrateur"]} />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="zones" element={<ZonesPage />} />
            <Route path="regles" element={<ReglesPage />} />
            <Route path="demandes" element={<DemandesPage />} />
            <Route path="incidents" element={<IncidentsAdminPage />} />
            <Route path="reservations" element={<ReservationsAdminPage />} />
            <Route path="utilisateurs" element={<UtilisateursPage />} />
            <Route path="journal" element={<JournalPage />} />
          </Route>
        </Route>
        {/* Toute URL inconnue retombe sur le catalogue. `replace` évite
            d'empiler l'URL erronée dans l'historique du navigateur. */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
