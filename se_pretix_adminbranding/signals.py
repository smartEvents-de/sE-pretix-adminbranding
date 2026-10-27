# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 the sE-pretix authors
from django.conf import settings
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from pretix.control.signals import html_page_start, nav_global
from pretix.presale.signals import global_html_head

from .storage import REL_PREFIX, get_store


def _link(presale):
    v = get_store().version(presale=presale)
    if v is None:
        return ""
    name = "presale.css" if presale else "branding.css"
    # Die CSP erlaubt nur Styles von der eigenen Domain/Media, kein Inline-CSS -> <link> auf eine Datei.
    return format_html('<link rel="stylesheet" href="{}{}/{}?v={}">', settings.MEDIA_URL, REL_PREFIX, name, v)


def _has_own_color(request) -> bool:
    """True, wenn Event/Veranstalter eine eigene Shop-Farbe (≠ pretix-Standard) gesetzt hat."""
    obj = getattr(request, "event", None) or getattr(request, "organizer", None)
    if obj is None:
        return False
    try:
        current = (obj.settings.primary_color or "").lower()
    except Exception:
        return False
    return bool(current) and current != str(settings.PRETIX_PRIMARY_COLOR).lower()


@receiver(html_page_start, dispatch_uid="se_pretix_adminbranding_css")
def css(sender, **kwargs):
    return _link(False)


@receiver(global_html_head, dispatch_uid="se_pretix_adminbranding_css_presale")
def css_presale(sender, request=None, **kwargs):
    if request is not None and _has_own_color(request):
        return ""   # eigene Eventfarbe respektieren
    return _link(True)


@receiver(nav_global, dispatch_uid="se_pretix_adminbranding_nav")
def nav(sender, request=None, **kwargs):
    if not request or not request.user.is_authenticated or not request.user.has_active_staff_session(
            request.session.session_key):
        return []
    url = reverse("plugins:se_pretix_adminbranding:index")
    return [{"label": _("Admin-Farbe"), "url": url, "active": request.path.startswith(url), "icon": "paint-brush"}]
