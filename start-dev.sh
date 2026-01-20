#!/bin/bash
# Family Hub - Script de démarrage en développement

echo "🚀 Démarrage de Family Hub..."

# Arrêter les processus existants
echo "🛑 Arrêt des processus existants..."
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "vite dev" 2>/dev/null
sleep 2

# Démarrer le backend
echo "🔧 Démarrage du backend (port 8000)..."
cd backend
PYTHONPATH=src nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/family-hub-backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Attendre que le backend soit prêt
echo "⏳ Attente du backend..."
sleep 3

# Vérifier le backend
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend prêt (PID: $BACKEND_PID)"
else
    echo "❌ Erreur: Backend ne répond pas"
    exit 1
fi

# Démarrer le frontend
echo "🎨 Démarrage du frontend (port 5173)..."
cd frontend
nohup npm run dev -- --host 0.0.0.0 > /tmp/family-hub-frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Attendre que le frontend soit prêt
echo "⏳ Attente du frontend..."
sleep 5

echo ""
echo "🎉 Family Hub démarré!"
echo ""
echo "📱 Frontend:  http://localhost:5173"
echo "🔌 Backend:   http://localhost:8000"
echo "📖 API Docs:  http://localhost:8000/api/docs"
echo ""
echo "👤 Comptes de test:"
echo "   - simon / temp123 (admin)"
echo "   - caroline / temp123 (adult)"
echo "   - admin / admin123 (admin)"
echo "   - kiosk / kiosk123 (kiosk)"
echo ""
echo "📋 Logs:"
echo "   - Backend:  tail -f /tmp/family-hub-backend.log"
echo "   - Frontend: tail -f /tmp/family-hub-frontend.log"
echo ""
echo "🛑 Pour arrêter:"
echo "   pkill -f 'uvicorn app.main:app'"
echo "   pkill -f 'vite dev'"
echo ""
