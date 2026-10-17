import { useCallback, useMemo } from "react";
import { listParkings, listZones } from "../api/catalogue";
import type { ParkingOut, ZoneWithDisponibilite } from "../types/api";
import { useApi } from "./useApi";

export interface ZoneIndex {
  parkings: ParkingOut[];
  zones: ZoneWithDisponibilite[];
  /** « Parking Copernic · Aérien » */
  label: (idZone: number) => string;
  reload: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

/**
 * Charge parkings et zones une fois, et fournit de quoi nommer une zone.
 *
 * Plusieurs écrans (réservations, incidents, back-office) n'affichent qu'un
 * `id_zone` renvoyé par l'API et doivent le traduire en libellé lisible.
 * Mutualiser ce chargement ici évite que chacun refasse les deux requêtes et
 * reconstruise sa propre table de correspondance.
 */
export function useZonesIndex(): ZoneIndex {
  // `Promise.all` lance les deux requêtes en parallèle : elles sont
  // indépendantes, les enchaîner doublerait inutilement le temps d'attente.
  const loader = useCallback(async () => {
    const [parkings, zones] = await Promise.all([listParkings(), listZones()]);
    return { parkings, zones };
  }, []);
  const { data, error, loading, reload } = useApi(loader, "Impossible de charger les zones");

  // Les libellés sont précalculés dans des Map, soit un accès en temps
  // constant : une recherche par `find` dans le tableau à chaque ligne d'un
  // tableau de réservations coûterait un parcours complet à chaque fois.
  // `useMemo` évite de refaire ce travail à chaque rendu du composant appelant.
  return useMemo(() => {
    const parkings = data?.parkings ?? [];
    const zones = data?.zones ?? [];
    const parkingNames = new Map(parkings.map((p) => [p.id_parking, p.nom_parking]));
    const zoneLabels = new Map(
      zones.map((z) => [z.id_zone, `${parkingNames.get(z.id_parking) ?? "?"} · ${z.nom_zone}`]),
    );
    return {
      parkings,
      zones,
      label: (idZone: number) => zoneLabels.get(idZone) ?? `Zone #${idZone}`,
      reload,
      loading,
      error,
    };
  }, [data, error, loading, reload]);
}
