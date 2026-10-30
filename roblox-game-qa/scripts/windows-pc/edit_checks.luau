local Http = game:GetService("HttpService")
local P = game:GetService("Players")
local r = { maxPlayers = P.MaxPlayers, preferredPlayers = P.PreferredPlayers, characterAutoLoads = P.CharacterAutoLoads,
	placeId = game.PlaceId, gameId = game.GameId, nome = game.Name, inst = #game:GetDescendants() }
local sons, semId, textos, menorTexto, scaled, qa = 0, {}, 0, math.huge, 0, {}
for _, d in game:GetDescendants() do
	if d:IsA("Sound") then sons += 1 if d.SoundId == "" and #semId < 15 then table.insert(semId, d:GetFullName()) end end
	if string.sub(d.Name, 1, 3) == "QA_" then table.insert(qa, d:GetFullName()) end
end
r.sons, r.sonsSemId, r.restosQA = sons, semId, qa
local L = game:GetService("Lighting")
local function ler(o, k) local ok, v = pcall(function() return o[k] end) return if ok then tostring(v) else "(sem acesso)" end
r.lighting = { tech = ler(L, "Technology"), brilho = ler(L, "Brightness"), hora = ler(L, "ClockTime"), amb = ler(L, "Ambient") }
local sp = game:GetService("StarterPlayer")
r.starterPlayer = { devTouch = tostring(sp.DevTouchMovementMode), devComp = tostring(sp.DevComputerMovementMode), camMode = tostring(sp.CameraMode), walk = sp.CharacterWalkSpeed, jump = sp.CharacterJumpPower }
local sgui = game:GetService("StarterGui")
r.starterGui = {} for _, c in sgui:GetChildren() do table.insert(r.starterGui, c.ClassName .. ":" .. c.Name) end
r.sps = {} for _, c in sp.StarterPlayerScripts:GetChildren() do table.insert(r.sps, c.ClassName .. ":" .. c.Name) end
r.sss = {} for _, c in game:GetService("ServerScriptService"):GetChildren() do table.insert(r.sss, c.ClassName .. ":" .. c.Name) end
r.rf = {} for _, c in game:GetService("ReplicatedFirst"):GetChildren() do table.insert(r.rf, c.ClassName .. ":" .. c.Name) end
local ok, v = pcall(function() return game:GetService("SoundService").RespectFilteringEnabled end) r.respectFE = ok and v
r.streaming = workspace.StreamingEnabled
return Http:JSONEncode(r)
