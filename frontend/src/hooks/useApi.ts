import { useCallback, useEffect, useState } from "react";
import { extractErrorMessage } from "../api/http";

interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => Promise<void>;
}

/**
 * Charge une ressource et expose chargement / erreur / rechargement.
 * `loader` doit être stable (useCallback) : il est rappelé quand il change.
 */
export function useApi<T>(loader: () => Promise<T>, fallbackError = "Chargement impossible"): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setData(await loader());
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err, fallbackError));
    } finally {
      setLoading(false);
    }
  }, [loader, fallbackError]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { data, error, loading, reload };
}
