# amrichtigenplatz.de – Website

Statische Website der amrichtigenplatz GbR (App-Vorstellungen, Support, Datenschutz, Impressum; Deutsch und Englisch).
Gehostet über GitHub Pages aus dem Ordner `docs/` (Branch `main`).

## Ändern

1. Daten bearbeiten: `site.json` (Firmendaten) oder `apps/<slug>/…` (eine App)
2. `python3 build.py` → erzeugt `docs/` komplett neu (benötigt Pillow)
3. Commit und Push auf `main` → GitHub Pages veröffentlicht nach ca. 1 Minute

## Eine App = ein Ordner `apps/<slug>/`

| Datei | Inhalt |
|---|---|
| `app.json` | `slug`, `name`, `category` (`productivity` / `music` / `church`), `platforms` (`mac`, `iphone`, `ipad`), `appstore_url` (null = „Bald im App Store“), `price` (null oder `{"de": "…", "en": "…"}`), `order`, optional `hidden: true`, `privacy_updated`, `de`/`en` mit `subtitle` und `promo`, `screenshots` (`mac`/`iphone` → Namensliste) |
| `icon.png` | App-Icon, quadratisch, 1024 px |
| `description.de.txt`, `description.en.txt` | Beschreibung wie im App Store. Zeile in GROSSBUCHSTABEN = Zwischenüberschrift, `•` = Aufzählung |
| `privacy.de.html`, `privacy.en.html` | Datenschutz-Abschnitte der App als HTML-Fragment (`<h2>`, `<p>`), ohne Kontaktblock – der wird automatisch ergänzt |
| `screenshots/<de|en>-<name>.png` | Screenshots; fehlt die deutsche Fassung, wird die englische genommen |

## Wichtige URLs pro App (für App Store Connect)

- Marketing-URL: `https://amrichtigenplatz.de/apps/<slug>/` (EN: `/en/apps/<slug>/`)
- Support-URL: `https://amrichtigenplatz.de/support/` (EN: `/en/support/`)
- Datenschutz-URL: `https://amrichtigenplatz.de/apps/<slug>/datenschutz/` (EN: `/en/apps/<slug>/privacy/`)
