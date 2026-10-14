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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
