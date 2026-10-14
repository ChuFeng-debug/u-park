import { useCallback, useState } from "react";
import { listTraces } from "../../api/admin";
import { ErrorMessage, Loading } from "../../components/Feedback";
import { useApi } from "../../hooks/useApi";
import { formatDateTime } from "../../utils/format";

const FAMILLES: Record<string, string> = {
  "": "Toutes les actions",
  "connexion.": "Connexions",
  "compte.": "Comptes",
  "reservation.": "Réservations",
  "blocage.": "Blocages",
  "zone.": "Zones",
  "regle.": "Règles d'accès",
  "demande.": "Demandes visiteurs",
  "incident.": "Incidents",
  "utilisateur.": "Administration des comptes",
  "rgpd.": "RGPD",
};

export default function JournalPage() {
  const [famille, setFamille] = useState("");
  const [idUtilisateur, setIdUtilisateur] = useState("");
  const loader = useCallback(
    () =>
      listTraces({
        type_action: famille || undefined,
        id_utilisateur: idUtilisateur ? Number(idUtilisateur) : undefined,
      }),
    [famille, idUtilisateur],
  );
  const traces = useApi(loader, "Impossible de charger le journal");

  return (
    <div>
      <h1>Journal des actions</h1>
      <p className="muted">
        Actions importantes, sans donnée personnelle : seuls les identifiants techniques sont
        enregistrés.
      </p>
      <div className="filters">
        <label>
          Type
          <select value={famille} onChange={(e) => setFamille(e.target.value)}>
            {Object.entries(FAMILLES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          N° utilisateur
          <input
            type="number"
            min={1}
            value={idUtilisateur}
            onChange={(e) => setIdUtilisateur(e.target.value)}
          />
        </label>
      </div>
      <ErrorMessage message={traces.error} onRetry={traces.reload} />
      {traces.loading && !traces.data && <Loading />}
      {traces.data && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Utilisateur</th>
                <th scope="col">Action</th>
                <th scope="col">Cible</th>
                <th scope="col">Détail</th>
              </tr>
            </thead>
            <tbody>
              {traces.data.map((t) => (
                <tr key={t.id_trace}>
                  <td>{formatDateTime(t.horodatage)}</td>
                  <td>#{t.id_utilisateur}</td>
                  <td>
                    <code>{t.type_action}</code>
                  </td>
                  <td>
                    {t.entite_cible} #{t.identifiant_cible}
                  </td>
                  <td className="muted">{t.detail_action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
