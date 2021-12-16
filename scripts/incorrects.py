#!/usr/bin/env python3
#
# Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from collections import defaultdict
from sys import argv, stderr

import yaml


if __name__ == '__main__':
    if len(argv) == 1:
        print(f'Usage: {argv[0]} file.yaml ...', file=stderr)
        exit(2)

    unique_ignore_rules_per_ruleset = defaultdict(set)

    for path in argv[1:]:
        with open(path) as content:
            rules = yaml.safe_load(content)

        for rule in rules:
            if not (rule.get('incorrect', False) or rule.get('untrusted', False)):
                continue

            match rule.get('name') or rule.get('namepat'):
                case str() as s:
                    keys = set([s])
                case list() as l:
                    keys = set(l)
                case _:
                    keys = set('?')

            match rule.get('ruleset'):
                case str() as s:
                    rulesets = set([s])
                case list() as l:
                    rulesets = set(l)
                case _:
                    continue

            for key in keys:
                for ruleset in rulesets:
                    unique_ignore_rules_per_ruleset[ruleset].add(key)

    print('Repository families by number of incorrect version rules:')
    for count, ruleset in sorted((len(v), k) for k, v in unique_ignore_rules_per_ruleset.items()):
        print(count, ruleset)
