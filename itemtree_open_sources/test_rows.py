# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""Test rows: the one filter that keeps the client's test and [DNT] rows out of every shipped module.

Brief TB3 (owner, 2026-10-04): Copper Ore's tooltip read "1 Test Profession [DNT] recipe", a test
skill line from the client's own SkillLine table shipped as a profession with a recipe. The client
tables carry such rows in every kind: skill lines ("Test Profession [DNT]"), spells ("[DNT] ..."),
items ("Test Fire Sword", "[PH] Robe of the Brilliant Dawn"), zones ("Valley of Heroes UNUSED",
"Test Dungeon"), creatures, and in the Classic Era databases creatures and objects ("Test Banker",
"[PH] Weegli's Armed Barrel"). None of them is content a player can meet, so none of them ships.

`is_test_name` is the one test, and TEST_MARKERS the one list it reads; every writer asks it
before it emits a row:

  * compile_lua, through `drop_test_rows` (itemtree_data/drop_test_rows.py, ours and not
    mirrored since brief GA1: it reads the client's graph and the harvest), for skill lines,
    recipes and items (the Skills, Recipes_<skill>, RecipeIndex and every item shaped module), on
    the baseline graph and the target graph both, before the diff, so a test row is neither
    shipped nor reported as removed, and for the withheld ids the Discovery Miner's harvest names
    with a test name;
  * compile_lua for the creatures met (Creatures.lua), by name or title;
  * era_sources (GPL), whose `is_scaffolding` calls `is_test_name` for creature, object and quest
    names (the EraSources rows, quest titles, givers and trainers); and the pipeline's own reader
    of a build's zone names (ours, never mirrored), which leaves out an area `is_test_name`
    refuses (every zone name EraSources, BossLoot, the vendors and the profession zones read).

Meta.testRows counts what went per kind, and the compile prints it.

The markers are deliberately narrow, and each was checked against the client tables of
1.60.1.70170 and 1.15.9.69722 and the Classic Era databases (docs/test-rows.md). "Test" is a
marker only where it reads as one: "(Test)", "TEST", a lower case "test", "Test" opening a name
(but not "Test of ...", the Classic quest titles "Test of Faith" and "Test of Lore") or glued to
a word ("TestBoots", "TESTAzshara"). "Test" closing a name is not a marker: "The Gordok Taste
Test" and "Toxic Test" are real quests, and "High Test" a real fishing line. A word that merely
contains the letters, such as "Contest", "Testament", "Protester" or "Field Testing Kit", is kept.
"OLD", "PH", "NYI" and "QA" are markers in capitals only, so "Old Murk-Eye" and "Old Tongue" are
kept, and "zz" opens a test name in lower case only, so "Zzarc' Vul" is kept.

This module reads names only, and writes none anywhere.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

# marker -> the pattern that finds it in a name. A pattern carries its own case rule: (?i) where
# the marker is a marker in any case, none where only capitals mark a test row.
TEST_MARKERS: dict[str, str] = {
    "[DNT]": r"(?i)\[dnt\]|\bdnt\b",
    "Test": (
        r"(?i:\(test\))"  # "Tan Leather Shoulderpads (Test)"
        r"|\bTEST"  # "Tome of Whirlwind (TEST)", "TESTAzshara"
        r"|\btest\b"  # "JYoo test item"
        r"|^Test\b(?! of\b)"  # "Test Profession [DNT]", "Test Dungeon"; not "Test of Faith"
        r"|\bTest(?=[A-Z])"  # "TestBoots - Puffed Mail Green"
    ),
    "Do Not Use": r"(?i)\bdo not use\b",
    "PH": r"\[PH\]|\bPH\b",
    "Placeholder": r"(?i)\bplaceholder\b",
    "UNUSED": r"(?i)\bunused\b",
    "DEPRECATED": r"(?i)\bdeprecated\b",
    "zzOLD": r"(?i:zzold)|^zz",
    "OLD": r"(?i:\(old\))|\bOLD\b",
    "NYI": r"\bNYI\b",
    "Debug": r"(?i)\bdebug\b",
    "QA": r"^QA\b|\[QA\]|\bQATest",
}
_MARKERS = {marker: re.compile(pattern) for marker, pattern in TEST_MARKERS.items()}


def test_marker(name: str | None) -> str | None:
    """The first TEST_MARKERS key whose pattern finds `name`, or None for a name that is content."""
    text = (name or "").strip()
    if not text:
        return None
    for marker, pattern in _MARKERS.items():
        if pattern.search(text):
            return marker
    return None


def is_test_name(name: str | None) -> bool:
    """Whether `name` marks its row as test data (TEST_MARKERS), so no shipped module may carry it.

    An empty or missing name is not a test name: what a nameless row means is each writer's own
    rule. A real name that only contains a marker's letters inside a word ("Contest",
    "Testament", "Protester") is kept."""
    return test_marker(name) is not None


# Not collected by pytest, which would otherwise read the two functions above as tests.
test_marker.__test__ = False  # type: ignore[attr-defined]
is_test_name.__test__ = False  # type: ignore[attr-defined]


def count_markers(names: Iterable[str | None]) -> dict[str, int]:
    """marker -> how many of `names` it decides, for the survey (docs/test-rows.md)."""
    found = Counter(test_marker(name) for name in names)
    found.pop(None, None)
    return {marker: found[marker] for marker in TEST_MARKERS if found.get(marker)}
