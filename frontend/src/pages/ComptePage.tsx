import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { changePassword, deleteMe, exportMe, updateMe } from "../api/compte";
import { extractErrorMessage } from "../api/http";
import { ErrorMessage, SuccessMessage } from "../components/Feedback";
import { useAuth } from "../contexts/AuthContext";
import { ROLE_LABEL } from "../utils/format";

function ProfilForm() {
  const { user, setCurrentUser } = useAuth();
  const [form, setForm] = useState({
    prenom_utilisateur: user?.prenom_utilisateur ?? "",
    nom_utilisateur: user?.nom_utilisateur ?? "",
    besoin_pmr: user?.besoin_pmr ?? false,
  });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      setCurrentUser(await updateMe(form));
      setMessage("Profil mis à jour.");
    } catch (err) {
      setError(extractErrorMessage(err, "Mise à jour impossible"));
    }
  }

  return (
    <form className="panel stack-form" onSubmit={handleSubmit}>
      <h2>Profil</h2>
      <p className="muted">
        {user?.email} · {user?.roles.map((r) => ROLE_LABEL[r] ?? r).join(", ")}
      </p>
      <label>
        Prénom
        <input
          required
          value={form.prenom_utilisateur}
          onChange={(e) => setForm({ ...form, prenom_utilisateur: e.target.value })}
        />
      </label>
      <label>
        Nom
        <input
          required
          value={form.nom_utilisateur}
          onChange={(e) => setForm({ ...form, nom_utilisateur: e.target.value })}
        />
      </label>
      <label className="form-checkbox">
        <input
          type="checkbox"
          checked={form.besoin_pmr}
          onChange={(e) => setForm({ ...form, besoin_pmr: e.target.checked })}
        />
        J'ai besoin d'une place PMR (déclaratif, aucun justificatif n'est stocké)
      </label>
      <button type="submit">Enregistrer</button>
      <SuccessMessage message={message} />
      <ErrorMessage message={error} />
    </form>
  );
}

function PasswordForm() {
  const [form, setForm] = useState({ actuel: "", nouveau: "", confirmation: "" });
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMessage(null);
    if (form.nouveau !== form.confirmation) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }
    try {
      await changePassword(form.actuel, form.nouveau);
      setForm({ actuel: "", nouveau: "", confirmation: "" });
      setMessage("Mot de passe modifié.");
    } catch (err) {
      setError(extractErrorMessage(err, "Modification impossible"));
    }
  }

  return (
    <form className="panel stack-form" onSubmit={handleSubmit}>
      <h2>Mot de passe</h2>
      <label>
        Mot de passe actuel
        <input
          type="password"
          required
          autoComplete="current-password"
          value={form.actuel}
          onChange={(e) => setForm({ ...form, actuel: e.target.value })}
        />
      </label>
      <label>
        Nouveau mot de passe (8 caractères minimum)
        <input
          type="password"
          required
          minLength={8}
          autoComplete="new-password"
          value={form.nouveau}
          onChange={(e) => setForm({ ...form, nouveau: e.target.value })}
        />
      </label>
      <label>
        Confirmation
        <input
          type="password"
          required
          autoComplete="new-password"
          value={form.confirmation}
          onChange={(e) => setForm({ ...form, confirmation: e.target.value })}
        />
      </label>
      <button type="submit">Changer le mot de passe</button>
      <SuccessMessage message={message} />
      <ErrorMessage message={error} />
    </form>
  );
}

function DonneesPersonnelles() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [motDePasse, setMotDePasse] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleExport() {
    setError(null);
    try {
      const data = await exportMe();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "u-park-mes-donnees.json";
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(extractErrorMessage(err, "Export impossible"));
    }
  }

  async function handleDelete(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await deleteMe(motDePasse);
      logout();
      navigate("/", { replace: true });
    } catch (err) {
      setError(extractErrorMessage(err, "Suppression impossible"));
    }
  }

  return (
    <section className="panel stack-form">
      <h2>Mes données personnelles</h2>
      <p className="muted">
        Voir la <Link to="/confidentialite">politique de données personnelles</Link>.
      </p>
      <button type="button" className="button--secondary" onClick={handleExport}>
        Télécharger mes données (JSON)
      </button>
      {!confirming ? (
        <button type="button" className="button--danger" onClick={() => setConfirming(true)}>
          Supprimer mon compte
        </button>
      ) : (
        <form className="danger-zone" onSubmit={handleDelete}>
          <p>
            Votre compte sera anonymisé et vos réservations à venir annulées. Cette action est
            définitive.
          </p>
          <label>
            Confirmez avec votre mot de passe
            <input
              type="password"
              required
              autoComplete="current-password"
              value={motDePasse}
              onChange={(e) => setMotDePasse(e.target.value)}
            />
          </label>
          <div className="card__actions">
            <button type="submit" className="button--danger">
              Supprimer définitivement
            </button>
            <button type="button" className="link-button" onClick={() => setConfirming(false)}>
              Annuler
            </button>
          </div>
        </form>
      )}
      <ErrorMessage message={error} />
    </section>
  );
}

export default function ComptePage() {
  return (
    <div className="compte">
      <h1>Mon compte</h1>
      <div className="compte__grid">
        <ProfilForm />
        <PasswordForm />
      </div>
      <DonneesPersonnelles />
    </div>
  );
}
