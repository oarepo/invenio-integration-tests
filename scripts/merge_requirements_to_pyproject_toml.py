import dataclasses
from typing import Dict, Set

import click
import toml
from requirements.parser import parse as parse_requirements, Requirement


@click.command()
@click.argument("pyproject_toml_path", type=click.Path(exists=True), required=True)
@click.argument("requirement_files", nargs=-1, type=click.Path(exists=True))
@click.option("--blacklisted-requirements-file")
@click.option("--blacklisted-extras", multiple=True)
@click.option("--merge-extras", multiple=True)
def main(
    pyproject_toml_path,
    requirement_files,
    blacklisted_requirements_file,
    blacklisted_extras,
    merge_extras,
):
    """
    Merge requirements to pyproject.toml
    """
    blacklisted_extras = set(
        y.strip() for x in blacklisted_extras for y in x.split(",") if y.strip()
    )
    merge_extras = {
        y.split(":")[0].strip(): y.split(":")[1].strip()
        for x in merge_extras
        for y in x.split(",")
        if ":" in y
    }

    with open(pyproject_toml_path, "r") as f:
        pyproject_toml = toml.load(f)

    blacklisted_requirements = set({})
    if blacklisted_requirements_file:
        with open(blacklisted_requirements_file, "r") as f:
            blacklisted_requirements.update(
                [x.name for x in parse_requirements(f.read())]
            )

    requirements = GroupedRequirements()

    for requirement_file in requirement_files:
        click.secho(
            f"\n\nProcessing {requirement_file}\n=====================================",
            fg="green",
        )
        with open(requirement_file, "r") as f:
            for group, reqs in parse_grouped_requirements(f.readlines()).items():
                if group in blacklisted_extras:
                    continue
                group = merge_extras.get(group, group)
                for r in reqs:
                    if r.name in blacklisted_requirements:
                        click.secho(
                            f"Skipping blacklisted requirement {serialize_requirement(r)}",
                            fg="yellow",
                        )
                        continue
                    requirements.add_requirement(group, r)

    pyproject_toml["project"]["dependencies"] = []
    pyproject_toml["project"]["optional-dependencies"] = {}

    for section in requirements.sections:
        if section.name == "default":
            pyproject_toml["project"]["dependencies"] = section.as_list()
        else:
            pyproject_toml["project"]["optional-dependencies"][
                section.name
            ] = section.as_list()

    with open(pyproject_toml_path, "w") as f:
        toml.dump(pyproject_toml, f)

    click.secho(toml.dumps(pyproject_toml), fg="green")


@dataclasses.dataclass
class RequirementSet:
    name: str
    requirements: Dict[str, Requirement] = dataclasses.field(default_factory=dict)

    def add_requirement(self, requirement):
        if requirement.name not in self.requirements:
            click.secho(
                f"Adding new requirement {serialize_requirement(requirement)} into group {self.name or 'default'}",
                fg="green",
            )
            self.requirements[requirement.name] = requirement
        else:
            # merge the two requirements, honouring
            existing_requirement = self.requirements[requirement.name]
            existing_version = existing_requirement.specs
            incoming_version = requirement.specs
            click.secho(
                f"Merging requirement {serialize_requirement(requirement)} with existing {serialize_requirement(existing_requirement)}",
                fg="yellow",
            )
            self.requirements[requirement.name] = Requirement.parse_line(
                serialize_requirement(
                    requirement, merge_versions(existing_version, incoming_version)
                )
            )
            click.secho(
                f"Merged: {serialize_requirement(self.requirements[requirement.name])} "
                f"into group {self.name or 'default'}",
                fg="green",
            )

    def as_list(self):
        return [
            serialize_requirement(requirement)
            for requirement in self.requirements.values()
        ]


@dataclasses.dataclass
class GroupedRequirements:
    _sections: Dict[str, RequirementSet] = dataclasses.field(default_factory=dict)

    def add_requirement(self, section, requirement):
        if section not in self._sections:
            self._sections[section] = RequirementSet(section)
        self._sections[section].add_requirement(requirement)

    @property
    def sections(self):
        return self._sections.values()


def parse_grouped_requirements(requirement_lines):
    """
    Splits requirement lines into groups separated by [groupname] lines.
    Parses each group separately and returns a dictionary of groupname -> list of requirements
    """
    current_group_name = "default"
    current_group = []
    groups = {current_group_name: current_group}
    for line in requirement_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("["):
            current_group_name = line[1:-1]
            current_group = []
            groups[current_group_name] = current_group
        else:
            current_group.append(Requirement.parse_line(line))
    return groups


def serialize_requirement(requirement, specs=None):
    """
    Serialize a requirement to a string.

    doctests:
    >>> serialize_requirement(Requirement.parse_line('Flask>=1.0.0'))
    'Flask>=1.0.0'
    >>> serialize_requirement(Requirement.parse_line('Flask [extra] >=1.0.0'))
    'Flask[extra]>=1.0.0'
    """
    extras = ("[" + ",".join(requirement.extras) + "]") if requirement.extras else ""
    return f"{requirement.name}{extras}{serialize_version(specs or requirement.specs)}"


def serialize_version(specs):
    """
    Serialize version specs to a string.

    doctests:
    >>> serialize_version([('>', '1.0.0'), ('<', '2.0.0')])
    '>1.0.0,<2.0.0'
    >>> serialize_version([('>', '1.0.0'), ('<=', '2.0.0')])
    '>1.0.0,<=2.0.0'
    >>> serialize_version([('==', '1.5.0')])
    '==1.5.0'
    """
    return ",".join([f"{op}{version}" for op, version in specs])


def merge_versions(existing_version, incoming_version):
    """
    Merges two version specs. It can handle only specs containing '>', '<', '>=', '<=', '=='.
    Wildcards are not supported.

    doctests:
    >>> merge_versions([('>', '1.0.0'), ('<', '2.0.0')], [('>', '1.0.0'), ('<', '2.0.0')])
    [('>', '1.0.0'), ('<', '2.0.0')]

    >>> merge_versions([('>', '1.0.0'), ('<', '2.0.0')], [('>=', '1.0.0'), ('<', '2.0.0')])
    [('>', '1.0.0'), ('<', '2.0.0')]

    >>> merge_versions([('>', '1.0.0'), ('<', '2.0.0')], [('>=', '1.5.0'), ('<', '2.0.0')])
    [('>=', '1.5.0'), ('<', '2.0.0')]

    >>> merge_versions([('>', '1.0.0'), ('<', '2.0.0')], [('>=', '1.5.0'), ('<=', '2.1.0')])
    [('>=', '1.5.0'), ('<', '2.0.0')]

    >>> merge_versions([('>', '1.0.0'), ('<', '2.0.0')], [('>=', '1.5.0'), ('<=', '1.8.0')])
    [('>=', '1.5.0'), ('<=', '1.8.0')]

    >>> merge_versions([('>', '1.0.0'), ('<=', '2.0.0')], [('>=', '2.0.0'), ('<=', '3.0.0')])
    [('==', '2.0.0')]

    """

    (
        existing_version_greater,
        existing_version_greater_inclusive,
        existing_version_lower,
        existing_version_lower_inclusive,
    ) = get_version_bounds(existing_version)

    (
        incoming_version_greater,
        incoming_version_greater_inclusive,
        incoming_version_lower,
        incoming_version_lower_inclusive,
    ) = get_version_bounds(incoming_version)

    merged_version_lower = None
    merged_version_lower_inclusive = None
    merged_version_greater = None
    merged_version_greater_inclusive = None

    if existing_version_lower or incoming_version_lower:
        merged_version_lower = min(
            existing_version_lower or incoming_version_lower,
            incoming_version_lower or existing_version_lower,
        )
        merged_version_lower_inclusive = True
        if merged_version_lower == existing_version_lower:
            merged_version_lower_inclusive = (
                merged_version_lower_inclusive and existing_version_lower_inclusive
            )
        if merged_version_lower == incoming_version_lower:
            merged_version_lower_inclusive = (
                merged_version_lower_inclusive and incoming_version_lower_inclusive
            )

    if existing_version_greater or incoming_version_greater:
        merged_version_greater = max(
            existing_version_greater or incoming_version_greater,
            incoming_version_greater or existing_version_greater,
        )
        merged_version_greater_inclusive = True
        if merged_version_greater == existing_version_greater:
            merged_version_greater_inclusive = (
                merged_version_greater_inclusive and existing_version_greater_inclusive
            )
        if merged_version_greater == incoming_version_greater:
            merged_version_greater_inclusive = (
                merged_version_greater_inclusive and incoming_version_greater_inclusive
            )

    ret_version = []
    if merged_version_lower == merged_version_greater:
        ret_version.append(("==", merged_version_lower))
    else:
        if merged_version_greater:
            ret_version.append(
                (
                    merged_version_greater_inclusive and ">=" or ">",
                    merged_version_greater,
                )
            )
        if merged_version_lower:
            ret_version.append(
                (merged_version_lower_inclusive and "<=" or "<", merged_version_lower)
            )
    return ret_version


def get_version_bounds(specs):
    """
    Returns a tuple of (greater_version, greater_inclusive, lower_version, lower_inclusive)
    If the version is ==, then the returned greater_version and lower_version are the same
    and greater_inclusive and lower_inclusive are True.

    doctests:
    >>> get_version_bounds([('>', '1.0.0'), ('<', '2.0.0')])
    ('1.0.0', False, '2.0.0', False)
    >>> get_version_bounds([('>=', '1.0.0'), ('<=', '2.0.0')])
    ('1.0.0', True, '2.0.0', True)
    >>> get_version_bounds([('>', '1.0.0'), ('<=', '2.0.0')])
    ('1.0.0', False, '2.0.0', True)
    >>> get_version_bounds([('==', '1.5.0')])
    ('1.5.0', True, '1.5.0', True)
    """
    existing_version_lower, existing_version_lower_inclusive = find_version("<", specs)
    existing_version_equal, __ = find_version("==", specs)
    existing_version_greater, existing_version_greater_inclusive = find_version(
        ">", specs
    )

    if existing_version_equal:
        existing_version_lower = existing_version_equal
        existing_version_greater = existing_version_equal
        existing_version_lower_inclusive = True
        existing_version_greater_inclusive = True
    return (
        existing_version_greater,
        existing_version_greater_inclusive,
        existing_version_lower,
        existing_version_lower_inclusive,
    )


def find_version(op, specs):
    """
    Finds a version with operator op ('>', '<') in specs.
    Returns a tuple of (version, inclusive) or tuple(None, None) if not found.

    doctest examples:
    >>> find_version('>', [('>', '1.0.0'), ('<', '2.0.0')])
    ('1.0.0', False)
    >>> find_version('>', [('>', '1.0.0'), ('<', '2.0.0'), ('==', '1.5.0')])
    ('1.0.0', False)
    >>> find_version('>', [('>=', '1.0.0'), ('<', '2.0.0')])
    ('1.0.0', True)
    >>> find_version('<', [('>=', '1.0.0'), ('<', '2.0.0')])
    ('2.0.0', False)
    >>> find_version('<', [('>=', '1.0.0'), ('<=', '2.0.0')])
    ('2.0.0', True)
    >>> find_version('==', [('>=', '1.0.0'), ('<=', '2.0.0')])
    (None, None)
    >>> find_version('==', [('==', '1.5.0')])
    ('1.5.0', True)

    """
    for specs_op, specs_version in specs:
        if op == "==" and specs_op == "==":
            return specs_version, True
        elif op == specs_op:
            return specs_version, False
        elif op == ">" and specs_op == ">=":
            return specs_version, True
        elif op == "<" and specs_op == "<=":
            return specs_version, True
    return None, None


if __name__ == "__main__":
    main()
