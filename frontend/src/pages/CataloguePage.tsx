import { useEffect, useState } from "react";
import { listParkings, listPlaces, listZones } from "../api/catalogue";
import { createReservation } from "../api/reservations";
import { useAuth } from "../contexts/AuthContext";
import { extractErrorMessage } from "../api/http";
import type { ParkingOut, PlaceOut, ZoneWithDisponibilite } from "../types/api";

function toDatetimeLocal(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`;
}

function ReservationForm({ place, onDone }: { place: PlaceOut; onDone: () => void }) {
  const now = new Date();
  const inOneHour = new Date(now.getTime() + 60 * 60 * 1000);
  const inThreeHours = new Date(now.getTime() + 3 * 60 * 60 * 1000);
  const [dateDebut, setDateDebut] = useState(toDatetimeLocal(inOneHour));
  const [dateFin, setDateFin] = useState(toDatetimeLocal(inThreeHours));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      await createReservation({
        id_place: place.id_place,
        date_debut: new Date(dateDebut).toISOString(),
        date_fin: new Date(dateFin).toISOString(),
      });
      onDone();
    } catch (err) {
      setError(extractErrorMessage(err, "Réservation impossible"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="reservation-form">
      <label>
        Début
        <input
          type="datetime-local"
          value={dateDebut}
          onChange={(e) => setDateDebut(e.target.value)}
        />
      </label>
      <label>
        Fin
        <input type="datetime-local" value={dateFin} onChange={(e) => setDateFin(e.target.value)} />
      </label>
      <button type="button" onClick={handleSubmit} disabled={submitting}>
        {submitting ? "Réservation…" : "Confirmer"}
      </button>
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}

function ZonePlaces({ zone }: { zone: ZoneWithDisponibilite }) {
  const { user } = useAuth();
  const [places, setPlaces] = useState<PlaceOut[] | null>(null);
  const [reservingPlaceId, setReservingPlaceId] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setPlaces(await listPlaces(zone.id_zone));
  }

  if (places === null) {
    return (
      <button type="button" onClick={load}>
        Voir les places
      </button>
    );
  }

  return (
    <ul className="place-list">
      {places.map((place) => (
        <li key={place.id_place}>
          <span>
            {place.numero_place} · {place.type_place} · {place.etat_place}
          </span>
          {user && zone.zone_active && place.etat_place === "libre" && (
            <>
              <button type="button" onClick={() => setReservingPlaceId(place.id_place)}>
                Réserver
              </button>
              {reservingPlaceId === place.id_place && (
                <ReservationForm
                  place={place}
                  onDone={() => {
                    setReservingPlaceId(null);
                    setMessage(`Place ${place.numero_place} réservée.`);
                    void load();
                  }}
                />
              )}
            </>
          )}
        </li>
      ))}
      {message && <p className="form-success">{message}</p>}
    </ul>
  );
}

export default function CataloguePage() {
  const [parkings, setParkings] = useState<ParkingOut[]>([]);
  const [zonesByParking, setZonesByParking] = useState<Record<number, ZoneWithDisponibilite[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const parkingList = await listParkings();
      setParkings(parkingList);
      const allZones = await listZones();
      const grouped: Record<number, ZoneWithDisponibilite[]> = {};
      for (const zone of allZones) {
        grouped[zone.id_parking] ??= [];
        grouped[zone.id_parking].push(zone);
      }
      setZonesByParking(grouped);
      setLoading(false);
    }
    void load();
  }, []);

  if (loading) return <p>Chargement du catalogue…</p>;

  return (
    <div className="catalogue">
      <h1>Catalogue des parkings</h1>
      {parkings.length === 0 && <p>Aucun parking pour le moment.</p>}
      {parkings.map((parking) => (
        <section key={parking.id_parking} className="parking-card">
          <h2>{parking.nom_parking}</h2>
          <p>{parking.localisation_parking}</p>
          {parking.description_parking && <p className="muted">{parking.description_parking}</p>}
          <div className="zone-list">
            {(zonesByParking[parking.id_parking] ?? []).map((zone) => (
              <div key={zone.id_zone} className={`zone-card ${zone.zone_active ? "" : "zone-card--blocked"}`}>
                <h3>{zone.nom_zone}</h3>
                <p>
                  {zone.heure_ouverture} – {zone.heure_fermeture}
                </p>
                <p>
                  {zone.nombre_places_libres} / {zone.nombre_places} places libres
                  {!zone.zone_active && " (zone bloquée)"}
                </p>
                <ZonePlaces zone={zone} />
              </div>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
