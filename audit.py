import os
import hashlib
import argparse
import json
import logging
from pathlib import Path
from difflib import SequenceMatcher
import settings
from datetime import datetime
from string import Template
import pandas as pd
import traceback
import json

"""
Given the path to a directory, generate a manifest file
[Finding files recursively] https://stackoverflow.com/questions/2186525/how-to-use-glob-to-find-files-recursively
"""


def similar(a, b):
    # Checking for string similarity
    return SequenceMatcher(None, a, b).ratio()


def get_md5(filepath):
    return hashlib.md5(open(filepath, "rb").read()).hexdigest()


def try_create_placeholder_measure_info(path):
    '''
    Given a file and a directory with no measure infos, create a placeholder
    conditions: filename is true, and file is a csv data frame that contains the required columns
    '''
    logging.info('trying to create placeholder measure_info')
    try:
        assert os.path.isfile(str(path.resolve()))
        df = pd.read_csv(path)

        columns_required = ['measure', 'measure_type']

        # check if columns exist
        assert set(columns_required).issubset(df.columns), 'file columns %s do not contain %s' % (list(df.columns), columns_required)

        # now check if those columns only have one measure and one measure_type
        assert len(df['measure'].unique()) == 1,  "%s found more than one meausre"%df['measure'].unique() 
        assert len(df['measure_type'].unique()) == 1, "%s found more than one measure_type"%df['measure_type'].unique() 

        with open('measure_info_template.json', 'r') as f:
            s = f.read()
        t = Template(s)
        data = t.substitute(filename=path.name, measure=df['measure'].unique()[0], measure_type=df['measure_type'].unique()[0])
        logging.debug(data)
        data=json.loads(data)
        logging.debug(data)

        export_file_name = os.path.join(path.parent.resolve(), 'measure_info.json')
        logging.debug('Exporting placeholder measure_info file into: %s' % export_file_name)
        with open(export_file_name, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except:
        logging.debug(traceback.print_exc())

def evaluate_folder(answer, dirpath):
    """
    Given a directory, add all file information into answer['data']
    Assume if it is under a distribution folder, to store the manifest for this data
    """
    logging.debug("Evaluating folder: %s", dirpath)

    for path in Path(dirpath).rglob("distribution/**/*"):
        logging.debug("\tEvaluating: %s" % path.name)

        if not os.path.isfile(path):
            continue

        parent_dir = path.parent
        to_append = {
            "name": path.name,
            # Append the raw github location, add the repository name after, and then add the path under the repository
            "path": os.path.relpath(path),
            "md5": get_md5(path),
            "size": os.path.getsize(path),
        }

        measure_data = None
        # Check if there is a manifest file. If so, then try to append the measure info
        logging.debug(
            "[%s] checking %s in suffix list"
            % (path.suffix in settings.SUFFIX_TO_MEASURE, path.suffix)
        )
        if ( # if the file suffix does not needs to be measured
            not path.suffix in settings.SUFFIX_TO_MEASURE
        ):
            continue 

        if "measure_info.json" in os.listdir(parent_dir): # check to see if there is a measure_info file
            measure_data = search_measure_info(
                path, os.path.join(parent_dir, "measure_info.json"), answer
            )
            if measure_data is not None:
                to_append["measure_info"] = measure_data
                answer['measures_found'] += 1
            else:
                answer['measure_to_check'].append(str(path))
                
        else: # if there is no measure_info file, try to create one
            auto_measure = try_create_placeholder_measure_info(path)
            if auto_measure is not None:
                answer['measure_generated'].append(str(path))

        logging.debug("-" * 80)
        # regardless of whether a measure info is found, you should still append the md5
        answer["data"].append(to_append)


def search_measure_info(path, measure_info_path, answer):
    """
    Find the measure info that match the file, then append that element to the data
    """
    with open(measure_info_path, "r") as f:
        measure_info = json.load(f)

    if "_references" in measure_info:
        answer["_references"].update(measure_info["_references"])

    logging.debug(measure_info)
    if len(measure_info) > 0:
        keys = measure_info.keys()
        logging.debug(path.name)
        logging.debug(keys)
        closest_matches = [
            key for key in keys if key.split(":")[0] in path.name
        ]  # the measure is ':' delimited, and the first element

        if len(closest_matches) > 0:
            logging.debug("Closest matches: %s" % closest_matches)
            matched_keys = [measure_info[match] for match in closest_matches]
            logging.debug("Matched keys found: %s" % matched_keys)
            return matched_keys
        else:
            logging.debug("No matches found!")
            return


def main(root, test=False):
    """
    Iterate through each file in the repository and check a hash
    """
    root = os.path.abspath(root)
    answer = {
        "name": os.path.basename(root),
        "count": 0,
        "utc_audited": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "data": [],
        'measure_generated': [],
        'measure_to_check': [],
        'measures_found': 0,
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
        logging.info("[%s] Manifest file created", os.path.isfile(export_file))


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
