import { NavLink, Outlet } from "react-router-dom";

const TABS = [
  { to: "/admin", label: "Tableau de bord", end: true },
  { to: "/admin/zones", label: "Zones et blocages" },
  { to: "/admin/regles", label: "Règles d'accès" },
  { to: "/admin/demandes", label: "Demandes visiteurs" },
  { to: "/admin/incidents", label: "Incidents" },
  { to: "/admin/reservations", label: "Réservations" },
  { to: "/admin/utilisateurs", label: "Utilisateurs" },
  { to: "/admin/journal", label: "Journal" },
];

export default function AdminLayout() {
  return (
    <div className="admin">
      <nav className="admin__tabs" aria-label="Administration">
        {TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.end}>
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
