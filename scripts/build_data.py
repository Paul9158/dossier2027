#!/usr/bin/env python3
"""Rassemble l'export de la base (un dossier par collection, un fichier JSON par fiche) en docs/data.json.

Usage : python3 scripts/build_data.py DOSSIER_EXPORT [docs/data.json] [--force]

Garde-fou : refuse d'écrire si une collection disparaît ou si le nombre total de fiches
baisse de plus de 20 % par rapport au data.json actuel (export incomplet), sauf --force.
N'écrit rien si les données n'ont pas changé.
"""
import datetime, json, pathlib, sys

COLLECTIONS = ["candidats", "mesures", "chiffres", "arguments", "debats",
               "journal", "sondages", "evenements", "actus"]

args = [a for a in sys.argv[1:] if not a.startswith("--")]
force = "--force" in sys.argv
if not args:
    sys.exit(__doc__)
src = pathlib.Path(args[0])
out = pathlib.Path(args[1] if len(args) > 1 else pathlib.Path(__file__).resolve().parent.parent / "docs" / "data.json")

cols = {}
for c in COLLECTIONS:
    d = src / c
    docs = []
    if d.is_dir():
        for f in sorted(d.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                sys.exit(f"{f} : contenu inattendu")
            docs.append({"id": f.stem, "data": data})
    cols[c] = docs

old = None
if out.exists():
    try:
        old = json.loads(out.read_text(encoding="utf-8"))
    except ValueError:
        old = None

counts = {c: len(v) for c, v in cols.items()}
total = sum(counts.values())
if old and not force:
    oc = {c: len(v) for c, v in old.get("collections", {}).items()}
    lost = [c for c in COLLECTIONS if oc.get(c) and not counts[c]]
    if lost:
        sys.exit("Export incomplet, collections vides : " + ", ".join(lost) + " (rien n'est écrit, --force pour passer outre)")
    if sum(oc.values()) and total < 0.8 * sum(oc.values()):
        sys.exit(f"Export incomplet : {total} fiches contre {sum(oc.values())} avant (rien n'est écrit, --force pour passer outre)")
    if old.get("collections") == cols:
        print(f"Données inchangées ({total} fiches), rien à écrire.")
        sys.exit(0)

generated = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
parts = [f'{{"generated":{dump(generated)},"counts":{dump(counts)},"collections":{{']
parts.append(",\n".join(f"{dump(c)}:[\n" + ",\n".join(dump(x) for x in cols[c]) + "\n]" for c in COLLECTIONS))
parts.append("}}\n")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(parts), encoding="utf-8")
json.loads(out.read_text(encoding="utf-8"))  # vérifie que le fichier est lisible
print(f"{out} : {total} fiches ({', '.join(f'{c} {n}' for c, n in counts.items())})")
