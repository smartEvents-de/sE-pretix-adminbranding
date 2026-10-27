# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 the sE-pretix authors
from django.conf import settings

from .branding import BrandingStore, check_compiled_css

REL_PREFIX = "adminbranding"
SETTING_KEY = "plugin_adminbranding_color"


def get_store() -> BrandingStore:
    return BrandingStore(settings.MEDIA_ROOT + "/" + REL_PREFIX)


def apply_color(color: str) -> str:
    return get_store().write(color)


def self_check() -> list[str]:
    return check_compiled_css(settings.STATIC_ROOT)
