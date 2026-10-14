import { useState } from "react";
import type { FormEvent } from "react";
import { listMesIncidents, signalerIncident } from "../api/compte";
import { extractErrorMessage } from "../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../components/Feedback";
import { useApi } from "../hooks/useApi";
import { useZonesIndex } from "../hooks/useZonesIndex";
import type { PrioriteIncident } from "../types/api";
import { formatDateTime, PRIORITE_LABEL, STATUT_INCIDENT_LABEL } from "../utils/format";

export default function IncidentsPage() {
  const index = useZonesIndex();
  const incidents = useApi(listMesIncidents, "Impossible de charger vos signalements");
  const [form, setForm] = useState({ id_zone: 0, description: "", priorite: "moyenne" as PrioriteIncident });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await signalerIncident({
        id_zone: form.id_zone,
        description_incident: form.description,
        priorite_incident: form.priorite,
      });
      setForm({ ...form, description: "" });
      setMessage("Incident signalé, merci. L'équipe parking va le traiter.");
      await incidents.reload();
    } catch (err) {
      setError(extractErrorMessage(err, "Signalement impossible"));
    }
  }

  return (
    <div>
      <h1>Signaler un incident</h1>
      <form className="panel inline-form" onSubmit={handleSubmit}>
        <label>
          Zone
          <select
            required
            value={form.id_zone || ""}
            onChange={(e) => setForm({ ...form, id_zone: Number(e.target.value) })}
          >
            <option value="">Choisir…</option>
            {index.zones.map((z) => (
              <option key={z.id_zone} value={z.id_zone}>
                {index.label(z.id_zone)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Urgence
          <select
            value={form.priorite}
            onChange={(e) => setForm({ ...form, priorite: e.target.value as PrioriteIncident })}
          >
            {Object.entries(PRIORITE_LABEL).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="inline-form__wide">
          Description
          <textarea
            required
            minLength={5}
            maxLength={500}
            rows={3}
            placeholder="Barrière bloquée, éclairage en panne, véhicule mal garé…"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </label>
        <button type="submit">Signaler</button>
      </form>
      <SuccessMessage message={message} />
      <ErrorMessage message={error ?? incidents.error} onRetry={incidents.reload} />

      <h2>Mes signalements</h2>
      {incidents.loading && !incidents.data && <Loading />}
      {incidents.data && incidents.data.length === 0 && <p className="muted">Aucun signalement.</p>}
      <ul className="card-list">
        {incidents.data?.map((i) => (
          <li key={i.id_incident} className="card">
            <div className="card__header">
              <strong>{index.label(i.id_zone)}</strong>
              <span className={`status-chip status-chip--incident-${i.statut_incident}`}>
                {STATUT_INCIDENT_LABEL[i.statut_incident]}
              </span>
            </div>
            <p>{i.description_incident}</p>
            <p className="muted">Signalé le {formatDateTime(i.date_signalement)}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
