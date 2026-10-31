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
			toqueVisiveis = (function()
				local tg = lp.PlayerGui:FindFirstChild("TouchGui")
				if not tg then return "sem TouchGui" end
				local v = {}
				for _, x in tg:GetDescendants() do
					if x:IsA("GuiObject") and x.Visible and (x.Name:find("Jump") or x.Name:find("Thumbstick")) then
						local vis, a = true, x.Parent
						while a and a ~= tg do if a:IsA("GuiObject") and not a.Visible then vis = false end a = a.Parent end
						if vis then table.insert(v, x.Name) end
					end
				end
				return (tg.Enabled and "on:" or "off:") .. table.concat(v, ",")
			end)(),
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
		-- macaco com seed (seed nova a cada iteracao): remotes do jogo x argumentos hostis aleatorios
		local disparos, falhasLocais = 0, 0
		if typeof(extra) == "table" and extra.seed then
			local rng = Random.new(extra.seed)
			local alvos = {}
			for _, x in R:GetChildren() do if x:IsA("RemoteEvent") then table.insert(alvos, x) end end
			table.sort(alvos, function(a, b) return a.Name < b.Name end)
			local pool = { 0, -1, 1, 2, 7, 1e9, -1e9, 0 / 0, math.huge, "", "Moenda", "Copos", "Fritadeira", "Servir", "Recusar", "Clique", "Inicio", "Fim", "Cozinheiro", "Vigia", "todos", string.rep("z", 3000), {}, { 1, 2, 3 }, { id = 1 }, true, false, Vector3.new(1e6, 0, 0), workspace, lp }
			for _ = 1, 120 do
				local alvo = alvos[rng:NextInteger(1, #alvos)]
				local a = {}
				local k = rng:NextInteger(0, 3)
				for j = 1, k do a[j] = pool[rng:NextInteger(1, #pool)] end
				local ok = pcall(function() alvo:FireServer(table.unpack(a, 1, k)) end)
				disparos += 1
				if not ok then falhasLocais += 1 end
				if rng:NextNumber() < 0.2 then task.wait() end
			end
		end
		task.wait(2)
		canal:FireServer("redteam", { papelDepois = papel, modoDepois = modo, maoMsgsNovas = cont.mao - m0, seed = typeof(extra) == "table" and extra.seed, disparos = disparos, falhasLocais = falhasLocais })
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
