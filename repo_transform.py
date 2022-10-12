import os
import argparse
import json
import logging
from pathlib import Path
import settings
from datetime import datetime
import util
from pprint import pprint
import pandas as pd


def create_placeholder_measures_info(root_dir, test):
    """
    If a file suffix is found under a distribution under a data directory and measure_info does not exist, create a temporary one
    """
    measure_info_generated = []
    for path in Path(root_dir).rglob("data/distribution/**/*"):
        logging.info("Checking %s" % path)
        parent_dir = path.parent
        logging.debug(
            "\t[%s]: %s" % (not path.suffix in settings.SUFFIX_TO_MEASURE, path.suffix)
        )
        logging.debug(
            "\t[%s]: %s" % ("measure_info.json" in os.listdir(parent_dir), parent_dir)
        )
        if not path.suffix in settings.SUFFIX_TO_MEASURE:
            continue
        if "measure_info.json" in os.listdir(parent_dir):
            continue

        logging.debug("-" * 80)
        logging.debug("Conditions met")
        # if the file does exists but not the measure info
        with open("measure_info_template.json", "r") as f:
            measure_info = json.load(f)

        df = pd.read_csv(path.resolve())

        # if there are more columns than prescribed, remove it
        # if not set(df.columns) == set(settings.MEASURE_COLS):
        #     logging.debug("=" * 80)
        #     logging.debug("Column difference found: %s" % path.resolve())
        #     df = df[settings.MEASURE_COLS]
        #     if not test:
        #         df.to_csv(path.resolve(), index=False)

        logging.debug(df)
        logging.debug("columns: %s" % df.columns)
        logging.debug(measure_info)

        measures = sorted(df["measure"].unique())
        final = []
        for measure in measures:
            mi = measure_info.copy()
            mi["measure_table"] = path.name
            mi["measure"] = measure
            mi["type"] = df[df["measure"] == measure]["measure_type"].unique()[0]
            pprint(mi)
            final.append(mi)

        export_measure_info_path = os.path.join(
            parent_dir.resolve(), "measure_info.json"
        )
        logging.info("Placeing measure_info into %s" % export_measure_info_path)
        measure_info_generated.append(export_measure_info_path)
        if not test:
            with open(export_measure_info_path, "w") as f:
                json.dump(final, f, indent=4, sort_keys=True)
    logging.info("=" * 80)
    logging.info(
        "[%s] Measure infos generated %s"
        % (len(measure_info_generated), measure_info_generated)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UVA BI SDAD audit a Data Repository")
    parser.add_argument(
        "-i",
        "--input_root",
        type=str,
        help="The root directory that needs to be audited",
        required=True,
    )
    parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction)
    parser.add_argument("-t", "--test", action=argparse.BooleanOptionalAction)

    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    if not os.path.isdir(args.input_root):
        logging.info("%s is not a directory", (args.input_root))
    else:
        logging.info("Auditing: %s", os.path.abspath(args.input_root))
        create_placeholder_measures_info(args.input_root, args.test)
