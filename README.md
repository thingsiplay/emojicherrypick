# "🍒⛏️" Emoji Cherry Pick

Choose an emoji and go wild.

* Author: Tuncay D.
* Source: https://github.com/thingsiplay/emojicherrypick
* Releases: https://github.com/thingsiplay/emojicherrypick/releases
* Update Notes: [CHANGES](CHANGES.md)
* License: [MIT License](MIT License)

# Introduction

Are you tired of the preinstalled emoji tools that come or does not come with
your distribution? Me neither; here is it anyway.

![default](default.webp) ![bigfavorits](bigfavorites.webp)

(Note: The screenshots show you my personal setup of `rofi`.)

This is a commandline driven frontend and launcher to several established Linux
applications, such as `rofi` and `xclip`. The default behavior is to open a
`rofi` search menu to choose an emoji, that is then copied to clipboard, print
to stdout and show a notification of chosen emoji.

## Features

You can...

* copy emoji to clipboard,
* print emoji to stdout,
* simulate typing emoji to current window,
* show notification of chosen emoji,
* use a `rofi` menu to choose emoji,
* use alternative filter algorithm for `rofi` search, such as "regex" or "glob",
* use `dmenu` instead `rofi`,
* choose emoji randomly without a menu (think of the possibilities),
* create a favorites file with your favorite emojis (requires manual text
  editing),
* keeps track of recently used emojis,
* disable main emoji database and list favorites and recent emojis only,
* ... and more.

# Requirements

This program is a Python 3.10 script written for Linux using X11. The below
listed external tools are not stricly required to run this program. But they
are required (for obvious reasons) the moment their functionality are being
used.

### Dependencies

* `rofi` - the default active menu, only required when option `--menu` is set to
  `rofi` (default)
* `dmenu` - alternative menu, only required if `--menu` is set to `dmenu`
* `xclip` - used to copy to clipboard, required if option `--clipboard` is
  enabled 
* `xdotool` - used to simulate typing on keyboard, required if option `--typing`
  is enabled
* `notify-send` - used to create notifications, required if option `--notify`
  is enabled (in Manjaro provided with package `libnotify`)

You only need those components which are being used.

The default font "*Noto Color Emoji*" can be changed, but if you are going to
leave and use it, you will need following packages:

* `noto-fonts-emoji` (on Arch, Manjaro)
* `fonts-noto-color-emoji` (on Debian, Ubuntu)

Single command to install all in one go on Manjaro:

`pamac install rofi dmenu xclip xdotool libnotify noto-fonts-emoji`

# Installation

The program itself does not require any special installation process, other
than the required programs and font. Run the script from any directory you
want. Give it the executable bit, rename the script to exclude file extension
and put it into a folder that is in the systems `$PATH` . An installation
script "install.sh" is provided, but not required. I recommend to assign a
keyboard shortcut to run the program for quick access.

It is a Python 3.10 script, so therefore it requires a decent Python version on
the system. If you have an older Python version, then you might want to check
the binary [release](https://github.com/thingsiplay/emojicherrypick/releases)
package, which bundles up the script and Python interpreter to create a
standalone executable.

## Optional: Makefile and PyInstaller (you can ignore this part)

The included "Makefile" is to build the package with the standalone binary. It
will create a venv, update stuff in it and run PyInstaller from it.

# Usage

```
usage: emojicherrypick [options]
```

On first run a small database with all emojis included will be downloaded and
prepaired for further usage. This is a process that takes probably just a
second and is needed only once (unless the file "emojis.json" already exists).
The program has a lot of options that you can use from the commandline in a
terminal or a script. Normally the program won't output your selected emoji,
unless you tell it to. But the selection will be saved in a history file, which
will be shown in the menu next time.

*Default*: If no commandline options are given to the program, then defaults
`-c -o -n` are in effect, to output emoji at stdout, save it to clipboard and
make a notification. Have in mind, the moment you are activating any option
manually like `-i` (short for `--ignore-case`), then no default options are in
effect anymore and you need to activate output manually.

Use `emojicherrypick --help` to list all options and their brief descriptions.

## Examples

```
$ emojicherrypick --help
$ emojicherrypick -o -i
$ emojicherrypick -ci
$ emojicherrypick --typing 
$ emojicherrypick -M random --clipboard
$ emojicherrypick -g "DejaVu Sans" --clipboard
$ emojicherrypick -@ "regex" -m regex --notify --clipboard 
$ emojicherrypick --norecents -M filter -p "mouse" -i --notify --stdout
$ emojicherrypick -@⭐ --noemojis --norecents -l6 -s32 --typing
$ emojicherrypick -@custom -E -k 0 -f "./custom.cherry" -o
```

## Favorites

You can have a sort of "bookmarks" of your favorite emojis by creating and
editing a text file. The program will always show them on top of the menu. The
location is at "~/.config/emojicherrypick/favorites.cherry" and has the same
format as the "recents.cherry" and "emojis.cherry" format:

```
EMOJI DESCRIPTION
```

Everything until first space is considered an emoji and it even works with text
only too. An example "favorites.cherry":

```
🌈 imagination
💩 poop
👉😎👈 this guy
⎇ alternative
very@important.org email
```

Depending on the application or font, some emojis may be not be visible to you.

# Additional files in use

These files are created by the script or optionally by the user.

## created automatically

* `~/.cache/emojicherrypick/emojis.json`
* `~/.cache/emojicherrypick/emojis.cherry`
* `~/.cache/emojicherrypick/recents.cherry`
 
"emojis.json" will be downloaded from following Github Gists link
"[@thingsiplay/emojis.json](https://gist.githubusercontent.com/thingsiplay/1f500459bc117cf0b63e1f5c11e03963/raw/d8e4b78cfe66862cf3809443c1dba017f37b61db/emojis.json)"
which is forked from
"[@oliveratgithub/emojis.json](https://gist.github.com/oliveratgithub/0bf11a9aff0d6da7b46f1490f86a71eb)"
, unless the file already exists on the disk. The other files are created
automatically by the program.

## optional user created data

* `~/.config/emojicherrypick/favorites.cherry`

"favorites.cherry" can be a user created list of cherries (emojis) and will be
loaded up automatically if present.

