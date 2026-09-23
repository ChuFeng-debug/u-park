import { useEffect, useState } from "react";
import { cancelReservation, listMyReservations } from "../api/reservations";
import { extractErrorMessage } from "../api/http";
import type { ReservationOut } from "../types/api";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR");
}

const STATUT_LABEL: Record<string, string> = {
  confirmee: "confirmée",
  annulee: "annulée",
  no_show: "no-show",
};

export default function ReservationsPage() {
  const [reservations, setReservations] = useState<ReservationOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setReservations(await listMyReservations());
    setLoading(false);
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleCancel(id: number) {
    setError(null);
    try {
      await cancelReservation(id);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "Annulation impossible"));
    }
  }

  if (loading) return <p>Chargement…</p>;

  return (
    <div className="reservations">
      <h1>Mes réservations</h1>
      {error && <p className="form-error">{error}</p>}
      {reservations.length === 0 && <p>Aucune réservation pour le moment.</p>}
      <table>
        <thead>
          <tr>
            <th>Place</th>
            <th>Début</th>
            <th>Fin</th>
            <th>Statut</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {reservations.map((reservation) => (
            <tr key={reservation.id_reservation}>
              <td>#{reservation.id_place}</td>
              <td>{formatDate(reservation.date_debut)}</td>
              <td>{formatDate(reservation.date_fin)}</td>
              <td>
                <span className={`status-chip status-chip--${reservation.statut_reservation}`}>
                  {STATUT_LABEL[reservation.statut_reservation] ?? reservation.statut_reservation}
                </span>
              </td>
              <td>
                {reservation.statut_reservation === "confirmee" && (
                  <button type="button" onClick={() => handleCancel(reservation.id_reservation)}>
                    Annuler
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
