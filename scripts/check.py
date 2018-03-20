#!/usr/bin/env python3
#
# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

import re
from sys import argv, exit, stderr

from voluptuous import Any, MultipleInvalid, Required, Schema

import yaml


families = [
    'alpine',
    'anitya',
    'aosc',
    'arch',
    'centos',
    'chocolatey',
    'cpan',
    'cran',
    'crates_io',
    'crux',
    'debuntu',
    'distrowatch',
    'fdroid',
    'fedora',
    'freebsd',
    'freshcode',
    'gentoo',
    'gobolinux',
    'guix',
    'hackage',
    'haikuports',
    'homebrew',
    'kaos',
    'libregamewiki',
    'macports',
    'mageia',
    'msys2',
    'nix',
    'openbsd',
    'openindiana',
    'openmandriva',
    'opensuse',
    'openwrt',
    'pclinuxos',
    'pkgsrc',
    'pypi',
    'ravenports',
    'rosa',
    'rubygems',
    'rudix',
    'scoop',
    'sisyphus',
    'slackbuilds',
    'snap',
    'vcpkg',
    'wikidata',
    'yacp',
]

rulesets = families + [
    'antix',
    'aur',
    'deb_multimedia',
    'deepin',
    'hyperbola',
    'maemo',
    'pardus',
    'parrot',
]

schema = Schema(
    {
        'name': Any(str, [str]),
        'namepat': str,
        'ver': Any(str, [str]),
        'verpat': str,
        'wwwpart': Any(str, [str]),
        'wwwpat': str,
        'family': Any(Any(*families), [Any(*families)]),  # XXX: legacy; remove after rules converted to ruleset
        'ruleset': Any(Any(*rulesets), [Any(*rulesets)]),
        'noruleset': Any(Any(*rulesets), [Any(*rulesets)]),
        'category': Any(str, [str]),
        'verlonger': int,
        'vergt': str,
        'verge': str,
        'verlt': str,
        'verle': str,
        'flag': str,
        'noflag': str,

        'setname': str,
        'setver': str,
        'addflavor': Any(bool, str, [str]),
        'resetflavors': bool,
        'remove': bool,
        'ignore': bool,
        'devel': bool,
        'p_is_patch': bool,
        'any_is_patch': bool,
        'outdated': bool,
        'legacy': bool,
        'incorrect': bool,
        'untrusted': bool,
        'noscheme': bool,
        'snapshot': bool,
        'successor': bool,
        'rolling': bool,
        'addflag': str,
        'last': bool,
        'tolowername': bool,
        'replaceinname': dict,
        'warning': str,
    }
)


class BadPlaceholderUsage(Exception):
    pass


def load_rule_file(path):
    with open(arg) as content:
        return yaml.safe_load(content)


def validate_regexps(rule):
    namegroups = 0
    vergroups = 0

    if 'namepat' in rule:
        r = re.compile(rule['namepat'])
        namegroups = r.groups
    if 'verpat' in rule:
        r = re.compile(rule['verpat'])
        vergroups = r.groups
    if 'wwwpat' in rule:
        re.compile(rule['wwwpat'])

    for n in range(5):
        ph = '$' + str(n)

        if 'setname' in rule and ph in rule['setname'] and n > namegroups:
            raise BadPlaceholderUsage('{} is used in setname, but the regular expression only has {} capture group(s)'.format(ph, namegroups))
        if 'addflavor' in rule and isinstance(rule['addflavor'], str) and ph in rule['addflavor'] and n > namegroups:
            raise BadPlaceholderUsage('{} is used in addflavor, but the regular expression only has {} capture group(s)'.format(ph, namegroups))
        if 'setver' in rule and ph in rule['setver'] and n > vergroups:
            raise BadPlaceholderUsage('{} is used in setver, but the regular expression only has {} capture group(s)'.format(ph, vergroups))


def check_rule_file(path):
    rules = None
    try:
        rules = load_rule_file(arg)
    except yaml.parser.ParserError as e:
        print('{}: cannot parse'.format(arg, str(e)), file=stderr)
        return False

    result = True
    for rule in rules:
        try:
            schema(rule)
        except MultipleInvalid as e:
            print('{}: schema check failed: {}'.format(arg, str(e)), file=stderr)
            print('  Rule: {}'.format(rule), file=stderr)
            result = False

        try:
            validate_regexps(rule)
        except re.error as e:
            print('{}: regular expression compilation failed: {}'.format(arg, str(e)), file=stderr)
            print('  Rule: {}'.format(rule), file=stderr)
            result = False
        except BadPlaceholderUsage as e:
            print('{}: placeholder problem: {}'.format(arg, str(e)), file=stderr)
            print('  Rule: {}'.format(rule), file=stderr)
            result = False

    return result


if __name__ == '__main__':
    if len(argv) <= 1:
        print('Usage: {} file.yaml ...'.format(argv[0]), file=stderr)
        exit(2)

    ok = True
    for arg in argv[1:]:
        ok &= check_rule_file(arg)

    exit(0 if ok else 1)
