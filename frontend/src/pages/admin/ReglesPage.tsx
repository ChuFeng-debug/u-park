import { useState } from "react";
import type { FormEvent } from "react";
import { createRegle, deleteRegle, listRegles, updateRegle } from "../../api/admin";
import { extractErrorMessage } from "../../api/http";
import { ErrorMessage, Loading, SuccessMessage } from "../../components/Feedback";
import { useApi } from "../../hooks/useApi";
import { useZonesIndex } from "../../hooks/useZonesIndex";
import type { RegleAccesOut } from "../../types/api";
import { ROLE_LABEL, ROLES, toDateInput } from "../../utils/format";

function RolesPicker({
  value,
  onChange,
  name,
}: {
  value: string[];
  onChange: (roles: string[]) => void;
  name: string;
}) {
  return (
    <fieldset className="checkbox-group">
      <legend>Rôles autorisés</legend>
      {ROLES.filter((r) => r !== "administrateur").map((role) => (
        <label key={role} className="form-checkbox">
          <input
            type="checkbox"
            name={name}
            checked={value.includes(role)}
            onChange={(e) =>
              onChange(e.target.checked ? [...value, role] : value.filter((r) => r !== role))
            }
          />
          {ROLE_LABEL[role]}
        </label>
      ))}
    </fieldset>
  );
}

function RegleRow({
  regle,
  zoneLabel,
  onChanged,
  onError,
}: {
  regle: RegleAccesOut;
  zoneLabel: string;
  onChanged: (message: string) => void;
  onError: (message: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [roles, setRoles] = useState(regle.roles);

  async function run(action: () => Promise<unknown>, message: string) {
    try {
      await action();
      setEditing(false);
      onChanged(message);
    } catch (err) {
      onError(extractErrorMessage(err, "Action impossible"));
    }
  }

  return (
    <li className={regle.regle_active ? undefined : "is-inactive"}>
      <div className="item-list__main">
        <strong>{regle.libelle_regle}</strong>
        <span className="muted">
          {zoneLabel} · priorité {regle.niveau_priorite} · depuis le{" "}
          {new Date(regle.date_debut_validite).toLocaleDateString("fr-FR")}
          {regle.date_fin_validite &&
            ` jusqu'au ${new Date(regle.date_fin_validite).toLocaleDateString("fr-FR")}`}
        </span>
        {editing ? (
          <RolesPicker name={`roles-${regle.id_regle}`} value={roles} onChange={setRoles} />
        ) : (
          <span className="tag-list">
            {regle.roles.map((role) => (
              <span key={role} className="tag">
                {ROLE_LABEL[role] ?? role}
              </span>
            ))}
            {!regle.regle_active && <span className="tag tag--muted">inactive</span>}
          </span>
        )}
      </div>
      <div className="item-list__actions">
        {editing ? (
          <>
            <button
              type="button"
              disabled={roles.length === 0}
              onClick={() => run(() => updateRegle(regle.id_regle, { roles }), "Règle modifiée.")}
            >
              Enregistrer
            </button>
            <button type="button" className="link-button" onClick={() => setEditing(false)}>
              Annuler
            </button>
          </>
        ) : (
          <>
            <button type="button" className="link-button" onClick={() => setEditing(true)}>
              Modifier les rôles
            </button>
            <button
              type="button"
              className="link-button"
              onClick={() =>
                run(
                  () => updateRegle(regle.id_regle, { regle_active: !regle.regle_active }),
                  regle.regle_active ? "Règle désactivée." : "Règle activée.",
                )
              }
            >
              {regle.regle_active ? "Désactiver" : "Activer"}
            </button>
            <button
              type="button"
              className="link-button link-button--danger"
              onClick={() => {
                if (window.confirm(`Supprimer la règle « ${regle.libelle_regle} » ?`)) {
                  void run(() => deleteRegle(regle.id_regle), "Règle supprimée.");
                }
              }}
            >
              Supprimer
            </button>
          </>
        )}
      </div>
    </li>
  );
}

export default function ReglesPage() {
  const index = useZonesIndex();
  const regles = useApi(listRegles, "Impossible de charger les règles");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    id_zone: 0,
    libelle_regle: "",
    niveau_priorite: 1,
    date_debut_validite: toDateInput(new Date()),
    date_fin_validite: "",
    roles: [] as string[],
  });

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createRegle({
        ...form,
        date_fin_validite: form.date_fin_validite || null,
        regle_active: true,
      });
      setForm({ ...form, libelle_regle: "", roles: [] });
      setMessage("Règle créée.");
      await Promise.all([regles.reload(), index.reload()]);
    } catch (err) {
      setError(extractErrorMessage(err, "Création impossible"));
    }
  }

  return (
    <div>
      <h1>Règles d'accès</h1>
      <p className="muted">
        Une zone sans règle active est ouverte à tous. Dès qu'une règle est active, seuls les rôles
        qu'elle cible peuvent réserver dans la zone.
      </p>

      <form className="panel inline-form" onSubmit={handleCreate}>
        <label>
          Zone
          <select
            required
            value={form.id_zone || ""}
            onChange={(e) => setForm({ ...form, id_zone: Number(e.target.value) })}
          >
            <option value="">Choisir…</option>
            {index.zones.map((z) => (
              <option key={z.id_zone} value={z.id_zone}>
                {index.label(z.id_zone)}
              </option>
            ))}
          </select>
        </label>
        <label>
          Libellé
          <input
            required
            minLength={3}
            value={form.libelle_regle}
            onChange={(e) => setForm({ ...form, libelle_regle: e.target.value })}
          />
        </label>
        <label>
          Priorité
          <input
            type="number"
            min={1}
            value={form.niveau_priorite}
            onChange={(e) => setForm({ ...form, niveau_priorite: Number(e.target.value) })}
          />
        </label>
        <label>
          Valable du
          <input
            type="date"
            required
            value={form.date_debut_validite}
            onChange={(e) => setForm({ ...form, date_debut_validite: e.target.value })}
          />
        </label>
        <label>
          au (facultatif)
          <input
            type="date"
            value={form.date_fin_validite}
            onChange={(e) => setForm({ ...form, date_fin_validite: e.target.value })}
          />
        </label>
        <RolesPicker name="roles-new" value={form.roles} onChange={(roles) => setForm({ ...form, roles })} />
        <button type="submit" disabled={form.roles.length === 0}>
          Créer la règle
        </button>
      </form>

      <SuccessMessage message={message} />
      <ErrorMessage message={error ?? regles.error} />
      {regles.loading && !regles.data && <Loading />}
      {regles.data && (
        <ul className="item-list">
          {regles.data.length === 0 && <li className="muted">Aucune règle.</li>}
          {regles.data.map((regle) => (
            <RegleRow
              key={`${regle.id_regle}-${regle.roles.join()}-${regle.regle_active}`}
              regle={regle}
              zoneLabel={index.label(regle.id_zone)}
              onChanged={(msg) => {
                setError(null);
                setMessage(msg);
                void regles.reload();
              }}
              onError={setError}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
