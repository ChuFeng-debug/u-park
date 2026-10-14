/** Messages d'état homogènes (chargement, erreur, succès), annoncés aux lecteurs d'écran. */
export function Loading({ label = "Chargement…" }: { label?: string }) {
  return (
    <p className="muted" role="status">
      {label}
    </p>
  );
}

export function ErrorMessage({ message, onRetry }: { message: string | null; onRetry?: () => void }) {
  if (!message) return null;
  return (
    <div className="form-error" role="alert">
      {message}
      {onRetry && (
        <button type="button" className="link-button" onClick={onRetry}>
          Réessayer
        </button>
      )}
    </div>
  );
}

export function SuccessMessage({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <p className="form-success" role="status">
      {message}
    </p>
  );
}
