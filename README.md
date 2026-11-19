# Dossier Présidentielle 2027 — version publique

Candidats, programmes, chiffres vérifiés, vrai / faux, débats et sondages de la présidentielle 2027,
en lecture seule, mis à jour chaque matin.

## Comment ça marche

- `docs/` est le site publié tel quel (aucune compilation) : `index.html`, `data.json`, icônes.
- `docs/data.json` contient toutes les fiches. Il est régénéré chaque matin vers 7 h (heure de Paris)
  par une tâche automatique de Claude, qui pousse le résultat sur `main`. GitHub Pages
  republie alors le site tout seul : https://paul9158.github.io/dossier2027/
- `source/artifact.html` est la page d'origine ; `scripts/build_page.py` en tire `docs/index.html`
  en remplaçant l'accès à la base par la lecture de `data.json`.

## Publier

- **GitHub Pages** (dépôt public) : *Settings → Pages → Deploy from a branch → main → /docs*.
- **Netlify** : *Add new site → Import an existing project → GitHub*, choisir ce dépôt.
  Les réglages sont lus dans `netlify.toml` (dossier publié : `docs`, pas de commande de build).
  Attention, l'offre gratuite à crédits ne couvre qu'environ 20 mises en ligne par mois.

## Reconstruire à la main

```bash
scripts/publish.sh CHEMIN_EXPORT [source/artifact.html]
```

`CHEMIN_EXPORT` contient un dossier par collection (`candidats/`, `mesures/`…) et un fichier JSON par fiche.
Le script refuse d'écrire si l'export semble incomplet. Pour l'adresse dans les aperçus de lien,
mettre `{"url": "https://…/"}` dans `site.json` puis relancer `scripts/build_page.py`.
