import typer

from .commands.server import server_app
from .commands.file import fs_general_app

app: typer.Typer = typer.Typer()
app.add_typer(server_app, name="server")
app.add_typer(fs_general_app)