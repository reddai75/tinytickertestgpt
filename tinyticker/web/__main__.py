import argparse
import logging
import sys
from pathlib import Path
from typing import List

from .. import config as cfg
from ..display import Display
from ..settings import CONFIG_FILE, LOG_DIR, generate_qrcode, set_verbosity
from ..utils import RawTextArgumentDefaultsHelpFormatter
from .app import LOGGER as APP_LOGGER
from .app import create_app

LOGGER = logging.getLogger(__name__)


def parse_args(args: List[str]) -> argparse.Namespace:
    """Parse the command line arguments.

    Args:
        args: The command line argument.

    Returns:
        The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        prog="tinyticker-web",
        description="tinyticker web interface.",
        formatter_class=RawTextArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-p",
        "--port",
        default=7104,
        type=int,
        help="Port number.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbosity.",
        action="count",
        default=0,
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Config file.",
        type=Path,
        default=CONFIG_FILE,
    )
    parser.add_argument(
        "-q",
        "--show-qrcode",
        help="Display a qrcode containing the URL of the dashboard and exit.",
        action="store_true",
    )
    parser.add_argument(
        "--log-dir",
        help="Directory containing tinyticker's log files.",
        type=Path,
        default=LOG_DIR,
    )
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    if args.verbose > 0:
        set_verbosity(LOGGER, args.verbose)
        set_verbosity(APP_LOGGER, args.verbose)

    LOGGER.debug("Args: %s", args)

    if not args.log_dir.is_dir():
        args.log_dir.mkdir(parents=True)

    if args.show_qrcode:
        LOGGER.info("Generating qrcode.")
        tt_config = cfg.TinytickerConfig.from_file(args.config)
        display = Display.from_tinyticker_config(tt_config)
        qrcode = generate_qrcode(
            display.epd.width,
            display.epd.height,
            args.port,
        )
        LOGGER.info("Displaying qrcode.")
        display.show_image(qrcode)
        del display
        sys.exit()

    LOGGER.info("Starting tinyticker-web")
    app = create_app(config_file=args.config, log_dir=args.log_dir)
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
    LOGGER.info("Stopping tinyticker-web")


if __name__ == "__main__":
    main()
