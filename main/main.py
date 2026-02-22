import argparse
import logging
import os

from dotenv import load_dotenv

from mbta_client.client import MBTAClient
from mbta_client.config import MBTAConfig
from repositories.subway_repository import SubwayRepository
from services import BroadQuestionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_secrets() -> None:
    """Load secrets from .env file for local development."""
    load_dotenv()


def build_config() -> MBTAConfig:
    """Build MBTA API configuration from environment variables."""
    api_key = os.getenv("MBTA_API_KEY")
    if not api_key:
        raise RuntimeError("MBTA_API_KEY is not set")
    return MBTAConfig(api_key=api_key)


def parse_args():
    parser = argparse.ArgumentParser(description="Broad MBTA screen")

    subparsers = parser.add_subparsers(
        dest="command", required=True  # Forces user to choose a command
    )

    tech_screen_parser = subparsers.add_parser(
        "tech-screen", help="Plan a trip between two stops"
    )

    tech_screen_parser.add_argument(
        "--start",
        "-s",
        type=str,
        required=True,
        help='Starting stop name (e.g., "Park Street")',
    )

    tech_screen_parser.add_argument(
        "--stop",
        "-e",
        type=str,
        required=True,
        help='Destination stop name (e.g., "South Station")',
    )

    subparsers.add_parser("list-stops", help="List all available stops")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_secrets()
    config = build_config()

    client = MBTAClient(config)
    repository = SubwayRepository(client)

    try:
        service = BroadQuestionService(client, repository)
        if args.command == "tech-screen":
            service.answer_all_questions(start_stop=args.start, final_stop=args.stop)
        elif args.command == "list-stops":
            stops = [stop for stop in service.subway_map.subway_graph.keys()]
            logger.info(
                f"\nStops available for --start and --stop:"
                f"\n  • " + "\n  • ".join(stops)
            )
    except Exception as e:
        logger.error(f"Error occurred: {type(e).__name__}: {e}", exc_info=True)
        return 1
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
