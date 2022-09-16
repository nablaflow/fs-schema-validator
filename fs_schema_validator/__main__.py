#!/usr/bin/env python

import sys
from pathlib import Path
from typing import List, Any

import click
import pydantic

from fs_schema_validator import Schema
from fs_schema_validator.string_expander.parser import ParseError, parse_assignment
from fs_schema_validator.string_expander.values import Assignment


class BindingParamType(click.ParamType):
    name = "binding"

    def convert(self, value: str, param: Any, ctx: Any) -> Assignment:
        try:
            return parse_assignment(value)
        except ParseError as e:
            self.fail(f"binding cannot be parsed: {e}", param, ctx)


@click.command()
@click.option(
    "--root-dir",
    "-r",
    type=click.Path(exists=True, readable=True, file_okay=False, path_type=Path),
    default=Path.cwd(),
    envvar="VALIDATION_ROOT_DIR",
    help="The directory to use as root for all paths specified inside the schema. Defaults to $CWD.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
)
@click.option("--binding", "-b", multiple=True, type=BindingParamType(), default=[])
@click.argument(
    "schema_path",
    type=click.Path(exists=True, readable=True, dir_okay=False, path_type=Path),
    envvar="VALIDATION_SCHEMA_PATH",
)
def validate(
    schema_path: Path, root_dir: Path, verbose: bool, binding: List[Assignment]
) -> None:
    """Validate a schema against a directory

    SCHEMA is a path to a YAML file.
    """

    if verbose:
        click.echo(f"Schema path: {schema_path}")
        click.echo(f"Root dir: {root_dir}")
        click.echo()

    with schema_path.open() as f:
        try:
            schema = Schema.from_yaml(f)
        except (pydantic.ValidationError, UnicodeDecodeError) as e:
            click.secho(f"❗️ The provided schema is invalid!", fg="red")
            click.echo("")
            click.secho(e, fg="red")
            sys.exit(127)

    extra_bindings = dict(binding)

    if verbose and len(extra_bindings) > 0:
        click.secho("⚠️  Overriding the following bindings:", fg="yellow")

        for k, v in extra_bindings.items():
            click.echo(f"  {k} = {v}")

        click.echo()

    report = schema.validate_(root_dir, extra_bindings)

    if verbose:
        click.echo(f"Inspected {report.count()} files.")
        click.echo()

    for valid_path in report.valid_paths:
        click.secho(f"✅ {valid_path}", fg="green")

    if report.okay():
        return

    click.echo()

    for path, reasons in report.grouped_by_path():
        click.secho(f"❗️ {path}", fg="red")

        for reason in reasons:
            click.secho(f"     - {reason}")

    sys.exit(1)


if __name__ == "__main__":
    validate()
