export type Role = "etudiant" | "personnel" | "visiteur" | "administrateur";

export interface UserOut {
  id_utilisateur: number;
  email: string;
  nom_utilisateur: string;
  prenom_utilisateur: string;
  statut_compte: string;
  besoin_pmr: boolean;
  roles: string[];
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  nom_utilisateur: string;
  prenom_utilisateur: string;
  role: Role;
  besoin_pmr?: boolean;
}

export interface ParkingOut {
  id_parking: number;
  nom_parking: string;
  localisation_parking: string;
  description_parking: string | null;
}

export interface ZoneWithDisponibilite {
  id_zone: number;
  id_parking: number;
  nom_zone: string;
  capacite_theorique: number;
  heure_ouverture: string;
  heure_fermeture: string;
  zone_active: boolean;
  nombre_places: number;
  nombre_places_libres: number;
  /** Rôles autorisés par les règles d'accès ; null = zone ouverte à tous. */
  roles_autorises: string[] | null;
}

export type TypePlace = "standard" | "pmr" | "electrique" | "moto";
export type EtatPlace = "libre" | "occupee" | "hors_service";

export interface PlaceOut {
  id_place: number;
  id_zone: number;
  numero_place: string;
  type_place: TypePlace;
  etat_place: EtatPlace;
}

export interface PlaceWithDisponibilite extends PlaceOut {
  disponible: boolean;
}

/** Créneau au format ISO 8601, envoyé tel quel à l'API. */
export interface Creneau {
  debut: string;
  fin: string;
}

export type StatutReservation = "confirmee" | "annulee" | "no_show";

export interface ReservationOut {
  id_reservation: number;
  id_utilisateur: number;
  id_place: number;
  date_debut: string;
  date_fin: string;
  statut_reservation: StatutReservation;
  date_creation_resa: string;
  date_annulation: string | null;
  motif_annulation: string | null;
  date_passage: string | null;
}

export interface ReservationCreatePayload {
  id_place: number;
  date_debut: string;
  date_fin: string;
}

export interface ApiError {
  detail: string;
}

// ---------- Compte ----------

export interface UserAdminOut extends UserOut {
  date_creation_compte: string;
}

// ---------- Back-office ----------

export interface ReservationDetailOut extends ReservationOut {
  numero_place: string;
  id_zone: number;
}

export interface ReservationAdminOut extends ReservationDetailOut {
  nom_utilisateur: string;
  prenom_utilisateur: string;
}

export interface BlocageOut {
  id_blocage: number;
  id_zone: number;
  id_utilisateur: number;
  motif_blocage: string;
  date_debut_blocage: string;
  date_fin_blocage: string;
}

export interface BlocageCreated extends BlocageOut {
  reservations_annulees: number;
}

export interface RegleAccesOut {
  id_regle: number;
  id_zone: number;
  libelle_regle: string;
  niveau_priorite: number;
  date_debut_validite: string;
  date_fin_validite: string | null;
  regle_active: boolean;
  roles: string[];
}

export type StatutDemande = "en_attente" | "validee" | "refusee";

export interface DemandeVisiteurOut {
  id_demande: number;
  id_demandeur: number;
  id_administrateur: number | null;
  id_reservation: number | null;
  date_demande: string;
  date_visite_souhaitee: string;
  date_fin_visite_souhaitee: string;
  motif_demande: string;
  statut_demande: StatutDemande;
  date_traitement: string | null;
  commentaire_traitement: string | null;
}

export interface DemandeVisiteurAdminOut extends DemandeVisiteurOut {
  nom_demandeur: string;
  prenom_demandeur: string;
}

export type PrioriteIncident = "basse" | "moyenne" | "haute";
export type StatutIncident = "ouvert" | "en_cours" | "resolu";

export interface IncidentOut {
  id_incident: number;
  id_zone: number;
  id_utilisateur_signalement: number;
  id_utilisateur_traitant: number | null;
  description_incident: string;
  priorite_incident: PrioriteIncident;
  statut_incident: StatutIncident;
  date_signalement: string;
  date_resolution: string | null;
}

export interface TraceOut {
  id_trace: number;
  id_utilisateur: number;
  horodatage: string;
  type_action: string;
  entite_cible: string;
  identifiant_cible: number;
  detail_action: string | null;
}

// ---------- Statistiques ----------

export interface Indicateurs {
  reservations: number;
  honorees: number;
  annulees: number;
  no_show: number;
  taux_annulation: number;
  taux_no_show: number;
  taux_occupation: number;
}

export interface StatJour extends Indicateurs {
  jour: string;
}

export interface StatZone extends Indicateurs {
  id_zone: number;
  nom_zone: string;
  id_parking: number;
  nom_parking: string;
  nombre_places: number;
}

export interface Statistiques {
  du: string;
  au: string;
  totaux: Indicateurs;
  par_jour: StatJour[];
  par_zone: StatZone[];
}
