#!/usr/bin/env python3
"""
kyntus_scraper.py
------------------
Se connecte au portail web Kyntus Partenaire et écrit les résultats SatCli
dans data/satcli_data.json, au format attendu par la vue "SatCli" de
index.html.

IMPORTANT — SÉCURITÉ
=====================
- Les identifiants ne sont JAMAIS écrits en dur dans ce fichier.
  Ils sont lus depuis des variables d'environnement (KYNTUS_USER / KYNTUS_PASS),
  elles-mêmes définies soit dans un fichier local ".env" (jamais commité sur
  Git — voir .gitignore fourni), soit dans les "Secrets" d'une Action GitHub
  si vous automatisez l'exécution sur GitHub.
- Ne collez jamais votre mot de passe directement dans ce script.
- Puisque le mot de passe a été partagé en clair dans une conversation,
  il est recommandé de le changer sur le portail Kyntus par précaution.

CE QUI MANQUE POUR QUE ÇA FONCTIONNE
=====================================
Ce script est un GABARIT fonctionnel (structure Playwright complète, gestion
d'erreurs, export JSON) mais les sélecteurs CSS du formulaire de connexion et
du tableau de résultats sont des exemples à adapter : je n'ai pas accès à
l'URL réelle du portail web Kyntus Partenaire (seul un exécutable Windows a
été fourni, pas un lien web). Étapes pour terminer l'intégration :

  1. Renseignez KYNTUS_LOGIN_URL ci-dessous (ou en variable d'environnement).
  2. Ouvrez cette page dans un navigateur, faites clic-droit > Inspecter sur
     le champ identifiant, le champ mot de passe et le bouton de connexion,
     et remplacez les sélecteurs marqués "# TODO" plus bas.
  3. Faites de même pour la page de résultats SatCli et le tableau de données.
  4. Lancez : python kyntus_scraper.py

INSTALLATION
============
    python -m venv venv
    source venv/bin/activate        # (ou venv\\Scripts\\activate sous Windows)
    pip install -r requirements.txt
    playwright install chromium

EXÉCUTION
=========
    export KYNTUS_USER="moba.fibre"      # ou définissez-les dans .env
    export KYNTUS_PASS="********"
    python kyntus_scraper.py
"""

import os
import re
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- Chargement optionnel d'un fichier .env local (jamais commité) --------
def charger_dotenv(chemin=".env"):
    p = Path(chemin)
    if not p.exists():
        return
    for ligne in p.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, _, valeur = ligne.partition("=")
        os.environ.setdefault(cle.strip(), valeur.strip().strip('"').strip("'"))

charger_dotenv()

KYNTUS_LOGIN_URL = os.environ.get("KYNTUS_LOGIN_URL", "https://REMPLACER-PAR-URL-REELLE.kyntus.fr/login")
KYNTUS_USER = os.environ.get("KYNTUS_USER")
KYNTUS_PASS = os.environ.get("KYNTUS_PASS")

SORTIE_JSON = Path(__file__).resolve().parent.parent / "data" / "satcli_data.json"


def recuperer_donnees_satcli():
    """Se connecte à Kyntus Partenaire et retourne la liste des résultats
    par technicien : [{"nom": str, "total": int, "reussies": int, "taux": float}, ...]
    """
    from playwright.sync_api import sync_playwright

    if not KYNTUS_USER or not KYNTUS_PASS:
        raise RuntimeError(
            "Identifiants manquants : définissez KYNTUS_USER et KYNTUS_PASS "
            "(variables d'environnement ou fichier .env local)."
        )

    resultats = []

    with sync_playwright() as p:
        navigateur = p.chromium.launch(headless=True)
        page = navigateur.new_page()

        # 1. Connexion ------------------------------------------------------
        page.goto(KYNTUS_LOGIN_URL, wait_until="networkidle")

        # TODO : adapter ces sélecteurs à la vraie page de connexion Kyntus.
        page.fill('input[name="username"]', KYNTUS_USER)      # TODO
        page.fill('input[name="password"]', KYNTUS_PASS)      # TODO
        page.click('button[type="submit"]')                   # TODO
        page.wait_for_load_state("networkidle")

        # Vérification basique que la connexion a réussi.
        if page.locator("text=Identifiant ou mot de passe incorrect").count() > 0:  # TODO
            navigateur.close()
            raise RuntimeError("Échec de connexion à Kyntus Partenaire : identifiants refusés.")

        # 2. Aller sur la page des résultats SatCli --------------------------
        # TODO : remplacer par l'URL réelle de la page de résultats/statistiques.
        page.goto(KYNTUS_LOGIN_URL.rsplit("/", 1)[0] + "/satcli", wait_until="networkidle")

        # 3. Extraire le tableau ---------------------------------------------
        # Exemple générique : on suppose un tableau HTML <table> avec une ligne
        # d'en-tête (Technicien / Total / Réussies / Taux) et une ligne par
        # technicien. Adaptez selon la structure réelle observée dans l'inspecteur.
        lignes = page.locator("table tbody tr")  # TODO
        nb = lignes.count()
        for i in range(nb):
            cellules = lignes.nth(i).locator("td")
            if cellules.count() < 3:
                continue
            nom = cellules.nth(0).inner_text().strip()               # TODO
            total_txt = cellules.nth(1).inner_text().strip()          # TODO
            reussies_txt = cellules.nth(2).inner_text().strip()       # TODO

            total = int(re.sub(r"[^\d]", "", total_txt) or 0)
            reussies = int(re.sub(r"[^\d]", "", reussies_txt) or 0)
            taux = round(1000 * reussies / total) / 10 if total else 0.0

            if nom:
                resultats.append({
                    "nom": nom,
                    "total": total,
                    "reussies": reussies,
                    "echouees": total - reussies,
                    "taux": taux,
                })

        navigateur.close()

    return resultats


def ecrire_json(resultats):
    SORTIE_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "techniciens": resultats,
    }
    SORTIE_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Données écrites dans {SORTIE_JSON} ({len(resultats)} technicien(s))")


def main():
    try:
        resultats = recuperer_donnees_satcli()
        ecrire_json(resultats)
    except ImportError:
        print(
            "Playwright n'est pas installé. Lancez :\n"
            "  pip install -r requirements.txt\n"
            "  playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"⚠ Erreur : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
