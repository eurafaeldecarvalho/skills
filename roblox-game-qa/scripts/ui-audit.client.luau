--!nocheck
-- ui-audit.client.luau — CLIENT probe: walks the visible PlayerGui and reports layout findings as JSON.
-- Run it with the server collector:  studio-mcp.py run-pair ui-audit.client.luau qa-collect.server.luau
-- (or paste into the client-side command bar during Play and read Output).
-- It audits whatever screen is showing at DELAY_S; drive the game to the screen you want first (or edit
-- STATES below to call your own remotes). Detector hits are EVIDENCE, not proof: look at the screen before
-- closing or filing a finding, and fix false positives by improving the detector.
local CONFIG = {
	DELAY_S = 8, -- let the UI settle (loading screens, tweens)
	MIN_TEXT_PX = 12, -- floor in real pixels after UIScale/TextScaled; set from GAME-QA.md (phones: ~14)
	MIN_TARGET_PX = 44, -- smallest side of an Active button on TOUCH (TouchEnabled: phone/tablet/Device Emulator)
	MIN_MOUSE_TARGET_PX = 24, -- mouse-only client (Studio PC window): 44 is a touch rule; games often scale buttons up only on touch
	OVERLAP_PX = 4, -- interactive rectangles overlapping more than this on both axes
	MAX_REPORT = 30, -- per rule
	TAG = "UI-AUDIT", -- report tag (use one tag per screen, e.g. UI-AUDIT-LOBBY / UI-AUDIT-T1)
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
