import { useCallback, useState } from "react";
import { listUtilisateurs, updateUtilisateur } from "../../api/admin";
import { extractErrorMessage } from "../../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../../components/Feedback";
import { useAuth } from "../../contexts/AuthContext";
import { useApi } from "../../hooks/useApi";
import { ROLE_LABEL, ROLES } from "../../utils/format";

export default function UtilisateursPage() {
  const { user: me } = useAuth();
  const [recherche, setRecherche] = useState("");
  const [query, setQuery] = useState({ recherche: "", role: "" });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loader = useCallback(
    () => listUtilisateurs({ recherche: query.recherche || undefined, role: query.role || undefined }),
    [query],
  );
  const users = useApi(loader, "Impossible de charger les utilisateurs");

  async function update(
    idUtilisateur: number,
    payload: { statut_compte?: "actif" | "suspendu"; roles?: string[] },
    success: string,
  ) {
    setError(null);
    try {
      await updateUtilisateur(idUtilisateur, payload);
      setMessage(success);
      await users.reload();
    } catch (err) {
      setError(extractErrorMessage(err, "Modification impossible"));
    }
  }

  return (
    <div>
      <h1>Utilisateurs</h1>
      <form
        className="filters"
        onSubmit={(e) => {
          e.preventDefault();
          setQuery({ ...query, recherche });
        }}
      >
        <label>
          Rechercher
          <input
            type="search"
            placeholder="Nom, prénom ou email"
            value={recherche}
            onChange={(e) => setRecherche(e.target.value)}
          />
        </label>
        <label>
          Rôle
          <select value={query.role} onChange={(e) => setQuery({ ...query, role: e.target.value })}>
            <option value="">Tous</option>
            {ROLES.map((role) => (
              <option key={role} value={role}>
                {ROLE_LABEL[role]}
              </option>
            ))}
          </select>
        </label>
        <button type="submit">Rechercher</button>
      </form>
      <SuccessMessage message={message} />
      <ErrorMessage message={error ?? users.error} onRetry={users.reload} />
      {users.loading && !users.data && <Loading />}
      {users.data && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Nom</th>
                <th scope="col">Email</th>
                <th scope="col">Rôle</th>
                <th scope="col">Compte</th>
              </tr>
            </thead>
            <tbody>
              {users.data.map((u) => {
                const self = u.id_utilisateur === me?.id_utilisateur;
                const supprime = u.statut_compte === "supprime";
                return (
                  <tr key={u.id_utilisateur}>
                    <td>
                      {u.prenom_utilisateur} {u.nom_utilisateur}
                      {u.besoin_pmr && <span className="tag">PMR</span>}
                    </td>
                    <td className="muted">{u.email}</td>
                    <td>
                      <select
                        aria-label={`Rôle de ${u.prenom_utilisateur} ${u.nom_utilisateur}`}
                        value={u.roles[0] ?? ""}
                        disabled={self || supprime}
                        onChange={(e) =>
                          update(u.id_utilisateur, { roles: [e.target.value] }, "Rôle modifié.")
                        }
                      >
                        {ROLES.map((role) => (
                          <option key={role} value={role}>
                            {ROLE_LABEL[role]}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      {supprime ? (
                        <span className="muted">supprimé (RGPD)</span>
                      ) : (
                        <button
                          type="button"
                          className={u.statut_compte === "actif" ? "link-button link-button--danger" : "link-button"}
                          disabled={self}
                          onClick={() =>
                            update(
                              u.id_utilisateur,
                              { statut_compte: u.statut_compte === "actif" ? "suspendu" : "actif" },
                              u.statut_compte === "actif" ? "Compte suspendu." : "Compte réactivé.",
                            )
                          }
                        >
                          {u.statut_compte === "actif" ? "Suspendre" : "Réactiver"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {users.data?.length === 50 && <p className="muted">50 premiers résultats : affinez la recherche.</p>}
    </div>
  );
}
