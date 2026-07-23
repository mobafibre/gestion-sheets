# SatCli — synchronisation Kyntus Partenaire

## Structure attendue sur votre dépôt / hébergement

```
votre-site/
├── index.html              (plateforme principale)
├── PERF.html                (outil Performance, onglet "📈 Performance")
├── data/
│   └── satcli_data.json     (généré par le script — lu par l'onglet "🛰 SatCli")
└── kyntus_sync/
    ├── kyntus_scraper.py
    ├── requirements.txt
    ├── .env.example
    └── .gitignore
```

## 1. Utilisation immédiate (sans scraping automatique)

En attendant de finaliser le scraping automatique (voir plus bas), l'onglet
**SatCli** de `index.html` permet d'**importer manuellement** un export
Excel/CSV téléchargé depuis Kyntus Partenaire (bouton "📂 Importer un export
Kyntus"). Le tableau calcule alors les taux de réussite par technicien,
exactement comme l'outil Performance.

## 2. Mise en place du scraping automatique

Le fichier `kyntus_scraper.py` est un **gabarit fonctionnel** (connexion,
extraction, écriture JSON) mais il lui manque deux informations que je
n'avais pas :

- l'URL réelle de la page de connexion web de Kyntus Partenaire (vous m'avez
  fourni un `.exe`, qui est une application bureau — pas un site web ; je ne
  peux ni l'exécuter ni le scraper depuis ici) ;
- la structure exacte (sélecteurs) du formulaire de connexion et du tableau
  de résultats SatCli.

**Pour terminer** : ouvrez le vrai portail dans Chrome, F12 → Inspecter sur
les champs identifiant / mot de passe / bouton de connexion et sur le
tableau de résultats, puis remplacez les lignes marquées `# TODO` dans
`kyntus_scraper.py`. Si vous préférez, envoyez-moi l'URL et une capture
d'écran de la page (sans vos identifiants visibles) et je peux compléter les
sélecteurs pour vous.

### Installation locale

```bash
cd kyntus_sync
python -m venv venv
source venv/bin/activate          # venv\Scripts\activate sous Windows
pip install -r requirements.txt
playwright install chromium
cp .env.example .env              # puis éditez .env avec vos identifiants
python kyntus_scraper.py
```

Le script écrit `../data/satcli_data.json`. Rechargez `index.html` puis
cliquez sur "🔄 Actualiser (données auto)" dans l'onglet SatCli.

### Exécution récurrente (option GitHub Actions)

Si vous hébergez le site sur GitHub Pages, vous pouvez automatiser
l'exécution périodique du script via une Action GitHub, en stockant
`KYNTUS_USER` et `KYNTUS_PASS` dans **Settings → Secrets and variables →
Actions** de votre dépôt (jamais dans un fichier commité). L'Action lance
`kyntus_scraper.py`, puis commite le nouveau `data/satcli_data.json` — le
site public ne contient alors à aucun moment le mot de passe en clair.

## ⚠️ Sécurité — à faire

- Ne committez jamais `.env` (déjà exclu via `.gitignore`).
- Le mot de passe Kyntus a été transmis en clair dans notre échange : par
  précaution, changez-le sur le portail Kyntus Partenaire.
- Ne mettez jamais d'identifiant/mot de passe directement dans `index.html`
  ou `PERF.html` : ce sont des fichiers publics une fois hébergés.
