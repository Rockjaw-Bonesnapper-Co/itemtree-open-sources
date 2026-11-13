# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2026 Rockjaw Bonesnapper Co
# Public home, the Corresponding Source of OpenSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-open-sources
"""OpenSources.lua: a gap filler from one pinned commit of an open source quest database (brief QZ2).

The third data source beside the Forever client's own tables and the Classic Era files, on the
owner's word of 2026-10-28: the quest, item, creature and object facts the QuestieDB project
(github.com/Questie/QuestieDB, GPL-3.0) holds for WoW Forever, kept in a GPL-3.0 file of its own
with a public Corresponding Source of its own, apart from the Classic Era (CMaNGOS) files, so each
dataset stays cleanly in its own licence. The addon uses it only where nothing else of ours and
nothing of Classic Era states a fact (brief QZ3): it fills gaps at run time. This module never
decides what is a gap.

The file is a pure function of ONE pinned upstream commit (PIN): this module reads nothing of the
pipeline's (no client table, curated file, mined bank, harvest, guess or compiled output) and
filters nothing by it. The only inputs are the pinned files, whose bytes the content hash fixes, the
layer set and the Lua interpreter that composes them.

How the file is made:

1. The pinned files. `read_archive` (from the commit's tarball) or `read_tree` (from a checkout)
   take the upstream's three load lists (its TOC, its configuration and its correction manifest)
   and the files they name for the Forever flavour (`derive_plan`, read as text: each file in one
   known layer or class, anything new a stop), and `tree_from_files` refuses them unless their
   content hash is PIN.content_sha256: the sha256 of one line per file, sorted by path,
   "<path> <sha256 of its bytes>\\n". The two licence notices (PIN.notices) are checked the same
   way, each by its own sha256. The result is an `UpstreamTree`, the one input `build` takes.
2. The composition. `compose` hands those bytes to open_sources_compose.lua (Lua 5.4, checked
   first), which loads every upstream file in a sandbox (an empty environment holding only the
   stand-ins the file needs, no io, os, require, dofile, loadfile, load, debug, package,
   string.dump, pcall or setmetatable, an instruction limit and a memory ceiling) and applies the
   upstream database's Forever layers over its base in the upstream's own order: LAYERS. Each
   value remembers every layer that stated it while it stood; the lowest is its FIRST ORIGIN. The
   composer writes the few fields this file keeps, as numbers, and an object's name (hexadecimal, so
   no byte of it can end a line): no other name, no text, comment, drop rate or waypoint leaves it,
   and nothing of the upstream text is ever run outside the sandbox.
3. The selection. `select_facts` keeps the facts whose first origin is in the layer set (LAYER_SETS;
   the shipped one is SHIPPED_LAYER_SET) under the minimal key set (ids and numbers only, KEYS):
   items d o c v r s, quests g G I e E n p l m x k N P f, creatures s f l L z a, objects s z. A
   creature drop list longer than MASS_DROPPERS is a world drop and is left out whole. Brief FFP (the
   owner's item 466): beside the facts, `object_names` keeps the upstream's English name of every
   object the kept facts name, whichever layer stated it, a label and no fact; a missing name or a
   placeholder is left out and counted, and the addon keeps the object's number for that row. Brief
   RS1 (the owner's "yes" of 2026-11-09, item 593): beside the records, `required_skills` keeps the
   skill line and rank a quest asks for (the upstream's requiredSkill) whose first origin is in the
   layer set, and (0, 0) where a layer in it cleared the pair while it stood: the upstream took it
   away. Brief Q41 (the owner's go of 2026-11-10, Lost in Battle 4921): beside them,
   `objective_targets` keeps what each quest's objectives name (a creature, an object, the area its
   triggerEnd completes in) and where each named creature and object stands, from every layer, the
   base among them, since no Classic Era file names an objective's target. Brief ST1 (the owner's
   self test of 2026-11-12: the Forever Runecloth donations' "Additional Runecloth" repeats 99195 and
   99200 counted as one time quests): a quest's `f`, the repeatable bit of the upstream's
   specialFlags (QUEST_FLAGS_KEPT), by first origin like every other fact.
4. The file. `pack_selection` packs each record into one string (the packed format below) and `module_text`
   writes OpenSources.lua: the header through the one GPL helper (era_sources.gpl_licence_lines),
   the value checked against the key allow list, and no address but the Corresponding Source. The
   value carries its own pin (brief QZ6): `u` the upstream commit and `L` the layer set; the
   object names (brief FFP): `on`; the quests' required skills (brief RS1): `rs`; and the objective
   targets (brief Q41): `ot`, with its own legend and guard (check_targets).

The upstream's zone ids (its own area ids) and its map coordinates (percent of its zone's map, one
decimal) ship as they are: mapping them onto a game client's maps needs that client's tables, so it
is the addon's job at run time (or a file of ours), never this module's.
"""

from __future__ import annotations

import hashlib
import io
import re
import shutil
import subprocess
import tarfile
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from .era_sources import (
    CMANGOS_COPYRIGHT,
    PACK_BASE,
    gpl_licence_lines,
    is_scaffolding,
    pack_int,
    unpack_int,
)
from .luaout import lua_module, lua_value

MODULE_NAME = "OpenSources"
FORMAT_VERSION = 1

# Where the Corresponding Source of OpenSources.lua lives, in the GPL-3.0 section 6(d) sense: this
# module, its composer, the pin and the upstream notices, in a public repository of its own. Not
# created yet: that waits for the owner.
CORRESPONDING_SOURCE_URL = "https://github.com/Rockjaw-Bonesnapper-Co/itemtree-open-sources"


class OpenSourcesError(RuntimeError):
    pass


class GuardError(OpenSourcesError):
    """The written value or text fails its allow list (check_value, check_addresses)."""


# ----- the pin ----------------------------------------------------------------------------------

UPSTREAM_NAME = "QuestieDB"
UPSTREAM_REPOSITORY = "github.com/Questie/QuestieDB"
# The pin. `itemtree-data open-sources update` rewrites these two lines, PIN.content_sha256 and
# PIN.notices in place on a re-pin (docs/open-sources.md, "Re-pinning"): keep each on its own line
# in this shape.
QUESTIEDB_COMMIT = "e19dfdf8528334ea63da0ecc4e291c134c0fc266"
QUESTIEDB_VERSION = "v1.0.14"

# The files the composer reads are not a list of ours: they are derived from the upstream's own load
# lists at the pinned commit (its TOC, its configuration's correction registry and its correction
# manifest; `derive_plan` below), so a correction file the upstream adds is picked up by a re-pin
# with no code edit, and a file the derivation does not know stops it. The three load lists are
# pinned with the files they name: the content hash covers all of them.
ARCHIVE_URL = "https://github.com/Questie/QuestieDB/archive/{commit}.tar.gz"
NOTICE_FILES: tuple[str, ...] = ("LICENSE.md", "gpl-3.0.md")


def archive_url_for(commit: str) -> str:
    if not re.fullmatch(r"[0-9a-z]{40}", commit):
        raise OpenSourcesError("an upstream commit is 40 lower case letters and digits")
    return ARCHIVE_URL.format(commit=commit)


@dataclass(frozen=True)
class Pin:
    """One upstream commit, pinned to exact bytes: every file read (the three load lists and the
    files they name), by their content hash, and the two licence notices that ship beside the file,
    each by its own sha256. A mismatch fails rather than quietly compiling something else."""

    commit: str
    version: str
    archive_url: str
    content_sha256: str
    notices: tuple[tuple[str, str], ...]


PIN = Pin(
    commit=QUESTIEDB_COMMIT,
    version=QUESTIEDB_VERSION,
    archive_url=archive_url_for(QUESTIEDB_COMMIT),
    content_sha256="aa3e6af8802780b32ca8e8e2c2c761618ebe875fa148d1e5160c5c3335832a85",
    notices=(
        ("LICENSE.md", "d9937e385c401d234ef416b91f00290f8ea8e517f39ed4359aed99115770d8c9"),
        ("gpl-3.0.md", "cc5470feed66192387f06ae93aed0bd4fefae5a5fd7c1e54a4acf4ea64f1028b"),
    ),
)

# A file the composer reads is a few MB at most; anything near this is not the pinned upstream.
MAX_FILE_BYTES = 64 * 1024 * 1024


def content_hash(files: Mapping[str, bytes]) -> str:
    """The sha256 of one line per file, sorted by path: "<path> <sha256 of its bytes>\\n"."""
    lines = "".join(f"{path} {hashlib.sha256(files[path]).hexdigest()}\n" for path in sorted(files))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def pin_for(commit: str, version: str, files: Mapping[str, bytes], notices: Mapping[str, bytes]) -> Pin:
    """The pin that holds exactly these files and notices (a re-pin's candidate, the tests' fixture)."""
    return Pin(
        commit=commit,
        version=version,
        archive_url=archive_url_for(commit),
        content_sha256=content_hash(files),
        notices=tuple(
            (name, hashlib.sha256(notices[name]).hexdigest()) for name in NOTICE_FILES if name in notices
        ),
    )


_TREE = object()


class UpstreamTree:
    """The pinned files' bytes, checked against the pin, and the plan derived from their load lists.
    Only `tree_from_files` makes one (the constructor refuses any other caller), so `build` can only
    ever be handed checked bytes."""

    __slots__ = ("commit", "files", "notices", "plan")

    def __init__(
        self,
        token: object,
        commit: str,
        files: Mapping[str, bytes],
        notices: Mapping[str, bytes],
        plan: Plan | None = None,
    ):
        if token is not _TREE:
            raise TypeError("an UpstreamTree is made by open_sources.tree_from_files, which checks the pin")
        self.commit = commit
        self.files = dict(files)
        self.notices = dict(notices)
        self.plan = plan


def tree_from_files(
    files: Mapping[str, bytes], notices: Mapping[str, bytes] | None = None, *, pin: Pin | None = None
) -> UpstreamTree:
    """The pinned tree, or OpenSourcesError: the files must be the three load lists and exactly the
    files they name for the Forever flavour (derive_plan, whose stops are UpstreamShapeError), their
    content hash pin.content_sha256, and each notice given must match its own sha256. The pin is PIN
    unless one is given (a re-pin's candidate, the tests' fixture)."""
    pin = pin or PIN
    missing_lists = [name for name in LOAD_LISTS if name not in files]
    if missing_lists:
        raise OpenSourcesError(
            f"the upstream files are not the pinned set (missing {missing_lists}, extra [])"
        )
    plan = derive_plan({name: files[name] for name in LOAD_LISTS})
    wanted = set(LOAD_LISTS) | set(plan.files)
    if set(files) != wanted:
        missing = sorted(wanted - set(files))
        extra = sorted(set(files) - wanted)
        raise OpenSourcesError(
            f"the upstream files are not the pinned set (missing {missing}, extra {extra})"
        )
    got = content_hash(files)
    if got != pin.content_sha256:
        raise OpenSourcesError(
            f"the upstream files' content hash is {got}, the pin says {pin.content_sha256}: refusing to "
            f"build anything but {pin.commit}"
        )
    wanted_notices = dict(pin.notices)
    for name, data in (notices or {}).items():
        if name not in wanted_notices:
            raise OpenSourcesError(f"{name} is not one of the pinned notices")
        if hashlib.sha256(data).hexdigest() != wanted_notices[name]:
            raise OpenSourcesError(f"the notice {name} is not the pinned one")
    return UpstreamTree(_TREE, pin.commit, files, notices or {}, plan)


def read_files(root: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """(files, notices) out of a folder laid out as the upstream repository (a checkout, or the tree
    the fetch writes), read only and unchecked against any pin: the load lists first, then the files
    the plan derived from them names. A flavour TOC beside QuestieDB.toc is a stop."""
    root = Path(root)
    if root.is_dir():
        check_root_names(path.name for path in root.iterdir())
    files: dict[str, bytes] = {}
    for rel in LOAD_LISTS:
        path = root / rel
        if not path.is_file():
            raise OpenSourcesError(f"{rel} is missing from {root}")
        files[rel] = path.read_bytes()
    plan = derive_plan(files)
    for rel in plan.files:
        path = root / rel
        if not path.is_file():
            raise OpenSourcesError(f"{rel} is missing from {root}")
        files[rel] = path.read_bytes()
    notices = {name: (root / name).read_bytes() for name in NOTICE_FILES if (root / name).is_file()}
    return files, notices


def read_tree(root: Path, *, pin: Pin | None = None, notices: bool = True) -> UpstreamTree:
    """The pinned files out of a folder laid out as the upstream repository (a checkout, or the
    tree the fetch extracts), checked: tree_from_files."""
    pin = pin or PIN
    files, held = read_files(root)
    for name, _sha in pin.notices:
        if notices and name not in held:
            raise OpenSourcesError(f"{name} is missing from {root}")
    return tree_from_files(files, held if notices else {}, pin=pin)


def read_archive(data: bytes, *, pin: Pin | None = None) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """(files, notices) out of the commit's .tar.gz, unchecked (tree_from_files checks them).

    Two passes over the members, each reading only what it wants through extractfile and never
    extracting anything to disk: the first takes the load lists and the notices and checks the
    shape (every member under one top folder, a wanted one a regular file under MAX_FILE_BYTES,
    none twice, no flavour TOC at the top); the plan is derived from the load lists; the second
    takes the files the plan names. Nothing else in the archive is opened. `pin` is accepted for
    the callers' symmetry; the members read do not depend on it."""
    del pin
    first = set(LOAD_LISTS) | set(NOTICE_FILES)
    lists, names = _archive_members(data, first)
    check_root_names(rel for rel in names if "/" not in rel)
    for rel in LOAD_LISTS:
        if rel not in lists:
            raise OpenSourcesError(f"{rel} is missing from the archive")
    plan = derive_plan({rel: lists[rel] for rel in LOAD_LISTS})
    named, _names = _archive_members(data, set(plan.files))
    missing = sorted(set(plan.files) - set(named))
    if missing:
        raise OpenSourcesError(f"the archive lacks files its load lists name: {missing}")
    files = {rel: lists[rel] for rel in LOAD_LISTS}
    files.update(named)
    notices = {rel: lists[rel] for rel in NOTICE_FILES if rel in lists}
    return files, notices


def _archive_members(data: bytes, wanted: set[str]) -> tuple[dict[str, bytes], set[str]]:
    """The wanted members' bytes, and every member's path below the top folder."""
    out: dict[str, bytes] = {}
    names: set[str] = set()
    top: str | None = None
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for member in archive:
                parts = PurePosixPath(member.name).parts
                if not parts or parts[0] in ("/", "..") or ".." in parts:
                    raise OpenSourcesError("the archive holds a path outside its own folder")
                if top is None:
                    top = parts[0]
                elif parts[0] != top:
                    raise OpenSourcesError("the archive holds more than one top folder")
                rel = "/".join(parts[1:])
                if rel:
                    names.add(rel)
                if rel not in wanted:
                    continue
                if not member.isreg():
                    raise OpenSourcesError(f"{rel} is not a regular file in the archive")
                if member.size > MAX_FILE_BYTES:
                    raise OpenSourcesError(f"{rel} is {member.size} bytes in the archive")
                if rel in out:
                    raise OpenSourcesError(f"{rel} is in the archive twice")
                handle = archive.extractfile(member)
                if handle is None:
                    raise OpenSourcesError(f"{rel} cannot be read from the archive")
                out[rel] = handle.read()
    except (tarfile.TarError, EOFError, OSError) as exc:
        raise OpenSourcesError(f"the archive cannot be read: {type(exc).__name__}") from exc
    return out, names


# ----- the layers -------------------------------------------------------------------------------

# The upstream's Forever layers in the order its registry applies them; bit 2**index in a mask.
#   base       data/Forever: the Classic Era seed (CMaNGOS lineage), coordinates converted
#   legacy     src/corrections/Forever/legacy: the inherited hand corrections
#   itemstart  legacy/itemStartFixes.lua: generated item quest starts (a site scraper's rows;
#              it only fills a start quest where none is stated)
#   delta      src/corrections/Forever/generated: the generated delta base (a site scraper's rows)
#   traces     src/corrections/Forever/traces: the aggregated player trace extract
#   authored   src/corrections/Forever/forever*Fixes.lua: hand written Forever corrections
LAYERS: tuple[str, ...] = ("base", "legacy", "itemstart", "delta", "traces", "authored")
SCRAPER_LAYERS = frozenset({"itemstart", "delta"})
POST_ERA = "post-era"
POST_ERA_NO_SCRAPER = "post-era-no-scraper"
LAYER_SETS: dict[str, frozenset[str]] = {
    # Every fact whose first origin is a layer above the base: what the upstream adds over the
    # Classic Era seed, which the Classic Era files already carry by their own lineage.
    POST_ERA: frozenset(LAYERS[1:]),
    # The same with the scraper layers never loaded at all: a fact a scraper layer alone states is
    # gone, and one a later layer states as well keeps that layer as its first origin.
    POST_ERA_NO_SCRAPER: frozenset(LAYERS[1:]) - SCRAPER_LAYERS,
}
LAYER_WORDS = {
    POST_ERA: (
        "every fact whose first origin is a layer above the emulator base: the inherited hand "
        "corrections, the generated item quest starts, the generated delta base, the player trace "
        "extract and the hand written Forever fixes"
    ),
    POST_ERA_NO_SCRAPER: (
        "every fact whose first origin is a layer above the emulator base, with the two site scraper "
        "layers (the generated item quest starts and the generated delta base) never loaded: the "
        "inherited hand corrections, the player trace extract and the hand written Forever fixes"
    ),
}

# THE ONE LINE: which layer set ships (the owner's call, brief QZ2). The file's header records it.
SHIPPED_LAYER_SET = POST_ERA


def layer_bits(layers: Iterable[str]) -> int:
    bits = 0
    for name in layers:
        bits |= 1 << LAYERS.index(name)
    return bits


def first_origin(mask: int) -> str | None:
    """The layer that first stated a value: the lowest bit of its mask, None for no origin."""
    if mask <= 0:
        return None
    return LAYERS[(mask & -mask).bit_length() - 1]


# ----- the plan: what the composer reads, from the upstream's own load lists ----------------------
#
# The upstream says itself what its Forever flavour loads, so the composer's file lists are read out
# of three of its files, AS TEXT (nothing of them runs): its TOC (QuestieDB.toc: every file the
# client loads, each line with its game type condition), its configuration (src/config.lua: the
# Forever flavour and the correction registry `config.ownedCorrections`, which names each
# correction file's module, entity, static functions and merge options) and its correction manifest
# (src/corrections/manifest.lua, the registry's other half). Each file the TOC loads for Forever is
# then put in exactly one known class by its path: a layer (LAYER_PATTERNS), an enum, meta or base
# file, or a known file the composer does not read (NOT_COMPOSED: the runtime, translations, drop
# rates, zone maps). Anything else is a STOP (UpstreamShapeError): a file in no known class, a known
# layer with no file, a registry entry that disagrees with the TOC or with its folder's layer, a
# load list whose shape is new. A new file's layer is never guessed: its folder and name decide, and
# a path no pattern takes stops the build until a person has read it.

TOC_FILE = "QuestieDB.toc"
CONFIG_FILE = "src/config.lua"
MANIFEST_FILE = "src/corrections/manifest.lua"
LOAD_LISTS: tuple[str, ...] = (TOC_FILE, CONFIG_FILE, MANIFEST_FILE)


class UpstreamShapeError(OpenSourcesError):
    """The upstream's load lists or a file's top level shape are not ones this reader knows: a stop
    (a person reads the change; nothing is guessed)."""


# The Forever flavour's game types, as the TOC's load conditions name them (config.flavors: gameType
# "camelot", alias "forever"), and every game type a condition may name.
FOREVER_GAME_TYPES = frozenset({"camelot", "forever"})
KNOWN_GAME_TYPES = frozenset({"vanilla", "tbc", "wrath", "cata", "mists"}) | FOREVER_GAME_TYPES
# A provider file's layer, by its path (each path matches at most one).
CORRECTIONS = "src/corrections/"
LAYER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("itemstart", re.compile(r"^src/corrections/Forever/legacy/itemStartFixes\.lua$")),
    ("legacy", re.compile(r"^src/corrections/Forever/legacy/classic[A-Za-z0-9]*Fixes\.lua$")),
    ("delta", re.compile(r"^src/corrections/Forever/generated/foreverBase[A-Za-z0-9]*\.lua$")),
    ("traces", re.compile(r"^src/corrections/Forever/traces/forever[A-Za-z0-9]*Traces\.lua$")),
    ("authored", re.compile(r"^src/corrections/Forever/forever[A-Za-z0-9]*Fixes\.lua$")),
)
ENUM_PATTERN = re.compile(r"^src/corrections/enum/[A-Za-z0-9_]+\.lua$")
FIRST_ENUM = "src/corrections/enum/constants.lua"
META_PATTERN = re.compile(r"^src/meta/(quest|npc|item|object)Meta\.lua$")
BASE_PATTERN = re.compile(r"^data/Forever/forever(Quest|Npc|Item|Object)DB\.lua$")
_ENTITY_OF = {"quest": "Quest", "npc": "Npc", "item": "Item", "object": "Object"}
# The files the Forever TOC loads that the composer never reads, each family with why. The data
# families are listed file by file, so a new support file stops rather than being taken for one.
NOT_COMPOSED: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(pattern), why)
    for pattern, why in (
        (r"^src/config\.lua$", "the configuration (read as text for the registry)"),
        (r"^src/meta/(normalize|codec)\.lua$", "schema helpers of the runtime"),
        (r"^src/corrections/tablePatch\.lua$", "the runtime's patch engine"),
        (r"^src/flavors/[A-Za-z]+\.lua$", "client flavour selection"),
        (r"^src/read/[A-Za-z_]+\.lua$", "the runtime's data loaders"),
        (r"^data/_end\.lua$", "loader teardown"),
        (r"^src/support/[A-Za-z_]+\.lua$", "the runtime's support loader and helpers"),
        # The Forever support block (src/support/data.lua: whole tables the upstream's consumer reads,
        # never applied to its entities), each file read and classified by brief OS14 (the owner's
        # "1B add new" of 2026-11-11; docs/open-sources.md, "The support files"). None states a
        # fact of the shipped layer set under a key the allow list holds.
        (
            r"^support/Forever/Zones/(dungeons|subZoneToParentZone|instanceIdToAreaId|areaIdToUiMapId"
            r"|uiMapIdToAreaId)\.lua$",
            "zone maps: area, sub zone, instance and map ids and dungeon entrances (mapping areas onto "
            "a client's maps is the addon's or a file of ours, never this file's)",
        ),
        (
            r"^support/Forever/DropTables/(itemDropCorrections|classicItemDrops)\.lua$",
            "drop rates, the Classic seed (no rate leaves the composer, and the seed is below the post "
            "era layers)",
        ),
        (
            r"^support/Forever/QuestXP/xpDB-classic\.lua$",
            "quest experience, the Classic seed (below the post era layers)",
        ),
        (
            r"^support/Forever/QuestXP/xpDB-traces\.lua$",
            "quest experience from the player trace extract (the upstream never applies its level to "
            "an entity; the experience is a key the allow list does not hold)",
        ),
        (
            r"^support/Forever/FactionTemplates/factionTemplateClassic\.lua$",
            "faction templates, the client's own (a creature's side is its friendlyToFaction)",
        ),
        (
            r"^src/corrections/(registry|compat|register|manifest|_begin|_end)\.lua$",
            "the correction registry",
        ),
        (r"^src/corrections/scopes/[A-Za-z]+\.lua$", "seasonal scope markers"),
        (r"^src/derived/[A-Za-z_]+\.lua$", "derived passes the runtime runs"),
        (r"^src/l10n/[A-Za-z0-9_/]+\.lua$", "the runtime's localisation"),
        (
            r"^l10n/Forever/(traces/)?lookup(Quests|Npcs|Items|Objects)/[a-z]{2}[A-Z]{2}\.lua$",
            "translated names (never a fact this file keeps)",
        ),
        (r"^src/ui/[A-Za-z_]+\.lua$", "the runtime's interface"),
        (r"^src/api\.lua$", "the runtime's public API"),
    )
)
# What the registry must say of each layer's providers: the load order window the upstream applies
# them in and whether it marks them generated (None: either). A provider whose entry disagrees with
# its folder's layer is a stop, because the order the composer applies would then differ from the
# upstream's. Known difference, accepted since brief QZ0: inside the Era window the upstream applies
# its generated files (the reputation and item start fixes) before the hand ones; the composer
# applies by layer (legacy, then itemstart), which at v1.0.9 gives the same file.
LAYER_REGISTRY: dict[str, tuple[str, bool | None]] = {
    "legacy": ("Era", None),
    "itemstart": ("Era", True),
    "delta": ("ForeverDeltaBase", True),
    "traces": ("Forever", True),
    "authored": ("Forever", False),
}
SPEC_FIELDS = frozenset(
    {
        "owned",
        "file",
        "module",
        "datatype",
        "static",
        "dynamic",
        "sourceExpansionOrder",
        "minExpansionOrder",
        "expansions",
        "window",
        "generated",
        "options",
    }
)
# The merge options the composer applies (each `true` when given).
PROVIDER_OPTIONS = frozenset({"noNewEntries", "noOverwrites"})
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SAFE_PATH = re.compile(r"^(?:[A-Za-z0-9_][A-Za-z0-9_.-]*/)*[A-Za-z0-9_][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class Provider:
    """One correction file the composer applies: its layer, path, module, entity, the static
    functions it calls in order, and its merge options (the names set true)."""

    layer: str
    path: str
    module: str
    entity: str
    functions: tuple[str, ...]
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class Plan:
    """What the composer reads, in the order it reads it: the enum files (TOC order), one meta and
    one base file per entity (ENTITIES order), and the providers (by layer, then in the registry's
    order). `skipped` lists the files the Forever TOC loads that the composer never reads, with why."""

    enums: tuple[str, ...]
    metas: tuple[tuple[str, str], ...]
    bases: tuple[tuple[str, str], ...]
    providers: tuple[Provider, ...]
    skipped: tuple[tuple[str, str], ...] = ()

    @property
    def files(self) -> tuple[str, ...]:
        return (
            *self.enums,
            *(path for _entity, path in self.metas),
            *(path for _entity, path in self.bases),
            *(provider.path for provider in self.providers),
        )

    def layer_of(self, path: str) -> str:
        """The class of a planned file: enum, meta, base or its provider's layer."""
        if path in self.enums:
            return "enum"
        if path in {meta for _entity, meta in self.metas}:
            return "meta"
        if path in {base for _entity, base in self.bases}:
            return "base"
        for provider in self.providers:
            if provider.path == path:
                return provider.layer
        raise KeyError(path)


def layer_of_path(path: str) -> str | None:
    """The layer a provider path's folder and name put it in, or None."""
    found = [layer for layer, pattern in LAYER_PATTERNS if pattern.match(path)]
    if len(found) > 1:
        raise UpstreamShapeError(f"{path} matches more than one layer pattern")
    return found[0] if found else None


def check_root_names(names: Iterable[str]) -> None:
    """The upstream's top folder must not hold a flavour TOC: the client loads one before
    QuestieDB.toc, and this reader follows only the source mode TOC."""
    for name in names:
        if name != TOC_FILE and re.fullmatch(r"QuestieDB_[A-Za-z0-9]+\.toc", name, re.IGNORECASE):
            raise UpstreamShapeError(
                f"the upstream holds a flavour TOC ({name}), which the client loads instead of {TOC_FILE}: "
                "a load list this reader does not follow"
            )


# ----- reading the load lists as text ------------------------------------------------------------

_TOC_FILE_LINE = re.compile(r"^(?P<path>[A-Za-z0-9_][A-Za-z0-9_\\/.-]*)(?:\s+\[(?P<cond>[^\]\[]*)\])?\s*$")
_TOC_CONDITION = re.compile(r"^(?P<kind>AllowLoadGameType|ExcludeLoadGameType)\s+(?P<types>[a-z, ]+)$")


def toc_forever_files(text: str) -> list[tuple[int, str]]:
    """(line number, path) of every file the TOC loads for the Forever flavour, in order. Read as
    text: a comment or metadata line (#), a blank line, or a file path with at most one game type
    condition; any other line, condition or game type is a stop."""
    out: list[tuple[int, str]] = []
    seen: set[str] = set()
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _TOC_FILE_LINE.match(line)
        if not match:
            raise UpstreamShapeError(f"{TOC_FILE} line {number} is not a shape this reader knows")
        path = match.group("path").replace("\\", "/")
        if not _SAFE_PATH.match(path) or ".." in path.split("/"):
            raise UpstreamShapeError(f"{TOC_FILE} line {number} names a path this reader does not take")
        loads = True
        if match.group("cond") is not None:
            cond = _TOC_CONDITION.match(match.group("cond").strip())
            if not cond:
                raise UpstreamShapeError(
                    f"{TOC_FILE} line {number} has a load condition this reader does not know"
                )
            types = {token.strip() for token in cond.group("types").split(",") if token.strip()}
            if not types or types - KNOWN_GAME_TYPES:
                raise UpstreamShapeError(
                    f"{TOC_FILE} line {number} names a game type this reader does not know"
                )
            named = bool(types & FOREVER_GAME_TYPES)
            loads = named if cond.group("kind") == "AllowLoadGameType" else not named
        if not loads:
            continue
        if not path.endswith(".lua"):
            raise UpstreamShapeError(
                f"{TOC_FILE} line {number} loads a file that is not Lua for Forever: a load list this "
                "reader does not follow"
            )
        if path in seen:
            raise UpstreamShapeError(f"{TOC_FILE} line {number} loads {path} a second time")
        seen.add(path)
        out.append((number, path))
    return out


_LUA_TOKEN = re.compile(
    r"""(?P<space>\s+)
      | (?P<long>--\[(?P<eq>=*)\[.*?\](?P=eq)\])
      | (?P<comment>--[^\n]*)
      | (?P<string>'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*")
      | (?P<number>-?[0-9]+(?:\.[0-9]+)?)
      | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<punct>[{}\[\]=,;])""",
    re.VERBOSE | re.DOTALL,
)
_ESCAPES = {"\\": "\\", "'": "'", '"': '"', "n": "\n", "t": "\t"}


class _LuaLiteral:
    """A reader for one Lua table constructor of plain data (strings, numbers, booleans and nested
    tables, keys as names, [string] or [number]): the upstream's registry tables, read as text.
    Anything else (an expression, a call, a variable) is a stop."""

    def __init__(self, text: str, where: str):
        self.text, self.where, self.pos = text, where, 0

    def _next(self) -> tuple[str, str]:
        while True:
            match = _LUA_TOKEN.match(self.text, self.pos)
            if not match:
                raise UpstreamShapeError(f"{self.where}: a token this reader does not know")
            self.pos = match.end()
            kind = match.lastgroup or ""
            if kind in ("space", "long", "comment"):
                continue
            return kind, match.group(kind)

    def _peek(self) -> tuple[str, str]:
        saved = self.pos
        token = self._next()
        self.pos = saved
        return token

    def _expect(self, value: str) -> None:
        kind, got = self._next()
        if kind != "punct" or got != value:
            raise UpstreamShapeError(f"{self.where}: expected {value!r} in a table this reader reads")

    def value(self) -> object:
        kind, got = self._next()
        if kind == "string":
            return self._unquote(got)
        if kind == "number":
            return float(got) if "." in got else int(got)
        if kind == "name" and got in ("true", "false"):
            return got == "true"
        if kind == "punct" and got == "{":
            return self._table()
        raise UpstreamShapeError(f"{self.where}: a value this reader does not take (only plain data)")

    def _unquote(self, quoted: str) -> str:
        body, out, index = quoted[1:-1], [], 0
        while index < len(body):
            char = body[index]
            if char == "\\":
                escaped = body[index + 1 : index + 2]
                if escaped not in _ESCAPES:
                    raise UpstreamShapeError(f"{self.where}: a string escape this reader does not take")
                out.append(_ESCAPES[escaped])
                index += 2
            else:
                out.append(char)
                index += 1
        return "".join(out)

    def _table(self) -> object:
        keyed: dict[object, object] = {}
        listed: list[object] = []
        while True:
            kind, got = self._peek()
            if kind == "punct" and got == "}":
                self._next()
                break
            if kind == "punct" and got == "[":
                self._next()
                key = self.value()
                if not isinstance(key, (str, int)) or isinstance(key, bool):
                    raise UpstreamShapeError(f"{self.where}: a table key this reader does not take")
                self._expect("]")
                self._expect("=")
                keyed[key] = self.value()
            elif kind == "name" and got not in ("true", "false"):
                self._next()
                self._expect("=")
                keyed[got] = self.value()
            else:
                listed.append(self.value())
            kind, got = self._next()
            if kind == "punct" and got == "}":
                break
            if kind != "punct" or got not in (",", ";"):
                raise UpstreamShapeError(f"{self.where}: a table this reader does not read")
        if keyed and listed:
            raise UpstreamShapeError(f"{self.where}: a table that mixes a list and keys")
        return listed if listed or not keyed else keyed


def lua_table_at(text: str, pattern: str, where: str) -> object:
    """The plain data table assigned by the one statement `pattern` matches at the start of a line
    (the pattern ends at the table's opening brace). None or more than one is a stop."""
    found = list(re.finditer(pattern, text, re.MULTILINE))
    if len(found) != 1:
        raise UpstreamShapeError(f"{where}: expected one such statement, found {len(found)}")
    reader = _LuaLiteral(text, where)
    reader.pos = found[0].end() - 1
    return reader.value()


def _text(lists: Mapping[str, bytes], name: str) -> str:
    try:
        return lists[name].decode("utf-8").removeprefix("﻿").replace("\r\n", "\n")
    except KeyError as exc:
        raise UpstreamShapeError(f"{name} is missing: it is one of the upstream's load lists") from exc
    except UnicodeDecodeError as exc:
        raise UpstreamShapeError(f"{name} is not UTF-8 text") from exc


def _forever_specs(lists: Mapping[str, bytes]) -> list[dict]:
    """The correction registry's Forever entries in registry order: the manifest's own entries, then
    config.ownedCorrections (which the manifest appends), those owned by Forever (the registry's
    rule: an owned entry applies to its owner alone, an unowned one never to Forever)."""
    config = _text(lists, CONFIG_FILE)
    manifest = _text(lists, MANIFEST_FILE)
    flavors = lua_table_at(config, r"^config\.flavors\s*=\s*\{", f"{CONFIG_FILE} config.flavors")
    forever = [entry for entry in flavors if isinstance(entry, dict) and entry.get("name") == "Forever"]  # type: ignore[union-attr]
    if len(forever) != 1:
        raise UpstreamShapeError(f"{CONFIG_FILE}: config.flavors does not hold one Forever flavour")
    flavour = forever[0]
    types = {flavour.get("gameType"), *(flavour.get("gameTypeAliases") or [])}
    if (
        types != FOREVER_GAME_TYPES
        or flavour.get("expansion") != "Forever"
        or flavour.get("dataPrefix") != "forever"
    ):
        raise UpstreamShapeError(
            f"{CONFIG_FILE}: the Forever flavour's game types, expansion or data prefix changed"
        )
    applies = re.search(
        r"^function config\.correctionApplies\(spec, flavor\)\n(?P<body>(?:.*\n)*?)end$", config, re.MULTILINE
    )
    if not applies or not (
        re.search(
            r"if\s+spec\.owned\s+then\s+return\s+spec\.owned\s*==\s*flavor\.name\s+end", applies["body"]
        )
        and re.search(r'if\s+flavor\.name\s*==\s*"Forever"\s+then\s+return\s+false\s+end', applies["body"])
    ):
        raise UpstreamShapeError(f"{CONFIG_FILE}: the rule for which corrections apply to Forever changed")
    own = lua_table_at(
        config, r"^config\.ownedCorrections\s*=\s*\{", f"{CONFIG_FILE} config.ownedCorrections"
    )
    listed = lua_table_at(manifest, r"^local manifest\s*=\s*\{", f"{MANIFEST_FILE} manifest")
    appends = re.findall(
        r"^for\s+_,\s*spec\s+in\s+ipairs\(config\.ownedCorrections\)\s+do\s+"
        r"manifest\[#manifest\s*\+\s*1\]\s*=\s*spec\s+end\s*$",
        manifest,
        re.MULTILINE,
    )
    if len(appends) != 1:
        raise UpstreamShapeError(f"{MANIFEST_FILE}: the manifest no longer appends config.ownedCorrections")
    specs: list[dict] = []
    for where, entries in ((MANIFEST_FILE, listed), (CONFIG_FILE, own)):
        if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
            raise UpstreamShapeError(f"{where}: the registry is not a list of entries")
        for entry in entries:
            owned = entry.get("owned")
            if owned is not None and not isinstance(owned, str):
                raise UpstreamShapeError(f"{where}: an entry's owner is not a name")
            if owned == "Forever":
                specs.append(entry)
    return specs


def _provider(spec: dict, sequence: int) -> tuple[Provider, int]:
    """A Forever registry entry as a Provider (and its registry sequence), checked: known fields only,
    its path's layer, and the window and generated mark that layer's providers carry."""
    unknown = sorted(set(spec) - SPEC_FIELDS)
    name = spec.get("file")
    if not isinstance(name, str) or not re.fullmatch(r"Forever/[A-Za-z0-9_/]+\.lua", name):
        raise UpstreamShapeError(f"{CONFIG_FILE}: a Forever correction entry names no file this reader takes")
    path = CORRECTIONS + name
    if unknown:
        raise UpstreamShapeError(
            f"the registry entry of {path} has fields this reader does not know: {unknown}"
        )
    layer = layer_of_path(path)
    if layer is None:
        raise UpstreamShapeError(
            f"the registry names {path}, which matches no known layer: read it, then classify it in "
            "open_sources.py (its layer is never guessed)"
        )
    module, entity = spec.get("module"), spec.get("datatype")
    if not isinstance(module, str) or not _IDENT.match(module):
        raise UpstreamShapeError(f"the registry entry of {path} names no module")
    if entity not in ENTITIES:
        raise UpstreamShapeError(f"the registry entry of {path} names an entity this reader does not know")
    static = spec.get("static")
    if (
        not isinstance(static, list)
        or not static
        or not all(isinstance(f, str) and _IDENT.match(f) for f in static)
    ):
        raise UpstreamShapeError(
            f"the registry entry of {path} has no static functions: a provider this composer does not apply"
        )
    dynamic = spec.get("dynamic", [])
    if not isinstance(dynamic, list) or not all(isinstance(f, str) and _IDENT.match(f) for f in dynamic):
        raise UpstreamShapeError(
            f"the registry entry of {path} has dynamic functions this reader does not read"
        )
    options = spec.get("options", {})
    if options == []:
        options = {}  # an empty table reads as an empty list
    if (
        not isinstance(options, dict)
        or set(options) - PROVIDER_OPTIONS
        or any(v is not True for v in options.values())
    ):
        raise UpstreamShapeError(
            f"the registry entry of {path} has merge options this composer does not apply"
        )
    if spec.get("minExpansionOrder") is not None or spec.get("sourceExpansionOrder", 1) != 1:
        raise UpstreamShapeError(
            f"the registry entry of {path} has an expansion order this composer does not apply"
        )
    if spec.get("expansions") not in (None, {"Forever": True}):
        raise UpstreamShapeError(
            f"the registry entry of {path} names expansions this composer does not apply"
        )
    generated = spec.get("generated", False)
    if not isinstance(generated, bool):
        raise UpstreamShapeError(
            f"the registry entry of {path} has a generated mark that is not true or false"
        )
    # register.WindowFor: an entry without a window under Forever/ falls to the Era window.
    window = spec.get("window", "Era")
    want_window, want_generated = LAYER_REGISTRY[layer]
    if window != want_window or (want_generated is not None and generated != want_generated):
        raise UpstreamShapeError(
            f"the registry applies {path} in the {window} window (generated {str(generated).lower()}), not "
            f"where its folder's layer {layer} sits: the order would differ from the upstream's"
        )
    provider = Provider(layer, path, module, str(entity), tuple(static), tuple(sorted(options)))
    return provider, sequence


def derive_plan(lists: Mapping[str, bytes]) -> Plan:
    """The composer's plan from the upstream's three load lists (LOAD_LISTS), read as text; any
    shape this reader does not know is an UpstreamShapeError (a stop)."""
    loaded = toc_forever_files(_text(lists, TOC_FILE))
    specs = _forever_specs(lists)
    providers = [_provider(spec, sequence) for sequence, spec in enumerate(specs)]
    by_path = {provider.path: (provider, sequence) for provider, sequence in providers}
    if len(by_path) != len(providers):
        raise UpstreamShapeError("the registry names one Forever correction file twice")
    modules = [provider.module for provider, _sequence in providers]
    if len(set(modules)) != len(modules):
        raise UpstreamShapeError(
            "two Forever correction files share a module: a shape this composer does not apply"
        )
    enums: list[str] = []
    metas: dict[str, str] = {}
    bases: dict[str, str] = {}
    toc_providers: list[str] = []
    skipped: list[tuple[str, str]] = []
    for number, path in loaded:
        layer = layer_of_path(path)
        if layer is not None:
            toc_providers.append(path)
            continue
        if ENUM_PATTERN.match(path):
            enums.append(path)
            continue
        meta = META_PATTERN.match(path)
        base = BASE_PATTERN.match(path)
        if meta or base:
            entity = _ENTITY_OF[meta.group(1)] if meta else base.group(1)  # type: ignore[union-attr]
            held = metas if meta else bases
            if entity in held:
                raise UpstreamShapeError(f"{TOC_FILE} line {number} loads a second {entity} file of its kind")
            held[entity] = path
            continue
        why = next((reason for pattern, reason in NOT_COMPOSED if pattern.match(path)), None)
        if why is None:
            raise UpstreamShapeError(
                f"{TOC_FILE} line {number} loads {path} for Forever, which matches no known layer or file "
                "class: read it, then classify it in open_sources.py (its layer is never guessed)"
            )
        skipped.append((path, why))
    if set(toc_providers) != set(by_path):
        toc_only = sorted(set(toc_providers) - set(by_path))
        registry_only = sorted(set(by_path) - set(toc_providers))
        raise UpstreamShapeError(
            "the TOC and the correction registry name different Forever correction files (TOC only "
            f"{toc_only}, registry only {registry_only})"
        )
    if toc_providers != [provider.path for provider, _sequence in providers]:
        raise UpstreamShapeError(
            "the TOC and the correction registry list the Forever corrections in different orders"
        )
    for layer in LAYERS[1:]:
        if not any(provider.layer == layer for provider, _sequence in providers):
            raise UpstreamShapeError(
                f"the layer {layer} has no file in the Forever load list: its folder vanished"
            )
    for kind, held in (("meta", metas), ("base", bases)):
        if set(held) != set(ENTITIES):
            raise UpstreamShapeError(
                f"the Forever load list lacks a {kind} file for {sorted(set(ENTITIES) - set(held))}"
            )
    if not enums or enums[0] != FIRST_ENUM:
        raise UpstreamShapeError(f"the enum files no longer start with {FIRST_ENUM}")
    ordered = sorted(providers, key=lambda pair: (LAYERS.index(pair[0].layer), pair[1]))
    return Plan(
        enums=tuple(enums),
        metas=tuple((entity, metas[entity]) for entity in ENTITIES),
        bases=tuple((entity, bases[entity]) for entity in ENTITIES),
        providers=tuple(provider for provider, _sequence in ordered),
        skipped=tuple(skipped),
    )


# ----- the top level shape of each planned file ---------------------------------------------------
#
# Before anything runs, each file the composer will load is read as text for its top level shape:
# the unindented statements the upstream writes at the top of a file. A provider declares its own
# module once, imports only the modules the composer stands in for, marks objective tables, defines
# its functions (every static function the registry names) and returns its module; a base file
# imports QuestieDB, states its keys and assigns its data string; a meta and an enum file open with
# the loader's arguments. Any other unindented statement is a stop: a new shape is read by a person
# first. (The sandbox still runs everything; this only refuses what is new before it runs.)

COMPOSER_IMPORTS = frozenset(
    {
        "QuestieDB",
        "ZoneDB",
        "QuestieProfessions",
        "QuestieCorrections",
        "l10n",
        "Phasing",
        "Expansions",
        "DropDB",
    }
)
OBJECTIVE_FIRST = frozenset(
    {
        "killCreditObjectiveFirst",
        "objectObjectiveFirst",
        "itemObjectiveFirst",
        "eventObjectiveFirst",
        "spellObjectiveFirst",
    }
)
_PROVIDER_TOP = (
    ("create", re.compile(r"^local ([A-Za-z_]\w*) = QuestieLoader:CreateModule\(\"([A-Za-z_]\w*)\"\);?$")),
    ("import", re.compile(r"^local ([A-Za-z_]\w*) = QuestieLoader:ImportModule\(\"([A-Za-z_]\w*)\"\);?$")),
    ("objective", re.compile(r"^QuestieCorrections\.([A-Za-z]+)\[[0-9]+\] = true;?$")),
    ("function", re.compile(r"^function ([A-Za-z_]\w*)[.:]([A-Za-z_]\w*)\(\)$")),
    ("end", re.compile(r"^end$")),
    ("return", re.compile(r"^return ([A-Za-z_]\w*)$")),
)
_LOADER_ARGS = re.compile(r"^local _, LibQuestieDB = \.\.\.\s*$", re.MULTILINE)


def _top_lines(text: str) -> Iterable[tuple[int, str]]:
    """(line number, line) of each unindented line that is not blank and not a comment; a long
    comment opened at the start of a line is skipped to its close."""
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        opened = re.match(r"^--\[(=*)\[", line)
        if opened:
            close = "]" + opened.group(1) + "]"
            rest = line[opened.end() :]
            while close not in rest:
                index += 1
                if index >= len(lines):
                    return  # never closed: Lua refuses the file when the composer loads it
                rest = lines[index]
            index += 1
            continue
        if line and not line[0].isspace() and not line.startswith("--"):
            yield index + 1, line
        index += 1


def check_shapes(tree: UpstreamTree, *, layers: Iterable[str] | None = None) -> None:
    """Every planned file's top level shape (of the layers given, the enum, meta and base files
    always), or UpstreamShapeError."""
    plan = tree.plan
    if plan is None:
        raise UpstreamShapeError("the tree carries no plan")
    loaded = set(LAYERS if layers is None else layers)
    for path in plan.enums:
        if not _LOADER_ARGS.search(_decoded(tree, path)):
            raise UpstreamShapeError(
                f"{path} does not open with the loader's arguments: a shape this reader does not know"
            )
    for _entity, path in plan.metas:
        text = _decoded(tree, path)
        if not (
            _LOADER_ARGS.search(text)
            and re.search(r"^local meta = \{", text, re.MULTILINE)
            and re.search(r"^return meta\s*$", text, re.MULTILINE)
        ):
            raise UpstreamShapeError(f"{path} is not a meta table of the shape this reader knows")
    for entity, path in plan.bases:
        _check_base(path, _decoded(tree, path), entity)
    for provider in plan.providers:
        if provider.layer in loaded:
            _check_provider(provider, _decoded(tree, provider.path))


def _decoded(tree: UpstreamTree, path: str) -> str:
    try:
        return tree.files[path].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UpstreamShapeError(f"{path} is not UTF-8 text") from exc


def _check_base(path: str, text: str, entity: str) -> None:
    field = {"Quest": "quest", "Npc": "npc", "Item": "item", "Object": "object"}[entity]
    opening = list(re.finditer(rf"^QuestieDB\.{field}Data = \[\[", text, re.MULTILINE))
    if len(opening) != 1:
        raise UpstreamShapeError(
            f"{path} does not assign one {field}Data string: a shape this reader does not know"
        )
    start = opening[0].start()
    close = text.find("]]", opening[0].end())
    if (
        close < 0
        or text[close + 2 :].strip(" \t\r\n")
        and not all(line.strip().startswith("--") for line in text[close + 2 :].splitlines() if line.strip())
    ):
        raise UpstreamShapeError(
            f"{path} holds statements after its data string: a shape this reader does not know"
        )
    allowed = (
        re.compile(r'^local QuestieDB = QuestieLoader:ImportModule\("QuestieDB"\);?$'),
        re.compile(rf"^QuestieDB\.{field}Keys = \{{$"),
        re.compile(r"^\}$"),
    )
    for number, line in _top_lines(text[:start]):
        if not any(pattern.match(line) for pattern in allowed):
            raise UpstreamShapeError(
                f"line {number} of {path} is a top level statement this reader does not know"
            )


def _check_provider(provider: Provider, text: str) -> None:
    created: list[tuple[str, str]] = []
    defined: set[tuple[str, str]] = set()
    for number, line in _top_lines(text):
        found = next(
            ((kind, match) for kind, pattern in _PROVIDER_TOP if (match := pattern.match(line))), None
        )
        if found is None:
            raise UpstreamShapeError(
                f"line {number} of {provider.path} is a top level statement this reader does not know"
            )
        kind, match = found
        if kind == "create":
            created.append((match.group(1), match.group(2)))
        elif kind == "import" and match.group(2) not in COMPOSER_IMPORTS:
            raise UpstreamShapeError(
                f"line {number} of {provider.path} imports a module the composer does not stand in for"
            )
        elif kind == "objective" and match.group(1) not in OBJECTIVE_FIRST:
            raise UpstreamShapeError(
                f"line {number} of {provider.path} marks a table the composer does not hold"
            )
        elif kind == "function":
            defined.add((match.group(1), match.group(2)))
    if len(created) != 1 or created[0][1] != provider.module:
        raise UpstreamShapeError(
            f"{provider.path} does not create the one module its registry entry names ({provider.module})"
        )
    local = created[0][0]
    for function in provider.functions:
        if (local, function) not in defined:
            raise UpstreamShapeError(
                f"{provider.path} does not define {provider.module}.{function} at its top level"
            )


# ----- the composition --------------------------------------------------------------------------

COMPOSER = "open_sources_compose.lua"
LUA_VERSION = "Lua 5.4"
ENTITIES = ("Quest", "Npc", "Item", "Object")
# The fields the composer writes, per entity and kind. Nothing else may come back.
PROJECTED: dict[str, dict[str, frozenset[str]]] = {
    "Quest": {
        "S": frozenset(
            {
                "sourceItemId",
                "questLevel",
                "requiredLevel",
                "requiredRaces",
                "requiredClasses",
                "nextQuestInChain",
                # Brief ST1: the special flags, of which the file keeps the repeatable bit.
                "specialFlags",
            }
        ),
        "L": frozenset({"preQuestSingle", "preQuestGroup"}),
        "G": frozenset({"startedBy", "finishedBy", "objectives"}),
        # Brief RS1: a pair, the skill line and rank a quest asks for.
        "R": frozenset({"requiredSkill"}),
        # Brief Q41: the kill credit objectives, a quest's killCreditObjectiveFirst mark and its
        # triggerEnd area's points (as P lines).
        "K": frozenset({"objectives"}),
        "F": frozenset({"killCreditObjectiveFirst"}),
        "P": frozenset(),
    },
    "Npc": {
        "S": frozenset({"npcFlags", "minLevel", "maxLevel", "zoneID", "friendlyToFaction"}),
        "P": frozenset(),
        # Brief Q41 (the owner's "Take" of 2026-11-10): a creature's name, kept only where an objective
        # names the creature (creature_names).
        "T": frozenset({"name"}),
    },
    "Item": {
        "S": frozenset({"startQuest"}),
        "L": frozenset({"npcDrops", "objectDrops", "itemDrops", "vendors", "questRewards"}),
    },
    "Object": {"S": frozenset({"zoneID"}), "P": frozenset(), "T": frozenset({"name"})},
}
_INT = re.compile(r"^-?[0-9]{1,20}$")
# A name as the composer writes one: its bytes in hexadecimal, at most its MAX_TEXT of them.
_HEX = re.compile(r"^(?:[0-9a-f]{2}){0,128}$")
_FLOAT = re.compile(r"^-?[0-9]{1,20}(?:\.[0-9]{1,20})?(?:e[-+]?[0-9]{1,3})?$")


def lua_version(lua: str) -> str:
    """What the interpreter says _VERSION is (run with -E: no LUA_INIT, no LUA_PATH)."""
    try:
        done = subprocess.run(
            [lua, "-E", "-e", "io.write(_VERSION)"], capture_output=True, text=True, timeout=30, check=False
        )
    except OSError as exc:
        raise OpenSourcesError(f"cannot run {lua}: {type(exc).__name__}") from exc
    return done.stdout.strip() if done.returncode == 0 else ""


def check_lua(lua: str) -> str:
    version = lua_version(lua)
    if version != LUA_VERSION:
        raise OpenSourcesError(f"the composer needs {LUA_VERSION}; {lua} is {version or 'not a Lua'}")
    return lua


def find_lua() -> str:
    """The first Lua 5.4 on PATH (lua5.4, then lua), else /opt/homebrew/bin/lua; checked."""
    for candidate in (shutil.which("lua5.4"), shutil.which("lua"), "/opt/homebrew/bin/lua"):
        if candidate and lua_version(candidate) == LUA_VERSION:
            return candidate
    raise OpenSourcesError(f"no {LUA_VERSION} interpreter found (lua5.4 or lua on PATH)")


def composer_path() -> Path:
    return Path(__file__).with_name(COMPOSER)


@dataclass
class Row:
    """One composed entity's projected fields, each value with its mask."""

    scalars: dict[str, tuple[int | float, int]] = field(default_factory=dict)
    lists: dict[str, list[tuple[int | float, int]]] = field(default_factory=dict)
    groups: dict[tuple[str, int], list[tuple[int | float, int]]] = field(default_factory=dict)
    # (zone, x, y, mask), zones ascending, each zone's points in the upstream's order.
    points: list[tuple[int, int | float, int | float, int]] = field(default_factory=list)
    # Brief FFP: a name as the composer wrote it, decoded and unchecked (object_name_fault checks it).
    texts: dict[str, str] = field(default_factory=dict)
    # Brief RS1: a pair field as (first, second, mask); (0, 0, mask) where a layer cleared it.
    pairs: dict[str, tuple[int, int, int]] = field(default_factory=dict)
    # Brief Q41: a quest's kill credit objectives in order, each (root creature or 0, (creatures that
    # give the credit, ...), mask), and the upstream's marks on it (killCreditObjectiveFirst). A
    # quest's `points` are its triggerEnd area's.
    credits: list[tuple[int, tuple[int, ...], int]] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class LayerStat:
    layer: str
    path: str
    rows: int
    created: int
    steps: int


@dataclass(frozen=True)
class Composed:
    rows: dict[str, dict[int, Row]]
    stats: tuple[LayerStat, ...]


def _number(token: str, where: int) -> int | float:
    if _INT.match(token):
        return int(token)
    if _FLOAT.match(token):
        return float(token)
    raise OpenSourcesError(f"the composer wrote a value this reader does not take (line {where})")


def parse_composed(text: bytes, paths: Iterable[str] | None = None) -> Composed:
    """The composer's lines, read strictly: any line that is not one of its numeric records ends
    the build. A stats line must name one of `paths` (the plan's files; any safe path when None).
    Nothing of a refused line is repeated in the error."""
    known = None if paths is None else frozenset(paths)
    try:
        decoded = text.decode("ascii")
    except UnicodeDecodeError as exc:
        raise OpenSourcesError("the composer wrote bytes that are not ASCII") from exc
    lines = decoded.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    rows: dict[str, dict[int, Row]] = {entity: {} for entity in ENTITIES}
    stats: list[LayerStat] = []
    ended = False
    for number, line in enumerate(lines, start=1):
        if ended:
            raise OpenSourcesError(f"the composer wrote past its end (line {number})")
        parts = line.split("\t")
        kind = parts[0]
        if kind == "END":
            if len(parts) != 2 or not _INT.match(parts[1]) or int(parts[1]) != number - 1:
                raise OpenSourcesError("the composer's end line does not count its lines")
            ended = True
            continue
        if kind == "#":
            if (
                len(parts) != 6
                or parts[1] not in LAYERS
                or not _SAFE_PATH.match(parts[2])
                or (known is not None and parts[2] not in known)
            ):
                raise OpenSourcesError(
                    f"the composer wrote a stats line this reader does not know ({number})"
                )
            counts = [_number(p, number) for p in parts[3:]]
            if not all(isinstance(c, int) and c >= 0 for c in counts):
                raise OpenSourcesError(f"the composer wrote a bad count ({number})")
            stats.append(LayerStat(parts[1], parts[2], *counts))
            continue
        widths = {"S": 6, "L": 6, "G": 7, "P": 7, "T": 6, "R": 7, "K": 7, "F": 4}
        if kind not in widths or len(parts) != widths[kind] or parts[1] not in ENTITIES:
            raise OpenSourcesError(f"the composer wrote a line this reader does not know ({number})")
        entity = parts[1]
        ident = _number(parts[2], number)
        # Brief Q41: an F line carries no mask (a mark, never a fact of its own).
        mask = 0 if kind == "F" else _number(parts[-1], number)
        if not isinstance(ident, int) or not isinstance(mask, int) or mask < 0:
            raise OpenSourcesError(f"the composer wrote a bad id or mask ({number})")
        allowed = PROJECTED[entity]
        if kind != "P" and parts[3] not in allowed.get(kind, ()):
            raise OpenSourcesError(f"the composer wrote a field this reader does not take ({number})")
        if kind == "P" and "P" not in allowed:
            raise OpenSourcesError(f"the composer wrote spawns for {entity} ({number})")
        row = rows[entity].setdefault(ident, Row())
        if kind == "F":
            row.flags.add(parts[3])
        elif kind == "K":
            # Brief Q41: the root (0 for none) and one or more creature ids, whole numbers above 0.
            root = _number(parts[4], number)
            credited = parts[5].split(",")
            ids = (
                [_number(token, number) for token in credited] if all(_INT.match(t) for t in credited) else []
            )
            if (
                not isinstance(root, int)
                or root < 0
                or not ids
                or not all(isinstance(value, int) and value > 0 for value in ids)
            ):
                raise OpenSourcesError(
                    f"the composer wrote a kill credit this reader does not take ({number})"
                )
            row.credits.append((root, tuple(int(value) for value in ids), mask))
        elif kind == "T":
            if not _HEX.match(parts[4]) or parts[3] in row.texts:
                raise OpenSourcesError(f"the composer wrote a name this reader does not take ({number})")
            row.texts[parts[3]] = bytes.fromhex(parts[4]).decode("utf-8", "replace")
        elif kind == "R":
            # Brief RS1: two whole numbers, neither below 0, once per field.
            first, second = _number(parts[4], number), _number(parts[5], number)
            if (
                parts[3] in row.pairs
                or not isinstance(first, int)
                or not isinstance(second, int)
                or first < 0
                or second < 0
            ):
                raise OpenSourcesError(f"the composer wrote a pair this reader does not take ({number})")
            row.pairs[parts[3]] = (first, second, mask)
        elif kind == "S":
            if parts[3] in row.scalars:
                raise OpenSourcesError(f"the composer wrote a scalar twice ({number})")
            row.scalars[parts[3]] = (_number(parts[4], number), mask)
        elif kind == "L":
            row.lists.setdefault(parts[3], []).append((_number(parts[4], number), mask))
        elif kind == "G":
            group = _number(parts[4], number)
            if not isinstance(group, int):
                raise OpenSourcesError(f"the composer wrote a bad group ({number})")
            row.groups.setdefault((parts[3], group), []).append((_number(parts[5], number), mask))
        else:
            zone = _number(parts[3], number)
            if not isinstance(zone, int):
                raise OpenSourcesError(f"the composer wrote a bad zone ({number})")
            row.points.append((zone, _number(parts[4], number), _number(parts[5], number), mask))
    if not ended:
        raise OpenSourcesError("the composer's output has no end line: it did not finish")
    return Composed(rows, tuple(stats))


def _clean(raw: bytes) -> str:
    """A short, printable form of the composer's error, for the developer."""
    text = raw.decode("utf-8", "replace")
    return re.sub(r"[^ -~]", "?", text).strip()[:400]


def plan_lines(plan: Plan) -> list[str]:
    """The plan as the composer reads it on stdin, before the files: "PLAN <n>", then one tab
    separated line per file: E <path> (an enum file, in order), M <entity> <path>, B <entity> <path>,
    C <layer> <entity> <module> <functions> <options or -> <path> (a provider, in the order applied)."""
    lines = [f"E\t{path}" for path in plan.enums]
    lines += [f"M\t{entity}\t{path}" for entity, path in plan.metas]
    lines += [f"B\t{entity}\t{path}" for entity, path in plan.bases]
    lines += [
        "\t".join(
            (
                "C",
                p.layer,
                p.entity,
                p.module,
                ",".join(p.functions),
                ",".join(p.options) or "-",
                p.path,
            )
        )
        for p in plan.providers
    ]
    return [f"PLAN\t{len(lines)}", *lines]


def compose(tree: UpstreamTree, *, leave_out: Iterable[str] = (), lua: str) -> Composed:
    """The composer run over the tree's checked bytes and its plan (handed over on stdin, so what it
    composes is exactly what was hashed), its output read strictly. `leave_out` names layers never
    loaded."""
    if not isinstance(tree, UpstreamTree):
        raise TypeError(f"compose takes an UpstreamTree, not {type(tree).__name__}")
    if tree.plan is None:
        raise OpenSourcesError("the tree carries no plan")
    skip = sorted(set(leave_out))
    for name in skip:
        if name not in LAYERS or name == "base":
            raise OpenSourcesError(f"{name!r} is not a layer that can be left out")
    check_lua(lua)
    planned = set(tree.plan.files)
    payload = [("\n".join(plan_lines(tree.plan)) + "\n").encode("ascii")]
    payload.append(f"{len(planned)}\n".encode("ascii"))
    for path in sorted(planned):
        body = tree.files[path]
        payload += [path.encode("ascii") + b"\n", f"{len(body)}\n".encode("ascii"), body]
    try:
        done = subprocess.run(
            [lua, "-E", str(composer_path()), ",".join(skip) or "-"],
            input=b"".join(payload),
            capture_output=True,
            timeout=900,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise OpenSourcesError("the composer ran past its time limit") from exc
    if done.returncode != 0:
        raise OpenSourcesError(f"the composer failed: {_clean(done.stderr)}")
    return parse_composed(done.stdout, planned)


# ----- the selection ----------------------------------------------------------------------------

# A creature drop list longer than this is a world drop: the whole list is left out (brief QZ0).
MASS_DROPPERS = 40
# Records per table, by the letter the file keys them under.
TABLES = (("i", "Item"), ("q", "Quest"), ("n", "Npc"), ("o", "Object"))
ITEM_LISTS = (
    ("d", "npcDrops"),
    ("o", "objectDrops"),
    ("c", "itemDrops"),
    ("v", "vendors"),
    ("r", "questRewards"),
)
QUEST_GROUPS = (
    ("g", "startedBy", 1),
    ("G", "startedBy", 2),
    ("I", "startedBy", 3),
    ("e", "finishedBy", 1),
    ("E", "finishedBy", 2),
    ("n", "objectives", 3),
)
QUEST_SCALARS = (
    ("p", "sourceItemId"),
    ("l", "questLevel"),
    ("m", "requiredLevel"),
    ("x", "requiredRaces"),
    ("k", "requiredClasses"),
    ("N", "nextQuestInChain"),
)
NPC_SCALARS = (("l", "minLevel"), ("L", "maxLevel"), ("z", "zoneID"), ("a", "friendlyToFaction"))
# npcFlags as the file keeps them: vendor 4 and trainer 16 (the upstream's Forever flag values).
NPC_FLAGS_KEPT = 4 | 16
# Brief ST1: a quest's specialFlags as the file keeps them (`f`): the repeatable bit alone (the upstream's
# specialFlags.REPEATABLE, 1). The owner's ruling of 2026-10-17 counts a repeatable quest but never lets it
# keep an item, and nothing else tells the addon that a Forever quest repeats: Classic Era's repeatable
# flag (CMaNGOS SpecialFlags) holds Classic quests alone. The owner, 2026-11-12: "1A", approving the key on
# this allow list. Numbers alone.
QUEST_FLAGS_KEPT = 1
# The key set, in the order a record writes its keys (the allow list of each table).
KEYS: dict[str, tuple[str, ...]] = {
    "i": ("d", "o", "c", "v", "r", "s"),
    "q": ("g", "G", "I", "e", "E", "n", "p", "l", "m", "x", "k", "N", "P", "f"),
    "n": ("s", "f", "l", "L", "z", "a"),
    "o": ("s", "z"),
}
# The keys whose value is a list of ids; every other key but a spawn list is one number.
LIST_KEYS: dict[str, frozenset[str]] = {
    "i": frozenset({"d", "o", "c", "v", "r"}),
    "q": frozenset({"g", "G", "I", "e", "E", "n", "P"}),
    "n": frozenset(),
    "o": frozenset(),
}
SPAWN_TABLES = frozenset({"n", "o"})


@dataclass(frozen=True)
class Selection:
    """The kept facts per table: {id: {key: value}}, a value an int, a list of ints, or for a spawn
    list (n and o, key s) a list of (zone, ((x10, y10), ...)) in tenths of a map percent. `facts` is
    QZ0's fact count (one per list element, scalar and spawn list), `origins` counts the kept values
    by first origin, `left_out` what the rules dropped, `fact_layers` each fact's first origin (for
    a spawn list, the lowest of its points'; a re-pin's change report reads it). Brief FFP:
    `object_names` the name of each object the kept facts name, no fact and in none of the counts
    above, and `names_left_out` why the others have none, by NAME_FAULTS. Brief RS1: `required_skills`,
    questId -> (skill line, rank) whose first origin is in the layer set, (0, 0) where the upstream
    cleared the pair; each is a fact ("q", quest, REQUIRED_SKILLS_FIELD, (skill line, rank)), so the
    counts above and a re-pin's change report hold them. Brief Q41: `targets`, what each quest's
    objectives name and where (objective_targets), a label beside the facts like `object_names`."""

    layer_set: str
    records: dict[str, dict[int, dict[str, object]]]
    facts: frozenset[tuple]
    origins: dict[str, int]
    left_out: dict[str, int]
    fact_layers: dict[tuple, str] = field(default_factory=dict)
    object_names: dict[int, str] = field(default_factory=dict)
    names_left_out: dict[str, int] = field(default_factory=dict)
    required_skills: dict[int, tuple[int, int]] = field(default_factory=dict)
    # Brief Q41: the objective targets (objective_targets), beside the facts and in none of their counts.
    targets: Targets | None = None
    # Brief Q41 (the owner's "Take" of 2026-11-10): the name of each creature an objective names
    # (creature_names), a label like object_names, and why the others have none.
    creature_names: dict[int, str] = field(default_factory=dict)
    creature_names_left_out: dict[str, int] = field(default_factory=dict)


def _tenths(value: int | float) -> int:
    return int(round(round(value, 1) * 10))


# Brief FFP: why an object keeps its number for a name. What a name may hold: plain English text, the
# letters, digits and marks of a world object's label, and nothing that could read as an address. DND
# marks a row the client never shows ("Corrupted Moonwell Spell Focus (DND)"), the one such mark the
# shared test row markers do not hold at this pin.
NAME_MISSING, NAME_PLACEHOLDER, NAME_NOT_PLAIN = "missing", "placeholder", "not plain text"
_OBJECT_NAME = re.compile(r"^[A-Za-z0-9\"][A-Za-z0-9 '\"\-,.:!&()/]{0,127}$")
_NAME_PLACEHOLDER_MARK = re.compile(r"\bDND\b")


def object_name_fault(name: str) -> str | None:
    """Why the file keeps no name for an object the upstream calls `name`, or None where it does."""
    if not name.strip():
        return NAME_MISSING
    if is_scaffolding(name) or _NAME_PLACEHOLDER_MARK.search(name):
        return NAME_PLACEHOLDER
    if not _OBJECT_NAME.match(name) or _URL.search(name) or _HOST.search(name):
        return NAME_NOT_PLAIN
    return None


def object_names(
    composed: Composed,
    records: Mapping[str, Mapping[int, Mapping[str, object]]],
    targets: Iterable[int] = (),
) -> tuple[dict[int, str], dict[str, int]]:
    """Brief FFP (the owner's item 466, "A add in next release"): the upstream's name of each object the
    kept records name (a row of `o`, an item's `o`, a quest's `G` and `E`), whichever layer stated it,
    so a row the file gives reads as its container and not as a number; and how many have none, by why.
    Brief Q41: and of each object an objective names (`targets`, the objective targets' `o`), so its
    row reads as the object. The file's own records choose: nothing of ours does."""
    named: set[int] = set(records["o"]) | set(targets)
    for record in records["i"].values():
        named.update(record.get("o", ()))  # type: ignore[arg-type]
    for record in records["q"].values():
        for key in ("G", "E"):
            named.update(record.get(key, ()))  # type: ignore[arg-type]
    names: dict[int, str] = {}
    left: Counter[str] = Counter()
    for obj in sorted(named):
        row = composed.rows["Object"].get(obj)
        text = row.texts.get("name", "") if row is not None else ""
        fault = object_name_fault(text)
        if fault is None:
            names[obj] = text
        else:
            left[fault] += 1
    return names, dict(left)


# ----- the objective targets (brief Q41) ------------------------------------------------------------
#
# The owner, 2026-11-10, on Lost in Battle (4921), whose objective row read "0/1 Find Mankrik's Wife" with
# no place: "One thing we dont have that I know is a common issue for players is the location of the wife
# in this quest (questie has the location) I feel like we could add it too", his go to use the upstream's
# objective targets. What each quest's objectives name, beside the facts: the creatures (objectives group
# 1, and the one creature each kill credit objective, group 5, stands for), the objects (group 2) and the
# area its triggerEnd completes in, and where each named creature and object stands. Unlike the facts,
# from EVERY layer, the base among them: no Classic Era file names an objective's creature, object or
# area (EraSources' qr names its items alone), so the post era rule would leave the Classic quests' own
# targets out, 4921's Beaten Corpse (10668) the first of them. Numbers alone: no objective text, no icon.

# The keys of the target tables: q (a quest) c creatures and o objects in the upstream's objective order,
# a the triggerEnd area (a zone segment: the zone, then its points); n and o (a named creature or
# object) s, one segment per zone it stands in, the zone with the most spawns first, each holding its
# one point where the zone holds one spawn and no point where it holds more (the quest page pins a
# place only where one spawn stands, brief TV4's rule for a Classic Era giver).
TARGET_TABLES = ("q", "n", "o")
TARGET_KEYS: dict[str, tuple[str, ...]] = {"q": ("c", "o", "a"), "n": ("s",), "o": ("s",)}
TARGET_ZONE_KEYS: dict[str, frozenset[str]] = {
    "q": frozenset({"a"}),
    "n": frozenset({"s"}),
    "o": frozenset({"s"}),
}
KILL_CREDIT_FIRST = "killCreditObjectiveFirst"


@dataclass(frozen=True)
class Targets:
    """What `objective_targets` keeps: `quests` {quest: {"c": [creature ids], "o": [object ids], "a":
    [(zone, ((x10, y10), ...)), ...]}}, each key left out where the quest's objectives name none of it;
    `places` {"n": {creature: [(zone, point or ())]}, "o": {object: ...}}, every creature and object the
    quests name that the upstream places, the point in tenths of a map percent; `left_out` what the rules
    dropped, by why."""

    quests: dict[int, dict[str, object]]
    places: dict[str, dict[int, list[tuple[int, tuple[tuple[int, int], ...]]]]]
    left_out: dict[str, int]


def credit_target(root: int, credited: Sequence[int], placed: Callable[[int], bool]) -> int:
    """The one creature a kill credit objective stands for: its root where the root gives the credit
    itself or stands somewhere, else the first credited creature that stands somewhere, else the root,
    else the first credited creature. `placed(creature)` says whether the upstream places it."""
    if root > 0 and (root in credited or placed(root)):
        return root
    for creature in credited:
        if placed(creature):
            return creature
    return root if root > 0 else credited[0]


def _zone_places(
    points: Iterable[tuple[int, int | float, int | float, int]],
) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    """A creature's or object's spawns as the target tables keep them: per zone, the most spawns first
    (then the lower zone id), the one point where the zone holds one spawn, none where it holds more."""
    by_zone: dict[int, list[tuple[int, int]]] = {}
    for zone, x, y, mask in points:
        if x >= 0 and y >= 0 and mask > 0:
            by_zone.setdefault(int(zone), []).append((_tenths(x), _tenths(y)))
    ordered = sorted(by_zone.items(), key=lambda item: (-len(item[1]), item[0]))
    return [(zone, tuple(points) if len(points) == 1 else ()) for zone, points in ordered]


def objective_targets(composed: Composed) -> Targets:
    """Brief Q41: every quest's objective targets and their places, from every layer (a value counts once
    some layer stated it while it stood: mask above 0). A pure function of the composed upstream."""
    left: Counter[str] = Counter()
    npcs, objects = composed.rows["Npc"], composed.rows["Object"]

    def placed(creature: int) -> bool:
        row = npcs.get(creature)
        return row is not None and any(x >= 0 and mask > 0 for _zone, x, _y, mask in row.points)

    quests: dict[int, dict[str, object]] = {}
    for quest, row in sorted(composed.rows["Quest"].items()):
        record: dict[str, object] = {}
        creatures = [int(value) for value, mask in row.groups.get(("objectives", 1), []) if mask > 0]
        credits = [credit_target(root, ids, placed) for root, ids, mask in row.credits if mask > 0]
        unstated = sum(1 for _v, mask in row.groups.get(("objectives", 1), []) if mask <= 0)
        if unstated:
            left["noOrigin"] += unstated
        monsters = credits + creatures if KILL_CREDIT_FIRST in row.flags else creatures + credits
        if any(value <= 0 for value in monsters):
            left["badCreature"] += sum(1 for value in monsters if value <= 0)
            monsters = [value for value in monsters if value > 0]
        if monsters:
            record["c"] = monsters
        things = [
            int(value) for value, mask in row.groups.get(("objectives", 2), []) if mask > 0 and value > 0
        ]
        if things:
            record["o"] = things
        area: dict[int, list[tuple[int, int]]] = {}
        for zone, x, y, mask in row.points:
            if x >= 0 and y >= 0 and mask > 0:
                area.setdefault(int(zone), []).append((_tenths(x), _tenths(y)))
            else:
                left["areaPointUnplaced"] += 1
        if area:
            record["a"] = [(zone, tuple(points)) for zone, points in sorted(area.items())]
        if record:
            quests[quest] = record
    places: dict[str, dict[int, list[tuple[int, tuple[tuple[int, int], ...]]]]] = {"n": {}, "o": {}}
    for letter, key, rows in (("n", "c", npcs), ("o", "o", objects)):
        named = sorted({ident for record in quests.values() for ident in record.get(key, ())})  # type: ignore[union-attr]
        for ident in named:
            row = rows.get(ident)
            spots = _zone_places(row.points) if row is not None else []
            if spots:
                places[letter][ident] = spots
            else:
                left["creatureUnplaced" if letter == "n" else "objectUnplaced"] += 1
    return Targets(quests, places, dict(left))


def pack_targets(targets: Targets) -> dict[str, object]:
    """The `ot` value: { legend = { q, n, o, xy }, q, n, o }, each record one string in the file's own
    packed format (segments joined by SEPARATOR, a key letter then fixed width numbers; a zone segment
    the zone then each point's x and y, legend.xy digits each). Widths from the data; nothing signed."""
    largest: dict[str, dict[str, int]] = {letter: {} for letter in TARGET_TABLES}
    tenths = [0]

    def note(letter: str, key: str, value: int) -> None:
        if value < 0:
            raise OpenSourcesError(f"a negative number in the objective targets' {letter}.{key}")
        largest[letter][key] = max(largest[letter].get(key, 0), value)

    for record in targets.quests.values():
        for key in ("c", "o"):
            for value in record.get(key, ()):  # type: ignore[union-attr]
                note("q", key, value)
        for zone, points in record.get("a", ()):  # type: ignore[union-attr]
            note("q", "a", zone)
            for x, y in points:
                tenths.extend((x, y))
    for letter in ("n", "o"):
        for spots in targets.places[letter].values():
            for zone, points in spots:
                note(letter, "s", zone)
                for x, y in points:
                    tenths.extend((x, y))
    if min(tenths) < 0:
        raise OpenSourcesError("a point below zero in the objective targets")
    legend: dict[str, object] = {
        letter: {key: _digits(top) for key, top in sorted(largest[letter].items())}
        for letter in TARGET_TABLES
    }
    legend[XY] = _digits(max(tenths))
    xy = int(legend[XY])  # type: ignore[call-overload]

    def zone_segment(letter: str, key: str, zone: int, points: Iterable[tuple[int, int]]) -> str:
        width = legend[letter][key]  # type: ignore[index]
        return key + pack_int(zone, width) + "".join(pack_int(x, xy) + pack_int(y, xy) for x, y in points)

    value: dict[str, object] = {"legend": legend, "q": {}, "n": {}, "o": {}}
    for quest, record in sorted(targets.quests.items()):
        segments = []
        for key in ("c", "o"):
            if key in record:
                width = legend["q"][key]  # type: ignore[index]
                segments.append(key + "".join(pack_int(ident, width) for ident in record[key]))  # type: ignore[union-attr]
        for zone, points in record.get("a", ()):  # type: ignore[union-attr]
            segments.append(zone_segment("q", "a", zone, points))
        value["q"][quest] = SEPARATOR.join(segments)  # type: ignore[index]
    for letter in ("n", "o"):
        for ident, spots in sorted(targets.places[letter].items()):
            value[letter][ident] = SEPARATOR.join(  # type: ignore[index]
                zone_segment(letter, "s", zone, points) for zone, points in spots
            )
    return value


def unpack_target_record(letter: str, text: str, value: Mapping) -> dict[str, object]:
    """The inverse of pack_targets for one record, for the tests and as the reference the addon's reader
    follows: {"c": [ids], "o": [ids], "a": [(zone, ((x, y), ...))]} or {"s": [(zone, ((x, y),) or ())]}."""
    legend = value["legend"]
    widths, xy = legend[letter], legend[XY]
    out: dict[str, object] = {}
    for segment in text.split(SEPARATOR):
        key, body = segment[0], segment[1:]
        if key not in widths or key not in TARGET_KEYS[letter]:
            raise OpenSourcesError(f"{key!r} is not a key of the objective targets' {letter}")
        width = widths[key]
        if key in TARGET_ZONE_KEYS[letter]:
            zone, rest = unpack_int(body[:width]), body[width:]
            if len(body) < width or len(rest) % (2 * xy):
                raise OpenSourcesError("an objective target zone segment of the wrong length")
            points = tuple(
                (unpack_int(rest[at : at + xy]), unpack_int(rest[at + xy : at + 2 * xy]))
                for at in range(0, len(rest), 2 * xy)
            )
            out.setdefault(key, []).append((zone, points))  # type: ignore[union-attr]
        else:
            if not body or len(body) % width:
                raise OpenSourcesError("an objective target segment of the wrong length")
            out[key] = [unpack_int(body[at : at + width]) for at in range(0, len(body), width)]
    return out


def check_targets(value: object) -> None:
    """Brief Q41, the objective targets' own guard: { legend = { q, n, o, xy }, q, n, o } and nothing else,
    each legend naming only its table's keys with whole widths, every id a whole number above 0, every
    record the packed alphabet only and only its table's keys, and each record reading back whole."""
    if not isinstance(value, Mapping) or set(value) != {"legend", *TARGET_TABLES}:
        raise GuardError(f"{OBJECTIVE_TARGETS_FIELD} holds only legend, q, n and o")
    legend = value["legend"]
    if not isinstance(legend, Mapping) or set(legend) - {*TARGET_TABLES, XY} or XY not in legend:
        raise GuardError(f"the legend of {OBJECTIVE_TARGETS_FIELD} names a table it does not hold")
    widths_ok = isinstance(legend[XY], int) and not isinstance(legend[XY], bool) and legend[XY] >= 1
    for letter in TARGET_TABLES:
        widths = legend.get(letter, {})
        if not isinstance(widths, Mapping) or set(widths) - set(TARGET_KEYS[letter]):
            raise GuardError(f"the legend of {OBJECTIVE_TARGETS_FIELD}.{letter} names a key outside its list")
        widths_ok = widths_ok and all(
            isinstance(width, int) and not isinstance(width, bool) and width >= 1 for width in widths.values()
        )
    if not widths_ok:
        raise GuardError(f"the legend of {OBJECTIVE_TARGETS_FIELD} holds a width that is not a whole number")
    for letter in TARGET_TABLES:
        records = value[letter]
        if not isinstance(records, Mapping):
            raise GuardError(f"{OBJECTIVE_TARGETS_FIELD}.{letter} is not id to packed string")
        for ident, text in records.items():
            if (
                not isinstance(ident, int)
                or isinstance(ident, bool)
                or ident < 1
                or not isinstance(text, str)
            ):
                raise GuardError(
                    f"{OBJECTIVE_TARGETS_FIELD}.{letter} holds a record that is not id to packed string"
                )
            if not _RECORD.match(text):
                raise GuardError(
                    f"{OBJECTIVE_TARGETS_FIELD}.{letter}[{ident}] holds a byte outside the packed alphabet"
                )
            if {segment[:1] for segment in text.split(SEPARATOR)} - set(TARGET_KEYS[letter]):
                raise GuardError(f"{OBJECTIVE_TARGETS_FIELD}.{letter}[{ident}] holds a key outside its list")
            try:
                record = unpack_target_record(letter, text, value)
            except (OpenSourcesError, KeyError) as exc:
                raise GuardError(f"{OBJECTIVE_TARGETS_FIELD}.{letter}[{ident}] does not read back") from exc
            if any(ident_ <= 0 for key in ("c", "o") for ident_ in record.get(key, ())):  # type: ignore[union-attr]
                raise GuardError(f"{OBJECTIVE_TARGETS_FIELD}.{letter}[{ident}] names an id below 1")


def creature_names(composed: Composed, targets: Targets) -> tuple[dict[int, str], dict[str, int]]:
    """Brief Q41, the owner's "Take" of 2026-11-10 (QuestieDB's creature names for the objective targets
    nothing of ours names): the upstream's English name of each creature a quest's objectives name (the
    targets' `c`), whichever layer stated it, held to the rule an object's name is (object_name_fault);
    and how many have none, by why. Names alone: no title (subName) or other text. The file's own targets
    choose, so it stays a pure function of the pin: whether a name of ours stands first is the addon's
    order (its namer is asked last), never this writer's."""
    named = sorted({ident for record in targets.quests.values() for ident in record.get("c", ())})  # type: ignore[attr-defined]
    names: dict[int, str] = {}
    left: Counter[str] = Counter()
    for creature in named:
        row = composed.rows["Npc"].get(creature)
        text = row.texts.get("name", "") if row is not None else ""
        fault = object_name_fault(text)
        if fault is None:
            names[creature] = text
        else:
            left[fault] += 1
    return names, dict(left)


def select_facts(composed: Composed, layer_set: str) -> Selection:
    """The facts whose first origin is in the layer set, under the key set (KEYS). The rules are
    QZ0's (research-questie/scripts/keyset.py, A_layers), with its one slip mended: an objective
    item whose upstream entry carries its text is kept like one that does not."""
    if layer_set not in LAYER_SETS:
        raise OpenSourcesError(f"{layer_set!r} is not a layer set ({', '.join(sorted(LAYER_SETS))})")
    allowed = layer_bits(LAYER_SETS[layer_set])
    origins: Counter[str] = Counter()
    left_out: Counter[str] = Counter()

    def ok(mask: int) -> bool:
        if mask <= 0:
            left_out["noOrigin"] += 1
            return False
        return bool((mask & -mask) & allowed)

    def counted(mask: int) -> None:
        origins[first_origin(mask) or "none"] += 1

    def take(mask: int) -> bool:
        """ok, and counted by first origin: for a value that is kept as soon as it passes."""
        if ok(mask):
            counted(mask)
            return True
        return False

    def origin(mask: int) -> str:
        return first_origin(mask) or "none"

    records: dict[str, dict[int, dict[str, object]]] = {table: {} for table, _entity in TABLES}
    facts: set[tuple] = set()
    fact_layers: dict[tuple, str] = {}
    required_skills: dict[int, tuple[int, int]] = {}

    def spawns(row: Row) -> tuple[list[tuple[int, tuple[tuple[int, int], ...]]], str]:
        by_zone: dict[int, list[tuple[int, int]]] = {}
        lowest = len(LAYERS)
        for zone, x, y, mask in row.points:
            if x >= 0 and take(mask):
                by_zone.setdefault(zone, []).append((_tenths(x), _tenths(y)))
                lowest = min(lowest, (mask & -mask).bit_length() - 1)
        placed = [(zone, tuple(by_zone[zone])) for zone in sorted(by_zone)]
        return placed, (LAYERS[lowest] if placed else "none")

    for item, row in sorted(composed.rows["Item"].items()):
        record: dict[str, object] = {}
        layers: dict[str, object] = {}
        for key, name in ITEM_LISTS:
            elems = row.lists.get(name, [])
            kept = [(value, mask) for value, mask in elems if ok(mask)]
            if name == "npcDrops" and len(elems) > MASS_DROPPERS:
                left_out["massDropFacts"] += len(kept)
                kept = []
            for _value, mask in kept:
                counted(mask)
            if kept:
                pairs = sorted((int(value), origin(mask)) for value, mask in kept)
                record[key] = [value for value, _origin in pairs]
                layers[key] = [where for _value, where in pairs]
        start = row.scalars.get("startQuest")
        if start and start[0] and take(start[1]):
            record["s"] = int(start[0])
            layers["s"] = origin(start[1])
        _keep(records["i"], facts, fact_layers, "i", item, record, layers)

    for quest, row in sorted(composed.rows["Quest"].items()):
        record = {}
        layers = {}
        for key, name, group in QUEST_GROUPS:
            kept = [(int(value), mask) for value, mask in row.groups.get((name, group), []) if take(mask)]
            if kept:
                record[key] = [value for value, _mask in kept]
                layers[key] = [origin(mask) for _value, mask in kept]
        for key, name in QUEST_SCALARS:
            held = row.scalars.get(name)
            if held and held[0] and take(held[1]):
                record[key] = int(held[0])
                layers[key] = origin(held[1])
        prior = [
            (int(value), mask)
            for name in ("preQuestSingle", "preQuestGroup")
            for value, mask in row.lists.get(name, [])
            if take(mask)
        ]
        if prior:
            record["P"] = [value for value, _mask in prior]
            layers["P"] = [origin(mask) for _value, mask in prior]
        # Brief ST1: the repeatable bit of the quest's special flags, where it stands, by first origin.
        flags = row.scalars.get("specialFlags")
        if flags and int(flags[0]) & QUEST_FLAGS_KEPT and take(flags[1]):
            record["f"] = int(flags[0]) & QUEST_FLAGS_KEPT
            layers["f"] = origin(flags[1])
        _keep(records["q"], facts, fact_layers, "q", quest, record, layers)
        # Brief RS1: the skill line and rank the quest asks for, a key of its own beside the records.
        skill = row.pairs.get("requiredSkill")
        if skill and take(skill[2]):
            pair = (int(skill[0]), int(skill[1]))
            required_skills[quest] = pair
            fact = ("q", quest, REQUIRED_SKILLS_FIELD, pair)
            facts.add(fact)
            fact_layers[fact] = origin(skill[2])

    for npc, row in sorted(composed.rows["Npc"].items()):
        record = {}
        layers = {}
        placed, where = spawns(row)
        if placed:
            record["s"] = placed
            layers["s"] = where
        flags = row.scalars.get("npcFlags")
        if flags and int(flags[0]) & NPC_FLAGS_KEPT and take(flags[1]):
            record["f"] = int(flags[0]) & NPC_FLAGS_KEPT
            layers["f"] = origin(flags[1])
        for key, name in NPC_SCALARS:
            held = row.scalars.get(name)
            if held and held[0] and take(held[1]):
                record[key] = int(held[0])
                layers[key] = origin(held[1])
        _keep(records["n"], facts, fact_layers, "n", npc, record, layers)

    for obj, row in sorted(composed.rows["Object"].items()):
        record = {}
        layers = {}
        placed, where = spawns(row)
        if placed:
            record["s"] = placed
            layers["s"] = where
        held = row.scalars.get("zoneID")
        if held and held[0] and take(held[1]):
            record["z"] = int(held[0])
            layers["z"] = origin(held[1])
        _keep(records["o"], facts, fact_layers, "o", obj, record, layers)

    targets = objective_targets(composed)
    named_objects = {ident for record in targets.quests.values() for ident in record.get("o", ())}  # type: ignore[attr-defined]
    names, names_left = object_names(composed, records, named_objects)
    creatures_named, creatures_left = creature_names(composed, targets)
    return Selection(
        layer_set,
        records,
        frozenset(facts),
        dict(origins),
        dict(left_out),
        fact_layers,
        object_names=names,
        names_left_out=names_left,
        required_skills=required_skills,
        targets=targets,
        creature_names=creatures_named,
        creature_names_left_out=creatures_left,
    )


def _keep(
    table: dict[int, dict[str, object]],
    facts: set[tuple],
    fact_layers: dict[tuple, str],
    letter: str,
    ident: int,
    record: dict,
    layers: Mapping[str, object],
) -> None:
    if not record:
        return
    ordered = {key: record[key] for key in KEYS[letter] if key in record}
    table[ident] = ordered

    def note(fact: tuple, where: str) -> None:
        facts.add(fact)
        held = fact_layers.get(fact)
        if held is None or _layer_rank(where) < _layer_rank(held):
            fact_layers[fact] = where

    for key, value in ordered.items():
        where = layers.get(key, "none")
        if letter in SPAWN_TABLES and key == "s":
            note((letter, ident, key, tuple(value)), str(where))
        elif isinstance(value, list):
            for entry, entry_where in zip(value, where, strict=True):  # type: ignore[arg-type]
                note((letter, ident, key, entry), entry_where)
        else:
            note((letter, ident, key, value), str(where))


def _layer_rank(name: str) -> int:
    return LAYERS.index(name) if name in LAYERS else len(LAYERS)


def plain_text(selection: Selection) -> str:
    """The selection as QZ0's candidate files wrote it (one decimal string per record), for the size
    comparison and the regression check against QZ0's A_layers.lua. Never shipped."""
    lines = ["return {"]
    for letter, _entity in TABLES:
        lines.append(f"{letter}={{")
        for ident, record in sorted(selection.records[letter].items()):
            parts = []
            for key, value in record.items():
                if letter in SPAWN_TABLES and key == "s":
                    zones = [
                        f"{zone}:" + ",".join(f"{x / 10:g}/{y / 10:g}" for x, y in points)
                        for zone, points in value  # type: ignore[union-attr]
                    ]
                    parts.append("s" + "|".join(zones))
                elif isinstance(value, list):
                    parts.append(key + ",".join(str(entry) for entry in value))
                else:
                    parts.append(f"{key}{value}")
            lines.append(f'[{ident}]="{";".join(parts)}",')
        lines.append("},")
    lines.append("}")
    return "\n".join(lines) + "\n"


# ----- the packed format ------------------------------------------------------------------------
#
# Each record is ONE string of segments joined by SEPARATOR ("!", byte 33, outside the alphabet).
# A segment is its key (one letter, KEYS) then fixed width numbers in EraSources' base 91 alphabet
# (bytes 35 to 126 without 92, most significant digit first; era_sources.pack_int): a list key one
# number per id, a scalar key one number, a spawn list (s on n and o) one segment per zone, the zone
# id then each point as x then y in tenths of a map percent. `legend[table][key]` is the width of a
# key's numbers (for s, of its zone id) and `legend.xy` the width of a coordinate. A key in
# `signed[table]` holds zigzag numbers (v >= 0 is 2v, v < 0 is -2v - 1): a quest level of -1 and
# the upstream's negative prior quest ids. Widths and the signed keys come from the data, so the
# addon reads them from the file rather than assuming them.
SEPARATOR = "!"
XY = "xy"
# Brief QZ6: the file carries its own pin, so the addon reads the upstream commit and the layer set off
# the loaded table (its debug line, its spec against the stamp line) and a re-pin needs no step in the
# addon. Both are the build's own inputs, so the file stays a pure function of the pin and the layer set.
PIN_FIELD = "u"
LAYERS_FIELD = "L"
# Brief FFP, the one key added to this allow list since QZ6: `on`, object id -> the upstream's English
# name, so "Object 423901" reads as its container. The owner, 2026-11-05, on his item 465 (QZ11 "Seems
# fine except container is not named"): "A add in next release", approving the extra key on this list
# (item 466). Objects alone: no other name, and no text of any other kind.
OBJECT_NAMES_FIELD = "on"
# Brief RS1, the one key added since FFP: `rs`, quest id -> { skill line, rank }, the upstream's
# requiredSkill (its inherited corrections and its Forever fixes), { 0, 0 } where it took the pair away.
# The owner, 2026-11-09, on his item 593: "yes" to the two required skill fields (this one and
# EraSources.lua's `rs`), approving the extra key on this list. Numbers alone.
REQUIRED_SKILLS_FIELD = "rs"
# Brief Q41, the one key added since RS1: `ot`, the objective targets (objective_targets): what each
# quest's objectives name, a creature, an object or the area its triggerEnd completes in, and where each
# named creature and object stands, from every layer. The owner, 2026-11-10, on Lost in Battle (4921):
# "the location of the wife in this quest (questie has the location) I feel like we could add it too",
# his go to use the upstream's objective targets. Numbers alone, under its own guard (check_targets).
OBJECTIVE_TARGETS_FIELD = "ot"
# Brief Q41, the one key added beside `ot`: `cn`, creature id -> the upstream's English name, for the
# creatures a quest's objectives name (creature_names). The owner, 2026-11-10: "Take" (QuestieDB's
# creature names for the objective targets nothing of ours names, 117 at the pin), approving the key.
# Creatures an objective names alone, names alone: no title, no other text.
CREATURE_NAMES_FIELD = "cn"
TOP_FIELDS = frozenset(
    {
        *("v", PIN_FIELD, LAYERS_FIELD, "legend", "signed", "i", "q", "n", "o"),
        *(OBJECT_NAMES_FIELD, REQUIRED_SKILLS_FIELD, OBJECTIVE_TARGETS_FIELD, CREATURE_NAMES_FIELD),
    }
)
# A commit id as the pin states one (Pin's own check): 40 lower case letters and digits.
_COMMIT = re.compile(r"^[0-9a-z]{40}$")


def _digits(largest: int) -> int:
    digits = 1
    while PACK_BASE**digits <= largest:
        digits += 1
    return digits


def zigzag(value: int) -> int:
    return 2 * value if value >= 0 else -2 * value - 1


def unzigzag(value: int) -> int:
    return value // 2 if value % 2 == 0 else -(value + 1) // 2


def _values(letter: str, key: str, value: object) -> list[int]:
    if letter in SPAWN_TABLES and key == "s":
        return [zone for zone, _points in value]  # type: ignore[union-attr]
    if isinstance(value, list):
        return list(value)
    return [int(value)]  # type: ignore[arg-type]


def legend_of(selection: Selection) -> tuple[dict, dict]:
    """(legend, signed): each key's width from its largest value, the signed keys from any value
    below zero."""
    legend: dict[str, object] = {}
    signed: dict[str, dict[str, int]] = {}
    tenths = [0]
    for letter, _entity in TABLES:
        largest: dict[str, int] = {}
        negative: set[str] = set()
        for record in selection.records[letter].values():
            for key, value in record.items():
                numbers = _values(letter, key, value)
                if any(number < 0 for number in numbers):
                    negative.add(key)
                largest[key] = max([largest.get(key, 0), *(abs(number) for number in numbers)])
                if letter in SPAWN_TABLES and key == "s":
                    for zone, points in value:  # type: ignore[union-attr]
                        for x, y in points:
                            if x < 0 or y < 0:
                                raise OpenSourcesError(f"a spawn point below zero on {letter} in zone {zone}")
                            tenths.extend((x, y))
        if negative:
            signed[letter] = {key: 1 for key in sorted(negative)}
        widths = {}
        for key, top in sorted(largest.items()):
            # A signed key's largest number once zigzagged is at most 2 * |v| + 1.
            widths[key] = _digits(2 * top + 1 if key in negative else top)
        legend[letter] = widths
    legend[XY] = _digits(max(tenths))
    return legend, signed


def pack_record(letter: str, record: Mapping[str, object], legend: Mapping, signed: Mapping) -> str:
    widths = legend[letter]
    zig = signed.get(letter, {})
    segments: list[str] = []
    for key, value in record.items():
        width = widths[key]

        def enc(number: int, key: str = key, width: int = width) -> str:
            return pack_int(zigzag(number) if key in zig else number, width)

        if letter in SPAWN_TABLES and key == "s":
            for zone, points in value:  # type: ignore[union-attr]
                coords = "".join(pack_int(x, legend[XY]) + pack_int(y, legend[XY]) for x, y in points)
                segments.append(key + enc(zone) + coords)
        elif isinstance(value, list):
            segments.append(key + "".join(enc(number) for number in value))
        else:
            segments.append(key + enc(int(value)))  # type: ignore[arg-type]
    return SEPARATOR.join(segments)


def unpack_record(letter: str, text: str, legend: Mapping, signed: Mapping) -> dict[str, object]:
    """The inverse of pack_record, for the tests and as the reference the addon's reader follows."""
    widths = legend[letter]
    zig = signed.get(letter, {})
    out: dict[str, object] = {}

    def dec(chunk: str, key: str) -> int:
        number = unpack_int(chunk)
        return unzigzag(number) if key in zig else number

    for segment in text.split(SEPARATOR):
        key, body = segment[0], segment[1:]
        if key not in widths:
            raise OpenSourcesError(f"{key!r} is not a key of {letter}")
        width = widths[key]
        if letter in SPAWN_TABLES and key == "s":
            step = 2 * legend[XY]
            zone, rest = dec(body[:width], key), body[width:]
            if len(rest) % step:
                raise OpenSourcesError("a spawn segment of the wrong length")
            points = tuple(
                (unpack_int(rest[at : at + legend[XY]]), unpack_int(rest[at + legend[XY] : at + step]))
                for at in range(0, len(rest), step)
            )
            out.setdefault("s", []).append((zone, points))  # type: ignore[union-attr]
        else:
            if not body or len(body) % width:
                raise OpenSourcesError("a segment of the wrong length")
            numbers = [dec(body[at : at + width], key) for at in range(0, len(body), width)]
            out[key] = numbers if key in LIST_KEYS[letter] else numbers[0]
    return out


def pack_selection(
    selection: Selection, *, commit: str | None = None, layer_set: str | None = None
) -> dict[str, object]:
    """The module's value: { v, u, L, legend, signed, i, q, n, o, on, rs, ot }; u (the upstream commit) and
    L (the layer set) where given, which `build` always gives (brief QZ6); on the object names (brief FFP);
    rs the quests' required skills (brief RS1), each { skill line, rank }; ot the objective targets
    (brief Q41, pack_targets)."""
    legend, signed = legend_of(selection)
    value: dict[str, object] = {"v": FORMAT_VERSION, "legend": legend, "signed": signed}
    if commit is not None:
        value[PIN_FIELD] = commit
    if layer_set is not None:
        value[LAYERS_FIELD] = layer_set
    for letter, _entity in TABLES:
        value[letter] = {
            ident: pack_record(letter, record, legend, signed)
            for ident, record in sorted(selection.records[letter].items())
        }
    value[OBJECT_NAMES_FIELD] = dict(sorted(selection.object_names.items()))
    value[REQUIRED_SKILLS_FIELD] = {
        quest: [skill, rank] for quest, (skill, rank) in sorted(selection.required_skills.items())
    }
    value[OBJECTIVE_TARGETS_FIELD] = pack_targets(selection.targets or Targets({}, {"n": {}, "o": {}}, {}))
    value[CREATURE_NAMES_FIELD] = dict(sorted(selection.creature_names.items()))
    return value


# The record bytes: the alphabet and the separator, nothing else.
_RECORD = re.compile(r"^[#-\[\]-~!]+$")


def check_value(value: Mapping) -> None:
    """The allow list: the top keys, each table's keys, and records of alphabet bytes only. A GPL
    writer checks its value before any text is made (brief GA1's rule)."""
    if not isinstance(value, Mapping) or set(value) - TOP_FIELDS:
        raise GuardError(f"OpenSources.lua holds only {sorted(TOP_FIELDS)}")
    if value.get("v") != FORMAT_VERSION:
        raise GuardError("OpenSources.lua's format version is not this writer's")
    # Brief QZ6: the pin fields hold a commit id and a layer set's name, never anything else.
    if PIN_FIELD in value and not (isinstance(value[PIN_FIELD], str) and _COMMIT.match(value[PIN_FIELD])):
        raise GuardError(f"OpenSources.lua's {PIN_FIELD} holds something other than a commit id")
    if LAYERS_FIELD in value and value[LAYERS_FIELD] not in LAYER_SETS:
        raise GuardError(f"OpenSources.lua's {LAYERS_FIELD} holds something other than a layer set")
    legend, signed = value.get("legend", {}), value.get("signed", {})
    if set(legend) - {letter for letter, _entity in TABLES} - {XY}:
        raise GuardError("the legend names a table this file does not hold")
    for letter, _entity in TABLES:
        keys = set(KEYS[letter])
        if set(legend.get(letter, {})) - keys or set(signed.get(letter, {})) - keys:
            raise GuardError(f"the legend of {letter} names a key outside the allow list")
        for ident, text in (value.get(letter) or {}).items():
            if not isinstance(ident, int) or isinstance(ident, bool) or not isinstance(text, str):
                raise GuardError(f"{letter} holds a record that is not id to packed string")
            if not _RECORD.match(text):
                raise GuardError(f"{letter}[{ident}] holds a byte outside the packed alphabet")
            if {segment[0] for segment in text.split(SEPARATOR)} - keys:
                raise GuardError(f"{letter}[{ident}] holds a key outside the allow list")
    # Brief FFP: object id -> a name that passes the rule the selection applied, nothing else.
    for ident, name in (value.get(OBJECT_NAMES_FIELD) or {}).items():
        if not isinstance(ident, int) or isinstance(ident, bool) or ident < 1 or not isinstance(name, str):
            raise GuardError(f"{OBJECT_NAMES_FIELD} holds a row that is not object id to name")
        if object_name_fault(name) is not None:
            raise GuardError(f"{OBJECT_NAMES_FIELD}[{ident}] holds something other than a plain name")
    # Brief RS1: quest id -> { skill line, rank }, two whole numbers neither below 0, and a removal is
    # { 0, 0 }: nothing else.
    skills = value.get(REQUIRED_SKILLS_FIELD) or {}
    if not isinstance(skills, Mapping):
        raise GuardError(f"{REQUIRED_SKILLS_FIELD} is not quest id to a pair")
    for ident, pair in skills.items():
        if not isinstance(ident, int) or isinstance(ident, bool) or ident < 1:
            raise GuardError(f"{REQUIRED_SKILLS_FIELD} holds a row that is not quest id to a pair")
        if (
            not isinstance(pair, list | tuple)
            or len(pair) != 2
            or not all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in pair)
            or (pair[0] == 0 and pair[1] != 0)
        ):
            raise GuardError(
                f"{REQUIRED_SKILLS_FIELD}[{ident}] holds something other than a skill line and rank"
            )
    # Brief Q41: the objective targets, under their own guard.
    if OBJECTIVE_TARGETS_FIELD in value:
        check_targets(value[OBJECTIVE_TARGETS_FIELD])
    # Brief Q41 (the owner's "Take"): creature id -> a name that passes the object names' rule, and only
    # for a creature the objective targets name.
    creatures = value.get(CREATURE_NAMES_FIELD) or {}
    if not isinstance(creatures, Mapping):
        raise GuardError(f"{CREATURE_NAMES_FIELD} is not creature id to name")
    targeted = _targeted_creatures(value.get(OBJECTIVE_TARGETS_FIELD))
    for ident, name in creatures.items():
        if not isinstance(ident, int) or isinstance(ident, bool) or ident < 1 or not isinstance(name, str):
            raise GuardError(f"{CREATURE_NAMES_FIELD} holds a row that is not creature id to name")
        if object_name_fault(name) is not None:
            raise GuardError(f"{CREATURE_NAMES_FIELD}[{ident}] holds something other than a plain name")
        if ident not in targeted:
            raise GuardError(f"{CREATURE_NAMES_FIELD}[{ident}] names a creature no objective names")


def _targeted_creatures(targets: object) -> set[int]:
    """The creatures the objective targets' quest records name (their `c`), or none."""
    out: set[int] = set()
    if not isinstance(targets, Mapping) or not isinstance(targets.get("q"), Mapping):
        return out
    for text in targets["q"].values():
        try:
            out.update(unpack_target_record("q", text, targets).get("c", ()))  # type: ignore[arg-type]
        except (OpenSourcesError, KeyError, TypeError):
            continue
    return out


# ----- the build --------------------------------------------------------------------------------

_BUILT = object()


class OpenSources:
    """What `build` made from one checked UpstreamTree: the module's value, the layer set, the
    commit, the counts and the plain (QZ0 decimal) text, and for a re-pin's change report the
    composed levels (`levels`: {"q": {quest: level}, "n": {creature: level}}, never written). The
    writer takes this and the stamps and nothing else; only `build` can make one."""

    __slots__ = ("value", "layer_set", "commit", "counts", "plain", "stats", "selection", "levels")

    def __init__(
        self,
        token: object,
        *,
        value: dict,
        layer_set: str,
        commit: str,
        counts: dict,
        plain: str,
        stats: tuple[LayerStat, ...],
        selection: Selection,
        levels: dict[str, dict[int, int]] | None = None,
    ):
        if token is not _BUILT:
            raise TypeError("an OpenSources table is made by open_sources.build alone")
        self.value = value
        self.layer_set = layer_set
        self.commit = commit
        self.counts = counts
        self.plain = plain
        self.stats = stats
        self.selection = selection
        self.levels = levels or {"q": {}, "n": {}}


def target_counts(targets: Targets | None) -> dict[str, int]:
    """Brief Q41: how many quests the objective targets hold, and their creatures, objects, areas and the
    creatures and objects they place."""
    quests = targets.quests if targets else {}
    places = targets.places if targets else {"n": {}, "o": {}}
    return {
        "targetQuests": len(quests),
        "targetCreatures": sum(len(record.get("c", ())) for record in quests.values()),  # type: ignore[arg-type]
        "targetObjects": sum(len(record.get("o", ())) for record in quests.values()),  # type: ignore[arg-type]
        "targetAreas": sum(1 for record in quests.values() if "a" in record),
        "targetPlaces": len(places["n"]) + len(places["o"]),
    }


def composed_levels(composed: Composed) -> dict[str, dict[int, int]]:
    """Each composed quest's level (its level, else its minimum level) and creature's (its minimum
    level, else its maximum), whatever layer stated them: numbers for a re-pin's level bands."""
    levels: dict[str, dict[int, int]] = {"q": {}, "n": {}}
    for letter, entity, names in (
        ("q", "Quest", ("questLevel", "requiredLevel")),
        ("n", "Npc", ("minLevel", "maxLevel")),
    ):
        for ident, row in composed.rows[entity].items():
            for name in names:
                held = row.scalars.get(name)
                if held and isinstance(held[0], int) and held[0] > 0:
                    levels[letter][ident] = held[0]
                    break
    return levels


def build(tree: UpstreamTree, *, layer_set: str, lua: str) -> OpenSources:
    """The whole stage: check the top level shape of every file the layer set loads (check_shapes),
    compose the pinned tree with those layers loaded (the base always), select by first origin,
    pack. Reads nothing but the tree."""
    if not isinstance(tree, UpstreamTree):
        raise TypeError(f"OpenSources.lua is built from an UpstreamTree alone, not {type(tree).__name__}")
    if layer_set not in LAYER_SETS:
        raise OpenSourcesError(f"{layer_set!r} is not a layer set ({', '.join(sorted(LAYER_SETS))})")
    leave_out = [name for name in LAYERS[1:] if name not in LAYER_SETS[layer_set]]
    check_shapes(tree, layers=[name for name in LAYERS if name not in leave_out])
    composed = compose(tree, leave_out=leave_out, lua=lua)
    selection = select_facts(composed, layer_set)
    value = pack_selection(selection, commit=tree.commit, layer_set=layer_set)
    check_value(value)
    plain = plain_text(selection)
    counts: dict[str, int] = {
        "items": len(selection.records["i"]),
        "quests": len(selection.records["q"]),
        "npcs": len(selection.records["n"]),
        "objects": len(selection.records["o"]),
        "facts": len(selection.facts),
        "plainBytes": len(plain.encode("utf-8")),
        "objectNames": len(selection.object_names),
        "objectNamesLeftOut": sum(selection.names_left_out.values()),
        "requiredSkills": len(selection.required_skills),
        "requiredSkillsRemoved": sum(1 for skill, _rank in selection.required_skills.values() if skill == 0),
        **target_counts(selection.targets),
        "creatureNames": len(selection.creature_names),
        "creatureNamesLeftOut": sum(selection.creature_names_left_out.values()),
    }
    return OpenSources(
        _BUILT,
        value=value,
        layer_set=layer_set,
        commit=tree.commit,
        counts=counts,
        plain=plain,
        stats=composed.stats,
        selection=selection,
        levels=composed_levels(composed),
    )


# ----- the writer -------------------------------------------------------------------------------

_STAMP = re.compile(r"^[A-Za-z0-9_.:+\-]{1,64}$")

# The one credit, wherever this data is shown (the header; the addon's credit line, brief QZ3).
CREDIT = (
    f"Open source quest and world data for WoW Forever, derived from {UPSTREAM_NAME} "
    f"({UPSTREAM_REPOSITORY}), the Questie project's database, at commit {QUESTIEDB_COMMIT} "
    f"({QUESTIEDB_VERSION}). Ids and numbers, the names of the objects they name and of the creatures "
    "quest objectives name: which creature, "
    "object or item starts, ends or "
    "asks for a quest, a quest's levels, sides, classes, chain, required profession and whether it repeats, "
    "which creature "
    "or object drops "
    "an item, which creature sells it, which quest rewards it, which creature, object or area a quest's "
    "objectives name, and where creatures and objects "
    "stand (the upstream's own zone ids and map percentages). WoW Forever may differ; the addon "
    "shows these as predicted."
)

UPSTREAM_DECLARED = f"{UPSTREAM_NAME}, the database it derives from ({UPSTREAM_REPOSITORY})"
UPSTREAM_QUESTIEDB = (
    f"{UPSTREAM_NAME}: {UPSTREAM_REPOSITORY} at commit {QUESTIEDB_COMMIT} ({QUESTIEDB_VERSION}), GPL-3.0. "
    "Its LICENSE.md and gpl-3.0.md ship unchanged as third party notices."
)
# Their LICENSE.md, said truthfully: shipped whole beside the file, summarised here.
UPSTREAM_CAVEAT = (
    f"{UPSTREAM_NAME}'s LICENSE.md says: content it imported from Questie stays under Questie's own "
    "licensing; its historic contributions never had a licence and consent is not complete, so when "
    "in doubt that content is to be considered all rights reserved; the Questie team is alright with "
    "copying under GPL-3.0 but cannot promise every contributor is; and the GPL does not extend to "
    "the Questie name and logo."
)
UPSTREAM_LINEAGE = (
    f"Lineage: {UPSTREAM_NAME}'s Classic base derives from the CMaNGOS Classic content database "
    "(github.com/cmangos/classic-db), GPL-3.0, by the Questie project's own record."
)
MODIFICATION_NOTICE = (
    f"Modified: this file is a modified, reduced derivation of {UPSTREAM_NAME}, made by the ItemTree "
    "pipeline on the Generated date above. The changes: a selection (the layers and the key set "
    "this header names; of its text only the names of the objects these facts name and of the "
    "creatures quest objectives name: no other names, "
    "and no quest text, drop rates, waypoints, comments or addresses), a "
    "composition (the upstream's Forever correction layers applied over its base, in its own order) "
    "and a re-keying (each fact under the short keys above, packed)."
)
LICENCE_FILES = (
    "The licence text ships as LICENSES/GPL-3.0.txt, QuestieDB's LICENSE.md and gpl-3.0.md as "
    "LICENSES/questiedb-LICENSE.md and LICENSES/questiedb-gpl-3.0.md, and the CMaNGOS notice as "
    "LICENSES/cmangos-COPYRIGHT.md, beside this file in the ItemTree addon."
)

# The only addresses the file may hold: the Corresponding Source (with its scheme) and, in the
# credit lines, the two upstream repositories (without one).
ALLOWED_URLS = frozenset({CORRESPONDING_SOURCE_URL})
ALLOWED_HOSTS = frozenset({"github.com"})
_URL = re.compile(r"https?://[^\s\"'<>()]+")
_HOST = re.compile(
    r"\b(?:[a-z0-9-]+\.)+(?:com|net|org|dev|io|gg|wiki|tools|app|info|co|uk|de|fr|ru|cn|eu|us|xyz)\b",
    re.IGNORECASE,
)


def licence_lines() -> list[str]:
    """The licence part of the header, through the one GPL helper (era_sources.gpl_licence_lines)."""
    return gpl_licence_lines(
        what="This generated file",
        rest="The rest of ItemTree is all rights reserved.",
        source="the compiler, its composer, the pin and these notices",
        upstream=UPSTREAM_DECLARED,
        corresponding_source=CORRESPONDING_SOURCE_URL,
        upstream_lines=[UPSTREAM_QUESTIEDB, UPSTREAM_CAVEAT, UPSTREAM_LINEAGE, CMANGOS_COPYRIGHT],
        modification=MODIFICATION_NOTICE,
        licence_files=LICENCE_FILES,
    )


def check_stamp(name: str, value: object) -> str:
    """A stamp is a short identifier (an ISO time, a version), never data."""
    if not isinstance(value, str) or not _STAMP.match(value):
        raise OpenSourcesError(f"{name} must be a short identifier, not {value!r}")
    return value


def header_lines(table: OpenSources, *, generated: str, version: str) -> list[str]:
    """The whole header comment: the stamp, the shape, the format, the layers, the credit, the
    licence and the counts."""
    check_stamp("generated", generated)
    check_stamp("version", version)
    counts = table.counts
    legend = table.value["legend"]
    return [
        "ItemTree generated data. Do not edit.",
        f"Module: {MODULE_NAME} | Upstream: {table.commit} | Layers: {table.layer_set} | "
        f"Generated: {generated} | Pipeline: {version}",
        "A gap filler from one pinned open source quest database: the addon uses a fact here only "
        "where its own data and the Classic Era files state nothing of that kind. Ids and numbers, and "
        "the names of the objects they name and of the creatures quest objectives name. "
        "docs/open-sources.md in the pipeline is the contract.",
        f"{{ v = {FORMAT_VERSION}, {PIN_FIELD}, {LAYERS_FIELD}, legend, signed, i = {{ [itemId] = record }}, "
        "q = { [questId] = record }, n = { [creatureId] = record }, o = { [objectId] = record }, "
        f"{OBJECT_NAMES_FIELD} = {{ [objectId] = name }}, "
        f"{REQUIRED_SKILLS_FIELD} = {{ [questId] = {{ skill line, rank }} }}, "
        f"{OBJECTIVE_TARGETS_FIELD} = {{ legend, q = {{ [questId] = record }}, "
        "n = { [creatureId] = record }, o = { [objectId] = record } }, "
        f"{CREATURE_NAMES_FIELD} = {{ [creatureId] = name }} }}. v is "
        f"the format version; refuse any other. {PIN_FIELD} is the upstream commit and {LAYERS_FIELD} the "
        "layer set this file was built from, the stamp line's own.",
        f"record: segments joined by {SEPARATOR!r}; a segment is its key letter then fixed width numbers "
        "in the EraSources alphabet (base 91, bytes 35 to 126 without 92, most significant first): "
        "legend[table][key] digits per number (for s on n and o: the zone id, then each point as x "
        f"and y in tenths of a map percent, legend.{XY} digits each, {legend[XY]} here). A key in "
        "signed[table] holds zigzag numbers (2v for v >= 0, -2v - 1 below).",
        "i: d creatures that drop it, o objects that hold it, c items that contain it, v creatures "
        "that sell it, r quests that reward it, s the quest it starts. q: g G I creatures, objects "
        "and items that start it, e E creatures and objects that end it, n items it asks for, p the "
        "item it hands over, l level, m minimum level, x race mask (bits 32 and 33 are Forever's "
        "own races), k class mask, N next quest, P prior quests, f flags (repeatable 1). n: s spawns, f "
        "flags (vendor 4, "
        "trainer 16), l L levels, z zone id, a side (1 Alliance, 2 Horde, 3 both). o: s spawns, z "
        "zone id. Zone ids are the upstream's own area ids and points its own map percentages. "
        f"{OBJECT_NAMES_FIELD}: the upstream's English name of each object this file names (a row of o, "
        "an item's o, a quest's G and E); a missing name or a placeholder has no row here. "
        f"{REQUIRED_SKILLS_FIELD}: the skill a quest asks the player to have, {{ skill line, rank }} (the "
        "SkillLine id: 164 Blacksmithing, 171 Alchemy, 202 Engineering, ...), for the quests whose "
        "requiredSkill was first stated by a layer of this set; { 0, 0 } where a layer of this set took "
        "the pair away: the quest asks for no skill. "
        f"{OBJECTIVE_TARGETS_FIELD}: what each quest's objectives name, from every layer "
        "(the base among them: no Classic Era file names an objective's creature, object or "
        "area), its own legend and the same packed records: q c the creatures (a kill credit "
        "objective's one creature among them) and o the objects, in the upstream's objective "
        "order, a the area its triggerEnd completes in (the zone, then its points); n and o, "
        "each named creature and object the upstream places: s one segment per zone, the most "
        "spawns first, with its one point where the zone holds one spawn and none where it "
        f"holds more. {CREATURE_NAMES_FIELD}: the upstream's English name of each creature a quest's "
        "objectives name (ot's c), a missing name or a placeholder left out.",
        f"Layers: {table.layer_set}, {LAYER_WORDS[table.layer_set]}. A creature drop list longer than "
        f"{MASS_DROPPERS} is a world drop and is left out whole.",
        CREDIT,
        *licence_lines(),
        f"{counts['items']} items, {counts['quests']} quests, {counts['npcs']} creatures, "
        f"{counts['objects']} objects; {counts['facts']} facts; {counts['objectNames']} object names, "
        f"{counts['objectNamesLeftOut']} objects with none; {counts['requiredSkills']} required skills "
        f"({counts['requiredSkillsRemoved']} taken away); objective targets for {counts['targetQuests']} "
        f"quests ({counts['targetCreatures']} creatures, {counts['targetObjects']} objects, "
        f"{counts['targetAreas']} areas; {counts['targetPlaces']} placed); {counts['creatureNames']} "
        f"creature names, {counts['creatureNamesLeftOut']} target creatures with none.",
    ]


def check_addresses(text: str) -> None:
    """No address in the file but the Corresponding Source, and no host but the upstreams' (the
    header names github.com/... without a scheme). The records hold no letters but base 91 digits,
    and check_value holds the object names to object_name_fault, which refuses a host, so only the
    header is read for hosts."""
    for url in _URL.findall(text):
        if url.rstrip(".,;:") not in ALLOWED_URLS:
            raise GuardError("OpenSources.lua would hold an address the allow list does not")
    header = "".join(line for line in text.splitlines(keepends=True) if line.startswith("--"))
    for host in _HOST.findall(header):
        if host.lower() not in ALLOWED_HOSTS:
            raise GuardError("OpenSources.lua's header would name a host the allow list does not")


def module_text(table: OpenSources, *, generated: str, version: str, pretty: bool = False) -> str:
    """OpenSources.lua, whole: the header made here from the two stamps (each checked) and the self
    registering module. The value is checked first, so no key outside the allow list can be
    written, and the text after, so no address outside the allow list can. The compile's one way to
    write the file: nothing but the OpenSources `build` made and the stamps can reach it."""
    if not isinstance(table, OpenSources):
        raise TypeError(f"OpenSources.lua is written from the table build made, not {type(table).__name__}")
    check_value(table.value)
    # Brief QZ6: the file carries its own pin, the same as its stamp line's.
    if table.value.get(PIN_FIELD) != table.commit or table.value.get(LAYERS_FIELD) != table.layer_set:
        raise GuardError("OpenSources.lua's own pin fields must be its stamp line's commit and layer set")
    header = header_lines(table, generated=generated, version=version)
    text = lua_module(MODULE_NAME, header, lua_value(table.value, pretty=pretty, indent=1))
    check_addresses(text)
    return text


def summary_lines(table: OpenSources, text: str) -> list[str]:
    """What a build made, for the command line: counts, sizes, the left out and the origins."""
    raw = len(text.encode("utf-8"))
    selection = table.selection
    origin = ", ".join(f"{name} {selection.origins.get(name, 0)}" for name in LAYERS)
    left = ", ".join(f"{key} {count}" for key, count in sorted(selection.left_out.items())) or "none"
    nameless = (
        ", ".join(f"{count} {why}" for why, count in sorted(selection.names_left_out.items())) or "none"
    )
    return [
        f"open sources: {table.layer_set} at {table.commit[:12]}: {table.counts['facts']:,} facts; "
        f"{table.counts['items']:,} items, {table.counts['quests']:,} quests, "
        f"{table.counts['npcs']:,} creatures, {table.counts['objects']:,} objects",
        f"  bytes: {raw:,} packed (the file), {table.counts['plainBytes']:,} as plain decimal records",
        f"  object names: {table.counts['objectNames']:,}; none for {nameless}",
        f"  required skills: {table.counts['requiredSkills']:,} ({table.counts['requiredSkillsRemoved']:,} "
        "taken away)",
        f"  objective targets: {table.counts['targetQuests']:,} quests, {table.counts['targetCreatures']:,} "
        f"creatures, {table.counts['targetObjects']:,} objects, {table.counts['targetAreas']:,} areas; "
        f"{table.counts['targetPlaces']:,} placed; {table.counts['creatureNames']:,} creature names, "
        f"{table.counts['creatureNamesLeftOut']:,} with none",
        f"  kept values by first origin: {origin}",
        f"  left out: {left}",
    ]
