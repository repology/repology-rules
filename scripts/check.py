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
    'conda',
    'cpan',
    'cran',
    'crates_io',
    'crux',
    'cygwin',
    'debuntu',
    'distrowatch',
    'elpa',
    'exherbo',
    'fdroid',
    'fedora',
    'fink',
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
    'lunar',
    'macports',
    'mageia',
    'mer',
    'msys2',
    'nix',
    'npackd',
    'openbsd',
    'openindiana',
    'openmandriva',
    'openpkg',
    'opensuse',
    'openwrt',
    'pclinuxos',
    'pisi',
    'pkgsrc',
    'pld',
    'pypi',
    'ravenports',
    'reactos',
    'rosa',
    'rubygems',
    'rudix',
    'salix',
    'scoop',
    'sisyphus',
    'slackbuilds',
    'slackware',
    'slitaz',
    'snap',
    'solus',
    't2',
    'termux',
    'vcpkg',
    'void',
    'wikidata',
    'yacp',
]

rulesets = families + [
    'antergos',
    'antix',
    'astra',
    'aur',
    'blackarch',
    'bunsenlabs',
    'deb_multimedia',
    'deepin',
    'epel',
    'frugalware',
    'funtoo',
    'gnuelpa',
    'hyperbola',
    'maemo',
    'macosx',
    'manjaro',
    'melpa',
    'mint',
    'msys2_mingw',
    'msys2_msys2',
    'mx',
    'packman',
    'parabola',
    'pardus',
    'parrot',
    'slitaz_next',
    'unitedrpms',
    'windows',
]

schema = Schema(
    {
        'name': Any(str, [str]),
        'namepat': str,
        'ver': Any(str, [str]),
        'verpat': str,
        'wwwpart': Any(str, [str]),
        'summpart': Any(str, [str]),
        'wwwpat': str,
        'ruleset': Any(Any(*rulesets), [Any(*rulesets)]),
        'noruleset': Any(Any(*rulesets), [Any(*rulesets)]),
        'category': Any(str, [str]),
        'maintainer': Any(str, [str]),
        'verlonger': int,
        'vergt': str,
        'verge': str,
        'verlt': str,
        'verle': str,
        'vereq': str,
        'verne': str,
        'flag': Any(str, [str]),
        'noflag': Any(str, [str]),
        'is_p_is_patch': bool,

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
        'debianism': bool,
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


features_by_pattern = {
    '.*800.renames-and-merges/(.|emacs)\.yaml': {
        'sort_field': 'setname',
    },
#    '.*850.split-ambiguities/.*\.yaml': 'name',
    '.*900.version-fixes/.*\.yaml': {
        'sort_field': 'name',
        'disallowed': {'setname'},
    },
    '.*950.split-branches.yaml': {
        'sort_field': 'name',
        'disallowed': {'setver'},
    }
}


class BadPlaceholderUsage(Exception):
    pass


class BadRuleValue(Exception):
    pass


class BadSorting(Exception):
    pass


class DisallowedFields(Exception):
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


def check_disallowed_fields(rule, disallowed_fields):
    bad_fields = set(rule.keys()) & set(disallowed_fields)
    if bad_fields:
        raise DisallowedFields('{} not allowed in this file'.format(', '.join(bad_fields)))


def check_sorting(path, rules, sort_field):
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

    features = []
    for pattern, candidate_features in features_by_pattern.items():
        if re.fullmatch(pattern, path):
            features.append(candidate_features)

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
            for feature in features:
                if 'disallowed' in feature:
                    check_disallowed_fields(rule, feature['disallowed'])
        except DisallowedFields as e:
            result.add_failure('disallowed field', str(e), rule)
    try:
        for feature in features:
            if 'sort_field' in feature:
                check_sorting(path, rules, feature['sort_field'])
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
