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

export function useZonesIndex(): ZoneIndex {
  const loader = useCallback(async () => {
    const [parkings, zones] = await Promise.all([listParkings(), listZones()]);
    return { parkings, zones };
  }, []);
  const { data, error, loading, reload } = useApi(loader, "Impossible de charger les zones");

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
