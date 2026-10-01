# Portfolio de Nisrine Khnifass

Site personnel présentant mon parcours d'élève ingénieure en cybersécurité (ENSICAEN), mes expériences, mes projets et mon CV.

**Site en ligne :** https://nisrinekhnifass.github.io/portfolio/

## Pages

Le site est disponible en français et en anglais. La page d'entrée `index.html` propose le choix de la langue.

| Français | English | Contenu |
| --- | --- | --- |
| `fr/index.html` | `en/index.html` | Présentation, photo en fondu qui se floute au défilement, stage recherché, domaines |
| `fr/parcours.html` | `en/education.html` | Formation (frise chronologique) et langues |
| `fr/experiences.html` | `en/experience.html` | Stages, documents de stage, projets, compétences, lien GitHub |
| `fr/au-dela.html` | `en/beyond-code.html` | Autres expériences, engagement BAFA, centres d'intérêt |
| `fr/cv.html` | `en/cv.html` | Aperçu et téléchargement du CV en PDF |
| `fr/contact.html` | `en/contact.html` | Coordonnées et formulaire de contact |

## Choix techniques

- **HTML5 sémantique** (`header`, `nav`, `main`, `article`, `footer`), sans framework, pour un site léger et rapide.
- **CSS** organisé avec des **variables** (thème clair et sombre), la convention de nommage **BEM** et une approche **mobile-first**.
- **JavaScript** vanilla en mode strict, découpé en fonctions d'initialisation indépendantes, avec des messages d'interface traduits selon la langue de la page.
- **Multilingue** : une version par langue, reliée par des balises `hreflang` pour le référencement.
- **Accessibilité** : lien d'évitement, navigation au clavier, attributs ARIA, contrastes vérifiés, respect du réglage « réduire les animations ».
- **Référencement** : balises meta et Open Graph sur chaque page.

## Structure

```
.
├── index.html          (choix de la langue)
├── fr/                 (pages en français)
├── en/                 (pages en anglais)
└── assets/
    ├── css/style.css
    ├── js/theme-init.js   (thème appliqué avant l'affichage)
    ├── js/main.js         (interactions)
    ├── img/               (photo, favicon, logos/)
    └── docs/              (CV et documents de stage en PDF)
```

## Lancer le projet en local

Aucune installation n'est nécessaire : ouvrez `index.html` dans un navigateur, ou lancez un petit serveur local :

```bash
python3 -m http.server 8000
```

puis rendez-vous sur http://localhost:8000.

## Contact

nisrine.khnifass@hotmail.com
