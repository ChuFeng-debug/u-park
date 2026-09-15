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

export type StatutReservation = "confirmee" | "annulee";

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
}

export interface ReservationCreatePayload {
  id_place: number;
  date_debut: string;
  date_fin: string;
}

export interface ApiError {
  detail: string;
}
