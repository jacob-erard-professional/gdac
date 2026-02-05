import typer
from .run import run_command
from .group_brands import group_brands_command
from .group_parent_companies import group_parent_companies_command
from .sentiment import sentiment_command
from .ad_sentiment import ad_sentiment_command
from .deep_sentiment import deep_sentiment_command

app = typer.Typer(add_completion=False)


@app.callback()
def root():
    """Super Bowl analytics CLI."""
    return None


app.command('run')(run_command)
app.command('group-brands')(group_brands_command)
app.command('group-parent-companies')(group_parent_companies_command)
app.command('sentiment')(sentiment_command)
app.command('ad-sentiment')(ad_sentiment_command)
app.command('deep-sentiment')(deep_sentiment_command)


def main():
    app()


if __name__ == '__main__':
    main()
