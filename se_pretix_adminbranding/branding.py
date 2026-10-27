# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 the sE-pretix authors
"""Farbpalette und CSS-Erzeugung ohne Django-Abhängigkeit (testbar ohne pretix).

pretix hält seine gesamte Primärfarbe in CSS-Variablen (`--pretix-brand-primary*`, siehe
`pretix/static/pretixbase/scss/_theme_variables.scss`). Dieses Plugin berechnet dieselbe Palette aus einer frei
gewählten Farbe und überschreibt die Variablen; dazu kommt eine kleine, feste Regelliste für die wenigen Stellen im
Admin, an denen pretix das Lila fest eincodiert hat.
"""
from __future__ import annotations

import colorsys
import os
import re
import tempfile
from pathlib import Path

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")
CSS_NAME = "branding.css"
PRESALE_NAME = "presale.css"


class ColorError(ValueError):
    pass


def normalize_hex(value: str) -> str:
    m = HEX_RE.match((value or "").strip())
    if not m:
        raise ColorError("Bitte einen Hex-Farbwert wie #1d6f96 angeben.")
    h = m.group(1).lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h


# ----------------------------------------------------------------------------------------------
# Farbrechnung (Sass-Semantik: lighten/darken/saturate arbeiten in HSL, tint/shade mischen mit Weiß/Schwarz)
# ----------------------------------------------------------------------------------------------
def _rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def _hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def _to_hls(h: str):
    r, g, b = (c / 255 for c in _rgb(h))
    return colorsys.rgb_to_hls(r, g, b)


def _from_hls(hh, l, s) -> str:
    r, g, b = colorsys.hls_to_rgb(hh, min(1, max(0, l)), min(1, max(0, s)))
    return _hex((r * 255, g * 255, b * 255))


def lighten(h: str, pct: float) -> str:
    hh, l, s = _to_hls(h)
    return _from_hls(hh, l + pct / 100, s)


def darken(h: str, pct: float) -> str:
    return lighten(h, -pct)


def saturate(h: str, pct: float) -> str:
    hh, l, s = _to_hls(h)
    return _from_hls(hh, l, s + pct / 100)


def mix(h: str, other: str, amount: float) -> str:
    a, b = _rgb(h), _rgb(other)
    return _hex([x + (y - x) * amount for x, y in zip(a, b)])


def tint(h: str, pct: float) -> str:
    return mix(h, "#ffffff", pct / 100)


def shade(h: str, pct: float) -> str:
    return mix(h, "#000000", pct / 100)


def luminance(h: str) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def link_color(h: str, background: str = "#ffffff", minimum: float = 4.5) -> str:
    """Wie pretix' choose-contrast-color: für Links auf weißem Grund nur ausreichend kontrastreiche Töne."""
    c = h
    for _ in range(40):
        if contrast(c, background) >= minimum:
            return c
        c = darken(c, 2)
    return c


LIGHTEN = (5, 20, 30, 40, 48, 50, 53, 55)
DARKEN = (5, 10, 15, 17, 20, 30)


def palette(color: str) -> dict[str, str]:
    """Die von pretix verwendeten Variablen `--pretix-brand-primary*` für die gegebene Farbe."""
    c = normalize_hex(color)
    p = {
        "--pretix-brand-primary": c,
        "--pretix-link-contrast-color": link_color(c),
        "--pretix-link-hover-contrast-color": link_color(darken(c, 15)),
    }
    for n in LIGHTEN:
        p[f"--pretix-brand-primary-lighten-{n}"] = lighten(c, n)
    for n in DARKEN:
        p[f"--pretix-brand-primary-darken-{n}"] = darken(c, n)
    p["--pretix-brand-primary-tint-90"] = tint(c, 90)
    p["--pretix-brand-primary-shade-25"] = shade(c, 25)
    p["--pretix-brand-primary-shade-42"] = shade(c, 42)
    p["--pretix-brand-primary-lighten-28-saturate-20"] = saturate(lighten(c, 28), 20)
    p["--pretix-brand-primary-lighten-23-saturate-2"] = saturate(lighten(c, 23), 2)
    return p


def build_vars_css(color: str) -> str:
    return ":root{" + ";".join(f"{k}:{v}" for k, v in palette(color).items()) + "}\n"


def _shadow(c: str) -> str:
    r, g, b = _rgb(c)
    return f"0 7px 14px 0 rgba({r},{g},{b},0.1),0 3px 6px 0 rgba(0,0,0,0.07)"


def build_shop_css(color: str) -> str:
    c = normalize_hex(color)
    return (f"/* automatisch erzeugt von se_pretix_adminbranding – nicht von Hand ändern */\n{build_vars_css(c)}"
            f"dialog.modal-card,.modal-wrapper .modal-card{{box-shadow:{_shadow(c)}}}\n")


def build_navbar_css(color: str) -> str:
    c = normalize_hex(color)
    dark_bg = luminance(c) < 0.45
    text = "#ffffff" if dark_bg else "#1b1b1b"
    text_hover = "#ffffff" if dark_bg else "#000000"
    hover = mix(c, "#ffffff" if dark_bg else "#000000", 0.14)
    active = mix(c, "#000000", 0.18)
    border = mix(c, "#000000", 0.25)
    return f"""/* Kopfzeile */
.navbar-inverse {{ background-color: {c}; border-color: {border}; }}
.navbar-inverse .navbar-brand,
.navbar-inverse .navbar-nav > li > a,
.navbar-inverse .navbar-text,
.navbar-inverse .btn-link,
.navbar-header .navbar-events {{ color: {text}; }}
.navbar-inverse .navbar-brand:hover,
.navbar-inverse .navbar-brand:focus,
.navbar-inverse .navbar-nav > li > a:hover,
.navbar-inverse .navbar-nav > li > a:focus,
.navbar-inverse .btn-link:hover,
.navbar-inverse .btn-link:focus {{ color: {text_hover}; background-color: {hover}; }}
.navbar-inverse .navbar-nav > .active > a,
.navbar-inverse .navbar-nav > .active > a:hover,
.navbar-inverse .navbar-nav > .active > a:focus,
.navbar-inverse .navbar-nav > .open > a,
.navbar-inverse .navbar-nav > .open > a:hover,
.navbar-inverse .navbar-nav > .open > a:focus {{ color: {text_hover}; background-color: {active}; }}
.navbar-inverse .navbar-collapse, .navbar-inverse .navbar-form {{ border-color: {border}; }}
.navbar-inverse .navbar-toggle {{ border-color: {border}; }}
.navbar-inverse .navbar-toggle:hover,
.navbar-inverse .navbar-toggle:focus {{ background-color: {hover}; }}
.navbar-inverse .navbar-toggle .icon-bar {{ background-color: {text}; }}
@media (max-width: 767px) {{
  .navbar-inverse .navbar-nav .open .dropdown-menu > .active > a,
  .navbar-inverse .navbar-nav .open .dropdown-menu > .active > a:hover,
  .navbar-inverse .navbar-nav .open .dropdown-menu > .active > a:focus {{ background-color: {active}; }}
  .navbar-inverse .navbar-nav .open .dropdown-menu .divider {{ background-color: {border}; }}
}}
"""


def build_admin_css(color: str) -> str:
    """Admin: Variablen + feste Regeln für die Stellen, an denen pretix das Lila fest eincodiert hat."""
    c = normalize_hex(color)
    return f"""/* automatisch erzeugt von se_pretix_adminbranding – nicht von Hand ändern */
{build_vars_css(c)}/* feste Stellen ohne Variable */
.sidebar-nav li > a > .fa, .big-icon {{ color: {c}; }}
.sidebar-nav li > a > svg path {{ fill: {c}; }}
.widget-container.widget-container-event .bottomrow a.orders {{ background: {c}; }}
.form-signin, .impersonate-warning, dialog.modal-card, .modal-wrapper .modal-card, .qr-code-overlay {{ box-shadow: {_shadow(c)}; }}
{build_navbar_css(c)}"""


# ----------------------------------------------------------------------------------------------
# Ablage
# ----------------------------------------------------------------------------------------------
class BrandingStore:
    """Dateien: branding.css (Admin), presale.css (Shop). Erste Zeile enthält die Farbe als Stempel."""

    def __init__(self, root: str | os.PathLike):
        self.root = Path(root)
        self.css_file = self.root / CSS_NAME
        self.presale_file = self.root / PRESALE_NAME

    def _atomic(self, path: Path, content: str) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.root, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)

    def write(self, color: str) -> str:
        c = normalize_hex(color)
        self.root.mkdir(parents=True, exist_ok=True)
        self._atomic(self.presale_file, build_shop_css(c))
        self._atomic(self.css_file, build_admin_css(c))
        return c

    def remove(self) -> None:
        for f in (self.css_file, self.presale_file):
            try:
                f.unlink()
            except FileNotFoundError:
                pass

    def version(self, presale: bool = False) -> int | None:
        """mtime der CSS-Datei (Cache-Busting) oder None, wenn keine Farbe gesetzt ist."""
        try:
            return int((self.presale_file if presale else self.css_file).stat().st_mtime)
        except OSError:
            return None


def check_compiled_css(static_root: str | os.PathLike) -> list[str]:
    """Selbstprüfung: Gibt es im von pretix erzeugten CSS noch die Variablen/Klassen, auf die das Plugin aufsetzt?
    Rückgabe: Liste von Warnungen (leer = alles wie erwartet)."""
    d = Path(static_root) / "CACHE" / "css"
    texts = []
    try:
        for f in d.glob("*.css"):
            texts.append(f.read_text(encoding="utf-8", errors="ignore"))
    except OSError:
        pass
    if not texts:
        return ["Kein kompiliertes pretix-CSS gefunden – Prüfung nicht möglich."]
    blob = "\n".join(texts)
    warnings = []
    if "--pretix-brand-primary:" not in blob:
        warnings.append("pretix definiert --pretix-brand-primary nicht mehr: Buttons und Links werden nicht umgefärbt.")
    if "navbar-inverse" not in blob:
        warnings.append("Die Kopfzeilen-Klasse .navbar-inverse fehlt im pretix-CSS: Kopfzeile wird nicht umgefärbt.")
    if "--pretix-brand-primary-darken-15:" not in blob:
        warnings.append("Abgeleitete Variablen (…-darken-15 u. a.) fehlen: pretix hat die Palette verändert.")
    return warnings
