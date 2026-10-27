# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 the sE-pretix authors
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from se_pretix_adminbranding.branding import (BrandingStore, ColorError, build_admin_css,  # noqa: E402
                                              build_shop_css, check_compiled_css, contrast, darken, lighten,
                                              luminance, normalize_hex, palette, saturate, shade, tint)

COLOR = "#1d6f96"


def test_normalize():
    assert normalize_hex("1D6F96") == "#1d6f96"
    assert normalize_hex("#ABC") == "#aabbcc"
    for bad in ("", "red", "#12345", "#1d6f96;}body{", "url(x)", "#gggggg"):
        with pytest.raises(ColorError):
            normalize_hex(bad)


def close(a, b, tol=1):
    return all(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) <= tol for i in (1, 3, 5))


def test_formulas_match_pretix_defaults():
    """Gegen die von pretix kompilierten Werte für #7f5a91 (Shop-Standard) geprüft (Rundung ±1)."""
    base = "#7f5a91"
    assert close(lighten(base, 5), "#8c659f")
    assert close(lighten(base, 30), "#c7b4d0")
    assert close(darken(base, 15), "#563d62")
    assert close(darken(base, 30), "#2c1f33")
    assert close(tint(base, 90), "#f2eff4")
    assert close(shade(base, 25), "#5f446d")
    assert close(saturate(lighten(base, 28), 20), "#c7a0da")


def test_palette_covers_pretix_variables():
    p = palette(COLOR)
    assert p["--pretix-brand-primary"] == COLOR
    for k in ("--pretix-brand-primary-lighten-5", "--pretix-brand-primary-darken-15", "--pretix-brand-primary-tint-90",
              "--pretix-brand-primary-shade-42", "--pretix-link-contrast-color", "--pretix-link-hover-contrast-color"):
        assert k in p
    assert len(p) == 3 + 8 + 6 + 5


def test_link_color_keeps_contrast():
    assert contrast(palette("#ffee66")["--pretix-link-contrast-color"], "#ffffff") >= 4.5
    assert palette(COLOR)["--pretix-link-contrast-color"] == COLOR   # dunkel genug -> unverändert


def test_css_is_safe_and_balanced():
    for css in (build_admin_css(COLOR), build_shop_css(COLOR)):
        assert css.count("{") == css.count("}")
        assert "url(" not in css and "@import" not in css and "javascript" not in css.lower()
    assert ".navbar-inverse" in build_admin_css(COLOR) and ".navbar-inverse" not in build_shop_css(COLOR)
    assert luminance("#000000") < 0.01 < 0.99 < luminance("#ffffff")


def test_text_contrast_on_navbar():
    assert "color: #ffffff" in build_admin_css(COLOR)
    assert "color: #1b1b1b" in build_admin_css("#ffee00")


def test_store(tmp_path):
    s = BrandingStore(tmp_path / "ab")
    assert s.version() is None and s.version(presale=True) is None
    assert s.write("#1D6F96") == COLOR
    assert COLOR in s.css_file.read_text() and COLOR in s.presale_file.read_text()
    assert s.version() is not None and s.version(presale=True) is not None
    s.remove(); s.remove()
    assert s.version() is None


def test_self_check(tmp_path):
    assert check_compiled_css(tmp_path)   # kein CSS -> Warnung
    d = tmp_path / "CACHE" / "css"
    d.mkdir(parents=True)
    (d / "a.css").write_text(":root{--pretix-brand-primary:#000;--pretix-brand-primary-darken-15:#000}.navbar-inverse{}")
    assert check_compiled_css(tmp_path) == []
    (d / "a.css").write_text(".x{}")
    assert len(check_compiled_css(tmp_path)) == 3
