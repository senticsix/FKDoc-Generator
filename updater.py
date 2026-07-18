"""Update-Check gegen die GitHub-Releases des Projekts.

Geprüft wird ausschließlich das neueste stabile Release (Pre-Releases aus dem
experimental-Branch werden von der GitHub-API bei /releases/latest automatisch
ausgelassen). Es wird nichts automatisch installiert - bei einem gefundenen
Update öffnet die App die Download-Seite im Browser.
"""

import json
import urllib.error
import urllib.request

from version import APP_VERSION, GITHUB_REPO

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"


def parse_version(text):
    """'v1.2.3' -> (1, 2, 3); tolerant gegenüber Zusätzen."""
    text = str(text).strip().lstrip("vV")

    parts = []
    for chunk in text.split("."):
        digits = ""
        for char in chunk:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits) if digits else 0)

    return tuple(parts) if parts else (0,)


def check_for_update(timeout=8):
    """Gibt bei neuerem stabilem Release ein Info-Dict zurück, sonst None.

    Wirft bei Netzwerkproblemen eine Exception; ein 404 (noch keine Releases)
    wird als "kein Update" (None) behandelt.
    """
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "FKscript-Updater",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise

    tag = data.get("tag_name") or ""

    if not tag or parse_version(tag) <= parse_version(APP_VERSION):
        return None

    return {
        "version": tag.lstrip("vV"),
        "notes": (data.get("body") or "").strip(),
        "url": data.get("html_url") or RELEASES_PAGE,
    }
