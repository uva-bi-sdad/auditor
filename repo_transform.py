from dataclasses import replace
import os
import argparse
import json
import logging
from pathlib import Path
import traceback
import settings
from datetime import datetime
import util
from pprint import pprint
import pandas as pd
import os

def delete_all_empty_measure_infos(root_dir, test):
    """
    If a file suffix is found under a distribution under a data directory and measure_info does not exist, create a temporary one
    """
    logging.info("=" * 80)
    measure_info_deleted = []
    for path in Path(root_dir).rglob("data/distribution/**/*"):
        parent_dir = path.parent
        if "measure_info.json" in os.listdir(parent_dir):
            measure_path = os.path.abspath(os.path.join(parent_dir, "measure_info.json"))
            if os.stat(measure_path).st_size <= 0 :
                os.remove(measure_path)
                measure_info_deleted.append(measure_path)
    logging.info('[%s] Empty measure files deleted: %s' % (len(measure_info_deleted), measure_info_deleted))

def fix_list_measure_infos(root_dir, test):
    """
    If a file suffix is found under a distribution under a data directory and measure_info does not exist, create a temporary one
    """
    logging.info("=" * 80)
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
        if "measure_info.json" in os.listdir(parent_dir):
            measure_path = os.path.abspath(os.path.join(parent_dir, "measure_info.json"))
            logging.info('checking: %s' % measure_path)
            fix_list_measure_info(measure_path)

def fix_list_measure_info(measure_info_path):
    if os.stat(measure_info_path).st_size > 0 : # if the file size is larger than 0
        with open(measure_info_path, "r") as f:
            measure_info = json.load(f)
        replacement = {}
        print(measure_info)
        if isinstance(measure_info, list):
            logging.info('-'*80)
            logging.info('Malformed list measure info found: %s' % measure_info)
            for e in measure_info:
                if 'measure' in e:
                    logging.info('Measure found in %s' % e)
                    replacement[e['measure']] = e

            logging.info('Replacement: %s' % replacement)
            with open(measure_info_path, "w") as f:
                json.dump(replacement, f,indent=4, sort_keys=True)
            logging.info('Fixed list measure_info: %s '% measure_info_path)


def enforce_directory(root, dir, test):
    """
    assuming you are in a repository like data, docs, or code
    Check if "distribution" is in the folder. If not, create one and put an empty temp file in it.
    Otherwise, skip and don't do anything
    """
    # if the doc, data, or code directory does not exist, make one
    dir_path = os.path.join(root, dir)
    logging.info("Checking directory for: %s" % dir_path)

    if not os.path.isdir(dir_path):
        logging.info("\tGenerating directory %s" % dir_path)
        if not test:
            os.makedirs(dir_path)

    # if the distribution directory does not exist, make one
    sub_dir_file = os.path.join(dir_path, "distribution")
    if not os.path.isdir(sub_dir_file):
        logging.info("\t\tGenerating distribution directory: %s" % sub_dir_file)
        os.makedirs(sub_dir_file)

    # if inside there are no files, create a placeholder
    if len(os.listdir(sub_dir_file)) == 0:
        logging.info("\t\t\tGenerating placeholder empty file: %s/temp" % sub_dir_file)
        open(os.path.join(sub_dir_file, "temp"), "w").close()


def generate_placeholder_folders(root_dir, test):
    """
    If a file is found under distribution, go one layer up and see if it is missing from settings.DATA_REPO_DIRS
    """
    logging.info("=" * 80)
    for path in Path(root_dir).rglob("*/distribution/**/*"):
        for i in range(3):  # search 3 layers up
            grandparent_dir = path.parents[i].resolve()

            if (
                len(
                    set(settings.DATA_REPO_DIRS).intersection(
                        os.listdir(grandparent_dir)
                    )
                )
                > 0
            ):
                logging.info("Grandparent: %s" % grandparent_dir)
                for dir in settings.DATA_REPO_DIRS:
                    enforce_directory(grandparent_dir, dir, test)


def create_placeholder_measures_info(root_dir, test):
    """
    If a file suffix is found under a distribution under a data directory and measure_info does not exist, create a temporary one
    """
    logging.info("=" * 80)
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
        scriptpath = Path(os.path.realpath(__file__))

        with open(
            os.path.join(scriptpath.parent.resolve(), "measure_info_template.json"), "r"
        ) as f:
            measure_info = json.load(f)

        df = pd.read_csv(path.resolve())
        logging.debug(df)
        logging.debug("columns: %s" % df.columns)
        logging.debug(measure_info)

        final = {}
        if "measure" in df.columns:
            measures = sorted(df["measure"].unique())
            for measure in measures:
                mi = measure_info.copy()
                mi["measure_table"] = path.name.split('.')[0]
                mi["measure"] = measure
                mi["type"] = ""
                try:
                    # because sometimes the path is empty
                    mi["type"] = df[df["measure"] == measure]["measure_type"].unique()[
                        0
                    ]
                except:
                    pass
                pprint(mi)
                final[measure] = mi
                # final.append(mi)

        export_measure_info_path = os.path.join(
            parent_dir.resolve(), "measure_info_%s.json" % mi['measure_table']
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
    parser.add_argument("-m", "--make_measures", action=argparse.BooleanOptionalAction)
    parser.add_argument("-g", "--generate_folders", action=argparse.BooleanOptionalAction)
    parser.add_argument("-f", "--fix_measure_lists", action=argparse.BooleanOptionalAction)
    parser.add_argument("-d", "--delete_empty_measures", action=argparse.BooleanOptionalAction)
    parser.add_argument("-t", "--test", action=argparse.BooleanOptionalAction)

    args = parser.parse_args()
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level)

    if not os.path.isdir(args.input_root):
        logging.info("%s is not a directory", (args.input_root))
    else:
        logging.info("Transforming: %s", os.path.abspath(args.input_root))
        
        if args.fix_measure_lists:
            fix_list_measure_infos(args.input_root, args.test)

        if args.delete_empty_measures:
            delete_all_empty_measure_infos(args.input_root, args.test)

        if args.make_measures:
            create_placeholder_measures_info(args.input_root, args.test)
        
        if args.generate_folders:
            generate_placeholder_folders(args.input_root, args.test)
