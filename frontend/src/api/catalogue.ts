import { http } from "./http";
import type { ParkingOut, PlaceOut, ZoneWithDisponibilite } from "../types/api";

export async function listParkings(): Promise<ParkingOut[]> {
  const { data } = await http.get<ParkingOut[]>("/parkings");
  return data;
}

export async function listZones(idParking?: number): Promise<ZoneWithDisponibilite[]> {
  const { data } = await http.get<ZoneWithDisponibilite[]>("/zones", {
    params: idParking ? { id_parking: idParking } : undefined,
  });
  return data;
}

export async function listPlaces(idZone?: number): Promise<PlaceOut[]> {
  const { data } = await http.get<PlaceOut[]>("/places", {
    params: idZone ? { id_zone: idZone } : undefined,
  });
  return data;
}
