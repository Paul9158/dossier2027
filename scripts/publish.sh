#!/usr/bin/env bash
# Mise à jour quotidienne : reconstruit docs/ à partir de l'export de la base
# (et, si on la fournit, de la dernière version de la page), puis prépare le commit.
# Usage : scripts/publish.sh DOSSIER_EXPORT [PAGE_ARTEFACT.html]
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "Usage : scripts/publish.sh DOSSIER_EXPORT [PAGE_ARTEFACT.html]" >&2; exit 2; }
python3 scripts/build_data.py "$1"
if [ -n "${2:-}" ]; then python3 scripts/build_page.py "$2" --save-source; else python3 scripts/build_page.py; fi
git add docs source
if git diff --cached --quiet; then echo "Rien de nouveau à publier."; else git diff --cached --stat; fi
