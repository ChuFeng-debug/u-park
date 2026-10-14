export default function ConfidentialitePage() {
  return (
    <article className="panel prose">
      <h1>Données personnelles</h1>
      <p>
        U-Park est une preuve de concept réalisée dans le cadre d'une SAE de l'Université Gustave
        Eiffel. Elle fonctionne avec des <strong>données fictives</strong>.
      </p>

      <h2>Ce que nous collectons</h2>
      <ul>
        <li>Email, nom et prénom : pour vous identifier.</li>
        <li>Mot de passe : stocké sous forme hachée, jamais lisible.</li>
        <li>Rôle (étudiant, personnel, visiteur) : pour appliquer les règles d'accès aux zones.</li>
        <li>Besoin d'une place PMR : facultatif et déclaratif, aucun justificatif n'est stocké.</li>
        <li>Vos réservations, passages, demandes et signalements : pour rendre le service.</li>
      </ul>
      <p>Aucune plaque d'immatriculation ni aucun numéro étudiant n'est demandé.</p>

      <h2>À quoi elles servent</h2>
      <p>
        À réserver une place, à vérifier vos droits d'accès et à produire des statistiques
        d'occupation <strong>agrégées</strong> pour l'administration du campus.
      </p>

      <h2>Traçabilité</h2>
      <p>
        Les actions importantes (connexion, réservation, annulation…) sont journalisées avec un
        identifiant technique, sans votre nom ni votre email, pour la sécurité du service.
      </p>

      <h2>Vos droits</h2>
      <p>Depuis la page « Mon compte », vous pouvez à tout moment :</p>
      <ul>
        <li>corriger votre nom, prénom et besoin PMR ;</li>
        <li>télécharger toutes vos données au format JSON ;</li>
        <li>
          supprimer votre compte : il est alors anonymisé (plus aucune donnée vous identifiant) et vos
          réservations à venir sont annulées.
        </li>
      </ul>
    </article>
  );
}
