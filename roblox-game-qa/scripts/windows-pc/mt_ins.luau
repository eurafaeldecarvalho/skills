local SSS = game:GetService("ServerScriptService") local SPS = game:GetService("StarterPlayer").StarterPlayerScripts
for _, x in {SSS:FindFirstChild("QA_Multi"), SPS:FindFirstChild("QA_MultiCli"), SPS:FindFirstChild("QA_UiLobby"), SPS:FindFirstChild("QA_UiTurno")} do x:Destroy() end
local function mk(cls, nome, pai, src) local s = Instance.new(cls) s.Name = nome s.Source = src s.Parent = pai return s end
mk("Script", "QA_Multi", SSS, [[-- QA_Multi (temporario): Server & Clients com N clientes; orquestra os clientes pelo QA_MultiCanal e encerra com EndTest
local STS = game:GetService("StudioTestService")
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local Http = game:GetService("HttpService")
local LogService = game:GetService("LogService")
local args = STS:GetTestArgs()
local n = tonumber(string.match(tostring(args), "^(%d+)")) or 2 -- args = "<n> <rotulo> seed<s>"
local t0 = os.clock()
local r = { args = tostring(args), passos = {}, cli = {}, logsServidor = {}, logsCliente = {}, ui = {} }
local function passo(s) table.insert(r.passos, string.format("%.1f %s", os.clock() - t0, s)) end
LogService.MessageOut:Connect(function(msg, tipo)
	if (tipo == Enum.MessageType.MessageError or tipo == Enum.MessageType.MessageWarning) and #r.logsServidor < 40 then
		table.insert(r.logsServidor, string.format("%.1f %s %s", os.clock() - t0, tipo.Name, string.sub(msg, 1, 300)))
	end
end)
local canal = Instance.new("RemoteEvent") canal.Name = "QA_MultiCanal" canal.Parent = RS
local qa = Instance.new("RemoteEvent") qa.Name = "QA_Channel" qa.Parent = RS -- ui-audit.client.luau da skill
local respostas = {}
canal.OnServerEvent:Connect(function(p, tag, info)
	if tag == "log" then
		if #r.logsCliente < 40 then table.insert(r.logsCliente, string.format("%.1f %s %s", os.clock() - t0, p.Name, tostring(info))) end
	else
		respostas[p.Name .. ":" .. tostring(tag)] = info
	end
end)
qa.OnServerEvent:Connect(function(p, tag, payload)
	table.insert(r.ui, { quem = p.Name, tag = tostring(tag), em = math.floor(os.clock() - t0), rel = payload })
end)
local Serv = game:GetService("ServerScriptService"):WaitForChild("Server"):WaitForChild("Servicos")
local Turno = require(Serv:WaitForChild("TurnoServico"))
local Sessao = require(Serv:WaitForChild("SessaoServico"))
local Fila = require(Serv:WaitForChild("FilaServico"))
local Cozinha = require(Serv:WaitForChild("CozinhaServico"))
local function ate(cond, lim) local f = os.clock() + lim while os.clock() < f do if cond() then return true end task.wait(0.25) end return cond() end
local encerrado = false
local function fim(motivo)
	if encerrado then return end
	encerrado = true
	r.motivo = motivo
	r.dt = os.clock() - t0
	passo("fim: " .. motivo)
	task.wait(0.5)
	STS:EndTest(Http:JSONEncode(r))
end
local function pedir(p, tag, extra, espera)
	respostas[p.Name .. ":" .. tag] = nil
	canal:FireClient(p, tag, extra)
	ate(function() return respostas[p.Name .. ":" .. tag] ~= nil end, espera or 8)
	return respostas[p.Name .. ":" .. tag]
end
local function relatorioTodos(rotulo)
	local t = {}
	for _, p in Players:GetPlayers() do t[p.Name] = pedir(p, "relatorio", nil, 6) end
	r.cli[rotulo] = t
end
local function papeis()
	local t = {}
	for _, p in Players:GetPlayers() do t[p.Name] = tostring(Sessao.papelDe(p)) .. "/" .. tostring(Sessao.postoDe(p)) end
	return t
end
local function snap(rotulo)
	local e = Turno.obter()
	r[rotulo] = { n = #Players:GetPlayers(), papeis = papeis(), modo = Sessao.modo(), estado = e.estado, turno = e.turno, tempo = e.tempoRestanteS, erros = e.errosTurno, vendas = e.vendasNoite, mao = table.concat(Cozinha.mao(), ","), inst = #game:GetDescendants() }
	passo(rotulo .. " " .. Http:JSONEncode(r[rotulo]))
end
task.delay(330, function() fim("tempo esgotado") end)
if not ate(function() return #Players:GetPlayers() >= n end, 90) then return fim("faltaram jogadores: " .. #Players:GetPlayers()) end
passo("jogadores: " .. #Players:GetPlayers())
snap("lobby")
if not ate(function() return Turno.obter().estado == "EmTurno" end, 120) then snap("travou") return fim("nao chegou ao EmTurno: " .. Turno.obter().estado) end
snap("emTurno")
task.wait(2)
relatorioTodos("inicioT1")
local coz, vig
for _, p in Players:GetPlayers() do
	local pp = Sessao.papelDe(p)
	if pp == "Cozinheiro" then coz = p elseif pp == "Vigia" then vig = p end
end
if not (coz and vig) then return fim("sem dupla Cozinheiro+Vigia: " .. Http:JSONEncode(papeis())) end
-- red-team pelo cliente Vigia (nao e cozinheiro): nada pode mudar na cozinha
local maoAntes = table.concat(Cozinha.mao(), ",")
r.seed = tonumber(string.match(tostring(args), "seed(%d+)")) or 0
local errosAntes = #r.logsServidor
r.redteamVigia = pedir(vig, "redteam", { seed = r.seed }, 25)
r.errosServidorNoRedteam = #r.logsServidor - errosAntes
task.wait(1)
r.redteamVigiaMao = { antes = maoAntes, depois = table.concat(Cozinha.mao(), ","), papeis = papeis(), modo = Sessao.modo() }
-- cozinheiro real: Caldo pelos remotes do cliente
r.caldo = pedir(coz, "caldo", nil, 20)
r.maoServidorAposCaldo = table.concat(Cozinha.mao(), ",")
-- fila compartilhada: os dois clientes veem o mesmo cliente na janelinha
local c
ate(function() c = Fila.clienteNaJanela() return c ~= nil end, 60)
r.clienteJanela = c and c.id
r.pedidoJanela = c and Http:JSONEncode(c.pedido)
task.wait(2)
relatorioTodos("comClienteNaJanela")
-- ui-audit da skill rodando nos 2 clientes durante o T1 (QA_UiTurno, DELAY_S curto disparado por comando)
for _, p in Players:GetPlayers() do canal:FireClient(p, "uiaudit") end
ate(function() local k = 0 for _, u in r.ui do if u.tag == "UI-AUDIT-TURNO" then k += 1 end end return k >= n end, 25)
-- cozinheiro atende o cliente da janela (Servir se o pedido for Caldo, senao Recusar)
if c then
	local dec = if string.find(r.pedidoJanela or "", "Caldo") and not string.find(r.pedidoJanela or "", "Pastel") then "Servir" else "Recusar"
	r.atendeu = { decisao = dec, resp = pedir(coz, "atender", { id = c.id, decisao = dec }, 8) }
	task.wait(1.5)
	snap("aposAtender")
end
-- saida do Vigia no meio do T1
passo("Kick " .. vig.Name)
vig:Kick("QA: parceiro saiu")
task.wait(3)
snap("aposKick")
relatorioTodos("aposKick")
fim("ok")
]])
mk("LocalScript", "QA_MultiCli", SPS, [[-- QA_MultiCli (temporario): responde aos comandos do QA_Multi pelos remotes reais do jogo
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
]])
mk("LocalScript", "QA_UiLobby", SPS, [[--!nocheck
--!nocheck
-- ui-audit.client.luau — CLIENT probe: walks the visible PlayerGui and reports layout findings as JSON.
-- Run it with the server collector:  studio-mcp.py run-pair ui-audit.client.luau qa-collect.server.luau
-- (or paste into the client-side command bar during Play and read Output).
-- It audits whatever screen is showing at DELAY_S; drive the game to the screen you want first (or edit
-- STATES below to call your own remotes). Detector hits are EVIDENCE, not proof: look at the screen before
-- closing or filing a finding, and fix false positives by improving the detector.
local CONFIG = {
	DELAY_S = 12, -- let the UI settle (loading screens, tweens)
	MIN_TEXT_PX = 12, -- floor in real pixels after UIScale/TextScaled; set from GAME-QA.md (phones: ~14)
	MIN_TARGET_PX = 44, -- smallest side of an Active button on TOUCH (TouchEnabled: phone/tablet/Device Emulator)
	MIN_MOUSE_TARGET_PX = 24, -- mouse-only client (Studio PC window): 44 is a touch rule; games often scale buttons up only on touch
	OVERLAP_PX = 4, -- interactive rectangles overlapping more than this on both axes
	MAX_REPORT = 30, -- per rule
	TAG = "UI-AUDIT-LOBBY", -- report tag (use one tag per screen, e.g. UI-AUDIT-LOBBY / UI-AUDIT-T1)
	CHANNEL_WAIT_S = 30, -- 0 = do not wait for QA_Channel (run directly with execute_luau datamodel_type=Client)
}
local Players = game:GetService("Players")
local GuiService = game:GetService("GuiService")
local UIS = game:GetService("UserInputService")
local HttpService = game:GetService("HttpService")
local RS = game:GetService("ReplicatedStorage")
local lp = Players.LocalPlayer
local pg = lp:WaitForChild("PlayerGui")
task.wait(CONFIG.DELAY_S)

local cam = workspace.CurrentCamera
local vp = cam.ViewportSize
local inset = GuiService:GetGuiInset()
local findings, counts = {}, {}
local function add(sev, rule, obj, detail)
	counts[rule] = (counts[rule] or 0) + 1
	if counts[rule] <= CONFIG.MAX_REPORT then
		local path = if typeof(obj) == "Instance" then obj:GetFullName():gsub("^.-PlayerGui%.", "") else tostring(obj)
		table.insert(findings, { sev = sev, rule = rule, path = path, detail = detail })
	end
end
local function visible(o)
	local a = o
	while a and a ~= pg do
		if a:IsA("GuiObject") and not a.Visible then
			return false
		end
		if a:IsA("LayerCollector") and not a.Enabled then
			return false
		end
		a = a.Parent
	end
	return true
end
local function scaleOf(o)
	local s, a = 1, o
	while a and a ~= pg do
		local u = a:FindFirstChildOfClass("UIScale")
		if u then
			s *= u.Scale
		end
		a = a.Parent
	end
	return s
end
local function rect(o, sg)
	-- screen coordinates. AbsolutePosition is measured from the ScreenGui's own origin, and current Studio puts
	-- an IgnoreGuiInset gui's origin at (0, -inset.Y) (a full-screen frame reads y = -58 there). Subtract the
	-- gui's origin and add where that gui really starts on screen, so both old and new engine behaviour work.
	local p, s = o.AbsolutePosition, o.AbsoluteSize
	local o0 = sg.AbsolutePosition
	local top = if sg.IgnoreGuiInset then 0 else inset.Y
	return p.X - o0.X, p.Y - o0.Y + top, s.X, s.Y
end
local function overlap(a, b)
	local ix = math.min(a[1] + a[3], b[1] + b[3]) - math.max(a[1], b[1])
	local iy = math.min(a[2] + a[4], b[2] + b[4]) - math.max(a[2], b[2])
	return ix > CONFIG.OVERLAP_PX and iy > CONFIG.OVERLAP_PX
end

-- mobile control zones: real TouchGui frames when present, else the default corners
local zones = {}
local tg = pg:FindFirstChild("TouchGui")
if tg and tg.Enabled then
	for _, o in tg:GetDescendants() do
		if
			o:IsA("GuiObject")
			and visible(o)
			and (o.Name:find("Jump") or o.Name:find("Thumbstick") or o.Name:find("DynamicThumbstick"))
		then
			local x, y, w, h = rect(o, tg)
			if w > 10 and h > 10 then
				table.insert(zones, { x, y, w, h, o.Name })
			end
		end
	end
end
-- TouchGui present but no visible Jump/Thumbstick = the game disabled the character controls (ControlModule:Disable):
-- nothing to overlap. The default corners are only a guess for when the TouchGui was not created yet.
if #zones == 0 and UIS.TouchEnabled and not tg then
	local s = math.min(vp.X, vp.Y)
	table.insert(zones, { 0, vp.Y - s * 0.45, s * 0.45, s * 0.45, "thumbstick(default)" })
	table.insert(zones, { vp.X - s * 0.3, vp.Y - s * 0.3, s * 0.3, s * 0.3, "jump(default)" })
end

local buttons, nVisible, minText, minTarget = {}, 0, math.huge, math.huge
local floorTarget = if UIS.TouchEnabled then CONFIG.MIN_TARGET_PX else CONFIG.MIN_MOUSE_TARGET_PX
for _, sg in pg:GetChildren() do
	if sg:IsA("ScreenGui") and sg.Enabled and sg ~= tg and sg.Name ~= "Freecam" then
		if sg.ScreenInsets ~= Enum.ScreenInsets.CoreUISafeInsets and not sg.IgnoreGuiInset then
			add(
				"P2",
				"screen-insets",
				sg,
				"ScreenInsets=" .. sg.ScreenInsets.Name .. " (HUD/buttons should use CoreUISafeInsets)"
			)
		end
		for _, o in sg:GetDescendants() do
			if o:IsA("GuiObject") and visible(o) and o.AbsoluteSize.X > 1 and o.AbsoluteSize.Y > 1 then
				nVisible += 1
				local x, y, w, h = rect(o, sg)
				local clipped = o:FindFirstAncestorWhichIsA("ScrollingFrame") ~= nil
				if not clipped and (x < -2 or y < -2 or x + w > vp.X + 2 or y + h > vp.Y + 2) then
					add(
						"P1",
						"off-screen",
						o,
						string.format("rect (%d,%d %dx%d) viewport %dx%d", x, y, w, h, vp.X, vp.Y)
					)
				end
				if
					(o:IsA("TextLabel") or o:IsA("TextButton") or o:IsA("TextBox"))
					and o.Text ~= ""
					and o.TextTransparency < 0.9
				then
					local px = if o.TextScaled
						then o.TextBounds.Y / math.max(1, #o.Text:split("\n"))
						else o.TextSize * scaleOf(o)
					minText = math.min(minText, px)
					if px < CONFIG.MIN_TEXT_PX then
						add(
							"P2",
							"small-text",
							o,
							string.format("%.1f px < %d: '%s'", px, CONFIG.MIN_TEXT_PX, o.Text:sub(1, 40))
						)
					end
					if utf8.len(o.Text) then
						for _, c in utf8.codes(o.Text) do
							if c >= 0x1F000 or (c >= 0x2600 and c <= 0x27BF) then
								add(
									"P3",
									"emoji-glyph",
									o,
									string.format("U+%X may render as a box on some platforms", c)
								)
								break
							end
						end
					end
					if UIS.TouchEnabled and not UIS.KeyboardEnabled then
						local t = o.Text:upper()
						if t:find("PRESS [A-Z]") or t:find("%[[A-Z]%]") or t:find("CLICK") then
							add("P2", "keyboard-hint-on-touch", o, "'" .. o.Text:sub(1, 40) .. "'")
						end
					end
				end
				if o:IsA("GuiButton") and o.Active then
					local m = math.min(w, h)
					minTarget = math.min(minTarget, m)
					if m < floorTarget then
						add("P2", "small-target", o, string.format("%dx%d px < %d", w, h, floorTarget))
					end
					table.insert(buttons, { o = o, r = { x, y, w, h }, sg = sg })
					for _, z in zones do
						if overlap({ x, y, w, h }, z) then
							add("P1", "touch-zone", o, "overlaps " .. z[5])
						end
					end
				elseif
					o:IsA("GuiObject")
					and o.Active
					and o.BackgroundTransparency >= 0.99
					and w * h > vp.X * vp.Y * 0.4
				then
					add(
						"P2",
						"invisible-blocker",
						o,
						string.format(
							"transparent Active %s covers %d%% of the screen",
							o.ClassName,
							math.floor(100 * w * h / (vp.X * vp.Y))
						)
					)
				end
			elseif o:IsA("GuiButton") and o.Modal and not visible(o) then
				add("P1", "hidden-modal", o, "Modal=true on a hidden button keeps capturing input/mouse")
			end
		end
	end
end
for i = 1, #buttons do
	for j = i + 1, #buttons do
		local a, b = buttons[i], buttons[j]
		if a.sg == b.sg and not a.o:IsDescendantOf(b.o) and not b.o:IsDescendantOf(a.o) and overlap(a.r, b.r) then
			add("P1", "overlap", a.o, "overlaps " .. b.o:GetFullName():gsub("^.-PlayerGui%.", ""))
		end
	end
end

local report = HttpService:JSONEncode({
	viewport = { vp.X, vp.Y },
	inset = { inset.X, inset.Y },
	input = { touch = UIS.TouchEnabled, keyboard = UIS.KeyboardEnabled, gamepad = UIS.GamepadEnabled },
	visible = nVisible,
	buttons = #buttons,
	minTextPx = if minText == math.huge then nil else math.floor(minText * 10) / 10,
	minTargetPx = if minTarget == math.huge then nil else math.floor(minTarget * 10) / 10,
	targetFloorPx = floorTarget,
	counts = counts,
	findings = findings,
})
local ch = if CONFIG.CHANNEL_WAIT_S > 0
	then RS:WaitForChild("QA_Channel", CONFIG.CHANNEL_WAIT_S)
	else RS:FindFirstChild("QA_Channel")
if ch then
	ch:FireServer(CONFIG.TAG, report)
end
print("[qa] " .. CONFIG.TAG .. " " .. report)
return report -- execute_luau (built-in StudioMCP) returns this string directly
]])
mk("LocalScript", "QA_UiTurno", SPS, [[--!nocheck
--!nocheck
-- ui-audit.client.luau — CLIENT probe: walks the visible PlayerGui and reports layout findings as JSON.
-- Run it with the server collector:  studio-mcp.py run-pair ui-audit.client.luau qa-collect.server.luau
-- (or paste into the client-side command bar during Play and read Output).
-- It audits whatever screen is showing at DELAY_S; drive the game to the screen you want first (or edit
-- STATES below to call your own remotes). Detector hits are EVIDENCE, not proof: look at the screen before
-- closing or filing a finding, and fix false positives by improving the detector.
local CONFIG = {
	DELAY_S = 50, -- let the UI settle (loading screens, tweens)
	MIN_TEXT_PX = 12, -- floor in real pixels after UIScale/TextScaled; set from GAME-QA.md (phones: ~14)
	MIN_TARGET_PX = 44, -- smallest side of an Active button on TOUCH (TouchEnabled: phone/tablet/Device Emulator)
	MIN_MOUSE_TARGET_PX = 24, -- mouse-only client (Studio PC window): 44 is a touch rule; games often scale buttons up only on touch
	OVERLAP_PX = 4, -- interactive rectangles overlapping more than this on both axes
	MAX_REPORT = 30, -- per rule
	TAG = "UI-AUDIT-TURNO", -- report tag (use one tag per screen, e.g. UI-AUDIT-LOBBY / UI-AUDIT-T1)
	CHANNEL_WAIT_S = 30, -- 0 = do not wait for QA_Channel (run directly with execute_luau datamodel_type=Client)
}
local Players = game:GetService("Players")
local GuiService = game:GetService("GuiService")
local UIS = game:GetService("UserInputService")
local HttpService = game:GetService("HttpService")
local RS = game:GetService("ReplicatedStorage")
local lp = Players.LocalPlayer
local pg = lp:WaitForChild("PlayerGui")
task.wait(CONFIG.DELAY_S)

local cam = workspace.CurrentCamera
local vp = cam.ViewportSize
local inset = GuiService:GetGuiInset()
local findings, counts = {}, {}
local function add(sev, rule, obj, detail)
	counts[rule] = (counts[rule] or 0) + 1
	if counts[rule] <= CONFIG.MAX_REPORT then
		local path = if typeof(obj) == "Instance" then obj:GetFullName():gsub("^.-PlayerGui%.", "") else tostring(obj)
		table.insert(findings, { sev = sev, rule = rule, path = path, detail = detail })
	end
end
local function visible(o)
	local a = o
	while a and a ~= pg do
		if a:IsA("GuiObject") and not a.Visible then
			return false
		end
		if a:IsA("LayerCollector") and not a.Enabled then
			return false
		end
		a = a.Parent
	end
	return true
end
local function scaleOf(o)
	local s, a = 1, o
	while a and a ~= pg do
		local u = a:FindFirstChildOfClass("UIScale")
		if u then
			s *= u.Scale
		end
		a = a.Parent
	end
	return s
end
local function rect(o, sg)
	-- screen coordinates. AbsolutePosition is measured from the ScreenGui's own origin, and current Studio puts
	-- an IgnoreGuiInset gui's origin at (0, -inset.Y) (a full-screen frame reads y = -58 there). Subtract the
	-- gui's origin and add where that gui really starts on screen, so both old and new engine behaviour work.
	local p, s = o.AbsolutePosition, o.AbsoluteSize
	local o0 = sg.AbsolutePosition
	local top = if sg.IgnoreGuiInset then 0 else inset.Y
	return p.X - o0.X, p.Y - o0.Y + top, s.X, s.Y
end
local function overlap(a, b)
	local ix = math.min(a[1] + a[3], b[1] + b[3]) - math.max(a[1], b[1])
	local iy = math.min(a[2] + a[4], b[2] + b[4]) - math.max(a[2], b[2])
	return ix > CONFIG.OVERLAP_PX and iy > CONFIG.OVERLAP_PX
end

-- mobile control zones: real TouchGui frames when present, else the default corners
local zones = {}
local tg = pg:FindFirstChild("TouchGui")
if tg and tg.Enabled then
	for _, o in tg:GetDescendants() do
		if
			o:IsA("GuiObject")
			and visible(o)
			and (o.Name:find("Jump") or o.Name:find("Thumbstick") or o.Name:find("DynamicThumbstick"))
		then
			local x, y, w, h = rect(o, tg)
			if w > 10 and h > 10 then
				table.insert(zones, { x, y, w, h, o.Name })
			end
		end
	end
end
-- TouchGui present but no visible Jump/Thumbstick = the game disabled the character controls (ControlModule:Disable):
-- nothing to overlap. The default corners are only a guess for when the TouchGui was not created yet.
if #zones == 0 and UIS.TouchEnabled and not tg then
	local s = math.min(vp.X, vp.Y)
	table.insert(zones, { 0, vp.Y - s * 0.45, s * 0.45, s * 0.45, "thumbstick(default)" })
	table.insert(zones, { vp.X - s * 0.3, vp.Y - s * 0.3, s * 0.3, s * 0.3, "jump(default)" })
end

local buttons, nVisible, minText, minTarget = {}, 0, math.huge, math.huge
local floorTarget = if UIS.TouchEnabled then CONFIG.MIN_TARGET_PX else CONFIG.MIN_MOUSE_TARGET_PX
for _, sg in pg:GetChildren() do
	if sg:IsA("ScreenGui") and sg.Enabled and sg ~= tg and sg.Name ~= "Freecam" then
		if sg.ScreenInsets ~= Enum.ScreenInsets.CoreUISafeInsets and not sg.IgnoreGuiInset then
			add(
				"P2",
				"screen-insets",
				sg,
				"ScreenInsets=" .. sg.ScreenInsets.Name .. " (HUD/buttons should use CoreUISafeInsets)"
			)
		end
		for _, o in sg:GetDescendants() do
			if o:IsA("GuiObject") and visible(o) and o.AbsoluteSize.X > 1 and o.AbsoluteSize.Y > 1 then
				nVisible += 1
				local x, y, w, h = rect(o, sg)
				local clipped = o:FindFirstAncestorWhichIsA("ScrollingFrame") ~= nil
				if not clipped and (x < -2 or y < -2 or x + w > vp.X + 2 or y + h > vp.Y + 2) then
					add(
						"P1",
						"off-screen",
						o,
						string.format("rect (%d,%d %dx%d) viewport %dx%d", x, y, w, h, vp.X, vp.Y)
					)
				end
				if
					(o:IsA("TextLabel") or o:IsA("TextButton") or o:IsA("TextBox"))
					and o.Text ~= ""
					and o.TextTransparency < 0.9
				then
					local px = if o.TextScaled
						then o.TextBounds.Y / math.max(1, #o.Text:split("\n"))
						else o.TextSize * scaleOf(o)
					minText = math.min(minText, px)
					if px < CONFIG.MIN_TEXT_PX then
						add(
							"P2",
							"small-text",
							o,
							string.format("%.1f px < %d: '%s'", px, CONFIG.MIN_TEXT_PX, o.Text:sub(1, 40))
						)
					end
					if utf8.len(o.Text) then
						for _, c in utf8.codes(o.Text) do
							if c >= 0x1F000 or (c >= 0x2600 and c <= 0x27BF) then
								add(
									"P3",
									"emoji-glyph",
									o,
									string.format("U+%X may render as a box on some platforms", c)
								)
								break
							end
						end
					end
					if UIS.TouchEnabled and not UIS.KeyboardEnabled then
						local t = o.Text:upper()
						if t:find("PRESS [A-Z]") or t:find("%[[A-Z]%]") or t:find("CLICK") then
							add("P2", "keyboard-hint-on-touch", o, "'" .. o.Text:sub(1, 40) .. "'")
						end
					end
				end
				if o:IsA("GuiButton") and o.Active then
					local m = math.min(w, h)
					minTarget = math.min(minTarget, m)
					if m < floorTarget then
						add("P2", "small-target", o, string.format("%dx%d px < %d", w, h, floorTarget))
					end
					table.insert(buttons, { o = o, r = { x, y, w, h }, sg = sg })
					for _, z in zones do
						if overlap({ x, y, w, h }, z) then
							add("P1", "touch-zone", o, "overlaps " .. z[5])
						end
					end
				elseif
					o:IsA("GuiObject")
					and o.Active
					and o.BackgroundTransparency >= 0.99
					and w * h > vp.X * vp.Y * 0.4
				then
					add(
						"P2",
						"invisible-blocker",
						o,
						string.format(
							"transparent Active %s covers %d%% of the screen",
							o.ClassName,
							math.floor(100 * w * h / (vp.X * vp.Y))
						)
					)
				end
			elseif o:IsA("GuiButton") and o.Modal and not visible(o) then
				add("P1", "hidden-modal", o, "Modal=true on a hidden button keeps capturing input/mouse")
			end
		end
	end
end
for i = 1, #buttons do
	for j = i + 1, #buttons do
		local a, b = buttons[i], buttons[j]
		if a.sg == b.sg and not a.o:IsDescendantOf(b.o) and not b.o:IsDescendantOf(a.o) and overlap(a.r, b.r) then
			add("P1", "overlap", a.o, "overlaps " .. b.o:GetFullName():gsub("^.-PlayerGui%.", ""))
		end
	end
end

local report = HttpService:JSONEncode({
	viewport = { vp.X, vp.Y },
	inset = { inset.X, inset.Y },
	input = { touch = UIS.TouchEnabled, keyboard = UIS.KeyboardEnabled, gamepad = UIS.GamepadEnabled },
	visible = nVisible,
	buttons = #buttons,
	minTextPx = if minText == math.huge then nil else math.floor(minText * 10) / 10,
	minTargetPx = if minTarget == math.huge then nil else math.floor(minTarget * 10) / 10,
	targetFloorPx = floorTarget,
	counts = counts,
	findings = findings,
})
local ch = if CONFIG.CHANNEL_WAIT_S > 0
	then RS:WaitForChild("QA_Channel", CONFIG.CHANNEL_WAIT_S)
	else RS:FindFirstChild("QA_Channel")
if ch then
	ch:FireServer(CONFIG.TAG, report)
end
print("[qa] " .. CONFIG.TAG .. " " .. report)
return report -- execute_luau (built-in StudioMCP) returns this string directly
]])
_G.QA_MT = "rodando" workspace:SetAttribute("QA_MT", "rodando")
task.spawn(function()
	local ok, res = pcall(function() return game:GetService("StudioTestService"):ExecuteMultiplayerTestAsync(__N__, "__ARG__") end)
	_G.QA_MT = (ok and "FIM RESULTADO " or "FIM ERRO ") .. tostring(res)
	pcall(function() workspace:SetAttribute("QA_MT", _G.QA_MT) end)
end)
return "inserido; teste com __N__ clientes disparado"
