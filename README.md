# Repology ruleset

[![Build Status](https://travis-ci.org/repology/repology-rules.svg?branch=master)](https://travis-ci.org/repology/repology-rules)

There can be a huge discrepancy in how packages for single project
are named and versioned in different repositories, so Repology
needs a flexible ruleset in order to overcome the differences,
match packages and make versions comparable.

## TL;DR

You are welcome to submit pull requests with rules you need. Here's
a quick pointer of how to add specific rules:

### You want to **merge** differently named packages into a single entry?

- Choose target name (prefer least ambiguous and/or most widely used name)
- Open correspoinding yaml file under `800.renames-and-merges/`
- Add rule like `- { setname: <new name>, name: <old name> }`

### You want to mark incorrect version of specific package?

- Open correspoinding yaml file under `900.version-fixes/`
- Add rule like: `- { name: <package name>, ver: <bad version>, ignore: true }`
- Consider using a `verpat` with regular expression to match similar
  bad versions which may appear in the future. Examples:
  - `verpat: "20[0-9]{6}"` to match dates (`20110323`)
  - `verpat: "20[0-9]{2}\\.[0-9]{2}\\.[0-9]{2}"` same, but for delimited date, (`2010.03.23`)
  - `verpat: ".*20[0-9]{6}.*"` to match dates anywhere in the version (`1.0.20110323`)
  - `verpat: "[0-9a-f]{7}"` match something resembling a git commit (`a7b823f`)
  - `verpat: "[0-9]{4,}"` match something resembling a build or revision number (`12345`)

### You want to split different projects with the same name

- Open correspoinding yaml file under `850.split-ambiguities/`
- Add a set of rules which distinct packages, such as:
  - `- { name: <ambiguous name>, wwwpart: <part of the homepage url>, setname: <specific name> }`
  - `- { name: <ambiguous name>, category: <category>, setname: <specific name> }`
  - `- { name: <ambiguous name>, verpat: <version pattern>, setname: <specific name> }`
  - `- { name: <ambiguous name>, ruleset: <families>, setname: <specific name> }` as a least resort

## Contributing

Things to know if you're submitting pull request or have push access
to this repository.

- Repology is currently set up to automatically pull latest ruleset
from `master` branch in this repo on each update, so everything
committed here will be automatically applied to repology in several
hours.
- Repology runs `make check` after updating the repo, and if it
fails, rolls back to the latest good commit, so it's somewhat
protected from broken ruleset.
- In the worst case, broken ruleset will prevent repology from
updating until the problem is resolved.
- Still, please run `make check` before committing, and/or install
a git hook (`scripts/pre-push`) which runs it for you (you can copy
it into `.git/hooks` or just run `make install-hook`).
- The checker script requires python modules `voluptous` and `PyYAML`.
`pip install PyYAML voluptuous` should install them for you.
- In general, stay close to the style already used in the ruleset,
use existing rules as examples, keep it simple and have fun!
- If in doubt, you can always just submit a report on the website
and avoid all the work!

## Rule basics

Rules are stored in a set of files in [YAML](http://yaml.org/) format,
a flexible human friendly markup format for structured data. Each
rule is a single item of big array, and may be written in single or
multiple lines (depending on what's more convenient for the particular
case), for example this rule renames `etracer` into `extreme-tuxracer`.

```yaml
- { name: etracer, setname: extreme-tuxracer }
```

which is the same as:

```yaml
- name: etracer
  setname: extreme-tuxracer
```

Each rule has a set of keywords which specify how a package is matched
(by name, version, repository, category etc.) and how it is modified
(package is renamed, version scheme is changed, flags are applied etc.).

Rule order matters, as multiple rules may match a single package, and
they are applied in order. Further more, changes applied by earlier
rules are affecting further matches: for instance, if a package is
renamed, new name will be matched for the following rules.

While rules are basically arbitrary, it's practical though to attribute
each rule to specific class of action, most distinctive of which are:

- Rename or merge rules. Match name, and set another name. Main purpose
  is to merge differently named packages into the same project. Such as
  `etracer`, `extremetuxracer`, `extreme-tuxracer` → `extreme-tuxracer`.
- Split rules. Match name and some additional property (version, homepage
  or repository) and set another name. Used to split similarly named
  packages of different projects. Such as `clementine` → `clementine-wm`,
  `clementine-player`.
- Version fixes. Match name but do not change it, instead change versions
  or set some version-related flags. Used to fix incorrect versioning scheme
  (`v1.0` → `1.0`), mark some versions as devel (such as beta versions),
  or ignore some versions (e.g. snapshots like `20130523` while there's
  official version like `1.0`).

## Ruleset structure

Ruleset is split into several distinctive parts, mostly based on functional
class of rules described above. They are arranged in such a way that when
adding a rule into a specific part you don't need to be aware of the rest of
the ruleset.

- **100.prefix-suffix** - normalization of repository specific prefixes and
  suffixes which are not part of the meaningful package name. Such as removal
  of `lib32-` prefixes.
- **2xx.handpicked** - a block where access to unmodified package names is
  needed, such as manual whitelists or blacklists.
- **[45]xx.wildcard** - wildcard rules which affect a lot of packages. These
  mostly handle modules for specific languages such as Perl (which may be
  named like `p5-Foo-Bar` or `libfoo-bar-perl` in different repos) by adding
  distinctive prefix (`perl:` in this case) to them, so they do not conflict
  with modules for other languages and other software.

  There are three subsets here:
  - **pure** rules which are known to not have any false positives
  (e.g. packages from `CPAN` are always perl modules).
  - **exceptions** for the wildcard rules
  - **wildcard** rules themselves

- **750.exceptions** - the small set of remaining exceptions. If a package
  needs rule here, it's most positively incorrectly named.
- **800.renames-and-merges** - pure merge rules
- **850.split-ambiguities** - pure split rules
- **900.version-fixes** - pure version fixes
- **950.split-branches** - additional split section for project which
  have multiple development branches which are incompatible and may
  present in a single repository at the same time for compatibility
  purposes. Such as `gtk2` and `gtk3`.

- There are also some **fixme** subsets which are remainings of previous
  generation of the ruleset. These files will eventually be refactored
  and removed.

This may seem complex, but in practice the mostly used rulesets are
**800**, **850** and **900**, which cleanly correspond to three functional
classes of rules described in the previous section.

Other parts of the ruleset may need attention when new repositories are
introduced.

## Rule syntax

As already mentioned, keywords which rules consist are related to either
matching packages or modifying them. Here's detailed description for all
of them.

### Conditions

#### ruleset

Each repository Repology supports has a set of *rulesets* associated with
it. For instance, all Debian-based distros have ruleset `debuntu`. It may
be used to only match packages in specific repositories, but without need
to chase specific repository version. You may look up repositories and
their retails in [repos.d](https://github.com/repology/repology/tree/master/repos.d)
directory of main Repology repository.

You may specify a list of rulesets to match either of them.

```yaml
- { ruleset: freebsd, ... }

- { ruleset: [ arch, openbsd ], ... }
```

#### noruleset

Disable rule matching for specified ruleset(s).

```yaml
# applies to all Debian derivatives, but not Deepin
- { ruleset: debuntu, noruleset: deepin, ... }
```

#### family

Deprecated. Same as **ruleset** and may be just changed into it.

#### category

Matches package category(ies). Note that category information is not
available for all repositories and each repository may have its
own set of categories.

```yaml
- { category: games, ... }

- { category: [ mail-client, mail-filter, mail-mta ], ... }
```

#### name

Match exact package name(s).

```yaml
- { name: firefox, ... }

- { name: [postgresql-client, postgresql-server, postgresql-contrib], ... }
```

#### namepat

Matches package name against a regular expression. Whole name is
matched. May contain captures.

```yaml
- { name: "swig[0-9]+", ... }
```

#### ver

Matches exact package version(s).

```yaml
- { name: firefox, ver: "50.0.1", ... }
```

#### verpat

Matches package version name against a regular expression. Whole
version is matched. Note that you need to escape periods which
mean "any symbol" in regular expressions. Matching is case insensitive.

```yaml
- { name: firefox, verpat: "50\\.[0-9]+", ... }

- { name: firefox, verpat: "50\\..*", ... }
```

#### verlonger

Matches versions longer than a given number of dot-separated parts.

Mostly useful to match broken version schemes with extra versions
components added.

```yaml
- { name: gimp, verlonger: 3, ...} # 2.9.8.12345 is something unofficial
```

#### vergt, verge, verlt, verle

Compares version to a given one and matches if it's:

- **vergt**: greater (>)
- **verge**: greater or equal (>=)
- **verlt**: lesser (<)
- **verle**: lesser or equal (<=)

```yaml
# match git >= 2.16
- { name: git, verge: "2.16", ...}
```

Be careful when using this with regard to pre-release versions:
`1.0beta1` is lesser than `1.0`, so it won't match `verge: 1.0`.
You may use **verpat** instead.

#### wwwpat

Matches package homepage against a regular expression. Note that
unlike namepat and verpat, partial match is allowed here. Also
note that it's preferred to escape dots with double slash, as `.`
means "any character" in regular expressions.

```yaml
- { name: firefox, wwwpat: "mozilla\\.org", ... }
```

#### wwwpart

Matches when a package homepage contains given substring. This
is usually more practical than **wwwpat** as in most cases you
just need to match an URL part and don't need complex patterns,
also you don't want to bother with escaping here.

```yaml
- { name: firefox, wwwpart: "mozilla.org", ... }
```

### Actions

#### setname

Effectively rename the package. You may use `$0` placeholder to
substitute original name or `$1`, `$2` etc. to subsided contents
of corresponding captures of regular expression used in **namepat**.
Note that you don't need to use neither **name** nor **namepat** for
`$0` to work, but you must have **namepat** with corresponding
captures to use `$1` and so on.

```yaml
# etracer→extreme-tuxracer
- { name: etracer, setname: extreme-tuxracer }

# aspell-dict-en→aspell-ru, aspell-dict-ru→aspell-ru etc.
- { namepat: "aspell-dict-(.*)", setname: "aspell-$1" }

# all packages in dev-perl Gentoo category are prepended `perl:`
# Locale-Msgfmt→perl:Locale-Msgfmt
- { ruleset: gentoo, category: dev-perl, setname: "perl:$0" }
```

#### setver

Changes the version of the package. As with **setname**, you may
use `$0`, `$1` placeholders.

```yaml
# remove bogus leading version component
- { verpat: "0\\.(.*)", setver: $1 }
```

#### remove

Set to `true` to completely remove package. It will not appear
anywhere in repology. Set to `false` to undo.

```yaml
# a metapackage which does not refer to any real project, we don't need it
- { name: "x11-fonts", remove: true }
```

#### devel

Set to `true` to mark version of matched package as development or
unstable version, so it does not make latest stable version outdated.
Set to `false` to undo.

```yaml
# mark versions with odd second component as devel
- { name: gnome-terminal, verpat: "[0-9]+\\.[0-9]*[13579]\\..*", devel: true }
```

#### ignore, incorrect, untrusted, noscheme, snapshot, successor, rolling

Set to `true` to ignore specific package versions. This is meant for the
cases where comparison is not possible - ignore version are excluded from
comparison and do not affect status of other versions. There are multiple
ignore flavors:

- `rolling` - package is fetched from always latest snapshot or VCS
  master/trunk. Its version has no meaning (like Gentoo's `9999`),
  it may contain repository specific format of commit hash, revision or
  date.
- `noscheme` - there's no official versioning scheme. Repositories may
  use random versions or dates, there's no point comparing them.
- `incorrect` - known incorrect version (e.g. version which was not
  released yet)
- `untrusted` - used for repositories which are known for providing
  incorrect versions, to ignore them proactively. It's common pattern
  to create a pair of `incorrect` rule matching specific version and
  `untrusted` rule for the following versions in a given repository.
- `ignored` - general ignore
- `successor` - currently alias for `devel` used to convey additional
  meaning: this is a fork of unmaintained original project
- `snapshot` - currently alias for `ignored`

```yaml
# Fedora was known to use "6.0.0" version before it was actually released
# mark as incorrect and prevent future problems
- { name: llvm, ver: "6.0.0", family: fedora, incorrect: true }
- { name: llvm, family: fedora, untrusted: true }
```

#### p_is_patch

Set to `true` to indicate that this project uses `p` letter in version
to indicate post- or patch releases. This fixes version comparison, as
by default `p` is treated as pre-release.

```yaml
# sudo 1.8.21p2 > 1.8.21
- { name: sudo, p_is_patch: true }
```

#### any_is_patch

Set to `true` to indicate that this project uses any letter in version
to indicate post- releases.

```yaml
# rb here denotes a patchset, treat is as such
- { name: webalizer, verpat: ".*rb.*", any_is_patch: true }
```

#### outdated

Set to `true` to force the package to be outdated, even if its version
is compared as greatest. `false` to undo.

```yaml
# when 0.20 follows 0.193:
- { version: "0.193", outdated: true }
```

#### legacy

Set to `true` to force the package to be legacy instead of outdated.
`false` to undo. Useful when a specific repository purposely contains
an outdated version of specific project for compatibility purposes.

```yaml
- { name: ruby-slack-notifier-1, ruleset: aur, legacy: true }
```

#### warning

Output a given warning when matched. Useful to catch places which

```yaml
# will catch unexpected versions
- { name: gtk, verpat: "1\\..*", setname: gtk1 }
- { name: gtk, verpat: "2\\..*", setname: gtk2 }
- { name: gtk, verpat: "3\\..*", setname: gtk3 }
- { name: gtk, verpat: "4\\..*", setname: gtk4 }
- { name: gtk, warning: "Neither of gtk1,2,3,4 - need a new rule or some weirdness is going on" }

# will trigger a warning if new project called "tesseract" appears
# ...or website changes, or just a package without website defined appears,
# so it'll require another condition
- { name: tesseract, setname: tesseract-game, wwwpart: tesseract.gg }
- { name: tesseract, setname: tesseract-ocr, wwwpart: tesseract-ocr }
- { name: tesseract, warning: "Please add rule for tesseract" }
```

#### addflavor

Flavors are used to distinct set of packages denoting a multiple
version of a project and a set of packages denoting a multiple parts
or variants of a project. Consider an example:

- `foo1 1.0` and `foo2 2.0` merged into `foo`. In this case they denote
  a multiple versions of the same project, flavors are not needed here
  and `foo1` will have `legacy` status.
- `foo-client 1.0` and `foo-server 1.1` merged into `foo`. In this case
  they denote a parts of the same project, which are expected to be of
  the same version. Flavors should be used in this case, so `foo-client`
  will have `outdated` status.

Flavors a plain strings and may be arbitrary, for example `client`
and `server` in the last example. You may specify flavor explicitly
or use `true` value to make flavor taken from the package name.

```yaml
- { name: postgresql-client, setname: postgresql, addflavor: client }
- { name: postgresql-server, setname: postgresql, addflavor: server }

# This works too
- { name: [postgresql-client, postgresql-server], setname: postgresql, addflavor: true }
```

#### resetflavors

Set to `true` to remove all previously added flavors.

#### last

Set to `true` to stop ruleset processing right after the current rule.

Consider this a legacy, it should not be needed

#### replaceinname

Takes pattern and replacement strings and applies them to the package
name. Used for low-level normalization.

```yaml
# slashes in package names are not allowed
- { replaceinname: { "/": "-" } }

# also useful for some repositories
- { replaceinname: { " ": "-" } }
```

#### tolowername

Converts a package name to lowercase. This is called once in the
very beginning of the ruleset. The purpose of having this as a rule
action is to be able to have exceptions, e.g. packages which should
be distinguished solely by the case of their names.

```yaml
- { tolowername: true }
```

### Conditional rules

For additional flexibility, a mechanism exists to toggle some rules
based on the previous rules.

#### addflag

Sets a virtual flag (arbitrary string) which only exists for the duration
of rule processing and may be checked in the following rules.

```yaml
- { name: python, addflag: not_python_module }
```

#### flag, noflag

Only matches if the specified flag is (or is not) set.

```yaml
- { name: python, addflag: not_python_module }
...
# will add "python:" prefix to all packages in category "python",
# but not for "python" package
- { category: python, noflag: not_python_module, setname: "python:$0" }
```

### Annotations

These annotations do not affect package processing, but are related
to ruleset maintenance.

#### maintenance

Indicates that a rule needs manual maintenance. For example, when
development version cannot be determined from the version schema,
one would need to revisit and update the version occasionally.

```yaml
- { name: tor, verge: "0.3.4", devel: true, maintenance: true }
```

#### precious

Indicates that a rule should not be removed even if it doesn't
match any packages. That is, a rule is likely to be useful sometime
in the future.

#### disposable

Indicates that a rule may be removed if it doesn't match any packages.

## Author

* [Dmitry Marakasov](https://github.com/AMDmi3) <amdmi3@amdmi3.ru>

## License

GPLv3 or later, see [COPYING](COPYING).
