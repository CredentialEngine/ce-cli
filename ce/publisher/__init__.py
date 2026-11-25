"""Publisher command group: API publishing to the Credential Registry.

The files follow the commands, as in ceops: a noun is a folder and a verb is a Python file that exposes its Click
command as `main`. The shared code is in `ce.implementations.publisher`.

    ce publisher project create                  ce/publisher/project/create.py
    ce publisher project add                     ce/publisher/project/add.py
    ce publisher project list                    ce/publisher/project/list.py
    ce publisher project complete                ce/publisher/project/complete.py
    ce publisher project abandon                 ce/publisher/project/abandon.py
    ce publisher project status show             ce/publisher/project/status/show.py
    ce publisher project audit show              ce/publisher/project/audit/show.py
    ce publisher project validation run          ce/publisher/project/validation/run.py
    ce publisher project validation status show  ce/publisher/project/validation/status/show.py
    ce publisher project validation errors show  ce/publisher/project/validation/errors/show.py

The text `ce publisher --help` shows comes from the docstrings of the groups and commands.
"""

from __future__ import annotations

import click

from ce.publisher.project import main as project_group


@click.group("publisher")
def main() -> None:
    """Publish resources to the Credential Registry through the Publisher.

    \b
    A project collects the files you publish together:
      1. ce publisher project create --name "My project"
      2. ce publisher project add --project-id N --file credentials.csv --type credentials
      3. ce publisher project validation run --project-id N
      4. ce publisher project validation errors show --project-id N
      5. fix the files and add them again, then validate again
      6. ce publisher project complete --project-id N

    \b
    Files are BU template CSVs (a BU project, the default), or JSON-LD in the
    shape the CSV transform produces (create the project with --jsonld).
    """


main.add_command(project_group, name="project")
