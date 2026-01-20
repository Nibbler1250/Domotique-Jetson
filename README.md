# Family Hub 🏠

Application de domotique familiale pour contrôler Hubitat, gérer les modes et personnaliser l'expérience par utilisateur.

## ✨ Fonctionnalités

### Pour Toute la Famille
- 🎨 **Thèmes personnalisés** - 7 thèmes (System, Light, Dark, Simon, Caroline, Kids, Kiosk)
- 📱 **Dashboard temps réel** - Statut des devices via MQTT + WebSocket
- 🌡️ **Contrôle climat** - Température, thermostats, raccourcis
- 💡 **Contrôle lumières** - Toggle, dimmer, par pièce
- 🎭 **Modes 1-clic** - Mode Nuit, Matin, Souper, etc.
- 📺 **Kiosk mode** - Affichage tablette 24/7 avec dimming jour/nuit

### Pour les Enfants
- 🔒 **Permissions** - Contrôle limité aux devices autorisés
- 🎨 **Thème Kids** - Interface adaptée
- 👤 **Profils** - Paramètres personnalisés par enfant

### Pour les Administrateurs
- 👥 **Gestion utilisateurs** - Créer, modifier, désactiver
- 🏥 **Santé système** - Monitoring Database, MQTT, Hubitat, Brain
- 📊 **Logs d'activité** - Traçabilité des actions
- 🔧 **Gestion automations** - Voir, activer/désactiver, déclencher
- 💾 **Export/Import** - Backup configuration en YAML

## 🚀 Démarrage Rapide

```bash
cd /home/simonp/Projects/domotique/family-hub
./start-dev.sh
```

Puis ouvre http://localhost:5173

**Comptes de test:**
- `simon` / `temp123` (admin)
- `caroline` / `temp123` (adult)
- `admin` / `admin123` (admin)
- `kiosk` / `kiosk123` (kiosk)

## 📖 Documentation

- [Guide de Test](GUIDE-TEST.md) - Tests manuels et automatisés
- [API Docs](http://localhost:8000/api/docs) - Documentation Swagger
- [Sprint Planning](_bmad-output/planning-artifacts/sprint-planning.md) - Plan de développement

## 🏗️ Architecture

### Stack Technique

**Frontend:**
- SvelteKit 5 (Svelte 5 runes)
- Tailwind CSS 4
- PWA (Vite PWA)
- TypeScript

**Backend:**
- FastAPI
- SQLAlchemy Core (async)
- SQLite (aiosqlite)
- MQTT (aiomqtt)
- JWT auth (httpOnly cookies)

**Infrastructure:**
- MQTT Broker: Mosquitto (Jetson 192.168.1.118:1883)
- Hubitat Hub: 192.168.1.66 (Maker API 274)
- Mistral Brain: Jetson 192.168.1.118:5000
- Node-RED: Jetson 192.168.1.118:1880

### Architecture Système

```
┌─────────────────────────────────────┐
│  Frontend (SvelteKit 5)             │
│  Port 5173                          │
│  - PWA, 7 themes, responsive        │
└──────────────┬──────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼──────────────────────┐
│  Backend (FastAPI)                  │
│  Port 8000                          │
│  - JWT auth, SQLite, MQTT           │
└──────┬───────┬──────────┬───────────┘
       │       │          │
   MQTT│   Maker API  Brain API
       │       │          │
┌──────▼───┐ ┌▼─────────┐ ┌▼──────────┐
│ Mosquitto│ │ Hubitat  │ │  Mistral  │
│  :1883   │ │  :66     │ │  Brain    │
└──────────┘ └──────────┘ └───────────┘
```

## 📁 Structure du Projet

```
family-hub/
├── backend/
│   ├── src/app/
│   │   ├── api/v1/          # Endpoints API
│   │   ├── core/            # Config, security, response
│   │   ├── db/              # Database
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── tests/               # Tests pytest
│   └── family_hub.db        # SQLite database
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/         # API clients
│   │   │   ├── components/  # Composants Svelte
│   │   │   ├── stores/      # Svelte stores
│   │   │   └── types/       # TypeScript types
│   │   └── routes/          # Pages SvelteKit
│   └── static/              # Assets statiques
├── start-dev.sh             # Script de démarrage
├── GUIDE-TEST.md            # Guide de test
└── README.md                # Ce fichier
```

## 🧪 Tests

### Backend (18 tests)

```bash
cd backend
PYTHONPATH=src pytest tests/ -v
```

**Tests inclus:**
- ✅ Auth (login, logout, refresh, current user)
- ✅ Health endpoints
- ✅ Kiosk auto-login
- ✅ User CRUD

### Frontend

```bash
cd frontend
npm run check     # Type checking
npm run build     # Build production
```

## 🔧 Développement

### Backend

```bash
cd backend
PYTHONPATH=src uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Le proxy Vite redirige `/api` vers `http://localhost:8000` pour éviter les problèmes CORS.

## 📊 MVP Complété (6 Sprints)

| Sprint | Focus | Stories | Status |
|--------|-------|---------|--------|
| 1 | Foundation | 8 | ✅ Complete |
| 2 | Real-Time Dashboard | 7 | ✅ Complete |
| 3 | Climate Control | 8 | ✅ Complete |
| 4 | Permissions & Modes | 7 | ✅ Complete |
| 5 | Admin & Monitoring | 8 | ✅ Complete |
| 6 | Themes & Kiosk | 13 | ✅ Complete |
| **Total** | | **51 stories** | **112 points** |

## 🔐 Sécurité

- JWT tokens stockés dans httpOnly cookies
- CORS configuré pour localhost
- Passwords hashed avec bcrypt
- CSRF protection via SameSite cookies
- 4 rôles: admin, family_adult, family_child, kiosk

## 🌐 Réseau Local

**Machine Locale (simon-80x7):**
- IP: 192.168.1.95
- Firewall: UFW actif, allow 192.168.1.0/24

**Jetson (simon-desktop):**
- IP: 192.168.1.118 (static)
- Services: MQTT, Mistral Brain, Node-RED
- Firewall: UFW actif

**Hubitat Hub:**
- IP: 192.168.1.66
- Maker API: App 274
- Token: 17a29aed-e45d-4d30-8640-c68adb895a84

## 📝 TODO Futur

- [ ] Tests E2E avec Playwright
- [ ] Notifications push (PWA)
- [ ] Graphiques historiques température
- [ ] Scènes personnalisées par utilisateur
- [ ] Widget météo avec vraies données
- [ ] Backup automatique configuration
- [ ] Dark mode auto selon heure
- [ ] Reconnaissance vocale (optionnel)

## 🐛 Troubleshooting

Voir [GUIDE-TEST.md](GUIDE-TEST.md) section Troubleshooting.

## 📄 License

Projet personnel - Tous droits réservés

## 👨‍💻 Auteur

Simon P. - Développé avec Claude Code et BMAD workflow
