import { http } from "./http";
import type {
  BlocageCreated,
  BlocageOut,
  DemandeVisiteurAdminOut,
  DemandeVisiteurOut,
  IncidentOut,
  ParkingOut,
  PlaceOut,
  PrioriteIncident,
  RegleAccesOut,
  ReservationAdminOut,
  ReservationOut,
  Statistiques,
  StatutDemande,
  StatutIncident,
  TraceOut,
  UserAdminOut,
  ZoneWithDisponibilite,
} from "../types/api";

type Params = Record<string, string | number | boolean | undefined | null>;

/** Retire les filtres vides pour ne pas envoyer « ?statut= ». */
function clean(params: Params): Params {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ""),
  );
}

// ---------- Tableau de bord ----------

export async function getStatistiques(params: {
  du?: string;
  au?: string;
  id_parking?: number;
}): Promise<Statistiques> {
  const { data } = await http.get<Statistiques>("/admin/statistiques", { params: clean(params) });
  return data;
}

// ---------- Catalogue ----------

export async function createParking(payload: {
  nom_parking: string;
  localisation_parking: string;
  description_parking?: string | null;
}): Promise<ParkingOut> {
  const { data } = await http.post<ParkingOut>("/parkings", payload);
  return data;
}

export interface ZonePayload {
  id_parking: number;
  nom_zone: string;
  capacite_theorique: number;
  heure_ouverture: string;
  heure_fermeture: string;
}

export async function createZone(payload: ZonePayload): Promise<ZoneWithDisponibilite> {
  const { data } = await http.post<ZoneWithDisponibilite>("/zones", payload);
  return data;
}

export async function updateZone(
  idZone: number,
  payload: Partial<ZonePayload> & { zone_active?: boolean },
): Promise<void> {
  await http.patch(`/zones/${idZone}`, payload);
}

export async function createPlace(payload: {
  id_zone: number;
  numero_place: string;
  type_place: string;
}): Promise<PlaceOut> {
  const { data } = await http.post<PlaceOut>("/places", payload);
  return data;
}

export async function updatePlace(idPlace: number, payload: { etat_place: string }): Promise<void> {
  await http.patch(`/places/${idPlace}`, payload);
}

// ---------- Blocages ----------

export async function listBlocages(idZone?: number): Promise<BlocageOut[]> {
  const { data } = await http.get<BlocageOut[]>("/blocages", { params: clean({ id_zone: idZone }) });
  return data;
}

export async function createBlocage(payload: {
  id_zone: number;
  motif_blocage: string;
  date_debut_blocage: string;
  date_fin_blocage: string;
}): Promise<BlocageCreated> {
  const { data } = await http.post<BlocageCreated>("/blocages", payload);
  return data;
}

export async function deleteBlocage(idBlocage: number): Promise<void> {
  await http.delete(`/blocages/${idBlocage}`);
}

// ---------- Règles d'accès ----------

export async function listRegles(): Promise<RegleAccesOut[]> {
  const { data } = await http.get<RegleAccesOut[]>("/regles-acces");
  return data;
}

export interface ReglePayload {
  id_zone: number;
  libelle_regle: string;
  niveau_priorite: number;
  date_debut_validite: string;
  date_fin_validite: string | null;
  regle_active: boolean;
  roles: string[];
}

export async function createRegle(payload: ReglePayload): Promise<RegleAccesOut> {
  const { data } = await http.post<RegleAccesOut>("/regles-acces", payload);
  return data;
}

export async function updateRegle(
  idRegle: number,
  payload: Partial<Omit<ReglePayload, "id_zone">>,
): Promise<RegleAccesOut> {
  const { data } = await http.patch<RegleAccesOut>(`/regles-acces/${idRegle}`, payload);
  return data;
}

export async function deleteRegle(idRegle: number): Promise<void> {
  await http.delete(`/regles-acces/${idRegle}`);
}

// ---------- Demandes visiteurs ----------

export async function listDemandes(statut?: StatutDemande): Promise<DemandeVisiteurAdminOut[]> {
  const { data } = await http.get<DemandeVisiteurAdminOut[]>("/demandes-visiteurs", {
    params: clean({ statut }),
  });
  return data;
}

export async function validerDemande(
  idDemande: number,
  payload: { id_place?: number; commentaire_traitement?: string },
): Promise<DemandeVisiteurOut> {
  const { data } = await http.post<DemandeVisiteurOut>(
    `/demandes-visiteurs/${idDemande}/valider`,
    payload,
  );
  return data;
}

export async function refuserDemande(
  idDemande: number,
  commentaire: string,
): Promise<DemandeVisiteurOut> {
  const { data } = await http.post<DemandeVisiteurOut>(`/demandes-visiteurs/${idDemande}/refuser`, {
    commentaire_traitement: commentaire,
  });
  return data;
}

// ---------- Incidents ----------

export async function listIncidents(params: {
  statut?: StatutIncident;
  id_zone?: number;
}): Promise<IncidentOut[]> {
  const { data } = await http.get<IncidentOut[]>("/incidents", { params: clean(params) });
  return data;
}

export async function updateIncident(
  idIncident: number,
  payload: { statut_incident?: StatutIncident; priorite_incident?: PrioriteIncident },
): Promise<IncidentOut> {
  const { data } = await http.patch<IncidentOut>(`/incidents/${idIncident}`, payload);
  return data;
}

// ---------- Réservations ----------

export async function listReservationsAdmin(params: {
  id_zone?: number;
  statut?: string;
  du?: string;
  au?: string;
  limit?: number;
}): Promise<ReservationAdminOut[]> {
  const { data } = await http.get<ReservationAdminOut[]>("/admin/reservations", {
    params: clean(params),
  });
  return data;
}

export async function annulerReservationAdmin(
  idReservation: number,
  motif: string,
): Promise<ReservationOut> {
  const { data } = await http.patch<ReservationOut>(`/admin/reservations/${idReservation}/annuler`, {
    motif_annulation: motif,
  });
  return data;
}

export async function marquerNoShows(): Promise<number> {
  const { data } = await http.post<{ reservations_marquees: number }>("/admin/reservations/no-shows");
  return data.reservations_marquees;
}

// ---------- Utilisateurs et journal ----------

export async function listUtilisateurs(params: {
  recherche?: string;
  role?: string;
}): Promise<UserAdminOut[]> {
  const { data } = await http.get<UserAdminOut[]>("/admin/utilisateurs", { params: clean(params) });
  return data;
}

export async function updateUtilisateur(
  idUtilisateur: number,
  payload: { statut_compte?: "actif" | "suspendu"; roles?: string[] },
): Promise<UserAdminOut> {
  const { data } = await http.patch<UserAdminOut>(`/admin/utilisateurs/${idUtilisateur}`, payload);
  return data;
}

export async function listTraces(params: {
  type_action?: string;
  id_utilisateur?: number;
}): Promise<TraceOut[]> {
  const { data } = await http.get<TraceOut[]>("/admin/traces", { params: clean(params) });
  return data;
}
