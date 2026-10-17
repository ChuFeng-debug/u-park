import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import * as authApi from "../api/auth";
import { getStoredToken, setStoredToken } from "../api/http";
import type { RegisterPayload, UserOut } from "../types/api";

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<UserOut>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  /** Remplace l'utilisateur courant (après une modification de profil). */
  setCurrentUser: (user: UserOut) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * Source de vérité unique sur l'utilisateur connecté.
 *
 * Le jeton JWT est conservé dans le localStorage (voir api/http.ts), mais il
 * n'est jamais décodé côté client : l'identité affichée provient toujours d'un
 * appel à /auth/me. Le navigateur ne décide donc pas des droits, il ne fait que
 * refléter ce que le backend lui répond.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  // Au premier rendu, on repart du jeton stocké pour rétablir la session :
  // sans cela, un simple rafraîchissement de page déconnecterait l'utilisateur.
  const refreshUser = useCallback(async () => {
    if (!getStoredToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const currentUser = await authApi.me();
      setUser(currentUser);
    } catch {
      // Jeton expiré ou révoqué : on le purge pour éviter de renvoyer
      // indéfiniment des requêtes vouées à un 401.
      setStoredToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const token = await authApi.login(email, password);
    setStoredToken(token.access_token);
    const currentUser = await authApi.me();
    setUser(currentUser);
    return currentUser;
  }, []);

  // L'inscription ne renvoie pas de jeton : on enchaîne volontairement sur un
  // login pour que l'utilisateur arrive connecté plutôt que sur l'écran de
  // connexion avec ses identifiants à ressaisir.
  const register = useCallback(async (payload: RegisterPayload) => {
    await authApi.register(payload);
    await login(payload.email, payload.password);
  }, [login]);

  const logout = useCallback(() => {
    setStoredToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, setCurrentUser: setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Accès au contexte d'authentification.
 *
 * Le contexte est typé `| undefined` et ce hook lève si le provider manque :
 * on transforme ainsi un bug d'arborescence en erreur explicite au lieu de
 * laisser les composants manipuler un `user` silencieusement toujours nul.
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth doit être utilisé dans un AuthProvider");
  }
  return context;
}
