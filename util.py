from difflib import SequenceMatcher
import hashlib
import logging
from pathlib import Path
from string import Template
import pandas as pd
import traceback
import os
import json

# since measure_info files have two different formats, use recursion to look for measure_table is version agnostic



def _finditems(obj, key):
    if key in obj:
        return [obj[key]]
    items = []
    for k, v in sorted(obj.items()):
        if isinstance(v, dict):
            item = _finditems(v, key)
            if item is not None:
                items.extend(item)
    return items


def similar(a, b):
    # Checking for string similarity
    return SequenceMatcher(None, a, b).ratio()


def get_md5(filepath):
    return hashlib.md5(open(filepath, "rb").read()).hexdigest()


def create_placeholder_measure_info(path):
    """
    Given a file and a directory with no measure infos, create a placeholder
    conditions: filename is true, and file is a csv data frame that contains the required columns
    """
    logging.info("trying to create placeholder measure_info")
    try:
        assert os.path.isfile(str(path.resolve()))
        df = pd.read_csv(path)

        columns_required = ["measure", "measure_type"]

        # check if columns exist
        assert set(columns_required).issubset(
            df.columns
        ), "file columns %s do not contain %s" % (list(df.columns), columns_required)

        # now check if those columns only have one measure and one measure_type
        assert len(df["measure"].unique()) == 1, (
            "%s found more than one meausre" % df["measure"].unique()
        )
        assert len(df["measure_type"].unique()) == 1, (
            "%s found more than one measure_type" % df["measure_type"].unique()
        )

        with open("measure_info_template.json", "r") as f:
            s = f.read()
        t = Template(s)
        data = t.substitute(
            filename=path.name,
            measure=df["measure"].unique()[0],
            measure_type=df["measure_type"].unique()[0],
        )
        logging.debug(data)
        data = json.loads(data)
        logging.debug(data)

        export_file_name = os.path.join(path.parent.resolve(), "measure_info.json")
        logging.debug(
            "Exporting placeholder measure_info file into: %s" % export_file_name
        )
        with open(export_file_name, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except:
        logging.debug(traceback.print_exc())
