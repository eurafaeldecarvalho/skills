# QA no PC Windows do Rafael (DESKTOP-UEOVLLP)

Validado em 2026-10-30 (Turno da Madrugada, Studio 0.745). Vale para qualquer jogo do Rafael (Turno da Madrugada,
Trenó às Cegas, Cópia da Cópia…). O box não roda Studio; o PC roda.

## Regras (todas obrigatórias)
- **Teste multiplayer REAL é obrigatório** sempre que o QA rodar neste PC: *Server & Clients* com **2+ clientes**
  (e 3 se o jogo tiver espectador/fila), saída de um jogador no meio da rodada e red-team pelo cliente. Sem isso o QA
  no PC está incompleto — não troque por Play solo nem por teste headless.
- Só o place **LOCAL** gerado pelo Rojo. Nunca abra/edite/publique o place ao vivo (Team Create), nem mexa na página
  da loja, acesso ou Robux.
- Um Studio de teste **seu**, aberto em `C:\Users\Rafael\turno-qa\<pkg>\<jogo>.rbxlx`. Não toque no Studio original
  do Rafael (título "Roblox Studio"), no RobloxPlayerBeta dele, nem na janela do Grok Bot. Ao fim, feche só o seu
  Studio pelo PID **e confira o título** antes do `Stop-Process` (fechar sem salvar).
- Cada comando no PC pede aprovação: **junte tudo num comando só** (extrair tar → rodar lote MCP → copiar capturas →
  empacotar resultado).
- `CopyToBox` só **depois** que o Shell que gera o arquivo terminou (em paralelo ele não acha o arquivo).
- Antes de qualquer clique com pyautogui: foque a janela e tire screenshot; prefira MCP a cliques. Nunca digite senha.
- Uma instância de servidor MCP por vez.

## Layout em `C:\Users\Rafael\turno-qa`
| Caminho | O quê |
|---|---|
| `rojo.exe` | build do place no PC (ou gere o .rbxlx no box com `rojo build` e copie) |
| `rbx-studio-mcp.exe` | servidor MCP open-source (alternativa; o embutido funcionou melhor) |
| `pcpkg\<jogo>.rbxlx` | place local de teste (o Turno usa `pcpkg\turno.rbxlx`) — use um `pcpkg-<jogo>` por jogo |
| `pcpkg\win.py` | `focus "<título>" [max]`, `shot x.png`, `click x y`, `key k`, `titles` (pyautogui; ignora janelas "grok") |
| `pcpkg\qa\` | `studio-mcp.py`, sondas `.luau` e lotes `.json` (este diretório da skill: `scripts/windows-pc/`) |
| `C:\Python314\python.exe` | Python com pyautogui/pygetwindow |

Fluxo: no box, monte `pcpkg/qa/` (scripts da skill + sondas do jogo) → `tar` → `CopyFromBox` para
`C:\Users\Rafael\turno-qa\` → no PC, um comando: `tar -xf`, rodar o lote, empacotar `res.tar` → `CopyToBox`.

## Servidor MCP que funciona: o embutido do Studio
- Ligue o botão **"MCP"** na barra de status do Studio (fica "MCP · 1"/"MCP Ready").
- PowerShell:
  ```
  $env:PYTHONIOENCODING='utf-8'
  $env:STUDIO_MCP_CMD='["C:\\Users\\Rafael\\AppData\\Local\\Roblox\\Versions\\version-<hash>\\StudioMCP.exe"]'
  cd C:\Users\Rafael\turno-qa\pcpkg\qa
  C:\Python314\python.exe studio-mcp.py --studio turno.rbxlx --out X.out.json batch X.json > X.log 2> X.err
  ```
  (o `version-<hash>` muda a cada atualização do Studio: `dir $env:LOCALAPPDATA\Roblox\Versions\*\StudioMCP.exe`).
- `--studio` escolhe a janela pelo título; `list_roblox_studios` precisa de polling (o script já faz).
- Caminhos `"luau": "x.luau"` no lote são relativos ao diretório atual. Itens de lote aceitam `dm` (Edit/Server/Client),
  `sub` (substituições de texto), `until`/`every`/`max` (polling) e `{"sleep": s}`.
- `screen_capture` salva em `%TEMP%\studio-mcp-*.png` — copie para o pacote de resultado.

## Pegadinhas
- `require()` num `execute_luau` dm=Server devolve **uma cópia nova** do módulo (estado vazio). Para ler estado do
  jogo, insira um Script (QA_*) ou peça pelo cliente via remote.
- Algumas propriedades exigem `pcall` (ex.: `Lighting.Technology` → "sem acesso").
- Place local não publicado: o CoreGui loga "Invalid value for enum CreatorType" (PlayerList/TopBar). É ruído do motor.
- **Corrigir sem reabrir:** `execute_luau` dm=Edit com `m.Source = [===[…]===]` aplica o módulo corrigido no Studio
  aberto (`patch_source.example.luau`). Não salve; reconstrua o .rbxlx para a rodada seguinte.
- Max Players do place ao vivo não aparece na API pública se o jogo for privado → Blocked, pergunte ao Rafael.

## Teste multiplayer (Server & Clients) via MCP — padrão mt_ins / multi_srv / multi_cli / mt_poll / mt_rem
`StudioTestService:ExecuteMultiplayerTestAsync(n, args)` disparado do **Edit** funciona e abre servidor + n clientes.
- `mt_ins.luau` (dm=Edit, `sub: {"__N__": "2", "__ARG__": "2 dois seed4101"}` — args = `"<n> <rótulo> seed<s>"`; troque a seed a cada iteração para o macaco do red-team ser novo): apaga sobras QA_*, insere `QA_Multi` (Script no
  ServerScriptService = `multi_srv.luau`), `QA_MultiCli` (LocalScript = `multi_cli.luau`) e as sondas de UI, e dispara o
  teste em `task.spawn`, gravando o resultado em `workspace:GetAttribute("QA_MT")`.
- `multi_srv.luau`: espera os n jogadores, orquestra os clientes por um RemoteEvent `QA_MultiCanal`
  (pedidos "relatorio", "redteam", ações reais do jogo, "uiaudit"), executa o roteiro (lobby → turno → ação real →
  red-team → kick de um jogador no meio) e chama `STS:EndTest(resultado)`.
- `multi_cli.luau`: responde aos pedidos usando os **remotes reais** do jogo e devolve papel/estado/logs do cliente.
- `mt_poll.luau` (until `"FIM "`, every 10, max 420) e `mt_rem.luau` (remove tudo QA_* e confere 0 restos).
- Lotes de exemplo: `b2_multi2.json` (2 clientes), `b3_multi3.json` (3 clientes). Os nomes de papéis/remotes são do
  Turno — adapte `multi_srv`/`multi_cli` (e regenere `mt_ins`) para cada jogo.
- Durante o teste, `win.py shot` após ~40 s captura as janelas dos clientes (evidência visual por cliente).
- Mínimo por jogo: 2 clientes jogando a ação principal pelos remotes reais, estado igual nos dois, red-team pelo
  cliente sem privilégio, um jogador sai no meio da rodada (kick) e o outro continua; 3 clientes se houver espectador.

## Device Simulator (toque emulado)
Foco no Studio de teste → screenshot → menu **Teste** (barra superior) → **Device Simulator** → escolha o aparelho
no seletor do topo da viewport (ex.: iPhone XR). Depois rode `start_stop_play` + `ui_direct.luau`/`cli_perf.luau` com
dm=Client (lote `b7_xr.json`): `input.touch` deve ser `true` e `targetFloorPx` 44. Continua sendo **emulador** (teto 3).

### Lições da iteração 2 no PC (2026-10-30)
- O Device Simulator ligado **persiste** entre sessões do Studio: os clientes do Server & Clients nascem em toque 801×413. Bom para auditar todos os papéis no celular (foi assim que apareceu um P2 de texto do Manual do Vigia), mas desligue de novo no fim (Teste → Device Simulator) e confira o viewport do solo no mouse.
- `touch-zone` contra os cantos "default" é falso positivo quando o jogo chama `Controls:Disable()`: o TouchGui existe mas sem Jump/Thumbstick visíveis. O ui-audit agora só usa os cantos padrão sem TouchGui; o `multi_cli` reporta `toqueVisiveis` por cliente para confirmar.
- O red-team do `multi_cli` agora inclui um macaco com seed (120 `FireServer` aleatórios em todos os RemoteEvents com argumentos hostis); `multi_srv` devolve `errosServidorNoRedteam`.
