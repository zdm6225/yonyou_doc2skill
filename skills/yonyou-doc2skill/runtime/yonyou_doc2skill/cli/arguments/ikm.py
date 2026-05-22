"""IKM command argument definitions."""

import argparse
from typing import Any

from .common import add_all_standard_arguments


IKM_ARGUMENTS: dict[str, dict[str, Any]] = {
    "base_url": {
        "flags": ("--base-url",),
        "kwargs": {
            "type": str,
            "default": "https://ikm.yonyou.com",
            "help": "IKM base URL",
            "metavar": "URL",
        },
    },
    "cookie": {
        "flags": ("--cookie",),
        "kwargs": {
            "type": str,
            "help": "IKM Cookie header value, or set IKM_COOKIE",
            "metavar": "COOKIE",
        },
    },
    "mode": {
        "flags": ("--mode",),
        "kwargs": {
            "choices": ["map", "portal", "search", "asset"],
            "default": "map",
            "help": "IKM extraction mode: map, portal, search, or asset",
        },
    },
    "url": {
        "flags": ("--url",),
        "kwargs": {
            "type": str,
            "help": "IKM detail page URL. For asset mode, pkasset/actionlocid are parsed from it.",
            "metavar": "URL",
        },
    },
    "pk": {
        "flags": ("--pk",),
        "kwargs": {
            "type": str,
            "help": "IKM knowledge map pk",
            "metavar": "PK",
        },
    },
    "actionlocid": {
        "flags": ("--actionlocid",),
        "kwargs": {
            "type": str,
            "help": "IKM portal/action location id",
            "metavar": "ID",
        },
    },
    "keyword": {
        "flags": ("--keyword",),
        "kwargs": {
            "type": str,
            "help": "Keyword for IKM search mode",
            "metavar": "TEXT",
        },
    },
    "portal_endpoint": {
        "flags": ("--portal-endpoint",),
        "kwargs": {
            "type": str,
            "default": "/space/initSharePortalChannel",
            "help": "IKM portal asset list endpoint",
            "metavar": "PATH",
        },
    },
    "search_endpoint": {
        "flags": ("--search-endpoint",),
        "kwargs": {
            "type": str,
            "default": "/asset/getAssetsByEs",
            "help": "IKM keyword search endpoint",
            "metavar": "PATH",
        },
    },
    "max_assets": {
        "flags": ("--max-assets",),
        "kwargs": {
            "type": int,
            "default": 100,
            "help": "Maximum number of map assets to extract (default: 100)",
            "metavar": "N",
        },
    },
    "download_attachments": {
        "flags": ("--download-attachments",),
        "kwargs": {
            "action": "store_true",
            "help": "Download attachment files into output/<name>/downloads",
        },
    },
    "parse_attachments": {
        "flags": ("--parse-attachments",),
        "kwargs": {
            "action": "store_true",
            "help": (
                "Download and parse supported attachment files into references/content.md. "
                "Implies --download-attachments."
            ),
        },
    },
    "max_attachment_chars": {
        "flags": ("--max-attachment-chars",),
        "kwargs": {
            "type": int,
            "default": 12000,
            "help": "Maximum parsed characters to keep per attachment (default: 12000)",
            "metavar": "N",
        },
    },
    "from_json": {
        "flags": ("--from-json",),
        "kwargs": {
            "type": str,
            "help": "Build skill from previously extracted IKM JSON",
            "metavar": "FILE",
        },
    },
}


def add_ikm_arguments(parser: argparse.ArgumentParser) -> None:
    """Add all IKM command arguments to a parser."""
    add_all_standard_arguments(parser)

    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = "AI enhancement level (default: 0 for IKM)"

    for arg_def in IKM_ARGUMENTS.values():
        parser.add_argument(*arg_def["flags"], **arg_def["kwargs"])
