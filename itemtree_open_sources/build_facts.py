# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""What the era sources compiler is handed about the client build it compiles for, and no more.

`era_sources.derive` takes the CMaNGOS half of the input (`era_sources.cmangos_only`, the pinned
dump and pfQuest's area ids, read) and one `BuildFacts`. Every field of a BuildFacts is a PLAIN
selection, ids and numbers worked out by the caller from its own data: the compiler never reads a
client table, a curated file or anything else of the caller's, and never names one. The ItemTree
pipeline works them out in its own (unmirrored) `era_places.select`; anyone holding the same
selections for a build can run the compiler without the rest of that pipeline.

Brief EK1 (2026-10-09): until then this was a protocol over the pipeline's whole build graph, and
the compiler read the build's `Lock` and `LockType` tables, its AreaTable, its Map,
CreatureDisplayInfo and SkillLineAbility tables and the addon's curated quests itself. What each
of those decided is now one selection below, so the choosing happens on the caller's side and the
compiler is handed the answer. The fields, each with what it decides (R1 to R7, the residual
ItemTree-Data's docs/licensing.md names):

  * `items` (R1): the item ids this build names. A row for an item ships only where the item is
    here or in `withheld`, and a container (c = 13) is named only where its own id is here.
  * `withheld` (R1): ids this build hides that an earlier build named, whose rows ship anyway and
    are counted apart.
  * `undiscovered` (R1, counted only): a refused item here is counted under `hidden`, any other
    under `notShipped`.
  * `row_areas` (R2): the area ids a row may carry. A pfQuest area that is not here is passed over
    for the next one, and a fishing template whose area is not here is refused (`noArea`).
  * `area_ranks` and `area_ties` (R2, where an area's place in `s` sits): the caller names each
    area with a string of its own, which `s` keeps a place for in its sort and ships BLANK (the
    caller ships the string). Where that place sits decides every index of `s`, so it is handed
    over, as numbers and never as the string: per area id a row may carry, its rank, how many of
    the dump's own strings (era_sources.dump_strings, sorted) sort before the caller's string;
    and, where the caller's string is not itself one of the dump's, its tie, its order among the
    caller's strings of that rank (0 first). An area with a rank and no tie is named by exactly
    the dump's string at that rank.
  * `creature_instances` and `object_instances` (R3): creature or object id -> the area it takes
    where no open world area is known for it.
  * `node_categories` (R4): object id -> the category a chest's lock files it under (8 herb, 9
    vein, 10 fishing pool); a chest with none is c = 11, and a fishing hole is always c = 10.
  * `known_displays` (R5): the display ids a `cd` entry may carry; any other is refused.
  * `profession_spells` (R6): the taught spells a trainer's `tr` list may carry; `class_spells`
    (counted only) the refused ones counted under `trainerSpellClass` rather than
    `trainerSpellUnknown`.
  * `quest_items_left_out` (R7): (quest id, item id) pairs whose quest row is left out, because
    the caller states that hand over first hand.

Plain values only, and checked: a BuildFacts holds frozensets of ids and mappings of ids to ids or
numbers, and refuses anything else at construction. It holds no string of any kind.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


def _ids(name: str, value: object) -> frozenset[int]:
    found = frozenset(value)  # type: ignore[arg-type]
    if not all(isinstance(one, int) and not isinstance(one, bool) for one in found):
        raise TypeError(f"BuildFacts.{name} holds ids only")
    return found


def _id_map(name: str, value: object) -> Mapping[int, int]:
    if not isinstance(value, Mapping):
        raise TypeError(f"BuildFacts.{name} is a mapping of ids")
    held = dict(value)
    for key, one in held.items():
        if not isinstance(key, int) or isinstance(key, bool):
            raise TypeError(f"BuildFacts.{name} is keyed by ids")
        if not isinstance(one, int) or isinstance(one, bool):
            raise TypeError(f"BuildFacts.{name} holds whole numbers only")
    return MappingProxyType(held)


@dataclass(frozen=True)
class BuildFacts:
    """The plain selections the era sources compiler reads (see the module docstring)."""

    items: frozenset[int] = frozenset()
    withheld: frozenset[int] = frozenset()
    undiscovered: frozenset[int] = frozenset()
    row_areas: frozenset[int] = frozenset()
    area_ranks: Mapping[int, int] = field(default_factory=dict)
    area_ties: Mapping[int, int] = field(default_factory=dict)
    creature_instances: Mapping[int, int] = field(default_factory=dict)
    object_instances: Mapping[int, int] = field(default_factory=dict)
    node_categories: Mapping[int, int] = field(default_factory=dict)
    known_displays: frozenset[int] = frozenset()
    profession_spells: frozenset[int] = frozenset()
    class_spells: frozenset[int] = frozenset()
    quest_items_left_out: frozenset[tuple[int, int]] = frozenset()

    def __post_init__(self) -> None:
        for name in (
            "items",
            "withheld",
            "undiscovered",
            "row_areas",
            "known_displays",
            "profession_spells",
            "class_spells",
        ):
            object.__setattr__(self, name, _ids(name, getattr(self, name)))
        for name in ("area_ranks", "area_ties", "creature_instances", "object_instances", "node_categories"):
            object.__setattr__(self, name, _id_map(name, getattr(self, name)))
        pairs = frozenset(self.quest_items_left_out)
        for pair in pairs:
            if not (
                isinstance(pair, tuple)
                and len(pair) == 2
                and all(isinstance(one, int) and not isinstance(one, bool) for one in pair)
            ):
                raise TypeError("BuildFacts.quest_items_left_out holds (quest id, item id) pairs only")
        object.__setattr__(self, "quest_items_left_out", pairs)
