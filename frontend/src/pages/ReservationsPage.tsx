import { useState } from "react";
import { Link } from "react-router-dom";
import { cancelReservation, enregistrerPassage, listMyReservations } from "../api/reservations";
import { extractErrorMessage } from "../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../components/Feedback";
import { useApi } from "../hooks/useApi";
import { useZonesIndex } from "../hooks/useZonesIndex";
import type { ReservationDetailOut } from "../types/api";
import { formatDateTime, formatRange, STATUT_RESERVATION_LABEL } from "../utils/format";

// Doit rester aligné sur PASSAGE_AVANCE_MINUTES côté API.
const PASSAGE_AVANCE_MS = 15 * 60 * 1000;

function passagePossible(reservation: ReservationDetailOut): boolean {
  const now = Date.now();
  return (
    reservation.statut_reservation === "confirmee" &&
    reservation.date_passage === null &&
    now >= new Date(reservation.date_debut).getTime() - PASSAGE_AVANCE_MS &&
    now < new Date(reservation.date_fin).getTime()
  );
}

function isUpcoming(reservation: ReservationDetailOut): boolean {
  return new Date(reservation.date_fin).getTime() > Date.now();
}

export default function ReservationsPage() {
  const reservations = useApi(listMyReservations, "Impossible de charger vos réservations");
  const index = useZonesIndex();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(action: () => Promise<unknown>, success: string) {
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(success);
      await reservations.reload();
    } catch (err) {
      setError(extractErrorMessage(err, "Action impossible"));
    }
  }

  const list = reservations.data ?? [];
  const aVenir = list.filter(isUpcoming).reverse();
  const passees = list.filter((r) => !isUpcoming(r));

  function renderRow(r: ReservationDetailOut) {
    return (
      <tr key={r.id_reservation}>
        <td>{formatRange(r.date_debut, r.date_fin)}</td>
        <td>
          <strong>{r.numero_place}</strong>
          <span className="muted"> · {index.label(r.id_zone)}</span>
        </td>
        <td>
          <span className={`status-chip status-chip--${r.statut_reservation}`}>
            {STATUT_RESERVATION_LABEL[r.statut_reservation] ?? r.statut_reservation}
          </span>
          {r.date_passage && (
            <span className="muted"> · entré à {formatDateTime(r.date_passage).slice(-5)}</span>
          )}
          {r.motif_annulation && <span className="muted"> · {r.motif_annulation}</span>}
        </td>
        <td className="cell-actions">
          {passagePossible(r) && (
            <button
              type="button"
              onClick={() => run(() => enregistrerPassage(r.id_reservation), "Passage enregistré, bon stationnement !")}
            >
              Simuler mon passage
            </button>
          )}
          {r.statut_reservation === "confirmee" && !r.date_passage && isUpcoming(r) && (
            <button
              type="button"
              className="link-button link-button--danger"
              onClick={() => {
                if (window.confirm(`Annuler la réservation de la place ${r.numero_place} ?`)) {
                  void run(() => cancelReservation(r.id_reservation), "Réservation annulée.");
                }
              }}
            >
              Annuler
            </button>
          )}
        </td>
      </tr>
    );
  }

  function renderTable(rows: ReservationDetailOut[], caption: string) {
    return (
      <div className="table-wrap">
        <table>
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              <th scope="col">Créneau</th>
              <th scope="col">Place</th>
              <th scope="col">Statut</th>
              <th scope="col">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>{rows.map(renderRow)}</tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="reservations">
      <h1>Mes réservations</h1>
      <SuccessMessage message={message} />
      <ErrorMessage message={error ?? reservations.error} onRetry={reservations.reload} />
      {reservations.loading && !reservations.data && <Loading />}
      {reservations.data && list.length === 0 && (
        <p>
          Aucune réservation pour le moment. <Link to="/">Trouver une place</Link>
        </p>
      )}
      {aVenir.length > 0 && (
        <section>
          <h2>À venir</h2>
          {renderTable(aVenir, "Réservations à venir")}
        </section>
      )}
      {passees.length > 0 && (
        <section>
          <h2>Historique</h2>
          {renderTable(passees, "Réservations passées")}
        </section>
      )}
    </div>
  );
}
