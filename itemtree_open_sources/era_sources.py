# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of EraSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources
"""Historical Classic Era source facts, derived from two pinned community databases.

No client build says where an item comes from: drops, vendors, gathering nodes, containers
and quest turn ins are all server side. This stage fills that gap from the **CMaNGOS Classic
content database**, the 1.12 world database the MaNGOS community maintains, and compiles the
result into a single module, `EraSources.lua`. The addon draws it under the Predicted badge
with a "Classic Era" provenance, never as a fact about the client the player is running.

It is the only source this module reads, and it is read whole: one source of truth, one
credit, and nothing blended in from anywhere else. What it gives over the version 1 table it
replaced on 2026-09-20 is every source an item has rather than one, thirteen categories
rather than five, and gathering at all, so Deviate Scale, Medium Hide, Black Lotus and Iron
Ore have a source and Refreshing Spring Water keeps all 184 of its vendors alongside its
quests. The measurement that settled it is the last section of docs/source-data-options.md.

What is taken, and nothing else: the source category, the creature, object, vendor and quest
NAME, the creature and object **id**, the creature's display id, the Blizzard area id, the
quest id and the faction its race mask implies, the drop chance, the level band of a
summarised group, a limited stock vendor's stock count, the container item's own id, and since
2026-09-20 a handful of **map pins** per creature name per area, and since 2026-09-27 per herb,
vein, fishing pool and chest name per area too, and since brief N3 which creature starts and which
ends each quest, by the creature's name, and since brief EK1 the lowest creature and object entry
id of each name (`ci`, `oi`), which the addon keys a page by, and since brief EO1 which world object
starts and which ends each quest, by the object's name (`og`). No prose of any kind: not the
loot rows' `comments`, not quest text, not gossip, not scripts.

Since 2026-09-27 (brief T1, on the owner's ruling of 2026-09-27) two more columns of
`creature_template` are read, for the vendors and the quest givers and enders the table already
names and no other creature: `SubName`, the short title under a name such as "Cooking Supplies",
which is a title and not prose, shipped in `st` so a vendor row can say where to look; and
`Faction`, a FactionTemplate id, which the caller reduces through a client build's own
`FactionTemplate` and `Faction` tables to one number (1 Alliance, 2 Horde, 3 both) on its own side
(ItemTree's EraPlaces.lua `cf`, never this file), so a recipe whose only vendor is Alliance can say
so. Nothing else about a faction is read.

Since 2026-09-29 (brief W12, on the owner's ruling of 2026-09-29) `quest_template.ReqItemId1..4`,
read before only so a quest only drop could name its quest, ships as well, with the two new
columns beside it, `ReqItemCount1..4`: per kept quest, the items it asks the player to bring and
how many of each, in `qr`, so a quest item's "Used by" can name the quest. Ids and counts only,
never the quest's text; an item this build does not ship is refused as a row for it would be.
A `qr` quest nothing else titles gets its title in `qt`: an index into `s` where `s` holds the
string, and otherwise the title itself as a plain string, so `s` never grows for `qr`.

Since 2026-10-03 (brief QN1, on the owner's ruling of 2026-10-03: "I want numerals on classic
quests too") three more `quest_template` columns are read, `PrevQuestId`, `NextQuestId` and
`NextQuestInChain`, the chain links, ids only. Where two or more quests of one chain share a
title, each ships its position in the chain and the chain's length in `qc`, so the addon can say
"Taming the Beast (II)". Same titled quests the links do not join get nothing (see quest_chains).

Since 2026-09-29 (brief W15, owner QA of 2026-09-29: "Quest: Deviate Hides (1486)" showed no
giver) every creature `creature_questrelation` or `creature_involvedrelation` names for a titled
quest ships as a name of its own, even where it drops, sells and trains nothing: its name in
`s`, its kind in `ck`, its display id in `cd`, its `SubName` in `st` and its quest lists in `qg`
(its pins and side in the caller's EraPlaces.lua), read by exactly the rules those columns follow.
Brief N3 had shipped a giver only where another row already named it. Nothing new is read, and a
creature with no quest link is untouched. So that a list record's two digit name field still fits
once `s` passes 8,280 strings, such an `s` is two sorted runs: the names the lists carry, then
the rest. A table that fits stays one sorted run.

Since 2026-10-22 (brief IW1, on the owner's ruling "B" of 2026-10-22: "Do B") the repeatable quests
that can only be taken while another quest is in the log ship their parent: `quest_template.PrevQuestId`
below 0 on a repeatable quest (SpecialFlags' repeatable bit, the columns QN1 and Q1 already read), as
`qw = { [questId] = parent questId }`, ids only. Filling the Soul Gem (593, PrevQuestId -592) is
available only while Saving Yenniku (592) is in the log, so the addon counts it as part of 592 rather
than as a repeatable quest of its own. Only repeatable ones ship: a one time quest with a negative
PrevQuestId keeps the item by the ordinary quest rules, so its parent would be read by nothing.

Since 2026-10-22 (brief PL1, on the owner's ruling "B" of 2026-10-22: ship the Classic Era quests'
prerequisite links) the same three chain link columns ship as links too, not only as `qc`'s numbers:
for every quest, the quests that come after it, as `qo`, keyed by quest id, each value the later
quests' ids packed as a `qg` list is. A later quest is one whose `PrevQuestId` is the quest, or the
quest's own `NextQuestId` or `NextQuestInChain`, each above 0 (quest_chains' own rule for a step), ids
only and nothing else read. So a step whose next quest has another title still has a next step:
Legends of Maraudon (7044) leads on to The Scepter of Celebras (7046, PrevQuestId 7044), which `qc`
cannot say.

Since 2026-10-23 (brief NX2, on the owner's word of 2026-10-23: "It's probably okay to add chain columns
to the file as well") `qo` holds two more kinds of later step, out of two more `quest_template` columns
and four number columns of one more table, ids and numbers only. `RequiredCondition` names a row of the
`conditions` table, of which `condition_entry`, `type`, `value1`, `value2` and `flags` are read (never
`comments`), and only for the rows that join conditions (AND, type -1, and OR, type -2, `value1` and
`value2` naming two more rows) and the rows that ask for a quest rewarded (type 8, `value1` the quest): a
quest whose `RequiredCondition` asks for the quest rewarded, through AND and OR rows alone, is a later
step of it. A NOT row (type -3) or a row whose `flags` reverses its answer (bit 1) is never walked into,
so a quest that asks for another NOT rewarded is no step of it. March of the Silithid (4493) asks for
either Rise of the Silithid (4267 or 162) rewarded, so it comes after both. And `BreadcrumbForQuestId`
names the quest a breadcrumb leads to, which counts as the breadcrumb's later step: Deliveries to Sven
(164) leads to Sven's Revenge (95). Neither is a step `qc` numbers by: its chains stay the three link
columns' alone (quest_successors).

Since 2026-10-22 (brief NX1, on the owner's ruling "2A" of 2026-10-22: ship the Classic Era provided
items) two more `quest_template` columns are read, `SrcItemId` and `SrcItemCount`: the item a quest
hands the player when it is taken, and how many. They ship as `qp`, keyed by quest id, each value one
`qr` record (the item id, then the count), ids and counts only and nothing else read: Saving Yenniku
(592) hands over the Soul Gem (3912). Only a titled quest that is no scaffolding, and only an item this
build ships (or withholds), as `qr`'s rule is; a `qp` quest nothing else titles gets its title in `qt`
the way a `qr` one does. Every such pair ships, an item that also starts its own quest among them: the
caller's addon leaves that one out where it reads `qp` (the brief's rule, which reads the client's own
item rows and so has no place in this file).

Since 2026-10-22 (brief EO1, on the owner's ruling "3A" of 2026-10-22) the world OBJECTS that start
and end quests are read the same way: `gameobject_questrelation` (which object starts a quest) and
`gameobject_involvedrelation` (which ends one), two id columns each and nothing else, so a wanted
poster's quest names its poster. Every object those two tables name for a titled quest ships as an
object name of its own: its name in `s`, its id in `oi` and its quest lists in `og`, keyed by the
object's name and packed exactly as `qg` is (its pins in the caller's EraPlaces.lua `op`, from the
`gameobject` positions of those objects, read as a chest's are). Its own key rather than `qg`,
because one string can name a creature and an object both. No quest text, no gossip, no script.

Since brief P6a three more tables are read, for the trainers: `npc_trainer` (a creature id and a
spell id per row), `npc_trainer_template` (a template id and a spell id per row, joined to a
creature through `creature_template.TrainerTemplateId`) and, from `spell_template`, the id, the
three `Effect` columns and the three `EffectTriggerSpell` columns and nothing else, to turn a
trainer's "learn" spell into the spell it teaches. Ids only: no spell name, no description, no
cost, no required level or skill (brief TR5 since reads the skill rank, and brief CT1 the level and
the price for the class trainers' `tc`, below). A taught spell is kept only where the caller's selection keeps
it (BuildFacts.profession_spells: ItemTree keeps the spells THIS build's own `SkillLineAbility`
files under a profession or secondary skill line, the coordinator's decision on brief P6a: its
trainer rows are about recipes, a class trainer teaches no item, and the class trainers' 27,038
pairs would have taken the file past the then 1.6 MB), and the list ships per trainer NAME in
`tr`, so a trainer's page can say what it teaches and a spell's sources can name its trainers. A
trainer is a creature the table lists, so it gets its portrait and title through the same paths a
vendor does.

Since brief TR6 (the owner's ruling of 2026-10-13 on the class trainers' places, "Take them from the
Era table") one more `creature_template` column is read, `TrainerType`, a plain number: a creature
that teaches, that the `creature` table spawns and whose TrainerType is a class (0) or a pet (3)
trainer's ships as a name of its own, with its kind, portrait, title and id (and its side and pins
in the caller's EraPlaces.lua), so a player can find their class trainer. Its spells stay cut: such
a name gets no `tr`. A CMaNGOS rule alone; nothing of the caller's chooses these names.

Since brief CT1 (the owner, 2026-10-17: "Let's queue to add the teaches spells for the next
release") those class trainers' spells ship after all, but in a shape of their own, `tc`, rather
than back in `tr`: two more columns of `npc_trainer` and `npc_trainer_template` are read, `reqlevel`
and `spellcost` (the level the trainer asks and the price in copper), and one more of
`creature_template`, `TrainerClass`. Most class trainers of one class teach the very same list, so
each distinct list ships once with its class and each class trainer name points at its list. Every
spell the dump states ships; nothing of the caller's chooses or orders a record.

The map pins and paths are read out of the dump here (the `creature` and `gameobject` positions,
the waypoints) and placed on a client build's own zone maps by the caller alone: since brief GA1
they ship in ItemTree's EraPlaces.lua, and since brief EK1 they are made in its own unmirrored
modules (era_places, era_pins). No coordinate of any kind is in this module's file.

Two inputs are pinned, fetched into the gitignored cache, verified by size and sha256 every
run, and never committed:

  * the cmangos dump, for every fact above but the zones, the spawn positions among them;
  * two files of pfQuest's vanilla database, read for the **area id** a creature or an object
    spawns in (the objects file, like the units file, per spawn since 2026-09-27). The cmangos
    spawn tables carry a map and a coordinate and no area at all, and
    turning a coordinate into an area needs terrain data this pipeline does not extract. Its
    own coordinates, which are already a zone percentage, are read for two things and no more:
    to tell which spawn of a creature a cmangos row is, so that spawn's area id can be taken,
    and to CHECK the pipeline's own arithmetic. No pfQuest coordinate is shipped.

Brief EK1 (owner ruling of 2026-10-09: the public mirror holds CMaNGOS logic only). `derive` takes
the CMaNGOS half of the input (`cmangos_only`) and a `BuildFacts` (build_facts.py) of plain
selections the caller worked out from its own data, and reads nothing else of a client build: no
client table, no curated file, nothing of the caller's is read or named here. Where a selection
still chooses this file's rows (the residual R1 to R7 of ItemTree-Data's docs/licensing.md), the
choosing is the caller's and this module is handed the answer: the items that ship, the areas a
row may carry, the instance a creature or an object stands inside (no database states an area for
one, and the caller's answer is its build's own `Map` rather than a guess at an entrance), the
category a chest's lock gives, the display ids and the trainer spells a name may carry, and the
quest rows to leave out. Where the caller's own zone names sit in the sorted `s` (their places are
shipped blank) is handed over as numbers too, ranks among the dump's own strings (dump_strings,
BuildFacts.area_ranks and area_ties): this module never holds one of those names.

What is refused: every row for an id the caller's `items` does not hold, unless it names it as
withheld (below); a quest only drop, which the source marks with a negative chance; a chance that
is zero, negative, above 100 or rounds below 0.1; a reference loot loop; a creature or object
whose name is scaffolding rather than content; a container whose own item id `items` does not
hold; and a quest row the caller leaves out because it states it first hand.

Withheld ids, since 2026-09-26. BuildFacts.withheld names ids the build hides (an `Item` row and
no `ItemSparse` row) that an earlier build named, which the caller ships beside this table with
their earlier details. Their rows are emitted exactly as a named item's are. The addon hides them
until the player's own client can name the item or a setting says to show them. A hidden id NOT
in the set, one no build has ever named, is still refused.

See docs/era-sources.md, which is the record shape's contract and is what the addon half is
briefed from. The whole feature is this module, its `compile` stage, the switch that turns it
off, and the one generated file.
"""

from __future__ import annotations

import gzip
import hashlib
import re
import shutil
from collections import Counter, defaultdict
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from .build_facts import BuildFacts
from .luaout import lua_module, lua_value
from .test_rows import is_test_name

# ----- the pinned inputs ------------------------------------------------------------------

CACHE_SUBDIR = "era"
# Every fetch sends these generic browser headers and nothing else: no tool name, version,
# repository url, owner or contact detail, and no Referer (owner rule, 2026-09-30). They match the
# pipeline's shared header set; the constants live here so this file stands alone.
GENERIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": GENERIC_USER_AGENT,
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

CMANGOS_COMMIT = "22b51464f1625f6ef6275771de1f5466c6f5d19e"
PFQUEST_COMMIT = "104f35678ca39ab1fb78b655f815cc7016f5e0c8"


@dataclass(frozen=True)
class Pin:
    """One file this stage reads, pinned to exact bytes.

    The point of pinning is that the stage compiles one known file or nothing: a mismatch
    fails rather than quietly compiling something else.
    """

    name: str
    version: str
    url: str
    sha256: str
    bytes: int
    filename: str

    def path(self, cache_dir: Path) -> Path:
        return cache_dir / CACHE_SUBDIR / self.filename


CMANGOS = Pin(
    name="cmangos-classic-db",
    version=CMANGOS_COMMIT[:12],
    url=(
        f"https://raw.githubusercontent.com/cmangos/classic-db/{CMANGOS_COMMIT}"
        "/Full_DB/ClassicDB_1_12_1_z2815.sql.gz"
    ),
    sha256="4f92db520868ab4e566726f68b5b2e380ae781209beaf22237b4f7f04600d0c0",
    bytes=12959882,
    filename=f"classic-db-{CMANGOS_COMMIT[:12]}.sql.gz",
)

PFQUEST_UNITS = Pin(
    name="pfquest-units",
    version=PFQUEST_COMMIT[:12],
    url=f"https://raw.githubusercontent.com/shagu/pfQuest/{PFQUEST_COMMIT}/db/units.lua",
    sha256="b8de09aa33fd4b16edb2287b8c4224c86e6ee420e717a4d428e2935c22c4a922",
    bytes=3497202,
    filename=f"pfquest-units-{PFQUEST_COMMIT[:12]}.lua",
)

PFQUEST_OBJECTS = Pin(
    name="pfquest-objects",
    version=PFQUEST_COMMIT[:12],
    url=f"https://raw.githubusercontent.com/shagu/pfQuest/{PFQUEST_COMMIT}/db/objects.lua",
    sha256="be4846e2f2049cafba7da5ed18d6422bde35ed0e6f6ac34cb1215c1bbafd306e",
    bytes=2464841,
    filename=f"pfquest-objects-{PFQUEST_COMMIT[:12]}.lua",
)

PINS: tuple[Pin, ...] = (CMANGOS, PFQUEST_UNITS, PFQUEST_OBJECTS)

# Inputs this stage used to read and no longer does. A build compiled before the change has
# them in its manifest, and a manifest that names a file the pipeline has stopped reading is
# not merely stale, it is wrong, so the stage drops them when it records its own. Empty today:
# no manifest under builds/ names an input this stage has stopped reading. Put a name back in
# here the next time a pin is dropped, and old manifests will forget it on their next compile.
RETIRED_INPUTS: tuple[str, ...] = ()

# ----- the credit, and the two licence readings -------------------------------------------

# The one sentence that goes wherever this data is shown: the generated module's header, the
# paragraph in docs/era-sources.md and the addon's README credit line all read it from here.
CREDIT = (
    "Historical Classic Era source data, derived from the CMaNGOS Classic content database "
    "(github.com/cmangos/classic-db), which the MaNGOS community compiled for World of "
    "Warcraft patch 1.12. Creature, object and quest names, vendor, trainer and quest giver "
    "titles and their factions (reduced to Alliance, Horde or both through the client's own "
    "faction tables) and which spells a trainer teaches are that database's own. Drop chances "
    "are that database's own loot table figures. Map pins are reduced from that database's own "
    "spawn positions. Creature and object zones come "
    "from pfQuest's vanilla database (github.com/shagu/pfQuest), which contributes the area "
    "id and nothing else. WoW Forever may differ; the addon shows these as predicted."
)

# There are two honest answers to the licence question and either is one constant away.
# "gpl" is shipped today, which is the owner's decision of 2026-09-20. Neither line claims the
# data is Blizzard's, and neither claims ItemTree's own licence covers the upstream database.
LICENCE_NOTE_FACTS = (
    "This module is a facts only derivation: ids, numbers, the names of creatures, objects "
    "and places, vendor, trainer and quest giver titles and factions, the spell ids a "
    "trainer teaches, and a handful of reduced map points, re-expressed by the pipeline. No prose, "
    "no descriptions, no quest text and no comments are taken from the source database, and "
    "none of its own text is reproduced here."
)

# Where the Corresponding Source of the generated file lives, in the GPL-3.0 section 6(d) sense:
# this compiler, `build_facts.py`, the pins above and the upstream notices, in a public repository.
CORRESPONDING_SOURCE_URL = "https://github.com/Rockjaw-Bonesnapper-Co/itemtree-era-sources"


# The upstream a GPL file's declaration names by default: the Classic Era files' one.
DECLARED_UPSTREAM = "the CMaNGOS Classic content database it derives from (github.com/cmangos/classic-db)"


def gpl_declaration(
    *,
    what: str,
    rest: str,
    source: str,
    upstream: str = DECLARED_UPSTREAM,
    corresponding_source: str = CORRESPONDING_SOURCE_URL,
) -> str:
    """THE one place a GPL-3.0 declaration is written (brief GA1, owner ruling of 2026-10-09).

    Only the mirrored modules call it (tests/test_gpl_guards.py fails on any other caller, and on
    the licence's name written anywhere else in the pipeline), and only for a file that holds
    nothing but what one pinned upstream gives: the CMaNGOS dump and pfQuest's area ids (the
    Classic Era files, the defaults), or since brief QZ2 the pinned QuestieDB commit
    (open_sources.py's OpenSources.lua, which passes its own `upstream` and its own
    `corresponding_source`). `what` names the file ("This one generated file"), `rest` says what
    around it is all rights reserved, `source` what the Corresponding Source holds.
    """
    return (
        f"{what} is distributed under the GNU General Public License version 3, the licence of "
        f"{upstream}. "
        f"{rest} Corresponding Source, as GPL-3.0 section 6(d) asks: {corresponding_source} "
        f"({source})."
    )


LICENCE_NOTE_GPL = gpl_declaration(
    what="This one generated file",
    rest="The rest of ItemTree is all rights reserved, EraPlaces.lua beside it included.",
    source="the compiler, the pinned inputs and these notices",
)

# The upstream notices, which travel with the file whichever reading ships. The CMaNGOS line is
# the notice its COPYRIGHT.md carries at the pinned commit, word for word: CMaNGOS states no
# copyright holder or year of its own, it states Blizzard's.
UPSTREAM_CMANGOS = (
    f"CMaNGOS Classic content database: github.com/cmangos/classic-db at commit {CMANGOS_COMMIT}, GPL-3.0."
)
CMANGOS_COPYRIGHT = (
    "CMaNGOS notice (COPYRIGHT.md): World of Warcraft content and materials are trademarks and "
    "copyrights of Blizzard or its licensors. All rights reserved. CMaNGOS project is not "
    "affiliated with Blizzard or its licensors."
)
UPSTREAM_PFQUEST = (
    f"pfQuest vanilla database: github.com/shagu/pfQuest at commit {PFQUEST_COMMIT}, MIT "
    "licensed, read for area ids only."
)

# GPL-3.0 section 5(a): a prominent notice that the work was modified, with a relevant date.
# The date is the Generated stamp on the header's second line, so it is never restated here.
MODIFICATION_NOTICE = (
    "Modified: this file is a modified, reduced derivation of that database, made by the "
    "ItemTree pipeline on the Generated date above; the changes are the reduction this header "
    "describes."
)

LICENCE_FILES = (
    "The licence text ships as LICENSES/GPL-3.0.txt and the CMaNGOS notice as "
    "LICENSES/cmangos-COPYRIGHT.md, beside this file in the ItemTree addon."
)

# "gpl" ships LICENCE_NOTE_GPL, "facts" ships LICENCE_NOTE_FACTS. Changing this one word
# changes the generated header, and docs/era-sources.md sets out both readings either way.
LICENCE_MODE = "gpl"


def licence_note() -> str:
    return LICENCE_NOTE_GPL if LICENCE_MODE == "gpl" else LICENCE_NOTE_FACTS


def gpl_licence_lines(
    *,
    what: str,
    rest: str,
    source: str,
    licence_files: str = LICENCE_FILES,
    pfquest: bool = True,
    upstream: str = DECLARED_UPSTREAM,
    corresponding_source: str = CORRESPONDING_SOURCE_URL,
    upstream_lines: Sequence[str] | None = None,
    modification: str = MODIFICATION_NOTICE,
) -> list[str]:
    """Every licence line of a GPL-3.0 generated file, the declaration (gpl_declaration) first, then
    the upstream commits and notices, the section 5(a) modification notice and where the licence
    files ship. The one helper the mirrored writers make a GPL header with (brief GA1). `pfquest`
    is whether the file reads pfQuest's area ids at all. A file of another upstream (brief QZ2:
    open_sources.py) passes that upstream's declaration words, Corresponding Source, notice lines and
    modification notice; left out, each is the Classic Era files' own, so their headers never move."""
    if upstream_lines is None:
        upstream_lines = [UPSTREAM_CMANGOS, CMANGOS_COPYRIGHT, *([UPSTREAM_PFQUEST] if pfquest else [])]
    return [
        gpl_declaration(
            what=what, rest=rest, source=source, upstream=upstream, corresponding_source=corresponding_source
        ),
        *upstream_lines,
        modification,
        licence_files,
    ]


def licence_lines() -> list[str]:
    """The licence part of the generated header, one comment line each.

    The reading, then the upstream commits and notices. Under "gpl" also the section 5(a)
    modification notice and where the licence files ship (gpl_licence_lines).
    """
    if LICENCE_MODE == "gpl":
        return gpl_licence_lines(
            what="This one generated file",
            rest="The rest of ItemTree is all rights reserved, EraPlaces.lua beside it included.",
            source="the compiler, the pinned inputs and these notices",
        )
    return [licence_note(), UPSTREAM_CMANGOS, CMANGOS_COPYRIGHT, UPSTREAM_PFQUEST]


# Kept under its old name because the addon and the manifest both already read it by this
# name: it is the credit sentence, not the licence reading.
PROVENANCE = CREDIT


# ----- the categories ----------------------------------------------------------------------

# Numbers, not strings: 18,000 repeated copies of "Skinned from" would cost more than the
# whole string table does. 1 to 5 are the numbers the first version of this module used, and
# they keep their meanings so a reader written against that version still reads a row it
# understands. 2 is reserved and no longer emitted: a zone drop meant "somewhere in this zone"
# with no creature behind it, and this source always has the creature.
CAT_BOSS_DROP = 1
CAT_ZONE_DROP = 2
CAT_QUEST = 3
CAT_VENDOR = 4
CAT_WORLD_DROP = 5
CAT_CREATURE_DROP = 6
CAT_SKINNED = 7
CAT_HERB = 8
CAT_VEIN = 9
CAT_FISHED = 10
CAT_OBJECT = 11
CAT_PICKPOCKET = 12
CAT_CONTAINER = 13

CATEGORY_NAMES = {
    CAT_BOSS_DROP: "Boss drop",
    CAT_ZONE_DROP: "Zone drop",
    CAT_QUEST: "Quest",
    CAT_VENDOR: "Vendor",
    CAT_WORLD_DROP: "World drop",
    CAT_CREATURE_DROP: "Creature drop",
    CAT_SKINNED: "Skinned from",
    CAT_HERB: "Herb node",
    CAT_VEIN: "Mining vein",
    CAT_FISHED: "Fished",
    CAT_OBJECT: "Object or chest",
    CAT_PICKPOCKET: "Pickpocketed",
    CAT_CONTAINER: "Container item",
}

# Categories that are never emitted by this version. Kept in CATEGORY_NAMES so the legend a
# reader sees is complete and a future version can fill them in without renumbering.
RESERVED_CATEGORIES = frozenset({CAT_ZONE_DROP})

FACTION_ALLIANCE = 1
FACTION_HORDE = 2
FACTION_BOTH = 3

# quest_template.RequiredRaces, as the 1.12 race mask. A quest open to one side only carries
# that side; a quest open to both, or to nobody in particular, carries neither and is shown
# to everyone, which is what an absent `f` means in the module.
RACE_MASK_ALLIANCE = 1 | 4 | 8 | 64  # human, dwarf, night elf, gnome
RACE_MASK_HORDE = 2 | 16 | 32 | 128  # orc, undead, tauren, troll

# gameobject_template.type. Only these two ever carry loot a player can take.
GO_TYPE_CHEST = 3
GO_TYPE_FISHING_HOLE = 25

# ----- the fan out rules, as named constants -------------------------------------------------

# How many named rows one category may put on one item before the rest become a count.
MAX_NAMED_ROWS = 3

# Above this many distinct creatures, naming three of them is a worse answer than saying the
# item drops out in the world, which is what category 5 already means. Linen Cloth has 737.
WORLD_DROP_CREATURES = 40

# Above this many vendors, three arbitrary names say less than the count does. Refreshing
# Spring Water has 184.
VENDOR_SUMMARY_AT = 20

# A herb or a vein is one node name in many zones. It is listed NODE by node, each node's zone
# rows together (up to this many zones per node, commonest first), and the named row cap counts
# nodes rather than rows: see _node_rows.
MAX_NODE_ZONES = 4

# The two categories whose rows are a node's zones, grouped node by node.
NODE_CATEGORIES = frozenset({CAT_HERB, CAT_VEIN})

# How many further quests a quest row may carry behind the first, in `m`. Unchanged from the
# first version: the case this exists to answer is the same turn in offered to each side.
MAX_FURTHER_QUESTS = 3

# Where a cap would leave exactly this many sources unnamed, the leftovers are named instead
# and no summary row is written. "and 1 more" is a row a player cannot read standing for a
# row we are holding in our hand: Black Lotus grows a fourth zone rather than a count of one.
SUMMARISE_AT_LEAST = 2

# One decimal place. The chances are a 1.12 server's loot tables, so more precision than this
# would be false confidence about a client that is not this one.
CHANCE_PLACES = 1
MIN_CHANCE = 0.1

# How deep a loot reference may be followed before the stage calls it a loop.
MAX_REFERENCE_DEPTH = 4

# Names that mark a row as scaffolding rather than content. Narrow on purpose: a loose rule
# refuses Old Murk-Eye and Old Icebeard, which are real rare creatures with real loot.
SCAFFOLDING_MARKERS = ("(Only GM can see it)", "[UNUSED]", "[PH]", "[DEPRECATED]")


class EraSourcesError(RuntimeError):
    pass


# ----- the two packed encodings -------------------------------------------------------------

# Both of the tables added on 2026-09-20, the creature kinds (`ck`) and the full lists behind
# the summary rows (`x` and `xl`), are packed rather than written as tables of their own.
# Nothing here needs `load`, `loadstring` or a bit library: every value comes back out with
# `math.floor`, `%`, `string.byte` and `string.sub`, which is all Lua 5.1 has.
#
# A record of one of the full lists is a fixed run of base 91 digits, most significant first.
# The alphabet is the printable bytes 35 ("#") to 126 ("~") with 92 (a backslash) left out,
# so no character the Lua writer would escape ever appears and one digit is always one byte.
PACK_BASE = 91
PACK_FIRST = 35
PACK_SKIPPED = 92

# The fields a record carries, in order and in digits. A container record names nothing and
# has no area: it carries the container item's own id where a named record carries its name.
PACK_NAME_DIGITS = 2  # the name's index into s, 0 for a record that names nothing
PACK_AREA_DIGITS = 2  # the area id, 0 for a record with no area
PACK_VALUE_DIGITS = 2  # the chance, the stock and the quest only flag: see pack_value
PACK_CONTAINER_DIGITS = 3  # the container item's own id (c = 13)

# The chance travels in tenths of a percent, so 1000 is 100.0%, and the quest only flag sits
# above it rather than taking a field of its own. A vendor record never carries a chance and
# never carries a condition, so its value is the limited stock count instead.
PACK_TENTHS = 10
PACK_QUEST_ONLY = 2048

# CreatureType, the beast Family and the level band, packed into ONE integer per name.
#
# The field order is not arbitrary. MaxLevel less MinLevel is 0, 1 or 2 for all but twenty of
# the names, and Family is 0 for every name that is not a beast, so the two cheapest fields go
# highest and most values stay at five or six digits. Packing MaxLevel itself would put two
# more digits on every name in the table.
KIND_TYPE_SPAN = 16  # CreatureType, 0 to 15 (this database uses 0 to 11)
KIND_LEVEL_SPAN = 128  # MinLevel, 0 to 127 (this database uses 1 to 63)
KIND_BAND_SPAN = 64  # MaxLevel less MinLevel, 0 to 63
KIND_FAMILY_SPAN = 64  # the beast Family, 0 to 63 (this database uses 0 to 27)

# The categories whose `n` is a creature, which are the ones a kind is shipped for.
CREATURE_CATEGORIES = frozenset({CAT_BOSS_DROP, CAT_CREATURE_DROP, CAT_SKINNED, CAT_PICKPOCKET})

# Brief N3: a VENDOR's name gets a kind too, so its page has a portrait and a map. A plain kind
# (zero or more) is a creature a c = 1, 6, 7 or 12 row names and no vendor row does, exactly as
# before. A vendor's kind is stored NEGATIVE, as -(2 * kind + both + 1), where both is 1 for a
# name that is a vendor AND a creature some creature row names, and 0 for a vendor only. The one
# added for the sign keeps a kind of 0 apart from its vendor twin. One integer per name still, and
# a vendor costs a byte or two over what its kind costs.
KIND_VENDOR_BOTH = 1

# The quest ids a quest giver's two lists hold, in base 91 digits. Three, because Classic quest ids
# run to 9,665 and two digits stop at 8,280.
QG_QUEST_DIGITS = 3

# Brief W12: what a quest asks the player to bring, in `qr`. One record per required item, the
# item id in QR_ITEM_DIGITS base 91 digits and the count in QR_COUNT_DIGITS. Three for the item,
# as a container's own id takes, because Classic item ids run past the 8,280 two digits hold; two
# for the count, because the most any 1.12 quest asks for is 1,200. pack_int fails the
# build rather than wrap if either is ever outgrown.
QR_ITEM_DIGITS = 3
QR_COUNT_DIGITS = 2

# ----- the trainers (brief P6a) ---------------------------------------------------------------
#
# A trainer's list in `tr` is the spell ids it teaches, each as TR_SPELL_DIGITS base 91 digits.
# Three, because the 1.12 spell ids a trainer teaches run to about 30,000 and two digits stop at
# 8,280; pack_int fails the build rather than wrap if one ever outgrows them.
TR_SPELL_DIGITS = 3
# Brief TR5 (the owner's ruling of 2026-10-13, option A): `tv` carries beside each of those spells
# the skill rank the trainer asks before teaching it (npc_trainer.reqskillvalue), as TV_LEVEL_DIGITS
# base 91 digits in the same order as the name's `tr` list. Two, because a 1.12 rank stops at 300.
TV_LEVEL_DIGITS = 2

# `npc_trainer.spell` is usually the trainer's own "learn" spell rather than the spell the player
# ends up with: its effect is SPELL_EFFECT_LEARN_SPELL and its EffectTriggerSpell is the real one
# (the mage trainer's 1142 teaches 116 Frostbolt). The dump's own spell_template says which.
SPELL_EFFECT_LEARN_SPELL = 36

# Brief TR6 (the owner's ruling of 2026-10-13, "Take them from the Era table"): `creature_template.
# TrainerType`, the kind of trainer a row is. A class or a pet trainer that teaches anything and
# stands somewhere joins the table as a name (its kind, portrait, title and id, and the caller's
# side and pins) with no `tr`: the cut of its spells stands (see _trainer_lists). 0 is also the
# column's default, so it says "class trainer" only on a creature that teaches.
TRAINER_TYPE_CLASS = 0
TRAINER_TYPE_MOUNTS = 1
TRAINER_TYPE_TRADESKILLS = 2
TRAINER_TYPE_PETS = 3
PLACED_TRAINER_TYPES = frozenset({TRAINER_TYPE_CLASS, TRAINER_TYPE_PETS})

# Brief CT1 (the owner, 2026-10-17: "Let's queue to add the teaches spells for the next release"):
# `tc`, the class spells a class trainer NAME teaches, which the P6a cut keeps out of `tr`. Each
# distinct list ships once (`l`, most class trainers of one class teach the very same list) with the
# class it is for (`c`, creature_template.TrainerClass), and each class trainer name points at its
# list (`n`). A record is the spell (TC_SPELL_DIGITS, the learn spell read as the spell it teaches,
# as `tr` reads one), the level the trainer asks (npc_trainer.reqlevel, TC_LEVEL_DIGITS: one digit
# holds 90 and a 1.12 level stops at 60) and the price in copper (npc_trainer.spellcost,
# TC_COST_DIGITS: three hold 753,570 and the dearest 1.12 class spell is 80,000). The playable class
# ids TrainerClass names (ChrClasses): a TrainerType 0 creature of any other class teaches nothing
# that ships here.
TC_SPELL_DIGITS = 3
TC_LEVEL_DIGITS = 1
TC_COST_DIGITS = 3
TC_RECORD_DIGITS = TC_SPELL_DIGITS + TC_LEVEL_DIGITS + TC_COST_DIGITS
CLASS_IDS = frozenset({1, 2, 3, 4, 5, 7, 8, 9, 11})

# creature.MovementType 2: the spawn walks its waypoints.
MOVEMENT_WAYPOINT = 2


def pack_digit(value: int) -> str:
    """One base 91 digit as one byte."""
    code = PACK_FIRST + value
    return chr(code if code < PACK_SKIPPED else code + 1)


def pack_int(value: int, digits: int) -> str:
    """One field, most significant digit first.

    A value that will not fit fails the build rather than wrapping: the addon reads these
    widths as fixed, so a table that outgrew one has to change both sides at once.
    """
    if value < 0 or value >= PACK_BASE**digits:
        raise EraSourcesError(f"{value} does not fit in {digits} base {PACK_BASE} digits")
    out: list[str] = []
    for _ in range(digits):
        out.append(pack_digit(value % PACK_BASE))
        value //= PACK_BASE
    return "".join(reversed(out))


def pack_value(row: Mapping, category: int) -> int:
    """The third field of a record: a stock count, or a chance with the quest only flag."""
    if category == CAT_VENDOR:
        return int(row.get("k", 0))
    value = int(round(float(row.get("p", 0.0)) * PACK_TENTHS))
    if "o" in row:
        value += PACK_QUEST_ONLY
    return value


def pack_record(row: Mapping, category: int) -> str:
    """One leftover source, as the fixed run of digits its category's layout asks for."""
    value = pack_int(pack_value(row, category), PACK_VALUE_DIGITS)
    if category == CAT_CONTAINER:
        return pack_int(int(row.get("i", 0)), PACK_CONTAINER_DIGITS) + value
    name = pack_int(int(row.get("n", 0)), PACK_NAME_DIGITS)
    area = pack_int(int(row.get("a", 0)), PACK_AREA_DIGITS)
    return name + area + value


def unpack_int(text: str) -> int:
    """The inverse of pack_int, for readers inside the pipeline (boss_loot reads `pt` and `mp`)."""
    value = 0
    for ch in text:
        code = ord(ch)
        value = value * PACK_BASE + (code - 1 if code > PACK_SKIPPED else code) - PACK_FIRST
    return value


def pack_kind(creature_type: int, family: int, min_level: int, max_level: int) -> int:
    """What kind of creature a name is, as one integer. See the spans above for the order."""
    low = max(0, min(min_level, KIND_LEVEL_SPAN - 1))
    band = max(0, min(max(max_level, low) - low, KIND_BAND_SPAN - 1))
    kind = max(0, min(creature_type, KIND_TYPE_SPAN - 1))
    beast = max(0, min(family, KIND_FAMILY_SPAN - 1))
    return kind + KIND_TYPE_SPAN * (low + KIND_LEVEL_SPAN * (band + KIND_BAND_SPAN * beast))


def vendor_kind(packed: int, creature_too: bool) -> int:
    """A packed kind marked as a vendor's (brief N3): negative, and odd inside where the name is a
    creature some creature row names as well. See KIND_VENDOR_BOTH for the layout."""
    both = KIND_VENDOR_BOTH if creature_too else 0
    return -(2 * packed + both + 1)


def pack_quests(quests: Sequence[int]) -> str:
    """A quest giver's list (brief N3): each quest id as QG_QUEST_DIGITS base 91 digits."""
    return "".join(pack_int(quest, QG_QUEST_DIGITS) for quest in quests)


def pack_requires(requires: Sequence[tuple[int, int]]) -> str:
    """A quest's required items (brief W12): each as the item id then the count, in base 91."""
    return "".join(
        pack_int(item, QR_ITEM_DIGITS) + pack_int(count, QR_COUNT_DIGITS) for item, count in requires
    )


def pack_spells(spells: Sequence[int]) -> str:
    """A trainer's list (brief P6a): each spell id as TR_SPELL_DIGITS base 91 digits."""
    return "".join(pack_int(spell, TR_SPELL_DIGITS) for spell in spells)


def pack_levels(levels: Sequence[int]) -> str:
    """A trainer's learn levels (brief TR5): each as TV_LEVEL_DIGITS base 91 digits, in the order
    of the name's `tr` list."""
    return "".join(pack_int(level, TV_LEVEL_DIGITS) for level in levels)


def pack_class_list(records: Sequence[tuple[int, int, int]]) -> str:
    """A class trainer's list (brief CT1): each record the spell, the level asked and the price in
    copper, as TC_SPELL_DIGITS, TC_LEVEL_DIGITS and TC_COST_DIGITS base 91 digits, in the order
    given."""
    return "".join(
        pack_int(spell, TC_SPELL_DIGITS) + pack_int(level, TC_LEVEL_DIGITS) + pack_int(price, TC_COST_DIGITS)
        for spell, level, price in records
    )


# ----- packed rows (brief OPT7) ----------------------------------------------------------------
#
# r ships each item's rows as ONE string, which the addon decodes the first time it reads that
# item (Core/EraSources.lua, through Data.UnpackRows in Core/Data.lua). A table per row cost the
# client about 9.6 MB over the whole of r; the strings cost their bytes. The format is the packed
# item rows' own (ItemTree-Data docs/data-format.md, brief OPT5), with one more separator between
# rows and one record kind for m:
#
#   module   r = { [itemId] = "<rows>" } beside legend = { {field, type[, sub legend]}, ... } and
#            packed = 1 at the top level of the module, so walking r still meets item ids only.
#   rows     the item's rows IN THE LIST'S ORDER (never sorted) joined by ROW_SEP (byte 29).
#   row      its slots in the legend's order joined by FIELD_SEP (byte 31); an absent field is an
#            empty slot and trailing empty slots are not written. A number is its shortest exact
#            form (an int as written, a float as Python's repr), a boolean 1 or 0, a string its
#            text (the empty string the single byte 30).
#   records  type "r": a list of keyed records, m's {q, n, f}. Its records joined by TOKEN_SEP
#            (byte 30), each one's fields in its own sub legend's order joined by RECORD_SEP (byte
#            28), absent fields empty, trailing ones not written. A record field is a number, a
#            boolean or a non empty string.
#
# No separator byte (28 to 31) may appear in any string: the writer refuses one rather than write
# rows the addon would read wrongly, and refuses an empty row, an empty record and an empty list.
PACK_FIELD_SEP = "\x1f"
PACK_TOKEN_SEP = "\x1e"
PACK_ROW_SEP = "\x1d"
PACK_RECORD_SEP = "\x1c"
PACK_SEPARATORS = (PACK_FIELD_SEP, PACK_TOKEN_SEP, PACK_ROW_SEP, PACK_RECORD_SEP)
PACKED_FORMAT = 1
# The slot order when two fields are as common as each other: the order the header names them.
ROW_FIELD_ORDER = ("c", "n", "a", "p", "q", "f", "m", "i", "k", "o", "t", "lo", "hi")
# The same for a record of m: the order the header names a further quest's fields.
RECORD_FIELD_ORDER = ("q", "n", "f")


def _packed_kind(value) -> str:
    if isinstance(value, bool):
        return "b"
    if isinstance(value, int | float):
        return "n"
    if isinstance(value, str):
        return "s"
    if isinstance(value, list | tuple) and value and all(isinstance(entry, Mapping) for entry in value):
        return "r"
    raise EraSourcesError(f"a packed era row cannot hold {value!r}")


def _packed_number(value) -> str:
    if isinstance(value, int):
        return str(value)
    if value != value or value in (float("inf"), float("-inf")):
        raise EraSourcesError(f"a packed era row cannot hold {value!r}")
    text = repr(value)
    return text if "." in text or "e" in text else text + ".0"


def _packed_text(value: str) -> str:
    if any(sep in value for sep in PACK_SEPARATORS):
        raise EraSourcesError(f"a packed era row cannot hold a separator byte: {value!r}")
    return value


def _field_legend(rows: Iterable[Mapping], order: Sequence[str], nested: bool) -> list[list]:
    counts: dict[str, int] = {}
    kinds: dict[str, str] = {}
    subs: dict[str, list[Mapping]] = {}
    for row in rows:
        for key, value in row.items():
            if value is None:
                continue
            if not isinstance(key, str) or not key or any(sep in key for sep in PACK_SEPARATORS):
                raise EraSourcesError(f"a packed era row needs plain string field names, not {key!r}")
            kind = _packed_kind(value)
            if kind == "r" and not nested:
                raise EraSourcesError(f"a record inside a record is not supported: {key!r}")
            held = kinds.setdefault(key, kind)
            if held != kind:
                raise EraSourcesError(f"field {key!r} is both {held} and {kind} in one table")
            counts[key] = counts.get(key, 0) + 1
            if kind == "r":
                subs.setdefault(key, []).extend(value)
    rank = {name: number for number, name in enumerate(order)}
    keys = sorted(counts, key=lambda k: (-counts[k], rank.get(k, len(rank)), k))
    legend: list[list] = []
    for key in keys:
        if kinds[key] == "r":
            legend.append([key, "r", _field_legend(subs[key], RECORD_FIELD_ORDER, False)])
        else:
            legend.append([key, kinds[key]])
    return legend


def row_legend(rows: Iterable[Mapping]) -> list[list]:
    """The legend for every row r holds: each field any row carries, most common first (ties in
    the header's order), with the one type every row holds it as, and for a record list ("r")
    the sub legend of its records' fields. Refuses a field two rows hold as different types."""
    return _field_legend(rows, ROW_FIELD_ORDER, True)


def _pack_fields(row: Mapping, legend: Sequence[Sequence], sep: str, nested: bool) -> str:
    known = {entry[0] for entry in legend}
    for key, value in row.items():
        if value is not None and key not in known:
            raise EraSourcesError(f"field {key!r} is not in the legend")
    slots: list[str] = []
    for entry in legend:
        key, kind = entry[0], entry[1]
        value = row.get(key)
        if value is None:
            slots.append("")
            continue
        if _packed_kind(value) != kind:
            raise EraSourcesError(f"field {key!r} is not of type {kind}")
        if kind == "b":
            slots.append("1" if value else "0")
        elif kind == "n":
            slots.append(_packed_number(value))
        elif kind == "s":
            if value:
                slots.append(_packed_text(value))
            elif nested:
                slots.append(PACK_TOKEN_SEP)
            else:
                raise EraSourcesError(f"an empty string in a packed record: {key!r}")
        else:
            slots.append(
                PACK_TOKEN_SEP.join(
                    _pack_fields(record, entry[2], PACK_RECORD_SEP, False) for record in value
                )
            )
    while slots and slots[-1] == "":
        slots.pop()
    if not slots:
        raise EraSourcesError("a packed era row or record cannot be empty")
    return sep.join(slots)


def pack_row(row: Mapping, legend: Sequence[Sequence]) -> str:
    """One row of r as its packed string (see the block comment above)."""
    return _pack_fields(row, legend, PACK_FIELD_SEP, True)


def pack_rows(rows: Sequence[Mapping], legend: Sequence[Sequence]) -> str:
    """One item's rows as ONE string, in the list's own order."""
    if not rows:
        raise EraSourcesError("a packed item needs at least one row")
    return PACK_ROW_SEP.join(pack_row(row, legend) for row in rows)


def _unpacked_number(text: str):
    try:
        return int(text)
    except ValueError:
        return float(text)


def _unpack_fields(text: str, legend: Sequence[Sequence], sep: str) -> dict:
    row: dict = {}
    for entry, slot in zip(legend, text.split(sep), strict=False):
        if slot == "":
            continue
        key, kind = entry[0], entry[1]
        if kind == "b":
            row[key] = slot == "1"
        elif kind == "n":
            row[key] = _unpacked_number(slot)
        elif kind == "s":
            row[key] = "" if slot == PACK_TOKEN_SEP else slot
        else:
            row[key] = [
                _unpack_fields(record, entry[2], PACK_RECORD_SEP) for record in slot.split(PACK_TOKEN_SEP)
            ]
    return row


def unpack_rows(text: str, legend: Sequence[Sequence]) -> list[dict]:
    """One packed item back as the list of rows pack_rows was handed, in its order."""
    return [_unpack_fields(row, legend, PACK_FIELD_SEP) for row in text.split(PACK_ROW_SEP)]


def pack_module(value: Mapping) -> dict:
    """A module value with r packed: each item's rows as one string, plus legend and packed.

    The value gpl_value returns, unchanged but for r, which is what the compile writes. A
    value that is already packed is answered as it is.
    """
    if value.get("packed") == PACKED_FORMAT:
        return dict(value)
    rows = value.get("r") or {}
    legend = row_legend(row for listed in rows.values() for row in listed)
    out = dict(value)
    out["r"] = {item: pack_rows(listed, legend) for item, listed in rows.items()}
    out["legend"] = legend
    out["packed"] = PACKED_FORMAT
    return out


def item_rows(value: Mapping) -> dict[int, list[dict]]:
    """r as {itemId: [row, ...]} from a module value, packed or plain (an older module)."""
    rows = value.get("r") or {}
    if value.get("packed") != PACKED_FORMAT:
        return {item: listed if isinstance(listed, list) else [listed] for item, listed in rows.items()}
    legend = value.get("legend") or []
    return {
        item: unpack_rows(listed, legend) if isinstance(listed, str) else listed
        for item, listed in rows.items()
    }


# ----- the facts, as plain data so a fixture can hand build them ----------------------------


@dataclass(frozen=True)
class LootEntry:
    """One row of a loot template, holding only the columns this pipeline reads.

    `chance` is `ChanceOrQuestChance` exactly as the source writes it, so a negative value
    still means "only while the player is on the quest" when the rules look at it. `reference`
    is `-mincountOrRef` where the row points at a reference template instead of an item.
    """

    item: int
    chance: float
    group: int = 0
    reference: int = 0


@dataclass(frozen=True)
class CreatureFacts:
    """What `creature_template` states about one creature, stripped to facts.

    Every script column and every piece of text but the name and the `SubName` are never read.
    `subname` is `SubName`, the short title under a name ("Cooking Supplies"), read since
    2026-09-27 on the owner's ruling of that day and shipped in `st` for vendors and quest
    givers and enders only. `faction` is the `Faction` column, a FactionTemplate id, read on the
    same ruling; the caller reduces it to the side it resolves to through a client build's own
    FactionTemplate and Faction tables (ItemTree's `cf`, never this file's). The pinned dump states
    one `Faction` column, not the later `FactionAlliance` and `FactionHorde` pair, and the reader
    takes whichever it finds.
    `creature_type` is `CreatureType` (1 beast, 2 dragonkin, and so on) and `family` is the
    beast `Family`, both plain ids: what KIND of thing a name is, so the interface can draw a
    spider differently from a murloc.

    `display` is the first `ModelId1..4` the row states, which is a `CreatureDisplayInfo` id and
    the one number the client's own portrait call takes. A creature states up to four models and
    picks one at spawn, so the first one it states is the one a row is drawn with; nothing here
    chooses between them on anything but that order.
    """

    id: int
    name: str = ""
    min_level: int = 0
    max_level: int = 0
    rank: int = 0
    creature_type: int = 0
    family: int = 0
    display: int = 0
    loot: int = 0
    skinning: int = 0
    pickpocket: int = 0
    vendor_template: int = 0
    subname: str = ""
    faction: int = 0
    # Brief P6a: `TrainerTemplateId`, the npc_trainer_template entry this creature teaches from
    # on top of its own npc_trainer rows. 0 for a creature that teaches from no template.
    trainer_template: int = 0
    # Brief TR6 (the owner's ruling of 2026-10-13, "Take them from the Era table"): `TrainerType`,
    # the kind of trainer the row is (TRAINER_TYPE_CLASS, TRAINER_TYPE_MOUNTS, TRAINER_TYPE_TRADESKILLS,
    # TRAINER_TYPE_PETS). A plain number, read so a class or pet trainer joins the table as a name.
    trainer_type: int = 0
    # Brief CT1: `TrainerClass`, the class a class trainer teaches (a ChrClasses id, CLASS_IDS), 0
    # for every other creature. A plain number, read so `tc` can say which class a list is for.
    trainer_class: int = 0


@dataclass(frozen=True)
class ObjectFacts:
    """What `gameobject_template` states about one world object, stripped to facts."""

    id: int
    name: str = ""
    kind: int = 0
    lock: int = 0
    loot: int = 0


@dataclass(frozen=True)
class Spawn:
    """One row of the cmangos `creature` table, stripped to a place on a map.

    `creature` is 0 on the rows that take their creature from `creature_spawn_entry` instead,
    which is how one point in the world spawns one of several creatures. `event` is
    `game_event_creature.event`: positive means the row only exists while that game event is
    running, negative means the row is REMOVED during it and is ordinary the rest of the year.
    `pooled` says the row is one member of a `pool_creature` pool, so one of the pool's points
    holds a creature at a time; every point is still a place the creature is found.

    The z, the orientation, the respawn times, the spawn distance, the movement type and the
    guid itself are read for nothing and reach no shipped table: `guid` is here only so the
    three side tables can be joined to the row.
    """

    guid: int
    creature: int
    map: int
    x: float
    y: float
    event: int = 0
    pooled: bool = False


@dataclass(frozen=True)
class SpawnPoint:
    """One spawn as pfQuest states it: a zone percentage and the area id it sits in.

    pfQuest's own `db/units.lua` has already done the reduction this pipeline cannot, so the
    area id is taken from here exactly as it always has been. The percentage is read only to
    tell one spawn from another and to CHECK the formula: no pfQuest coordinate is shipped.
    """

    x: float
    y: float
    area: int


@dataclass(frozen=True)
class VendorOffer:
    """One line of `npc_vendor` or `npc_vendor_template`. `stock` 0 is unlimited."""

    vendor: int
    item: int
    stock: int = 0


@dataclass(frozen=True)
class QuestFacts:
    """One quest's title, race mask and the items it hands over.

    Quest text of every kind (`Details`, `Objectives`, `OfferRewardText`, `RequestItemsText`)
    is never read: the title is a name, and a name is a fact.
    """

    id: int
    title: str
    races: int = 0
    # The items the quest hands over.
    items: tuple[int, ...] = ()
    # The items the quest asks the player to bring, in the template's slot order. Read so that a
    # quest only drop can name the quest that makes it drop and, since brief W12, so that a quest
    # item can name the quest it is used by (`qr`). Never to describe the quest itself.
    requires: tuple[int, ...] = ()
    # Brief W12: how many of each `requires` asks for, slot by slot (`ReqItemCount1..4`). Empty,
    # or a count of 0, reads as one.
    require_counts: tuple[int, ...] = ()


@dataclass
class EraInput:
    """What the two pinned files state, read, so the stage can be driven from a fixture too.

    Every field is the CMaNGOS dump's (CMANGOS_FIELDS) or pfQuest's area ids (PFQUEST_FIELDS), and
    nothing else (brief EK1). What the compiler is told about a client build is a BuildFacts of
    plain selections, never a field here; a caller that keeps more beside these facts does so on a
    class of its own, which the compiler never reads (derive takes the CmangosOnly cmangos_only
    makes of it).
    """

    creatures: dict[int, CreatureFacts] = field(default_factory=dict)
    objects: dict[int, ObjectFacts] = field(default_factory=dict)
    creature_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    skinning_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    pickpocket_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    object_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    fishing_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    item_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    reference_loot: dict[int, list[LootEntry]] = field(default_factory=dict)
    vendor_offers: list[VendorOffer] = field(default_factory=list)
    vendor_template_offers: list[VendorOffer] = field(default_factory=list)
    quests: dict[int, QuestFacts] = field(default_factory=dict)
    # Every quest_template entry, whatever it hands over or asks for, title or none. The
    # compile ships these ids beside Era's QuestV2 ids as the quests Classic Era knew, so a
    # quest on screen whose id is in neither reads as new in Forever.
    quest_ids: set[int] = field(default_factory=set)
    # quest id -> (the fixed reward item ids, the reward choice item ids), each in the
    # template's slot order with repeats dropped, for every quest_template entry that hands
    # over at least one item. Ids only: no counts and no text. The compile ships it as the
    # QuestRewards module.
    quest_rewards: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = field(default_factory=dict)
    unit_zones: dict[int, tuple[int, ...]] = field(default_factory=dict)
    object_zones: dict[int, tuple[int, ...]] = field(default_factory=dict)
    # The spawns. `spawns` is the cmangos `creature` table, the positions the map pins are reduced
    # from; `spawn_entries` is `creature_spawn_entry`, which names the creature of a row that leaves
    # `id` at 0; `unit_points` is pfQuest per spawn, for the area id and for the cross check.
    spawns: tuple[Spawn, ...] = ()
    spawn_entries: dict[int, tuple[int, ...]] = field(default_factory=dict)
    # Brief W18, the paths' three inputs: the guids whose `creature.MovementType` is a waypoint
    # walk; `creature_movement`, guid -> its waypoints in walking order as world (x, y); and
    # `creature_movement_template`, creature id -> path id -> the same. CMaNGOS positions only.
    waypoint_guids: set[int] = field(default_factory=set)
    paths: dict[int, tuple[tuple[float, float], ...]] = field(default_factory=dict)
    template_paths: dict[int, dict[int, tuple[tuple[float, float], ...]]] = field(default_factory=dict)
    unit_points: dict[int, tuple[SpawnPoint, ...]] = field(default_factory=dict)
    # object id -> every map the cmangos `gameobject` table spawns it on (a guid that leaves `id`
    # at 0 counts for each entry `gameobject_spawn_entry` names). The map alone: the positions
    # are the object pins' input below, not this one's. It exists for one question, whether an
    # object stands on one map alone (inside an instance, or a Boss loot chest).
    object_spawn_maps: dict[int, tuple[int, ...]] = field(default_factory=dict)
    # The object map pins' three inputs (brief D7), the twins of `spawns`, `spawn_entries` and
    # `unit_points`. `object_spawns` is the cmangos `gameobject` table, kept only for a chest or a
    # fishing hole with a loot template and (brief EO1) an object that starts or ends a quest (see
    # lootable_object_spawns), each a Spawn whose
    # `creature` field holds the object id; `object_spawn_entries` is `gameobject_spawn_entry`
    # for the guids among them that leave `id` at 0; `object_points` is pfQuest per object spawn,
    # for the area id and for the cross check.
    object_spawns: tuple[Spawn, ...] = ()
    object_spawn_entries: dict[int, tuple[int, ...]] = field(default_factory=dict)
    object_points: dict[int, tuple[SpawnPoint, ...]] = field(default_factory=dict)
    # Brief N3: `creature_questrelation` (who starts a quest) and `creature_involvedrelation` (who
    # ends one), each as (creature id, quest id) in the dump's order, and the title of EVERY
    # quest_template entry that has one, which is what names the quests a giver's page lists.
    # Titles only: no quest text of any kind.
    quest_starts: list[tuple[int, int]] = field(default_factory=list)
    quest_ends: list[tuple[int, int]] = field(default_factory=list)
    quest_names: dict[int, str] = field(default_factory=dict)
    # Brief EO1 (the owner's ruling "3A" of 2026-10-22): `gameobject_questrelation` (which world
    # object starts a quest) and `gameobject_involvedrelation` (which ends one), each as (object id,
    # quest id) in the dump's order. Two id columns and nothing else.
    object_quest_starts: list[tuple[int, int]] = field(default_factory=list)
    object_quest_ends: list[tuple[int, int]] = field(default_factory=list)
    # Brief QN1 (the owner's ruling of 2026-10-03): quest_template's three chain link columns,
    # questId -> (PrevQuestId, NextQuestId, NextQuestInChain), for every entry with one non zero.
    # Ids only. Read to number the quests of one chain that share a title (quest_chains).
    quest_links: dict[int, tuple[int, int, int]] = field(default_factory=dict)
    # Brief NX1 (the owner's ruling "2A" of 2026-10-22): quest_template's SrcItemId and SrcItemCount,
    # questId -> (the item the quest hands the player when it is taken, how many; a count of 0 read as
    # 1), for every entry whose SrcItemId is above 0. Ids and counts only. Shipped as `qp`.
    quest_sources: dict[int, tuple[int, int]] = field(default_factory=dict)
    # Brief NX2 (the owner's word of 2026-10-23): quest_template's RequiredCondition, questId -> the
    # `conditions` row it names, and its BreadcrumbForQuestId, questId -> the quest the breadcrumb leads
    # to, each for every entry with one above 0; and the `conditions` rows themselves, condition_entry ->
    # (type, value1, value2, flags), for the AND (-1), OR (-2), NOT (-3) and quest rewarded (8) rows
    # alone. Ids and numbers only. Read for qo's later steps (quest_later_steps).
    quest_conditions: dict[int, int] = field(default_factory=dict)
    quest_breadcrumbs: dict[int, int] = field(default_factory=dict)
    conditions: dict[int, tuple[int, int, int, int]] = field(default_factory=dict)
    # Brief P6a, the trainers. `trainer_spells` is `npc_trainer` as (creature id, spell id) and
    # `trainer_template_spells` is `npc_trainer_template` as (template id, spell id), both in the
    # dump's order; `learned_spells` is spell_template's learn spells, spell id -> the spell it
    # teaches.
    trainer_spells: list[tuple[int, int]] = field(default_factory=list)
    trainer_template_spells: list[tuple[int, int]] = field(default_factory=list)
    learned_spells: dict[int, int] = field(default_factory=dict)
    # Brief TR5 (the owner's ruling of 2026-10-13): the same two tables' reqskillvalue, the skill
    # rank asked before the spell is taught, (entry, spell as the row names it) -> the lowest the
    # rows state. Read only where the dump states the column.
    trainer_ranks: dict[tuple[int, int], int] = field(default_factory=dict)
    trainer_template_ranks: dict[tuple[int, int], int] = field(default_factory=dict)
    # Brief CT1 (the owner, 2026-10-17): the same two tables' reqlevel and spellcost, the level a
    # class trainer asks before teaching the spell and its price in copper, (entry, spell as the row
    # names it) -> (level, price), the lowest of each the rows state. Read only where the dump
    # states both columns; only a class trainer's rows are ever shipped (`tc`).
    trainer_terms: dict[tuple[int, int], tuple[int, int]] = field(default_factory=dict)
    trainer_template_terms: dict[tuple[int, int], tuple[int, int]] = field(default_factory=dict)
    # Brief Q1: `game_event_quest`, questId -> the game events it belongs to, ascending (ids only;
    # quest_events reads it), and the reputation turn ins (quest_turn_ins).
    quest_event_links: dict[int, tuple[int, ...]] = field(default_factory=dict)
    quest_turn_ins: set[int] = field(default_factory=set)
    # Brief Q1 (the owner's ruling of 2026-10-09): quest_template's QuestLevel and MinLevel,
    # questId -> (level, minimum level), for every entry stating either (a level below 1 reads 0).
    quest_levels: dict[int, tuple[int, int]] = field(default_factory=dict)
    # Brief INT1b (the owner's ruling of 2026-10-10, Q(b)): the classes a quest is for, questId ->
    # class mask, quest_template's RequiredClasses joined with its ZoneOrSort where that is a class
    # sort (QUEST_SORT_CLASSES), both signals, union. Only the quests restricted to some playable
    # classes and not all of them (quest_class_mask).
    quest_classes: dict[int, int] = field(default_factory=dict)
    # Brief QS2 (the owner's ruling of 2026-10-13): quest_template's RequiredRaces, questId -> race
    # mask, for EVERY entry stating one (non zero). `quests` holds the mask only for a quest that
    # hands over or asks for an item; a quest players recorded in Forever keeps its race mask's side
    # whatever it hands over. A plain number per quest; no GPL file ships it.
    quest_races: dict[int, int] = field(default_factory=dict)
    # Addon brief QV1 (the owner's ruling "2.a" of 2026-10-18): quest_template's RewRepFaction1..5,
    # questId -> the faction ids whose RewRepValue is above 0, in slot order, for every entry stating
    # one. Ids only; no GPL file ships it (the caller's own table names and selects them).
    quest_reputations: dict[int, tuple[int, ...]] = field(default_factory=dict)


# ----- the CMaNGOS only input (brief GA1) ------------------------------------------------------
#
# Owner ruling of 2026-10-09: ONLY data derived from the pinned CMaNGOS Classic content database
# (and pfQuest's MIT area ids) may be in a GPL file. Every EraInput field is one of the two kinds
# below, and tests/test_gpl_guards.py fails on a field that is in neither or in both, so a new field
# has to be classified before anything can read it (brief EK1: a field of the caller's own lives on
# the caller's own class, never here). The Classic Era writers take a CmangosOnly, which holds these
# two kinds and nothing else: era_boss_loot.build and jettison.build_era_facts, and since brief EK1
# derive too.

# Read out of the pinned CMaNGOS dump by read_cmangos.
CMANGOS_FIELDS = frozenset(
    {
        "creatures",
        "objects",
        "creature_loot",
        "skinning_loot",
        "pickpocket_loot",
        "object_loot",
        "fishing_loot",
        "item_loot",
        "reference_loot",
        "vendor_offers",
        "vendor_template_offers",
        "quests",
        "quest_ids",
        "quest_rewards",
        "spawns",
        "spawn_entries",
        "waypoint_guids",
        "paths",
        "template_paths",
        "object_spawn_maps",
        "object_spawns",
        "object_spawn_entries",
        "quest_starts",
        "quest_ends",
        "quest_names",
        "object_quest_starts",
        "object_quest_ends",
        "quest_links",
        "quest_sources",
        "quest_conditions",
        "quest_breadcrumbs",
        "conditions",
        "trainer_spells",
        "trainer_template_spells",
        "learned_spells",
        "trainer_ranks",
        "trainer_template_ranks",
        "trainer_terms",
        "trainer_template_terms",
        "quest_event_links",
        "quest_turn_ins",
        "quest_levels",
        "quest_classes",
        "quest_races",
        "quest_reputations",
    }
)
# Read out of the two pinned pfQuest files, which give the area id a spawn is in and nothing else.
PFQUEST_FIELDS = frozenset({"unit_zones", "object_zones", "unit_points", "object_points"})

# The one key that opens CmangosOnly's constructor. Module private: cmangos_only is the only way to
# make one, and it copies the CMANGOS_FIELDS and PFQUEST_FIELDS of an EraInput and nothing else.
_CMANGOS_ONLY = object()


@dataclass(frozen=True)
class CmangosOnly:
    """The pinned CMaNGOS dump's facts and pfQuest's area ids, and nothing else (brief GA1).

    Made only by `cmangos_only`, which copies the CMaNGOS and pfQuest fields of an EraInput (of a
    caller's class built on EraInput too) and the instance_encounters credits (also read out of
    the dump) and leaves everything else behind. A writer of a GPL file that takes this type
    cannot be handed a client table, a curated file, a mined bank, a harvest or a creature cache:
    there is nowhere on it to put them, and reading any other attribute raises AttributeError.
    """

    key: object = field(repr=False, compare=False)
    facts: Mapping[str, object] = field(default_factory=dict)
    # CMaNGOS `instance_encounters`, creditType 0: DungeonEncounter id -> the creatures credited.
    credits: Mapping[int, tuple[int, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.key is not _CMANGOS_ONLY:
            raise TypeError("a CmangosOnly is made by era_sources.cmangos_only and nothing else")
        unknown = set(self.facts) - CMANGOS_FIELDS - PFQUEST_FIELDS
        if unknown:
            raise TypeError(f"a CmangosOnly holds CMaNGOS and pfQuest fields only, not {sorted(unknown)}")

    def __getattr__(self, name: str):
        facts = object.__getattribute__(self, "facts")
        if name in facts:
            return facts[name]
        raise AttributeError(f"a CmangosOnly holds the CMaNGOS and pfQuest facts alone, not {name}")


def cmangos_only(era_input: EraInput, *, credits: Mapping[int, Sequence[int]] | None = None) -> CmangosOnly:
    """The CMaNGOS and pfQuest half of an EraInput, as the one type a Classic Era GPL writer takes.

    `credits` is CMaNGOS `instance_encounters` (era_boss_loot.read_credits), checked to be ids only.
    """
    if not isinstance(era_input, EraInput):
        raise TypeError(
            f"cmangos_only takes the era sources stage's EraInput, not {type(era_input).__name__}"
        )
    held: dict[int, tuple[int, ...]] = {}
    for encounter, creatures in (credits or {}).items():
        if not isinstance(encounter, int) or isinstance(encounter, bool):
            raise TypeError("an instance_encounters credit is keyed by an encounter id")
        ids = tuple(creatures)
        if not all(isinstance(cid, int) and not isinstance(cid, bool) for cid in ids):
            raise TypeError("an instance_encounters credit names creature ids only")
        held[encounter] = ids
    facts = {name: getattr(era_input, name) for name in sorted(CMANGOS_FIELDS | PFQUEST_FIELDS)}
    return CmangosOnly(_CMANGOS_ONLY, facts, held)


# What the rules read the dump's facts from: the CmangosOnly derive is handed, or an EraInput (a
# fixture, or the pipeline's own readers). Either holds the CMaNGOS and pfQuest fields and no other.
CmangosFacts = EraInput | CmangosOnly


@dataclass
class EraSources:
    """The derived table, ready to serialise, plus what was kept and what was refused.

    Brief GA1: the Classic Era sources ship as TWO files. This is EraSources.lua's half (GPL-3.0):
    `gpl_value` is the file's value, every table read out of the dump (GPL_FIELDS) and `s` with
    every place in `blank` left empty. EraPlaces.lua, the other half, is the caller's (ItemTree's
    era_places, ours, all rights reserved): its table is built on this one, fills each blank
    place with its own string and adds its own tables; the addon joins the two.

    Brief EK1: derive makes this from the dump alone and the BuildFacts selections. It holds no
    string of the caller's: a place `blank` names is "" in `strings` as derive hands it back.
    """

    # Every string, sorted (`s`). A place in `blank` is "" as derive makes it; a caller's own table
    # built on this one may put its string there and append its own after the last.
    strings: list[str] = field(default_factory=list)
    # Brief GA1: every place in `s` EraSources.lua ships blank: the places derive keeps in the sort
    # for an area's string of the caller's (BuildFacts.area_ranks and area_ties) that no field of
    # the dump names too, and any place a caller appends after the last of derive's own.
    blank: set[int] = field(default_factory=set)
    # Brief EK1: area id -> the index into `s` of its place (the caller's string for it), for every
    # area a row or a list entry carries. Never shipped here.
    area_strings: dict[int, int] = field(default_factory=dict)
    rows: dict[int, list[dict]] = field(default_factory=dict)
    # questId -> its title's index into `s`, for the quests that make a quest only drop drop
    # and that no `c = 3` row names anywhere in the table.
    # Since brief W12 a value is either that index or, for a quest only `qr` carries whose title
    # `s` does not hold, the title itself as a plain string.
    quest_titles: dict[int, int | str] = field(default_factory=dict)
    # A creature name's index into `s` -> what kind of creature it is, packed by pack_kind.
    kinds: dict[int, int] = field(default_factory=dict)
    # A creature name's index into `s` -> the CreatureDisplayInfo id the client draws that
    # creature's portrait from. Every id here is one of BuildFacts.known_displays.
    displays: dict[int, int] = field(default_factory=dict)
    # Brief EK1: a creature name's index into `s` -> the LOWEST CMaNGOS creature_template entry id
    # whose name is exactly that string, for every name `ck` carries. The addon keys a Classic Era
    # creature page by it rather than by the name's place in `s`. Shipped as `ci`.
    creature_ids: dict[int, int] = field(default_factory=dict)
    # Brief EK1 Part 2c: an OBJECT name's index into `s` -> the LOWEST CMaNGOS gameobject_template entry
    # id whose name is exactly that string, for every object name a shipped row or list names. The
    # addon keys a Classic Era object page by it. Shipped as `oi`.
    object_ids: dict[int, int] = field(default_factory=dict)
    # itemId -> category -> the number of the list in `lists` that holds the rest of it.
    list_index: dict[int, dict[int, int]] = field(default_factory=dict)
    # The lists themselves, each a packed string, each stored once however many items open it.
    lists: list[str] = field(default_factory=list)
    # Brief N3: a creature or vendor name's index into `s` -> (the quests it starts, the quests it
    # ends), each a string packed by pack_quests, "" where it has none of that side.
    quest_givers: dict[int, tuple[str, str]] = field(default_factory=dict)
    # Brief EO1: a world OBJECT name's index into `s` -> (the quests it starts, the quests it ends),
    # packed as quest_givers is. Shipped as `og`.
    object_givers: dict[int, tuple[str, str]] = field(default_factory=dict)
    # Brief T1: a vendor or quest giver NAME's index into `s` -> its SubName's index into `s`.
    subnames: dict[int, int] = field(default_factory=dict)
    # Brief P6a: a trainer NAME's index into `s` -> the spell ids it teaches, packed by pack_spells.
    trainers: dict[int, str] = field(default_factory=dict)
    # Brief TR5: the same NAME's index -> the learn level of each of those spells, packed by
    # pack_levels in the same order. Shipped as `tv`.
    trainer_levels: dict[int, str] = field(default_factory=dict)
    # Brief CT1: the class trainers' lists, shipped as `tc`: each distinct list packed by
    # pack_class_list (`l`), the class each is for (`c`, parallel to it) and a class trainer NAME's
    # index into `s` -> the 1 based number of its list (`n`).
    class_lists: list[str] = field(default_factory=list)
    class_list_classes: list[int] = field(default_factory=list)
    class_trainer_lists: dict[int, int] = field(default_factory=dict)
    # Brief W12: questId -> the items it asks the player to bring with their counts, packed by
    # pack_requires, for every kept quest that asks for an item this build ships.
    quest_requires: dict[int, str] = field(default_factory=dict)
    # Brief QN1: questId -> (c, cl), its position in a chain of quests that share its title and
    # the chain's length, for every quest quest_chains numbers. Shipped as `qc`.
    quest_chains: dict[int, tuple[int, int]] = field(default_factory=dict)
    # Brief Q1: questId -> the game event it belongs to (quest_events). Shipped as `qe`.
    quest_events: dict[int, int] = field(default_factory=dict)
    # Brief Q1: questId -> its level and minimum level, packed (pack_quest_level). Shipped as `ql`.
    quest_levels: dict[int, int] = field(default_factory=dict)
    # Brief INT1b (the owner's ruling of 2026-10-10): questId -> the class mask of a class restricted
    # quest (quest_class_mask). Shipped as `qa`, beside an item row's `ac` (its allowed classes).
    quest_classes: dict[int, int] = field(default_factory=dict)
    # Brief IW1 (the owner's ruling "B" of 2026-10-22): a repeatable quest that can only be taken while
    # another is in the log (PrevQuestId < 0) -> that parent quest (quest_helpers). Shipped as `qw`.
    quest_helpers: dict[int, int] = field(default_factory=dict)
    # Brief PL1 (the owner's ruling "B" of 2026-10-22): questId -> the quests that come after it (its
    # chain links, quest_successors; since brief NX2 also its RequiredCondition and breadcrumb steps,
    # quest_later_steps), packed by pack_quests. Shipped as `qo`.
    quest_next: dict[int, str] = field(default_factory=dict)
    # Brief NX1 (the owner's ruling "2A" of 2026-10-22): questId -> the item it hands the player when
    # it is taken and how many (quest_template.SrcItemId and SrcItemCount), one record packed by
    # pack_requires, as a `qr` record is. Shipped as `qp`.
    quest_provided: dict[int, str] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)
    dropped: dict[str, int] = field(default_factory=dict)
    # Brief EK1, for the caller that places the names (never shipped): which names the table opens
    # a page for, by their index into `s` and by the rule that ships each ("creature": a c = 1, 6,
    # 7 or 12 row or list names it; "vendor": a c = 4 row or list; "trainer": `tr`; "giver": `qg`;
    # brief EO1 "objectGiver": the OBJECT names `og` carries), every object name a row or list names
    # with the category it is filed under (the lower where two), and the creature ids whose lists
    # `tr` holds.
    page_names: dict[str, frozenset[int]] = field(default_factory=dict)
    object_names: dict[int, int] = field(default_factory=dict)
    teachers: frozenset[int] = frozenset()

    def gpl_strings(self) -> list[str]:
        """EraSources.lua's `s` (brief GA1): every string in its place, a place in `blank` empty,
        and none after the last place that is not blank."""
        out = ["" if index in self.blank else value for index, value in enumerate(self.strings, start=1)]
        while out and len(out) in self.blank:
            out.pop()
        return out

    def class_value(self) -> dict:
        """Brief CT1: `tc` as it ships, { l = { packed list, ... }, c = { class id, ... }, n = {
        [string index] = list number } }."""
        return {
            "l": list(self.class_lists),
            "c": list(self.class_list_classes),
            "n": dict(self.class_trainer_lists),
        }

    def gpl_value(self, generated: str | None = None) -> dict:
        """EraSources.lua's value (brief GA1): the GPL_FIELDS tables and `s` with every blank place
        empty (gpl_strings). `generated` is the compile's stamp, the same one the header prints, and
        ships as `g` (brief E85) so the addon can read at run time which compile a table came from:
        a guess module's creature references index `s` and hold only against the table they were
        compiled with. Left out when no stamp is given, as the unit tests do. Checked against the
        allow list before it is handed back."""
        value = {
            "s": self.gpl_strings(),
            "r": dict(self.rows),
            "qt": dict(self.quest_titles),
            "ck": dict(self.kinds),
            "cd": dict(self.displays),
            "ci": dict(self.creature_ids),
            "oi": dict(self.object_ids),
            "qg": {index: list(pair) for index, pair in self.quest_givers.items()},
            "st": dict(self.subnames),
            "tr": dict(self.trainers),
            "qr": dict(self.quest_requires),
            "x": dict(self.list_index),
            "xl": list(self.lists),
        }
        if self.trainer_levels:
            value["tv"] = dict(self.trainer_levels)
        if self.class_trainer_lists:
            value["tc"] = self.class_value()
        # Brief EO1: the quests a world object starts and ends, absent where no object gives one.
        if self.object_givers:
            value["og"] = {index: list(pair) for index, pair in self.object_givers.items()}
        if self.quest_chains:
            value["qc"] = {quest: {"c": c, "cl": cl} for quest, (c, cl) in self.quest_chains.items()}
        if self.quest_events:
            value["qe"] = dict(self.quest_events)
        if self.quest_levels:
            value["ql"] = dict(self.quest_levels)
        if self.quest_classes:
            value["qa"] = dict(self.quest_classes)
        # Brief IW1: the repeatable helpers' parents, absent where none ships.
        if self.quest_helpers:
            value["qw"] = dict(self.quest_helpers)
        # Brief PL1: the quests that come after each quest, absent where none ships.
        if self.quest_next:
            value["qo"] = dict(self.quest_next)
        # Brief NX1: the item each quest hands the player when it is taken, absent where none ships.
        if self.quest_provided:
            value["qp"] = dict(self.quest_provided)
        if generated:
            value["g"] = generated
        check_gpl_value(value, self.blank)
        return value


# Brief GA1: the keys EraSources.lua (GPL-3.0) may hold, and nothing else. Each is read out of the
# pinned CMaNGOS dump (or pfQuest's area ids inside `r` and `xl`), selected, ordered and packed.
# Brief CT1 adds `tc`, the class trainers' lists (npc_trainer and npc_trainer_template, as `tr` and
# `tv` are): a key the owner's word puts here (docs/licensing.md). Brief EO1 adds `og`, the quests a
# world object starts and ends (gameobject_questrelation and gameobject_involvedrelation, as `qg`
# reads the creature ones), on the owner's ruling "3A" of 2026-10-22. Brief IW1 adds `qw`, a repeatable
# helper quest's parent (quest_template.PrevQuestId below 0), on the owner's ruling "B" of 2026-10-22.
# Brief PL1 adds `qo`, the quests that come after a quest (quest_template.PrevQuestId, NextQuestId and
# NextQuestInChain above 0), on the owner's ruling "B" of 2026-10-22 (the prerequisite links); brief NX2
# widens it with quest_template.RequiredCondition (the conditions rows asking for a quest rewarded) and
# BreadcrumbForQuestId, on the owner's word of 2026-10-23 ("It's probably okay to add chain columns").
# Brief NX1 adds `qp`, the item a quest hands the player when it is taken (quest_template.SrcItemId and
# SrcItemCount), on the owner's ruling "2A" of 2026-10-22 (the Classic Era provided items).
GPL_FIELDS = frozenset(
    {
        *("s", "r", "qt", "ck", "cd", "ci", "oi", "qg", "og", "st", "tr", "tv", "tc", "qr"),
        *("qc", "qe", "ql", "qa", "qw", "qo", "qp", "x", "xl", "g"),
    }
)
# The keys a packed module adds beside them (pack_module).
GPL_PACKING_FIELDS = frozenset({"legend", "packed"})


def check_gpl_value(value: Mapping, blank: Collection[int] = ()) -> None:
    """Every key of EraSources.lua's value in the allow list, and every blank place of `s` empty:
    a CMaNGOS fact, nothing else (brief GA1). Raises EraSourcesError."""
    extra = set(value) - GPL_FIELDS - GPL_PACKING_FIELDS
    if extra:
        raise EraSourcesError(
            f"EraSources.lua: keys not allowed in the GPL file: {', '.join(sorted(map(str, extra)))}"
        )
    strings = value.get("s") or []
    for index in sorted(blank):
        if 0 < index <= len(strings) and strings[index - 1]:
            raise EraSourcesError(
                f"EraSources.lua: s[{index}] holds {strings[index - 1]!r} in a place the file ships blank"
            )


# ----- fetching and verifying the pinned files -----------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_pin(pin: Pin, path: Path) -> int:
    """Check a file against its pinned size and sha256.

    A mismatch is a failure, not a reason to fetch again.
    """
    size = path.stat().st_size
    if size != pin.bytes:
        raise EraSourcesError(f"{path} is {size} bytes, expected {pin.bytes} for {pin.name} {pin.version}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != pin.sha256:
        raise EraSourcesError(
            f"{path} has sha256 {actual}, expected {pin.sha256} for {pin.name} {pin.version}; "
            "delete it and fetch again"
        )
    return size


def fetch_pin(
    pin: Pin,
    cache_dir: Path,
    *,
    force: bool = False,
    transport: httpx.BaseTransport | None = None,
    timeout: float = 300.0,
) -> Path:
    """Put one pinned file in the cache and return its path.

    One request, one file, only when the cache has not already got it. The cache directory is
    gitignored and nothing here is ever committed. CI never runs this: the suite reads hand
    written fixtures.
    """
    dest = pin.path(cache_dir)
    if dest.exists() and not force:
        verify_pin(pin, dest)
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers=dict(REQUEST_HEADERS),
        transport=transport,
    ) as client:
        try:
            response = client.get(pin.url)
        except httpx.HTTPError as exc:
            raise EraSourcesError(f"{pin.url}: {exc}") from exc
    if response.status_code != 200:
        raise EraSourcesError(f"{pin.url} returned HTTP {response.status_code}")
    part = dest.with_name(dest.name + ".part")
    part.write_bytes(response.content)
    try:
        verify_pin(pin, part)
    except EraSourcesError:
        part.unlink(missing_ok=True)
        raise
    shutil.move(str(part), str(dest))
    return dest


def external_inputs() -> list[dict]:
    """What the build manifest records about the files this stage read."""
    return [
        {
            "name": pin.name,
            "version": pin.version,
            "url": pin.url,
            "sha256": pin.sha256,
            "bytes": pin.bytes,
            "note": CREDIT,
        }
        for pin in PINS
    ]


# ----- reading the cmangos dump ----------------------------------------------------------------

_CREATE = re.compile(r"^CREATE TABLE `([a-z_]+)` \(")
_COLUMN = re.compile(r"^\s*`([A-Za-z_0-9]+)`")
_INSERT = re.compile(r"^INSERT INTO `([a-z_]+)` VALUES ")

# Every table this stage reads, and nothing else. Every other table in the dump, which is most
# of it, is skipped without being parsed at all.
WANTED_TABLES = (
    "creature",
    "creature_spawn_entry",
    "pool_creature",
    # Brief W18: a pool that names a creature ENTRY rather than a spawn, so every spawn of that
    # creature is one member of the pool; and the waypoints a spawn or a creature walks. Of the
    # waypoint tables only the ids, the point number and the two world coordinates are read.
    "pool_creature_template",
    "creature_movement",
    "creature_movement_template",
    "game_event_creature",
    "creature_template",
    "gameobject_template",
    "gameobject",
    "gameobject_spawn_entry",
    "creature_loot_template",
    "skinning_loot_template",
    "pickpocketing_loot_template",
    "gameobject_loot_template",
    "fishing_loot_template",
    "item_loot_template",
    "reference_loot_template",
    "npc_vendor",
    "npc_vendor_template",
    "quest_template",
    # Brief N3: which creature starts a quest and which one ends it. Two columns each, a creature
    # id and a quest id, and nothing else in either table.
    "creature_questrelation",
    "creature_involvedrelation",
    # Brief EO1 (the owner's ruling "3A" of 2026-10-22): which world object starts a quest and which
    # one ends it. Two columns each, an object id and a quest id, and nothing else in either table.
    "gameobject_questrelation",
    "gameobject_involvedrelation",
    # Brief P6a: which creature teaches which spell, directly or through a trainer template, and
    # spell_template's learn effects to turn a trainer's learn spell into the spell it teaches.
    "npc_trainer",
    "npc_trainer_template",
    "spell_template",
    # Brief Q1: which game event a quest belongs to. Two columns, both ids.
    "game_event_quest",
    # Brief NX2 (the owner's word of 2026-10-23): the condition rows a quest's RequiredCondition names,
    # four number columns (condition_entry, type, value1, value2) and flags, of the AND, OR and quest
    # rewarded rows alone; never the comments.
    "conditions",
)

LOOT_TABLES = {
    "creature_loot_template": "creature_loot",
    "skinning_loot_template": "skinning_loot",
    "pickpocketing_loot_template": "pickpocket_loot",
    "gameobject_loot_template": "object_loot",
    "fishing_loot_template": "fishing_loot",
    "item_loot_template": "item_loot",
    "reference_loot_template": "reference_loot",
}


def split_values(line: str, start: int) -> Iterator[list[str]]:
    """Yield each `(...)` tuple of an extended INSERT as a list of raw field strings.

    A hand rolled scanner rather than a regex, because the dump's text columns hold brackets,
    commas and escaped quotes. Nothing it yields is kept: the callers take the numeric columns
    and the names and throw the rest away without ever looking at it.
    """
    i = start
    depth = 0
    field_chars: list[str] = []
    row: list[str] = []
    in_string = False
    escaped = False
    length = len(line)
    while i < length:
        ch = line[i]
        i += 1
        if in_string:
            if escaped:
                field_chars.append(ch)
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "'":
                in_string = False
            else:
                field_chars.append(ch)
            continue
        if ch == "'":
            in_string = True
            continue
        if ch == "(":
            depth += 1
            field_chars = []
            row = []
            continue
        if ch == ")" and depth:
            depth -= 1
            row.append("".join(field_chars).strip())
            yield row
            field_chars = []
            continue
        if ch == "," and depth == 1:
            row.append("".join(field_chars).strip())
            field_chars = []
            continue
        if depth:
            field_chars.append(ch)
    return


def _num(value: str | float | None, default: float = 0.0) -> float:
    if value is None or value == "NULL" or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _int(value: str | float | None, default: int = 0) -> int:
    return int(_num(value, default))


@dataclass
class _Reading:
    """What the dump reader accumulates before it can put it on an EraInput.

    The three spawn side tables are keyed by guid and the dump states `creature` before any of
    them, so the rows are gathered here and joined once the file has been read.
    """

    loot: dict[str, dict[int, list[LootEntry]]] = field(
        default_factory=lambda: {name: defaultdict(list) for name in LOOT_TABLES}
    )
    vendor_rows: list[VendorOffer] = field(default_factory=list)
    vendor_template_rows: list[VendorOffer] = field(default_factory=list)
    # guid -> (creature id, map, x, y), the `creature` table with everything else dropped.
    spawn_rows: list[tuple[int, int, int, float, float]] = field(default_factory=list)
    spawn_entries: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))
    events: dict[int, int] = field(default_factory=dict)
    pools: set[int] = field(default_factory=set)
    # Brief W18: the creature ids `pool_creature_template` pools, the guids whose MovementType is
    # a waypoint walk, and the waypoints themselves as (point number, x, y), per guid and per
    # (creature id, path id).
    pool_entries: set[int] = field(default_factory=set)
    waypoint_guids: set[int] = field(default_factory=set)
    paths: dict[int, list[tuple[int, float, float]]] = field(default_factory=lambda: defaultdict(list))
    template_paths: dict[tuple[int, int], list[tuple[int, float, float]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    # guid -> (object id, map, x, y), the `gameobject` table with everything else dropped, and
    # the entries `gameobject_spawn_entry` names for a guid that leaves its id at 0.
    object_rows: list[tuple[int, int, int, float, float]] = field(default_factory=list)
    object_entries: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))


def read_cmangos(path: Path) -> EraInput:
    """Read the pinned dump into the facts this stage keeps, and nothing else.

    The dump is one gzipped mysqldump of 6,457 lines, each INSERT a single very long line, so
    it is read line by line and every table but WANTED_TABLES is skipped on the first regex.
    """
    era = EraInput()
    columns: dict[str, list[str]] = {}
    pending: str | None = None
    reading = _Reading()

    try:
        handle = gzip.open(path, "rt", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise EraSourcesError(f"cannot read {path}: {exc}") from exc
    with handle:
        for line in handle:
            if pending is not None:
                if line.startswith(")"):
                    pending = None
                    continue
                found = _COLUMN.match(line)
                if found:
                    columns[pending].append(found.group(1))
                continue
            create = _CREATE.match(line)
            if create:
                # A table this stage does not read has its definition skipped without a single
                # column name being collected, and its INSERT lines are never parsed at all.
                pending = create.group(1) if create.group(1) in WANTED_TABLES else None
                if pending is not None:
                    columns[pending] = []
                continue
            insert = _INSERT.match(line)
            if not insert:
                continue
            table = insert.group(1)
            if table not in WANTED_TABLES or table not in columns:
                continue
            cols = columns[table]
            index = {name: position for position, name in enumerate(cols)}
            width = len(cols)
            for row in split_values(line, insert.end()):
                if len(row) != width:
                    continue
                _absorb(era, reading, table, row, index)

    for table, attribute in LOOT_TABLES.items():
        setattr(era, attribute, {entry: rows for entry, rows in sorted(reading.loot[table].items())})
    era.vendor_offers = reading.vendor_rows
    era.vendor_template_offers = reading.vendor_template_rows
    era.spawns = tuple(
        Spawn(
            guid=guid,
            creature=creature,
            map=map_id,
            x=x,
            y=y,
            event=reading.events.get(guid, 0),
            pooled=guid in reading.pools or (creature != 0 and creature in reading.pool_entries),
        )
        for guid, creature, map_id, x, y in sorted(reading.spawn_rows)
    )
    era.waypoint_guids = set(reading.waypoint_guids)
    era.paths = {guid: _walk(points) for guid, points in sorted(reading.paths.items())}
    template_paths: dict[int, dict[int, tuple[tuple[float, float], ...]]] = defaultdict(dict)
    for (entry, path_id), points in sorted(reading.template_paths.items()):
        template_paths[entry][path_id] = _walk(points)
    era.template_paths = dict(template_paths)
    era.spawn_entries = {
        guid: tuple(sorted(set(entries))) for guid, entries in sorted(reading.spawn_entries.items())
    }
    era.object_spawn_maps = object_maps(reading.object_rows, reading.object_entries)
    era.object_spawns, era.object_spawn_entries = lootable_object_spawns(
        reading.object_rows, reading.object_entries, era.objects, quest_objects(era)
    )
    return era


def _walk(points: Sequence[tuple[int, float, float]]) -> tuple[tuple[float, float], ...]:
    """One path's waypoints in walking order (by point number), as world (x, y)."""
    return tuple((x, y) for _point, x, y in sorted(points))


def object_maps(rows: Sequence[tuple], entries: Mapping[int, Sequence[int]]) -> dict[int, tuple[int, ...]]:
    """object id -> the maps it spawns on, ascending. A guid with no id of its own stands for
    every entry `gameobject_spawn_entry` names for it. Each row is (guid, id, map, ...): the
    position the reader keeps behind the map is not read here."""
    maps: dict[int, set[int]] = defaultdict(set)
    for guid, oid, map_id, *_rest in rows:
        for member in (oid,) if oid else entries.get(guid, ()):
            if member:
                maps[member].add(map_id)
    return {oid: tuple(sorted(found)) for oid, found in sorted(maps.items())}


def _lootable(obj: ObjectFacts | None) -> bool:
    """A chest or a fishing hole with a loot template: the only objects a source row can name."""
    return obj is not None and obj.kind in (GO_TYPE_CHEST, GO_TYPE_FISHING_HOLE) and bool(obj.loot)


def quest_objects(era_input: CmangosFacts) -> frozenset[int]:
    """Brief EO1: every object id gameobject_questrelation or gameobject_involvedrelation names, the
    objects that start or end a quest."""
    return frozenset(
        int(oid)
        for relation in (era_input.object_quest_starts, era_input.object_quest_ends)
        for oid, _q in relation
    )


def lootable_object_spawns(
    rows: Sequence[tuple[int, int, int, float, float]],
    entries: Mapping[int, Sequence[int]],
    objects: Mapping[int, ObjectFacts],
    quest_givers: Collection[int] = frozenset(),
) -> tuple[tuple[Spawn, ...], dict[int, tuple[int, ...]]]:
    """The `gameobject` rows an object pin could ever be made from, as spawns, and the spawn
    entries of the guids among them that leave their id at 0.

    Only a chest or a fishing hole with a loot template can be the object a source row names, and
    (brief EO1) only an object `quest_givers` names (quest_objects) can be a quest's giver or turn
    in, so every other object's spawn (a door, a chair, a mailbox) is dropped here, at the end of
    the streaming pass, and never reaches an EraInput. A Spawn's `creature` field holds the OBJECT
    id: the shape is the creature table's, and so is every rule read over it.
    """

    def kept(oid: int) -> bool:
        return _lootable(objects.get(oid)) or oid in quest_givers

    kept_entries: dict[int, tuple[int, ...]] = {}
    spawns: list[Spawn] = []
    for guid, oid, map_id, x, y in sorted(rows):
        if oid:
            if not kept(oid):
                continue
        else:
            members = tuple(sorted({e for e in entries.get(guid, ()) if kept(e)}))
            if not members:
                continue
            kept_entries[guid] = members
        spawns.append(Spawn(guid=guid, creature=oid, map=map_id, x=x, y=y))
    return tuple(spawns), kept_entries


def _absorb(
    era: EraInput,
    reading: _Reading,
    table: str,
    row: list[str],
    index: Mapping[str, int],
) -> None:
    """Take one parsed row into the facts, by table. Every other column is dropped here."""

    def col(name: str) -> str | None:
        position = index.get(name)
        return row[position] if position is not None else None

    if table in LOOT_TABLES:
        entry = _int(col("entry"))
        item = _int(col("item"))
        mincount = _int(col("mincountOrRef"))
        reading.loot[table][entry].append(
            LootEntry(
                item=item,
                chance=_num(col("ChanceOrQuestChance")),
                group=_int(col("groupid")),
                reference=-mincount if mincount < 0 else 0,
            )
        )
        return
    if table == "creature_template":
        cid = _int(col("Entry"))
        display = 0
        # ModelId1 is the model a creature is nearly always drawn with; 2 to 4 are the other
        # models the server may pick at spawn. The first one stated is the answer, so a row that
        # leaves ModelId1 at 0 falls back through the three behind it rather than losing its id.
        for slot in ("ModelId1", "ModelId2", "ModelId3", "ModelId4"):
            display = _int(col(slot))
            if display > 0:
                break
        era.creatures[cid] = CreatureFacts(
            id=cid,
            name=(col("Name") or "").strip(),
            min_level=_int(col("MinLevel")),
            max_level=_int(col("MaxLevel")),
            rank=_int(col("Rank")),
            creature_type=_int(col("CreatureType")),
            family=_int(col("Family")),
            display=max(0, display),
            loot=_int(col("LootId")),
            skinning=_int(col("SkinningLootId")),
            pickpocket=_int(col("PickpocketLootId")),
            vendor_template=_int(col("VendorTemplateId")),
            # Brief T1, the owner's ruling of 2026-09-27: the title under the name and the
            # faction template id. The pinned dump states one `Faction` column; a later dump's
            # `FactionAlliance` is the same template for the side that matters first.
            # An unquoted NULL is how the dump leaves a SubName out, on nearly every creature.
            subname="" if col("SubName") in (None, "NULL") else (col("SubName") or "").strip(),
            faction=_int(col("Faction") if col("Faction") is not None else col("FactionAlliance")),
            trainer_template=_int(col("TrainerTemplateId")),
            trainer_type=_int(col("TrainerType")),
            trainer_class=_int(col("TrainerClass")),
        )
        return
    if table in ("npc_trainer", "npc_trainer_template"):
        # Brief P6a: the entry and the spell; brief TR5 (the owner's ruling of 2026-10-13) the
        # required skill rank beside them; brief CT1 (the owner, 2026-10-17) the required level and
        # the price, which only a class trainer's list ships (`tc`). Not the required skill line or
        # abilities, not the condition.
        pair = (_int(col("entry")), _int(col("spell")))
        (era.trainer_spells if table == "npc_trainer" else era.trainer_template_spells).append(pair)
        if "reqskillvalue" in index:
            ranks = era.trainer_ranks if table == "npc_trainer" else era.trainer_template_ranks
            rank = max(0, _int(col("reqskillvalue")))
            ranks[pair] = min(rank, ranks.get(pair, rank))
        if "reqlevel" in index and "spellcost" in index:
            terms = era.trainer_terms if table == "npc_trainer" else era.trainer_template_terms
            level, price = max(0, _int(col("reqlevel"))), max(0, _int(col("spellcost")))
            held = terms.get(pair)
            terms[pair] = (level, price) if held is None else (min(held[0], level), min(held[1], price))
        return
    if table == "spell_template":
        # Brief P6a: the id and the three effects with their trigger spells, and only for a spell
        # one of whose effects is a learn effect. No name, no text, nothing else of the spell.
        for slot in (1, 2, 3):
            if _int(col(f"Effect{slot}")) == SPELL_EFFECT_LEARN_SPELL:
                taught = _int(col(f"EffectTriggerSpell{slot}"))
                if taught > 0:
                    era.learned_spells[_int(col("Id"))] = taught
                    break
        return
    if table == "gameobject_template":
        oid = _int(col("entry"))
        era.objects[oid] = ObjectFacts(
            id=oid,
            name=(col("name") or "").strip(),
            kind=_int(col("type")),
            lock=_int(col("data0")),
            loot=_int(col("data1")),
        )
        return
    if table in ("npc_vendor", "npc_vendor_template"):
        offer = VendorOffer(vendor=_int(col("entry")), item=_int(col("item")), stock=_int(col("maxcount")))
        (reading.vendor_rows if table == "npc_vendor" else reading.vendor_template_rows).append(offer)
        return
    if table == "creature":
        # The position and the map, and nothing else: not the z, not the orientation, not the
        # respawn times and not the spawn distance. Since brief W18 the movement type is read for
        # one bit, whether the spawn walks its waypoints (MOVEMENT_WAYPOINT), kept apart from
        # Spawn in EraInput.waypoint_guids.
        if _int(col("MovementType")) == MOVEMENT_WAYPOINT:
            reading.waypoint_guids.add(_int(col("guid")))
        reading.spawn_rows.append(
            (
                _int(col("guid")),
                _int(col("id")),
                _int(col("map")),
                _num(col("position_x")),
                _num(col("position_y")),
            )
        )
        return
    if table == "creature_spawn_entry":
        reading.spawn_entries[_int(col("guid"))].append(_int(col("entry")))
        return
    if table == "gameobject":
        # The map and the position, and nothing else: not the z, not the orientation, not the
        # rotation, not the spawn mask and not the respawn times. Since 2026-09-27 (brief D7) the
        # position is read for the object map pins, the way the `creature` table's always was.
        reading.object_rows.append(
            (
                _int(col("guid")),
                _int(col("id")),
                _int(col("map")),
                _num(col("position_x")),
                _num(col("position_y")),
            )
        )
        return
    if table == "gameobject_spawn_entry":
        reading.object_entries[_int(col("guid"))].append(_int(col("entry")))
        return
    if table == "game_event_creature":
        reading.events[_int(col("guid"))] = _int(col("event"))
        return
    if table == "pool_creature":
        # The pool's own chance and description are read for nothing: what matters is that the
        # row is one member of a pool, so the point is a place the creature is found.
        reading.pools.add(_int(col("guid")))
        return
    if table == "pool_creature_template":
        # Brief W18: the same, for a pool that names the creature rather than one spawn of it.
        reading.pool_entries.add(_int(col("id")))
        return
    if table == "creature_movement":
        # Brief W18: the point number and the two world coordinates. Not the z, the orientation,
        # the wait time, the script or the comment.
        point = (_int(col("Point")), _num(col("PositionX")), _num(col("PositionY")))
        reading.paths[_int(col("Id"))].append(point)
        return
    if table == "creature_movement_template":
        point = (_int(col("Point")), _num(col("PositionX")), _num(col("PositionY")))
        reading.template_paths[(_int(col("Entry")), _int(col("PathId")))].append(point)
        return
    if table in ("creature_questrelation", "creature_involvedrelation"):
        pair = (_int(col("id")), _int(col("quest")))
        (era.quest_starts if table == "creature_questrelation" else era.quest_ends).append(pair)
        return
    if table in ("gameobject_questrelation", "gameobject_involvedrelation"):
        # Brief EO1: the object and the quest, two ids, the creature tables' twins.
        pair = (_int(col("id")), _int(col("quest")))
        (era.object_quest_starts if table == "gameobject_questrelation" else era.object_quest_ends).append(
            pair
        )
        return
    if table == "conditions":
        # Brief NX2: an AND, OR or NOT row, or one that asks for a quest rewarded; four numbers and the
        # flags. Every other kind of row (an aura, an item, a level, ...) is dropped unread.
        kind = _int(col("type"))
        if kind in CONDITION_KINDS_READ:
            era.conditions[_int(col("condition_entry"))] = (
                kind,
                _int(col("value1")),
                _int(col("value2")),
                _int(col("flags")),
            )
        return
    if table == "game_event_quest":
        # Brief Q1: a quest and a game event it belongs to, two ids.
        quest = _int(col("quest"))
        era.quest_event_links[quest] = tuple(
            sorted({*era.quest_event_links.get(quest, ()), _int(col("event"))})
        )
        return
    if table == "quest_template":
        qid = _int(col("entry"))
        title = (col("Title") or "").strip()
        if qid > 0:
            era.quest_ids.add(qid)
            if title:
                era.quest_names[qid] = title
            # Brief QN1, the owner's ruling of 2026-10-03: the chain link columns, ids only.
            links = (_int(col("PrevQuestId")), _int(col("NextQuestId")), _int(col("NextQuestInChain")))
            if any(links):
                era.quest_links[qid] = links
            # Brief NX1, the owner's ruling "2A" of 2026-10-22: the item the quest hands over when it
            # is taken, and how many, ids and counts only.
            source = _int(col("SrcItemId"))
            if source > 0:
                era.quest_sources[qid] = (source, max(1, _int(col("SrcItemCount"))))
            # Brief NX2, the owner's word of 2026-10-23: the condition row the quest asks to hold before
            # it can be taken, and the quest a breadcrumb leads to, ids only.
            condition = _int(col("RequiredCondition"))
            if condition > 0:
                era.quest_conditions[qid] = condition
            breadcrumb = _int(col("BreadcrumbForQuestId"))
            if breadcrumb > 0:
                era.quest_breadcrumbs[qid] = breadcrumb
        fixed: list[int] = []
        for key in ("RewItemId1", "RewItemId2", "RewItemId3", "RewItemId4"):
            value = _int(col(key))
            if value > 0:
                fixed.append(value)
        choices: list[int] = []
        for number in range(1, 7):
            value = _int(col(f"RewChoiceItemId{number}"))
            if value > 0:
                choices.append(value)
        items: list[int] = fixed + choices
        if qid > 0 and items:
            era.quest_rewards[qid] = (tuple(dict.fromkeys(fixed)), tuple(dict.fromkeys(choices)))
        # Brief Q1: a reputation turn in (is_turn_in), an id only; and the quest's two levels.
        if qid > 0 and is_turn_in(col):
            era.quest_turn_ins.add(qid)
        if qid > 0 and (_int(col("QuestLevel")) > 0 or _int(col("MinLevel")) > 0):
            era.quest_levels[qid] = (max(0, _int(col("QuestLevel"))), max(0, _int(col("MinLevel"))))
        # Brief INT1b (the owner's ruling of 2026-10-10): the classes the quest is for, a mask.
        classes = quest_class_mask(_int(col("RequiredClasses")), _int(col("ZoneOrSort")))
        if qid > 0 and classes:
            era.quest_classes[qid] = classes
        # Brief QS2: every quest's race mask, not only the ones `quests` keeps below.
        races = _int(col("RequiredRaces"))
        if qid > 0 and races > 0:
            era.quest_races[qid] = races
        # Addon brief QV1: the factions the quest raises, ids only, in slot order.
        reputations = tuple(
            _int(col(f"RewRepFaction{number}"))
            for number in range(1, 6)
            if _int(col(f"RewRepFaction{number}")) > 0 and _int(col(f"RewRepValue{number}")) > 0
        )
        if qid > 0 and reputations:
            era.quest_reputations[qid] = tuple(dict.fromkeys(reputations))
        requires: list[int] = []
        require_counts: list[int] = []
        for number in range(1, 5):
            value = _int(col(f"ReqItemId{number}"))
            if value > 0:
                requires.append(value)
                # Brief W12, the owner's ruling of 2026-09-29: the count beside the id, a number.
                require_counts.append(_int(col(f"ReqItemCount{number}")))
        # A quest that only asks for something is kept too: it hands nothing over, so it makes
        # no c=3 row, but it is what lets a quest only drop name the quest behind it.
        if title and (items or requires):
            era.quests[qid] = QuestFacts(
                id=qid,
                title=title,
                races=_int(col("RequiredRaces")),
                items=tuple(items),
                requires=tuple(requires),
                require_counts=tuple(require_counts),
            )
        return


# ----- reading pfQuest's zone map ---------------------------------------------------------------

_PF_ID = re.compile(r"^  \[(\d+)\] = \{")
# { x, y, zone, respawn }. The third number is the area id, which is what this file has always
# been read for. The two coordinates in front of it are already a percentage of the zone map, and
# since 2026-09-20 they are read as well, for two things and no more: to tell one spawn of a
# creature from another so that each one's own area id can be taken, and to CHECK the formula the
# pipeline computes its own pins with. No pfQuest coordinate is ever shipped. The respawn timer
# is matched so the line can be recognised and is discarded.
_PF_COORD = re.compile(r"^\s*\[\d+\] = \{ (-?[\d.]+), (-?[\d.]+), (\d+), -?[\d.]+ \},?\s*$")


def read_spawn_points(path: Path) -> dict[int, tuple[SpawnPoint, ...]]:
    """id -> each spawn pfQuest states for it, as a zone percentage and an area id.

    Read with a line reader rather than a Lua interpreter so that nothing else in the file can
    reach the pipeline: a line that is not one spawn in the one shape above is not read at all.
    """
    points: dict[int, list[SpawnPoint]] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise EraSourcesError(f"cannot read {path}: {exc}") from exc
    current: int | None = None
    for line in text.splitlines():
        found = _PF_ID.match(line)
        if found:
            current = int(found.group(1))
            continue
        if current is None:
            continue
        coord = _PF_COORD.match(line)
        if coord:
            area = int(coord.group(3))
            if area > 0:
                points.setdefault(current, []).append(
                    SpawnPoint(x=float(coord.group(1)), y=float(coord.group(2)), area=area)
                )
    return {key: tuple(value) for key, value in sorted(points.items())}


def zones_from_points(points: Mapping[int, Sequence[SpawnPoint]]) -> dict[int, tuple[int, ...]]:
    """id -> the area ids that id spawns in, commonest first.

    Commonest first, ties by the lower area id, so the one area a row carries never depends on
    the order the file happened to state its spawns in.
    """
    zones: dict[int, tuple[int, ...]] = {}
    for key in sorted(points):
        seen: dict[int, int] = {}
        for point in points[key]:
            seen[point.area] = seen.get(point.area, 0) + 1
        if seen:
            order = sorted(seen.items(), key=lambda pair: (-pair[1], pair[0]))
            zones[key] = tuple(area for area, _count in order)
    return zones


def read_zone_map(path: Path) -> dict[int, tuple[int, ...]]:
    """id -> the area ids that id spawns in, commonest first, and nothing else. The stage itself
    reads the objects file through read_spawn_points since brief D7, because the object map pins
    match each spawn to its area the way the creature pins do; this is the zones alone."""
    return zones_from_points(read_spawn_points(path))


# ----- the rules ----------------------------------------------------------------------------


def chance_percent(value: float | None) -> float | None:
    """A loot table chance as a percentage, or None when the number is not worth shipping.

    The source states a percentage directly. Zero, anything above 100 and anything that rounds
    below 0.1 are refused, and the row is kept without a chance, which reads as "we do not
    know" instead of as a wrong number. A quest only drop reaches this as its absolute value,
    under exactly the same rules as any other chance.
    """
    if value is None:
        return None
    percent = round(float(value), CHANCE_PLACES)
    if percent < MIN_CHANCE or percent > 100.0:
        return None
    return percent


def is_quest_only(entry: LootEntry) -> bool:
    """A negative ChanceOrQuestChance: the item drops only while the player is on the quest.

    The row is kept and marked. "Which creature drops it" is the answer a player wants for a
    quest item, and the addon can say the condition in words even though it cannot check it.
    The number itself is the absolute value, which is the chance the source states.
    """
    return entry.chance < 0


def is_scaffolding(name: str) -> bool:
    """Whether a creature or object name marks a row as build scaffolding, not content.

    Deliberately narrow. A loose rule ("starts with Old", "contains TEST") refuses Old
    Murk-Eye, Old Icebeard and Old Serra'kis, which are real rare creatures with real loot.
    Brief TB3: a test name (test_rows.is_test_name, the one filter every writer shares: "Test
    Banker", "Warlock (TEST)", "Placeholder - Jasperlode Mine") is scaffolding too. Its markers are
    as narrow, so "Test of Faith" and "Old Murk-Eye" stay content.
    """
    if not name:
        return True
    return any(marker in name for marker in SCAFFOLDING_MARKERS) or is_test_name(name)


def faction_of(races: int) -> int | None:
    """The side a quest's race mask implies, or None for a quest open to everyone."""
    if races <= 0:
        return None
    alliance = bool(races & RACE_MASK_ALLIANCE)
    horde = bool(races & RACE_MASK_HORDE)
    if alliance and not horde:
        return FACTION_ALLIANCE
    if horde and not alliance:
        return FACTION_HORDE
    return None


@dataclass(frozen=True)
class Drop:
    """What one loot template gives one item: how often, and on what condition.

    `quest_only` is the source's negative chance, meaning the item drops only while the player
    is on a quest that asks for it. It is a fact about the drop, not a reason to hide it.
    """

    chance: float
    quest_only: bool = False


@dataclass(frozen=True)
class _Normalised:
    """One loot row after the group rule, with its chance made positive and its flag kept."""

    item: int
    chance: float
    reference: int
    quest_only: bool


def _group_chances(entries: Sequence[LootEntry]) -> list[_Normalised]:
    """Apply the loot group rule: a zero chance inside a group shares what the group has left.

    A groupid of 0 means the row rolls on its own. Inside a group exactly one row is chosen,
    the explicit chances are taken first and the rows that state none divide the remainder.
    A quest chance is negative in the source, so the group arithmetic is done on absolute
    values and the flag travels beside the number.
    """
    by_group: dict[int, list[LootEntry]] = defaultdict(list)
    for entry in entries:
        by_group[entry.group].append(entry)
    out: list[_Normalised] = []
    for group, rows in sorted(by_group.items()):
        stated = [_Normalised(row.item, abs(row.chance), row.reference, is_quest_only(row)) for row in rows]
        if group == 0:
            out.extend(stated)
            continue
        explicit = sum(row.chance for row in stated if row.chance > 0)
        zeros = [row for row in stated if row.chance <= 0]
        share = max(0.0, 100.0 - explicit) / len(zeros) if zeros else 0.0
        for row in stated:
            out.append(row if row.chance > 0 else _Normalised(row.item, share, row.reference, row.quest_only))
    return out


def expand_loot(
    table: Mapping[int, Sequence[LootEntry]],
    reference_loot: Mapping[int, Sequence[LootEntry]],
    dropped: dict[str, int],
) -> dict[int, dict[int, Drop]]:
    """template entry -> {itemId: the best Drop that template gives it}.

    A row whose `reference` is set points at a reference template rather than an item, and the
    item's effective chance is the two multiplied. References are followed to
    MAX_REFERENCE_DEPTH and a template that reappears on its own path is a loop: it is counted
    and abandoned rather than followed. A reference reached through a quest chance is quest
    only all the way down.

    Where one template gives the same item both ways, the unconditional drop wins: it is the
    better answer and the condition would be false of it.
    """

    def walk(
        entries: Sequence[LootEntry],
        weight: float,
        path: tuple[int, ...],
        quest_only: bool,
        into: dict[int, Drop],
    ) -> None:
        for entry in _group_chances(entries):
            conditional = quest_only or entry.quest_only
            if entry.reference:
                if entry.reference in path or len(path) >= MAX_REFERENCE_DEPTH:
                    dropped["refLoop"] += 1
                    continue
                walk(
                    reference_loot.get(entry.reference, ()),
                    weight * entry.chance / 100.0,
                    (*path, entry.reference),
                    conditional,
                    into,
                )
                continue
            if entry.item <= 0:
                continue
            # weight is 1.0 at the top and the product of the referencing rows' chances below
            # it, so a 20% row pointing at a template that gives the item 50% reads 10%.
            #
            # A chance of zero still makes a row: the source states plenty of them, and the
            # honest answer is "this creature drops it and we cannot say how often", not
            # silence. The chance rule drops the number later and keeps the row.
            found = into.get(entry.item)
            effective = weight * entry.chance
            better = (not conditional, effective)
            if found is None or better > (not found.quest_only, found.chance):
                into[entry.item] = Drop(chance=effective, quest_only=conditional)

    out: dict[int, dict[int, Drop]] = {}
    for entry_id in sorted(table):
        acc: dict[int, Drop] = {}
        walk(table[entry_id], 1.0, (), False, acc)
        out[entry_id] = acc
    return out


class _Strings:
    """A string table that hands back 1 based indexes and keeps each string once.

    Brief EK1: beside the strings, a place can be RESERVED by a sort key alone (`reserve`), for a
    string of the caller's this table never holds: it takes its place in the sort by its key and is
    blank in the table sorted_table hands back.
    """

    def __init__(self) -> None:
        self._index: dict[str, int] = {}
        self._values: list[str] = []
        # Brief GA1: the strings a CMaNGOS field put in, so blank_only can tell the rest.
        self._cmangos: set[str] = set()
        # Brief EK1: (rank, tie) -> insertion index, for each place reserved by its key alone.
        self._reserved: dict[tuple[int, int], int] = {}

    def add(self, value: str, *, blank: bool = False) -> int:
        """`blank` is a dump string added only because a place of the caller's is that very string
        (BuildFacts.area_ranks with no tie): it takes its place in the sort like any other, and
        EraSources.lua ships that place blank unless a CMaNGOS field names the same string too."""
        found = self._index.get(value)
        if found is None:
            found = len(self._values) + 1
            self._index[value] = found
            self._values.append(value)
        if not blank:
            self._cmangos.add(value)
        return found

    def reserve(self, rank: int, tie: int) -> int:
        """Brief EK1: a place for a string of the caller's, by its key alone (BuildFacts.area_ranks
        and area_ties): it sorts after every dump string before `rank` in dump_strings and before
        the rest, `tie` ordering the places of one rank. Always blank; the same key, the same place."""
        found = self._reserved.get((rank, tie))
        if found is None:
            found = len(self._values) + 1
            self._reserved[(rank, tie)] = found
            self._values.append("")
        return found

    def blank_only(self) -> set[int]:
        """The insertion index of every place no CMaNGOS field put a string in (brief GA1): each
        reserved place, and each blank string no field of the dump names as well."""
        found = {index for value, index in self._index.items() if value not in self._cmangos}
        return found | set(self._reserved.values())

    def find(self, value: str) -> int:
        """The insertion index a string already has, or 0 where the table does not hold it."""
        return self._index.get(value, 0)

    def value(self, index: int) -> str:
        """The string at one insertion index, or "" for a reserved place or an index this table
        never handed out."""
        return self._values[index - 1] if 0 < index <= len(self._values) else ""

    def sorted_table(
        self, first: Collection[int] = (), positions: Mapping[str, int] | None = None
    ) -> tuple[list[str], dict[int, int]]:
        """The strings in sorted order, and a remap from the insertion index to the new one.

        Sorting keeps the file stable: the same inputs always compile to the same bytes.

        `first` is insertion indexes that must take the lowest numbers once the table is too long
        for them (brief W15, 2026-09-29): the names a packed list record carries, whose field is
        PACK_NAME_DIGITS base 91 digits and stops at 8,280. A table longer than that is two sorted
        runs, those strings and then every other one, so every list record still fits; a table
        that fits is the one sorted run it always was, so a small table's indexes do not move.

        Brief EK1: a reserved place sorts by its key among the strings of its run: (rank, tie)
        after every string whose place in `positions` (dump_strings, each string's index there) is
        below `rank`, before the rest, and before any other place of its rank with a higher tie.
        A reserved place is "" in the table handed back.
        """
        fits = len(self._values) < PACK_BASE**PACK_NAME_DIGITS
        front = set() if fits else {self._values[i - 1] for i in first if 0 < i <= len(self._values)}
        rest = sorted(value for value in self._index if value not in front)
        if self._reserved:
            missing = [value for value in rest if value not in (positions or {})]
            if missing:
                raise EraSourcesError(
                    f"{len(missing)} strings of s are not the dump's own (dump_strings), "
                    f"so a reserved place cannot be sorted among them: {missing[:3]}"
                )
            keyed = [((positions[value], 1, 0), self._index[value]) for value in rest]  # type: ignore[index]
            keyed += [((rank, 0, tie), index) for (rank, tie), index in self._reserved.items()]
            second = [index for _key, index in sorted(keyed)]
        else:
            second = [self._index[value] for value in rest]
        order = [self._index[value] for value in sorted(front)] + second
        remap = {index: position + 1 for position, index in enumerate(order)}
        return [self._values[index - 1] for index in order], remap


def dump_strings(era_input: CmangosFacts) -> list[str]:
    """Brief EK1: every string derive can put in `s`, from the dump alone, sorted and once each:
    each creature's name and SubName, each object's name and each quest title (`quests` and
    `quest_names`). The order BuildFacts.area_ranks counts in: a caller's string for an area is
    handed over as how many of these sort before it, never as the string."""
    found = {facts.name for facts in era_input.creatures.values()}
    found.update(facts.subname for facts in era_input.creatures.values())
    found.update(obj.name for obj in era_input.objects.values())
    found.update(quest.title for quest in era_input.quests.values())
    found.update(era_input.quest_names.values())
    found.discard("")
    return sorted(found)


# ----- one candidate source, before the caps ---------------------------------------------------


@dataclass(frozen=True)
class _Source:
    """One thing that gives an item, before the caps decide whether it gets named."""

    category: int
    name: str = ""
    area: int = 0
    chance: float = 0.0
    stock: int = 0
    container: int = 0
    min_level: int = 0
    max_level: int = 0
    # The source says this one only drops while the player is on a quest that asks for it.
    quest_only: bool = False
    # The quest that asks for it, where the source names one without guesswork.
    quest: int = 0
    # A herb or a vein only: where this zone stands in the node's own zones, commonest first.
    # It orders a node's zone rows (see _node_rows) and nothing else.
    spot: int = 0

    def order(self) -> tuple:
        """Best first, and never by anything that varies between runs.

        A drop anyone can get sorts before a quest only one, so the cap of three named rows
        spends its slots on the answer that is true for every player first.
        """
        return (self.quest_only, -self.chance, self.name, self.area, self.container)


def _zone_of(zones: Mapping[int, tuple[int, ...]], key: int, allowed: Collection[int]) -> int:
    """The area id a creature or object is most often found in, among the `allowed` ones."""
    for area in zones.get(key, ()):  # commonest first
        if area in allowed:
            return area
    return 0


def _node_category(obj: ObjectFacts, selected: BuildFacts) -> int:
    """The category a lootable object's rows are filed under: a fishing hole is fished (the dump's
    own type), and a chest is what its lock files it under (BuildFacts.node_categories, brief EK1:
    the caller reads the build's Lock and LockType), or a plain chest."""
    if obj.kind == GO_TYPE_FISHING_HOLE:
        return CAT_FISHED
    return selected.node_categories.get(obj.id, CAT_OBJECT)


def collect(
    era_input: CmangosFacts, selected: BuildFacts, dropped: dict[str, int]
) -> dict[int, list[_Source]]:
    """Every candidate source for every item, before any cap is applied. `era_input` is the dump's
    facts (a CmangosOnly or an EraInput) and `selected` the caller's plain selections (BuildFacts)."""
    allowed = selected.row_areas
    creatures = era_input.creatures
    objects = era_input.objects
    candidates: dict[int, list[_Source]] = defaultdict(list)

    # itemId -> the one quest whose own required item fields ask for it. The source states
    # this directly, so it costs nothing and guesses nothing: where two or more quests ask
    # for the same item there is no single right answer and the row simply carries no q.
    asks: dict[int, list[int]] = defaultdict(list)
    for quest_id in sorted(era_input.quests):
        for required in era_input.quests[quest_id].requires:
            asks[required].append(quest_id)

    def asked_by(item: int) -> int:
        found = asks.get(item, ())
        return found[0] if len(found) == 1 else 0

    # Where a creature lives inside an instance, that instance IS its place (BuildFacts
    # creature_instances, brief EK1: the caller reads the build's Map). Only ever consulted for a
    # creature neither database names an open world area for.
    inside = selected.creature_instances

    def place_of(cid: int) -> int:
        """The area a creature's row carries: the open world one first, the instance second."""
        return _zone_of(era_input.unit_zones, cid, allowed) or inside.get(cid, 0)

    expanded = {
        "creature": expand_loot(era_input.creature_loot, era_input.reference_loot, dropped),
        "skinning": expand_loot(era_input.skinning_loot, era_input.reference_loot, dropped),
        "pickpocket": expand_loot(era_input.pickpocket_loot, era_input.reference_loot, dropped),
        "object": expand_loot(era_input.object_loot, era_input.reference_loot, dropped),
        "fishing": expand_loot(era_input.fishing_loot, era_input.reference_loot, dropped),
        "item": expand_loot(era_input.item_loot, era_input.reference_loot, dropped),
    }

    # Creatures: one loot template can serve many creatures, so the map runs the other way.
    for attribute, key, category in (
        ("creature", "loot", CAT_CREATURE_DROP),
        ("skinning", "skinning", CAT_SKINNED),
        ("pickpocket", "pickpocket", CAT_PICKPOCKET),
    ):
        by_template: dict[int, list[int]] = defaultdict(list)
        for cid in sorted(creatures):
            template = getattr(creatures[cid], key)
            if template:
                by_template[template].append(cid)
        for template, items in expanded[attribute].items():
            for cid in by_template.get(template, ()):
                facts = creatures[cid]
                if is_scaffolding(facts.name):
                    dropped["scaffolding"] += 1
                    continue
                # A boss keeps the category the first version of this module used, because a
                # boss drop is a different answer from "a hundred trash mobs drop it".
                kind = CAT_BOSS_DROP if (category == CAT_CREATURE_DROP and facts.rank == 3) else category
                for item, drop in sorted(items.items()):
                    candidates[item].append(
                        _Source(
                            category=kind,
                            name=facts.name,
                            area=place_of(cid),
                            chance=drop.chance,
                            min_level=facts.min_level,
                            max_level=facts.max_level,
                            quest_only=drop.quest_only,
                            quest=asked_by(item) if drop.quest_only else 0,
                        )
                    )

    # World objects. Only a chest and a fishing hole ever carry loot a player can take.
    inside_objects = selected.object_instances
    by_object_template: dict[int, list[int]] = defaultdict(list)
    for oid in sorted(objects):
        obj = objects[oid]
        if obj.kind in (GO_TYPE_CHEST, GO_TYPE_FISHING_HOLE) and obj.loot:
            by_object_template[obj.loot].append(oid)
    for template, items in expanded["object"].items():
        for oid in by_object_template.get(template, ()):
            obj = objects[oid]
            if is_scaffolding(obj.name):
                dropped["scaffolding"] += 1
                continue
            category = _node_category(obj, selected)
            spawn_zones = [area for area in era_input.object_zones.get(oid, ()) if area in allowed]
            # A herb or a vein is one name in many places, so it is listed by zone, commonest
            # first; one pfQuest places nowhere takes the instance it stands inside, where the
            # dump's own spawns say so. Everything else is listed once, in the zone it is
            # commonest in.
            if category in NODE_CATEGORIES and spawn_zones:
                places = spawn_zones[:MAX_NODE_ZONES]
            elif category in NODE_CATEGORIES and inside_objects.get(oid):
                places = [inside_objects[oid]]
            else:
                places = [spawn_zones[0]] if spawn_zones else [0]
            for item, drop in sorted(items.items()):
                for spot, area in enumerate(places):
                    candidates[item].append(
                        _Source(
                            category=category,
                            name=obj.name,
                            area=area,
                            chance=drop.chance,
                            quest_only=drop.quest_only,
                            quest=asked_by(item) if drop.quest_only else 0,
                            spot=spot,
                        )
                    )

    # Fishing by zone: the template entry IS an area id, stated first hand by the source.
    for area, items in expanded["fishing"].items():
        if area not in allowed:
            dropped["noArea"] += 1
            continue
        for item, drop in sorted(items.items()):
            candidates[item].append(
                _Source(
                    category=CAT_FISHED,
                    area=area,
                    chance=drop.chance,
                    quest_only=drop.quest_only,
                    quest=asked_by(item) if drop.quest_only else 0,
                )
            )

    # Container items: the container is an item this build names itself (BuildFacts.items), so the
    # row carries its id and no string, and the addon can make it a real edge instead of a dead end.
    for container, items in expanded["item"].items():
        if container not in selected.items:
            dropped["containerNotShipped"] += 1
            continue
        for item, drop in sorted(items.items()):
            candidates[item].append(
                _Source(
                    category=CAT_CONTAINER,
                    container=container,
                    chance=drop.chance,
                    quest_only=drop.quest_only,
                    quest=asked_by(item) if drop.quest_only else 0,
                )
            )

    # Vendors: a creature sells its own lines and its template's.
    by_template_offers: dict[int, list[VendorOffer]] = defaultdict(list)
    for offer in era_input.vendor_template_offers:
        by_template_offers[offer.vendor].append(offer)
    direct: dict[int, list[VendorOffer]] = defaultdict(list)
    for offer in era_input.vendor_offers:
        direct[offer.vendor].append(offer)
    for cid in sorted(set(direct) | {c for c in creatures if creatures[c].vendor_template}):
        facts = creatures.get(cid)
        if facts is None:
            # An npc_vendor line for a creature the dump has no template row for. Nothing to
            # name, so nothing to show.
            dropped["scaffolding"] += 1
            continue
        if is_scaffolding(facts.name):
            dropped["scaffolding"] += 1
            continue
        offers = list(direct.get(cid, ()))
        if facts.vendor_template:
            offers.extend(by_template_offers.get(facts.vendor_template, ()))
        # A vendor inside an instance gets the instance too. It falls out of the same call and
        # says the same true thing: five vendors on this build stand inside one.
        area = place_of(cid)
        for offer in offers:
            if offer.item <= 0:
                continue
            candidates[offer.item].append(
                _Source(category=CAT_VENDOR, name=facts.name, area=area, stock=offer.stock)
            )

    return candidates


# ----- the caps ---------------------------------------------------------------------------------


def _summary(category: int, group: Sequence[_Source], total: int | None = None) -> dict:
    """The row that stands for a whole category: how many sources it has, and their level band.

    `t` is always the total for that category on that item, never the leftover. The addon
    subtracts the named rows it has already drawn, which is one rule for both the capped case
    (three named, t of 242, so "and 239 more") and the summarise in place case (no named rows
    at all, so "184 vendors"). One meaning, decidable from the list itself. For a herb or a vein
    the sources are NODES, so `total` is the node count and the addon counts the nodes it drew.
    """
    row: dict = {"c": category, "t": len(group) if total is None else total}
    levels = [source for source in group if source.min_level]
    if levels:
        row["lo"] = min(source.min_level for source in levels)
        row["hi"] = max(source.max_level or source.min_level for source in levels)
    # o only where the condition is true of EVERY source the row stands for. A group holding
    # one drop anyone can get is not a quest only group.
    if group and all(source.quest_only for source in group):
        row["o"] = 1
    return row


def _named_row(
    source: _Source, strings: _Strings, area_strings: dict[int, int], area_place: Callable[[int], int]
):
    row: dict = {"c": source.category}
    if source.container:
        row["i"] = source.container
    elif source.name:
        row["n"] = strings.add(source.name)
    if source.area:
        row["a"] = source.area
        # Brief GA1: an area's string is the caller's: `s` keeps its place in the sort, and
        # EraSources.lua ships that place blank (brief EK1: `area_place`, see derive).
        area_strings[source.area] = area_place(source.area)
    percent = chance_percent(source.chance)
    if percent is not None:
        row["p"] = percent
    if source.stock:
        row["k"] = source.stock
    if source.quest_only:
        row["o"] = 1
        if source.quest:
            row["q"] = source.quest
    return row


def by_node(ranked: Sequence[_Source]) -> list[list[_Source]]:
    """A herb's or a vein's sources, grouped into nodes, in the order to draw them.

    A node is one name. The nodes go best first (a node anyone can gather before a quest only
    one, then the node's best chance, then its name), and inside one node its zone rows go the
    way the node's own zones do: anyone first, best chance first, then commonest first as the
    spawn table states them, then area id. Nothing here varies between runs.

    A row with no area inside a node that has zones says nothing its zone rows do not (one of
    the node's objects pfQuest places nowhere, Copper Vein's on Copper Ore), so it is dropped.
    """
    nodes: dict[str, list[_Source]] = {}
    for source in ranked:
        nodes.setdefault(source.name, []).append(source)
    for name, group in nodes.items():
        placed = [source for source in group if source.area]
        if placed:
            nodes[name] = placed
    groups = [
        sorted(group, key=lambda source: (source.quest_only, -source.chance, source.spot, source.area))
        for group in nodes.values()
    ]
    groups.sort(
        key=lambda group: (
            all(source.quest_only for source in group),
            -max(source.chance for source in group),
            group[0].name,
        )
    )
    return groups


def _node_rows(
    category: int,
    ranked: Sequence[_Source],
    listed: Callable[[Sequence[_Source]], list[dict]],
    strings: _Strings,
    area_strings: dict[int, int],
    area_place: Callable[[int], int],
    counts: dict[str, int],
) -> tuple[list[dict], list[dict]]:
    """Rule 1 for a herb or a vein, counted in NODES rather than rows.

    The first MAX_NAMED_ROWS nodes are named, each with all its zone rows together; the summary
    row's `t` is the node count; and the list behind it holds the remaining nodes' zone rows in
    the same node major order. The leftover of one exception is the same, by node: four nodes
    are four named nodes and no summary.
    """
    nodes = by_node(ranked)
    named = MAX_NAMED_ROWS
    if len(nodes) == MAX_NAMED_ROWS + 1:
        named = len(nodes)
        counts["summaryOfOne"] += 1
    rows = [
        _named_row(source, strings, area_strings, area_place) for node in nodes[:named] for source in node
    ]
    if len(nodes) > named:
        counts["summaryRows"] += 1
        rows.append(_summary(category, ranked, total=len(nodes)))
        return rows, listed([source for node in nodes[named:] for source in node])
    return rows, []


def _rows_for_category(
    category: int,
    sources: list[_Source],
    strings: _Strings,
    area_strings: dict[int, int],
    area_place: Callable[[int], int],
    counts: dict[str, int],
    creature_names: set[str],
) -> tuple[list[dict], list[dict]]:
    """The rows one category puts on one item, and the rest of the list behind them.

    The second half of the answer is the sources a summary row stands for, in the same order
    and in the same row shape, so they can be packed into `xl` and opened by a player. A
    category that got no summary row has nothing left over, and `c = 5` never ships a list.
    """
    # The same creature, object or vendor can reach an item twice, through a template and
    # through a reference. One name in one place is one row.
    unique: dict[tuple, _Source] = {}
    for source in sources:
        key = (source.name, source.area, source.container)
        best = unique.get(key)
        if best is None or source.chance > best.chance:
            unique[key] = source
    ranked = sorted(unique.values(), key=lambda source: source.order())

    if category == CAT_CREATURE_DROP and len(ranked) > WORLD_DROP_CREATURES:
        # Rule 2: naming three of seven hundred says less than "it drops out in the world".
        counts["worldDropRule"] += 1
        # No chance on it. The best of seven hundred creatures is 100% for Refreshing Spring
        # Water, and "World drop, 100%" is a sentence that is true of one creature and false
        # of the row. A summary row never carries a chance, whichever rule made it.
        #
        # No list either, and this is the one place a list is refused rather than shipped:
        # the 1,098 world drop rows stand for 357,692 creatures between them, which is about
        # 2.1 MB packed. See docs/era-sources.md.
        return [_summary(CAT_WORLD_DROP, ranked)], []

    def listed(rest: Sequence[_Source]) -> list[dict]:
        # A name in a list is a name the player can now read, so it gets a kind like any
        # other: the list rows are the ones a search has to match.
        if category in CREATURE_CATEGORIES:
            creature_names.update(source.name for source in rest if source.name)
        return [_named_row(source, strings, area_strings, area_place) for source in rest]

    if category in NODE_CATEGORIES:
        return _node_rows(category, ranked, listed, strings, area_strings, area_place, counts)

    if category == CAT_VENDOR and len(ranked) > VENDOR_SUMMARY_AT:
        # Rule 3: three arbitrary vendors out of 184 say less than the count does. The count
        # names none of them, so the whole list is what sits behind it.
        counts["vendorSummaryRule"] += 1
        return [_summary(CAT_VENDOR, ranked)], listed(ranked)

    # Rule 1, and the exception the owner asked for on 2026-09-20: a summary standing for
    # exactly one source says less than that source does, and the player cannot open it, so
    # where the cap would leave one over it is named instead and no summary row is written.
    named = MAX_NAMED_ROWS
    if len(ranked) == MAX_NAMED_ROWS + 1:
        named = len(ranked)
        counts["summaryOfOne"] += 1
    rows = [_named_row(source, strings, area_strings, area_place) for source in ranked[:named]]
    if category in CREATURE_CATEGORIES:
        creature_names.update(source.name for source in ranked[:named] if source.name)
    if len(ranked) > named:
        # Everything past the cap is kept as a truthful count, never silently dropped, and the
        # rest of the list is shipped behind it so the count can be opened and searched.
        counts["summaryRows"] += 1
        rows.append(_summary(category, ranked))
        return rows, listed(ranked[named:])
    return rows, []


def _quest_rows(
    offered: Sequence[QuestFacts],
    strings: _Strings,
    counts: dict[str, int],
) -> list[dict]:
    """The one quest row for an item, with the other turn ins behind it in `m`.

    The shape is unchanged from the first version of this module: the first quest in `q`, `n`
    and `f`, and up to MAX_FURTHER_QUESTS others in `m`, each with the same three keys. The
    commonest reason an item has several is that each side has its own turn in.
    """
    if not offered:
        return []
    if len(offered) > 1:
        counts["multiQuest"] += 1
    first, *further = offered
    row: dict = {"c": CAT_QUEST, "q": first.id, "n": strings.add(first.title)}
    side = faction_of(first.races)
    if side:
        row["f"] = side
    if len(further) > MAX_FURTHER_QUESTS:
        counts["furtherQuestsDropped"] += len(further) - MAX_FURTHER_QUESTS
        further = further[:MAX_FURTHER_QUESTS]
    if further:
        entries = []
        for quest in further:
            entry: dict = {"q": quest.id, "n": strings.add(quest.title)}
            side = faction_of(quest.races)
            if side:
                entry["f"] = side
            entries.append(entry)
        row["m"] = entries
        counts["furtherQuests"] += len(entries)
    return [row]


def _quest_titles(
    era_input: CmangosFacts,
    entries: Mapping[int, Sequence[dict]],
    strings: _Strings,
) -> dict[int, int]:
    """questId -> its title's index into `s`, for the quests an `o` row names and nothing else.

    A quest only row carries `q`, the quest that makes the item drop, but the addon can only
    title a quest the table itself names, and it names a quest by handing an item over on it
    (`c = 3`). 1,526 rows carry `q` and only 592 of those quests appear on a `c = 3` row
    anywhere in the table, so the other 934 rows said "only while on a quest" although the
    source database has the title in front of it.

    The titles the addon cannot already reach are shipped here, in one small table rather than
    as a key on each row: 478 quests against 934 rows, and it measured 1.8 KB smaller. Titles
    only. No `Details`, no `Objectives`, no `RequestItemsText`, ever.
    """
    handed_over: set[int] = set()
    for rows in entries.values():
        for row in rows:
            if row["c"] == CAT_QUEST:
                handed_over.add(row["q"])
                for further in row.get("m", ()):
                    handed_over.add(further["q"])
    titles: dict[int, int] = {}
    for rows in entries.values():
        for row in rows:
            if "o" not in row:
                continue
            quest = row.get("q")
            if not quest or quest in handed_over or quest in titles:
                continue
            facts = era_input.quests.get(quest)
            if facts is not None and facts.title:
                titles[quest] = strings.add(facts.title)
    return titles


def _creature_kinds(
    era_input: CmangosFacts,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
) -> dict[int, int]:
    """A creature name's index into `s` -> what kind of creature it is, packed by pack_kind.

    Keyed by the NAME and not by a creature id, because the table has never carried creature
    ids and the row the player reads is a name: every row naming "Deviate Creeper" wants the
    same icon. Where two creatures share a name and disagree, the commoner CreatureType wins
    (ties by the lower id, so the answer never depends on dictionary order), the commoner
    Family among the creatures of that type wins with it, and the level band is the widest of
    all of them: a name that covers levels 11 to 14 and 36 to 40 covers 11 to 40.

    Ids and numbers only. `SubName` is not read here. Since 2026-09-27, on the owner's ruling of
    that day, it is read for vendors and quest givers alone and ships in `st`: see _titles.
    """
    by_name: dict[str, list[CreatureFacts]] = defaultdict(list)
    for creature_id in sorted(era_input.creatures):
        facts = era_input.creatures[creature_id]
        if facts.name in names:
            by_name[facts.name].append(facts)
    kinds: dict[int, int] = {}
    conflicts = 0
    for name in sorted(by_name):
        creatures = by_name[name]
        types = Counter(facts.creature_type for facts in creatures)
        kind = min(types.items(), key=lambda pair: (-pair[1], pair[0]))[0]
        families = Counter(facts.family for facts in creatures if facts.creature_type == kind)
        family = min(families.items(), key=lambda pair: (-pair[1], pair[0]))[0] if families else 0
        low = min(facts.min_level for facts in creatures)
        high = max(max(facts.max_level, facts.min_level) for facts in creatures)
        if len({(f.creature_type, f.family, f.min_level, f.max_level) for f in creatures}) > 1:
            conflicts += 1
        kinds[strings.add(name)] = pack_kind(kind, family, low, high)
    counts["kindConflicts"] = conflicts
    return kinds


def _creature_displays(
    era_input: CmangosFacts,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
    dropped: dict[str, int],
    known: Collection[int],
) -> dict[int, int]:
    """A creature name's index into `s` -> the display id the client draws its portrait from.

    Keyed by the NAME, for the same reason `ck` is: the table has never carried creature ids
    and every row naming "Deviate Creeper" wants the same portrait. Where two creatures share a
    name and state different models the commonest wins, ties by the lower display id so the
    answer never depends on dictionary order.

    Every id is checked against `known` (BuildFacts.known_displays: the caller reads them from THIS
    build's own `CreatureDisplayInfo`) and any other is dropped: the addon may only ever hand the
    client an id the client has. A name
    whose creatures state no model at all simply gets no entry, which reads in the addon exactly
    as a name with no kind does, and the row keeps its stock kind icon.

    One plain integer per name. No portrait file, no model path and no art of any kind is
    shipped: the id names the client's own model and the client draws it.
    """
    by_name: dict[str, list[CreatureFacts]] = defaultdict(list)
    for creature_id in sorted(era_input.creatures):
        facts = era_input.creatures[creature_id]
        if facts.name in names:
            by_name[facts.name].append(facts)
    displays: dict[int, int] = {}
    conflicts = 0
    without = 0
    for name in sorted(by_name):
        stated = [facts for facts in by_name[name] if facts.display > 0]
        if not stated:
            without += 1
            continue
        counted = Counter(facts.display for facts in stated)
        if len(counted) > 1:
            conflicts += 1
        display = min(counted.items(), key=lambda pair: (-pair[1], pair[0]))[0]
        if display not in known:
            dropped["displayNotInBuild"] += 1
            continue
        displays[strings.add(name)] = display
    counts["displayConflicts"] = conflicts
    counts["namesWithoutDisplay"] = without
    return displays


def _creature_ids(
    era_input: CmangosFacts,
    names: Collection[str],
    strings: _Strings,
    counts: dict[str, int],
) -> dict[int, int]:
    """Brief EK1 (owner ruling of 2026-10-09): a creature name's index into `s` -> the LOWEST
    `creature_template` entry id whose `Name` is exactly that string, for every name given (the
    names `ck` carries, vendors included).

    One page per name, as before: creatures of one name still share one page, and the page is now
    keyed by this id rather than by the name's place in `s`, which is a position in a sorted table
    and not a fact about the creature. The match is exact, case and spacing included, over every
    entry of the dump (a scaffolding entry of the same name included: the lowest id is a CMaNGOS
    fact either way). A name no entry states exactly has no id and no entry here.
    """
    wanted = set(names)
    lowest: dict[str, int] = {}
    shared = 0
    for creature_id in sorted(era_input.creatures):
        name = era_input.creatures[creature_id].name
        if name in wanted:
            if name in lowest:
                shared += 1
            else:
                lowest[name] = creature_id
    ids = {strings.add(name): creature_id for name, creature_id in sorted(lowest.items())}
    counts["creatureIds"] = len(ids)
    counts["creatureIdsNamesShared"] = shared
    counts["creatureIdsWithout"] = len(wanted) - len(ids)
    return ids


def _object_ids(
    era_input: CmangosFacts,
    names: Collection[str],
    strings: _Strings,
    counts: dict[str, int],
) -> dict[int, int]:
    """Brief EK1 Part 2c (owner ruling of 2026-10-09): an OBJECT name's index into `s` -> the LOWEST
    `gameobject_template` entry id whose `name` is exactly that string, for every name given (every
    object name a shipped row or list names: the herbs, veins, fishing pools and chests,
    _object_names). The object twin of `ci`, by the same rule: one page per name, keyed by this id
    rather than by the name's place in `s`; the match is exact over every entry of the dump; a name
    no entry states exactly has no id and no entry here.
    """
    wanted = set(names)
    lowest: dict[str, int] = {}
    shared = 0
    for object_id in sorted(era_input.objects):
        name = era_input.objects[object_id].name
        if name in wanted:
            if name in lowest:
                shared += 1
            else:
                lowest[name] = object_id
    ids = {strings.add(name): object_id for name, object_id in sorted(lowest.items())}
    counts["objectIds"] = len(ids)
    counts["objectIdsNamesShared"] = shared
    counts["objectIdsWithout"] = len(wanted) - len(ids)
    return ids


# ----- the spawns: which are always there, and which walk -------------------------------------------
#
# CMaNGOS rules alone, read by the caller's map pins and paths (ItemTree's era_pins, brief EK1) and
# by its Boss loot index: this module ships no coordinate.


def _spawns_by_creature(
    spawns: Sequence[Spawn], entries: Mapping[int, Sequence[int]]
) -> tuple[dict[int, list[Spawn]], int, int]:
    """creature id -> the spawns that are always there, plus what was left out and why.

    Two of the dump's own rules are applied here and nowhere else:

      * a row whose `id` is 0 takes its creature from `creature_spawn_entry`, and a row with no
        entry there names no creature and is left out (568 of the 2,802 on this dump);
      * a row `game_event_creature` gives a POSITIVE event id only exists while that event is
        running, so it is left out: a Hallow's End spawn is not where the creature is found. A
        negative event id means the row is removed during the event and is ordinary the rest of
        the year, so it is kept.

    A pooled row is kept. One member of a pool holds a creature at a time, but every point in
    the pool is a place the creature is found, which is exactly what a pin says.
    """
    by_creature: dict[int, list[Spawn]] = defaultdict(list)
    event_only = 0
    nameless = 0
    for spawn in spawns:
        if spawn.event > 0:
            event_only += 1
            continue
        ids = (spawn.creature,) if spawn.creature else tuple(entries.get(spawn.guid, ()))
        if not ids:
            nameless += 1
            continue
        for creature in ids:
            by_creature[creature].append(spawn)
    return by_creature, event_only, nameless


def template_walk(era_input: CmangosFacts, creature: int) -> tuple[tuple[float, float], ...] | None:
    """The creature's own `creature_movement_template` path, the lowest path id where it states
    several (a script picks between them; path 0 is the one a spawn walks by default)."""
    by_path = era_input.template_paths.get(creature)
    if not by_path:
        return None
    return by_path[min(by_path)] or None


def spawn_walk(
    era_input: CmangosFacts, spawn: Spawn, creature: int
) -> tuple[tuple[float, float], ...] | None:
    """The path one spawn walks: none unless its MovementType is a waypoint walk, then its own
    `creature_movement` rows, else its creature's template path."""
    if spawn.guid not in era_input.waypoint_guids:
        return None
    return era_input.paths.get(spawn.guid) or template_walk(era_input, creature)


def listed_creatures(era_input: CmangosFacts) -> set[int]:
    """Every creature id any `creature` row names, an event only row included."""
    out: set[int] = set()
    for spawn in era_input.spawns:
        out.update((spawn.creature,) if spawn.creature else era_input.spawn_entries.get(spawn.guid, ()))
    out.discard(0)
    return out


def _unspawned_walkers(
    era_input: CmangosFacts, listed: Collection[int]
) -> dict[tuple[tuple[float, float], ...], list[int]]:
    """A template path -> the creatures with no `creature` row at all (script spawns) that walk
    exactly it. The four dragons of the Emerald Dream share one, which is how the dump says any of
    them walks it. A creature whose only rows are event only is not one: it is not found at all."""
    walkers: dict[tuple[tuple[float, float], ...], list[int]] = defaultdict(list)
    for creature in sorted(era_input.template_paths):
        if creature in listed:
            continue
        walk = template_walk(era_input, creature)
        if walk:
            walkers[walk].append(creature)
    return walkers


def shared_places(era_input: CmangosFacts) -> set[int]:
    """Brief W18: the creature ids whose places are shared, so at a time the creature stands at
    one of them, or another creature does: a pooled spawn (`pool_creature`, or a creature
    `pool_creature_template` pools), a spawn `creature_spawn_entry` gives several creatures, or,
    for a creature with no `creature` row at all, a template path another such creature walks too."""
    out: set[int] = set()
    for spawn in era_input.spawns:
        if spawn.event > 0:
            continue
        ids = (spawn.creature,) if spawn.creature else tuple(era_input.spawn_entries.get(spawn.guid, ()))
        if spawn.pooled or len(ids) > 1:
            out.update(creature for creature in ids if creature)
    for creatures in _unspawned_walkers(era_input, listed_creatures(era_input)).values():
        if len(creatures) > 1:
            out.update(creatures)
    return out


# The categories whose `n` is an OBJECT, which are the ones an object pin is made for, and the
# word each is counted under.
OBJECT_CATEGORIES = {CAT_HERB: "Herb", CAT_VEIN: "Vein", CAT_FISHED: "Pool", CAT_OBJECT: "Chest"}


def _object_names(
    entries: Mapping[int, Sequence[dict]],
    leftovers: Mapping[int, Mapping[int, Sequence[dict]]],
    strings: _Strings,
) -> dict[str, int]:
    """Every object name a shipped row or a packed list names -> the category it is filed under.

    The rows still carry insertion indexes here, before the string table is sorted. A name filed
    under two object categories (a node that is also a chest somewhere) takes the lower number,
    so the answer never depends on the order the items were read in.
    """
    found: dict[str, int] = {}

    def note(row: Mapping) -> None:
        category = row.get("c")
        if category in OBJECT_CATEGORIES and "n" in row and "t" not in row:
            name = strings.value(row["n"])
            if name:
                found[name] = min(found.get(name, category), category)

    for rows in entries.values():
        for row in rows:
            note(row)
    for by_kind_rows in leftovers.values():
        for rest in by_kind_rows.values():
            for row in rest:
                note(row)
    return dict(sorted(found.items()))


def _vendor_names(
    entries: Mapping[int, Sequence[dict]],
    leftovers: Mapping[int, Mapping[int, Sequence[dict]]],
    strings: _Strings,
) -> set[str]:
    """Every vendor name a shipped row or a packed list names (brief N3).

    These are the names a vendor's page can be opened on, so they are the ones that get a kind,
    a portrait and pins beside the creatures'. Read off the rows while they still carry insertion
    indexes, the way _object_names reads the object names.
    """
    found: set[str] = set()

    def note(row: Mapping) -> None:
        if row.get("c") == CAT_VENDOR and "n" in row and "t" not in row:
            name = strings.value(row["n"])
            if name:
                found.add(name)

    for rows in entries.values():
        for row in rows:
            note(row)
    for by_kind_rows in leftovers.values():
        for row in by_kind_rows.get(CAT_VENDOR, ()):
            note(row)
    return found


def _handed_over(entries: Mapping[int, Sequence[dict]]) -> set[int]:
    """Every quest a c = 3 row names, first or further: the quests the addon can already title."""
    found: set[int] = set()
    for rows in entries.values():
        for row in rows:
            if row["c"] == CAT_QUEST:
                found.add(row["q"])
                for further in row.get("m", ()):
                    found.add(further["q"])
    return found


def _giver_names(era_input: CmangosFacts) -> set[str]:
    """Every creature NAME that starts or ends a quest the table can title (brief W15).

    Owner QA, 2026-09-29: "Quest: Deviate Hides (1486)" showed no giver, because Nalpak gives
    and takes it and Nalpak drops, sells and trains nothing, so brief N3's rule (a giver ships
    only where some other row already names it) left him out. Since 2026-09-29 every such name
    ships: it joins the creature, vendor and trainer names in `ck`, `cd`, `mp`, `st`, `cf` and
    `qg`. The same tests _quest_givers applies decide it: a creature with no template, no name
    or a scaffolding name gives nothing, and a quest with no title or a scaffolding one is no
    reason to ship a name. A creature with no quest link is not read here at all.
    """
    found: set[str] = set()
    for relation in (era_input.quest_starts, era_input.quest_ends):
        for creature_id, quest in relation:
            facts = era_input.creatures.get(creature_id)
            if facts is None or is_scaffolding(facts.name):
                continue
            title = era_input.quest_names.get(quest, "")
            if title and not is_scaffolding(title):
                found.add(facts.name)
    return found


def _quest_givers(
    era_input: CmangosFacts,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[tuple[int, ...], tuple[int, ...]]]:
    """A creature or vendor NAME's index into `s` -> (the quests it starts, the quests it ends).

    Brief N3. Keyed by the name, the way `ck`, `cd` and `mp` are: every creature of one name is
    the same giver to a player, so "Innkeeper Farley" starts what any creature called that
    starts. `names` is every name the table ships a page for, which since brief W15 (2026-09-29)
    includes every giver _giver_names finds, so a giver that drops, sells and trains nothing,
    such as Nalpak, gets its entry too. What `questGiverNotShipped` counts now is a relation row
    whose creature has no template, no name or a scaffolding name.

    A quest is kept only where quest_template gives it a title, and a title that is scaffolding
    is refused like a scaffolding name, because a quest the addon cannot title is a row that says
    nothing. Each list is quest id ascending with repeats dropped; a quest a name both starts and
    ends is in both.
    """
    by_id = era_input.creatures
    lists: dict[str, tuple[set[int], set[int]]] = {}
    for side, relation in ((0, era_input.quest_starts), (1, era_input.quest_ends)):
        for creature_id, quest in relation:
            facts = by_id.get(creature_id)
            if facts is None:
                dropped["questGiverNotShipped"] += 1
                continue
            title = era_input.quest_names.get(quest, "")
            if not title:
                dropped["questGiverUntitled"] += 1
                continue
            if is_scaffolding(title):
                dropped["questGiverScaffolding"] += 1
                continue
            if facts.name not in names:
                dropped["questGiverNotShipped"] += 1
                continue
            lists.setdefault(facts.name, (set(), set()))[side].add(quest)
    out: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = {}
    for name in sorted(lists):
        starts, ends = lists[name]
        out[strings.add(name)] = (tuple(sorted(starts)), tuple(sorted(ends)))
    counts["questGiverNames"] = len(out)
    counts["questGiverStarts"] = sum(len(pair[0]) for pair in out.values())
    counts["questGiverEnds"] = sum(len(pair[1]) for pair in out.values())
    counts["questGiverBoth"] = sum(len(set(pair[0]) & set(pair[1])) for pair in out.values())
    # Brief W15: how many distinct quests have a giver or an ender the table names.
    counts["questGiverQuests"] = len({quest for pair in out.values() for side in pair for quest in side})
    return out


def _object_givers(
    era_input: CmangosFacts,
    strings: _Strings,
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[tuple[int, ...], tuple[int, ...]]]:
    """Brief EO1 (the owner's ruling "3A" of 2026-10-22): a world OBJECT name's index into `s` ->
    (the quests it starts, the quests it ends), out of gameobject_questrelation and
    gameobject_involvedrelation, by exactly _quest_givers' rules: keyed by the NAME (every object of
    one name is the same giver to a player: the four "Wanted Poster" entries are one poster), a
    relation row whose object has no template or a scaffolding name gives nothing
    (`objectGiverNotShipped`), and a quest with no title or a scaffolding one is no reason to ship
    a name (`objectGiverUntitled`, `objectGiverScaffolding`). Every object those rules keep ships as
    a name of its own, whatever else it is: a wanted poster drops nothing and is no chest. Each list
    is quest id ascending with repeats dropped; a quest a name both starts and ends is in both."""
    lists: dict[str, tuple[set[int], set[int]]] = {}
    for side, relation in ((0, era_input.object_quest_starts), (1, era_input.object_quest_ends)):
        for object_id, quest in relation:
            facts = era_input.objects.get(object_id)
            if facts is None or not facts.name or is_scaffolding(facts.name):
                dropped["objectGiverNotShipped"] += 1
                continue
            title = era_input.quest_names.get(quest, "")
            if not title:
                dropped["objectGiverUntitled"] += 1
                continue
            if is_scaffolding(title):
                dropped["objectGiverScaffolding"] += 1
                continue
            lists.setdefault(facts.name, (set(), set()))[side].add(quest)
    out: dict[int, tuple[tuple[int, ...], tuple[int, ...]]] = {}
    for name in sorted(lists):
        starts, ends = lists[name]
        out[strings.add(name)] = (tuple(sorted(starts)), tuple(sorted(ends)))
    counts["objectGiverNames"] = len(out)
    counts["objectGiverStarts"] = sum(len(pair[0]) for pair in out.values())
    counts["objectGiverEnds"] = sum(len(pair[1]) for pair in out.values())
    counts["objectGiverQuests"] = len({quest for pair in out.values() for side in pair for quest in side})
    counts["objectRelationStartRows"] = len(era_input.object_quest_starts)
    counts["objectRelationEndRows"] = len(era_input.object_quest_ends)
    return out


def _quest_requires(
    era_input: CmangosFacts,
    shipped: Callable[[int], bool],
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[tuple[int, int], ...]]:
    """questId -> (item id, count) for each item the quest asks the player to bring (brief W12).

    Owner, 2026-09-29 (queue item 136): Deviate Hide showed "Used by (0)" although its creature's
    loot row says "only on the quest", because a quest's required items never reached the file
    and the addon had no edge from the item to the quest. This is that edge, ids and counts only.

    Every kept quest (a title, and items or requires) that asks for something is a candidate. A
    required item this build does not ship, and does not ship as withheld, is refused the way a
    row for it would be, and a quest left asking for nothing has no entry. A quest whose title is
    scaffolding is refused like a scaffolding name. The items are in the template's slot order;
    an item named in two slots is one entry with the two counts added. A count of 0 reads as one.
    """
    out: dict[int, tuple[tuple[int, int], ...]] = {}
    for quest_id in sorted(era_input.quests):
        quest = era_input.quests[quest_id]
        if not quest.requires:
            continue
        if is_scaffolding(quest.title):
            dropped["questRequiresScaffolding"] += 1
            continue
        wanted: dict[int, int] = {}
        for slot, item in enumerate(quest.requires):
            if not shipped(item):
                dropped["questRequiresNotShipped"] += 1
                continue
            count = quest.require_counts[slot] if slot < len(quest.require_counts) else 0
            wanted[item] = wanted.get(item, 0) + max(count, 1)
        if wanted:
            out[quest_id] = tuple(wanted.items())
    counts["questRequiresQuests"] = len(out)
    counts["questRequiresPairs"] = sum(len(pairs) for pairs in out.values())
    counts["questRequiresItems"] = len({item for pairs in out.values() for item, _count in pairs})
    counts["questRequiresCountAboveOne"] = sum(
        1 for pairs in out.values() for _item, count in pairs if count > 1
    )
    return out


def quest_provided(
    era_input: CmangosFacts,
    shipped: Callable[[int], bool],
    counts: dict[str, int],
    dropped: dict[str, int],
) -> dict[int, tuple[int, int]]:
    """questId -> (item id, count): the item the quest hands the player when it is taken (brief NX1,
    the owner's ruling "2A" of 2026-10-22), out of quest_template's SrcItemId and SrcItemCount alone.

    Saving Yenniku (592) hands over the Soul Gem (3912) to be filled. Only a quest `quest_template`
    titles, never one whose title is scaffolding (refused like a `qr` quest), and only an item this
    build ships or withholds (`shipped`, as `qr`'s rule): any other pair is counted in `dropped`.
    A count of 0 reads as 1. Every such pair is kept, an item that also starts its own quest among
    them (the caller's addon leaves that one out where it reads `qp`). Ids and counts only. Pure."""
    out: dict[int, tuple[int, int]] = {}
    for quest_id, (item, count) in sorted(era_input.quest_sources.items()):
        title = era_input.quest_names.get(quest_id, "")
        if not title:
            dropped["questProvidedUntitled"] += 1
            continue
        if is_scaffolding(title):
            dropped["questProvidedScaffolding"] += 1
            continue
        if not shipped(item):
            dropped["questProvidedNotShipped"] += 1
            continue
        out[quest_id] = (item, max(1, count))
    counts["questProvidedQuests"] = len(out)
    counts["questProvidedItems"] = len({item for item, _count in out.values()})
    counts["questProvidedCountAboveOne"] = sum(1 for _item, count in out.values() if count > 1)
    return out


def _vendor_creatures(era_input: CmangosFacts) -> set[int]:
    """Every creature id that sells anything, by `npc_vendor` or by a vendor template."""
    found = {offer.vendor for offer in era_input.vendor_offers}
    found.update(cid for cid, facts in era_input.creatures.items() if facts.vendor_template)
    return found


def speaking_creatures(
    era_input: CmangosFacts, names: Collection[str], trainers: Collection[int] = ()
) -> dict[str, list[CreatureFacts]]:
    """Brief T1: per vendor, trainer or quest giver NAME of `names`, the creatures that speak for it,
    in id order: where creatures share a name, the ones that sell something if any of them does (so
    "Innkeeper Farley" the vendor is not titled by a quest giver of the same name), else the ones
    that teach (`trainers`, the creature ids `tr` stands for: a trainer's title is its "Journeyman
    Enchanter" rather than some quest giver's of its name), else all of them. A CMaNGOS rule alone:
    the title (`st`, _titles) and the caller's side for the name (EraPlaces.lua's `cf`) both read it.
    """
    sellers = _vendor_creatures(era_input)
    teachers = set(trainers)
    by_name: dict[str, list[CreatureFacts]] = defaultdict(list)
    for creature_id in sorted(era_input.creatures):
        facts = era_input.creatures[creature_id]
        if facts.name in names:
            by_name[facts.name].append(facts)
    out: dict[str, list[CreatureFacts]] = {}
    for name in sorted(by_name):
        creatures = by_name[name]
        out[name] = (
            [facts for facts in creatures if facts.id in sellers]
            or [facts for facts in creatures if facts.id in teachers]
            or creatures
        )
    return out


def _titles(
    era_input: CmangosFacts,
    names: set[str],
    strings: _Strings,
    counts: dict[str, int],
    trainers: Collection[int] = (),
) -> dict[int, int]:
    """Brief T1: a vendor, trainer or quest giver NAME's index into `s` -> its SubName's index into
    `s`, for the names given and no other.

    Keyed by the name, the way `ck` and `qg` are. Among the creatures that speak for a name
    (speaking_creatures) the commonest non empty SubName wins, ties by the lowest creature id.
    """
    subnames: dict[int, int] = {}
    conflicts = 0
    for name, speaking in speaking_creatures(era_input, names, trainers).items():
        titles = Counter(facts.subname for facts in speaking if facts.subname)
        if titles:
            first = {}
            for facts in speaking:
                first.setdefault(facts.subname, facts.id)
            title = min(titles, key=lambda value: (-titles[value], first[value]))
            if len(titles) > 1:
                conflicts += 1
            subnames[strings.add(name)] = strings.add(title)
    counts["subnames"] = len(subnames)
    counts["subnameConflicts"] = conflicts
    return subnames


def trainer_creature_spells(era_input: CmangosFacts) -> dict[int, set[int]]:
    """creature id -> every spell id it teaches, before any reduction (brief P6a).

    A creature teaches its own `npc_trainer` rows and every row of the `npc_trainer_template`
    entry its TrainerTemplateId names. A learn spell (see SPELL_EFFECT_LEARN_SPELL) stands for the
    spell it teaches, which is the one a player, the build and the addon know it by.
    """
    templates: dict[int, set[int]] = defaultdict(set)
    for template, spell in era_input.trainer_template_spells:
        templates[template].add(spell)
    taught: dict[int, set[int]] = defaultdict(set)
    for creature, spell in era_input.trainer_spells:
        taught[creature].add(spell)
    for creature_id, facts in era_input.creatures.items():
        if facts.trainer_template and templates.get(facts.trainer_template):
            taught[creature_id] |= templates[facts.trainer_template]
    learned = era_input.learned_spells
    return {
        creature: {learned.get(spell, spell) for spell in spells if spell > 0}
        for creature, spells in sorted(taught.items())
        if creature > 0
    }


def trainer_creature_ranks(era_input: CmangosFacts) -> dict[int, dict[int, int]]:
    """creature id -> taught spell id -> the lowest skill rank any of its rows asks (brief TR5).

    The same join as trainer_creature_spells (its own rows and its template's, a learn spell read
    as the spell it teaches), over npc_trainer.reqskillvalue and npc_trainer_template's. A row
    whose rank the dump did not state is left out.
    """
    learned = era_input.learned_spells
    templates: dict[int, dict[int, int]] = defaultdict(dict)
    for (template, spell), rank in era_input.trainer_template_ranks.items():
        taught = learned.get(spell, spell)
        templates[template][taught] = min(rank, templates[template].get(taught, rank))
    out: dict[int, dict[int, int]] = defaultdict(dict)
    for (creature, spell), rank in era_input.trainer_ranks.items():
        taught = learned.get(spell, spell)
        out[creature][taught] = min(rank, out[creature].get(taught, rank))
    for creature_id, facts in era_input.creatures.items():
        if not facts.trainer_template:
            continue
        for taught, rank in templates.get(facts.trainer_template, {}).items():
            out[creature_id][taught] = min(rank, out[creature_id].get(taught, rank))
    return {creature: ranks for creature, ranks in sorted(out.items()) if creature > 0}


def _trainer_levels(
    era_input: CmangosFacts, lists: Mapping[str, Sequence[int]], teachers: Collection[int]
) -> dict[str, tuple[int, ...]]:
    """A trainer NAME -> the learn level of each spell of its `tr` list, in that list's order
    (brief TR5): the lowest rank any creature of the name asks, 0 where none states one."""
    ranks = trainer_creature_ranks(era_input)
    best: dict[str, dict[int, int]] = defaultdict(dict)
    for creature in sorted(teachers):
        name = era_input.creatures[creature].name
        held = best[name]
        for spell, rank in ranks.get(creature, {}).items():
            held[spell] = min(rank, held.get(spell, rank))
    return {name: tuple(best[name].get(spell, 0) for spell in spells) for name, spells in lists.items()}


def _trainer_lists(
    era_input: CmangosFacts,
    selected: BuildFacts,
    counts: dict[str, int],
    dropped: dict[str, int],
) -> tuple[dict[str, tuple[int, ...]], set[int]]:
    """A trainer NAME -> the spell ids its creatures teach, ascending (brief P6a), and the ids
    of the creatures that stand behind those names.

    Keyed by the name, the way `ck`, `qg` and `st` are: every creature called "Kitta Firewind"
    is the same trainer to a player. Reduced to BuildFacts.profession_spells (the caller's cut:
    the spells THIS build's own SkillLineAbility files under a profession or secondary line), so
    no spell id the client cannot name ships; a spell in BuildFacts.class_spells is refused by the
    cut and counted under `trainerSpellClass`, so a class trainer ships nothing, and any other
    under `trainerSpellUnknown`. A creature with no name, or a scaffolding one, teaches nothing
    that ships: there is no page to open it on.
    """
    lists: dict[str, set[int]] = defaultdict(set)
    teachers: set[int] = set()
    for creature, spells in trainer_creature_spells(era_input).items():
        facts = era_input.creatures.get(creature)
        if facts is None or not facts.name or is_scaffolding(facts.name):
            dropped["trainerUnnamed"] += 1
            continue
        kept = spells & selected.profession_spells
        classed = sum(1 for spell in spells if spell in selected.class_spells and spell not in kept)
        dropped["trainerSpellClass"] += classed
        dropped["trainerSpellUnknown"] += len(spells) - len(kept) - classed
        if not kept:
            dropped["trainerNothingKnown"] += 1
            continue
        lists[facts.name] |= kept
        teachers.add(creature)
    out = {name: tuple(sorted(lists[name])) for name in sorted(lists)}
    pairs = [(name, spell) for name, spells in out.items() for spell in spells]
    counts["trainerNames"] = len(out)
    counts["trainerCreatures"] = len(teachers)
    counts["trainerPairs"] = len(pairs)
    counts["trainerSpells"] = len({spell for _name, spell in pairs})
    return out, teachers


def spawned_creatures(era_input: CmangosFacts) -> set[int]:
    """Every creature id the cmangos `creature` table spawns somewhere: a row's own `id`, or each
    entry `creature_spawn_entry` names for a row that leaves it at 0."""
    found: set[int] = set()
    for spawn in era_input.spawns:
        if spawn.creature > 0:
            found.add(spawn.creature)
        else:
            found.update(era_input.spawn_entries.get(spawn.guid, ()))
    return found


def class_trainers(
    era_input: CmangosFacts, counts: dict[str, int], dropped: dict[str, int]
) -> tuple[set[str], set[int]]:
    """Brief TR6: the class and pet trainer NAMES the table lists for their place alone, and the
    creature ids behind them.

    A creature counts where its `TrainerType` is a class or a pet trainer's (PLACED_TRAINER_TYPES),
    it teaches at least one spell (its own `npc_trainer` rows or its template's: TrainerType 0 is
    the column's default, so teaching is what makes it a trainer) and the `creature` table spawns
    it, since a name with nowhere to stand adds nothing a player can find. A creature with no name
    or a scaffolding one is left out. None of these names gets a `tr` list: the class spells stay
    cut (_trainer_lists); the name gets its kind, portrait, title and id here and its side and pins
    on the caller's side, by the rules every other name follows.
    """
    spawned = spawned_creatures(era_input)
    names: set[str] = set()
    ids: set[int] = set()
    pets: set[str] = set()
    for creature, spells in trainer_creature_spells(era_input).items():
        facts = era_input.creatures.get(creature)
        if facts is None or facts.trainer_type not in PLACED_TRAINER_TYPES or not spells:
            continue
        if not facts.name or is_scaffolding(facts.name):
            dropped["classTrainerUnnamed"] += 1
            continue
        if creature not in spawned:
            dropped["classTrainerNotSpawned"] += 1
            continue
        names.add(facts.name)
        ids.add(creature)
        if facts.trainer_type == TRAINER_TYPE_PETS:
            pets.add(facts.name)
    counts["classTrainerNames"] = len(names - pets)
    counts["petTrainerNames"] = len(pets)
    counts["classTrainerCreatures"] = len(ids)
    return names, ids


def trainer_creature_terms(era_input: CmangosFacts) -> dict[int, dict[int, tuple[int, int]]]:
    """Brief CT1: creature id -> taught spell id -> (level, price), the level the trainer asks and
    the price in copper.

    The same join as trainer_creature_spells (its own rows and its template's, a learn spell read as
    the spell it teaches), over npc_trainer's reqlevel and spellcost and npc_trainer_template's: the
    lowest of each where two rows name one spell. A row the dump states neither column for is left
    out (its spell reads 0 and 0 in the list)."""
    learned = era_input.learned_spells

    def lowest(into: dict[int, tuple[int, int]], spell: int, terms: tuple[int, int]) -> None:
        if spell <= 0:
            return
        held = into.get(spell)
        into[spell] = terms if held is None else (min(held[0], terms[0]), min(held[1], terms[1]))

    templates: dict[int, dict[int, tuple[int, int]]] = defaultdict(dict)
    for (template, spell), terms in era_input.trainer_template_terms.items():
        lowest(templates[template], learned.get(spell, spell), terms)
    out: dict[int, dict[int, tuple[int, int]]] = defaultdict(dict)
    for (creature, spell), terms in era_input.trainer_terms.items():
        lowest(out[creature], learned.get(spell, spell), terms)
    for creature_id, facts in era_input.creatures.items():
        if not facts.trainer_template:
            continue
        for taught, terms in templates.get(facts.trainer_template, {}).items():
            lowest(out[creature_id], taught, terms)
    return {creature: terms for creature, terms in sorted(out.items()) if creature > 0}


def _class_trainer_lists(
    era_input: CmangosFacts, names: Collection[str], counts: dict[str, int], dropped: dict[str, int]
) -> tuple[dict[str, int], list[str], list[int]]:
    """Brief CT1 (the owner, 2026-10-17): a class trainer NAME -> the 1 based number of its list,
    the lists themselves (packed by pack_class_list, each distinct list once) and the class each
    list is for.

    The names are class_trainers' (named, spawned); a creature of one speaks for it only where its
    TrainerType is a class trainer's and its TrainerClass a playable class (CLASS_IDS), so a pet
    trainer ships no list, and a class trainer of no class is counted under
    `classTrainerNoClass`. Keyed by the NAME, the way `tr` is: the name teaches the union of its
    creatures' spells, each at the lowest level and the lowest price any of them asks, in level
    order then spell id. Where its creatures name two classes the lowest class id is the list's
    (`classTrainerClassesDisagree`; none do in the pinned dump). A CMaNGOS rule alone: nothing of
    the caller's chooses a record, so a spell a client build no longer has ships as the dump states
    it, and the addon leaves out what its client cannot name (EraPlaces.lua's `tf`, the caller's)."""
    terms = trainer_creature_terms(era_input)
    taught: dict[str, dict[int, tuple[int, int]]] = defaultdict(dict)
    classes: dict[str, set[int]] = defaultdict(set)
    for creature, spells in trainer_creature_spells(era_input).items():
        facts = era_input.creatures.get(creature)
        if facts is None or facts.name not in names or facts.trainer_type != TRAINER_TYPE_CLASS or not spells:
            continue
        if facts.trainer_class not in CLASS_IDS:
            dropped["classTrainerNoClass"] += 1
            continue
        classes[facts.name].add(facts.trainer_class)
        held = taught[facts.name]
        stated = terms.get(creature, {})
        for spell in spells:
            level, price = stated.get(spell, (0, 0))
            known = held.get(spell)
            held[spell] = (level, price) if known is None else (min(known[0], level), min(known[1], price))
    pool: dict[tuple[int, str], int] = {}
    lists: list[str] = []
    list_classes: list[int] = []
    numbers: dict[str, int] = {}
    pairs = 0
    for name in sorted(taught):
        if len(classes[name]) > 1:
            counts["classTrainerClassesDisagree"] = counts.get("classTrainerClassesDisagree", 0) + 1
        class_id = min(classes[name])
        records = sorted((level, spell, price) for spell, (level, price) in taught[name].items())
        packed = pack_class_list([(spell, level, price) for level, spell, price in records])
        number = pool.get((class_id, packed))
        if number is None:
            lists.append(packed)
            list_classes.append(class_id)
            number = len(lists)
            pool[(class_id, packed)] = number
        numbers[name] = number
        pairs += len(records)
    counts["classTrainerListNames"] = len(numbers)
    counts["classTrainerLists"] = len(lists)
    counts["classTrainerListRecords"] = sum(len(packed) // TC_RECORD_DIGITS for packed in lists)
    counts["classTrainerListPairs"] = pairs
    counts["classTrainerListSpells"] = len({spell for held in taught.values() for spell in held})
    return numbers, lists, list_classes


def derive(cmangos: CmangosOnly, selected: BuildFacts) -> EraSources:
    """Turn the two pinned databases into EraSources.lua's table, counting every refusal.

    `cmangos` is the dump's facts and pfQuest's area ids (cmangos_only) and `selected` the caller's
    plain selections (BuildFacts, brief EK1): which items ship (`items`, `withheld`), which areas a
    row may carry and where each area's place sorts in `s` (its rank among dump_strings), the
    instance a creature or an object takes, the category a chest's lock gives, the display ids
    and the trainer spells a name may carry, and the quest rows to leave out. Nothing else of a
    client build is read.

    A withheld id's rows are emitted exactly as a named item's are, and `counts["withheldItems"]`
    and `counts["withheldRows"]` say how many. Every other id outside `items` is refused and
    counted under `dropped["hidden"]` (an id in `undiscovered`) or `dropped["notShipped"]`.

    The table holds no string of the caller's, and derive is never handed one: each area's place
    no field of the dump names too is "" in `strings` and listed in `blank`, and `area_strings`
    says which area each place stands for. The caller (ItemTree's era_places) puts its strings
    there and adds its own tables on its own side.
    """
    if not isinstance(cmangos, CmangosOnly):
        raise TypeError(
            f"derive reads the CMaNGOS half of the input (cmangos_only), not {type(cmangos).__name__}"
        )
    if not isinstance(selected, BuildFacts):
        raise TypeError(f"derive reads plain selections (BuildFacts), not {type(selected).__name__}")
    era_input = cmangos
    withheld_ids = selected.withheld
    dropped: dict[str, int] = {
        "hidden": 0,
        "notShipped": 0,
        "refLoop": 0,
        "scaffolding": 0,
        "noArea": 0,
        "containerNotShipped": 0,
        "curatedQuest": 0,
        "displayNotInBuild": 0,
        "questGiverNotShipped": 0,
        "questGiverUntitled": 0,
        "questGiverScaffolding": 0,
        "objectGiverNotShipped": 0,
        "objectGiverUntitled": 0,
        "objectGiverScaffolding": 0,
        "trainerUnnamed": 0,
        "trainerSpellUnknown": 0,
        "trainerSpellClass": 0,
        "trainerNothingKnown": 0,
        "classTrainerUnnamed": 0,
        "classTrainerNotSpawned": 0,
        "classTrainerNoClass": 0,
        "questRequiresNotShipped": 0,
        "questRequiresScaffolding": 0,
        "questProvidedUntitled": 0,
        "questProvidedScaffolding": 0,
        "questProvidedNotShipped": 0,
    }
    counts: dict[str, int] = {
        "multiQuest": 0,
        "furtherQuests": 0,
        "furtherQuestsDropped": 0,
        "worldDropRule": 0,
        "vendorSummaryRule": 0,
        "summaryRows": 0,
        "summaryOfOne": 0,
    }
    strings = _Strings()
    area_strings: dict[int, int] = {}
    # Brief EK1 (R2): where each area's string sits in `s` is handed over as numbers, never as the
    # string: its rank among the dump's own strings (dump_strings) and, where it is not one of
    # them, its tie among the caller's strings of that rank. A string the dump holds itself is that
    # string's place; any other is a place reserved by its key alone. Either way EraSources.lua
    # ships it blank unless a field of the dump names it too.
    universe = dump_strings(era_input)
    positions = {value: position for position, value in enumerate(universe)}

    def area_place(area: int) -> int:
        rank = selected.area_ranks.get(area)
        if rank is None:
            raise EraSourcesError(f"area {area} is carried by a row and has no rank (BuildFacts.area_ranks)")
        tie = selected.area_ties.get(area)
        if tie is not None:
            return strings.reserve(rank, tie)
        if not 0 <= rank < len(universe):
            raise EraSourcesError(f"area {area}'s rank {rank} names no string of the dump")
        return strings.add(universe[rank], blank=True)

    # Every creature name any shipped row or any full list names, for the kinds table.
    creature_names: set[str] = set()

    candidates = collect(era_input, selected, dropped)

    # itemId -> the quests that hand it over, in quest id order, built once.
    quests_for: dict[int, list[QuestFacts]] = defaultdict(list)
    for quest_id in sorted(era_input.quests):
        quest = era_input.quests[quest_id]
        for item in quest.items:
            quests_for[item].append(quest)

    # Every item either database says anything about, counted once per item.
    for item in sorted(set(candidates) | set(quests_for)):
        if item not in selected.items and item not in withheld_ids:
            dropped["hidden" if item in selected.undiscovered else "notShipped"] += 1
            candidates.pop(item, None)
            quests_for.pop(item, None)

    # The curated duplicate rule, applied quest by quest so that an item offered by an Alliance
    # quest the caller states first hand and a Horde quest it does not keeps the half it cannot
    # state (BuildFacts.quest_items_left_out). A row left with nothing is the duplicate and is
    # counted as one.
    left_out = selected.quest_items_left_out
    for item in sorted(quests_for):
        kept = [q for q in quests_for[item] if (q.id, item) not in left_out]
        if not kept:
            dropped["curatedQuest"] += 1
        quests_for[item] = kept

    entries: dict[int, list[dict]] = {}
    leftovers: dict[int, dict[int, list[dict]]] = defaultdict(dict)
    by_category: dict[int, int] = dict.fromkeys(CATEGORY_NAMES, 0)

    for item in sorted(set(candidates) | set(quests_for)):
        by_kind: dict[int, list[_Source]] = defaultdict(list)
        for source in candidates.get(item, ()):
            by_kind[source.category].append(source)
        rows: list[dict] = []
        # Rows are emitted in category order, and within a category best chance first with the
        # summary row last, so the addon draws them in file order and never sorts.
        for category in sorted(by_kind):
            made, rest = _rows_for_category(
                category, by_kind[category], strings, area_strings, area_place, counts, creature_names
            )
            rows.extend(made)
            if rest:
                leftovers[item][category] = rest
        rows.extend(_quest_rows(quests_for.get(item, ()), strings, counts))
        if not rows:
            continue
        rows.sort(key=lambda row: (row["c"], 1 if "t" in row else 0))
        entries[item] = rows
        for row in rows:
            by_category[row["c"]] = by_category.get(row["c"], 0) + 1

    quest_titles = _quest_titles(era_input, entries, strings)
    # Brief N3: a vendor's name joins ck and cd beside the creatures', so a vendor's page has a
    # portrait (and the caller's map). One entry per name: a name that is a creature and a vendor
    # both is one kind and one display, and its kind says it is both.
    vendor_names = _vendor_names(entries, leftovers, strings)
    # Brief P6a: a trainer's name joins them too, so a trainer's page has a portrait and a title. A
    # trainer's kind stays a plain kind: `tr` is what says it teaches.
    trainer_lists, teachers = _trainer_lists(era_input, selected, counts, dropped)
    trainer_levels = _trainer_levels(era_input, trainer_lists, teachers)
    counts["trainerLevels"] = sum(1 for levels in trainer_levels.values() for level in levels if level > 0)
    trainer_names = set(trainer_lists)
    # Brief TR6 (the owner's ruling of 2026-10-13): the class and pet trainers join as names of their
    # own, so a class trainer has a page with a portrait, a title, a side and its pins. No `tr`.
    class_trainer_names, class_teachers = class_trainers(era_input, counts, dropped)
    teachers = teachers | class_teachers
    counts["classTrainerNamesNew"] = len(class_trainer_names - trainer_names)
    # Brief CT1 (the owner, 2026-10-17): and the class spells each of those names teaches, by level,
    # with its price, one list per distinct list (`tc`).
    class_list_of, class_lists, class_list_classes = _class_trainer_lists(
        era_input, class_trainer_names, counts, dropped
    )
    # Brief W15 (2026-09-29): every creature that starts or ends a titled quest ships as a name
    # of its own, with its kind, portrait, title and quest lists, even where it drops, sells and
    # trains nothing. Its kind stays a plain kind: `qg` is what says it gives quests.
    giver_names = _giver_names(era_input)
    npc_names = creature_names | vendor_names | trainer_names | class_trainer_names | giver_names
    kinds = _creature_kinds(era_input, npc_names, strings, counts)
    for index in kinds:
        name = strings.value(index)
        if name in vendor_names:
            kinds[index] = vendor_kind(kinds[index], name in creature_names)
    displays = _creature_displays(era_input, npc_names, strings, counts, dropped, selected.known_displays)
    # Brief EK1: the lowest creature entry id behind each of the same names, keyed the way ck is.
    creature_ids = _creature_ids(era_input, [strings.value(index) for index in kinds], strings, counts)
    # Who starts and ends which quest, for the same names (brief N3). A quest a giver lists that no
    # c = 3 row titles gets its title in qt, which is the table the addon names a quest from first.
    givers = _quest_givers(era_input, npc_names, strings, counts, dropped)
    handed_over = _handed_over(entries)
    added = 0
    for starts, ends in givers.values():
        for quest in (*starts, *ends):
            if quest not in handed_over and quest not in quest_titles:
                quest_titles[quest] = strings.add(era_input.quest_names[quest])
                added += 1
    counts["questGiverTitlesAdded"] = added
    # Brief EO1: the world objects that start and end quests, by name, titled by the same rule.
    object_givers = _object_givers(era_input, strings, counts, dropped)
    added = 0
    for starts, ends in object_givers.values():
        for quest in (*starts, *ends):
            if quest not in handed_over and quest not in quest_titles:
                quest_titles[quest] = strings.add(era_input.quest_names[quest])
                added += 1
    counts["objectGiverTitlesAdded"] = added
    object_giver_names = {strings.value(index) for index in object_givers}
    # Brief W12: what each kept quest asks the player to bring, so a quest item's Used by can name
    # the quest. Titled at the end, once every other string is in.
    requires = _quest_requires(
        era_input, lambda item: item in selected.items or item in withheld_ids, counts, dropped
    )
    # Brief NX1 (the owner's ruling "2A" of 2026-10-22): the item each kept quest hands the player when
    # it is taken, by the same rule for the item (shipped or withheld). Titled with qr's quests below.
    provided = quest_provided(
        era_input, lambda item: item in selected.items or item in withheld_ids, counts, dropped
    )
    # Brief T1, the owner's ruling of 2026-09-27: the title under the name, for the vendors and
    # the quest givers and enders the table names, and no other creature (the caller's side for
    # the same names, EraPlaces.lua's `cf`, is read by the same speaking_creatures rule).
    titled_names = (
        vendor_names | trainer_names | class_trainer_names | {strings.value(index) for index in givers}
    )
    subnames = _titles(era_input, titled_names, strings, counts, teachers)
    trainers = {strings.add(name): spells for name, spells in trainer_lists.items()}
    levels_of = {strings.find(name): levels for name, levels in trainer_levels.items()}
    counts["vendorNames"] = len(vendor_names)
    counts["vendorNamesSharedWithCreature"] = len(vendor_names & creature_names)
    counts["vendorKinds"] = sum(1 for packed in kinds.values() if packed < 0)
    counts["vendorDisplays"] = sum(1 for index in displays if strings.value(index) in vendor_names)
    counts["trainerNamesSharedWithOthers"] = len(trainer_names & (creature_names | vendor_names))
    giver_only = giver_names - creature_names - vendor_names - trainer_names
    counts["giverOnlyNames"] = len(giver_only)
    counts["giverOnlyTitles"] = sum(1 for index in subnames if strings.value(index) in giver_only)
    counts["trainerDisplays"] = sum(1 for index in displays if index in trainers)
    counts["trainerTitles"] = sum(1 for index in subnames if index in trainers)
    # The object names a shipped row or list names, with the category each is filed under, for the
    # caller (brief D7: the object pins are EraPlaces.lua's).
    object_names = _object_names(entries, leftovers, strings)
    # Brief EK1 Part 2c: the lowest object entry id behind each of those names, keyed the way op is.
    # Brief EO1: and behind each object name og carries, so a quest's giver row opens its page.
    object_ids = _object_ids(era_input, set(object_names) | object_giver_names, strings, counts)
    counts["objectGiverNamesSharedWithRows"] = len(object_giver_names & set(object_names))

    # Brief W12: a qr quest no c = 3 row and no qt entry titles gets its title in qt. Where `s`
    # already holds that very string the entry is its index, as every qt entry was before; where it
    # does not, the entry is the title itself, a plain string (the coordinator's ruling of
    # 2026-09-29). `s` never grows for qr: a list record's name field is PACK_NAME_DIGITS (two)
    # digits, which stop at 8,280, and before brief W15 `s` held 7,852 on 1.60.1.70009, so the
    # 646 new titles qr would add would have taken it past what a list can index. Brief W15 took
    # `s` past 8,280 anyway and put the list names first instead (see _Strings.sorted_table).
    by_index = 0
    by_string = 0
    for quest in requires:
        if quest in handed_over or quest in quest_titles:
            continue
        title = era_input.quests[quest].title
        index = strings.find(title)
        if index:
            quest_titles[quest] = index
            by_index += 1
        else:
            quest_titles[quest] = title
            by_string += 1
    counts["questRequiresTitlesByIndex"] = by_index
    counts["questRequiresTitlesByString"] = by_string
    # Brief NX1: a qp quest nothing above titles gets its title in qt by the same rule (an index where
    # `s` holds the very string, else the title itself), so its Provided items rows can name it.
    by_index = 0
    by_string = 0
    for quest in provided:
        if quest in handed_over or quest in quest_titles:
            continue
        title = era_input.quest_names[quest]
        index = strings.find(title)
        if index:
            quest_titles[quest] = index
            by_index += 1
        else:
            quest_titles[quest] = title
            by_string += 1
    counts["questProvidedTitlesByIndex"] = by_index
    counts["questProvidedTitlesByString"] = by_string
    # Brief QN1: the quests of one chain that share a title, numbered by chain position.
    chains = quest_chains(era_input.quest_names, era_input.quest_links, era_input.quest_ids)
    agree, disagree = chains.id_order_check()
    counts["questChains"] = len(chains.chains)
    counts["questChainQuests"] = len(chains.numbers)
    counts["questChainsBranched"] = chains.branched
    counts["questChainsIdOrderAgrees"] = agree
    counts["questChainsIdOrderDisagrees"] = len(disagree)
    counts["questsSameTitleUnlinked"] = chains.unlinked
    # Brief Q1: the quests tied to a game event, and the quests' levels.
    events = quest_events(era_input)
    counts["questEvents"] = len(events)
    counts["questLevels"] = len(era_input.quest_levels)
    # Brief INT1b: the class restricted quests.
    counts["questClasses"] = len(era_input.quest_classes)
    # Brief IW1 (the owner's ruling "B" of 2026-10-22): the repeatable helper quests and their parents.
    helpers = quest_helpers(era_input)
    counts["questHelpers"] = len(helpers)
    # Brief PL1 (the owner's ruling "B" of 2026-10-22): the quests that come after each quest. Brief NX2
    # (the owner's word of 2026-10-23): and the quests whose RequiredCondition asks for one rewarded, and
    # the quest each breadcrumb leads to.
    later, by_condition, by_breadcrumb = quest_later_steps(
        era_input.quest_links,
        era_input.quest_ids,
        era_input.quest_names,
        quest_conditions=era_input.quest_conditions,
        conditions=era_input.conditions,
        breadcrumbs=era_input.quest_breadcrumbs,
    )
    counts["questNextQuests"] = len(later)
    counts["questNextLinks"] = sum(len(quests) for quests in later.values())
    counts["questNextByCondition"] = by_condition
    counts["questNextByBreadcrumb"] = by_breadcrumb

    # Brief W15: the names a list record packs go first, so their two digit field always fits.
    listed_names = {
        row["n"]
        for by_kind_rows in leftovers.values()
        for rest in by_kind_rows.values()
        for row in rest
        if row.get("n")
    }
    table, remap = strings.sorted_table(listed_names, positions)
    counts["stringsListed"] = len(listed_names)
    counts["stringsListedFirst"] = int(len(table) >= PACK_BASE**PACK_NAME_DIGITS)
    for rows in entries.values():
        for row in rows:
            if "n" in row:
                row["n"] = remap[row["n"]]
            for further in row.get("m", ()):
                further["n"] = remap[further["n"]]
    for by_kind_rows in leftovers.values():
        for rest in by_kind_rows.values():
            for row in rest:
                if "n" in row:
                    row["n"] = remap[row["n"]]
    # Brief GA1: each place only the caller's string holds (a reserved place, or a dump string no
    # field of the dump names), by its place in the sorted table, is left blank: EraSources.lua
    # ships it empty and the caller puts its string back (brief EK1: this table never holds one).
    blank = {remap[index] for index in strings.blank_only()}
    for index in blank:
        table[index - 1] = ""
    area_strings = {area: remap[index] for area, index in sorted(area_strings.items())}
    # A qt value is an index into `s` (remapped with it) or, for a qr quest only, the title itself.
    quest_titles = {
        quest: title if isinstance(title, str) else remap[title]
        for quest, title in sorted(quest_titles.items())
    }
    kinds = {remap[index]: packed for index, packed in kinds.items()}
    subnames = {remap[index]: remap[title] for index, title in subnames.items()}
    trainers_out = {remap[index]: pack_spells(spells) for index, spells in trainers.items()}
    levels_out = {remap[index]: pack_levels(levels_of[index]) for index in trainers}
    displays = {remap[index]: display for index, display in displays.items()}
    creature_ids = {remap[index]: creature for index, creature in creature_ids.items()}
    object_ids = {remap[index]: object_id for index, object_id in object_ids.items()}
    givers_out = {
        remap[index]: (pack_quests(starts), pack_quests(ends)) for index, (starts, ends) in givers.items()
    }
    object_givers_out = {
        remap[index]: (pack_quests(starts), pack_quests(ends))
        for index, (starts, ends) in object_givers.items()
    }
    index_of = {
        name: remap[strings.find(name)] for name in npc_names | set(object_names) | object_giver_names
    }
    class_trainer_lists = {index_of[name]: number for name, number in class_list_of.items()}
    page_names = {
        "creature": frozenset(index_of[name] for name in creature_names),
        "vendor": frozenset(index_of[name] for name in vendor_names),
        "trainer": frozenset(index_of[name] for name in trainer_names),
        "classTrainer": frozenset(index_of[name] for name in class_trainer_names),
        "giver": frozenset(index_of[name] for name in giver_names),
        # Brief EO1: the world objects og carries, for the caller's object pins (EraPlaces.lua op).
        "objectGiver": frozenset(index_of[name] for name in object_giver_names),
    }
    object_names_out = {index_of[name]: category for name, category in object_names.items()}

    # The lists, packed and then shared: the 184 vendors of one drink are the vendors of every
    # drink, so an identical list is written once and every item that opens it points at the
    # same number.
    pool: dict[str, int] = {}
    list_index: dict[int, dict[int, int]] = {}
    list_entries = 0
    for item in sorted(leftovers):
        for category in sorted(leftovers[item]):
            rest = leftovers[item][category]
            packed = "".join(pack_record(row, category) for row in rest)
            number = pool.get(packed)
            if number is None:
                number = len(pool) + 1
                pool[packed] = number
            list_index.setdefault(item, {})[category] = number
            list_entries += len(rest)
    lists = [packed for packed, _number in sorted(pool.items(), key=lambda pair: pair[1])]

    all_rows = [row for rows in entries.values() for row in rows]
    counts["items"] = len(entries)
    counts["rows"] = len(all_rows)
    counts["rowsWithChance"] = sum(1 for row in all_rows if "p" in row)
    counts["rowsWithArea"] = sum(1 for row in all_rows if "a" in row)
    counts["rowsNamed"] = sum(1 for row in all_rows if "n" in row)
    # The hidden ids the caller named as withheld, whose rows ship all the same. See derive.
    counts["withheldItems"] = sum(1 for item in entries if item in withheld_ids)
    counts["withheldRows"] = sum(len(rows) for item, rows in entries.items() if item in withheld_ids)
    counts["rowsWithFurtherQuests"] = sum(1 for row in all_rows if "m" in row)
    counts["rowsQuestOnly"] = sum(1 for row in all_rows if "o" in row)
    counts["questOnlyWithQuest"] = sum(1 for row in all_rows if "o" in row and "q" in row)
    counts["strings"] = len(table)
    counts["questTitles"] = len(quest_titles)
    counts["questTitlesAsString"] = sum(1 for title in quest_titles.values() if isinstance(title, str))
    counts["kinds"] = len(kinds)
    counts["displays"] = len(displays)
    counts["questRelationStartRows"] = len(era_input.quest_starts)
    counts["questRelationEndRows"] = len(era_input.quest_ends)
    counts["listsShipped"] = sum(len(by_kind_rows) for by_kind_rows in list_index.values())
    counts["listsStored"] = len(lists)
    counts["listEntries"] = list_entries
    for category, name in CATEGORY_NAMES.items():
        counts[name] = by_category.get(category, 0)
    return EraSources(
        strings=table,
        blank=blank,
        area_strings=area_strings,
        rows=dict(sorted(entries.items())),
        quest_titles=quest_titles,
        kinds=dict(sorted(kinds.items())),
        displays=dict(sorted(displays.items())),
        creature_ids=dict(sorted(creature_ids.items())),
        object_ids=dict(sorted(object_ids.items())),
        quest_givers=dict(sorted(givers_out.items())),
        object_givers=dict(sorted(object_givers_out.items())),
        subnames=dict(sorted(subnames.items())),
        trainers=dict(sorted(trainers_out.items())),
        trainer_levels=dict(sorted(levels_out.items())),
        class_lists=class_lists,
        class_list_classes=class_list_classes,
        class_trainer_lists=dict(sorted(class_trainer_lists.items())),
        quest_requires={quest: pack_requires(pairs) for quest, pairs in sorted(requires.items())},
        quest_chains=chains.numbers,
        quest_events=events,
        quest_levels={
            quest: pack_quest_level(*pair) for quest, pair in sorted(era_input.quest_levels.items())
        },
        quest_classes=dict(sorted(era_input.quest_classes.items())),
        quest_helpers=helpers,
        quest_next={quest: pack_quests(quests) for quest, quests in later.items()},
        quest_provided={quest: pack_requires([pair]) for quest, pair in sorted(provided.items())},
        list_index={
            item: dict(sorted(by_kind_rows.items())) for item, by_kind_rows in sorted(list_index.items())
        },
        lists=lists,
        counts=counts,
        dropped=dropped,
        page_names=page_names,
        object_names=dict(sorted(object_names_out.items())),
        teachers=frozenset(teachers),
    )


# ----- the quest chains (brief QN1) ---------------------------------------------------------------


@dataclass
class QuestChains:
    """What quest_chains finds: the numbers to ship and what the id order check needs.

    `numbers` is questId -> (c, cl), its 1 based position in its chain and the chain's length.
    `chains` is every numbered chain as its positions in order, each position a tuple of the
    quest ids standing there in id order (two or more only where the links branch). `unlinked`
    counts the titled quests that share a title with another and are linked to none of them,
    `branched` the numbered chains with a position held by two or more quests, and `cyclic` the
    groups whose links loop, which are left unnumbered.
    """

    numbers: dict[int, tuple[int, int]] = field(default_factory=dict)
    chains: list[tuple[tuple[int, ...], ...]] = field(default_factory=list)
    unlinked: int = 0
    branched: int = 0
    cyclic: int = 0

    def id_order_agrees(self, chain: Sequence[Sequence[int]]) -> bool:
        """Whether ascending quest id gives the links' order: every quest at an earlier position
        has a smaller id than every quest at a later one."""
        return all(max(chain[n]) < min(chain[n + 1]) for n in range(len(chain) - 1))

    def id_order_check(self) -> tuple[int, list[tuple[int, ...]]]:
        """The chains id order agrees with, by count, and the ids of each one it does not, in the
        links' order (ids only)."""
        agree = 0
        disagree: list[tuple[int, ...]] = []
        for chain in self.chains:
            if self.id_order_agrees(chain):
                agree += 1
            else:
                disagree.append(tuple(quest for position in chain for quest in position))
        return agree, disagree


def quest_successors(
    links: Mapping[int, tuple[int, int, int]],
    quest_ids: Collection[int] = (),
    names: Collection[int] = (),
) -> dict[int, tuple[int, ...]]:
    """The quests that come after each quest, out of `quest_template`'s three chain link columns
    (brief QN1's rule for a step, which quest_chains numbers by; since brief PL1, the owner's ruling
    "B" of 2026-10-22, it also ships in `qo`, beside brief NX2's two more kinds of step:
    quest_later_steps): questId -> the later quest ids, ascending, in quest id
    order, for every quest with one. A positive `PrevQuestId` makes the quest a later one of that
    quest; a positive `NextQuestId` or `NextQuestInChain` names a later one of the quest itself. A
    negative link (a quest that must be in the log at the same time) is no step, and a link to itself
    or to an id `quest_template` does not hold is dropped. `quest_ids` is every entry (empty: every id
    `names` or `links` holds). Ids only. Pure."""
    known = set(quest_ids) or (set(names) | set(links))
    succ: dict[int, set[int]] = defaultdict(set)
    for quest, (prev, nxt, in_chain) in links.items():
        if quest not in known:
            continue
        if prev > 0 and prev in known and prev != quest:
            succ[prev].add(quest)
        for later in (nxt, in_chain):
            if later > 0 and later in known and later != quest:
                succ[quest].add(later)
    return {quest: tuple(sorted(succ[quest])) for quest in sorted(succ)}


# Brief NX2 (the owner's word of 2026-10-23): the CMaNGOS `conditions` row kinds qo's later steps read.
# AND and OR name two more rows (value1, value2), NOT one (value1); a quest rewarded row names its quest
# (value1). A row whose flags hold CONDITION_REVERSED answers the opposite, as a NOT does.
CONDITION_AND = -1
CONDITION_OR = -2
CONDITION_NOT = -3
CONDITION_QUEST_REWARDED = 8
CONDITION_KINDS_READ = frozenset({CONDITION_AND, CONDITION_OR, CONDITION_NOT, CONDITION_QUEST_REWARDED})
CONDITION_REVERSED = 1
# How deep a condition tree is walked; the dump's deepest is a handful of rows.
CONDITION_DEPTH = 32


def condition_quests_rewarded(conditions: Mapping[int, tuple[int, int, int, int]], entry: int) -> set[int]:
    """The quests a `conditions` row asks for rewarded (brief NX2, the owner's word of 2026-10-23): a
    quest rewarded row's quest (type 8, value1), and through AND and OR rows (types -1 and -2, value1 and
    value2) every such row below them. A NOT row (type -3) and a row whose flags reverse its answer are
    never walked into, so a quest asked for NOT rewarded is never among them, and neither is anything
    under a NOT. A row the table does not hold, a loop and a tree deeper than CONDITION_DEPTH stop the
    walk there. Ids only. Pure."""
    out: set[int] = set()
    seen: set[int] = set()
    stack = [(entry, 0)]
    while stack:
        at, depth = stack.pop()
        row = conditions.get(at)
        if row is None or at in seen or depth > CONDITION_DEPTH:
            continue
        seen.add(at)
        kind, first, second, flags = row
        if flags & CONDITION_REVERSED:
            continue
        if kind == CONDITION_QUEST_REWARDED and first > 0:
            out.add(first)
        elif kind in (CONDITION_AND, CONDITION_OR):
            stack += [(first, depth + 1), (second, depth + 1)]
    return out


def quest_later_steps(
    links: Mapping[int, tuple[int, int, int]],
    quest_ids: Collection[int] = (),
    names: Collection[int] = (),
    *,
    quest_conditions: Mapping[int, int] | None = None,
    conditions: Mapping[int, tuple[int, int, int, int]] | None = None,
    breadcrumbs: Mapping[int, int] | None = None,
) -> tuple[dict[int, tuple[int, ...]], int, int]:
    """The quests that come after each quest, as `qo` ships them: quest_successors' chain links (brief
    PL1), and since brief NX2 (the owner's word of 2026-10-23) two more kinds of step. A quest whose
    `RequiredCondition` asks for the quest rewarded (condition_quests_rewarded: through AND and OR, never
    NOT) comes after it, and a breadcrumb's `BreadcrumbForQuestId` comes after the breadcrumb. A link to
    itself or to an id `quest_template` does not hold is dropped, as quest_successors drops one. Returns
    (questId -> the later quest ids, ascending, for every quest with one; the condition links and the
    breadcrumb links the chain links do not already hold). Ids only. Pure."""
    known = set(quest_ids) or (set(names) | set(links))
    succ: dict[int, set[int]] = defaultdict(set)
    for quest, later in quest_successors(links, quest_ids, names).items():
        succ[quest].update(later)
    by_condition = by_breadcrumb = 0
    tree = conditions or {}
    for quest, entry in sorted((quest_conditions or {}).items()):
        if quest not in known:
            continue
        for earlier in sorted(condition_quests_rewarded(tree, entry)):
            if earlier in known and earlier != quest and quest not in succ[earlier]:
                succ[earlier].add(quest)
                by_condition += 1
    for quest, target in sorted((breadcrumbs or {}).items()):
        if quest in known and target in known and target != quest and target not in succ[quest]:
            succ[quest].add(target)
            by_breadcrumb += 1
    later = {quest: tuple(sorted(succ[quest])) for quest in sorted(succ) if succ[quest]}
    return later, by_condition, by_breadcrumb


def quest_chains(
    names: Mapping[int, str],
    links: Mapping[int, tuple[int, int, int]],
    quest_ids: Collection[int] = (),
) -> QuestChains:
    """Number the quests of one chain that share a title (brief QN1, the owner's ruling of 2026-10-03).

    Reads `quest_template`'s three chain link columns and nothing else of the chain: `PrevQuestId`
    (positive: the quest this one needs done first), `NextQuestId` (positive: the quest that needs
    this one done first) and `NextQuestInChain` (the quest the client offers next). Each positive
    one is a link from the earlier quest to the later; a negative `PrevQuestId` or `NextQuestId`
    (a quest that must be in the log at the same time) is not a step and is not followed. A link
    to an id `quest_template` does not hold is dropped. `names` is the titles (`quest_names`),
    `links` questId -> (PrevQuestId, NextQuestId, NextQuestInChain) and `quest_ids` every entry,
    so a link may pass through an untitled quest (empty: every id `names` or `links` holds).

    Two quests of one title are in one chain when either reaches the other through the links,
    whatever titles stand between them. A chain's position for a quest is the longest run of its
    same titled chain mates that lead to it, so a straight chain reads 1, 2, 3 and two quests
    that are alternatives at one step (one per race, say) share a number. A same titled quest
    linked to none of the others is not numbered: that is the zone suffix's case, the addon's.
    Pure.
    """
    succ = quest_successors(links, quest_ids, names)

    def reach(start: int) -> set[int]:
        seen: set[int] = set()
        stack = [start]
        while stack:
            for later in succ.get(stack.pop(), ()):
                if later not in seen:
                    seen.add(later)
                    stack.append(later)
        return seen

    by_title: dict[str, list[int]] = defaultdict(list)
    for quest, title in names.items():
        if title.strip():
            by_title[title.strip()].append(quest)
    out = QuestChains()
    parent: dict[int, int] = {}

    def root(quest: int) -> int:
        while parent[quest] != quest:
            parent[quest] = parent[parent[quest]]
            quest = parent[quest]
        return quest

    for title in sorted(by_title):
        quests = sorted(by_title[title])
        if len(quests) < 2:
            continue
        reached = {quest: reach(quest) & set(quests) for quest in quests}
        # One chain per set of quests the links join, either way round.
        parent.clear()
        parent.update({quest: quest for quest in quests})
        for quest in quests:
            for later in reached[quest]:
                parent[root(later)] = root(quest)
        groups: dict[int, list[int]] = defaultdict(list)
        for quest in quests:
            groups[root(quest)].append(quest)
        for members in sorted(groups.values()):
            if len(members) < 2:
                out.unlinked += 1
                continue
            if any(quest in reached[quest] for quest in members):
                out.cyclic += 1
                continue
            before = {quest: {other for other in members if quest in reached[other]} for quest in members}
            depth: dict[int, int] = {}
            for quest in sorted(members, key=lambda q: (len(before[q]), q)):
                depth[quest] = max((depth[other] + 1 for other in before[quest]), default=0)
            length = max(depth.values()) + 1
            positions = tuple(tuple(sorted(q for q in members if depth[q] == step)) for step in range(length))
            out.chains.append(positions)
            if any(len(position) > 1 for position in positions):
                out.branched += 1
            for quest in members:
                out.numbers[quest] = (depth[quest] + 1, length)
    out.numbers = dict(sorted(out.numbers.items()))
    return out


def quest_chain_report(chains: QuestChains) -> list[str]:
    """The `era-quest-chains` command's lines: the chains found and the id order check, ids only."""
    agree, disagree = chains.id_order_check()
    lines = [
        f"{len(chains.chains)} chains numbered over {len(chains.numbers)} quests "
        f"({chains.branched} with a step two or more quests share), "
        f"{chains.unlinked} same titled quests linked to none of their title, "
        f"{chains.cyclic} looped groups left unnumbered",
        f"id order agrees with the links on {agree} chains and disagrees on {len(disagree)}",
    ]
    lines += [" ".join(str(quest) for quest in ids) for ids in disagree]
    return lines


# ----- the event quests and the reputation turn ins (brief Q1) -----------------------------------
#
# The owner's rulings of 2026-10-09: a quest tied to a game event (the Ahn'Qiraj War Effort, a
# holiday, any event) never keeps an item and its Used by row says "Event"; a reputation turn in
# (a repeatable cloth donation and the like) never keeps one either. Both are the dump's own facts,
# ids only.

# quest_template.SpecialFlags: the quest can be done again.
QUEST_SPECIAL_REPEATABLE = 1
# Brief Q1 (the owner's ruling of 2026-10-09): `ql` packs a quest's level and minimum level into one
# whole number, level + QL_LEVEL_SPAN * minimum level (no Classic quest level reaches 128).
QL_LEVEL_SPAN = 128

# Brief INT1b (the owner's ruling of 2026-10-10, Q(b)): a class quest keeps an item only for a
# character of one of its classes. The class mask bits run by class id (bit = 2 ^ (id - 1)): 1
# Warrior, 2 Paladin, 4 Hunter, 8 Rogue, 16 Priest, 64 Shaman, 128 Mage, 256 Warlock, 1024 Druid,
# the nine playable classes, CLASS_MASK_PLAYABLE in all.
CLASS_MASK_PLAYABLE = 1 | 2 | 4 | 8 | 16 | 64 | 128 | 256 | 1024
# quest_template.ZoneOrSort below 0 is a quest sort; these nine are the class sorts, each with the one
# class mask bit it stands for. Checked against the pinned dump (every quest filed under each sort
# states exactly that RequiredClasses mask: -61 94 quests, -81 72, -82 42, -141 58, -161 46, -162 54,
# -261 44, -262 59, -263 38) and against the sorts' own names in the client's QuestSort table.
QUEST_SORT_CLASSES = {
    -61: 256,  # Warlock
    -81: 1,  # Warrior
    -82: 64,  # Shaman
    -141: 2,  # Paladin
    -161: 128,  # Mage
    -162: 8,  # Rogue
    -261: 4,  # Hunter
    -262: 16,  # Priest
    -263: 1024,  # Druid
}


def quest_class_mask(required_classes: int, zone_or_sort: int) -> int:
    """The classes one quest is for, as a class mask: its RequiredClasses joined with the class its
    ZoneOrSort names where that is a class sort (both signals, union), the playable classes' bits
    only. 0, no restriction, where neither names a class or the two together name every playable
    class."""
    mask = (max(0, required_classes) | QUEST_SORT_CLASSES.get(zone_or_sort, 0)) & CLASS_MASK_PLAYABLE
    if mask == CLASS_MASK_PLAYABLE:
        return 0
    return mask


def is_turn_in(col: Callable[[str], str | None]) -> bool:
    """Whether one quest_template row is a reputation turn in: flagged repeatable (SpecialFlags, the
    cloth turn ins, the battleground mark and faction turn ins among them, which state their
    reputation elsewhere). `col` reads the row's columns. Brief BQ27 (the owner's ruling Q6 of
    2026-10-10): the repeatable flag alone, so a one time hand in (the first cloth donation at each
    capital, A Donation of Wool among them) is an ordinary quest and keeps its items."""
    return bool(_int(col("SpecialFlags")) & QUEST_SPECIAL_REPEATABLE)


def pack_quest_level(level: int, minimum: int) -> int:
    """A quest's `ql` value: its QuestLevel plus QL_LEVEL_SPAN times its MinLevel, each 0 where the
    dump states none."""
    if not 0 <= level < QL_LEVEL_SPAN or not 0 <= minimum < QL_LEVEL_SPAN:
        raise EraSourcesError(f"a quest level of {level} or a minimum of {minimum} does not pack")
    return level + QL_LEVEL_SPAN * minimum


def quest_helpers(era_input: CmangosFacts) -> dict[int, int]:
    """Brief IW1 (the owner's ruling "B" of 2026-10-22): questId -> its parent questId, in quest id order,
    for every repeatable quest (quest_turn_ins, SpecialFlags' repeatable bit) whose PrevQuestId is below
    0: CMaNGOS's mark that the quest can only be taken while the parent quest is in the log (Filling the
    Soul Gem 593, -592: only while Saving Yenniku is). Ids only, out of the columns QN1 and Q1 read."""
    out: dict[int, int] = {}
    for quest, (previous, _next, _in_chain) in sorted(era_input.quest_links.items()):
        if previous < 0 and quest in era_input.quest_turn_ins:
            out[quest] = -previous
    return out


def quest_events(era_input: CmangosFacts) -> dict[int, int]:
    """questId -> the game event it belongs to, the lowest event id where it belongs to several,
    in quest id order: every quest `game_event_quest` names, and every quest whose givers the dump
    spawns only while a game event runs (each of them has a `creature` row, and every row of each
    has a positive `game_event_creature` event). The givers are the creatures that start it, or
    for a quest no creature starts, the creatures that end it (a Darkmoon Faire deck). The AQ War
    Effort's item collection quests are the second kind: their giver stands only in event 120."""
    events: dict[int, set[int]] = defaultdict(set)
    for quest, linked in era_input.quest_event_links.items():
        events[quest].update(event for event in linked if event > 0)
    spawned: dict[int, set[int]] = defaultdict(set)
    for spawn in era_input.spawns:
        for creature in (spawn.creature,) if spawn.creature else era_input.spawn_entries.get(spawn.guid, ()):
            spawned[creature].add(spawn.event)
    starts: dict[int, set[int]] = defaultdict(set)
    ends: dict[int, set[int]] = defaultdict(set)
    for creature, quest in era_input.quest_starts:
        starts[quest].add(creature)
    for creature, quest in era_input.quest_ends:
        ends[quest].add(creature)
    for quest in set(starts) | set(ends):
        givers = starts.get(quest) or ends.get(quest) or set()
        seen = [spawned.get(creature, set()) for creature in givers]
        if givers and all(rows and min(rows) > 0 for rows in seen):
            events[quest].update(*seen)
    return {quest: min(found) for quest, found in sorted(events.items()) if found and quest > 0}


# ----- the header the module carries -------------------------------------------------------------


def header_lines(table: EraSources) -> list[str]:
    """EraSources.lua's header comment (brief GA1: the GPL-3.0 file): the legend of the GPL_FIELDS,
    the credit, the licence lines (gpl_licence_lines, the one GPL helper) and the counts of what
    this file holds. Nothing of EraPlaces.lua's (the zone names, z, zm, zf, cf, mp, op, ok, pt, mc)
    is described or counted here: itemtree_data/era_places.py writes that file's own header."""
    counts = table.counts
    emitted = [
        f"{counts.get(name, 0)} {name.lower()}"
        for category, name in CATEGORY_NAMES.items()
        if counts.get(name, 0)
    ]
    return [
        "Historical Classic Era sources. Facts only, linked by item id. The addon joins this file to "
        "EraPlaces.lua (ours, all rights reserved), which holds the zone names and every map, pin "
        "and side, and which creature pages are one page with Forever's: z, zm, zf, cf, mp, op, ok, pt, "
        "mc and cm, and this build's own word on the class spells tc lists, tf.",
        "{ s = {strings}, r = { [itemId] = packed rows }, "
        "qt = { [questId] = string index or title }, ck = { [string index] = packed creature kind }, "
        "cd = { [string index] = creature display id }, ci = { [string index] = creature id }, "
        "oi = { [string index] = object id }, "
        "qg = { [string index] = { starts, ends } }, "
        + ("og = { [string index] = { starts, ends } }, " if table.object_givers else "")
        + "st = { [string index] = string index }, "
        "tr = { [string index] = packed spell ids }, "
        + ("tv = { [string index] = packed learn levels }, " if table.trainer_levels else "")
        + (
            "tc = { l = { packed class list, ... }, c = { class id, ... }, n = { [string index] = list "
            "number } }, "
            if table.class_trainer_lists
            else ""
        )
        + "qr = { [questId] = packed required items }, "
        "x = { [itemId] = { [c] = list number } }, xl = { packed list, ... }, "
        + ("qc = { [questId] = { c = position, cl = chain length } }, " if table.quest_chains else "")
        + ("qe = { [questId] = game event id }, " if table.quest_events else "")
        + ("ql = { [questId] = level + 128 * minimum level }, " if table.quest_levels else "")
        + ("qa = { [questId] = class mask }, " if table.quest_classes else "")
        + ("qw = { [questId] = parent questId }, " if table.quest_helpers else "")
        + ("qo = { [questId] = the quests that come after it, packed }, " if table.quest_next else "")
        + ("qp = { [questId] = the item it hands over when taken, packed }, " if table.quest_provided else "")
        + "legend = { {field, type}, ... }, packed = 1, g = the Generated stamp above }",
        "r[itemId] is a LIST of rows, in the order to draw them: category ascending, best "
        "chance first inside a category, the summary row last. Never sort it. A herb or a vein "
        "(c=8, 9) is listed NODE by node: one row per zone the node stands in, a node's zone "
        "rows together (commonest zone first), the nodes best chance first then by name. Its "
        f"cap counts nodes, not rows: {MAX_NAMED_ROWS} named nodes, t is the NODE count, and "
        "its x list holds the remaining nodes' rows in the same order. Packed (packed = 1, brief "
        "OPT7): r[itemId] is ONE string, the rows in that order joined by byte 29, each row's "
        "fields in legend order joined by byte 31, m's records joined by byte 30 and their fields "
        "by byte 28 (ItemTree-Data docs/data-format.md); the addon decodes an item on first use.",
        "row = { c category, n name (index into s), a areaId, p chance, q questId, f faction, "
        "m {further quests}, i container item id, k vendor stock, o quest only, t how many "
        "in all, lo/hi level band }",
        "Every key but c is optional. Read what your category promises and nothing else. "
        "s: every string once, sorted; once it holds more than 8,280 strings (it does since "
        "2026-09-29) in two sorted runs: first the names an xl list record carries, whose field is "
        "two base 91 digits and stops at 8,280, then every other string. The order means nothing "
        "else; look a string up by its index. No zone name: a place only a zone name (this build's "
        "AreaTable) holds is an empty string here, and the names of the places new in Forever, "
        "which come last, are not here at all; EraPlaces.lua's zs puts each back in its place when "
        "the addon joins the two.",
        "c: 1 boss drop, 2 zone drop (reserved, never emitted), 3 quest, 4 vendor, 5 world "
        "drop, 6 creature drop, 7 skinned from, 8 herb node, 9 mining vein, 10 fished, "
        "11 world object or chest, 12 pickpocketed, 13 found inside a container item.",
        "t: a summary row. t is how many sources this category has on this item IN TOTAL, so "
        "the addon subtracts the named rows it has already drawn to say 'and n more'. It "
        f"names nothing and carries no chance of its own. lo and hi are that group's level "
        f"band. The cap is {MAX_NAMED_ROWS} named rows per category per item, and a category "
        f"with exactly {SUMMARISE_AT_LEAST - 1} more than that names them all and writes no "
        "summary row at all.",
        "n: the creature (c=1, 6, 7, 12), the object (c=8, 9, 10, 11), the vendor (c=4) or "
        "the quest (c=3). A c=5 row and a c=13 row name nothing.",
        "i: the container item's own id (c=13). This build names that item itself, so the row "
        "carries no string and the addon can draw it as a real edge.",
        "a: the area, as an id THIS build's AreaTable names; EraPlaces.lua's z[a] is its name. For "
        "c=10 with no n the area IS the fishing zone, stated first hand by the source. Where a "
        "creature's (or a herb's or a vein's) every spawn is on one instance map, a is that "
        "INSTANCE's own area, taken "
        "from this build's Map table: such an area has no map and no pins, and "
        "the addon says the creature is inside it rather than drawing a map.",
        "p: the chance as a percentage to one decimal place. Absent where the source states "
        f"none, or one below {MIN_CHANCE}, at or below 0, or above 100.",
        "k: a limited stock vendor's stock count (c=4). Absent means unlimited.",
        "o: 1 means this source only gives the item while the player is on a quest that asks "
        "for it. Say so in words; there is nothing to check. On a summary row it means every "
        "source it stands for is that way. Ordinary rows come before o rows in a category.",
        "q: on a c=3 row, the quest that hands the item over. On an o row, the quest that "
        "makes it drop, where the source names exactly one; absent means unknown, never none.",
        "f: 1 Alliance, 2 Horde, 3 both (c=3); absent means the quest is open to everyone.",
        f"m: the other quests that hand the same item over (c=3), at most {MAX_FURTHER_QUESTS}: "
        "{ { q questId, n name, f faction }, ... }. Present only where there is more than one, "
        "so an Alliance player is never shown only the Horde quest.",
        "qt: the title of a quest an o row names in q, a qg list names or qr carries, for the "
        "quests no c=3 row names anywhere in the table. A value is a NUMBER, an index into s, or "
        "(only for a qr quest whose title s does not hold) a STRING, the title itself: test the "
        "type. Titles only, and the addon reads its own quest index first."
        + (" A qp quest is titled by the same rule as a qr one." if table.quest_provided else ""),
        "ck: what kind of creature a NAME is, one integer per name: CreatureType + "
        f"{KIND_TYPE_SPAN} * (MinLevel + {KIND_LEVEL_SPAN} * (MaxLevel less MinLevel + "
        f"{KIND_BAND_SPAN} * beast Family)). Present for the names c=1, 6, 7 and 12 rows and "
        "their x lists use, for the vendor names c=4 rows and lists use, and for the trainer "
        "names tr carries (a trainer's is a plain kind) and the class and pet trainers st names, "
        "and since 2026-09-29 for every quest "
        "giver and ender qg carries, including one that drops, sells and trains nothing (a "
        "plain kind: qg is what says it gives quests). A vendor's is "
        "NEGATIVE, -(2 * kind + both + 1), both 1 where the name is a creature row's too. Where "
        "two creatures share a name, the commoner type and the widest level band.",
        "cd: the CreatureDisplayInfo id the client draws that NAME's portrait from, keyed the "
        "way ck is. creature_template.ModelId1 (falling back to ModelId2..4 where it is 0), "
        "the commonest where creatures of one name disagree, and every id checked against THIS "
        "build's own CreatureDisplayInfo: an id this build has not is not shipped. A plain "
        "integer, no art of any kind. A name with no entry keeps its stock kind icon.",
        "ci: the CMaNGOS creature id a NAME's page is keyed by, keyed the way ck is: the LOWEST "
        "creature_template entry whose Name is exactly that string (case and spacing included), so "
        "creatures of one name still share one page. Present for every name ck carries that an entry "
        "states exactly.",
        "oi: the CMaNGOS object id an OBJECT name's page is keyed by (a herb, a vein, a fishing pool "
        "or a chest: the names c=8, 9, 10 and 11 rows and their x lists use, and since 2026-10-22 the "
        "world objects og carries): the LOWEST "
        "gameobject_template entry whose name is exactly that string, so objects of one name share one "
        "page. Present for every such name an entry states exactly.",
        "qg: the quests a creature NAME starts and ends (creature_questrelation, "
        "creature_involvedrelation), keyed the way ck is: two packed strings, each quest id as "
        f'{QG_QUEST_DIGITS} base 91 digits, ascending, "" for none. A quest in both lists is '
        "both started and ended there. Every quest here is titled by a c=3 row or by qt. Since "
        "2026-09-29 every creature that starts or ends a titled quest has an entry, not only "
        "one that drops, sells or trains something: such a giver ships its name, ck, cd and st "
        "the way a vendor does (its pins and side are EraPlaces.lua's). "
        + (
            "og: the quests a world OBJECT name starts and ends (gameobject_questrelation, "
            "gameobject_involvedrelation, since 2026-10-22: a wanted poster, a sign), keyed by the "
            "object name's index the way oi is and packed exactly as qg is; its own key because one "
            "string can name a creature and an object both. Every quest here is titled by a c=3 row "
            "or by qt; every name here has its id in oi (its pins are EraPlaces.lua's op). "
            if table.object_givers
            else ""
        ),
        "st: the title under a vendor's, a trainer's or a quest giver's NAME "
        "(creature_template.SubName, such as Cooking Supplies), as an index into s, keyed the way "
        "ck is. Present only for the vendor names c=4 rows and lists use, the names tr and qg "
        "carry, the class and pet trainers (since 2026-10-13: creature_template.TrainerType 0 or "
        "3 on a creature that teaches and is spawned, listed for its place, with no tr), and only "
        "where the source states one. Where creatures share a name, a vendor's "
        "title wins, then a trainer's, then the commonest. "
        "tr: the spells a trainer NAME teaches (npc_trainer, and npc_trainer_template through "
        "creature_template.TrainerTemplateId, a learn spell read as the spell it teaches by "
        "spell_template's learn effect), keyed the way ck is: one packed string, each spell id as "
        f"{TR_SPELL_DIGITS} base 91 digits, ascending. Only spells THIS build's SkillLineAbility "
        "files under a profession or secondary skill line: no class trainer. A spell's trainers "
        "are the "
        "names whose list holds it. "
        + (
            "tv: beside each spell of the same name's tr list, in the same order, the skill rank "
            f"the trainer asks before teaching it (npc_trainer.reqskillvalue), {TV_LEVEL_DIGITS} base "
            "91 digits each, the lowest any creature of the name asks, 0 for none. "
            if table.trainer_levels
            else ""
        )
        + (
            "tc: the class spells a class trainer NAME teaches (npc_trainer and npc_trainer_template "
            "as tr reads them, for a creature whose TrainerType is a class trainer's and whose "
            "TrainerClass is a playable class): l holds each distinct list once, a run of fixed "
            f"{TC_RECORD_DIGITS} byte records in the x lists' base 91 alphabet, most significant digit "
            f"first: the spell id ({TC_SPELL_DIGITS} digits), the level the trainer asks "
            f"(npc_trainer.reqlevel, {TC_LEVEL_DIGITS} digit) and the price in copper "
            f"(npc_trainer.spellcost, {TC_COST_DIGITS} digits), in level order then spell id, each the "
            "lowest any creature of the name asks; c[i] is the class list i is for (creature_template."
            "TrainerClass: 1 Warrior, 2 Paladin, 3 Hunter, 4 Rogue, 5 Priest, 7 Shaman, 8 Mage, 9 "
            "Warlock, 11 Druid); n is keyed the way ck is, a class trainer name's 1 based number into "
            "l. Every spell the dump states, the ones a client build no longer has included. "
            if table.class_trainer_lists
            else ""
        )
        + "qr: what a quest asks the player to bring (quest_template.ReqItemId1..4 and "
        "ReqItemCount1..4), keyed by quest id: one packed string, a run of fixed "
        f"{QR_ITEM_DIGITS + QR_COUNT_DIGITS} byte records in the x lists' base 91 alphabet, most "
        f"significant digit first: the item id ({QR_ITEM_DIGITS} digits) then how many "
        f"({QR_COUNT_DIGITS} digits), in the quest's own slot order. Only items this build ships "
        "(or withholds); a quest asking for none of them has no entry. An item's Used by quests "
        "are the quests whose record holds it. Every quest here is titled by a c=3 row or by qt "
        "(as an index or as a plain string; s gains no string for qr).",
        *(
            [
                "qc: the quests of one chain that share a title (quest_template.PrevQuestId, "
                "NextQuestId and NextQuestInChain), keyed by quest id: c its 1 based position in "
                "the chain, cl the chain's length. Same titled quests the links do not join have "
                f"no entry. {counts.get('questChains', 0)} chains over "
                f"{counts.get('questChainQuests', 0)} quests.",
            ]
            if table.quest_chains
            else []
        ),
        *(
            [
                "qe: the quests tied to a game event (a holiday, the Ahn'Qiraj War Effort, the "
                "Darkmoon Faire), keyed by quest id: the game_event entry it belongs to, the lowest "
                "where several. A quest game_event_quest names, or one whose givers (the creatures "
                "that start it, else those that end it) are spawned only while an event runs: every "
                "creature row of each has a positive game_event_creature event. "
                f"{counts.get('questEvents', 0)} quests.",
            ]
            if table.quest_events
            else []
        ),
        *(
            [
                "ql: a quest's level and the level it can be taken from (quest_template.QuestLevel and "
                f"MinLevel), keyed by quest id: level + {QL_LEVEL_SPAN} * minimum level, 0 for a level the "
                f"dump does not state. {counts.get('questLevels', 0)} quests.",
            ]
            if table.quest_levels
            else []
        ),
        *(
            [
                "qa: the classes a class quest is for, keyed by quest id: a class mask (1 Warrior, 2 "
                "Paladin, 4 Hunter, 8 Rogue, 16 Priest, 64 Shaman, 128 Mage, 256 Warlock, 1024 Druid), "
                "quest_template.RequiredClasses joined with the class its ZoneOrSort names where that "
                "is a class sort. Only a quest some classes cannot do. "
                f"{counts.get('questClasses', 0)} quests.",
            ]
            if table.quest_classes
            else []
        ),
        *(
            [
                "qw: a repeatable quest that can only be taken while another quest is in the log, keyed "
                "by quest id: that parent quest's id (quest_template.PrevQuestId below 0 on a quest "
                f"whose SpecialFlags mark it repeatable). {counts.get('questHelpers', 0)} quests.",
            ]
            if table.quest_helpers
            else []
        ),
        *(
            [
                "qo: the quests that come after a quest, keyed by quest id: one packed string, each later "
                f"quest's id as {QG_QUEST_DIGITS} base 91 digits (as a qg list), ascending. A later quest is "
                "one whose quest_template.PrevQuestId is the quest, or the quest's own NextQuestId or "
                "NextQuestInChain, each above 0; one whose RequiredCondition asks for the quest rewarded "
                "(a conditions row of type 8, through AND and OR rows, never NOT or a reversed row); or the "
                "quest's own BreadcrumbForQuestId. "
                f"{counts.get('questNextQuests', 0)} quests, {counts.get('questNextLinks', 0)} links "
                f"({counts.get('questNextByCondition', 0)} by RequiredCondition and "
                f"{counts.get('questNextByBreadcrumb', 0)} by BreadcrumbForQuestId beyond the chain links).",
            ]
            if table.quest_next
            else []
        ),
        *(
            [
                "qp: the item a quest hands the player when it is taken (quest_template.SrcItemId and "
                "SrcItemCount), keyed by quest id: one packed string, one qr record (the item id in "
                f"{QR_ITEM_DIGITS} base 91 digits, then how many in {QR_COUNT_DIGITS}). Only items this "
                "build ships (or withholds); an item that also starts the quest is kept here and left out "
                "by the reader. Every quest here is titled by a c=3 row or by qt. "
                f"{counts.get('questProvidedQuests', 0)} quests, {counts.get('questProvidedItems', 0)} "
                f"items ({counts.get('questProvidedTitlesByIndex', 0)} titled in qt by index, "
                f"{counts.get('questProvidedTitlesByString', 0)} by string).",
            ]
            if table.quest_provided
            else []
        ),
        "x, xl: the rest of the list a summary row stands for, so it can be opened and "
        "searched. x[itemId][c] is a 1 based number into xl, and xl holds each distinct list "
        "once. A list is a run of fixed width records of base 91 digits (the bytes 35 to 126 "
        "with 92 left out), most significant first: c=13 is i (3 digits) then value (2), "
        "every other category is n (2), a (2), value (2). 0 means the field is absent. The "
        f"value is the stock for c=4, and otherwise the chance in tenths of a percent plus "
        f"{PACK_QUEST_ONLY} where the source is quest only. A list entry never carries q: the "
        "row says 'only while on a quest' and names none. c=5 ships no list.",
        CREDIT,
        *licence_lines(),
        "No item names, tooltips, flavour text, icons, comments or quest text are taken from "
        "either source. No row is emitted for an item this build hides, except the "
        f"{counts.get('withheldItems', 0)} withheld items an earlier build named, whose "
        f"{counts.get('withheldRows', 0)} rows ship so they can show once the client names the "
        "item. No coordinate of any kind is in this file: the map pins are EraPlaces.lua's.",
        f"{counts.get('items', 0)} items, {counts.get('rows', 0)} rows ({', '.join(emitted)}), "
        f"{counts.get('rowsWithChance', 0)} with a chance, {counts.get('rowsWithArea', 0)} with "
        f"an area, over {len(table.gpl_strings())} strings.",
        f"{counts.get('questTitles', 0)} quest titles in qt, {counts.get('kinds', 0)} creature "
        f"kinds in ck ({counts.get('vendorKinds', 0)} of them vendors), "
        f"{counts.get('displays', 0)} creature display ids in cd, "
        f"{counts.get('creatureIds', 0)} creature ids in ci, "
        f"{counts.get('objectIds', 0)} object ids in oi, "
        f"{counts.get('questGiverNames', 0)} quest givers in qg ({counts.get('giverOnlyNames', 0)} "
        f"of them givers only; starts {counts.get('questGiverStarts', 0)}, ends "
        f"{counts.get('questGiverEnds', 0)}, {counts.get('questGiverQuests', 0)} quests in all), "
        + (
            f"{counts.get('objectGiverNames', 0)} object quest givers in og (starts "
            f"{counts.get('objectGiverStarts', 0)}, ends {counts.get('objectGiverEnds', 0)}, "
            f"{counts.get('objectGiverQuests', 0)} quests in all), "
            if table.object_givers
            else ""
        )
        + f"and {counts.get('listEntries', 0)} further sources in "
        f"{counts.get('listsShipped', 0)} lists, stored as {counts.get('listsStored', 0)} "
        f"distinct packed strings; {counts.get('subnames', 0)} titles in st; "
        f"{counts.get('trainerNames', 0)} trainers in tr ({counts.get('trainerCreatures', 0)} "
        f"creatures) teaching {counts.get('trainerPairs', 0)} name and spell pairs over "
        f"{counts.get('trainerSpells', 0)} spells, profession and secondary only; "
        f"{counts.get('classTrainerNames', 0)} class trainers and {counts.get('petTrainerNames', 0)} "
        f"pet trainers listed for their place ({counts.get('classTrainerCreatures', 0)} creatures); "
        + (
            f"{counts.get('classTrainerListNames', 0)} class trainers in tc teaching "
            f"{counts.get('classTrainerListPairs', 0)} name and spell pairs over "
            f"{counts.get('classTrainerListSpells', 0)} class spells, stored as "
            f"{counts.get('classTrainerLists', 0)} distinct lists of "
            f"{counts.get('classTrainerListRecords', 0)} records; "
            if table.class_trainer_lists
            else ""
        )
        + f"{counts.get('questRequiresQuests', 0)} quests in qr asking for "
        f"{counts.get('questRequiresItems', 0)} items ({counts.get('questRequiresPairs', 0)} quest "
        f"and item pairs; {counts.get('questRequiresTitlesByIndex', 0)} titled in qt by index, "
        f"{counts.get('questRequiresTitlesByString', 0)} by string).",
        f"{counts.get('rowsInsideInstance', 0)} rows and "
        f"{counts.get('listEntriesInsideInstance', 0)} list entries carry an instance's own area.",
    ]


MODULE_NAME = "EraSources"
# A stamp (build, baseline, generated, pipeline version) is a short identifier, never data.
_STAMP = re.compile(r"^[A-Za-z0-9_.:+\-]{1,64}$")


def module_text(
    table: EraSources, *, build: str, baseline: str, generated: str, version: str, pretty: bool = False
) -> str:
    """EraSources.lua, whole (brief GA1): the stamp line, the GPL header (header_lines, through the one
    GPL helper) and the packed GPL value (gpl_value, checked against GPL_FIELDS). The only writer of
    the file: the compile hands it the table and its stamps and writes what comes back."""
    if not isinstance(table, EraSources):
        raise TypeError(
            f"EraSources.lua is written from the EraSources derive made, not {type(table).__name__}"
        )
    for name, stamp in (
        ("build", build),
        ("baseline", baseline),
        ("generated", generated),
        ("version", version),
    ):
        if not isinstance(stamp, str) or not _STAMP.match(stamp):
            raise EraSourcesError(f"{name} must be a short identifier, not {stamp!r}")
    value = pack_module(table.gpl_value(generated))
    check_gpl_value(value, table.blank)
    header = [
        "ItemTree generated data. Do not edit.",
        f"Module: {MODULE_NAME} | Build: {build} | Baseline: {baseline} | Generated: {generated} "
        f"| Pipeline: {version}",
        *header_lines(table),
    ]
    return lua_module(MODULE_NAME, header, lua_value(value, pretty=pretty, indent=1))


# ----- assembling the stage -----------------------------------------------------------------------


def read_inputs(*, cache_dir: Path, force: bool = False) -> EraInput:
    """Fetch the pinned files and read them: an EraInput holding the CMaNGOS and pfQuest fields
    (CMANGOS_FIELDS, PFQUEST_FIELDS) and nothing of ours.

    Brief GA1: a client build's own tables and the addon's curated quests are read by the
    caller (ItemTree's own era_places module, never mirrored), which calls this first, and handed
    to `derive` only as plain selections (build_facts.BuildFacts, brief EK1). Everything here is
    I/O. The rules live in `derive`.
    """
    cmangos = fetch_pin(CMANGOS, cache_dir, force=force)
    units = fetch_pin(PFQUEST_UNITS, cache_dir, force=force)
    objects = fetch_pin(PFQUEST_OBJECTS, cache_dir, force=force)
    era_input = read_cmangos(cmangos)
    era_input.unit_points = read_spawn_points(units)
    era_input.unit_zones = zones_from_points(era_input.unit_points)
    era_input.object_points = read_spawn_points(objects)
    era_input.object_zones = zones_from_points(era_input.object_points)
    return era_input
