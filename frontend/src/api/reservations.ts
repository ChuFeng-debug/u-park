import { http } from "./http";
import type { ReservationCreatePayload, ReservationOut } from "../types/api";

export async function listMyReservations(): Promise<ReservationOut[]> {
  const { data } = await http.get<ReservationOut[]>("/reservations");
  return data;
}

export async function createReservation(
  payload: ReservationCreatePayload,
): Promise<ReservationOut> {
  const { data } = await http.post<ReservationOut>("/reservations", payload);
  return data;
}

export async function cancelReservation(
  idReservation: number,
  motifAnnulation?: string,
): Promise<ReservationOut> {
  const { data } = await http.patch<ReservationOut>(
    `/reservations/${idReservation}/annuler`,
    { motif_annulation: motifAnnulation ?? null },
  );
  return data;
}
