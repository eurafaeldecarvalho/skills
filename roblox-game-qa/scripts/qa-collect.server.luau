--!nocheck
-- qa-collect.server.luau — SERVER side of a client probe (run with: studio-mcp.py run-pair CLIENT SERVER).
-- Creates ReplicatedStorage.QA_Channel, waits for probe reports from clients and prints them as
-- "[qa] <TAG> <json>" so the play tool returns them in its logs. Also forwards client Output errors.
-- Edit WAIT_S / EXPECT to match the probe. Remove nothing here: studio-mcp.py removes the client script.
local RS = game:GetService("ReplicatedStorage")
local WAIT_S, EXPECT = 45, 1 -- seconds to wait, number of reports to wait for
local ch = RS:FindFirstChild("QA_Channel") or Instance.new("RemoteEvent")
ch.Name = "QA_Channel"
ch.Parent = RS
local got = 0
ch.OnServerEvent:Connect(function(plr, tag, payload)
	if tag == "log" then
		print("[qa] CLIENT-LOG " .. plr.Name .. " " .. tostring(payload))
	else
		got += 1
		print("[qa] " .. tostring(tag) .. " " .. tostring(payload))
	end
end)
local t0 = os.clock()
while got < EXPECT and os.clock() - t0 < WAIT_S do
	task.wait(0.5)
end
ch:Destroy()
return if got >= EXPECT then "ok " .. got .. " report(s)" else "TIMEOUT: " .. got .. "/" .. EXPECT .. " report(s)"
