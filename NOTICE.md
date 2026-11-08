# Notice

This repository is the corresponding source for derived data that ships in a World of Warcraft
addon: ItemTree's `ItemTree_Data/Data/generated/OpenSources.lua`. That file holds data derived from
one pinned commit of QuestieDB alone, and is distributed under GPL-3.0. Nothing else of the addon is
in this repository.

## Upstream data

- **QuestieDB**, [Questie/QuestieDB](https://github.com/Questie/QuestieDB), at commit
  `4d31c10394b11bd133069ecf1662062cdf4d8691` (v1.0.12). It declares the GNU General Public License
  version 3, with the caveats its own `LICENSE.md` sets out (content imported from Questie stays
  under Questie's licensing; where in doubt its historic content is to be considered all rights
  reserved; the GPL does not extend to the Questie name and logo). Its `LICENSE.md` and `gpl-3.0.md`
  are vendored verbatim at `third_party/QuestieDB/`. Every fact in the derived file comes from it:
  which creature, object or item starts, ends or asks for a quest, a quest's levels, race and class
  masks and chain links, which creature or object drops an item, which creature sells it, which quest
  rewards it, creature and object spawn points (its own zone ids and map percentages), creature
  levels, flags and sides, and the names of the objects those facts name.
- **CMaNGOS Classic content database**, [cmangos/classic-db](https://github.com/cmangos/classic-db),
  the lineage of QuestieDB's Classic base by the Questie project's own record. Licensed under the
  GNU General Public License version 3. Its licence and its copyright notice are vendored verbatim at
  `third_party/cmangos-classic-db/LICENSE.md` and `third_party/cmangos-classic-db/COPYRIGHT.md`.

World of Warcraft content and materials are trademarks and copyrights of Blizzard or its
licensors (see CMaNGOS's `COPYRIGHT.md`). This repository is not affiliated with Blizzard
Entertainment, the Questie project or CMaNGOS.

## Corresponding source

Per GPL v3, the **corresponding source** for that derived data is this repository. The build
scripts are exactly these files:

- `itemtree_open_sources/open_sources.py`, the compiler of `OpenSources.lua`, with the pin
- `itemtree_open_sources/open_sources_compose.lua`, its sandboxed composer
- `itemtree_open_sources/era_sources.py`, the GPL header helper and the packing alphabet it uses
- `itemtree_open_sources/build_facts.py` and `itemtree_open_sources/test_rows.py`, which
  `era_sources.py` imports
- `itemtree_open_sources/luaout.py`, the writer that produces the .lua bytes

with the pinned input listed in `README.md`. The derived file is a modified, reduced derivation of
QuestieDB: a selection (the layers and the key set its header names; of its text only the names of
the objects these facts name: no other names, and no quest text, drop rates, waypoints, comments or
addresses), a composition (QuestieDB's Forever correction layers
applied over its base, in its own order) and a re-keying (each fact under short keys, packed), as
its own header and the compiler's docstrings describe. The upstream notices are vendored under
`third_party/`, and this repository is licensed under GPL-3.0 (`LICENSE`).
