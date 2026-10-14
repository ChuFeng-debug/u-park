export const ROLE_LABEL: Record<string, string> = {
  etudiant: "Étudiant",
  personnel: "Personnel",
  visiteur: "Visiteur",
  administrateur: "Administrateur",
};

export const ROLES = Object.keys(ROLE_LABEL);

export const STATUT_RESERVATION_LABEL: Record<string, string> = {
  confirmee: "confirmée",
  annulee: "annulée",
  no_show: "no-show",
};

export const STATUT_DEMANDE_LABEL: Record<string, string> = {
  en_attente: "en attente",
  validee: "validée",
  refusee: "refusée",
};

export const STATUT_INCIDENT_LABEL: Record<string, string> = {
  ouvert: "ouvert",
  en_cours: "en cours",
  resolu: "résolu",
};

export const PRIORITE_LABEL: Record<string, string> = {
  basse: "basse",
  moyenne: "moyenne",
  haute: "haute",
};

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDay(isoDate: string): string {
  return new Date(`${isoDate}T00:00`).toLocaleDateString("fr-FR", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

/** « 13/10/2026 · 14:00 – 16:00 » (ou deux dates si le créneau change de jour). */
export function formatRange(debutIso: string, finIso: string): string {
  const debut = new Date(debutIso);
  const fin = new Date(finIso);
  const heure = (d: Date) => d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  if (debut.toDateString() === fin.toDateString()) {
    return `${debut.toLocaleDateString("fr-FR")} · ${heure(debut)} – ${heure(fin)}`;
  }
  return `${formatDateTime(debutIso)} – ${formatDateTime(finIso)}`;
}

export function formatPercent(ratio: number): string {
  return `${(ratio * 100).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} %`;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** Date locale au format des champs <input type="date">. */
export function toDateInput(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** Valeur d'un <input type="datetime-local"> → ISO 8601 (UTC). */
export function localInputToIso(value: string): string {
  return new Date(value).toISOString();
}

/** Date → valeur d'un <input type="datetime-local">. */
export function toDatetimeLocal(date: Date): string {
  return `${toDateInput(date)}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}
