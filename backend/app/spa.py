"""Static file serving with a SPA fallback for dynamic SoulBook routes.

The frontend is a Next.js static export. Dynamic routes (/soulbooks/<id>/...)
are exported once under a placeholder segment ("_"); this serves that template
for any concrete id so deep-links and refreshes resolve instead of 404-ing. The
client reads the real ids from the live URL.
"""

from __future__ import annotations

import re

from starlette.staticfiles import StaticFiles
from starlette.types import Scope

_PAGE_RE = re.compile(r"^/soulbooks/[^/]+/chapters/[^/]+/pages/[^/]+/?$")
_CHAPTER_RE = re.compile(r"^/soulbooks/[^/]+/chapters/[^/]+/?$")
_BOOK_RE = re.compile(r"^/soulbooks/[^/]+/?$")

_TEMPLATES = (
    (_PAGE_RE, "soulbooks/_/chapters/_/pages/_/index.html"),
    (_CHAPTER_RE, "soulbooks/_/chapters/_/index.html"),
    (_BOOK_RE, "soulbooks/_/index.html"),
)


class SpaStaticFiles(StaticFiles):
    """StaticFiles that falls back to a route template for dynamic SoulBook URLs."""

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        if response.status_code != 404:
            return response

        request_path = scope.get("path", "/")
        for pattern, template in _TEMPLATES:
            if pattern.match(request_path):
                try:
                    return await super().get_response(template, scope)
                except Exception:  # pragma: no cover - template missing
                    break
        return response
