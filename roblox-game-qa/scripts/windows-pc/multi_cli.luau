-- QA_MultiCli (temporario): responde aos comandos do QA_Multi pelos remotes reais do jogo
local RS = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")
local LogService = game:GetService("LogService")
local R = RS:WaitForChild("Remotes")
local lp = Players.LocalPlayer
local cont = { chegou = {}, eventos = 0, sinais = 0, sinaisComPista = 0, mao = 0, estados = 0, avisos = {} }
local papel, modo, posto, ultimoEstado, ultimaMao
R.PapelAtribuido.OnClientEvent:Connect(function(p, m, ps) papel, modo, posto = p, m, ps end)
R.EstadoNoite.OnClientEvent:Connect(function(e) cont.estados += 1 ultimoEstado = e end)
R.ClienteEvento.OnClientEvent:Connect(function(ev) cont.eventos += 1 if typeof(ev) == "table" and ev.tipo == "Chegou" then table.insert(cont.chegou, tostring(ev.clienteId)) end end)
R.SinaisParaVigia.OnClientEvent:Connect(function(id, pistas) cont.sinais += 1 if id ~= -1 and typeof(pistas) == "table" and #pistas > 0 then cont.sinaisComPista += 1 end end)
R.MaoAtualizada.OnClientEvent:Connect(function(m) cont.mao += 1 ultimaMao = m end)
R.EstacaoAtualizada.OnClientEvent:Connect(function(_e, d) if typeof(d) == "table" and d.aviso and #cont.avisos < 6 then table.insert(cont.avisos, d.aviso) end end)
local canal = RS:WaitForChild("QA_MultiCanal", 120)
if not canal then return end
LogService.MessageOut:Connect(function(msg, tipo)
	if (tipo == Enum.MessageType.MessageError or tipo == Enum.MessageType.MessageWarning) and string.sub(msg, 1, 4) ~= "[qa]" then
		canal:FireServer("log", tipo.Name .. " " .. string.sub(msg, 1, 300))
	end
end)
local function telas()
	local t = {}
	for _, sg in lp.PlayerGui:GetChildren() do
		if sg:IsA("ScreenGui") and sg.Enabled then table.insert(t, sg.Name) end
	end
	table.sort(t)
	return table.concat(t, ",")
end
local function maoTxt(m) if typeof(m) ~= "table" then return tostring(m) end local t = {} for _, v in m do table.insert(t, tostring(v)) end return table.concat(t, ",") end
canal.OnClientEvent:Connect(function(tag, extra)
	if tag == "relatorio" then
		local cam = workspace.CurrentCamera
		canal:FireServer("relatorio", {
			papel = papel, modo = modo, posto = posto, estados = cont.estados,
			estado = ultimoEstado and ultimoEstado.estado, turno = ultimoEstado and ultimoEstado.turno,
			tempo = ultimoEstado and ultimoEstado.tempoRestanteS, eventos = cont.eventos, chegou = table.concat(cont.chegou, ","),
			sinais = cont.sinais, sinaisComPista = cont.sinaisComPista, maoMsgs = cont.mao, mao = maoTxt(ultimaMao),
			avisos = table.concat(cont.avisos, " | "), telas = telas(), cameraTipo = cam.CameraType.Name,
			camPos = string.format("%.0f,%.0f,%.0f", cam.CFrame.Position.X, cam.CFrame.Position.Y, cam.CFrame.Position.Z),
			viewport = string.format("%dx%d", cam.ViewportSize.X, cam.ViewportSize.Y),
		})
	elseif tag == "redteam" then
		-- cliente hostil: tipos errados, papel alheio, spam
		local m0 = cont.mao
		R.AcaoCozinha:FireServer("Moenda", "Clique")
		R.AcaoCozinha:FireServer({}, nil)
		R.AcaoCozinha:FireServer(string.rep("x", 5000), "Inicio")
		R.Atender:FireServer(1, "Servir")
		R.Atender:FireServer("1", {})
		R.PedirPapel:FireServer(123)
		for _ = 1, 40 do R.PedirPapel:FireServer("Cozinheiro") end
		for _ = 1, 40 do R.TrocarPosto:FireServer() end
		R.MaisUmaNoite:FireServer()
		R.EnviarPing:FireServer(999, "todos")
		R.EnviarPing:FireServer(nil, nil)
		task.wait(2)
		canal:FireServer("redteam", { papelDepois = papel, modoDepois = modo, maoMsgsNovas = cont.mao - m0 })
	elseif tag == "caldo" then
		local m0 = cont.mao
		R.AcaoCozinha:FireServer("Moenda", "Clique")
		task.wait(0.4)
		R.AcaoCozinha:FireServer("Moenda", "Inicio")
		task.wait(3.3)
		R.AcaoCozinha:FireServer("Moenda", "Fim")
		task.wait(0.4)
		R.AcaoCozinha:FireServer("Copos", "Clique")
		task.wait(1)
		canal:FireServer("caldo", { mao = maoTxt(ultimaMao), maoMsgsNovas = cont.mao - m0, avisos = table.concat(cont.avisos, " | ") })
	elseif tag == "atender" then
		R.Atender:FireServer(extra.id, extra.decisao)
		task.wait(1)
		canal:FireServer("atender", { mao = maoTxt(ultimaMao), avisos = table.concat(cont.avisos, " | ") })
	elseif tag == "uiaudit" then
		local s = script.Parent:FindFirstChild("QA_UiTurnoSrc")
		if s then
			local fn = loadstring
			canal:FireServer("uiaudit", "sem loadstring no cliente")
		end
	end
end)
