import typer
from .run import run_command

app = typer.Typer(add_completion=False)
app.command('run')(run_command)


def main():
    app()


if __name__ == '__main__':
    main()
