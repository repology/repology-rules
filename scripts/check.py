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
    'adelie',
    'aix',
    'alpine',
    'anitya',
    'aosc',
    'arch',
    'buckaroo',
    'centos',
    'chocolatey',
    'cpan',
    'cran',
    'crates_io',
    'crux',
    'debuntu',
    'distrowatch',
    'exherbo',
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
    'hpux',
    'kaos',
    'libregamewiki',
    'macports',
    'mageia',
    'msys2',
    'nix',
    'openbsd',
    'openindiana',
    'openmandriva',
    'openpkg',
    'opensuse',
    'openwrt',
    'pclinuxos',
    'pkgsrc',
    'pld',
    'pypi',
    'ravenports',
    'rosa',
    'rubygems',
    'rudix',
    'scoop',
    'sisyphus',
    'slackbuilds',
    'slitaz',
    'snap',
    'termux',
    'vcpkg',
    'wikidata',
    'yacp',
]

rulesets = families + [
    'antix',
    'aur',
    'blackarch',
    'deb_multimedia',
    'deepin',
    'epel',
    'frugalware',
    'hyperbola',
    'maemo',
    'manjaro',
    'packman',
    'parabola',
    'pardus',
    'parrot',
    'slitaz_next',
    'unitedrpms',
]

schema = Schema(
    {
        'name': Any(str, [str]),
        'namepat': str,
        'ver': Any(str, [str]),
        'verpat': str,
        'wwwpart': Any(str, [str]),
        'wwwpat': str,
        'ruleset': Any(Any(*rulesets), [Any(*rulesets)]),
        'noruleset': Any(Any(*rulesets), [Any(*rulesets)]),
        'category': Any(str, [str]),
        'verlonger': int,
        'vergt': str,
        'verge': str,
        'verlt': str,
        'verle': str,
        'vereq': str,
        'verne': str,
        'flag': str,
        'noflag': str,

        'setname': str,
        'setver': str,
        'addflavor': Any(bool, str, [str]),
        'resetflavors': bool,
        'remove': bool,
        'ignore': bool,
        'devel': bool,
        'weak_devel': bool,
        'p_is_patch': bool,
        'any_is_patch': bool,
        'outdated': bool,
        'legacy': bool,
        'incorrect': bool,
        'untrusted': bool,
        'noscheme': bool,
        'rolling': bool,
        'snapshot': bool,
        'successor': bool,
        'generated': bool,
        'addflag': str,
        'last': bool,
        'tolowername': bool,
        'replaceinname': {str: str},
        'warning': str,

        'maintenance': bool,
        'disposable': bool,
        'precious': bool,
    }
)


order_fields_by_pattern = {
    '.*800.renames-and-merges/[0duwyz]\.yaml': 'setname',
#    '.*850.split-ambiguities/.*\.yaml': 'name',
    '.*900.version-fixes/[1a-z].*\.yaml': 'name',
    '.*950.split-branches.yaml': 'name',
}


class BadPlaceholderUsage(Exception):
    pass


class BadRuleValue(Exception):
    pass


class BadSorting(Exception):
    pass


def load_rule_file(path):
    with open(path) as content:
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
            raise BadPlaceholderUsage('"{}" is used in setname, but the regular expression only has {} capture group(s)'.format(ph, namegroups))
        if 'addflavor' in rule and isinstance(rule['addflavor'], str) and ph in rule['addflavor'] and n > namegroups:
            raise BadPlaceholderUsage('"{}" is used in addflavor, but the regular expression only has {} capture group(s)'.format(ph, namegroups))
        if 'setver' in rule and ph in rule['setver'] and n > vergroups:
            raise BadPlaceholderUsage('"{}" is used in setver, but the regular expression only has {} capture group(s)'.format(ph, vergroups))


def validate_value(key, val):
    if key in ['namepat', 'verpat', 'wwwpat']:
        val = val.replace('\n', '')
    if val.strip() != val:
        raise BadRuleValue('{} is not stripped'.format(key))
    if val.strip('"') != val:
        raise BadRuleValue('{} contains stray ", check for unbalanced YAML quotes'.format(key))
    if key.endswith('pat') and '\\.*' in val:
        raise BadRuleValue('{} contains incorrect pattern "\\\\.*", perhaps you\'ve meant "\\\\..*"?'.format(key))
    if key in ('name', 'ver') and ('.*' in val or '[' in val or '{' in val or '|' in val):
        raise BadRuleValue('{0} is not a pattern but contains pattern characters, perhaps you\'ve meant to use {0}pat?'.format(key))
    if key == 'verpat' and re.fullmatch('[0-9]+(\\.[0-9]+)+', val):
        raise BadRuleValue('verpat contains literal versions, perhaps you\'ve meant to use ver?')


def validate_values(rule):
    for key, val in rule.items():
        if isinstance(val, str):
            validate_value(key, val)
        elif isinstance(val, list):
            if len(set(val)) < len(val):
                raise BadRuleValue('{} contains duplicate items'.format(key))
            for valitem in val:
                validate_value(key, valitem)

    if 'name' in rule and 'setname' in rule and rule['name'] == rule['setname']:
        raise BadRuleValue('setname is the same as name, rule is tautologic'.format(key))


class RulesetCheckResult:
    def __init__(self, filename):
        self.filename = filename
        self.failures = []

    def add_failure(self, message, description, rule=None):
        self.failures.append((message, description, rule))

    def is_ok(self):
        return not self.failures

    def dump_errors(self):
        if self.is_ok():
            return

        print('===> Validation failed for {}'.format(self.filename), file=stderr)

        for failure in self.failures:
            print('{}: {}'.format(failure[0], failure[1]), file=stderr)
            if failure[2]:
                print('  Rule: {}'.format(failure[2]), file=stderr)


def check_sorting(path, rules):
    sort_field = None
    for pattern, field in order_fields_by_pattern.items():
        if re.fullmatch(pattern, path):
            sort_field = field
            break

    if sort_field is None:
        return

    prevkey = None
    for rule in rules:
        key = None
        if sort_field in rule:
            key = rule[sort_field]
            if isinstance(key, list):
                key = key[0]

        if key is not None and prevkey is not None and key < prevkey:
            raise BadSorting('sorting problem, {} after {}'.format(key, prevkey))

        prevkey = key


def check_rule_file(path):
    result = RulesetCheckResult(path)

    rules = []
    try:
        rules = load_rule_file(path)
    except yaml.parser.ParserError as e:
        result.add_failure('cannot parse file', str(e))

    for rule in rules:
        try:
            schema(rule)
        except MultipleInvalid as e:
            result.add_failure('schema check failed', str(e), rule)

        try:
            validate_regexps(rule)
        except re.error as e:
            result.add_failure('regular expression problem', str(e), rule)
        except BadPlaceholderUsage as e:
            result.add_failure('placeholder problem', str(e), rule)

        try:
            validate_values(rule)
        except BadRuleValue as e:
            result.add_failure('value problem', str(e), rule)

    try:
        check_sorting(path, rules)
    except BadSorting as e:
        result.add_failure('sorting problem', str(e))

    return result


if __name__ == '__main__':
    if len(argv) <= 1:
        print('Usage: {} file.yaml ...'.format(argv[0]), file=stderr)
        exit(2)

    try:
        from multiprocessing import Pool
        results = Pool().map(check_rule_file, argv[1:])
    except ImportError:
        results = map(check_rule_file, argv[1:])

    ok = True
    for result in results:
        result.dump_errors()
        ok &= result.is_ok()

    exit(0 if ok else 1)
