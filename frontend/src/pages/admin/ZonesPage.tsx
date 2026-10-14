import { useCallback, useState } from "react";
import type { FormEvent } from "react";
import {
  createBlocage,
  createParking,
  createPlace,
  createZone,
  deleteBlocage,
  listBlocages,
  updatePlace,
  updateZone,
} from "../../api/admin";
import { listPlaces } from "../../api/catalogue";
import { extractErrorMessage } from "../../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../../components/Feedback";
import { useApi } from "../../hooks/useApi";
import { useZonesIndex } from "../../hooks/useZonesIndex";
import type { ZoneWithDisponibilite } from "../../types/api";
import { formatRange, localInputToIso, toDatetimeLocal } from "../../utils/format";

const TYPES_PLACE = ["standard", "pmr", "electrique", "moto"];
const ETATS_PLACE: Record<string, string> = {
  libre: "en service",
  occupee: "occupée (simulé)",
  hors_service: "hors service",
};

function BlocageForm({ zone, onDone }: { zone: ZoneWithDisponibilite; onDone: (msg: string) => void }) {
  const demain8h = new Date();
  demain8h.setDate(demain8h.getDate() + 1);
  demain8h.setHours(8, 0, 0, 0);
  const [form, setForm] = useState({
    motif: "",
    debut: toDatetimeLocal(demain8h),
    fin: toDatetimeLocal(new Date(demain8h.getTime() + 4 * 60 * 60 * 1000)),
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const blocage = await createBlocage({
        id_zone: zone.id_zone,
        motif_blocage: form.motif,
        date_debut_blocage: localInputToIso(form.debut),
        date_fin_blocage: localInputToIso(form.fin),
      });
      setForm({ ...form, motif: "" });
      onDone(
        `Zone bloquée. ${blocage.reservations_annulees} réservation(s) annulée(s) sur la période.`,
      );
    } catch (err) {
      setError(extractErrorMessage(err, "Blocage impossible"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <label>
        Motif
        <input
          required
          minLength={3}
          value={form.motif}
          placeholder="Travaux, événement…"
          onChange={(e) => setForm({ ...form, motif: e.target.value })}
        />
      </label>
      <label>
        Début
        <input
          type="datetime-local"
          required
          value={form.debut}
          onChange={(e) => setForm({ ...form, debut: e.target.value })}
        />
      </label>
      <label>
        Fin
        <input
          type="datetime-local"
          required
          value={form.fin}
          onChange={(e) => setForm({ ...form, fin: e.target.value })}
        />
      </label>
      <button type="submit" disabled={submitting}>
        {submitting ? "Blocage…" : "Bloquer la zone"}
      </button>
      <ErrorMessage message={error} />
    </form>
  );
}

function ZoneDetail({
  zone,
  titre,
  onChanged,
}: {
  zone: ZoneWithDisponibilite;
  titre: string;
  onChanged: () => void;
}) {
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newPlace, setNewPlace] = useState({ numero_place: "", type_place: "standard" });

  const blocagesLoader = useCallback(() => listBlocages(zone.id_zone), [zone.id_zone]);
  const blocages = useApi(blocagesLoader);
  const placesLoader = useCallback(() => listPlaces(zone.id_zone), [zone.id_zone]);
  const places = useApi(placesLoader);

  async function run(action: () => Promise<unknown>, success: string) {
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(success);
      await Promise.all([blocages.reload(), places.reload()]);
      onChanged();
    } catch (err) {
      setError(extractErrorMessage(err, "Action impossible"));
    }
  }

  return (
    <section className="panel" aria-labelledby={`zone-${zone.id_zone}`}>
      <div className="panel__header">
        <div>
          <h2 id={`zone-${zone.id_zone}`}>{titre}</h2>
          <p className="muted">
            {zone.nombre_places} places · ouvert de {zone.heure_ouverture.slice(0, 5)} à{" "}
            {zone.heure_fermeture.slice(0, 5)} · {zone.nombre_places_libres} libres maintenant
          </p>
        </div>
        <button
          type="button"
          className={zone.zone_active ? "button--danger" : undefined}
          onClick={() =>
            run(
              () => updateZone(zone.id_zone, { zone_active: !zone.zone_active }),
              zone.zone_active ? "Zone désactivée." : "Zone réactivée.",
            )
          }
        >
          {zone.zone_active ? "Désactiver la zone" : "Réactiver la zone"}
        </button>
      </div>
      <SuccessMessage message={message} />
      <ErrorMessage message={error} />

      <h3>Blocages</h3>
      <p className="muted">
        Un blocage rend la zone indisponible sur une période et annule les réservations concernées.
      </p>
      <BlocageForm
        zone={zone}
        onDone={(msg) => {
          setMessage(msg);
          void blocages.reload();
          onChanged();
        }}
      />
      {blocages.loading && !blocages.data && <Loading />}
      <ErrorMessage message={blocages.error} />
      {blocages.data && blocages.data.length === 0 && <p className="muted">Aucun blocage.</p>}
      {blocages.data && blocages.data.length > 0 && (
        <ul className="item-list">
          {blocages.data.map((b) => (
            <li key={b.id_blocage}>
              <span>
                <strong>{b.motif_blocage}</strong>
                <span className="muted"> · {formatRange(b.date_debut_blocage, b.date_fin_blocage)}</span>
              </span>
              <button
                type="button"
                className="link-button"
                onClick={() => run(() => deleteBlocage(b.id_blocage), "Blocage supprimé.")}
              >
                Supprimer
              </button>
            </li>
          ))}
        </ul>
      )}

      <h3>Places</h3>
      <form
        className="inline-form"
        onSubmit={(e) => {
          e.preventDefault();
          void run(
            () => createPlace({ id_zone: zone.id_zone, ...newPlace }),
            `Place ${newPlace.numero_place} ajoutée.`,
          ).then(() => setNewPlace({ ...newPlace, numero_place: "" }));
        }}
      >
        <label>
          Numéro
          <input
            required
            maxLength={10}
            value={newPlace.numero_place}
            onChange={(e) => setNewPlace({ ...newPlace, numero_place: e.target.value })}
          />
        </label>
        <label>
          Type
          <select
            value={newPlace.type_place}
            onChange={(e) => setNewPlace({ ...newPlace, type_place: e.target.value })}
          >
            {TYPES_PLACE.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </label>
        <button type="submit">Ajouter une place</button>
      </form>
      {places.loading && !places.data && <Loading />}
      {places.data && (
        <ul className="item-list item-list--scroll">
          {places.data.map((place) => (
            <li key={place.id_place}>
              <span>
                <strong>{place.numero_place}</strong> <span className="muted">· {place.type_place}</span>
              </span>
              <select
                aria-label={`État de la place ${place.numero_place}`}
                value={place.etat_place}
                onChange={(e) =>
                  run(
                    () => updatePlace(place.id_place, { etat_place: e.target.value }),
                    `Place ${place.numero_place} : ${ETATS_PLACE[e.target.value]}.`,
                  )
                }
              >
                {Object.entries(ETATS_PLACE).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function NewZoneForm({
  parkings,
  onCreated,
}: {
  parkings: { id_parking: number; nom_parking: string }[];
  onCreated: (idZone: number) => void;
}) {
  const [form, setForm] = useState({
    id_parking: parkings[0]?.id_parking ?? 0,
    nouveau_parking: "",
    localisation: "",
    nom_zone: "",
    capacite_theorique: 10,
    heure_ouverture: "07:00",
    heure_fermeture: "20:00",
  });
  const [error, setError] = useState<string | null>(null);
  const creatingParking = form.id_parking === 0;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      let idParking = form.id_parking;
      if (creatingParking) {
        const parking = await createParking({
          nom_parking: form.nouveau_parking,
          localisation_parking: form.localisation,
        });
        idParking = parking.id_parking;
      }
      const zone = await createZone({
        id_parking: idParking,
        nom_zone: form.nom_zone,
        capacite_theorique: form.capacite_theorique,
        heure_ouverture: `${form.heure_ouverture}:00`,
        heure_fermeture: `${form.heure_fermeture}:00`,
      });
      onCreated(zone.id_zone);
    } catch (err) {
      setError(extractErrorMessage(err, "Création impossible"));
    }
  }

  return (
    <form className="panel inline-form" onSubmit={handleSubmit}>
      <label>
        Parking
        <select
          value={form.id_parking}
          onChange={(e) => setForm({ ...form, id_parking: Number(e.target.value) })}
        >
          {parkings.map((p) => (
            <option key={p.id_parking} value={p.id_parking}>
              {p.nom_parking}
            </option>
          ))}
          <option value={0}>+ Nouveau parking</option>
        </select>
      </label>
      {creatingParking && (
        <>
          <label>
            Nom du parking
            <input
              required
              value={form.nouveau_parking}
              onChange={(e) => setForm({ ...form, nouveau_parking: e.target.value })}
            />
          </label>
          <label>
            Adresse
            <input
              required
              value={form.localisation}
              onChange={(e) => setForm({ ...form, localisation: e.target.value })}
            />
          </label>
        </>
      )}
      <label>
        Nom de la zone
        <input
          required
          value={form.nom_zone}
          onChange={(e) => setForm({ ...form, nom_zone: e.target.value })}
        />
      </label>
      <label>
        Capacité
        <input
          type="number"
          min={1}
          required
          value={form.capacite_theorique}
          onChange={(e) => setForm({ ...form, capacite_theorique: Number(e.target.value) })}
        />
      </label>
      <label>
        Ouverture
        <input
          type="time"
          value={form.heure_ouverture}
          onChange={(e) => setForm({ ...form, heure_ouverture: e.target.value })}
        />
      </label>
      <label>
        Fermeture
        <input
          type="time"
          value={form.heure_fermeture}
          onChange={(e) => setForm({ ...form, heure_fermeture: e.target.value })}
        />
      </label>
      <button type="submit">Créer la zone</button>
      <ErrorMessage message={error} />
    </form>
  );
}

export default function ZonesPage() {
  const index = useZonesIndex();
  const [selected, setSelected] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const zone = index.zones.find((z) => z.id_zone === selected) ?? null;

  return (
    <div>
      <h1>Zones et blocages</h1>
      <ErrorMessage message={index.error} onRetry={index.reload} />
      {index.loading && index.zones.length === 0 && <Loading />}
      <div className="filters">
        <label>
          Zone
          <select
            value={selected ?? ""}
            onChange={(e) => {
              setCreating(false);
              setSelected(e.target.value ? Number(e.target.value) : null);
            }}
          >
            <option value="">Choisir une zone…</option>
            {index.parkings.map((parking) => (
              <optgroup key={parking.id_parking} label={parking.nom_parking}>
                {index.zones
                  .filter((z) => z.id_parking === parking.id_parking)
                  .map((z) => (
                    <option key={z.id_zone} value={z.id_zone}>
                      {z.nom_zone}
                      {z.zone_active ? "" : " (désactivée)"}
                    </option>
                  ))}
              </optgroup>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => setCreating(!creating)}>
          {creating ? "Annuler" : "Nouvelle zone"}
        </button>
      </div>

      {creating && (
        <NewZoneForm
          parkings={index.parkings}
          onCreated={(idZone) => {
            setCreating(false);
            void index.reload().then(() => setSelected(idZone));
          }}
        />
      )}
      {zone && (
        <ZoneDetail
          key={zone.id_zone}
          zone={zone}
          titre={index.label(zone.id_zone)}
          onChanged={() => void index.reload()}
        />
      )}
      {!zone && !creating && !index.loading && (
        <p className="muted">Sélectionnez une zone pour la bloquer, la désactiver ou gérer ses places.</p>
      )}
    </div>
  );
}
