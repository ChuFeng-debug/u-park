import { useCallback, useState } from "react";
import { listDemandes, refuserDemande, validerDemande } from "../../api/admin";
import { listPlaces } from "../../api/catalogue";
import { extractErrorMessage } from "../../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../../components/Feedback";
import { useApi } from "../../hooks/useApi";
import { useZonesIndex } from "../../hooks/useZonesIndex";
import type { DemandeVisiteurAdminOut, PlaceWithDisponibilite, StatutDemande } from "../../types/api";
import { formatDateTime, formatRange, STATUT_DEMANDE_LABEL } from "../../utils/format";

function DemandeCard({
  demande,
  onDone,
}: {
  demande: DemandeVisiteurAdminOut;
  onDone: (message: string) => void;
}) {
  const index = useZonesIndex();
  const [mode, setMode] = useState<"idle" | "choisir" | "refuser">("idle");
  const [idZone, setIdZone] = useState<number | null>(null);
  const [places, setPlaces] = useState<PlaceWithDisponibilite[]>([]);
  const [idPlace, setIdPlace] = useState<number | null>(null);
  const [commentaire, setCommentaire] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Zones où un visiteur peut se garer : ouvertes à tous ou réservées aux visiteurs.
  const zonesVisiteur = index.zones.filter(
    (z) => z.zone_active && (z.roles_autorises === null || z.roles_autorises.includes("visiteur")),
  );

  async function chooseZone(id: number) {
    setIdZone(id);
    setIdPlace(null);
    const all = await listPlaces(id, {
      debut: demande.date_visite_souhaitee,
      fin: demande.date_fin_visite_souhaitee,
    });
    setPlaces(all.filter((p) => p.disponible && p.type_place !== "pmr"));
  }

  async function run(action: () => Promise<unknown>, message: string) {
    setError(null);
    setSubmitting(true);
    try {
      await action();
      onDone(message);
    } catch (err) {
      setError(extractErrorMessage(err, "Action impossible"));
    } finally {
      setSubmitting(false);
    }
  }

  const enAttente = demande.statut_demande === "en_attente";
  const debut = demande.date_visite_souhaitee;
  const fin = demande.date_fin_visite_souhaitee;

  return (
    <li className="card">
      <div className="card__header">
        <strong>
          {demande.prenom_demandeur} {demande.nom_demandeur}
        </strong>
        <span className={`status-chip status-chip--${demande.statut_demande}`}>
          {STATUT_DEMANDE_LABEL[demande.statut_demande]}
        </span>
      </div>
      <p>{formatRange(debut, fin)}</p>
      <p className="muted">« {demande.motif_demande} » · déposée le {formatDateTime(demande.date_demande)}</p>
      {demande.commentaire_traitement && <p className="muted">Réponse : {demande.commentaire_traitement}</p>}

      {enAttente && mode === "idle" && (
        <div className="card__actions">
          <button
            type="button"
            disabled={submitting}
            onClick={() => run(() => validerDemande(demande.id_demande, {}), "Demande validée : place attribuée automatiquement.")}
          >
            Valider (place automatique)
          </button>
          <button type="button" className="button--secondary" onClick={() => setMode("choisir")}>
            Choisir la place
          </button>
          <button type="button" className="link-button link-button--danger" onClick={() => setMode("refuser")}>
            Refuser
          </button>
        </div>
      )}

      {enAttente && mode === "choisir" && (
        <div className="inline-form">
          <label>
            Zone
            <select value={idZone ?? ""} onChange={(e) => void chooseZone(Number(e.target.value))}>
              <option value="">Choisir…</option>
              {zonesVisiteur.map((z) => (
                <option key={z.id_zone} value={z.id_zone}>
                  {index.label(z.id_zone)}
                </option>
              ))}
            </select>
          </label>
          {idZone !== null && (
            <label>
              Place libre sur le créneau
              <select value={idPlace ?? ""} onChange={(e) => setIdPlace(Number(e.target.value))}>
                <option value="">{places.length ? "Choisir…" : "Aucune place libre"}</option>
                {places.map((p) => (
                  <option key={p.id_place} value={p.id_place}>
                    {p.numero_place}
                  </option>
                ))}
              </select>
            </label>
          )}
          <button
            type="button"
            disabled={idPlace === null || submitting}
            onClick={() =>
              run(
                () => validerDemande(demande.id_demande, { id_place: idPlace ?? undefined }),
                "Demande validée.",
              )
            }
          >
            Valider
          </button>
          <button type="button" className="link-button" onClick={() => setMode("idle")}>
            Annuler
          </button>
        </div>
      )}

      {enAttente && mode === "refuser" && (
        <form
          className="inline-form"
          onSubmit={(e) => {
            e.preventDefault();
            void run(() => refuserDemande(demande.id_demande, commentaire), "Demande refusée.");
          }}
        >
          <label>
            Motif du refus (communiqué au visiteur)
            <input required minLength={3} value={commentaire} onChange={(e) => setCommentaire(e.target.value)} />
          </label>
          <button type="submit" className="button--danger" disabled={submitting}>
            Refuser
          </button>
          <button type="button" className="link-button" onClick={() => setMode("idle")}>
            Annuler
          </button>
        </form>
      )}
      <ErrorMessage message={error} />
    </li>
  );
}

export default function DemandesPage() {
  const [statut, setStatut] = useState<StatutDemande | "">("en_attente");
  const [message, setMessage] = useState<string | null>(null);
  const loader = useCallback(() => listDemandes(statut || undefined), [statut]);
  const demandes = useApi(loader, "Impossible de charger les demandes");

  return (
    <div>
      <h1>Demandes visiteurs</h1>
      <div className="filters">
        <label>
          Statut
          <select value={statut} onChange={(e) => setStatut(e.target.value as StatutDemande | "")}>
            <option value="en_attente">En attente</option>
            <option value="validee">Validées</option>
            <option value="refusee">Refusées</option>
            <option value="">Toutes</option>
          </select>
        </label>
      </div>
      <SuccessMessage message={message} />
      <ErrorMessage message={demandes.error} onRetry={demandes.reload} />
      {demandes.loading && !demandes.data && <Loading />}
      {demandes.data && demandes.data.length === 0 && <p className="muted">Aucune demande.</p>}
      <ul className="card-list">
        {demandes.data?.map((demande) => (
          <DemandeCard
            key={`${demande.id_demande}-${demande.statut_demande}`}
            demande={demande}
            onDone={(msg) => {
              setMessage(msg);
              void demandes.reload();
            }}
          />
        ))}
      </ul>
    </div>
  );
}
