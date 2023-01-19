import os
import argparse
import json
import logging
from pathlib import Path
import settings
from datetime import datetime
import util
from pprint import pprint
import traceback


"""
Given the path to a directory, generate a manifest file
[Finding files recursively] https://stackoverflow.com/questions/2186525/how-to-use-glob-to-find-files-recursively
"""


def exception_handler(func):
    def wrapper(*args, **kwargs):
        try:
            print("-" * 80)
            func(*args, **kwargs)
            print("-" * 80)
        except Exception as e:
            print(traceback.format_exc())

    return wrapper


def evaluate_folder(answer, dirpath):
    """
    Given a directory, add all file information into answer['data']
    Assume if it is under a distribution folder, to store the manifest for this data
    """
    logging.debug("Evaluating folder: %s", dirpath)

    for path in Path(dirpath).rglob("distribution/**/*"):
        logging.debug("\tEvaluating: %s" % path.name)

        if not os.path.isfile(path):
            # if path is not a file, skip to the next file to check
            continue

        parent_dir = path.parent
        to_append = {
            "name": path.name,
            # Append the raw github location, add the repository name after, and then add the path under the repository
            "path": os.path.relpath(path),
            "md5": util.get_md5(path),
            "size": os.path.getsize(path),
        }

        measure_data = None
        # Check if there is a manifest file. If so, then try to append the measure info
        if (
            path.suffix in settings.SUFFIX_TO_MEASURE
            and "measure_info.json" in os.listdir(parent_dir)
        ):
            measure_data = search_measure_info(
                path, os.path.join(parent_dir, "measure_info.json"), answer
            )
            if measure_data is not None:
                to_append["measure_info"] = measure_data
            else:
                answer["measure_not_found"].append(str(path.resolve()))
            logging.debug("-" * 80)
        # regardless of whether a measure info is found, you should still append the md5
        answer["data"].append(to_append)


@exception_handler
def search_measure_info(path, measure_info_path, answer):
    """
    Find the measure info that match the file, then append that element to the data
    """
    with open(measure_info_path, "r") as f:
        measure_info = json.load(f)

    if "_references" in measure_info:
        answer["_references"].update(measure_info["_references"])

    if len(measure_info) > 0:
        # there are two different formats of measure_info files, so look recurisvely for the measure table instead
        tables = util._finditems(measure_info, "measure_table")
        logging.info("[%s] Found tables: %s " % (len(tables), tables))
        logging.info(path.name)

        matches = [table for table in tables if path.name.split(".")[0] in table]

        logging.info("searching: %s" % path.name.split(".")[0])
        logging.info("\ttables: %s" % tables)
        logging.info("\tmatches: %s" % matches)
        logging.info("-" * 80)

        if len(matches) > 0:
            # search recursively in the same order and reconstruct the dictionaries to add
            matched_keys = []

            # a dictionary containing lists of parsed elements, assuming 1:1 between key and value
            ad = {}
            for k in settings.MEASURE_KEYS:
                ad[k] = util._finditems(measure_info, k)
                # print("%s: %s" % (k, len(ad[k])))
            # pprint(ad)
            for i in range(len(tables)):
                if (
                    not tables[i] == path.name.split(".")[0]
                ):  # if there is no table match, skip
                    logging.debug("%s == %s" % (tables[i], path.name.split(".")[0]))
                    logging.debug("Skipping")
                    continue
                d = {}
                for key in settings.MEASURE_KEYS:
                    if len(ad[key]) > i:  # because sometimes this value is empty
                        d[key] = ad[key][i]
                    else:
                        d[key] = []
                    logging.debug("[%s]: %s" % (key, ad[key]))
                matched_keys.append(d)
            logging.debug("Matched keys found: %s" % matched_keys)
            return matched_keys
        else:
            logging.debug("No matches found!")
            return


@exception_handler
def main(root, test=False):
    """
    Iterate through each file in the repository and check a hash
    """
    root = os.path.abspath(root)
    answer = {
        "name": os.path.basename(root),
        "measure_not_found": [],
        "count": 0,
        "utc_audited": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "data": [],
        "_references": {},
    }

    for file in os.listdir(root):
        logging.debug(file)
        dirpath = os.path.join(root, file)
        if os.path.isdir(dirpath):
            logging.debug("%s is a related directory" % (dirpath))
            evaluate_folder(answer, dirpath)
    answer["count"] = len(answer["data"])

    # logging.debug(answer) # too large
    logging.info("Manifest file: %s", json.dumps(answer, indent=4, sort_keys=True))
    # export the file to root
    if not test:
        export_file = os.path.join(root, "manifest.json")
        with open(export_file, "w") as f:
            json.dump(answer, f, indent=2)
        logging.info(
            "[%s] Manifest file created at: %s"
            % (os.path.isfile(export_file), export_file),
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
        main(args.input_root, args.test)
