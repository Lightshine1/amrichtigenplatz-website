#!/usr/bin/env python3
"""Baut die Website amrichtigenplatz.de nach docs/ (GitHub Pages).

Aufbau:
  site.json                 Firmendaten (Impressum, Kontakt)
  apps/<slug>/app.json      Daten einer App (Name, Plattformen, App-Store-Link …)
  apps/<slug>/icon.png      App-Icon (quadratisch, mind. 512 px)
  apps/<slug>/description.{de,en}.txt   Beschreibung (Store-Text; GROSSBUCHSTABEN-Zeile = Überschrift, • = Aufzählung)
  apps/<slug>/privacy.{de,en}.html      Datenschutz-Abschnitte der App (HTML-Fragment, ohne Kontakt)
  apps/<slug>/screenshots/<lang>-<name>.png
  static/                   Logo, Favicon

Aufruf: python3 build.py   → schreibt docs/ komplett neu.
"""
import html, json, os, re, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
SITE = json.loads((ROOT / "site.json").read_text())
LANGS = ["de", "en"]

# ---------------------------------------------------------------- Texte
T = {
 "de": {
  "tagline": "Nützliche Apps für Mac, iPhone und iPad",
  "hero_title": "Mit kleinen Apps eine große Hilfe",
  "hero_text": "Wir entwickeln übersichtliche Apps für Mac, iPhone und iPad – für den Alltag, für Musikerinnen und Musiker und für Kirchengemeinden. Ohne Werbung, ohne Abo-Zwang, mit Respekt vor deinen Daten.",
  "our_apps": "Unsere Apps",
  "coming": "Bald im App Store",
  "appstore": "Im App Store laden",
  "more": "Mehr erfahren",
  "nav_apps": "Apps", "nav_support": "Support",
  "imprint": "Impressum", "privacy": "Datenschutz", "support": "Support",
  "app_privacy": "Datenschutzerklärung der App",
  "screens_mac": "Auf dem Mac", "screens_iphone": "Auf dem iPhone",
  "about_app": "Über die App",
  "available_for": "Verfügbar für",
  "help": "Hilfe & Kontakt",
  "price": "Preis",
  "cat": {"productivity": "Produktivität", "music": "Musik", "church": "Kirche & Gemeinde"},
  "plat": {"mac": "Mac", "iphone": "iPhone", "ipad": "iPad"},
  "updated": "Stand",
  "other_lang": "English", "lang_label": "Sprache",
 },
 "en": {
  "tagline": "Useful apps for Mac, iPhone and iPad",
  "hero_title": "Small apps, big help",
  "hero_text": "We build clear, focused apps for Mac, iPhone and iPad – for everyday tasks, for musicians and for church communities. No ads, no forced subscriptions, and respect for your data.",
  "our_apps": "Our apps",
  "coming": "Coming soon to the App Store",
  "appstore": "Download on the App Store",
  "more": "Learn more",
  "nav_apps": "Apps", "nav_support": "Support",
  "imprint": "Legal notice", "privacy": "Privacy", "support": "Support",
  "app_privacy": "App privacy policy",
  "screens_mac": "On Mac", "screens_iphone": "On iPhone",
  "about_app": "About the app",
  "available_for": "Available for",
  "help": "Help & contact",
  "price": "Price",
  "cat": {"productivity": "Productivity", "music": "Music", "church": "Church & community"},
  "plat": {"mac": "Mac", "iphone": "iPhone", "ipad": "iPad"},
  "updated": "Last updated",
  "other_lang": "Deutsch", "lang_label": "Language",
 },
}

# Seitenpfade je Sprache (ohne führenden Slash, mit Slash am Ende; "" = Startseite)
PATHS = {
 "home":    {"de": "",                "en": "en/"},
 "support": {"de": "support/",        "en": "en/support/"},
 "privacy": {"de": "datenschutz/",    "en": "en/privacy/"},
 "imprint": {"de": "impressum/",      "en": "en/legal-notice/"},
}
def app_path(slug, lang):          return ("" if lang == "de" else "en/") + f"apps/{slug}/"
def app_privacy_path(slug, lang):  return app_path(slug, lang) + ("datenschutz/" if lang == "de" else "privacy/")

e = html.escape

def rel(frm, to):
    """Relativer Link von Seite `frm` zu Seite/Datei `to` (beide relativ zur Wurzel)."""
    depth = frm.count("/")
    r = "../" * depth + to
    return r if r else "./"

# ---------------------------------------------------------------- Apps laden
def load_apps():
    apps = []
    for d in sorted((ROOT / "apps").iterdir()):
        if not (d / "app.json").exists():
            continue
        a = json.loads((d / "app.json").read_text())
        if a.get("hidden"):
            continue
        a["dir"] = d
        for l in LANGS:
            a[l]["description"] = (d / f"description.{l}.txt").read_text()
            a[l]["privacy_html"] = (d / f"privacy.{l}.html").read_text()
        apps.append(a)
    apps.sort(key=lambda a: (a.get("order", 99), a["name"]))
    return apps

def desc_to_html(txt):
    out, ul = [], False
    for line in txt.strip().split("\n"):
        s = line.strip()
        if s.startswith("•") or s.startswith("- "):
            if not ul: out.append("<ul>"); ul = True
            out.append(f"<li>{e(s.lstrip('•- ').strip())}</li>")
            continue
        if ul: out.append("</ul>"); ul = False
        if not s:
            continue
        letters = re.sub(r"[^A-Za-zÄÖÜäöü]", "", s)
        if letters and letters.upper() == letters and len(s) < 60:
            out.append(f"<h3>{e(s.capitalize())}</h3>")
        else:
            out.append(f"<p>{e(s)}</p>")
    if ul: out.append("</ul>")
    return "\n".join(out)

# ---------------------------------------------------------------- Bilder
def img(src, dst, width):
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src)
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=82, method=6)
    return im.size

# ---------------------------------------------------------------- Layout
CSS = (ROOT / "static" / "style.css")

def page(path, lang, title, body, alt_path, description=""):
    t = T[lang]
    R = lambda p: rel(path, p)
    other = "en" if lang == "de" else "de"
    canonical = f"https://{SITE['domain']}/{path}"
    head = f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description or t['tagline'])}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="{lang}" href="{canonical}">
<link rel="alternate" hreflang="{other}" href="https://{SITE['domain']}/{alt_path}">
<link rel="icon" type="image/png" href="{R('static/favicon.png')}">
<link rel="apple-touch-icon" href="{R('static/apple-touch-icon.png')}">
<link rel="stylesheet" href="{R('static/style.css')}">
</head>
<body>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="{R(PATHS['home'][lang])}"><img src="{R('static/logo.png')}" alt="" width="34" height="38"><span>amrichtigenplatz</span></a>
    <nav>
      <a href="{R(PATHS['home'][lang])}#apps">{t['nav_apps']}</a>
      <a href="{R(PATHS['support'][lang])}">{t['nav_support']}</a>
      <a class="lang" href="{R(alt_path)}" hreflang="{other}" lang="{other}" aria-label="{t['lang_label']}: {t['other_lang']}">{other.upper()}</a>
    </nav>
  </div>
</header>
<main>
{body}
</main>
<footer class="foot">
  <div class="wrap foot-in">
    <div><strong>{e(SITE['company'])}</strong><br>{e(SITE['street'])} · {e(SITE['city'])}</div>
    <nav>
      <a href="{R(PATHS['support'][lang])}">{t['support']}</a>
      <a href="{R(PATHS['privacy'][lang])}">{t['privacy']}</a>
      <a href="{R(PATHS['imprint'][lang])}">{t['imprint']}</a>
      <a href="{R(alt_path)}" lang="{other}">{t['other_lang']}</a>
    </nav>
  </div>
</footer>
</body>
</html>
"""
    f = OUT / path / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(head)

def store_button(a, lang, R):
    t = T[lang]
    if a.get("appstore_url"):
        return f'<a class="btn" href="{e(a["appstore_url"])}">{APPLE_SVG}{t["appstore"]}</a>'
    return f'<span class="soon">{t["coming"]}</span>'

APPLE_SVG = '<svg viewBox="0 0 384 512" width="16" height="20" aria-hidden="true"><path fill="currentColor" d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>'

def platforms(a, lang):
    return " · ".join(T[lang]["plat"][p] for p in a["platforms"])

# ---------------------------------------------------------------- Seiten
def build_home(apps, lang):
    t = T[lang]; path = PATHS["home"][lang]; R = lambda p: rel(path, p)
    cards = []
    for a in apps:
        L = a[lang]; ap = app_path(a["slug"], lang)
        cards.append(f"""
  <a class="card" href="{R(ap)}">
    <img class="icon" src="{R('assets/apps/' + a['slug'] + '/icon-256.webp')}" alt="" width="96" height="96">
    <div class="card-body">
      <div class="cat">{t['cat'].get(a['category'], '')}</div>
      <h3>{e(a['name'])}</h3>
      <p>{e(L['subtitle'])}</p>
      <div class="meta">{platforms(a, lang)}</div>
    </div>
  </a>""")
    body = f"""
<section class="hero">
  <div class="wrap hero-in">
    <img class="hero-logo" src="{R('static/logo.png')}" alt="Logo amrichtigenplatz" width="150" height="169">
    <div>
      <p class="eyebrow">{t['tagline']}</p>
      <h1>{t['hero_title']}</h1>
      <p class="lead">{t['hero_text']}</p>
    </div>
  </div>
</section>
<section class="wrap" id="apps">
  <h2>{t['our_apps']}</h2>
  <div class="grid">{''.join(cards)}
  </div>
</section>"""
    page(path, lang, f"amrichtigenplatz – {t['tagline']}", body, PATHS["home"]["en" if lang == "de" else "de"])

def build_app(a, lang):
    t = T[lang]; L = a[lang]; slug = a["slug"]
    path = app_path(slug, lang); R = lambda p: rel(path, p)
    other = "en" if lang == "de" else "de"
    shots = ""
    for kind, label, cls in [("mac", t["screens_mac"], "shots-mac"), ("iphone", t["screens_iphone"], "shots-phone")]:
        names = a.get("screenshots", {}).get(kind, [])
        if not names: continue
        imgs = "".join(
            f'<img src="{R(f"assets/apps/{slug}/{lang}-{n}.webp")}" alt="{e(a["name"])} – {label}" loading="lazy" width="{SIZES[(slug, lang, n)][0]}" height="{SIZES[(slug, lang, n)][1]}">'
            for n in names)
        shots += f'<h2>{label}</h2><div class="shots {cls}">{imgs}</div>'
    price = f'<div class="facts-row"><span>{t["price"]}</span><span>{e(a["price"][lang] if isinstance(a.get("price"), dict) else a["price"])}</span></div>' if a.get("price") else ""
    body = f"""
<section class="app-hero">
  <div class="wrap app-hero-in">
    <img class="icon-big" src="{R(f'assets/apps/{slug}/icon-512.webp')}" alt="" width="160" height="160">
    <div>
      <div class="cat">{t['cat'].get(a['category'], '')}</div>
      <h1>{e(a['name'])}</h1>
      <p class="subtitle">{e(L['subtitle'])}</p>
      <p class="lead">{e(L['promo'])}</p>
      {store_button(a, lang, R)}
    </div>
  </div>
</section>
<section class="wrap">
  {shots}
  <div class="cols">
    <article class="desc">
      <h2>{t['about_app']}</h2>
      {desc_to_html(L['description'])}
    </article>
    <aside class="facts">
      <div class="facts-row"><span>{t['available_for']}</span><span>{platforms(a, lang)}</span></div>
      {price}
      <div class="facts-row"><span>{t['help']}</span><span><a href="{R(PATHS['support'][lang])}">{t['support']}</a></span></div>
      <div class="facts-row"><span>{t['privacy']}</span><span><a href="{R(app_privacy_path(slug, lang))}">{t['app_privacy']}</a></span></div>
    </aside>
  </div>
</section>"""
    page(path, lang, f"{a['name']} – {L['subtitle']}", body, app_path(slug, other), L["promo"])

def build_app_privacy(a, lang):
    t = T[lang]; L = a[lang]; slug = a["slug"]
    path = app_privacy_path(slug, lang); R = lambda p: rel(path, p)
    other = "en" if lang == "de" else "de"
    h1 = f"Datenschutzerklärung für „{a['name']}“" if lang == "de" else f"Privacy Policy for “{a['name']}”"
    contact_h = "Verantwortlich und Kontakt" if lang == "de" else "Controller and contact"
    more = ("Allgemeine Hinweise zu deinen Rechten findest du in der " if lang == "de" else "General information about your rights can be found in our ")
    body = f"""
<section class="wrap prose">
  <p class="back"><a href="{R(app_path(slug, lang))}">← {e(a['name'])}</a></p>
  <h1>{e(h1)}</h1>
  <p class="muted">{t['updated']}: {e(a.get('privacy_updated', SITE['privacy_updated'])[lang])}</p>
  {L['privacy_html']}
  <h2>{contact_h}</h2>
  <p>{contact_block(lang)}</p>
  <p>{more}<a href="{R(PATHS['privacy'][lang])}">{t['privacy'] if lang == 'de' else 'privacy policy'}</a>.</p>
</section>"""
    page(path, lang, f"{h1} – amrichtigenplatz", body, app_privacy_path(slug, other))

def contact_block(lang):
    return (f"{e(SITE['company'])}<br>{e(SITE['street'])}<br>{e(SITE['city'])}<br>"
            f"{'E-Mail' if lang == 'de' else 'Email'}: <a href=\"mailto:{SITE['email']}\">{SITE['email']}</a>")

def build_static_page(key, lang, title, html_body):
    path = PATHS[key][lang]
    other = "en" if lang == "de" else "de"
    page(path, lang, f"{title} – amrichtigenplatz", f'<section class="wrap prose">\n<h1>{e(title)}</h1>\n{html_body}\n</section>', PATHS[key][other])

def build_support(apps, lang):
    s = SITE
    path = PATHS["support"][lang]; R = lambda p: rel(path, p)
    lis = "".join(f'<li><a href="{R(app_path(a["slug"], lang))}">{e(a["name"])}</a></li>' for a in apps)
    if lang == "de":
        b = f"""<p>Du hast eine Frage zu einer unserer Apps, einen Fehler gefunden oder einen Verbesserungsvorschlag? Schreib uns – wir antworten in der Regel innerhalb von zwei Werktagen.</p>
<p class="mailbox"><a class="btn" href="mailto:{s['support_email']}">{s['support_email']}</a></p>
<h2>Damit wir schnell helfen können</h2>
<ul><li>Name der App und Versionsnummer</li><li>Gerät und System, z. B. „MacBook Air, macOS 26“ oder „iPhone 16, iOS 26“</li><li>Was du gemacht hast, was passiert ist und was du erwartet hättest</li><li>Gern einen Screenshot</li></ul>
<h2>Käufe und Erstattungen</h2>
<p>Käufe im App Store wickelt Apple ab. Eine Erstattung kannst du direkt bei Apple unter <a href="https://reportaproblem.apple.com">reportaproblem.apple.com</a> beantragen.</p>
<h2>Apps</h2><ul>{lis}</ul>
<h2>Anschrift</h2><p>{contact_block('de')}<br>Telefon: {e(s['phone'])}</p>"""
        build_static_page("support", "de", "Support", b)
    else:
        b = f"""<p>Have a question about one of our apps, found a bug or have an idea for an improvement? Write to us – we usually reply within two business days.</p>
<p class="mailbox"><a class="btn" href="mailto:{s['support_email']}">{s['support_email']}</a></p>
<h2>To help us help you quickly</h2>
<ul><li>App name and version number</li><li>Device and system, e.g. “MacBook Air, macOS 26” or “iPhone 16, iOS 26”</li><li>What you did, what happened and what you expected</li><li>A screenshot, if possible</li></ul>
<h2>Purchases and refunds</h2>
<p>App Store purchases are handled by Apple. You can request a refund directly from Apple at <a href="https://reportaproblem.apple.com">reportaproblem.apple.com</a>.</p>
<h2>Apps</h2><ul>{lis}</ul>
<h2>Address</h2><p>{contact_block('en')}<br>Phone: {e(s['phone_intl'])}</p>"""
        build_static_page("support", "en", "Support", b)

def build_imprint(lang):
    s = SITE
    partners = ", ".join(s["partners"])
    if lang == "de":
        b = f"""<h2>Angaben gemäß § 5 DDG</h2>
<p>{e(s['company'])}<br>{e(s['street'])}<br>{e(s['city'])}<br>{e(s['country_de'])}</p>
<p><strong>Vertreten durch die Gesellschafter:</strong><br>{e(partners)}</p>
<h2>Kontakt</h2>
<p>Telefon: {e(s['phone'])}<br>E-Mail: <a href="mailto:{s['email']}">{s['email']}</a></p>
<h2>Umsatzsteuer-ID</h2>
<p>Umsatzsteuer-Identifikationsnummer gemäß § 27a Umsatzsteuergesetz:<br>{e(s['vat_id'])}</p>
<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2>
<p>{e(s['responsible'])}<br>{e(s['street'])}<br>{e(s['city'])}</p>
<h2>Verbraucherstreitbeilegung</h2>
<p>Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
<h2>Haftung für Links</h2>
<p>Diese Website enthält Links zu externen Websites Dritter, insbesondere zum App Store von Apple. Auf deren Inhalte haben wir keinen Einfluss; für sie ist der jeweilige Anbieter verantwortlich.</p>"""
        build_static_page("imprint", "de", "Impressum", b)
    else:
        b = f"""<h2>Information pursuant to Section 5 DDG (German Digital Services Act)</h2>
<p>{e(s['company'])}<br>{e(s['street'])}<br>{e(s['city'])}<br>{e(s['country_en'])}</p>
<p><strong>Represented by the partners:</strong><br>{e(partners)}</p>
<h2>Contact</h2>
<p>Phone: {e(s['phone_intl'])}<br>Email: <a href="mailto:{s['email']}">{s['email']}</a></p>
<h2>VAT ID</h2>
<p>VAT identification number pursuant to Section 27a of the German VAT Act:<br>{e(s['vat_id'])}</p>
<h2>Responsible for content pursuant to Section 18 (2) MStV</h2>
<p>{e(s['responsible'])}<br>{e(s['street'])}<br>{e(s['city'])}</p>
<h2>Consumer dispute resolution</h2>
<p>We are neither willing nor obliged to participate in dispute resolution proceedings before a consumer arbitration board.</p>
<p class="muted">The German version of this legal notice is authoritative.</p>"""
        build_static_page("imprint", "en", "Legal notice", b)

def build_privacy(apps, lang):
    s = SITE
    path = PATHS["privacy"][lang]; R = lambda p: rel(path, p)
    applinks = "".join(f'<li><a href="{R(app_privacy_path(a["slug"], lang))}">{e(a["name"])}</a></li>' for a in apps)
    if lang == "de":
        b = f"""<p class="muted">Stand: {s['privacy_updated']['de']}</p>
<h2>1. Verantwortlicher</h2>
<p>{contact_block('de')}<br>Telefon: {e(s['phone'])}</p>
<h2>2. Kurz gesagt</h2>
<p>Diese Website verwendet keine Cookies, kein Tracking, keine Analysedienste und keine eingebundenen Schriftarten oder Inhalte von Drittanbietern. Personenbezogene Daten fallen nur beim technisch notwendigen Abruf der Seiten (Server-Logdateien) und an, wenn du uns eine E-Mail schreibst.</p>
<h2>3. Hosting und Server-Logdateien</h2>
<p>Die Website wird über GitHub Pages bereitgestellt, einen Dienst der GitHub B.V. (Prins Bernhardplein 200, 1097 JB Amsterdam, Niederlande) bzw. der GitHub, Inc. (88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA). Beim Aufruf der Seiten verarbeitet GitHub technisch notwendige Daten, insbesondere deine IP-Adresse, Datum und Uhrzeit des Abrufs, die aufgerufene Seite sowie Browser- und Systemangaben, um die Website auszuliefern und vor Missbrauch zu schützen.</p>
<p>Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO; unser berechtigtes Interesse liegt in einer sicheren und zuverlässigen Bereitstellung der Website. Dabei können Daten in die USA übermittelt werden. GitHub stützt solche Übermittlungen nach eigenen Angaben auf das EU-US Data Privacy Framework und Standardvertragsklauseln der EU-Kommission. Weitere Informationen: <a href="https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement">Datenschutzerklärung von GitHub</a>.</p>
<h2>4. Kontakt per E-Mail</h2>
<p>Wenn du uns per E-Mail kontaktierst, verarbeiten wir deine Angaben (E-Mail-Adresse, Name, Inhalt der Nachricht), um deine Anfrage zu beantworten. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO, soweit deine Anfrage einen Vertrag oder dessen Anbahnung betrifft, ansonsten Art. 6 Abs. 1 lit. f DSGVO. Wir löschen die Daten, wenn sie nicht mehr erforderlich sind und keine gesetzlichen Aufbewahrungspflichten bestehen.</p>
<h2>5. Links zum App Store</h2>
<p>Links zum App Store führen zu Angeboten der Apple Inc. bzw. Apple Distribution International Ltd. Erst wenn du einen solchen Link anklickst, werden Daten an Apple übermittelt. Für Käufe und Downloads im App Store gilt die Datenschutzerklärung von Apple.</p>
<h2>6. Unsere Apps</h2>
<p>Für jede App gibt es eine eigene Datenschutzerklärung:</p>
<ul>{applinks}</ul>
<h2>7. Deine Rechte</h2>
<p>Du hast das Recht auf Auskunft (Art. 15 DSGVO), Berichtigung (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18), Datenübertragbarkeit (Art. 20) und Widerspruch gegen Verarbeitungen auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO (Art. 21). Wende dich dazu an die oben genannte Adresse.</p>
<p>Außerdem kannst du dich bei einer Datenschutz-Aufsichtsbehörde beschweren. Für uns zuständig ist das Bayerische Landesamt für Datenschutzaufsicht (BayLDA), Promenade 18, 91522 Ansbach.</p>"""
        build_static_page("privacy", "de", "Datenschutzerklärung", b)
    else:
        b = f"""<p class="muted">Last updated: {s['privacy_updated']['en']}</p>
<h2>1. Controller</h2>
<p>{contact_block('en')}<br>Phone: {e(s['phone_intl'])}</p>
<h2>2. In short</h2>
<p>This website uses no cookies, no tracking, no analytics and no fonts or content embedded from third parties. Personal data is only processed when pages are delivered (server log files) and when you send us an email.</p>
<h2>3. Hosting and server log files</h2>
<p>This website is served via GitHub Pages, a service of GitHub B.V. (Prins Bernhardplein 200, 1097 JB Amsterdam, Netherlands) and GitHub, Inc. (88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, USA). When you visit, GitHub processes technically necessary data, in particular your IP address, date and time of access, the page requested and browser and system information, in order to deliver the website and protect it against abuse.</p>
<p>The legal basis is Art. 6(1)(f) GDPR; our legitimate interest is the secure and reliable provision of this website. Data may be transferred to the USA. According to GitHub, such transfers rely on the EU-US Data Privacy Framework and the EU Commission's Standard Contractual Clauses. More information: <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub Privacy Statement</a>.</p>
<h2>4. Contact by email</h2>
<p>If you email us, we process your details (email address, name, content of your message) to answer your request. The legal basis is Art. 6(1)(b) GDPR where your request relates to a contract or its preparation, otherwise Art. 6(1)(f) GDPR. We delete the data once it is no longer needed and no statutory retention obligations apply.</p>
<h2>5. Links to the App Store</h2>
<p>Links to the App Store lead to services of Apple Inc. and Apple Distribution International Ltd. Data is only transferred to Apple once you click such a link. Purchases and downloads in the App Store are subject to Apple's privacy policy.</p>
<h2>6. Our apps</h2>
<p>Each app has its own privacy policy:</p>
<ul>{applinks}</ul>
<h2>7. Your rights</h2>
<p>You have the right of access (Art. 15 GDPR), rectification (Art. 16), erasure (Art. 17), restriction of processing (Art. 18), data portability (Art. 20) and to object to processing based on Art. 6(1)(f) GDPR (Art. 21). Please contact us at the address above.</p>
<p>You may also lodge a complaint with a data protection supervisory authority. The authority responsible for us is the Bavarian State Office for Data Protection Supervision (BayLDA), Promenade 18, 91522 Ansbach, Germany.</p>"""
        build_static_page("privacy", "en", "Privacy Policy", b)

# ---------------------------------------------------------------- Hauptprogramm
SIZES = {}

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")
    apps = load_apps()
    for a in apps:
        d = a["dir"]; slug = a["slug"]; dst = OUT / "assets" / "apps" / slug
        img(d / "icon.png", dst / "icon-256.webp", 256)
        img(d / "icon.png", dst / "icon-512.webp", 512)
        for lang in LANGS:
            for kind, names in a.get("screenshots", {}).items():
                for n in names:
                    src = d / "screenshots" / f"{lang}-{n}.png"
                    if not src.exists():
                        src = d / "screenshots" / f"en-{n}.png"
                    SIZES[(slug, lang, n)] = img(src, dst / f"{lang}-{n}.webp", 1600 if kind == "mac" else 660)
    for lang in LANGS:
        build_home(apps, lang)
        build_support(apps, lang)
        build_imprint(lang)
        build_privacy(apps, lang)
        for a in apps:
            build_app(a, lang)
            build_app_privacy(a, lang)
    # 404, CNAME, .nojekyll
    (OUT / "CNAME").write_text(SITE["domain"] + "\n")
    (OUT / ".nojekyll").write_text("")
    page_404 = (OUT / "index.html").read_text()
    (OUT / "404.html").write_text(page_404.replace('href="static/', 'href="/static/').replace('src="static/', 'src="/static/').replace('src="assets/', 'src="/assets/').replace('href="apps/', 'href="/apps/').replace('href="support/', 'href="/support/').replace('href="datenschutz/', 'href="/datenschutz/').replace('href="impressum/', 'href="/impressum/').replace('href="en/', 'href="/en/').replace('href="./', 'href="/'))
    # sitemap
    urls = []
    for lang in LANGS:
        urls += [PATHS[k][lang] for k in PATHS]
        for a in apps:
            urls += [app_path(a["slug"], lang), app_privacy_path(a["slug"], lang)]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>https://{SITE['domain']}/{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: https://{SITE['domain']}/sitemap.xml\n")
    print(f"OK: {len(apps)} App(s), {len(urls)} Seiten → {OUT}")

if __name__ == "__main__":
    main()
