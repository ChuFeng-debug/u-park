import { http } from "./http";
import type {
  Creneau,
  ParkingOut,
  PlaceWithDisponibilite,
  ZoneWithDisponibilite,
} from "../types/api";

export async function listParkings(): Promise<ParkingOut[]> {
  const { data } = await http.get<ParkingOut[]>("/parkings");
  return data;
}

export async function listZones(
  creneau?: Creneau,
  idParking?: number,
): Promise<ZoneWithDisponibilite[]> {
  const { data } = await http.get<ZoneWithDisponibilite[]>("/zones", {
    params: { ...creneau, ...(idParking ? { id_parking: idParking } : {}) },
  });
  return data;
}

export async function listPlaces(
  idZone: number,
  creneau?: Creneau,
): Promise<PlaceWithDisponibilite[]> {
  const { data } = await http.get<PlaceWithDisponibilite[]>("/places", {
    params: { id_zone: idZone, ...creneau },
  });
  return data;
}
