/**
 * Client HTTP partagé par toute l'application.
 *
 * Centraliser axios ici évite que chaque module d'appel ait à connaître
 * l'adresse du backend ou à rattacher le jeton à la main.
 */
import axios from "axios";

// Injectée au build par Vite (fichier .env) : l'URL diffère entre le
// développement local et le déploiement Docker.
const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const http = axios.create({ baseURL });

const TOKEN_KEY = "upark_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

// Intercepteur : relit le jeton avant CHAQUE requête et l'ajoute en en-tête
// `Authorization: Bearer ...`, au format attendu par OAuth2 côté FastAPI.
// Le relire à chaque fois (plutôt que de le figer à la création du client)
// permet à une connexion ou une déconnexion de prendre effet immédiatement.
http.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Traduit une erreur axios en message affichable.
 *
 * FastAPI place ses messages d'erreur dans le champ `detail`. On ne l'affiche
 * que s'il s'agit bien d'une chaîne : lors d'une erreur de validation (422),
 * `detail` est un tableau d'objets, illisible pour l'utilisateur — d'où le
 * repli sur un message générique fourni par l'appelant.
 */
export function extractErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}
