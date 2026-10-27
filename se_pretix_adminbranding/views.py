# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 the sE-pretix authors
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from pretix.base.settings import GlobalSettingsObject
from pretix.control.permissions import AdministratorPermissionRequiredMixin

from .branding import ColorError, normalize_hex
from .storage import SETTING_KEY, apply_color, get_store, self_check

DEFAULT_PICKER = "#336699"   # nur Startwert des Farbwählers, wird nie ungefragt gespeichert


class IndexView(AdministratorPermissionRequiredMixin, TemplateView):
    template_name = "se_pretix_adminbranding/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current = GlobalSettingsObject().settings.get(SETTING_KEY, as_type=str, default="") or ""
        ctx.update(current=current, picker=current or DEFAULT_PICKER, warnings=self_check())
        return ctx

    def post(self, request, *args, **kwargs):
        gs = GlobalSettingsObject().settings
        back = redirect(reverse("plugins:se_pretix_adminbranding:index"))
        if request.POST.get("action") == "reset":
            gs.delete(SETTING_KEY)
            get_store().remove()
            messages.success(request, "Zurückgesetzt: pretix-Standarddesign.")
            return back
        raw = (request.POST.get("hex") or "").strip() or request.POST.get("picker", "")
        try:
            color = normalize_hex(raw)
            apply_color(color)
        except ColorError as e:
            messages.error(request, str(e))
            return back
        except OSError as e:
            messages.error(request, f"CSS konnte nicht geschrieben werden: {e}")
            return back
        gs.set(SETTING_KEY, color)
        messages.success(request, f"Farbe {color} gespeichert.")
        return back
