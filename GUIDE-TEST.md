# Guide de Test - Family Hub

## Démarrage Rapide

```bash
cd /home/simonp/Projects/domotique/family-hub
./start-dev.sh
```

Puis ouvre http://localhost:5173 dans ton navigateur.

## Comptes de Test

| Utilisateur | Mot de passe | Rôle | Thème |
|-------------|--------------|------|-------|
| `simon` | `temp123` | admin | simon |
| `caroline` | `temp123` | adult | caroline |
| `admin` | `admin123` | admin | system |
| `kiosk` | `kiosk123` | kiosk | kiosk |

## Tests à Effectuer

### 1. Authentification ✅

**Test 1.1 - Login Simon**
1. Va sur http://localhost:5173
2. Entre `simon` / `temp123`
3. Clique "Se connecter"
4. ✅ Tu devrais voir le dashboard

**Test 1.2 - Logout**
1. Clique sur ton nom en haut à droite
2. Clique "Déconnexion"
3. ✅ Tu devrais retourner à la page de login

**Test 1.3 - Mauvais mot de passe**
1. Entre `simon` / `wrong`
2. ✅ Tu devrais voir "Invalid username or password"

### 2. Dashboard & Devices 📱

**Test 2.1 - Voir les devices**
1. Connecte-toi avec `simon` / `temp123`
2. ✅ Tu devrais voir des cartes de devices (lumières, capteurs)
3. ✅ Le statut (online/offline) devrait s'afficher

**Test 2.2 - Contrôler une lumière**
1. Trouve une carte de lumière
2. Clique sur le bouton toggle
3. ✅ La lumière devrait changer d'état (si Hubitat connecté)

**Test 2.3 - WebSocket temps réel**
1. Dans un autre onglet, change un device via Hubitat
2. ✅ Le dashboard devrait se mettre à jour automatiquement

### 3. Température 🌡️

**Test 3.1 - Voir température**
1. Va dans l'onglet "Climat"
2. ✅ Tu devrais voir les lectures de température

**Test 3.2 - Ajuster thermostat**
1. Trouve le widget de température avec setpoint
2. Clique "Modifier"
3. Ajuste avec le slider
4. Clique "Enregistrer"
5. ✅ La consigne devrait changer

**Test 3.3 - Raccourcis température**
1. Clique sur "J'ai frette" ou "J'ai chaud"
2. ✅ La température devrait s'ajuster

### 4. Modes 🎭

**Test 4.1 - Activer un mode**
1. Va dans l'onglet "Modes"
2. Clique sur "Mode Nuit" ou "Mode Jour"
3. ✅ Le mode devrait s'activer
4. ✅ Les actions du mode devraient s'exécuter

**Test 4.2 - Voir le mode actif**
1. ✅ Le mode actif devrait apparaître en haut du dashboard

**Test 4.3 - Créer un mode (admin)**
1. Va dans Admin > Modes
2. Clique "Nouveau mode"
3. Entre nom, icône, actions
4. Sauvegarde
5. ✅ Le nouveau mode devrait apparaître

### 5. Thèmes 🎨

**Test 5.1 - Changer de thème**
1. Va dans "Paramètres"
2. Sélectionne un thème (Light, Dark, Simon, Caroline, Kids)
3. ✅ Les couleurs devraient changer immédiatement

**Test 5.2 - Taille de police**
1. Dans Paramètres, change la taille de police
2. ✅ Le texte devrait s'agrandir/rétrécir

**Test 5.3 - Accessibilité**
1. Active "Réduire les mouvements"
2. ✅ Les animations devraient être réduites

### 6. Kiosk Mode 📺

**Test 6.1 - Accéder au kiosk**
1. Va sur http://localhost:5173/kiosk
2. ✅ Tu devrais voir l'horloge plein écran
3. ✅ Les devices favoris devraient s'afficher
4. ✅ Le mode actif devrait être visible

**Test 6.2 - Dimming jour/nuit**
1. Change l'heure système à 23h00
2. ✅ Le kiosk devrait être assombri
3. Change à 8h00
4. ✅ Le kiosk devrait être lumineux

### 7. Admin - Utilisateurs 👥

**Test 7.1 - Voir utilisateurs**
1. Connecte-toi avec `simon` / `temp123`
2. Va dans Admin > Utilisateurs
3. ✅ Tu devrais voir 4 utilisateurs

**Test 7.2 - Créer utilisateur**
1. Clique "Nouvel utilisateur"
2. Entre username, nom, mot de passe, rôle
3. Sauvegarde
4. ✅ L'utilisateur devrait apparaître dans la liste

**Test 7.3 - Modifier utilisateur**
1. Clique sur un utilisateur
2. Change le rôle ou le thème
3. Sauvegarde
4. ✅ Les changements devraient être appliqués

### 8. Admin - System Health 🏥

**Test 8.1 - Voir status système**
1. Va dans Admin > Santé du système
2. ✅ Tu devrais voir:
   - Status Database (healthy)
   - Status MQTT (connected/disconnected)
   - Status Hubitat (connected/disconnected)
   - Status Mistral Brain (connected/unavailable)

**Test 8.2 - Devices health**
1. ✅ Tu devrais voir le nombre de devices online/offline
2. ✅ Les devices avec batterie faible devraient être listés

### 9. Admin - Integrations 🔌

**Test 9.1 - Status intégrations**
1. Va dans Admin > Intégrations
2. ✅ Tu devrais voir le status de:
   - Hubitat (connected/error)
   - MQTT (connected/disconnected)
   - Mistral Brain (connected/unavailable)

### 10. Admin - Activity Logs 📋

**Test 10.1 - Voir les logs**
1. Va dans Admin > Logs d'activité
2. ✅ Tu devrais voir les actions récentes (login, device_on, etc.)

**Test 10.2 - Filtrer les logs**
1. Filtre par action "login"
2. ✅ Tu devrais voir seulement les connexions

### 11. Config Export/Import 💾

**Test 11.1 - Exporter config**
1. Va dans Admin > Configuration
2. Clique "Exporter YAML"
3. ✅ Un fichier `family-hub-config-YYYY-MM-DD.yaml` devrait se télécharger

**Test 11.2 - Importer config**
1. Clique "Importer YAML"
2. Sélectionne le fichier exporté
3. ✅ Tu devrais voir "Import successful" avec les stats

## Tests Backend (API)

```bash
cd backend

# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run specific test
PYTHONPATH=src pytest tests/test_auth.py -v

# Run with coverage
PYTHONPATH=src pytest tests/ --cov=app --cov-report=html
```

## Tests Frontend (Types)

```bash
cd frontend

# Type checking
npm run check

# Build
npm run build

# Preview build
npm run preview
```

## Troubleshooting

### Le login ne fonctionne pas
- Vérifie que le backend tourne: `curl http://localhost:8000/api/health`
- Vérifie que le frontend tourne: `curl http://localhost:5173`
- Vérifie les logs: `tail -f /tmp/family-hub-backend.log`
- Réinitialise la DB: `rm backend/family_hub.db` puis redémarre

### Les devices ne s'affichent pas
- Vérifie MQTT: `mosquitto_sub -h 192.168.1.118 -t 'hubitat/#' -v`
- Vérifie Hubitat Maker API: `curl http://192.168.1.66/apps/api/274/devices?access_token=17a29aed-e45d-4d30-8640-c68adb895a84`

### Le WebSocket ne fonctionne pas
- Ouvre la console du navigateur (F12)
- Cherche des erreurs WebSocket
- Vérifie que le backend MQTT service est démarré

### Les cookies ne fonctionnent pas
- Vérifie que tu utilises http://localhost:5173 (pas 5174 ou 5175)
- Le proxy Vite est configuré pour `/api` → `http://localhost:8000`
- Les cookies sont httpOnly avec samesite=none

## Architecture Technique

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (SvelteKit 5 + Tailwind 4) - Port 5173       │
│  - Proxy /api → Backend                                 │
│  - PWA enabled                                          │
│  - 7 themes, responsive                                 │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP + WebSocket
┌─────────────────▼───────────────────────────────────────┐
│  Backend (FastAPI) - Port 8000                          │
│  - JWT auth (httpOnly cookies)                          │
│  - SQLite + SQLAlchemy Core                             │
│  - MQTT client → Hubitat                                │
│  - WebSocket server                                     │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┬─────────────┐
        │                   │             │
┌───────▼────────┐  ┌──────▼──────┐  ┌──▼──────────────┐
│ MQTT Broker    │  │ Hubitat Hub │  │ Mistral Brain   │
│ 192.168.1.118  │  │ 192.168.1.66│  │ 192.168.1.118   │
│ Port 1883      │  │ Maker API   │  │ Port 5000       │
└────────────────┘  └─────────────┘  └─────────────────┘
```

## URLs Importantes

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Kiosk: http://localhost:5173/kiosk

## Logs

- Backend: `/tmp/family-hub-backend.log`
- Frontend: `/tmp/family-hub-frontend.log`
