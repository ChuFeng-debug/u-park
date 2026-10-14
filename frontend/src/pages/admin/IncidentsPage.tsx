import { useCallback, useState } from "react";
import { listIncidents, updateIncident } from "../../api/admin";
import { extractErrorMessage } from "../../api/http";
import { ErrorMessage, Loading } from "../../components/Feedback";
import { useApi } from "../../hooks/useApi";
import { useZonesIndex } from "../../hooks/useZonesIndex";
import type { PrioriteIncident, StatutIncident } from "../../types/api";
import { formatDateTime, PRIORITE_LABEL, STATUT_INCIDENT_LABEL } from "../../utils/format";

export default function IncidentsPage() {
  const index = useZonesIndex();
  const [statut, setStatut] = useState<StatutIncident | "">("ouvert");
  const [error, setError] = useState<string | null>(null);
  const loader = useCallback(() => listIncidents({ statut: statut || undefined }), [statut]);
  const incidents = useApi(loader, "Impossible de charger les incidents");

  async function change(
    idIncident: number,
    payload: { statut_incident?: StatutIncident; priorite_incident?: PrioriteIncident },
  ) {
    setError(null);
    try {
      await updateIncident(idIncident, payload);
      await incidents.reload();
    } catch (err) {
      setError(extractErrorMessage(err, "Mise à jour impossible"));
    }
  }

  return (
    <div>
      <h1>Incidents</h1>
      <div className="filters">
        <label>
          Statut
          <select value={statut} onChange={(e) => setStatut(e.target.value as StatutIncident | "")}>
            <option value="ouvert">Ouverts</option>
            <option value="en_cours">En cours</option>
            <option value="resolu">Résolus</option>
            <option value="">Tous</option>
          </select>
        </label>
      </div>
      <ErrorMessage message={error ?? incidents.error} onRetry={incidents.reload} />
      {incidents.loading && !incidents.data && <Loading />}
      {incidents.data && incidents.data.length === 0 && <p className="muted">Aucun incident.</p>}
      <ul className="card-list">
        {incidents.data?.map((incident) => (
          <li key={incident.id_incident} className="card">
            <div className="card__header">
              <strong>{index.label(incident.id_zone)}</strong>
              <span className={`status-chip status-chip--priorite-${incident.priorite_incident}`}>
                priorité {PRIORITE_LABEL[incident.priorite_incident]}
              </span>
            </div>
            <p>{incident.description_incident}</p>
            <p className="muted">
              Signalé le {formatDateTime(incident.date_signalement)}
              {incident.date_resolution && ` · résolu le ${formatDateTime(incident.date_resolution)}`}
            </p>
            <div className="inline-form">
              <label>
                Statut
                <select
                  value={incident.statut_incident}
                  onChange={(e) =>
                    change(incident.id_incident, { statut_incident: e.target.value as StatutIncident })
                  }
                >
                  {Object.entries(STATUT_INCIDENT_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Priorité
                <select
                  value={incident.priorite_incident}
                  onChange={(e) =>
                    change(incident.id_incident, {
                      priorite_incident: e.target.value as PrioriteIncident,
                    })
                  }
                >
                  {Object.entries(PRIORITE_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
