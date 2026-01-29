# Family Hub - Référence Rapide

**Dernière mise à jour**: 2026-01-28

## 🚀 Démarrage Rapide

```bash
cd /home/simonp/Projects/domotique/family-hub
./start-dev.sh
```

Puis ouvrir: http://192.168.1.119:5173

## 📱 URLs d'Accès

| Service | URL | Compte |
|---------|-----|--------|
| **Dashboard** | http://192.168.1.119:5173 | simon / temp123 |
| **API Backend** | http://192.168.1.119:8000 | N/A |
| **API Docs** | http://192.168.1.119:8000/api/docs | N/A |

## 👤 Comptes de Test

| Utilisateur | Mot de passe | Rôle | Accès |
|-------------|--------------|------|-------|
| simon | temp123 | admin | Tout |
| caroline | temp123 | family_adult | Domotique + Trading (lecture) |
| admin | admin123 | admin | Tout |
| kiosk | kiosk123 | kiosk | Affichage tablette |

## 🏗️ Architecture Réseau

### Machine Locale (192.168.1.119)
- **Frontend**: Port 5173 (SvelteKit)
- **Backend**: Port 8000 (FastAPI)
- **SSH Tunnel**: localhost:11883 → Jetson:1883

### ProDesk (192.168.1.113)
- **Momentum Trader V7**: systemd service
- **IBKR Gateway**: Port 4002
- **Publie MQTT**: → Jetson:1883

### Jetson (192.168.1.118)
- **MQTT Broker**: Port 1883
- **Node-RED**: Port 1880
- **Mistral Brain**: Port 5000

### Hubitat Hub (192.168.1.66)
- **Maker API**: App 274
- **Token**: 17a29aed-e45d-4d30-8640-c68adb895a84

## 🔄 Gestion des Services

### Démarrer
```bash
cd /home/simonp/Projects/domotique/family-hub
./start-dev.sh
```

### Arrêter
```bash
pkill -f "uvicorn app.main:app"
pkill -f "vite dev"
```

### Redémarrer Backend uniquement
```bash
pkill -f "uvicorn app.main:app"
cd /home/simonp/Projects/domotique/family-hub/backend
PYTHONPATH=src nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/family-hub-backend.log 2>&1 &
```

### Redémarrer Frontend uniquement
```bash
pkill -f "vite dev"
cd /home/simonp/Projects/domotique/family-hub/frontend
nohup npm run dev -- --host 0.0.0.0 > /tmp/family-hub-frontend.log 2>&1 &
```

## 📋 Logs

### Afficher les logs
```bash
# Backend
tail -f /tmp/family-hub-backend.log

# Frontend
tail -f /tmp/family-hub-frontend.log

# Dernières 50 lignes backend
tail -50 /tmp/family-hub-backend.log

# Filtrer les erreurs
tail -100 /tmp/family-hub-backend.log | grep ERROR
```

## 🔧 Tunnel SSH MQTT

### Vérifier le tunnel
```bash
ps aux | grep "ssh.*11883"
ss -tuln | grep 11883
nc -zv localhost 11883
```

### Créer le tunnel
```bash
ssh -f -N -L 11883:localhost:1883 simon@192.168.1.118
```

### Tuer le tunnel
```bash
pkill -f "ssh.*11883"
```

### Tester MQTT
```bash
# Écouter les messages momentum
mosquitto_sub -h localhost -p 11883 -t 'momentum/#' -v

# Tester depuis le Jetson directement
ssh simon@192.168.1.118 "mosquitto_sub -h localhost -t 'momentum/#' -C 5"
```

## 🐛 Troubleshooting

### Backend ne démarre pas
```bash
# Voir les erreurs
tail -50 /tmp/family-hub-backend.log

# Vérifier le port 8000
ss -tuln | grep 8000

# Tuer processus ghost et redémarrer
pkill -9 -f "uvicorn app.main"
cd /home/simonp/Projects/domotique/family-hub/backend
PYTHONPATH=src uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### MQTT connection refused
```bash
# 1. Vérifier le tunnel existe
ps aux | grep "ssh.*11883"

# 2. Si absent, le créer
ssh -f -N -L 11883:localhost:1883 simon@192.168.1.118

# 3. Vérifier le broker Jetson
ssh simon@192.168.1.118 "ss -tuln | grep 1883"

# 4. Tester la connexion
nc -zv localhost 11883

# 5. Redémarrer backend
pkill -f "uvicorn app.main"
cd /home/simonp/Projects/domotique/family-hub/backend
PYTHONPATH=src nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/family-hub-backend.log 2>&1 &
```

### Frontend ne charge pas
```bash
# Voir les logs
tail -50 /tmp/family-hub-frontend.log

# Vérifier le port 5173
ss -tuln | grep 5173

# Rebuild node_modules
cd /home/simonp/Projects/domotique/family-hub/frontend
npm install

# Redémarrer
npm run dev -- --host 0.0.0.0
```

### Pas de données trading
```bash
# 1. Vérifier le trader publie sur MQTT
ssh simon@192.168.1.113 "tail -50 ~/Projects/momentum_trader_v7/main/logs/trader-service.log | grep MQTT"

# 2. Vérifier le service trader
ssh simon@192.168.1.113 "systemctl --user status momentum-trader"

# 3. Vérifier les topics MQTT
mosquitto_sub -h localhost -p 11883 -t 'momentum/#' -v

# 4. Vérifier la config .env du trader
ssh simon@192.168.1.113 "grep MQTT ~/Projects/momentum_trader_v7/main/.env"
```

## 🗄️ Base de Données

**Location**: `/home/simonp/Projects/domotique/family-hub/backend/family_hub.db`

### Accéder à la DB
```bash
cd /home/simonp/Projects/domotique/family-hub/backend
sqlite3 family_hub.db

# Lister les tables
.tables

# Voir les utilisateurs
SELECT * FROM users;

# Voir les logs d'activité récents
SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 10;

# Quitter
.quit
```

## 🔐 Sécurité

### Changer un mot de passe
```bash
cd /home/simonp/Projects/domotique/family-hub/backend
PYTHONPATH=src python3 -c "
from app.core.security import get_password_hash
print(get_password_hash('nouveau_mot_de_passe'))
"

# Puis update dans la DB
sqlite3 family_hub.db "UPDATE users SET hashed_password='<hash>' WHERE username='simon';"
```

## 📊 Monitoring

### Vérifier la santé du système
```bash
# API Health
curl http://localhost:8000/api/health | jq

# Status des services
ps aux | grep -E "uvicorn|vite" | grep -v grep

# Ports en écoute
ss -tuln | grep -E "5173|8000|11883"

# Tunnel SSH
ps aux | grep "ssh.*11883"
```

## 🎨 Développement

### Structure du Projet
```
family-hub/
├── backend/
│   ├── src/app/
│   │   ├── api/v1/          # Endpoints API
│   │   ├── core/            # Config, security
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   └── family_hub.db        # SQLite database
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api/         # API clients
│   │   │   ├── components/  # Composants Svelte
│   │   │   └── stores/      # Svelte stores
│   │   └── routes/          # Pages SvelteKit
│   └── package.json
└── start-dev.sh             # Script de démarrage
```

### Tests
```bash
# Backend tests
cd backend
PYTHONPATH=src pytest tests/ -v

# Frontend type checking
cd frontend
npm run check

# Frontend build test
npm run build
```

## 📝 Configuration

### Fichiers de configuration
- `backend/.env` - Variables d'environnement
- `backend/src/app/core/config.py` - Config application
- `frontend/vite.config.ts` - Config Vite/SvelteKit
- `frontend/tailwind.config.ts` - Config Tailwind

### Variables d'environnement (.env)
```bash
# MQTT (via SSH tunnel)
MQTT_HOST=127.0.0.1
MQTT_PORT=11883

# Hosts de référence
PRODESK_HOST=192.168.1.113
JETSON_HOST=192.168.1.118
```

## 🔗 Liens Utiles

- [README.md](README.md) - Documentation complète
- [GUIDE-TEST.md](GUIDE-TEST.md) - Guide de test
- [MVP-COMPLETE.md](MVP-COMPLETE.md) - Sprints et features
- [API Docs](http://192.168.1.119:8000/api/docs) - Swagger UI

## 📞 Support

Pour toute question, voir la documentation complète dans `README.md` ou consulter `/home/simonp/.claude/MCP.md` pour la configuration globale du système.
