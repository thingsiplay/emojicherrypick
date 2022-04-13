#!/bin/env python3

import sys
import os
import shutil
import argparse
import json
import urllib.request
import subprocess
import random

from pathlib import Path
from typing import Tuple
from typing import TypeAlias

CompletedProcess: TypeAlias = subprocess.CompletedProcess


class App:
    """ Contains all settings and meta information for the application. """

    name: str = 'emojicherrypick'
    version: str = '0.2'

    def __init__(self, args: argparse.Namespace) -> None:
        """ Construct application attributes used as settings. """

        self.list_version: bool = args.version
        self.frozen: bool = bool(getattr(sys, 'frozen', False)
                                 and hasattr(sys, '_MEIPASS'))
        self.wipe_cache: bool = args.wipe_cache
        self.offline: bool = args.offline
        self.menu: str = args.menu
        self.url: str = args.url
        self.cache_dir: Path = fullpath(args.cache_dir)
        self.db_source: Path = Path(self.cache_dir / 'emojis.json')
        self.noemojis: bool = args.noemojis
        self.db_filtered: Path | None = None
        if not self.noemojis:
            self.db_filtered = self.db_source.with_suffix('.cherry')
        self.nofavorites: bool = args.nofavorites
        self.db_favorites: Path | None = None
        if not self.nofavorites:
            self.db_favorites = fullpath(args.favorites)
        self.recents_size: int = args.recents_size
        self.norecents: bool = args.norecents
        self.db_recents: Path | None = None
        if not self.norecents:
            self.db_recents = fullpath(args.recents)
        self.font_family: str = args.font_family
        self.font_size: int = args.font_size
        self.list_size: int = args.list_size
        self.selected_emoji: str | None = None
        self.selected_desc: str | None = None
        self.stdout: bool = args.stdout and not args.nostdout
        self.clipboard: bool = args.clipboard and not args.noclipboard
        self.notify: bool = args.notify and not args.nonotify
        self.typing: bool = args.typing and not args.notyping
        self.ignore_case: bool = args.ignore_case and not args.noignore_case
        self.ignore_skin: bool = args.ignore_skin
        self.matching_rofi: str = args.matching_rofi
        self.pattern: str = args.pattern
        self.prompt: str = args.prompt
        self.list_programs: bool = args.list_programs
        self.programs: dict[str, Path] = {
            'Python': Path(sys.executable),
            'rofi': App.which(args.rofi),
            'dmenu': App.which(args.dmenu),
            'pmenu': App.which(args.pmenu),
            'fzf': App.which(args.fzf),
            'xclip': App.which(args.xclip),
            'xdotool': App.which(args.xdotool),
            'notify-send': App.which(args.notifysend),
        }

        if self.wipe_cache:
            self.wipe_cache_files()
        if not self.offline or not self.noemojis:
            self.download_db_source()
        self.filter_db_source()

    def load_emoji_list(self, aslist=False) -> str | list:
        """ Read all emojis, recents and favorites into a single string. """

        emoji_list: str = ''
        filtered_list: str = ''
        recents_list: str = ''
        favorites_list: str = ''
        if (not self.norecents
                and self.db_recents
                and self.db_recents.exists()):
            recents_list = self.db_recents.read_text().strip('\n')
            recents_top: list = recents_list.splitlines()
            recents_top.reverse()
            recents_top = list(dict.fromkeys(recents_top))
            recents_top = recents_top[0:self.recents_size]
            recents_list = '\n'.join(recents_top)
        if (not self.nofavorites
                and self.db_favorites
                and self.db_favorites.exists()):
            favorites_list = self.db_favorites.read_text().strip('\n')
        if (not self.noemojis
                and self.db_filtered
                and self.db_filtered.exists()):
            filtered_list = self.db_filtered.read_text().strip('\n')
        if recents_list:
            emoji_list += '\n' + recents_list
        if favorites_list:
            emoji_list += '\n' + favorites_list
        if filtered_list:
            emoji_list += '\n' + filtered_list
        elist: list[str] = list(dict.fromkeys(emoji_list.splitlines()))
        if aslist:
            return elist
        else:
            emoji_list = '\n'.join(elist)
            return emoji_list.lstrip('\n')

    def wipe_cache_files(self) -> None:
        """ Clean cache by deleting all known files in it. """

        if self.db_source:
            self.db_source.unlink(missing_ok=True)
        if self.db_filtered:
            self.db_filtered.unlink(missing_ok=True)
        if self.db_recents:
            self.db_recents.unlink(missing_ok=True)
        return None

    def download_db_source(self, force=False):
        """ Download emojis.json database source from URL to cache. """

        if force:
            self.db_source.unlink(missing_ok=True)
        if not self.db_source.exists():
            self.cache_dir.mkdir(exist_ok=True)
            self.db_filtered.unlink(missing_ok=True)
            response = urllib.request.urlopen(self.url)
            data = response.read()
            text = data.decode('utf-8')
            self.db_source.write_text(text)

    def filter_db_source(self, force=False):
        """ Convert, filter and sort cached database to a small text file. """

        def sorted_by_order(elem):
            """ Used to determined sort key by 'order' for sorted(). """

            return elem['order']

        if force:
            self.db_filtered.unlink(missing_ok=True)
        if self.db_filtered and not self.db_filtered.exists():
            source = json.loads(self.db_source.read_text())
            filtered: str = ''
            emojis_face: str = ''
            emojis_finger: str = ''
            emojis_other: str = ''
            for emoji in sorted(source['emojis'], key=sorted_by_order):

                # Exclude emojis that have "skin" in their names, as they are
                # mostly color variations of the main emoji.
                not_ignored_by_skin = 'skin' not in emoji['name'] \
                    and 'skin_tone' not in emoji['shortname'] if self.ignore_skin \
                        else True
                if (not_ignored_by_skin and emoji['name']):

                    # Format:
                    # ☺️ smiling face Smileys & Emotion (face-affection)
                    str_emoji: str = (emoji['emoji'].strip()
                                      + ' '
                                      + emoji['name'].strip()
                                      + ' ~ '
                                      + emoji['category'].strip())

                    # Create multiple lists with emojis, so later it can be put
                    # together for sorted groups.
                    if ('face' in emoji['name']
                            or 'face' in emoji['category']):
                        emojis_face += str_emoji + '\n'
                    elif 'finger' in emoji['category']:
                        emojis_finger += str_emoji + '\n'
                    else:
                        emojis_other += str_emoji + '\n'

            filtered = emojis_face + emojis_finger + emojis_other
            self.db_filtered.write_text(filtered.strip('\n'))

    def update_selected_emoji(self, emoji: list | None) -> str | None:
        """ Update last selected emoji and return by stripping newlines. """

        if emoji is None:
            self.selected_emoji = None
            self.selected_desc = None
        else:
            try:
                emoji = [emoji[0].strip('\n'), emoji[1].strip('\n')]
                self.selected_emoji = emoji[0]
                self.selected_desc = emoji[1]
                self.append_recents()
            except (ValueError, AttributeError, IndexError):
                self.selected_emoji = None
                self.selected_desc = None
        return self.selected_emoji

    def select_by_none(self):
        """ Selects nothing and resets last selected emoji. """

        return self.update_selected_emoji(None)

    def select_by_random(self):
        """ Selects an emoji by random chance. """

        random_set: set = set(self.load_emoji_list(aslist=True))
        random_set.discard('')
        random_list: list = list(random_set)
        random.shuffle(random_list)
        emoji = random_list[0].split(' ', 1)
        return self.update_selected_emoji(emoji)

    def select_by_filter(self) -> str | None:
        """ Select an emoji without a menu but first match on a filter. """

        emoji_list: str | list = self.load_emoji_list(aslist=True)
        if self.ignore_case:
            emoji_list = list(filter(
                lambda line: self.pattern.lower() in line.lower(),
                emoji_list
            ))
        else:
            emoji_list = list(filter(
                lambda line: self.pattern in line,
                emoji_list
            ))
        try:
            emoji = emoji_list[0].split(' ', 1)
        except (ValueError, AttributeError, IndexError):
            emoji = None
        return self.update_selected_emoji(emoji)

    def select_by_dmenu(self):
        """ Select an emoji with dmenu and get emoji and desc tuple. """

        command: list[str] = []
        command.append(self.programs['dmenu'].as_posix())
        command.append('-p')
        command.append(self.prompt)
        command.append('-l')
        command.append(str(self.list_size))
        command.append('-fn')
        command.append(f'"{self.font_family}-{str(self.font_size)}"')
        emoji_list = self.load_emoji_list()
        if self.ignore_case:
            emoji_list = emoji_list.lower()
        emoji = App.select_command_emoji(command, emoji_list)
        return self.update_selected_emoji(emoji)

    def select_by_rofi(self):
        """ Select an emoji with rofi and get emoji and desc tuple. """

        command: list[str] = []
        command.append(self.programs['rofi'].as_posix())
        command.append('-dmenu')
        command.append('-steal-focus')
        command.append('-p')
        command.append(self.prompt)
        command.append('-title')
        command.append(self.name)
        command.append('-l')
        command.append(str(self.list_size))
        command.append('-font')
        command.append(f'"{self.font_family} {str(self.font_size)}"')
        command.append('-no-custom')
        command.append('-matching')
        command.append(self.matching_rofi)
        if self.ignore_case:
            command.append('-i')
            command.append('-nocase-sensitive')
        emoji_list = self.load_emoji_list()
        emoji = App.select_command_emoji(command, emoji_list)
        return self.update_selected_emoji(emoji)

    def select_by_pmenu(self):
        """ Select an emoji with pmenu and get emoji and desc tuple. """

        command: list[str] = []
        command.append(self.programs['pmenu'].as_posix())
        command.append('-p')
        command.append(self.prompt)
        emoji_list = self.load_emoji_list()
        if self.ignore_case:
            emoji_list = emoji_list.lower()
        emoji = App.select_command_emoji(command, emoji_list)
        return self.update_selected_emoji(emoji)

    def select_by_fzf(self):
        """ Select an emoji with fzf and get emoji and desc tuple. """

        command: list[str] = []
        command.append(self.programs['fzf'].as_posix())
        command.append('--layout')
        command.append('reverse')
        command.append('--prompt')
        command.append(self.prompt)
        if self.pattern:
            command.append('--filter')
            command.append(self.pattern)
        if self.ignore_case:
            command.append('-i')
        emoji_list = self.load_emoji_list()
        emoji = App.select_command_emoji(command, emoji_list)
        return self.update_selected_emoji(emoji)

    @classmethod
    def select_command_emoji(
            cls,
            command,
            emoji_list) -> Tuple[str, str] | Tuple[None, None]:
        """ Return selected emoji and desc from list using custom command. """

        output_p: CompletedProcess | None = None
        try:
            output_p = subprocess.run(command,
                                      input=emoji_list,
                                      stdout=subprocess.PIPE,
                                      text=True)
        except FileNotFoundError:
            raise subprocess.SubprocessError
        if output_p and output_p.stdout:
            try:
                emoji, desc = output_p.stdout.split(' ', 1)
                return emoji.strip(' \n'), desc.strip(' \n')
            except ValueError:
                return None, None
        else:
            return None, None

    def send_emoji_to_stdout(self, newline=True) -> None:
        """ Print out emoji to stdout. """

        if newline:
            print(self.selected_emoji)
        else:
            print(self.selected_emoji, end='')

    def send_emoji_to_clipboard(self) -> subprocess.Popen | None:
        """ Copy emoji to systems clipboard. """

        command: list[str] = []
        command.append(self.programs['xclip'].as_posix())
        command.append('-rmlastnl')
        command.append('-selection')
        command.append('clipboard')
        xclip_p: subprocess.Popen | None = None
        xclip_p = subprocess.Popen(command,
                                   stdin=subprocess.PIPE,
                                   text=True)
        if xclip_p:
            try:
                xclip_p.communicate(input=(self.selected_emoji), timeout=2)
                if xclip_p.returncode:
                    raise subprocess.SubprocessError
            except subprocess.TimeoutExpired:
                xclip_p.kill()
                xclip_p = None
                raise subprocess.SubprocessError
        else:
            xclip_p = None
            raise subprocess.SubprocessError
        return xclip_p

    def send_emoji_to_typing(self) -> CompletedProcess | None:
        """ Output emoji to active window as if user typed it on keyboard. """

        command: list[str] = []
        command.append(self.programs['xdotool'].as_posix())
        command.append('getwindowfocus')
        command.append('windowfocus')
        command.append('--sync')
        command.append('type')
        command.append('--clearmodifiers')
        command.append('--delay')
        command.append('25')
        if self.selected_emoji:
            command.append(self.selected_emoji)
        xdotool_p: CompletedProcess | None = None
        xdotool_p = subprocess.run(command,
                                   stdin=subprocess.PIPE,
                                   text=True,
                                   check=True,
                                   timeout=1)
        return xdotool_p

    def send_emoji_to_notify(self) -> CompletedProcess | None:
        """ Send the emoji as a notification message. """

        command: list[str] = []
        command.append(self.programs['notify-send'].as_posix())
        command.append('--urgency=low')
        if self.selected_emoji:
            command.append(self.selected_emoji)
        notify_p: CompletedProcess | None = None
        notify_p = subprocess.run(command,
                                  stdin=subprocess.PIPE,
                                  text=True,
                                  check=True,
                                  timeout=1)
        return notify_p

    def append_recents(self) -> bool:
        """ Append the last selected emoji entry to the recents file. """

        if (not self.norecents
                and self.db_recents
                and self.selected_emoji
                and self.selected_desc):
            line: str = ''
            if self.db_recents.exists():
                line = '\n'
                self.trim_recents_file()
            line += self.selected_emoji + ' ' + self.selected_desc
            with open(self.db_recents, 'a') as file:
                file.write(line)
            return True
        else:
            return False

    def trim_recents_file(self) -> bool:
        """ Shortens and strips recents file if it gets big. """

        max_byte_size: int = 4096
        max_list_entries: int = 50
        if (self.db_recents
                and self.db_recents.stat().st_size > max_byte_size):
            data: str = self.db_recents.read_text().strip('\n')
            recents_list: list = data.splitlines()
            recents_list.reverse()
            recents_list = list(dict.fromkeys(recents_list))
            recents_list = recents_list[0:max_list_entries]
            recents_list.reverse()
            data = '\n'.join(recents_list)
            self.db_recents.unlink(missing_ok=True)
            self.db_recents.write_text(data)
            return True
        else:
            return False

    def print_version(self):
        """ Print version and frozen state of this program. """

        if self.frozen:
            frozen = ' (pyinstaller)'
        else:
            frozen = ''
        print(f'{self.name} v{self.version}{frozen}')

    def print_list_programs(self):
        """ Print all program names and paths to stdout. """

        for name, path in self.programs.items():
            print(name + ':', path.as_posix())

    @classmethod
    def which(cls, command: str) -> Path:
        """ Find command in $PATH or get fullpath. """

        program: str | None = shutil.which(command)
        path: Path
        if program:
            path = Path(program)
        else:
            path = fullpath(command)
            if not path.is_file():
                path = Path(command)
        return path


def fullpath(file: str) -> Path:
    """ Transform str to path, resolve env vars, tilde and make absolute. """

    expandedfile: str = os.path.expandvars(file)
    path: Path = Path(expandedfile).expanduser().resolve()
    return path


def parse_arguments(args: list[str] | None = None) -> argparse.Namespace:
    """ Programs CLI options. """

    parser = argparse.ArgumentParser(
        description=('🍒⛏️ Emoji Cherry Pick - Select an emoji and go wild.'),
        epilog=('Copyright © 2022 Tuncay D. '
                '<https://github.com/thingsiplay/emojicherrypick>'),
    )

    parser.add_argument(
        '--version',
        default=False,
        action='store_true',
        help='print version and exit'
    )

    parser.add_argument(
        '--list-programs',
        default=False,
        action='store_true',
        help='list available programs and exit'
    )

    p_enable_output = parser.add_argument_group('enable output')

    p_enable_output.add_argument(
        '-o', '--stdout',
        default=False,
        action='store_true',
        help=('write selected emoji to stdout, unless option "--nostdout" '
              'is in effect')
    )

    p_enable_output.add_argument(
        '-t', '--typing',
        default=False,
        action='store_true',
        help=('simulate typing out the emoji on the keyboard, unless option '
              '"--notyping" is in effect, typing can be unreliable and not '
              'all applications may accept or play nice with it')
    )

    p_enable_output.add_argument(
        '-c', '--clipboard',
        default=False,
        action='store_true',
        help=('copy selected emoji to system clipboard, unless option '
              '"--noclipboard" is in effect')
    )

    p_enable_output.add_argument(
        '-n', '--notify',
        default=False,
        action='store_true',
        help=('send selected emoji as a notification message, unless option '
              '"--nonotify" is in effect')
    )

    p_disable_output = parser.add_argument_group('disable output')

    p_disable_output.add_argument(
        '-O', '--nostdout',
        default=False,
        action='store_true',
        help='disable interaction with stdout, regardless of other options'
    )

    p_disable_output.add_argument(
        '-T', '--notyping',
        default=False,
        action='store_true',
        help=('disable simulated typing to active window, regardless of '
              'other options')
    )

    p_disable_output.add_argument(
        '-C', '--noclipboard',
        default=False,
        action='store_true',
        help=('disable interaction with clipboard, regardless of other '
              'options')
    )

    p_disable_output.add_argument(
        '-N', '--nonotify',
        default=False,
        action='store_true',
        help=('do not send any notification messages, regardless of other '
              'options')
    )

    p_programs = parser.add_argument_group('programs')

    p_programs.add_argument(
        '--rofi',
        metavar='CMD',
        default='rofi',
        help=('name or path to "rofi" program when option "--menu" is set to '
              '"rofi"')
    )

    p_programs.add_argument(
        '--dmenu',
        metavar='CMD',
        default='dmenu',
        help=('name or path to "dmenu" program when option "--menu" is set to '
              '"dmenu"')
    )

    p_programs.add_argument(
        '--pmenu',
        metavar='CMD',
        default='pmenu',
        help=('name or path to "pmenu" program when option "--menu" is set to '
              '"pmenu"')
    )

    p_programs.add_argument(
        '--fzf',
        metavar='CMD',
        default='fzf',
        help=('name or path to "fzf" program when option "--menu" is set to '
              '"fzf"')
    )

    p_programs.add_argument(
        '--xclip',
        metavar='CMD',
        default='xclip',
        help=('name or path to "xclip" program to handle clipboard when '
              'option "--clipboard" is active')
    )

    p_programs.add_argument(
        '--xdotool',
        metavar='CMD',
        default='xdotool',
        help=('name or path to "xdotool" program to handle typing when option '
              '"--typing" is active')
    )

    p_programs.add_argument(
        '--notifysend',
        metavar='CMD',
        default='notify-send',
        help=('name or path to "notify-send" program to handle notifications '
              'when option "--notify" is active')
    )

    p_menufilter = parser.add_argument_group('engines and filters')

    default_menu: str = 'rofi'
    p_menufilter.add_argument(
        '-M', '--menu',
        metavar='SYSTEM',
        default=default_menu,
        choices=['rofi', 'dmenu', 'pmenu', 'fzf', 'filter', 'random', 'none'],
        help=('change menu engine to select emojis, available systems: '
              '"rofi", "dmenu", "pmenu", "fzf", "filter", "random", "none", '
              'system "none" disables selection, "filter" won\'t display a '
              'menu but choose first entry in the list that matches the text '
              'at option "--pattern", systems "fzf" and "pmenu" are terminal '
              'programs, "random" won\'t display a menu but choose an entry '
              f'by random chance, defaults to: "{default_menu}"')
    )

    p_menufilter.add_argument(
        '-p', '--pattern',
        metavar='filter',
        default='',
        help=('simple text filter, used when option "--menu" is set to '
              '"filter" or "fzf", causes in both cases to non interactive '
              'selection of first emoji that matches the pattern')
    )

    default_matching_rofi: str = 'normal'
    p_menufilter.add_argument(
        '-m', '--matching-rofi',
        metavar='MODE',
        default=default_matching_rofi,
        choices=['normal', 'regex', 'glob', 'fuzzy', 'prefix'],
        help=('set matching algorithm for search in rofi, available modes: '
              '"normal", "regex", "glob", "fuzzy", "prefix", defaults to: '
              f'"{default_matching_rofi}"')
    )

    p_menufilter.add_argument(
        '-i', '--ignore-case',
        default=False,
        action='store_true',
        help=('ignore case sensitivity when searching list of emojis, '
              'unless option "--noignore-case" is in effect')
    )

    p_menufilter.add_argument(
        '-I', '--noignore-case',
        default=False,
        action='store_true',
        help='case sensitive search of emojis, regardless of other options'
    )

    p_cache = parser.add_argument_group('cache files')

    default_url = ('https://gist.githubusercontent.com/thingsiplay/'
                   '1f500459bc117cf0b63e1f5c11e03963/raw/'
                   'd8e4b78cfe66862cf3809443c1dba017f37b61db/emojis.json')
    p_cache.add_argument(
        '-u', '--url',
        metavar='URL',
        default=(default_url),
        help=('source web address to download file "emojis.json", defaults '
              f'to: "{default_url}"')
    )

    p_cache.add_argument(
        '-U', '--offline',
        default=False,
        action='store_true',
        help='prohibit downloading files from network, mainly "emojis.json"'
    )

    default_cache: str = "~/.cache/emojicherrypick"
    p_cache.add_argument(
        '-d', '--cache-dir',
        metavar='DIR',
        default=default_cache,
        help=('directory for downloads and other long-lived temporary files '
              f'used for quick access, defaults to: "{default_cache}"')
    )

    p_cache.add_argument(
        '-w', '--wipe-cache',
        default=False,
        action='store_true',
        help=('delete temporary cache files, redownload and recreate them '
              'unless option "--offline" is in effect')
    )

    p_cache.add_argument(
        '-E', '--noemojis',
        default=False,
        action='store_true',
        help=('disable loading from main emojis database created from '
              '"emojis.json"')
    )

    default_recents: str = "~/.cache/emojicherrypick/recents.cherry"
    p_cache.add_argument(
        '-r', '--recents',
        metavar='FILE',
        default=default_recents,
        help=('program keeps track of last used emojis and saves them to '
              'a history file, the last entries will be displayed at the top '
              'of each emoji listing in the menus, same format as '
              '"--favorites" file, use option "--recents-size" to set number '
              f'of entries to show blah, defaults to: "{default_recents}"')
    )

    p_cache.add_argument(
        '-R', '--norecents',
        default=False,
        action='store_true',
        help='disable recents file specified at option "--recents"'
    )

    default_recents_size: int = 2
    p_cache.add_argument(
        '-k', '--recents-size',
        metavar='NUM',
        default=default_recents_size,
        type=int,
        choices=range(0, 200),
        help=('read number of recently used emojis and ignore rest of file, '
              'can be used for displaying in the menu or at filters, '
              f'defaults to: "{default_recents_size}"')
    )

    p_cache.add_argument(
        '--ignore-skin',
        default=True,
        action=argparse.BooleanOptionalAction,
        help='ignore emoji skin variations when creating the cache'
    )

    p_config = parser.add_argument_group('config files')

    default_favorites: str = "~/.config/emojicherrypick/favorites.cherry"
    p_config.add_argument(
        '-f', '--favorites',
        metavar='FILE',
        default=default_favorites,
        help=('user list of emojis to list at the beginning of each emoji '
              'listing in the menus, 1 line per emoji set, each set starts '
              'with an emoji or any text and goes until first space is found, '
              'rest of the line are names, descripion and keywords, defaults '
              f'to: "{default_favorites}"')
    )

    p_config.add_argument(
        '-F', '--nofavorites',
        default=False,
        action='store_true',
        help='disable favorites file specified at option "--favorites"'
    )

    p_menuinterface = parser.add_argument_group('menu interface')

    default_prompt: str = '🍒'
    p_menuinterface.add_argument(
        '-@', '--prompt',
        metavar='TEXT',
        default=default_prompt,
        help=('set custom prompt on user input menu left of entry field, '
              f'defaults to: "{default_prompt}"')
    )

    default_font_family: str = 'Noto Color Emoji'
    p_menuinterface.add_argument(
        '-g', '--font-family',
        metavar='NAME',
        default=default_font_family,
        help=('font name to use for dispaly with the menu, defaults to: '
              f'"{default_font_family}"')
    )

    default_font_size: int = 16
    p_menuinterface.add_argument(
        '-s', '--font-size',
        metavar='NUM',
        default=default_font_size,
        type=int,
        choices=range(4, 256),
        help=('font size of emojis and text to display in the menu, '
              f'defaults to: "{default_font_size}"')
    )

    default_list_size: int = 15
    p_menuinterface.add_argument(
        '-l', '--list-size',
        metavar='NUM',
        default=default_list_size,
        type=int,
        choices=range(1, 200),
        help=('number of rows to display in the menu, defaults to: '
              f'"{default_list_size}"')
    )

    if args is None:
        return parser.parse_args()
    else:
        return parser.parse_args(args)


def main(args: list[str] | None = None) -> int:
    """ Run the application. """

    app: App
    if not args and not sys.argv[1:]:
        args_default: list[str] = [os.getenv('EMOJICHERRYPICK_DEFAULT',
                                   default='-con')]
        app = App(parse_arguments(args_default))
    else:
        app = App(parse_arguments(args))

    if app.list_version:
        app.print_version()
        return 0
    elif app.list_programs:
        app.print_list_programs()
        return 0

    try:
        if app.menu == 'rofi':
            app.select_by_rofi()
        elif app.menu == 'dmenu':
            app.select_by_dmenu()
        elif app.menu == 'pmenu':
            app.select_by_pmenu()
        elif app.menu == 'fzf':
            app.select_by_fzf()
        elif app.menu == 'filter':
            app.select_by_filter()
        elif app.menu == 'random':
            app.select_by_random()
        elif app.menu == 'none':
            app.select_by_none()
        else:
            raise RuntimeError('Unkown menu option.')
            return -1
    except subprocess.SubprocessError:
        return 1

    if app.selected_emoji:
        try:
            if app.stdout:
                app.send_emoji_to_stdout()
            if app.clipboard:
                app.send_emoji_to_clipboard()
            if app.typing:
                app.send_emoji_to_typing()
            if app.notify:
                app.send_emoji_to_notify()
        except subprocess.SubprocessError:
            return 3
    elif app.menu == 'none':
        return 0
    else:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
