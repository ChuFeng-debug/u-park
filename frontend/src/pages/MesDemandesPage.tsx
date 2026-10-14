import { useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { createDemande, listMesDemandes } from "../api/compte";
import { extractErrorMessage } from "../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../components/Feedback";
import { useApi } from "../hooks/useApi";
import { formatDateTime, formatRange, STATUT_DEMANDE_LABEL, toDateInput } from "../utils/format";

export default function MesDemandesPage() {
  const demandes = useApi(listMesDemandes, "Impossible de charger vos demandes");
  const [form, setForm] = useState(() => ({
    jour: toDateInput(new Date(Date.now() + 24 * 60 * 60 * 1000)),
    debut: "09:00",
    fin: "12:00",
    motif: "",
  }));
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    const debut = new Date(`${form.jour}T${form.debut}`);
    const fin = new Date(`${form.jour}T${form.fin}`);
    if (fin <= debut) {
      setError("L'heure de fin doit être après l'heure de début.");
      return;
    }
    setSubmitting(true);
    try {
      await createDemande({
        date_visite_souhaitee: debut.toISOString(),
        date_fin_visite_souhaitee: fin.toISOString(),
        motif_demande: form.motif,
      });
      setForm({ ...form, motif: "" });
      setMessage("Demande envoyée. Vous serez informé ici dès qu'elle sera traitée.");
      await demandes.reload();
    } catch (err) {
      setError(extractErrorMessage(err, "Envoi impossible"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Mes demandes de place</h1>
      <p className="muted">
        En tant que visiteur, vous demandez une place pour un créneau ; l'administration valide la
        demande et vous attribue une place.
      </p>
      <form className="panel inline-form" onSubmit={handleSubmit}>
        <label>
          Jour
          <input
            type="date"
            required
            min={toDateInput(new Date())}
            value={form.jour}
            onChange={(e) => setForm({ ...form, jour: e.target.value })}
          />
        </label>
        <label>
          Arrivée
          <input type="time" required value={form.debut} onChange={(e) => setForm({ ...form, debut: e.target.value })} />
        </label>
        <label>
          Départ
          <input type="time" required value={form.fin} onChange={(e) => setForm({ ...form, fin: e.target.value })} />
        </label>
        <label className="inline-form__wide">
          Motif de la visite
          <input
            required
            minLength={3}
            maxLength={255}
            placeholder="Jury, conférence, rendez-vous…"
            value={form.motif}
            onChange={(e) => setForm({ ...form, motif: e.target.value })}
          />
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? "Envoi…" : "Envoyer la demande"}
        </button>
      </form>
      <SuccessMessage message={message} />
      <ErrorMessage message={error ?? demandes.error} onRetry={demandes.reload} />
      {demandes.loading && !demandes.data && <Loading />}
      {demandes.data && demandes.data.length === 0 && <p className="muted">Aucune demande pour le moment.</p>}
      <ul className="card-list">
        {demandes.data?.map((d) => (
          <li key={d.id_demande} className="card">
            <div className="card__header">
              <strong>{formatRange(d.date_visite_souhaitee, d.date_fin_visite_souhaitee)}</strong>
              <span className={`status-chip status-chip--${d.statut_demande}`}>
                {STATUT_DEMANDE_LABEL[d.statut_demande]}
              </span>
            </div>
            <p className="muted">
              « {d.motif_demande} » · envoyée le {formatDateTime(d.date_demande)}
            </p>
            {d.statut_demande === "validee" && (
              <p>
                Place attribuée : voir <Link to="/reservations">Mes réservations</Link>.
              </p>
            )}
            {d.commentaire_traitement && <p>Réponse : {d.commentaire_traitement}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
