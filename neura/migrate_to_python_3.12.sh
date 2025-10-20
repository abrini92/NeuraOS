#!/bin/bash

# Migration automatique vers Python 3.12 pour Neura
# Date: 2025-10-18

set -e  # Exit on error

echo "🔧 Migration Neura vers Python 3.12"
echo "===================================="
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Erreur: pyproject.toml introuvable"
    echo "   Exécutez ce script depuis la racine du projet Neura"
    exit 1
fi

# Vérifier que Python 3.12 est installé
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 introuvable"
    echo ""
    echo "Installation:"
    echo "  brew install python@3.12"
    echo ""
    exit 1
fi

echo "✅ Python 3.12 trouvé: $(which python3.12)"
echo "   Version: $(python3.12 --version)"
echo ""

# Afficher l'environnement actuel
echo "📊 Environnement actuel:"
poetry env info 2>/dev/null || echo "   Aucun environnement actif"
echo ""

# Demander confirmation
read -p "Supprimer l'environnement actuel et recréer avec Python 3.12? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration annulée"
    exit 0
fi

echo ""
echo "🗑️  Suppression de l'environnement actuel..."
poetry env remove --all || true

echo ""
echo "🔨 Création du nouvel environnement Python 3.12..."
poetry env use python3.12

echo ""
echo "📦 Installation des dépendances..."
poetry install

echo ""
echo "✅ Migration terminée !"
echo ""
echo "📊 Nouvel environnement:"
poetry env info

echo ""
echo "🧪 Vérifications:"
echo "  Python version: $(poetry run python --version)"
echo ""

# Tester la CLI
echo "🖥️  Test CLI..."
if poetry run neura --help > /dev/null 2>&1; then
    echo "✅ CLI fonctionne !"
else
    echo "⚠️  CLI a des warnings (normal si Ollama non démarré)"
fi

echo ""
echo "✅ Migration réussie !"
echo ""
echo "Prochaines étapes:"
echo "  1. poetry run pytest           # Lancer les tests"
echo "  2. poetry run neura --help     # Tester la CLI"
echo "  3. poetry run uvicorn neura.core.api:app --reload  # Démarrer l'API"
echo ""
