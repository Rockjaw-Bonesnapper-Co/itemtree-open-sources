# itemtree-open-sources

This repository is the Corresponding Source, in the GPL-3.0 sense, for one generated file:

| file | ships in | what it is |
| --- | --- | --- |
| `OpenSources.lua` | the ItemTree addon's `ItemTree_Data` folder | quest, item, creature and object ids and numbers, and the names of the objects they name, for WoW Forever, from one pinned commit of QuestieDB |

`OpenSources.lua` holds data derived from the pinned commit of
[QuestieDB](https://github.com/Questie/QuestieDB) alone, so it is distributed under the GNU General
Public License version 3, the licence QuestieDB declares, and so is everything here (see `LICENSE`).
The addon itself is all rights reserved, and nothing else of it is in this repository. The addon uses
the file only as a gap filler: where its own data and its Classic Era files state nothing of a kind,
it may show a fact from this file, marked as predicted.

ItemTree is published at CurseForge and at Wago Addons. This repository is not affiliated with the
Questie project, CMaNGOS or Blizzard Entertainment, and it is not Questie: the GPL does not extend to
the Questie name and logo, which are the Questie project's.

## The credit

`OpenSources.lua` carries this paragraph, word for word, and so does everything that shows its data:

> Open source quest and world data for WoW Forever, derived from QuestieDB
> (github.com/Questie/QuestieDB), the Questie project's database, at commit
> 4d31c10394b11bd133069ecf1662062cdf4d8691 (v1.0.12). Ids and numbers, and the names of the objects
> they name: which creature, object or item starts, ends or asks for a quest, a quest's levels, sides, classes and chain, which creature
> or object drops an item, which creature sells it, which quest rewards it, and where creatures and
> objects stand (the upstream's own zone ids and map percentages). WoW Forever may differ; the addon
> shows these as predicted.

## The upstream's licence, as it stands

QuestieDB's `LICENSE.md` and `gpl-3.0.md` are vendored verbatim at `third_party/QuestieDB/` and ship
beside the file in the addon. Read them whole. In short, its `LICENSE.md` says that content it
imported from Questie stays under Questie's own licensing; that its historic contributions never had
a licence and consent from every contributor is not complete, so when in doubt that content is to be
considered all rights reserved; that the Questie team is alright with others copying under GPL-3.0
but cannot promise every contributor is; and that the GPL does not extend to the Questie name and
logo. QuestieDB's Classic base derives, by the Questie project's own record, from the CMaNGOS Classic
content database (GPL-3.0), whose notices are vendored at `third_party/cmangos-classic-db/`.

## What is here

| file | what it is |
| --- | --- |
| `itemtree_open_sources/open_sources.py` | the compiler of `OpenSources.lua`: the pin, reading the pinned files out of the commit's tarball or a checkout and checking their content hash, running the composer, the selection by layer, the packed format and the writer with its header |
| `itemtree_open_sources/open_sources_compose.lua` | the composer (Lua 5.4): loads every upstream file in a sandbox and applies the upstream's Forever layers over its base, remembering which layer first stated each fact, and writes the kept fields as numbers only |
| `itemtree_open_sources/era_sources.py` | carried because `open_sources.py` imports it: the one helper that writes a GPL licence line into a generated file (`gpl_declaration`, through `gpl_licence_lines`), the base 91 alphabet (`pack_int`) and the CMaNGOS notice. Its Classic Era compiler is not run for `OpenSources.lua`; it is the same file the ItemTree pipeline's other public repository, itemtree-era-sources, carries |
| `itemtree_open_sources/build_facts.py`, `test_rows.py` | carried because `era_sources.py` imports them; not run for `OpenSources.lua` |
| `itemtree_open_sources/luaout.py` | the writer: serialises the module's value and header into the .lua bytes |
| `NOTICE.md` | the upstream database, its licence and commit |
| `third_party/` | the upstream licence and copyright notices, verbatim |

The Python and Lua files are byte for byte copies of the ones in the ItemTree data pipeline, which a
sync script checks every time they are published. The pipeline's own tests fail if any file outside
the mirrored ones writes a GPL licence line, imports a module that is not mirrored, or names an input
of the pipeline's own.

Comments refer to `docs/open-sources.md` and `docs/licensing.md`. Those live in the private
pipeline and are not published here; the record shape they describe is restated, key by key, in the
header of the generated file itself.

## The pinned input

One commit of QuestieDB, fixed by the constants at the top of `open_sources.py` (`PIN`):

| what | value |
| --- | --- |
| repository | QuestieDB (GPL-3.0, with the caveats above) |
| commit | `4d31c10394b11bd133069ecf1662062cdf4d8691` (v1.0.12) |
| tarball | `https://github.com/Questie/QuestieDB/archive/4d31c10394b11bd133069ecf1662062cdf4d8691.tar.gz` |
| content hash | `93d6ee23f0ee126d9f037fc70c02e77611a5e5f83072a911892a046a20351091` |
| `LICENSE.md` | sha256 `d9937e385c401d234ef416b91f00290f8ea8e517f39ed4359aed99115770d8c9` |
| `gpl-3.0.md` | sha256 `cc5470feed66192387f06ae93aed0bd4fefae5a5fd7c1e54a4acf4ea64f1028b` |

The files read are not a list kept here: `open_sources.derive_plan` reads them out of QuestieDB's own
load lists at the commit, as text (its `QuestieDB.toc`, its `src/config.lua` with the correction
registry, and `src/corrections/manifest.lua`), and puts each file the Forever flavour loads in one
known class (a layer by its folder and name, an enum, meta or base file, or a known file that is
never composed); anything else stops the build. The content hash is the sha256 of one line per file
read (the three load lists and the files they name), sorted by path, each
`<path> <sha256 of its bytes>` and a newline. A tarball's own bytes are not pinned (a host may pack
the same commit differently); its files are. The compiler builds those exact bytes or nothing.

## How the file is built

Requirements: Python 3.12 and Lua 5.4 (`lua5.4` or `lua` on PATH).

1. Get the pinned files: download the tarball above, then
   `files, notices = open_sources.read_archive(data)` reads the three load lists, the files they name
   and the two notices out of it (nothing is extracted to disk), or `open_sources.read_tree(folder)`
   reads them from a checkout at the commit. `open_sources.tree_from_files(files, notices)` checks
   the content hash and the notices' hashes and returns an `UpstreamTree`, the one input the
   compiler takes.
2. `open_sources.build(tree, layer_set=open_sources.SHIPPED_LAYER_SET, lua=open_sources.find_lua())`
   reads each file's top level shape as text (anything new stops it), runs the composer over exactly
   those bytes and the plan (handed to it on stdin), keeps the facts whose first origin is in the
   layer set, and packs them.
3. `open_sources.module_text(table, generated=..., version=...)` writes the file: the header names
   the commit, the layer set, the format, the credit and the licence; the value carries the same
   commit and layer set as its own top level fields `u` and `L`; the value is checked against the
   key allow list and the text against the address allow list first.

## The layers and the layer set

The composer applies the upstream's Forever data in its own order: its base (`data/Forever`, the
Classic seed of CMaNGOS lineage), the inherited hand corrections, the generated item quest starts and
the generated delta base (both made by a site scraper upstream), the player trace extract, and the
hand written Forever corrections. Each fact keeps every layer that stated it while it stood; the
lowest is its first origin. The shipped layer set, `post-era`, keeps every fact whose first origin is
a layer above the base; `post-era-no-scraper` never loads the two scraper layers. The file's header
says which one it was built with.

## Sandbox

The upstream files are untrusted input. The composer loads each one as text only, into an
environment of its own that holds only the stand-ins that file needs: no `io`, `os`, `require`,
`dofile`, `loadfile`, `load`, `debug`, `package`, `string` methods (so no `string.dump`), `pcall` or
`setmetatable`. A count hook stops any call after 100 million instructions or past 2 GB of memory,
and any error ends the run. Only the projected numbers leave it.
