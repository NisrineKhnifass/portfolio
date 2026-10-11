# Magecart Scanner

[English version](README.en.md)

Prototype d'un outil qui **inventorie les scripts d'une page de paiement e-commerce** et **détecte quand l'un d'eux change**, pour aider à répondre aux exigences **PCI DSS 4.0 : 6.4.3** (inventaire, justification et intégrité des scripts) et **11.6.1** (détection de modification des en-têtes et du contenu des pages de paiement).

> **Statut : prototype v0.1, projet personnel en cours.** Voir [ce qui est fait et ce qui reste](#statut).

## Pourquoi

Le Magecart (web-skimming) vole les données de carte directement dans le navigateur du client, via un script tiers compromis sur la page de paiement. Les contrôles côté serveur ne voient pas ce qui s'exécute dans le navigateur. L'objectif à terme est un outil simple, utilisable par une PME sans équipe sécurité (par exemple sous forme de plugin WooCommerce).

Présentation du projet (diapositives) : [FR](docs/magecart-presentation-fr.pdf) · [EN](docs/magecart-presentation-en.pdf)

## Ce que fait la v0.1

- **Inventaire** : Playwright charge la page dans Chromium, liste les scripts externes et inline (y compris ceux chargés dynamiquement) et calcule une empreinte **SHA-256** de chacun.
- **En-têtes HTTP** : enregistre les en-têtes de sécurité de la page (CSP, HSTS, etc.).
- **Comparaison** : compare deux scans et signale les scripts ajoutés, retirés ou **modifiés**, ainsi que les en-têtes modifiés.
- **Liste blanche** : signale les scripts chargés depuis un domaine non autorisé.
- **Indicateurs** : repère des signes d'obfuscation (`eval`, `atob`, `new Function`, longues chaînes base64...). Ce sont des **signaux à examiner**, pas des preuves : du code légitime minifié peut les déclencher.

## Installation

Python 3.10 ou plus.

```bash
git clone https://github.com/NisrineKhnifass/portfolio.git
cd portfolio/project/magecart-scanner
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -e ".[dev]"
playwright install chromium
```

## Utilisation

```bash
magecart-scanner scan https://exemple.test/paiement -o scan1.json   # inventaire
magecart-scanner scan https://exemple.test/paiement -o scan2.json   # plus tard
magecart-scanner compare scan1.json scan2.json                      # différences (code retour 1 s'il y en a)
magecart-scanner check scan2.json --allowlist domaines.txt          # domaines inconnus, indicateurs
```

`domaines.txt` : un domaine autorisé par ligne (`#` pour commenter). Le domaine de la page scannée est toujours autorisé, et un domaine autorisé couvre ses sous-domaines.

> **Ne scannez que des sites qui vous appartiennent ou pour lesquels vous avez une autorisation.**

## Essayer sur le banc d'essai local

Le dossier `testbench/` contient une fausse page de paiement et un faux script tiers **inoffensif** (deux versions, dont une modifiée). Aucun vrai paiement, aucun code de vol de données.

```bash
python testbench/serve.py                                  # terminal 1 : boutique (8000) + domaine tiers (8001)

magecart-scanner scan http://127.0.0.1:8000/ -o scan1.json # terminal 2
curl http://localhost:8001/__variant/v2                    # le faux script tiers change
magecart-scanner scan http://127.0.0.1:8000/ -o scan2.json
magecart-scanner compare scan1.json scan2.json
```

Résultat attendu :

```
[~] Script CHANGED: http://localhost:8001/analytics.js
      before: 981975a4...
      after:  47626030...
```

Les messages de l'outil sont en anglais.

Le script tiers est servi par `localhost`, alors que la page est scannée via `127.0.0.1` : ce sont deux hôtes différents, donc `magecart-scanner check scan1.json` le signale comme domaine non autorisé, et `--allowlist testbench/allowlist.txt` le déclare autorisé.

## Tests et qualité du code

```bash
pytest                     # tous les tests (le test de bout en bout lance Chromium)
pytest -m "not browser"    # tests unitaires seulement
ruff check . && ruff format --check .
```

## Conventions de code

- Code en anglais, sans commentaires : les noms de fonctions et de variables décrivent ce qu'elles font.
- Fonctions courtes qui ne font qu'une chose, pas de valeur « magique » (les seuils sont des constantes nommées).
- La logique qui n'a pas besoin du navigateur (`build_scan`, `compare_scans`, `check_scan`) est séparée de la partie Playwright, ce qui la rend testable sans Chromium.

## Statut

| Fonction | État |
| --- | --- |
| Inventaire des scripts + SHA-256 | fait (v0.1) |
| Comparaison de deux scans, en-têtes HTTP | fait (v0.1) |
| Liste blanche de domaines, indicateurs d'obfuscation | fait (v0.1, règles simples) |
| Banc d'essai local | fait (v0.1, scénario de modification de script) |
| Requêtes sortantes suspectes | à venir |
| Alertes (email, webhook Slack / Discord) | à venir |
| Rapport de conformité exportable et horodaté | à venir |
| Plugin WooCommerce | à venir |
| Surveillance en temps réel dans le navigateur (MutationObserver) | idée pour une phase 2 |

## Limites

- Un script **inline** modifié apparaît comme « retiré » puis « ajouté » (il n'a pas d'identifiant stable).
- Un scan périodique **ne remplace pas une surveillance continue** : un script peut être modifié entre deux scans, ou ne se comporter mal que pour certains visiteurs.
- Les indicateurs d'obfuscation produisent des **faux positifs**.
- Cet outil **aide à préparer la conformité** mais ne remplace pas l'évaluation d'un auditeur qualifié (QSA).

## Licence

MIT, voir [LICENSE](LICENSE).
