-- Funk Master: theme-scoped styling, restored by ordinary theme switching.
local border = { colors = {
  "rgba(d6ff62ff)", "rgba(ff67beff)", "rgba(ff9b54ff)"
}, angle = 45 }

hl.config({
  general = {
    gaps_in = 7, gaps_out = 16, border_size = 3,
    col = { active_border = border, inactive_border = "rgba(684574cc)" },
  },
  decoration = {
    rounding = 20,
    shadow = { enabled = true, range = 18, render_power = 3, color = "rgba(100916aa)" },
    blur = { enabled = true, size = 3, passes = 1 },
  },
  group = {
    col = { border_active = border, border_inactive = "rgba(684574cc)" },
    groupbar = { height = 26, gradient_rounding = 12,
      text_color = "rgb(fff0d0)", text_color_inactive = "rgb(b29dba)" },
  },
})

hl.curve("funkGlide", { type = "bezier", points = { { 0.18, 0.9 }, { 0.3, 1 } } })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 3.2, bezier = "funkGlide", style = "popin 92%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 2, bezier = "funkGlide", style = "popin 96%" })
hl.animation({ leaf = "border", enabled = true, speed = 3, bezier = "funkGlide" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 3, bezier = "funkGlide", style = "slide" })
