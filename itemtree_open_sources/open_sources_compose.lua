-- SPDX-License-Identifier: GPL-3.0-only
-- Copyright (c) 2026 Rockjaw Bonesnapper Co
-- Public home, the Corresponding Source of OpenSources.lua: https://github.com/Rockjaw-Bonesnapper-Co/itemtree-open-sources
--[[
The composer behind OpenSources.lua (brief QZ2). It applies the pinned upstream database's Forever
layers over its base, in that database's own load order, and remembers which layer stated each
fact, then writes the few fields the file keeps as numbers. open_sources.py runs it (compose());
nothing else should.

Lua 5.4 only (it checks _VERSION first): it relies on 64 bit integers (a race mask uses bits 32
and 33), integer division and the bitwise operators.

The upstream files are untrusted. Each one is loaded with load(text, name, "t", env): text only
(a binary chunk is refused), into an environment of its own that holds only the few stand-ins
that file needs (QuestieLoader, a table of icon kinds) and nothing of Lua's own: no io, os,
require, dofile, loadfile, load, debug, package, string, pcall, setmetatable or getmetatable.
While upstream code runs, the strings' shared metatable answers no method at all (so no
("").dump), and a count hook stops it after a fixed number of instructions or past a memory
ceiling. Any error, upstream or ours, ends the run with a non zero exit: it fails closed. The
text in the files is data, never instructions: nothing of it is printed but the numbers below.

Protocol (open_sources.compose writes stdin and reads stdout):
  arg[1]  the layers to leave out, comma separated, or "-" for none.
  stdin   the plan, then the files. The plan is "PLAN <n>" and n tab separated lines, which
          open_sources.derive_plan made from the upstream's own load lists:
            E <path>                                                an enum file, in load order
            M <entity> <path>                                       the entity's meta file
            B <entity> <path>                                       the entity's base file
            C <layer> <entity> <module> <functions> <options> <path> a correction file, in the
                                                                    order applied (functions and
                                                                    options comma separated,
                                                                    options "-" for none)
          Then "<count>\n", then per file "<path>\n<byte length>\n<bytes>": exactly the files the
          plan names, already checked against the pin's content hash by the caller.
  stdout  one tab separated line per projected value, numbers only:
            S <entity> <id> <field> <value> <mask>          a scalar field
            L <entity> <id> <field> <value> <mask>          one element of a list field, in order
            G <entity> <id> <field> <group> <value> <mask>  one element of a grouped field
            P <entity> <id> <zone> <x> <y> <mask>           one spawn point
            # <layer> <file> <rows> <created> <steps>       what each provider did
          then "END <lines>". A mask is the bits of every layer that stated the value while it
          stood (bit 2^i for LAYERS[i]); its lowest bit is the value's first origin.
]]

assert(_VERSION == "Lua 5.4", "open_sources_compose.lua needs Lua 5.4, not " .. tostring(_VERSION))

local sformat, sbyte, smatch, gmatch = string.format, string.byte, string.match, string.gmatch
local tconcat, tsort, tpack, tunpack = table.concat, table.sort, table.pack, table.unpack
local mtype, floor = math.type, math.floor

-------------------------------------------------------------------------------- the plan
local LAYERS = { [0] = "base", "legacy", "itemstart", "delta", "traces", "authored" }
local LAYER_INDEX = {}
for index = 0, #LAYERS do
  LAYER_INDEX[LAYERS[index]] = index
end
local ENTITIES = { "Quest", "Npc", "Item", "Object" }
local ENTITY = { Quest = true, Npc = true, Item = true, Object = true }
local OPTIONS = { noNewEntries = true, noOverwrites = true }
local DATA_FIELDS = { Quest = "questData", Npc = "npcData", Item = "itemData", Object = "objectData" }
local KEYS_FIELDS = { Quest = "questKeys", Npc = "npcKeys", Item = "itemKeys", Object = "objectKeys" }

local skip = {}
assert(arg[1], "usage: lua open_sources_compose.lua <layers to leave out, or -> < plan and files")
if arg[1] ~= "-" then
  for name in gmatch(arg[1], "[^,]+") do
    assert(LAYER_INDEX[name] and name ~= "base", "not a layer that can be left out: " .. name)
    skip[name] = true
  end
end

local function split(line)
  local out = {}
  for part in gmatch(line .. "\t", "([^\t]*)\t") do
    out[#out + 1] = part
  end
  return out
end

local function checked_path(path)
  assert(
    type(path) == "string" and smatch(path, "^[%w_][%w_%./%-]*%.lua$") and not smatch(path, "%.%.")
      and not smatch(path, "//"),
    "the plan names a path this composer does not take"
  )
  return path
end

local function checked_name(name)
  assert(type(name) == "string" and smatch(name, "^[%a_][%w_]*$"), "the plan names a module or function badly")
  return name
end

local function names(list)
  local out = {}
  if list ~= "-" then
    for name in gmatch(list, "[^,]+") do
      out[#out + 1] = checked_name(name)
    end
  end
  return out
end

-- The enum files, each entity's meta and base file, and the correction layers in the order the
-- upstream registry applies them: { layer, file, module, entity, functions, options }. A provider
-- with noNewEntries and noOverwrites (the item start fixes) only fills where nothing is stated.
local ENUM_FILES, META_FILES, BASE_FILES, PROVIDERS = {}, {}, {}, {}
local PLANNED = {}
do
  local count = tonumber(smatch(io.read("l") or "", "^PLAN\t(%d+)$"))
  assert(count, "the input does not start with a plan")
  for _ = 1, count do
    local parts = split(io.read("l") or "")
    local kind = parts[1]
    local path
    if kind == "E" and #parts == 2 then
      path = checked_path(parts[2])
      ENUM_FILES[#ENUM_FILES + 1] = path
    elseif (kind == "M" or kind == "B") and #parts == 3 then
      assert(ENTITY[parts[2]], "the plan names an entity this composer does not know")
      local held = kind == "M" and META_FILES or BASE_FILES
      assert(held[parts[2]] == nil, "the plan names an entity's file twice")
      path = checked_path(parts[3])
      held[parts[2]] = path
    elseif kind == "C" and #parts == 7 then
      local layer, entity = parts[2], parts[3]
      assert(LAYER_INDEX[layer] and layer ~= "base", "the plan names a layer this composer does not know")
      assert(ENTITY[entity], "the plan names an entity this composer does not know")
      local functions = names(parts[5])
      assert(#functions > 0, "the plan names a correction file without functions")
      local options = {}
      for _, option in ipairs(names(parts[6])) do
        assert(OPTIONS[option], "the plan names a merge option this composer does not apply")
        options[option] = true
      end
      path = checked_path(parts[7])
      PROVIDERS[#PROVIDERS + 1] =
        { layer, path, checked_name(parts[4]), entity, functions, next(options) and options or nil }
      if #PROVIDERS > 1 then
        assert(
          LAYER_INDEX[PROVIDERS[#PROVIDERS - 1][1]] <= LAYER_INDEX[layer],
          "the plan applies the layers out of their order"
        )
      end
    else
      error("the plan holds a line this composer does not know", 0)
    end
    assert(PLANNED[path] == nil, "the plan names a file twice")
    PLANNED[path] = true
  end
  assert(#ENUM_FILES > 0, "the plan names no enum file")
  for _, entity in ipairs(ENTITIES) do
    assert(META_FILES[entity] and BASE_FILES[entity], "the plan lacks a meta or base file for " .. entity)
  end
end

-------------------------------------------------------------------------------- input
local FILES = {}
do
  local count = math.tointeger(tonumber(io.read("l")))
  assert(count and count >= 0, "the input does not give a file count after the plan")
  for _ = 1, count do
    local path = io.read("l")
    local length = math.tointeger(tonumber(io.read("l")))
    assert(path and PLANNED[path], "the input holds a file the plan does not name")
    assert(length and length >= 0, "a file without its length")
    assert(FILES[path] == nil, "a file given twice")
    local body = length == 0 and "" or io.read(length)
    assert(body and #body == length, "a file shorter than its length")
    FILES[path] = body
  end
  for path in pairs(PLANNED) do
    assert(FILES[path] ~= nil, "a file the plan names is missing: " .. path)
  end
end

-------------------------------------------------------------------------------- the sandbox
local STRING_META = getmetatable("")
local HOST_STRING_INDEX = STRING_META.__index
local SANDBOX_STRING_INDEX = {}

-- The count hook fires every STEP instructions. One call of upstream code may take LIMIT_STEPS of
-- them (100 million instructions; the largest file, the creature base, takes 54 steps at the
-- pinned commit, so a loop that never ends stops in about a second) while the whole process holds
-- at most MEMORY_KB (2 GB; the composer peaks at about 350 MB at the pinned commit).
local STEP = 10000
local LIMIT_STEPS = 10000
local MEMORY_KB = 2 * 1024 * 1024

local function run_limited(label, fn, ...)
  local steps = 0
  local function hook()
    steps = steps + 1
    if steps > LIMIT_STEPS then
      error("instruction limit reached", 0)
    end
    if collectgarbage("count") > MEMORY_KB then
      error("memory limit reached", 0)
    end
  end
  STRING_META.__index = SANDBOX_STRING_INDEX
  debug.sethook(hook, "", STEP)
  local result = tpack(pcall(fn, ...))
  debug.sethook()
  STRING_META.__index = HOST_STRING_INDEX
  if not result[1] then
    local message = result[2]
    if type(message) ~= "string" then
      message = "an error value of type " .. type(message)
    end
    error(label .. ": " .. message:sub(1, 300), 0)
  end
  return steps, tunpack(result, 2, result.n)
end

local function load_text(text, name, env)
  assert(type(text) == "string", name .. " is not text")
  assert(sbyte(text, 1) ~= 27, "binary chunk refused: " .. name)
  local fn, problem = load(text, "=" .. name, "t", env)
  if not fn then
    error(name .. ": " .. tostring(problem):sub(1, 300), 0)
  end
  return fn
end

local STEPS = {}

local function run_file(path, env, ...)
  local steps, a, b, c = run_limited(path, load_text(FILES[path], path, env), ...)
  STEPS[path] = (STEPS[path] or 0) + steps
  return a, b, c
end

local function copy(source)
  local out = {}
  for key, value in pairs(source) do
    out[key] = value
  end
  return out
end

-------------------------------------------------------------------------------- constants and schemas
local ns = { Meta = {} }
for _, path in ipairs(ENUM_FILES) do
  run_file(path, {}, "QuestieDB", ns)
end
local constants = ns.Enum
assert(type(constants) == "table", "the enum files made no constants")

local META = {}
for _, entity in ipairs(ENTITIES) do
  local meta = run_file(META_FILES[entity], {}, "QuestieDB", ns)
  assert(type(meta) == "table" and type(meta.keys) == "table" and type(meta.names) == "table", entity)
  assert(mtype(meta.fieldCount) == "integer", entity .. " meta has no field count")
  META[entity] = meta
  local keys = {}
  for name, index in pairs(meta.keys) do
    keys[name] = index
    keys[name .. "_add"] = index + 1000
    keys[name .. "_remove"] = index - 1000
  end
  constants[KEYS_FIELDS[entity]] = keys
end

-- The fields the file is made from must still exist with the structure this composer reads (false:
-- a plain value). A schema that renamed, dropped or reshaped one is a new shape: stop, never guess.
local SCHEMA = {
  Quest = {
    startedBy = "questgivers",
    finishedBy = "questgivers",
    objectives = "objectives",
    preQuestSingle = "idarray",
    preQuestGroup = "idarray",
    sourceItemId = false,
    questLevel = false,
    requiredLevel = false,
    requiredRaces = false,
    requiredClasses = false,
    nextQuestInChain = false,
  },
  Npc = {
    spawns = "spawnlist",
    npcFlags = false,
    minLevel = false,
    maxLevel = false,
    zoneID = false,
    friendlyToFaction = false,
  },
  Item = {
    npcDrops = "idarray",
    objectDrops = "idarray",
    itemDrops = "idarray",
    vendors = "idarray",
    questRewards = "idarray",
    startQuest = false,
  },
  Object = { spawns = "spawnlist", zoneID = false },
}
for _, entity in ipairs(ENTITIES) do
  local meta = META[entity]
  local fields = {}
  for name in pairs(SCHEMA[entity]) do
    fields[#fields + 1] = name
  end
  tsort(fields)
  for _, name in ipairs(fields) do
    local index = meta.keys[name]
    assert(
      mtype(index) == "integer" and index >= 1 and index <= meta.fieldCount,
      entity .. " schema has no field " .. name .. ": a shape this composer does not know"
    )
    local want = SCHEMA[entity][name]
    local got = meta.structures and meta.structures[index]
    assert(
      (want == false and got == nil) or got == want,
      entity .. " schema reshaped " .. name .. ": a shape this composer does not know"
    )
  end
end

-- classKeys and npcFlags differ by flavour: Forever's own, else Classic's.
local ACTIVE = { classKeys = true, npcFlags = true }
local function pick(name)
  local shared = (not ACTIVE[name]) and constants[name] or nil
  if shared ~= nil then
    return shared
  end
  local by = constants.byExpansion or {}
  local value = by.Forever and by.Forever[name]
  if value == nil then
    value = by.Classic and by.Classic[name]
  end
  if value == nil then
    error("unknown constant " .. name, 0)
  end
  return value
end

local captured = { Quest = {}, Npc = {}, Item = {}, Object = {} }
local modules = {}
modules.QuestieDB = {
  questKeys = constants.questKeys,
  npcKeys = constants.npcKeys,
  itemKeys = constants.itemKeys,
  objectKeys = constants.objectKeys,
  raceKeys = pick("raceKeys"),
  classKeys = pick("classKeys"),
  sortKeys = pick("sortKeys"),
  specialFlags = pick("specialFlags"),
  factionIDs = pick("factionIDs"),
  questFlags = pick("questFlags"),
  npcFlags = pick("npcFlags"),
  itemClasses = pick("itemClasses"),
  waypointPresets = pick("waypointPresets"),
  questData = captured.Quest,
  npcData = captured.Npc,
  itemData = captured.Item,
  objectData = captured.Object,
}
for _, field in ipairs({ "questKeys", "npcKeys", "itemKeys", "objectKeys" }) do
  local reversed = {}
  for key, index in pairs(modules.QuestieDB[field]) do
    reversed[index] = key
  end
  modules.QuestieDB[field .. "Reversed"] = reversed
end
modules.ZoneDB = { zoneIDs = pick("zoneIDs") }
modules.QuestieProfessions = {
  professionKeys = pick("professionKeys"),
  specializationKeys = pick("specializationKeys"),
  rankNames = pick("rankNames"),
}
modules.QuestieCorrections = {
  killCreditObjectiveFirst = {},
  objectObjectiveFirst = {},
  itemObjectiveFirst = {},
  eventObjectiveFirst = {},
  spellObjectiveFirst = {},
}
modules.Phasing = { phases = pick("phases") }
modules.l10n = setmetatable({}, {
  __call = function(_, text)
    return text
  end,
})
modules.Expansions = { Era = 1, Classic = 1, Tbc = 2, Wotlk = 3, Cata = 4, MoP = 5, Current = 1 }
modules.DropDB = { correctionKeys = { WOWHEAD = -1, PSERVER = -2 } }

local QuestieLoader = {
  ImportModule = function(_, name)
    modules[name] = modules[name] or {}
    return modules[name]
  end,
  CreateModule = function(_, name)
    modules[name] = modules[name] or {}
    return modules[name]
  end,
}
local QUESTIE_STAND_IN = copy(constants.iconTypes or {})

-------------------------------------------------------------------------------- shapes
local function shape(entity, field)
  return META[entity].structures and META[entity].structures[field]
end
local GROUPED = { questgivers = true, objectives = true, spawnlist = true, waypointlist = true }

local function ser(value)
  local kind = type(value)
  if kind == "number" then
    if mtype(value) == "integer" then
      return sformat("%d", value)
    end
    if value == floor(value) and math.abs(value) < 2 ^ 53 then
      return sformat("%d", floor(value))
    end
    return sformat("%.6g", value)
  elseif kind == "string" then
    return sformat("%q", value)
  elseif kind == "table" then
    local keys = {}
    for key in pairs(value) do
      keys[#keys + 1] = key
    end
    tsort(keys, function(a, b)
      if type(a) == type(b) then
        return a < b
      end
      return type(a) == "number"
    end)
    local parts = {}
    for _, key in ipairs(keys) do
      parts[#parts + 1] = ser(key) .. "=" .. ser(value[key])
    end
    return "{" .. tconcat(parts, ",") .. "}"
  end
  return tostring(value)
end

-- The key an element is known by inside a list: the unit of add, remove and origin.
local function elemkey(sh, group, elem)
  if sh == "spawnlist" then
    if type(elem) == "table" then
      return sformat("%.2f,%.2f", tonumber(elem[1]) or -1, tonumber(elem[2]) or -1)
    end
    return ser(elem)
  end
  if sh == "objectives" and type(elem) == "table" and group ~= 4 and group ~= 5 then
    return ser(elem[1])
  end
  return ser(elem)
end

local function isempty(value)
  return type(value) == "table" and next(value) == nil
end

-- Numeric keys in ascending order, so every pass is the same pass on every run.
local function sorted_keys(source)
  local keys = {}
  for key in pairs(source) do
    keys[#keys + 1] = key
  end
  tsort(keys, function(a, b)
    local ta, tb = type(a), type(b)
    if ta == tb and (ta == "number" or ta == "string") then
      return a < b
    end
    return ta < tb
  end)
  return keys
end

-------------------------------------------------------------------------------- state
local DB, ORG = {}, {}
for _, entity in ipairs(ENTITIES) do
  DB[entity], ORG[entity] = {}, {}
end

local function kind_of(entity, field)
  local sh = shape(entity, field)
  if sh and GROUPED[sh] and sh ~= "waypointlist" then
    return "grouped", sh
  end
  if sh == "idarray" or sh == "pairs" or sh == "reputationpairs" then
    return "list", sh
  end
  return "scalar", sh
end

-- The origin of a field after `bit`'s layer replaced its value: an element that stood before
-- keeps its bits, a new one gets this layer's.
local function origin_replace(entity, id, field, old, new, bit)
  local origins = ORG[entity][id]
  local before = origins[field]
  local kind, sh = kind_of(entity, field)
  if new == nil then
    origins[field] = nil
    return
  end
  if kind == "scalar" then
    if before and ser(old) == ser(new) then
      origins[field] = { m = before.m | bit }
    else
      origins[field] = { m = bit }
    end
  elseif kind == "list" then
    local e = {}
    for _, elem in ipairs(new) do
      local key = elemkey(sh, nil, elem)
      local held = before and before.e and before.e[key]
      e[key] = (held or 0) | bit
    end
    origins[field] = { e = e }
  else
    local g = {}
    for group, list in pairs(new) do
      g[group] = {}
      if type(list) == "table" then
        for _, elem in ipairs(list) do
          local key = elemkey(sh, group, elem)
          local held = before and before.g and before.g[group] and before.g[group][key]
          g[group][key] = (held or 0) | bit
        end
        if sh == "objectives" and group == 4 and next(list) ~= nil and #list == 0 then
          local key = ser(list)
          local held = before and before.g and before.g[group] and before.g[group][key]
          g[group][key] = (held or 0) | bit
        end
      end
    end
    origins[field] = { g = g }
  end
end

local function find(list, key, sh, group)
  for index, elem in ipairs(list) do
    if elemkey(sh, group, elem) == key then
      return index
    end
  end
  return nil
end

-- An add or a remove operation, keeping origins.
local function apply_op(entity, id, field, op, operand, bit)
  local row = DB[entity][id]
  local origins = ORG[entity][id]
  local kind, sh = kind_of(entity, field)
  local current = row[field]
  if kind == "list" then
    current = current and { tunpack(current) } or {}
    local origin = (origins[field] and origins[field].e) or {}
    for _, elem in ipairs(operand) do
      local key = elemkey(sh, nil, elem)
      local at = find(current, key, sh, nil)
      if op == "add" then
        if at then
          origin[key] = (origin[key] or 0) | bit
        else
          current[#current + 1] = elem
          origin[key] = bit
        end
      elseif at then
        table.remove(current, at)
        origin[key] = nil
      end
    end
    if #current == 0 then
      row[field], origins[field] = nil, nil
    else
      row[field], origins[field] = current, { e = origin }
    end
  elseif kind == "grouped" then
    local out = {}
    if type(current) == "table" then
      for group, list in pairs(current) do
        out[group] = list
      end
    end
    local og = (origins[field] and origins[field].g) or {}
    for _, group in ipairs(sorted_keys(operand)) do
      local list = operand[group]
      if type(list) == "table" then
        local held = out[group] and { tunpack(out[group]) } or {}
        og[group] = og[group] or {}
        if sh == "objectives" and group == 4 then
          local key = ser(list)
          if op == "add" then
            held, og[group] = list, { [key] = bit }
          else
            held, og[group] = {}, {}
          end
        else
          for _, elem in ipairs(list) do
            local key = elemkey(sh, group, elem)
            local at = find(held, key, sh, group)
            if op == "add" then
              if at then
                og[group][key] = (og[group][key] or 0) | bit
              else
                held[#held + 1] = elem
                og[group][key] = bit
              end
            elseif at then
              table.remove(held, at)
              og[group][key] = nil
            end
          end
        end
        if next(held) == nil then
          out[group], og[group] = nil, nil
        else
          out[group] = held
        end
      end
    end
    if next(out) == nil then
      row[field], origins[field] = nil, nil
    else
      row[field], origins[field] = out, { g = og }
    end
  else
    error(sformat("an operation on a scalar field: %s %s %d", entity, tostring(field), id), 0)
  end
end

local STATS = {}

local function merge(entity, layer, corrections, options, label)
  options = options or {}
  local bit = 1 << LAYER_INDEX[layer]
  local stat = STATS[label] or { layer = layer, rows = 0, created = 0 }
  STATS[label] = stat
  local count = META[entity].fieldCount
  for _, id in ipairs(sorted_keys(corrections)) do
    local fields = corrections[id]
    if mtype(id) == "integer" and type(fields) == "table" then
      stat.rows = stat.rows + 1
      local row = DB[entity][id]
      if not row and not options.noNewEntries and next(fields) ~= nil then
        row = {}
        DB[entity][id], ORG[entity][id] = row, {}
        stat.created = stat.created + 1
      end
      if row then
        local keys = sorted_keys(fields)
        -- Replacements first, then operations (the two never share a field).
        for _, key in ipairs(keys) do
          local value = fields[key]
          if mtype(key) == "integer" and key >= 1 and key <= count then
            if options.noOverwrites and row[key] ~= nil then -- luacheck: ignore 542
              -- left as it is
            elseif isempty(value) then
              row[key], ORG[entity][id][key] = nil, nil
            else
              local old = row[key]
              row[key] = value
              origin_replace(entity, id, key, old, value, bit)
            end
          end
        end
        for _, key in ipairs(keys) do
          local value = fields[key]
          if mtype(key) == "integer" and (key >= 1000 or key <= 0) then
            local field = key >= 1000 and key - 1000 or key + 1000
            local op = key >= 1000 and "add" or "remove"
            if field >= 1 and field <= count and type(value) == "table" and next(value) ~= nil then
              apply_op(entity, id, field, op, value, bit)
            end
          end
        end
      end
    end
  end
end

-------------------------------------------------------------------------------- the base
local function load_base(entity)
  local path = BASE_FILES[entity]
  local stub = {}
  local loader = {
    ImportModule = function()
      return stub
    end,
    CreateModule = function()
      return stub
    end,
  }
  run_file(path, { QuestieLoader = loader })
  local text = stub[DATA_FIELDS[entity]]
  assert(type(text) == "string", "no data string in " .. path)
  local steps, rows = run_limited(path .. ":data", load_text(text, path .. ":data", {}))
  STEPS[path] = (STEPS[path] or 0) + steps
  assert(type(rows) == "table", "the data string of " .. path .. " made no table")
  return rows
end

for _, entity in ipairs(ENTITIES) do
  local rows = load_base(entity)
  local stat = { layer = "base", rows = 0, created = 0 }
  STATS["base " .. BASE_FILES[entity]] = stat
  for _, id in ipairs(sorted_keys(rows)) do
    local source = rows[id]
    if mtype(id) == "integer" and type(source) == "table" then
      local row = {}
      for field = 1, META[entity].fieldCount do
        local value = source[field]
        if value ~= nil and not isempty(value) then
          row[field] = value
        end
      end
      DB[entity][id], ORG[entity][id] = row, {}
      for _, field in ipairs(sorted_keys(row)) do
        origin_replace(entity, id, field, nil, row[field], 1)
      end
      stat.rows = stat.rows + 1
      stat.created = stat.created + 1
    end
  end
end

-------------------------------------------------------------------------------- the correction layers
-- Every provider file is loaded first (as the upstream TOC does), then the static functions run
-- in order, each one's rows merged per entity as the upstream registry applies them.
local fileEnv = { QuestieLoader = QuestieLoader, Questie = QUESTIE_STAND_IN }
for _, provider in ipairs(PROVIDERS) do
  if not skip[provider[1]] then
    run_file(provider[2], fileEnv)
  end
end
for _, provider in ipairs(PROVIDERS) do
  local layer, path, name, entity, functions, options = tunpack(provider, 1, 6)
  if not skip[layer] then
    local module = modules[name]
    assert(type(module) == "table", "module missing: " .. name)
    for _, fname in ipairs(functions) do
      for _, held in pairs(captured) do
        for key in pairs(held) do
          held[key] = nil
        end
      end
      local fn = module[fname]
      assert(type(fn) == "function", name .. "." .. fname .. " missing")
      local steps, corrections = run_limited(path, fn, module)
      STEPS[path] = (STEPS[path] or 0) + steps
      corrections = corrections or {}
      assert(type(corrections) == "table", path .. " returned no table")
      local label = layer .. " " .. path
      merge(entity, layer, corrections, options, label)
      for _, other in ipairs(ENTITIES) do
        if next(captured[other]) then
          merge(other, layer, captured[other], options, label)
        end
      end
    end
  end
end

-------------------------------------------------------------------------------- out: numbers only
-- The fields OpenSources.lua is made from, by the upstream meta names. Nothing else leaves.
local PROJECT = {
  Quest = {
    scalar = { "sourceItemId", "questLevel", "requiredLevel", "requiredRaces", "requiredClasses", "nextQuestInChain" },
    list = { "preQuestSingle", "preQuestGroup" },
    grouped = { startedBy = { 1, 2, 3 }, finishedBy = { 1, 2 }, objectives = { 3 } },
  },
  Npc = { scalar = { "npcFlags", "minLevel", "maxLevel", "zoneID" }, side = "friendlyToFaction", spawns = "spawns" },
  Item = { scalar = { "startQuest" }, list = { "npcDrops", "objectDrops", "itemDrops", "vendors", "questRewards" } },
  Object = { scalar = { "zoneID" }, spawns = "spawns" },
}
local SIDES = { A = 1, H = 2, AH = 3 }

local out = {}

local function number(value, where)
  if mtype(value) == "integer" then
    return sformat("%d", value)
  end
  if mtype(value) == "float" and value == value and value ~= math.huge and value ~= -math.huge then
    if value == floor(value) and math.abs(value) < 2 ^ 53 then
      return sformat("%d", math.tointeger(value))
    end
    return sformat("%.17g", value)
  end
  error("not a number where one belongs: " .. where, 0)
end

-- The id inside an element: the element itself, or its first entry (an objective's item).
local function first(elem)
  if type(elem) == "table" then
    return elem[1]
  end
  return elem
end

for _, entity in ipairs(ENTITIES) do
  local project = PROJECT[entity]
  local index = META[entity].keys
  for _, id in ipairs(sorted_keys(DB[entity])) do
    local row, origins = DB[entity][id], ORG[entity][id]
    local where = entity .. " " .. sformat("%d", id)
    for _, name in ipairs(project.scalar or {}) do
      local field = index[name]
      local value = field and row[field]
      if value ~= nil then
        local mask = origins[field] and origins[field].m or 0
        out[#out + 1] = tconcat({
          "S", entity, sformat("%d", id), name, number(value, where .. " " .. name), sformat("%d", mask),
        }, "\t")
      end
    end
    for _, name in ipairs(project.list or {}) do
      local field = index[name]
      local value = field and row[field]
      if type(value) == "table" then
        local sh = shape(entity, field)
        local origin = origins[field] and origins[field].e or {}
        for _, elem in ipairs(value) do
          local mask = origin[elemkey(sh, nil, elem)] or 0
          out[#out + 1] = tconcat({
            "L", entity, sformat("%d", id), name, number(first(elem), where .. " " .. name), sformat("%d", mask),
          }, "\t")
        end
      end
    end
    for _, name in ipairs(sorted_keys(project.grouped or {})) do
      local field = index[name]
      local value = field and row[field]
      if type(value) == "table" then
        local sh = shape(entity, field)
        local og = origins[field] and origins[field].g or {}
        for _, group in ipairs(project.grouped[name]) do
          local list = value[group]
          if type(list) == "table" then
            for _, elem in ipairs(list) do
              local id_ = first(elem)
              if id_ ~= nil then
                local mask = og[group] and og[group][elemkey(sh, group, elem)] or 0
                out[#out + 1] = tconcat({
                  "G", entity, sformat("%d", id), name, sformat("%d", group),
                  number(id_, where .. " " .. name), sformat("%d", mask),
                }, "\t")
              end
            end
          end
        end
      end
    end
    if project.side then
      local field = index[project.side]
      local value = field and row[field]
      local side = type(value) == "string" and SIDES[value] or nil
      if side then
        local mask = origins[field] and origins[field].m or 0
        out[#out + 1] = tconcat({
          "S", entity, sformat("%d", id), project.side, sformat("%d", side), sformat("%d", mask),
        }, "\t")
      end
    end
    if project.spawns then
      local field = index[project.spawns]
      local value = field and row[field]
      if type(value) == "table" then
        local sh = shape(entity, field)
        local og = origins[field] and origins[field].g or {}
        for _, zone in ipairs(sorted_keys(value)) do
          local list = value[zone]
          if mtype(zone) == "integer" and type(list) == "table" then
            for _, point in ipairs(list) do
              if type(point) == "table" and type(point[1]) == "number" and type(point[2]) == "number" then
                local mask = og[zone] and og[zone][elemkey(sh, zone, point)] or 0
                out[#out + 1] = tconcat({
                  "P", entity, sformat("%d", id), sformat("%d", zone),
                  number(point[1], where .. " x"), number(point[2], where .. " y"), sformat("%d", mask),
                }, "\t")
              end
            end
          end
        end
      end
    end
  end
end

for _, label in ipairs(sorted_keys(STATS)) do
  local stat = STATS[label]
  local path = smatch(label, "^%S+ (.+)$")
  out[#out + 1] = tconcat({
    "#", stat.layer, path, sformat("%d", stat.rows), sformat("%d", stat.created), sformat("%d", STEPS[path] or 0),
  }, "\t")
end
out[#out + 1] = "END\t" .. sformat("%d", #out)
io.write(tconcat(out, "\n"), "\n")
