import typer
from .run import run_command
from .group_brands import group_brands_command

app = typer.Typer(add_completion=False)


@app.callback()
def root():
    """Super Bowl analytics CLI."""
    return None


app.command('run')(run_command)
app.command('group-brands')(group_brands_command)


def main():
    app()


if __name__ == '__main__':
    main()
