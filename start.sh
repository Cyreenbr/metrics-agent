#!/bin/bash
# Script de démarrage rapide de l'agent Metrics
#
# Usage: ./start.sh

set -e

echo "======================================"
echo "  Metrics Agent - Démarrage"
echo "======================================"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier Python
echo -e "${YELLOW}[1/5]${NC} Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python $(python3 --version) trouvé"

# 2. Créer l'environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[2/5]${NC} Création de l'environnement virtuel..."
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Environnement virtuel créé"
else
    echo -e "${YELLOW}[2/5]${NC} Environnement virtuel existant trouvé"
fi

# 3. Activer l'environnement virtuel
echo -e "${YELLOW}[3/5]${NC} Activation de l'environnement virtuel..."
source venv/bin/activate

# 4. Installer les dépendances
echo -e "${YELLOW}[4/5]${NC} Installation des dépendances..."
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Dépendances installées"

# 5. Créer le répertoire de logs
mkdir -p logs

# 6. Vérifier Prometheus
echo -e "${YELLOW}[5/5]${NC} Vérification de Prometheus..."
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo -e "${GREEN}✓${NC} Prometheus accessible sur http://localhost:9090"
else
    echo -e "${YELLOW}⚠${NC}  Prometheus n'est pas accessible"
    echo "   Lancez 'docker-compose up -d' pour démarrer Prometheus"
    echo ""
    read -p "Voulez-vous démarrer Prometheus maintenant ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose up -d
        echo "Attente du démarrage de Prometheus..."
        sleep 5
    fi
fi

echo ""
echo "======================================"
echo -e "${GREEN}Prêt à démarrer !${NC}"
echo "======================================"
echo ""
echo "Lancement de l'agent..."
echo ""

# Démarrer l'agent
python3 -m src.main