import typer
from .run import run_command
from .group_brands import group_brands_command
from .group_parent_companies import group_parent_companies_command
from .sentiment import sentiment_command
from .ad_sentiment import ad_sentiment_command
from .deep_sentiment import deep_sentiment_command
from .run_everything import run_everything_command
from .parent_company_sentiment import parent_company_sentiment_command
from .parent_company_deep_sentiment import parent_company_deep_sentiment_command
from .agentic_emotion import agentic_emotion_command

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
app.command('run-everything')(run_everything_command)
app.command('parent-company-sentiment')(parent_company_sentiment_command)
app.command('parent-company-deep-sentiment')(parent_company_deep_sentiment_command)
app.command('agentic-emotion')(agentic_emotion_command)


def main():
    app()


if __name__ == '__main__':
    main()
