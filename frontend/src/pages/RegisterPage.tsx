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
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
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
          <input
            type="password"
            minLength={8}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </label>
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
