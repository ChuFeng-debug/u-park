-- U-Park - Schéma relationnel
-- Fusion du MCD initial et du schéma normalisé (rôles, blocages, demandes visiteurs, traçabilité)

CREATE TABLE role (
    code_role          VARCHAR(20)  NOT NULL,
    libelle_role       VARCHAR(50)  NOT NULL,
    description_role   VARCHAR(255),
    CONSTRAINT pk_role PRIMARY KEY (code_role)
);

CREATE TABLE utilisateur (
    id_utilisateur        INT          NOT NULL,
    email                 VARCHAR(150) NOT NULL,
    mot_de_passe_hash     VARCHAR(255) NOT NULL,
    nom_utilisateur       VARCHAR(80)  NOT NULL,
    prenom_utilisateur    VARCHAR(80)  NOT NULL,
    statut_compte         VARCHAR(20)  NOT NULL,
    besoin_pmr            BOOLEAN      NOT NULL DEFAULT FALSE,
    date_creation_compte  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_utilisateur PRIMARY KEY (id_utilisateur),
    CONSTRAINT uq_utilisateur_email UNIQUE (email)
);

CREATE TABLE attribution_role (
    id_utilisateur    INT         NOT NULL,
    code_role         VARCHAR(20) NOT NULL,
    date_attribution  DATE        NOT NULL,
    CONSTRAINT pk_attribution_role PRIMARY KEY (id_utilisateur, code_role),
    CONSTRAINT fk_attrib_utilisateur FOREIGN KEY (id_utilisateur) REFERENCES utilisateur (id_utilisateur),
    CONSTRAINT fk_attrib_role FOREIGN KEY (code_role) REFERENCES role (code_role)
);

CREATE TABLE parking (
    id_parking            INT          NOT NULL,
    nom_parking           VARCHAR(80)  NOT NULL,
    localisation_parking  VARCHAR(150) NOT NULL,
    description_parking   VARCHAR(255),
    CONSTRAINT pk_parking PRIMARY KEY (id_parking)
);

CREATE TABLE zone (
    id_zone             INT         NOT NULL,
    id_parking          INT         NOT NULL,
    nom_zone            VARCHAR(80) NOT NULL,
    capacite_theorique  INT         NOT NULL,
    heure_ouverture     TIME        NOT NULL,
    heure_fermeture     TIME        NOT NULL,
    zone_active         BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_zone PRIMARY KEY (id_zone),
    CONSTRAINT fk_zone_parking FOREIGN KEY (id_parking) REFERENCES parking (id_parking)
);

CREATE TABLE place (
    id_place      INT         NOT NULL,
    id_zone       INT         NOT NULL,
    numero_place  VARCHAR(10) NOT NULL,
    type_place    VARCHAR(20) NOT NULL,
    etat_place    VARCHAR(20) NOT NULL,
    CONSTRAINT pk_place PRIMARY KEY (id_place),
    CONSTRAINT fk_place_zone FOREIGN KEY (id_zone) REFERENCES zone (id_zone)
);

-- Réservation liée directement à une place (simplicité pour le MVP :
-- le taux d'occupation et le tableau de bord se calculent sans étape
-- d'affectation intermédiaire). Le type de place demandé est déjà
-- porté par place.type_place.
CREATE TABLE reservation (
    id_reservation      INT       NOT NULL,
    id_utilisateur      INT       NOT NULL,
    id_place            INT       NOT NULL,
    date_debut          TIMESTAMP NOT NULL,
    date_fin             TIMESTAMP NOT NULL,
    statut_reservation  VARCHAR(20) NOT NULL,
    date_creation_resa  TIMESTAMP NOT NULL,
    date_annulation     TIMESTAMP,
    motif_annulation    VARCHAR(255),
    CONSTRAINT pk_reservation PRIMARY KEY (id_reservation),
    CONSTRAINT fk_resa_utilisateur FOREIGN KEY (id_utilisateur) REFERENCES utilisateur (id_utilisateur),
    CONSTRAINT fk_resa_place FOREIGN KEY (id_place) REFERENCES place (id_place)
);

CREATE TABLE regle_acces (
    id_regle             INT          NOT NULL,
    id_zone              INT          NOT NULL,
    libelle_regle        VARCHAR(100) NOT NULL,
    niveau_priorite      INT          NOT NULL,
    date_debut_validite  DATE         NOT NULL,
    date_fin_validite    DATE,
    regle_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_regle_acces PRIMARY KEY (id_regle),
    CONSTRAINT fk_regle_zone FOREIGN KEY (id_zone) REFERENCES zone (id_zone)
);

CREATE TABLE cible_role (
    id_regle   INT         NOT NULL,
    code_role  VARCHAR(20) NOT NULL,
    CONSTRAINT pk_cible_role PRIMARY KEY (id_regle, code_role),
    CONSTRAINT fk_cible_regle FOREIGN KEY (id_regle) REFERENCES regle_acces (id_regle),
    CONSTRAINT fk_cible_role FOREIGN KEY (code_role) REFERENCES role (code_role)
);

-- Blocage d'une zone par un administrateur (critère d'acceptation :
-- "un administrateur peut bloquer une zone et voir l'impact sur les
-- disponibilités").
CREATE TABLE blocage (
    id_blocage          INT          NOT NULL,
    id_zone             INT          NOT NULL,
    id_utilisateur      INT          NOT NULL,
    motif_blocage       VARCHAR(255) NOT NULL,
    date_debut_blocage  TIMESTAMP    NOT NULL,
    date_fin_blocage    TIMESTAMP    NOT NULL,
    CONSTRAINT pk_blocage PRIMARY KEY (id_blocage),
    CONSTRAINT fk_blocage_zone FOREIGN KEY (id_zone) REFERENCES zone (id_zone),
    CONSTRAINT fk_blocage_utilisateur FOREIGN KEY (id_utilisateur) REFERENCES utilisateur (id_utilisateur)
);

-- Demande de place temporaire par un visiteur, validée par un
-- administrateur (MVP : "valider des demandes visiteurs").
CREATE TABLE demande_visiteur (
    id_demande              INT          NOT NULL,
    id_demandeur            INT          NOT NULL,
    id_administrateur       INT,
    id_reservation          INT,
    date_demande            TIMESTAMP    NOT NULL,
    date_visite_souhaitee   TIMESTAMP    NOT NULL,
    motif_demande           VARCHAR(255) NOT NULL,
    statut_demande          VARCHAR(20)  NOT NULL,
    date_traitement         TIMESTAMP,
    commentaire_traitement  VARCHAR(255),
    CONSTRAINT pk_demande_visiteur PRIMARY KEY (id_demande),
    CONSTRAINT uq_demande_reservation UNIQUE (id_reservation),
    CONSTRAINT fk_demande_demandeur FOREIGN KEY (id_demandeur) REFERENCES utilisateur (id_utilisateur),
    CONSTRAINT fk_demande_admin FOREIGN KEY (id_administrateur) REFERENCES utilisateur (id_utilisateur),
    CONSTRAINT fk_demande_reservation FOREIGN KEY (id_reservation) REFERENCES reservation (id_reservation)
);

-- Incident : signalé par un utilisateur, traité (optionnellement) par
-- un administrateur -- les deux rôles sont distincts.
CREATE TABLE incident (
    id_incident               INT          NOT NULL,
    id_zone                   INT          NOT NULL,
    id_utilisateur_signalement INT         NOT NULL,
    id_utilisateur_traitant   INT,
    description_incident      VARCHAR(500) NOT NULL,
    priorite_incident         VARCHAR(20)  NOT NULL,
    statut_incident           VARCHAR(20)  NOT NULL,
    date_signalement          TIMESTAMP    NOT NULL,
    date_resolution           TIMESTAMP,
    CONSTRAINT pk_incident PRIMARY KEY (id_incident),
    CONSTRAINT fk_incident_zone FOREIGN KEY (id_zone) REFERENCES zone (id_zone),
    CONSTRAINT fk_incident_signalement FOREIGN KEY (id_utilisateur_signalement) REFERENCES utilisateur (id_utilisateur),
    CONSTRAINT fk_incident_traitant FOREIGN KEY (id_utilisateur_traitant) REFERENCES utilisateur (id_utilisateur)
);

-- Journal d'actions (exigence RGPD / traçabilité du cahier des
-- charges).
CREATE TABLE trace (
    id_trace           INT         NOT NULL,
    id_utilisateur     INT         NOT NULL,
    horodatage         TIMESTAMP   NOT NULL,
    type_action        VARCHAR(50) NOT NULL,
    entite_cible       VARCHAR(50) NOT NULL,
    identifiant_cible  INT         NOT NULL,
    detail_action      VARCHAR(255),
    CONSTRAINT pk_trace PRIMARY KEY (id_trace),
    CONSTRAINT fk_trace_utilisateur FOREIGN KEY (id_utilisateur) REFERENCES utilisateur (id_utilisateur)
);
