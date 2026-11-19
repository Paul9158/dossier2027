#!/usr/bin/env python3
"""Fabrique docs/index.html, la version publique en lecture seule, à partir de la page de l'artefact claude.ai.

Usage : python3 scripts/build_page.py [PAGE.html] [docs/index.html] [--save-source]

PAGE.html vaut source/artifact.html par défaut. Avec --save-source, la page lue (débarrassée
du squelette ajouté par claude.ai) remplace source/artifact.html.

La page de l'artefact lit ses données avec window.claude.use("db"). Ici, un petit module
remplace cet accès par la lecture de data.json (même dossier), sans écriture possible.
Si site.json contient {"url": "https://..."}, les balises d'aperçu de lien pointent vers cette adresse.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
src_path = pathlib.Path(args[0]) if args else ROOT / "source" / "artifact.html"
out_path = pathlib.Path(args[1]) if len(args) > 1 else ROOT / "docs" / "index.html"
src = src_path.read_text(encoding="utf-8")

# La page de l'artefact est un fragment : partie <head> (title, link, style) puis le contenu.
# Lue avec l'outil Artifact, elle arrive enveloppée dans le squelette de claude.ai : on en ressort le fragment.
m_wrap = re.search(r"<body[^>]*>(.*)</body>", src, re.S | re.I)
if m_wrap and re.match(r"\s*<(title|meta|link|style)\b", m_wrap.group(1), re.I):
    src = m_wrap.group(1).strip() + "\n"
if "--save-source" in sys.argv:
    (ROOT / "source" / "artifact.html").write_text(src, encoding="utf-8")

if re.search(r"<!doctype|<html[\s>]", src[:500], re.I):
    m_head = re.search(r"<head[^>]*>(.*?)</head>", src, re.S | re.I)
    m_body = re.search(r"<body[^>]*>(.*)</body>", src, re.S | re.I)
    if not (m_head and m_body):
        sys.exit("Page complète mais <head>/<body> introuvables")
    head, body = m_head.group(1), m_body.group(1)
else:
    m = re.search(r"^<(?!title|meta|link|style|/style|script|/script|!--|base|noscript)[a-z]", src, re.M)
    if not m:
        sys.exit("Début du contenu introuvable dans la page")
    head, body = src[:m.start()], src[m.start():]

head = re.sub(r'<meta name="claude:[^"]*"[^>]*>\s*', "", head)
head = re.sub(r"<meta charset[^>]*>\s*|<meta name=\"?viewport\"?[^>]*>\s*", "", head, flags=re.I)

# Le module de remplacement ne sait servir que la base (db) et l'utilisateur (user).
used = set(re.findall(r"""claude\?*\.use\?*\.?\(\s*["'](\w+)["']""", src))
if used - {"db", "user"}:
    print("Attention, la page utilise des capacités non gérées ici :", ", ".join(sorted(used - {"db", "user"})), file=sys.stderr)

# Textes propres à claude.ai, adaptés pour les visiteurs.
REPLACE = [
    ("Les données ne sont pas accessibles dans cette vue. Ouvre la page connecté à ton compte claude.ai.",
     "Les données n'ont pas pu être chargées. Vérifie ta connexion puis recharge la page."),
    ("la tâche automatique ne tourne plus : demande à Claude de la relancer.",
     "la mise à jour automatique ne tourne plus : préviens la personne qui t'a envoyé le lien."),
]
for old, new in REPLACE:
    n = body.count(old)
    if n == 0:
        print("Attention, texte introuvable (la page a changé ?) :", old[:60], file=sys.stderr)
    body = body.replace(old, new)

SHIM = r"""
/* Version publique : les données viennent de data.json (lecture seule) au lieu de la base claude.ai.
   Le fichier est relu quand on revient sur la page et toutes les 30 minutes, la page se met à jour seule. */
(()=>{
  let cur=null,pending=null,last=0;const subs=new Set();
  const get=()=>fetch("data.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error("data.json : erreur "+r.status);return r.json()});
  const load=()=>cur?Promise.resolve(cur):pending||(pending=get().then(d=>{cur=d;last=Date.now();return d}).finally(()=>{pending=null}));
  const snap=(d,c)=>({docs:((d.collections||{})[c]||[]).map(x=>({id:x.id,data:()=>JSON.parse(JSON.stringify(x.data))}))});
  async function refresh(){
    if(!cur||Date.now()-last<60e3)return;last=Date.now();
    try{const d=await get();if(d.generated!==cur.generated){cur=d;subs.forEach(s=>s.next(snap(d,s.c)))}}catch(e){}
  }
  document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")refresh()});
  setInterval(()=>{if(document.visibilityState==="visible")refresh()},30*60e3);
  const ro=()=>Promise.reject(new Error("Version publique : lecture seule"));
  const db={collection:c=>({
    onSnapshot(next,err){const s={c,next};subs.add(s);load().then(d=>{if(subs.has(s))next(snap(d,c))},e=>{if(err)err(e)});return()=>{subs.delete(s)}},
    doc:()=>({set:ro,update:ro,delete:ro})})};
  window.claude={use:n=>n==="db"?load().then(()=>db):n==="user"?Promise.resolve({canEdit:()=>Promise.resolve(false)}):Promise.resolve(null)};
})();
"""

site = {}
if (ROOT / "site.json").exists():
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
url = (site.get("url") or "").strip()
if url and not url.endswith("/"):
    url += "/"
TITLE = "Dossier Présidentielle 2027"
DESC = "Candidats, programmes, chiffres vérifiés, vrai / faux, débats et sondages de la présidentielle 2027. Mis à jour chaque matin."
e = lambda s: html.escape(s, quote=True)
og_abs = (f'<meta property="og:url" content="{e(url)}">\n<meta property="og:image" content="{e(url)}og.png">\n'
          f'<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
          f'<meta name="twitter:card" content="summary_large_image">\n<link rel="canonical" href="{e(url)}">\n') if url else ""

page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{e(DESC)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#f5f5f7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Dossier 2027">
<link rel="icon" type="image/png" href="favicon-64.png">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="manifest" href="manifest.webmanifest">
<meta property="og:type" content="website">
<meta property="og:locale" content="fr_FR">
<meta property="og:site_name" content="Dossier 2027">
<meta property="og:title" content="{e(TITLE)}">
<meta property="og:description" content="{e(DESC)}">
{og_abs}<style>body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<script>{SHIM}</script>
{head.strip()}
</head>
<body>
{body.strip()}
</body>
</html>
"""
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(page, encoding="utf-8")

manifest = {"name": TITLE, "short_name": "Dossier 2027", "description": DESC, "lang": "fr",
            "start_url": "./", "scope": "./", "display": "standalone",
            "background_color": "#f5f5f7", "theme_color": "#f5f5f7",
            "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                      {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                      {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
(out_path.parent / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"{out_path} : {len(page) // 1024} Ko" + (f", adresse {url}" if url else ", sans adresse publique (site.json vide)"))
