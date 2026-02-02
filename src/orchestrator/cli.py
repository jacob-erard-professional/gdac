import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Super Bowl analytics pipeline")
    parser.add_argument("--event", required=True)
    parser.add_argument("--year", type=int)
    parser.add_argument("--years", help="Comma-separated years for multi-year run")
    parser.add_argument("--config", required=True)
    return parser.parse_args()
