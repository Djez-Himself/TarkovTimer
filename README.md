# Tarkov Trader Timers

Une application de bureau compacte et élégante pour suivre les temps de restock des marchands de Escape from Tarkov.

## ✨ Fonctionnalités

- 🎯 Interface graphique moderne et compacte
- 🕒 Timers en temps réel pour chaque marchand
- 🔔 Alertes sonores personnalisées :
  - Son "Yeet" à 10 minutes du restock
  - Son de chasse d'eau au début du restock
- 🎨 Indicateurs visuels intelligents :
  - Cadre rouge quand il reste moins de 10 minutes
  - Cadre bleu pendant le reset
  - Design compact et optimisé
- ⚡ Fonctionnalités avancées :
  - Mise à jour automatique toutes les 2 secondes
  - Rafraîchissement manuel disponible
  - Sélection flexible des marchands à afficher
  - Affichage des heures en format local
  - Redimensionnement adaptatif (2-4 colonnes selon la taille)

## 🗂️ Structure du projet

```
TimerBiruh/
│
├── main.py              # Script principal
├── README.md           # Documentation
├── requirements.txt    # Dépendances Python
│
├── img/               # Avatars des marchands
│   ├── prapor.png
│   ├── therapute.png
│   ├── skier.png
│   ├── pissekeeper.png
│   ├── mechanic.png
│   ├── ragman.png
│   ├── jaeger.png
│   ├── fence.png
│   └── ref.png
│
├── sons/              # Sons des alertes
│   ├── Yeet-sound-effect.mp3    # Alerte 10 minutes
│   └── Toilet-flushing.mp3      # Son de reset
│
├── selection.json     # Configuration des marchands
└── app.log           # Fichier de logs
```

## 💻 Prérequis

- Python 3.8 ou supérieur
- Bibliothèques requises (voir requirements.txt)

## 🚀 Installation

1. Cloner le repository :
```bash
git clone https://github.com/votre-username/TimerBiruh.git
cd TimerBiruh
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## 📱 Utilisation

1. Lancer l'application :
```bash
python main.py
```

2. Interface intuitive :
   - Cartes compactes pour chaque marchand
   - Avatars et noms distinctifs
   - Timers précis avant restock
   - Heure locale de restock

3. Interactions :
   - Menu "Sélection Traders" pour choisir les marchands
   - Bouton "Rafraîchir" pour mise à jour manuelle
   - Redimensionnement automatique de la grille
   - Alertes sonores et visuelles configurées

## 📄 Fichiers générés

- `selection.json` : Sauvegarde des préférences d'affichage
- `app.log` : Journal des événements (nettoyé au démarrage)

## 🔧 Détails techniques

- Source des données : tarkovbot.eu
- Intervalle de mise à jour : 2 secondes
- Gestion du son : pygame
- Interface graphique : tkinter
- Traitement des images : PIL
- Gestion des dates : pytz, python-dateutil
- Requêtes réseau : requests

## 🤝 Contribution

Les contributions sont bienvenues ! Pour contribuer :
1. Forkez le projet
2. Créez une branche pour votre fonctionnalité
3. Committez vos changements
4. Poussez vers votre branche
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails. 