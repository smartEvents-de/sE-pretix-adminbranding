# sE-pretix-adminbranding

pretix-Plugin: Das pretix-Lila (Kopfzeile, Buttons, Links, Akzente) im Admin-Bereich **und** im Shop durch eine frei gewählte Farbe ersetzen.
Einstellbar im Admin-Modus unter `/control/global/adminbranding/` („Admin-Farbe“): Farbwähler oder Hex-Wert, „Zurücksetzen“ stellt das pretix-Standarddesign wieder her.
Das Plugin ist unsichtbar (kein Schalter pro Event). Ohne gespeicherte Farbe ändert sich nichts.

## So funktioniert es

pretix hält seine Primärfarbe in CSS-Variablen (`--pretix-brand-primary*`). Das Plugin berechnet dieselbe Palette (hell/dunkel/tint/shade, wie in
`_theme_variables.scss`) aus Ihrer Farbe und schreibt sie beim Speichern als CSS-Datei nach `MEDIA_ROOT/adminbranding/`:

- `branding.css` (Admin): Variablen + eine kleine feste Regelliste für Stellen, an denen pretix das Lila fest eincodiert hat (Kopfzeile, Sidebar-Icons, Schatten).
- `presale.css` (Shop): nur die Variablen. **Wird nicht ausgeliefert, wenn Event oder Veranstalter eine eigene Shop-Farbe gesetzt haben.**

Die Dateien werden per `<link>` eingebunden (pretix' Content-Security-Policy erlaubt im Admin kein Inline-CSS). Das CSS hängt nur von der Farbe ab, nicht vom pretix-Build;
nach pretix-Updates ist nichts neu zu erzeugen.

## Installation

```bash
pip install se-pretix-adminbranding     # danach pretix neu starten
```

Docker: `RUN pip3 install …` im eigenen Dockerfile auf Basis von `pretix/standalone`. `/media/` muss vom Webserver ausgeliefert werden (Standard-Docker-Konfiguration: ja).

## Kompatibilität

`pretix>=2026.8.0,<2027.0.0`. Die Seite „Admin-Farbe“ prüft das kompilierte pretix-CSS auf die Variablen und Klassen, auf die das Plugin aufsetzt, und warnt,
wenn pretix sie ändert. Grenzen: die Login-Seite des Admin (kein Hook), Logos und Bilder bleiben unverändert; sehr helle Farben ergeben schlecht lesbare Buttons.

## Tests

```bash
python -m venv .venv && .venv/bin/pip install pytest && .venv/bin/python -m pytest -q
```

## Lizenz

GNU Affero General Public License v3 oder später (siehe `LICENSE`). Das Plugin ist ein abgeleitetes Werk von pretix und
steht deshalb ebenfalls unter der AGPL. Für den Betrieb von pretix gelten zusätzlich die
[Zusatzbedingungen von pretix](https://github.com/pretix/pretix/blob/master/LICENSE).

**Inoffiziell:** Dieses Projekt wird nicht vom pretix-Team entwickelt oder unterstützt. „pretix“ ist eine Marke von rami.io GmbH.
