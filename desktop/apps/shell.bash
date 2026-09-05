# Funk Master shell colors. Source after Omarchy's normal shell initialization.
# Preserve the incoming status so Starship still displays failed commands.
if [[ ${_funk_shell_loaded:-} != 1 ]]; then
  _funk_shell_loaded=1
  declare -A _funk_original _funk_present
  for _funk_key in STARSHIP_CONFIG LS_COLORS EZA_COLORS FZF_DEFAULT_OPTS LG_CONFIG_FILE; do
    if [[ -v $_funk_key ]]; then
      _funk_present[$_funk_key]=1
      _funk_original[$_funk_key]=${!_funk_key}
    fi
  done
  unset _funk_key

  _funk_sync() {
    local previous_status=$? theme_name="" name
    [[ -r "$HOME/.local/state/omarchy/current/theme.name" ]] &&
      IFS= read -r theme_name < "$HOME/.local/state/omarchy/current/theme.name"
    [[ -d "$HOME/.config/omarchy/funk-apps" ]] || theme_name=""
    if [[ $theme_name == "${_funk_last_theme:-}" ]]; then return "$previous_status"; fi
    _funk_last_theme=$theme_name
    if [[ $theme_name == funk-master && -d "$HOME/.config/omarchy/funk-apps" ]]; then
      export STARSHIP_CONFIG="$HOME/.config/omarchy/funk-apps/starship.toml"
      export LS_COLORS="${_funk_original[LS_COLORS]:-}:di=1;38;2;255;103;190:ln=38;2;116;233;223:ex=1;38;2;214;255;98:*.md=38;2;255;226;121:*.toml=38;2;198;154;255:*.py=38;2;255;155;84:*.js=38;2;255;155;84:*.png=38;2;255;103;190:*.mp4=38;2;255;103;190"
      export EZA_COLORS="${_funk_original[EZA_COLORS]:-}:di=1;38;2;255;103;190:ex=1;38;2;214;255;98:ln=38;2;116;233;223"
      export FZF_DEFAULT_OPTS="${_funk_original[FZF_DEFAULT_OPTS]:-} --color=bg:#211329,bg+:#57335F,fg:#FFF0D0,fg+:#FFF0D0,hl:#FF67BE,hl+:#D6FF62,pointer:#D6FF62,marker:#FF9B54,prompt:#D6FF62,info:#C69AFF,border:#684574,header:#74E9DF"
      export LG_CONFIG_FILE="${_funk_original[LG_CONFIG_FILE]:-$HOME/.config/lazygit/config.yml},$HOME/.config/omarchy/funk-apps/lazygit.yml"
    else
      for name in STARSHIP_CONFIG LS_COLORS EZA_COLORS FZF_DEFAULT_OPTS LG_CONFIG_FILE; do
        if [[ ${_funk_present[$name]:-} == 1 ]]; then
          printf -v "$name" '%s' "${_funk_original[$name]}"
          export "$name"
        else
          unset "$name"
        fi
      done
    fi
    return "$previous_status"
  }
  PROMPT_COMMAND=(_funk_sync "${PROMPT_COMMAND[@]}")
fi
_funk_sync
