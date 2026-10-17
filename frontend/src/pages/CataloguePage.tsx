import { useCallback, useEffect, useMemo, useState } from "react";
import { listParkings, listPlaces, listZones } from "../api/catalogue";
import { createReservation } from "../api/reservations";
import { useAuth } from "../contexts/AuthContext";
import { extractErrorMessage } from "../api/http";
import type {
  Creneau,
  UserOut,
  ParkingOut,
  PlaceWithDisponibilite,
  ZoneWithDisponibilite,
} from "../types/api";

interface CreneauForm {
  jour: string; // YYYY-MM-DD
  heureDebut: string; // HH:MM
  heureFin: string; // HH:MM
}

const pad = (n: number) => String(n).padStart(2, "0");

function toDateInput(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** Prochaine heure pleine sur 2 h ; demain 8 h si la journée est trop avancée. */
function defaultCreneau(): CreneauForm {
  const now = new Date();
  const debut = now.getHours() + 1;
  if (debut >= 7 && debut <= 18) {
    return { jour: toDateInput(now), heureDebut: `${pad(debut)}:00`, heureFin: `${pad(debut + 2)}:00` };
  }
  const demain = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  return { jour: toDateInput(demain), heureDebut: "08:00", heureFin: "10:00" };
}

function toCreneau(form: CreneauForm): Creneau | null {
  const debut = new Date(`${form.jour}T${form.heureDebut}`);
  const fin = new Date(`${form.jour}T${form.heureFin}`);
  if (Number.isNaN(debut.getTime()) || Number.isNaN(fin.getTime()) || fin <= debut) return null;
  return { debut: debut.toISOString(), fin: fin.toISOString() };
}

function formatCreneau(form: CreneauForm): string {
  const jour = new Date(`${form.jour}T00:00`).toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
  return `${jour} de ${form.heureDebut} à ${form.heureFin}`;
}

function availabilityBadgeClass(libres: number, total: number): string {
  if (total === 0 || libres === 0) return "badge--full";
  if (libres / total <= 0.25) return "badge--tight";
  return "badge--available";
}

const TYPE_LABEL: Record<string, string> = {
  standard: "standard",
  pmr: "PMR",
  electrique: "électrique",
  moto: "moto",
};

const ROLE_LABEL: Record<string, string> = {
  etudiant: "étudiants",
  personnel: "personnels",
  visiteur: "visiteurs",
  administrateur: "administrateurs",
};

/**
 * Miroir des règles appliquées par l'API, pour ne proposer que ce qui est
 * réservable.
 *
 * Cette duplication de la règle métier est assumée : elle sert uniquement à
 * masquer des boutons voués à l'échec. L'API revalide systématiquement, donc
 * une divergence entre les deux dégrade l'ergonomie, jamais la sécurité.
 */
function isVisitorOnly(user: UserOut | null): boolean {
  // « every » et non « some » : un visiteur qui serait aussi personnel garde
  // le droit de réserver directement.
  return !!user && user.roles.every((role) => role === "visiteur");
}

function canReserveInZone(user: UserOut | null, zone: ZoneWithDisponibilite): boolean {
  // Les visiteurs passent par une demande validée par un administrateur.
  if (!user || isVisitorOnly(user)) return false;
  if (user.roles.includes("administrateur") || zone.roles_autorises === null) return true;
  return user.roles.some((role) => zone.roles_autorises?.includes(role));
}

function canReservePlace(user: UserOut | null, place: PlaceWithDisponibilite): boolean {
  if (!user || !place.disponible) return false;
  if (place.type_place !== "pmr") return true;
  return user.besoin_pmr || user.roles.includes("administrateur");
}

function placeStatus(place: PlaceWithDisponibilite): string {
  if (place.etat_place === "hors_service") return "hors service";
  return place.disponible ? "disponible" : "réservée";
}

/**
 * Liste dépliable des places d'une zone, pour le créneau choisi en haut de page.
 *
 * Les places ne sont chargées qu'à l'ouverture : une page de catalogue peut
 * compter des dizaines de zones, les interroger toutes d'emblée représenterait
 * autant de requêtes pour des listes que l'utilisateur n'ouvrira pas.
 */
function ZonePlaces({
  zone,
  creneau,
  creneauLabel,
  onReserved,
}: {
  zone: ZoneWithDisponibilite;
  creneau: Creneau;
  creneauLabel: string;
  onReserved: () => void;
}) {
  const { user } = useAuth();
  const canReserveZone = canReserveInZone(user, zone);
  const [places, setPlaces] = useState<PlaceWithDisponibilite[] | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [onlyAvailable, setOnlyAvailable] = useState(true);
  const [reservingPlaceId, setReservingPlaceId] = useState<number | null>(null);
  // Le message reste lié au créneau réservé : il disparaît si le créneau change.
  const [message, setMessage] = useState<{ text: string; creneau: Creneau } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setPlaces(await listPlaces(zone.id_zone, creneau));
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de charger les places"));
    } finally {
      setLoading(false);
    }
  }, [zone.id_zone, creneau]);

  // Recharge à l'ouverture et à chaque changement de créneau.
  // `load` est enveloppé dans useCallback et dépend du créneau : modifier le
  // créneau produit une nouvelle fonction, ce qui relance cet effet. C'est
  // aussi pourquoi `creneau` doit être mémoïsé par le parent — un objet
  // recréé à chaque rendu provoquerait ici une boucle de rechargement.
  useEffect(() => {
    if (expanded) void load();
  }, [expanded, load]);

  function show() {
    setExpanded(true);
  }

  function hide() {
    setExpanded(false);
    setMessage(null);
    setError(null);
  }

  async function reserve(place: PlaceWithDisponibilite) {
    setReservingPlaceId(place.id_place);
    setMessage(null);
    setError(null);
    try {
      await createReservation({
        id_place: place.id_place,
        date_debut: creneau.debut,
        date_fin: creneau.fin,
      });
      setMessage({ text: `Place ${place.numero_place} réservée le ${creneauLabel}.`, creneau });
      await load();
      onReserved();
    } catch (err) {
      setError(extractErrorMessage(err, "Réservation impossible"));
    } finally {
      setReservingPlaceId(null);
    }
  }

  if (!expanded) {
    return (
      <button type="button" onClick={show}>
        Voir les places
      </button>
    );
  }

  const visibles = (places ?? []).filter((place) => !onlyAvailable || place.disponible);

  return (
    <>
      <label className="form-checkbox place-filter">
        <input
          type="checkbox"
          checked={onlyAvailable}
          onChange={(e) => setOnlyAvailable(e.target.checked)}
        />
        Uniquement les places disponibles
      </label>
      {loading && places === null && <p>Chargement…</p>}
      {places !== null && visibles.length === 0 && (
        <p className="muted">Aucune place disponible sur ce créneau.</p>
      )}
      <ul className="place-list">
        {visibles.map((place) => (
          <li key={place.id_place}>
            <span>
              <strong>{place.numero_place}</strong> · {TYPE_LABEL[place.type_place] ?? place.type_place}
            </span>
            <span className={`badge ${place.disponible ? "badge--available" : "badge--full"}`}>
              {placeStatus(place)}
            </span>
            {canReserveZone && canReservePlace(user, place) && (
              <button
                type="button"
                onClick={() => reserve(place)}
                disabled={reservingPlaceId !== null}
              >
                {reservingPlaceId === place.id_place ? "Réservation…" : "Réserver"}
              </button>
            )}
          </li>
        ))}
      </ul>
      {/* Comparaison par référence, volontaire : le parent recrée l'objet
          `creneau` dès que l'utilisateur change de date ou d'heure, donc
          l'égalité échoue et la confirmation disparaît d'elle-même. Elle ne
          peut ainsi jamais rester affichée sous un créneau qu'elle ne
          concerne plus. */}
      {message?.creneau === creneau && <p className="form-success">{message.text}</p>}
      {error && <p className="form-error">{error}</p>}
      <button type="button" className="link-button" onClick={hide}>
        Afficher moins
      </button>
    </>
  );
}

function CreneauPicker({
  value,
  onChange,
}: {
  value: CreneauForm;
  onChange: (value: CreneauForm) => void;
}) {
  return (
    <form className="creneau-picker" onSubmit={(e) => e.preventDefault()}>
      <label>
        Jour
        <input
          type="date"
          value={value.jour}
          min={toDateInput(new Date())}
          onChange={(e) => onChange({ ...value, jour: e.target.value })}
        />
      </label>
      <label>
        De
        <input
          type="time"
          step={900}
          value={value.heureDebut}
          onChange={(e) => onChange({ ...value, heureDebut: e.target.value })}
        />
      </label>
      <label>
        À
        <input
          type="time"
          step={900}
          value={value.heureFin}
          onChange={(e) => onChange({ ...value, heureFin: e.target.value })}
        />
      </label>
    </form>
  );
}

/**
 * Page d'accueil : parkings, zones et disponibilité sur un créneau choisi.
 *
 * Le créneau est l'état central de l'écran. Il n'est saisi qu'une fois, en
 * haut de page, et toutes les disponibilités affichées en découlent — plutôt
 * que de demander des dates à chaque tentative de réservation.
 */
export default function CataloguePage() {
  const { user } = useAuth();
  const [parkings, setParkings] = useState<ParkingOut[]>([]);
  const [zones, setZones] = useState<ZoneWithDisponibilite[]>([]);
  const [creneauForm, setCreneauForm] = useState<CreneauForm>(defaultCreneau);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Vaut null tant que la saisie est incohérente (fin avant début), ce qui
  // suspend l'affichage des places au lieu d'interroger l'API pour rien.
  // useMemo garantit en outre une référence stable tant que le formulaire ne
  // change pas : cet objet sert de dépendance aux effets des zones.
  const creneau = useMemo(() => toCreneau(creneauForm), [creneauForm]);

  const loadZones = useCallback(async () => {
    if (!creneau) return;
    try {
      setZones(await listZones(creneau));
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de charger les disponibilités"));
    }
  }, [creneau]);

  // Les parkings ne dépendent pas du créneau : une seule requête au montage,
  // d'où le tableau de dépendances vide. Les zones, elles, sont rechargées
  // par l'effet suivant à chaque changement de créneau.
  useEffect(() => {
    listParkings()
      .then(setParkings)
      .catch((err) => setError(extractErrorMessage(err, "Impossible de charger le catalogue")))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    void loadZones();
  }, [loadZones]);

  // L'API renvoie les zones à plat ; l'affichage les veut regroupées sous
  // leur parking. On indexe donc une fois par id_parking plutôt que de
  // refiltrer le tableau complet pour chacun d'eux.
  const zonesByParking = useMemo(() => {
    const grouped: Record<number, ZoneWithDisponibilite[]> = {};
    for (const zone of zones) {
      grouped[zone.id_parking] ??= [];
      grouped[zone.id_parking].push(zone);
    }
    return grouped;
  }, [zones]);

  if (loading) return <p>Chargement du catalogue…</p>;

  const creneauLabel = formatCreneau(creneauForm);

  return (
    <div className="catalogue">
      <h1>Catalogue des parkings</h1>
      <section className="creneau-bar" aria-label="Créneau recherché">
        <CreneauPicker value={creneauForm} onChange={setCreneauForm} />
        {creneau ? (
          <p className="muted">Disponibilités pour le {creneauLabel}.</p>
        ) : (
          <p className="form-error">L'heure de fin doit être après l'heure de début.</p>
        )}
        {!user && <p className="muted">Connectez-vous pour réserver une place.</p>}
        {isVisitorOnly(user) && (
          <p className="muted">
            En tant que visiteur, votre place est attribuée après validation d'une demande par
            l'administration.
          </p>
        )}
      </section>
      {error && <p className="form-error">{error}</p>}
      {parkings.length === 0 && !error && <p>Aucun parking pour le moment.</p>}
      {parkings.map((parking) => (
        <section key={parking.id_parking} className="parking-card">
          <h2>{parking.nom_parking}</h2>
          <p>{parking.localisation_parking}</p>
          {parking.description_parking && <p className="muted">{parking.description_parking}</p>}
          <div className="zone-list">
            {(zonesByParking[parking.id_parking] ?? []).map((zone) => (
              <div
                key={zone.id_zone}
                className={`zone-card ${zone.zone_active ? "" : "zone-card--blocked"}`}
              >
                <h3>{zone.nom_zone}</h3>
                <p>
                  Ouvert de {zone.heure_ouverture.slice(0, 5)} à {zone.heure_fermeture.slice(0, 5)}
                </p>
                <p>
                  {zone.zone_active ? (
                    <span
                      className={`badge ${availabilityBadgeClass(zone.nombre_places_libres, zone.nombre_places)}`}
                    >
                      {zone.nombre_places_libres} / {zone.nombre_places} libres
                    </span>
                  ) : (
                    <span className="badge badge--blocked">zone bloquée</span>
                  )}
                </p>
                {zone.roles_autorises && (
                  <p>
                    Réservé aux{" "}
                    {zone.roles_autorises.map((role) => ROLE_LABEL[role] ?? role).join(", ")}
                  </p>
                )}
                {zone.zone_active && creneau && (
                  <ZonePlaces
                    zone={zone}
                    creneau={creneau}
                    creneauLabel={creneauLabel}
                    onReserved={loadZones}
                  />
                )}
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
