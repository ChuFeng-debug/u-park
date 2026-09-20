import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { extractErrorMessage } from "../api/http";
import type { Role } from "../types/api";

const ROLES: { value: Role; label: string }[] = [
  { value: "etudiant", label: "Étudiant" },
  { value: "personnel", label: "Personnel" },
  { value: "visiteur", label: "Visiteur" },
  { value: "administrateur", label: "Administrateur" },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: "",
    password: "",
    nom_utilisateur: "",
    prenom_utilisateur: "",
    role: "etudiant" as Role,
    besoin_pmr: false,
  });
  // Hors de `form` : ce champ sert uniquement à la vérification, il n'est pas envoyé à l'API.
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const passwordsMismatch =
    passwordConfirm.length > 0 && passwordConfirm !== form.password;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (form.password !== passwordConfirm) {
      setError("Les mots de passe ne correspondent pas");
      return;
    }
    setSubmitting(true);
    try {
      await register(form);
      navigate("/reservations");
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible de créer le compte"));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="form-page">
      <h1>Inscription</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Prénom
          <input
            value={form.prenom_utilisateur}
            onChange={(e) => setForm({ ...form, prenom_utilisateur: e.target.value })}
            required
          />
        </label>
        <label>
          Nom
          <input
            value={form.nom_utilisateur}
            onChange={(e) => setForm({ ...form, nom_utilisateur: e.target.value })}
            required
          />
        </label>
        <label>
          Email
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </label>
        <label>
          Mot de passe
          <div className="password-field">
            <input
              type={showPassword ? "text" : "password"}
              minLength={8}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={
                showPassword ? "Masquer le mot de passe" : "Afficher le mot de passe"
              }
            >
              {showPassword ? "Masquer" : "Afficher"}
            </button>
          </div>
        </label>
        <label>
          Confirmation du mot de passe
          <div className="password-field">
            <input
              type={showPasswordConfirm ? "text" : "password"}
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              aria-invalid={passwordsMismatch}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPasswordConfirm(!showPasswordConfirm)}
              aria-label={
                showPasswordConfirm
                  ? "Masquer la confirmation du mot de passe"
                  : "Afficher la confirmation du mot de passe"
              }
            >
              {showPasswordConfirm ? "Masquer" : "Afficher"}
            </button>
          </div>
        </label>
        {passwordsMismatch && (
          <p className="form-error">Les mots de passe ne correspondent pas</p>
        )}
        <label>
          Profil
          <select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
          >
            {ROLES.map((role) => (
              <option key={role.value} value={role.value}>
                {role.label}
              </option>
            ))}
          </select>
        </label>
        <label className="form-checkbox">
          <input
            type="checkbox"
            checked={form.besoin_pmr}
            onChange={(e) => setForm({ ...form, besoin_pmr: e.target.checked })}
          />
          Besoin d'accessibilité PMR
        </label>
        {error && <p className="form-error">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? "Création…" : "Créer le compte"}
        </button>
      </form>
    </div>
  );
}
