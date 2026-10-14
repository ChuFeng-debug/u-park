import { useCallback, useState } from "react";
import { annulerReservationAdmin, listReservationsAdmin, marquerNoShows } from "../../api/admin";
import { extractErrorMessage } from "../../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../../components/Feedback";
import { useApi } from "../../hooks/useApi";
import { useZonesIndex } from "../../hooks/useZonesIndex";
import { formatRange, STATUT_RESERVATION_LABEL, toDateInput } from "../../utils/format";

export default function ReservationsAdminPage() {
  const index = useZonesIndex();
  const [filters, setFilters] = useState({
    id_zone: "",
    statut: "confirmee",
    jour: toDateInput(new Date()),
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loader = useCallback(() => {
    const debut = filters.jour ? new Date(`${filters.jour}T00:00`) : null;
    const fin = debut ? new Date(debut.getTime() + 24 * 60 * 60 * 1000) : null;
    return listReservationsAdmin({
      id_zone: filters.id_zone ? Number(filters.id_zone) : undefined,
      statut: filters.statut || undefined,
      du: debut?.toISOString(),
      au: fin?.toISOString(),
      limit: 300,
    });
  }, [filters]);
  const reservations = useApi(loader, "Impossible de charger les réservations");

  async function cancel(idReservation: number) {
    const motif = window.prompt("Motif de l'annulation (communiqué à l'utilisateur) :");
    if (!motif) return;
    setError(null);
    try {
      await annulerReservationAdmin(idReservation, motif);
      setMessage("Réservation annulée.");
      await reservations.reload();
    } catch (err) {
      setError(extractErrorMessage(err, "Annulation impossible"));
    }
  }

  async function noShows() {
    setError(null);
    try {
      const count = await marquerNoShows();
      setMessage(`${count} réservation(s) passée(s) en no-show.`);
      await reservations.reload();
    } catch (err) {
      setError(extractErrorMessage(err, "Action impossible"));
    }
  }

  return (
    <div>
      <h1>Réservations</h1>
      <div className="filters">
        <label>
          Jour
          <input
            type="date"
            value={filters.jour}
            onChange={(e) => setFilters({ ...filters, jour: e.target.value })}
          />
        </label>
        <label>
          Zone
          <select
            value={filters.id_zone}
            onChange={(e) => setFilters({ ...filters, id_zone: e.target.value })}
          >
            <option value="">Toutes les zones</option>
            {index.zones.map((z) => (
              <option key={z.id_zone} value={z.id_zone}>
                {index.label(z.id_zone)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Statut
          <select
            value={filters.statut}
            onChange={(e) => setFilters({ ...filters, statut: e.target.value })}
          >
            <option value="">Tous</option>
            {Object.entries(STATUT_RESERVATION_LABEL).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="button--secondary" onClick={noShows}>
          Détecter les no-shows
        </button>
      </div>
      <SuccessMessage message={message} />
      <ErrorMessage message={error ?? reservations.error} onRetry={reservations.reload} />
      {reservations.loading && !reservations.data && <Loading />}
      {reservations.data && (
        <>
          <p className="muted">
            {reservations.data.length} réservation(s){reservations.data.length === 300 && " (300 premières)"}
          </p>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Créneau</th>
                  <th scope="col">Place</th>
                  <th scope="col">Utilisateur</th>
                  <th scope="col">Statut</th>
                  <th scope="col">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {reservations.data.map((r) => (
                  <tr key={r.id_reservation}>
                    <td>{formatRange(r.date_debut, r.date_fin)}</td>
                    <td>
                      {r.numero_place}
                      <span className="muted"> · {index.label(r.id_zone)}</span>
                    </td>
                    <td>
                      {r.prenom_utilisateur} {r.nom_utilisateur}
                    </td>
                    <td>
                      <span className={`status-chip status-chip--${r.statut_reservation}`}>
                        {STATUT_RESERVATION_LABEL[r.statut_reservation]}
                      </span>
                      {r.date_passage && <span className="muted"> · entré</span>}
                    </td>
                    <td>
                      {r.statut_reservation === "confirmee" && !r.date_passage && (
                        <button type="button" className="link-button" onClick={() => cancel(r.id_reservation)}>
                          Annuler
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
