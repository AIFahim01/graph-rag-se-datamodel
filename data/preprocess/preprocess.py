#!/usr/bin/env python3

import argparse
import datetime
import logging
import os
import time

from console_watcher import TqdmLoggingHandler


def configure_logging() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    log_filepath = os.path.join(log_dir, log_filename)

    file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
    tqdm_handler = TqdmLoggingHandler()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[file_handler, tqdm_handler],
        force=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess PDF documents.")
    parser.add_argument("-i", "--input", dest="input_folder", help="Input folder path.")
    parser.add_argument("-o", "--output", dest="output_folder", help="Output folder path.")
    return parser.parse_args()


def main() -> int:
    configure_logging()
    logger = logging.getLogger("preprocess")
    args = parse_args()

    input_folder = args.input_folder or input("Input folder: ").strip()
    output_folder = args.output_folder or input("Output folder: ").strip()

    if not input_folder or not output_folder:
        logger.error("Both input and output folders are required.")
        return 1

    input_folder = os.path.abspath(os.path.expanduser(input_folder))
    output_folder = os.path.abspath(os.path.expanduser(output_folder))

    logger.info("Starting preprocessing from '%s' to '%s'", input_folder, output_folder)

    if not os.path.isdir(input_folder):
        logger.error("Input folder does not exist or is not a directory: %s", input_folder)
        return 1
    
    start_time = time.perf_counter()

    from orchestrator import DataPreprocessingOrchestrator

    orchestrator = DataPreprocessingOrchestrator(input_folder, output_folder)
    success = orchestrator.run()

    end_time = time.perf_counter()
    logger.info("Preprocessing completed in %.2f seconds", end_time - start_time)
    
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())