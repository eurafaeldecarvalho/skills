-- fps/memoria do cliente em 5 s + telas visiveis
local RunS = game:GetService("RunService") local Http = game:GetService("HttpService") local St = game:GetService("Stats")
local n, t0, pior, last = 0, os.clock(), 0, os.clock()
local con = RunS.RenderStepped:Connect(function() local a = os.clock() pior = math.max(pior, a - last) last = a n += 1 end)
task.wait(5) con:Disconnect()
local lp = game:GetService("Players").LocalPlayer local t = {}
for _, sg in lp.PlayerGui:GetChildren() do if sg:IsA("ScreenGui") and sg.Enabled then table.insert(t, sg.Name) end end
local cam = workspace.CurrentCamera
return Http:JSONEncode({ fps = math.floor(n / (os.clock() - t0)), piorFrameMs = math.floor(pior * 1000), memMb = math.floor(St:GetTotalMemoryUsageMb()), telas = t, vp = { cam.ViewportSize.X, cam.ViewportSize.Y }, camTipo = cam.CameraType.Name, ping = St.Network.ServerStatsItem and nil, inst = #game:GetDescendants() })
