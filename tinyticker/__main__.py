import argparse
import atexit
import logging
import os
import sys
from typing import List

from . import config, logger
from .config import DEFAULT, TYPES
from .display import Display
from .settings import CONFIG_FILE, PID_FILE, set_verbosity
from .ticker import INTERVAL_LOOKBACKS, Ticker


class RawTextArgumentDefaultsHelpFormatter(
    argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
):
    pass


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""Raspberry Pi crypto ticker using an LCD display.

Note:
    Make sure SPI is enabled on your RPi.
""",
        formatter_class=RawTextArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a",
        "--api-key",
        help="CryptoCompare API key, https://min-api.cryptocompare.com/pricing.",
        type=str,
        default=DEFAULT["api_key"],
    )
    parser.add_argument(
        "-c",
        "--coin",
        help="Crypto coin.",
        type=str,
        default=DEFAULT["coin"],
    )
    parser.add_argument(
        "-C",
        "--currency",
        help="Display currency.",
        type=str,
        default=DEFAULT["currency"],
    )
    parser.add_argument(
        "-i",
        "--interval",
        help="Interval.",
        type=str,
        default=DEFAULT["interval"],
        choices=INTERVAL_LOOKBACKS.keys(),
    )
    parser.add_argument(
        "-l",
        "--lookback",
        help="Look back amount.",
        type=int,
        default=DEFAULT["lookback"],
    )
    parser.add_argument(
        "-w",
        "--wait-time",
        help="Wait time in seconds.",
        type=int,
        default=DEFAULT["wait_time"],
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Plot style, see mplfinance.",
        type=str,
        default=DEFAULT["type"],
        choices=TYPES,
    )
    parser.add_argument(
        "-f",
        "--flip",
        help="Flip the display.",
        action="store_true",
    )

    parser.add_argument("-v", "--verbose", help="Verbosity.", action="count", default=0)
    parser.add_argument(
        "--config",
        help=f"Take values from config file: {CONFIG_FILE}",
        action="store_true",
    )
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    args = vars(args)
    if args["config"]:
        # upadte the values if theyare not None
        # allows for using other args to set values not set in the config file
        args.update({k: v for k, v in config.read().items() if v is not None})

    if args["verbose"] > 0:
        set_verbosity(logger, args["verbose"])

    logger.debug("Args: %s", args)
    if not args["api_key"]:
        logger.error("No API key provided.")
        raise ValueError("No API key provided.")

    display = Display(
        args["coin"],
        args["currency"],
        flip=args["flip"],
    )
    ticker = Ticker(
        args["api_key"],
        coin=args["coin"],
        currency=args["currency"],
        interval=args["interval"],
        lookback=args["lookback"],
        wait_time=args["wait_time"],
    )

    def cleanup(display: Display):
        logger.info("Exiting.")
        if PID_FILE.is_file():
            PID_FILE.unlink()
        del display

    atexit.register(cleanup, display)

    with open(PID_FILE, "w") as pid_file:
        pid = os.getpid()
        logger.info("PID: %s", pid)
        pid_file.write(str(pid))

    try:
        for historical, current in ticker.tick():
            logger.debug("API response[0]: %s", historical[0])
            logger.debug("API len(response): %s", len(historical))
            display.plot(
                historical,
                current,
                sub_string=f"{ticker.lookback} {args['interval']}s",
                type=args["type"],
                show=True,
            )
    except Exception as e:
        logger.error(e, stack_info=True)
        display.text(str(e), show=True)
