# Changes

Update history for **Emoji Cherry Pick**.

## current

* new: options `--ignore-skin` and `--no-ignore-skin` to ignore emoji skin
  color variations when creating the cache, default behavior was to ignore
  and exclude other colors than base (thanks contribution from dotcs)

## v0.2 - April 5, 2022

* new: CLI engine `fzf` at option `--mode`, also related option `--filter`
  causes to use `fzf` like a non interactive filter
* new: CLI engine `pmenu` at option `--mode`, similar to dmenu but for the
  terminal
* changed: does not hide stderr stream of called programs
* new: environmental variable `EMOJICHERRYPICK_DEFAULT` used as default
  commandline arguments if the program is run without options, defaults itself
  to `-con` if the variable is not set
* new: option `--list-programs` to list name and path of required and optional
  programs
* new: options `--rofi`, `--dmenu`, `--pmenu`, `--fzf`, `--xclip`, `--xdotool`
  and `--notifysend` to change the name or path of program to be used
* changed: fails silently on failing programs, but sets shell exitcode
  accordingly (0=success), added a few checks to detect failure

## v0.1 - April 3, 2022

* Initial release.

