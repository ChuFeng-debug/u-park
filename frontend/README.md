# Frontend — U-Park

Application React + TypeScript + Vite, consommant l'API U-Park.

## Démarrage (via Docker Compose, depuis la racine du projet)

```bash
docker compose up -d --build
```

L'application est disponible sur http://localhost:5173.

## Développement local (hors Docker)

```bash
cp .env.example .env
npm install
npm run dev
```

## Structure

```
src/
├── main.tsx / App.tsx   # point d'entrée, routes
├── api/                 # client HTTP (axios) et appels par domaine
├── contexts/             # AuthContext (utilisateur connecté, token)
├── components/            # Layout, ProtectedRoute
├── pages/                 # Login, Register, Catalogue, Reservations
└── types/                 # types partagés avec l'API
```

## Pages disponibles

- `/` — catalogue des parkings/zones/places, disponibilité en temps réel, réservation (si connecté)
- `/login`, `/register` — authentification
- `/reservations` — réservations de l'utilisateur connecté, annulation

## Build de production

```bash
npm run build
```
