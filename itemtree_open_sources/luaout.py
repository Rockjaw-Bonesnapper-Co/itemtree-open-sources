# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""Serialise Python values as Lua 5.1 table constructors, deterministically."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_LUA_KEYWORDS = {
    "and",
    "break",
    "do",
    "else",
    "elseif",
    "end",
    "false",
    "for",
    "function",
    "if",
    "in",
    "local",
    "nil",
    "not",
    "or",
    "repeat",
    "return",
    "then",
    "true",
    "until",
    "while",
}


def lua_string(value: str) -> str:
    out = []
    for ch in value:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif code < 32 or code == 127:
            out.append(f"\\{code:03d}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def lua_key(key) -> str:
    if isinstance(key, bool):
        raise TypeError("boolean table keys are not supported")
    if isinstance(key, int):
        return f"[{key}]"
    if isinstance(key, str):
        if _IDENT.match(key) and key not in _LUA_KEYWORDS:
            return key
        return f"[{lua_string(key)}]"
    raise TypeError(f"unsupported Lua key type {type(key).__name__}")


def lua_value(value, *, indent: int = 0, pretty: bool = False) -> str:
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "0"
        text = repr(value)
        return text if "." in text or "e" in text else text + ".0"
    if isinstance(value, str):
        return lua_string(value)
    if isinstance(value, Mapping):
        items = sorted(value.items(), key=_key_order)
        parts = [
            f"{lua_key(k)}={lua_value(v, indent=indent + 1, pretty=pretty)}"
            for k, v in items
            if v is not None
        ]
        return _wrap(parts, indent, pretty)
    if isinstance(value, Sequence | set | frozenset):
        seq = sorted(value) if isinstance(value, set | frozenset) else list(value)
        parts = [lua_value(v, indent=indent + 1, pretty=pretty) for v in seq]
        return _wrap(parts, indent, pretty)
    raise TypeError(f"unsupported Lua value type {type(value).__name__}")


def _key_order(item):
    key = item[0]
    return (0, key, "") if isinstance(key, int) else (1, 0, str(key))


def _wrap(parts: list[str], indent: int, pretty: bool) -> str:
    if not parts:
        return "{}"
    if not pretty:
        return "{" + ",".join(parts) + "}"
    pad = "  " * (indent + 1)
    end = "  " * indent
    return "{\n" + "".join(f"{pad}{p},\n" for p in parts) + end + "}"


def lua_module(name: str, header_lines: list[str], body: str) -> str:
    """A generated data module. Self registering so load order does not matter."""
    header = "".join(f"-- {line}\n" for line in header_lines)
    return (
        f"{header}"
        "local _, ItemTree = ...\n"
        "local Data = ItemTree.Data or {}\n"
        "ItemTree.Data = Data\n"
        "Data.modules = Data.modules or {}\n"
        f"Data.modules[{lua_string(name)}] = function()\n"
        f"  return {body}\n"
        "end\n"
    )
