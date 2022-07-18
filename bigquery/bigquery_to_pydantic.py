import json
import getopt
import sys

# this list is by no means complete, at this stage we only
# use these.
bq_type_to_pydantic_type = {
    "STRING": "str",
    "BOOLEAN": "bool",
    "TIMESTAMP": "datetime",
    "INTEGER": "int",
    "FLOAT": "float"
}


def get_pydantic_type(bq_type, bq_mode):
    ret = bq_type_to_pydantic_type[bq_type]
    if bq_mode == "REQUIRED":
        return ret
    elif bq_mode == "REPEATED":
        return f"List[{ret}]"
    else:
        return f"Optional[{ret}]"


def pydantic_model_from_bq_schema(bq_schema_filename, output_filename, model_name):
    with open(bq_schema_filename, 'r') as json_file:
        data = json.load(json_file)

        with open(output_filename, 'w') as model_file:
            model_file.write("from datetime import datetime\n")
            model_file.write("from pydantic import BaseModel\n")
            model_file.write("from typing import Optional, List\n")
            model_file.write("\n\n")
            model_file.write(f"class {model_name}(BaseModel):\n")

            for field in data:
                model_file.write("    " + field['name']
                                 + ": " + get_pydantic_type(field['type'],
                                                            field['mode'])
                                 + "\n")


if __name__ == "__main__":
    # Options
    options = "hmo:"

    # Long options
    long_options = ["help", "input=", "output="]
    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:o:m", ["input=", "output=", "model="])
    except getopt.GetoptError:
        print("Usage: bq_to_pydantic.py -i <bq_schema_filename> -o <output_filename>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-i", "--input"):
            bq_schema_filename = arg
        elif opt in ("-o", "--output"):
            output_filename = arg
        elif opt in ("-m", "--model"):
            model_name = arg
    pydantic_model_from_bq_schema(bq_schema_filename, output_filename, model_name)
