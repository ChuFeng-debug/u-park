import { http } from "./http";
import type { DemandeVisiteurOut, IncidentOut, PrioriteIncident, UserOut } from "../types/api";

export interface ProfilUpdate {
  nom_utilisateur?: string;
  prenom_utilisateur?: string;
  besoin_pmr?: boolean;
}

export async function updateMe(payload: ProfilUpdate): Promise<UserOut> {
  const { data } = await http.patch<UserOut>("/auth/me", payload);
  return data;
}

export async function changePassword(actuel: string, nouveau: string): Promise<void> {
  await http.post("/auth/me/mot-de-passe", {
    mot_de_passe_actuel: actuel,
    nouveau_mot_de_passe: nouveau,
  });
}

export async function exportMe(): Promise<unknown> {
  const { data } = await http.get("/auth/me/export");
  return data;
}

export async function deleteMe(motDePasse: string): Promise<void> {
  await http.delete("/auth/me", { data: { mot_de_passe: motDePasse } });
}

// ---------- Visiteurs ----------

export async function listMesDemandes(): Promise<DemandeVisiteurOut[]> {
  const { data } = await http.get<DemandeVisiteurOut[]>("/demandes-visiteurs/mes-demandes");
  return data;
}

export async function createDemande(payload: {
  date_visite_souhaitee: string;
  date_fin_visite_souhaitee: string;
  motif_demande: string;
}): Promise<DemandeVisiteurOut> {
  const { data } = await http.post<DemandeVisiteurOut>("/demandes-visiteurs", payload);
  return data;
}

// ---------- Incidents ----------

export async function listMesIncidents(): Promise<IncidentOut[]> {
  const { data } = await http.get<IncidentOut[]>("/incidents/mes-signalements");
  return data;
}

export async function signalerIncident(payload: {
  id_zone: number;
  description_incident: string;
  priorite_incident: PrioriteIncident;
}): Promise<IncidentOut> {
  const { data } = await http.post<IncidentOut>("/incidents", payload);
  return data;
}
