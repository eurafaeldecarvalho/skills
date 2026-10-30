local SSS = game:GetService("ServerScriptService") local SPS = game:GetService("StarterPlayer").StarterPlayerScripts
local t = {}
workspace:SetAttribute("QA_MT", nil)
for _, x in {SSS:FindFirstChild("QA_Multi"), SPS:FindFirstChild("QA_MultiCli"), SPS:FindFirstChild("QA_UiLobby"), SPS:FindFirstChild("QA_UiTurno"), game.ReplicatedStorage:FindFirstChild("QA_MultiCanal"), game.ReplicatedStorage:FindFirstChild("QA_Channel")} do table.insert(t, x.Name) x:Destroy() end
local resto = {} for _, d in game:GetDescendants() do if string.sub(d.Name,1,3) == "QA_" then table.insert(resto, d:GetFullName()) end end
return "removidos: " .. table.concat(t, ",") .. " | restos QA_: " .. #resto
