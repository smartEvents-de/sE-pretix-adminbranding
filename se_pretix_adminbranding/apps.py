# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026 the sE-pretix authors
from django.utils.translation import gettext_lazy as _

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:  # pragma: no cover
    raise RuntimeError("Dieses Plugin braucht pretix (>= 2026.8).")


class PluginApp(PluginConfig):
    default = True
    name = "se_pretix_adminbranding"
    verbose_name = _("Admin-Farbe")

    class PretixPluginMeta:
        name = _("Admin-Farbe (global)")
        author = "sE-pretix"
        version = __version__
        category = "CUSTOMIZATION"
        visible = False   # wirkt global (Admin-Menü „Admin-Farbe“), kein Schalter pro Event
        description = _("Farbe der Kopfzeile im Admin-Bereich über das Interface festlegen.")
        compatibility = "pretix>=2026.8.0,<2027.0.0"

    def ready(self):
        from . import signals  # noqa
