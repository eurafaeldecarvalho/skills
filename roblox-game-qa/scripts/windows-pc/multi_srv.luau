-- QA_Multi (temporario): Server & Clients com N clientes; orquestra os clientes pelo QA_MultiCanal e encerra com EndTest
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
