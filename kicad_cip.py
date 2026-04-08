# Kicad CIP command line tool
# Usage:
# kicad_cip --keywords/-k part_number [--output/-o db_name], adding a single part to sqlite.db
# kicad_cip --input/-i parts.csv [--output/-o db_name], adding parts listed in parts.csv
# workflow:
#   show list of parts (show if part is new or exist and tbl_name)->
#   select one part ->
#   show list of properties ->
#   [select one property to edit] -> repeat
#   save to database or quit

# sqlite database schema
#   tbl_name -> part category name
#   key -> ManufacturerProductNumber
#
# CREATE TABLE IF NOT EXISTS "components" (
# 	"Categories"	TEXT NOT NULL,
# 	"Description"	TEXT NOT NULL,
# 	"Keywords"	TEXT NOT NULL,
# 	"Value"	TEXT NOT NULL,
# 	"Manufacturer"	TEXT NOT NULL,
# 	"ManufacturerProductNumber"	TEXT NOT NULL UNIQUE,
# 	"Package"	TEXT NOT NULL,
# 	"KicadSymbolLibrary"	TEXT,
# 	"KicadFootprintLibrary"	TEXT,
# 	"PartStatus"	TEXT NOT NULL,
# 	"Distributor"	TEXT,
# 	"DistributorProductNumber"	TEXT,
# 	"UnitPrice"	TEXT,
# 	"ProductUrl"	TEXT,
# 	"DatasheetUrl"	TEXT,
# 	"ParameterName_01"	TEXT,
# 	"ParameterValue_01"	TEXT,
# 	"ParameterName_02"	TEXT,
# 	"ParameterValue_02"	TEXT,
# 	"ParameterName_03"	TEXT,
# 	"ParameterValue_03"	TEXT,
# 	"ParameterName_04"	TEXT,
# 	"ParameterValue_04"	TEXT,
# 	"ParameterName_05"	TEXT,
# 	"ParameterValue_05"	TEXT,
# 	"ParameterName_06"	TEXT,
# 	"ParameterValue_06"	TEXT,
# 	"ParameterName_07"	TEXT,
# 	"ParameterValue_07"	TEXT,
# 	"ParameterName_08"	TEXT,
# 	"ParameterValue_08"	TEXT,
# 	"ParameterName_09"	TEXT,
# 	"ParameterValue_09"	TEXT,
# 	"ParameterName_10"	TEXT,
# 	"ParameterValue_10"	TEXT,
# 	"ParameterName_11"	TEXT,
# 	"ParameterValue_11"	TEXT,
# 	"ParameterName_12"	TEXT,
# 	"ParameterValue_12"	TEXT,
# 	"ParameterName_13"	TEXT,
# 	"ParameterValue_13"	TEXT,
# 	"ParameterName_14"	TEXT,
# 	"ParameterValue_14"	TEXT,
# 	"ParameterName_15"	TEXT,
# 	"ParameterValue_15"	TEXT,
# 	"ParameterName_16"	TEXT,
# 	"ParameterValue_16"	TEXT,
# 	PRIMARY KEY("ManufacturerProductNumber")
# )

import sqlite3
import argparse
import csv
import logging
import sys
import os
from datetime import datetime
from digikey_search import digikey_search
import re
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import ANSI
from dataclasses import dataclass, astuple, field

import colors


@dataclass
# notes:
# use main_category as tbl_name
# id = sub_categories + manufacturer_product_number
class ProductInfoBase:
    main_category: str = ""
    id: str = ""
    description: str = ""
    keywords: str = ""
    value: str = ""
    manufacturer: str = ""
    manufacturer_product_number: str = ""
    package: str = ""
    kicad_symbol_library: str = ""
    kicad_footprint_library: str = ""
    part_status: str = ""
    qty_available: str = ""
    distributor: str = ""
    distributor_product_number: str = ""
    unit_price: str = ""
    product_url: str = ""
    datasheet_url: str = ""


@dataclass
class ProductInfo:
    base: ProductInfoBase = field(default_factory=ProductInfoBase)
    # params: list[dict[str, str]] = field(default_factory=list)
    params: list[dict[str, str]] = field(
        default_factory=lambda: [{"param": "-", "value": "-"}] * 32
    )


class ProductDb:
    def __init__(self, db_name: str = "components.db"):
        self.con = sqlite3.connect(db_name)
        self.cur = self.con.cursor()
        self.cur.execute(f""" SELECT type, tbl_name FROM sqlite_master 
                         WHERE type="table" AND tbl_name="components"
                         """)
        if self.cur.fetchone() is None:
            self.create_tbl("components")

    def create_tbl(self, tbl_name: str):
        self.cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {tbl_name} (
            "ID"	TEXT NOT NULL,
        	"Description"	TEXT NOT NULL,
        	"Keywords"	TEXT NOT NULL,
        	"Value"	TEXT NOT NULL,
        	"Manufacturer"	TEXT NOT NULL,
        	"ManufacturerProductNumber"	TEXT NOT NULL,
        	"Package"	TEXT NOT NULL,
        	"KicadSymbolLibrary"	TEXT NOT NULL,
        	"KicadFootprintLibrary"	TEXT NOT NULL,
        	"PartStatus"	TEXT NOT NULL,
            "QtyAvailable"  TEXT,
        	"Distributor"	TEXT,
        	"DistributorProductNumber"	TEXT,
        	"UnitPrice"	TEXT,
        	"ProductUrl"	TEXT,
        	"DatasheetUrl"	TEXT,
        	"Param01"	TEXT,
        	"Value01"	TEXT,
        	"Param02"	TEXT,
        	"Value02"	TEXT,
        	"Param03"	TEXT,
        	"Value03"	TEXT,
        	"Param04"	TEXT,
        	"Value04"	TEXT,
        	"Param05"	TEXT,
        	"Value05"	TEXT,
        	"Param06"	TEXT,
        	"Value06"	TEXT,
        	"Param07"	TEXT,
        	"Value07"	TEXT,
        	"Param08"	TEXT,
        	"Value08"	TEXT,
        	"Param09"	TEXT,
        	"Value09"	TEXT,
        	"Param10"	TEXT,
        	"Value10"	TEXT,
        	"Param11"	TEXT,
        	"Value11"	TEXT,
        	"Param12"	TEXT,
        	"Value12"	TEXT,
        	"Param13"	TEXT,
        	"Value13"	TEXT,
        	"Param14"	TEXT,
        	"Value14"	TEXT,
        	"Param15"	TEXT,
        	"Value15"	TEXT,
        	"Param16"	TEXT,
        	"Value16"	TEXT,
        	"Param17"	TEXT,
        	"Value17"	TEXT,
        	"Param18"	TEXT,
        	"Value18"	TEXT,
        	"Param19"	TEXT,
        	"Value19"	TEXT,
        	"Param20"	TEXT,
        	"Value20"	TEXT,
        	"Param21"	TEXT,
        	"Value21"	TEXT,
        	"Param22"	TEXT,
        	"Value22"	TEXT,
        	"Param23"	TEXT,
        	"Value23"	TEXT,
        	"Param24"	TEXT,
        	"Value24"	TEXT,
        	"Param25"	TEXT,
        	"Value25"	TEXT,
        	"Param26"	TEXT,
        	"Value26"	TEXT,
        	"Param27"	TEXT,
        	"Value27"	TEXT,
        	"Param28"	TEXT,
        	"Value28"	TEXT,
        	"Param29"	TEXT,
        	"Value29"	TEXT,
        	"Param30"	TEXT,
        	"Value30"	TEXT,
        	"Param31"	TEXT,
        	"Value31"	TEXT,
        	"Param32"	TEXT,
        	"Value32"	TEXT
        	)
            """)

    # insert data into table, replace old data if it exist
    def insert_record(self, tbl_name: str, product: ProductInfo):
        # prepare data
        product_base_info = astuple(product.base)
        product_params_dict = product.params
        product_params_list = []
        for param in product_params_dict:
            product_params_list += [param["param"], param["value"]]

        product_info = product_base_info[1:] + tuple(product_params_list)

        # insert data into table
        self.cur.execute(f"""
            INSERT OR REPLACE INTO {tbl_name} VALUES {product_info}
                         """)
        self.con.commit()
        return product_info

    def query_record(self, product: ProductInfo) -> None | tuple[str]:
        self.cur.execute(f'''
                            SELECT ManufacturerProductNumber
                            FROM components
                            WHERE ManufacturerProductNumber="{product.base.manufacturer_product_number}"
                        ''')
        res = self.cur.fetchone()
        return res

    def edit_record(self, product: ProductInfo):
        return

    def delete_record(self, product: ProductInfo):
        print("coming soon...")
        return

    # return a list of symbol names in current database for auto-completion
    def query_symbols(self) -> None | list[tuple[int, str]]:
        self.cur.execute(f"""
                            SELECT MAX(_ROWID_) As LastID, KicadSymbolLibrary
                            FROM components
                            GROUP BY KicadSymbolLibrary
                            ORDER BY LastID DESC
                         """)
        res = self.cur.fetchall()
        return res

    # return a list of footprint names in current database for auto-completion
    def query_footprints(self) -> None | list[tuple[int, str]]:
        self.cur.execute(f"""
                            SELECT MAX(_ROWID_) As LastID, KicadFootprintLibrary
                            FROM components
                            GROUP BY KicadFootprintLibrary
                            ORDER BY LastID DESC
                         """)
        res = self.cur.fetchall()
        return res

    def close(self):
        self.con.close()


def parse_digikey_response(response: any) -> ProductInfo:
    product = ProductInfo()

    # populate product variation and pricing info into list
    distro_product_number = []
    distro_price = []
    for variation in response["ProductVariations"]:
        distro_product_number.append(
            {"digikey_product_number": variation["DigiKeyProductNumber"]}
        )
        if len(variation["StandardPricing"]) != 0:
            distro_price.append(
                {
                    "break_qty": variation["StandardPricing"][0]["BreakQuantity"],
                    "standard_pricing": variation["StandardPricing"][0]["UnitPrice"],
                }
            )
        else:
            distro_price.append({"break_qty": "-", "standard_pricing": "-"})

    # populate parameters
    product.base.value = response["ManufacturerProductNumber"]
    params = (
        response["Parameters"]
        if len(response["Parameters"]) < 33
        else response["Parameters"][:32]
    )
    for index, param in enumerate(params):
        # remove blank char
        value = param["ValueText"]
        if param["ParameterType"] != "String":
            value = re.sub(r"\s", "", value)
        # populate params list
        product.params[index] = {"param": param["ParameterText"], "value": value}
        # populate package if provided
        if param["ParameterText"] == "Package / Case":
            product.base.package = value

        # replace resistor/capacitor/inductor product.base number with values
        if (
            param["ParameterId"] == 2085
            or param["ParameterId"] == 1
            or param["ParameterId"] == 2087
            or param["ParameterId"] == 2049
        ):
            if value.find("Ohms") != -1:
                product.base.value = value.removesuffix("Ohms").upper()
            else:
                product.base.value = value

    # populate categories
    product.base.main_category = response["Category"]["Name"]
    product.base.id = (
        product.base.main_category
        + "/".join(parse_categories([""], response["Category"]["ChildCategories"]))
        + "/"
        + response["ManufacturerProductNumber"]
    )
    product.base.description = response["Description"]["ProductDescription"]
    product.base.keywords = response["Description"]["DetailedDescription"]
    product.base.manufacturer = response["Manufacturer"]["Name"]
    product.base.manufacturer_product_number = response["ManufacturerProductNumber"]
    product.base.kicad_symbol_library = ""
    product.base.kicad_footprint_library = ""
    product.base.part_status = response["ProductStatus"]["Status"]
    product.base.qty_available = str(response["QuantityAvailable"])
    product.base.distributor = "Digikey"
    product.base.distributor_product_number = "/".join(
        [item["digikey_product_number"] for item in distro_product_number]
    )
    product.base.unit_price = "/".join(
        [
            str(item["standard_pricing"]) + "@" + str(item["break_qty"])
            for item in distro_price
        ]
    )
    if response["ProductUrl"] is not None:
        product.base.product_url = response["ProductUrl"]
    if response["DatasheetUrl"] is not None:
        product.base.datasheet_url = (
            response["DatasheetUrl"]
            if response["DatasheetUrl"][:4] == "http"
            else "https:" + response["DatasheetUrl"]
        )
    return product


def parse_categories(
    flattened_categories: list[str], nested_categories: list[any]
) -> list[str]:
    # no more nested list, return flattened list
    if len(nested_categories) == 0:
        return flattened_categories
    else:
        # append top nested list to flattened list and pass next nested list to recursive call
        flattened_categories.append(nested_categories[0]["Name"])
        return parse_categories(
            flattened_categories, nested_categories[0]["ChildCategories"]
        )


def select_product_prompt(products: list[ProductInfo]) -> ProductInfo:
    """
    Select one product from list of products
    Args:
        products (list[ProductInfo]): list of ProductInfo
    Returns:
        ProductInfo: selected product or an empty ProductInfo instance
    """
    colors.print_info(f"Total {len(products)} products found:")

    # if found nothing, return a empty product record
    if len(products) == 0:
        return ProductInfo()
    else:
        for index, product in enumerate(products):
            print(colors.print_product_item(
                index + 1,
                product.base.manufacturer_product_number,
                product.base.manufacturer,
                product.base.description,
                product.base.qty_available,
                product.base.part_status
            ))
        while True:
            try:
                product_index = int(prompt(ANSI(colors.question("Choose one product, 0 to exit: ")), default="1"))
                if product_index == 0:
                    sys.exit()
                if product_index < 1 or product_index > len(products):
                    colors.print_error("Invalid selection, please retry...")
                    continue
                product = products[product_index - 1]
                break
            except (ValueError, IndexError):
                colors.print_error("Invalid selection, please retry...")
        print(colors.print_selected(
            product.base.manufacturer_product_number,
            product.base.manufacturer,
            product.base.description
        ))
        return product


def input_product_info_prompt(
    product: ProductInfo,
    symbol_completer: None | WordCompleter,
    footprint_completer: None | WordCompleter,
) -> ProductInfo:
    """
    Input product info, can use ? as a placeholder for manufacturer_product_number.
    It will be replaced later with real product number later

    Args:
        product (ProductInfo): ProductInfo dataclass, can be an instance with empty info

    Returns:
        ProductInfo: return can be an empty instance when choosing not to enter info manually
    """

    # empty instance = not found from Digikey, allow manual input
    try:
        if product.base.manufacturer_product_number == "":
            colors.print_warning("No product found in Digikey")
            if prompt(
                ANSI(colors.question("Enter manually? [y|n]: ")), default="n"
            ) in ["y", "Y"]:
                product.base.id = prompt(ANSI(colors.question("Enter Product ID: ")))
                product.base.description = prompt(ANSI(colors.question("Enter Product Description: ")))
                product.base.keywords = prompt(ANSI(colors.question("Enter Product keywords: ")))
                product.base.manufacturer = prompt(ANSI(colors.question("Enter Product Manufacturer: ")))
                product.base.manufacturer_product_number = prompt(
                    ANSI(colors.question("Enter Product Manufacturer Product Number: "))
                )
                product.base.value = product.base.manufacturer_product_number
            else:
                return product

        # enter kicad symbol and footprint library
        prompt_input = prompt(
            ANSI(colors.question("Enter Kicad symbol library name: ")),
            default=product.base.kicad_symbol_library,
            completer=symbol_completer,
            complete_while_typing=True,
        )
        # allow using ? as placeholder for manufacturer product number
        product.base.kicad_symbol_library = re.sub(
            r"\?", f"{product.base.manufacturer_product_number}", prompt_input
        )
        prompt_input = prompt(
            ANSI(colors.question("Enter Kicad footprint library name: ")),
            default=product.base.kicad_footprint_library,
            completer=footprint_completer,
            complete_while_typing=True,
        )
        product.base.kicad_footprint_library = re.sub(
            r"\?", f"{product.base.manufacturer_product_number}", prompt_input
        )
        return product
    except KeyboardInterrupt:
        colors.print_error("Keyboard interrupt, exit")
        sys.exit()


def write_batch_log(log_entries: list[dict], input_filename: str):
    """
    Write batch mode log file with format:
    <manufacturer_product_number>: <database record> ==> <status>
    """
    timestamp = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    log_filename = f"{base_name}-{timestamp}.log"

    with open(log_filename, "w") as log_file:
        for entry in log_entries:
            mpn = entry["mpn"]
            record = entry["record"]
            status = entry["status"]
            log_file.write(f"{mpn}: {record} ==> {status}\n")

    return log_filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # input args, either part number or csv file 
    input_group = parser.add_argument_group("Inputs")
    input_mutex = input_group.add_mutually_exclusive_group(required=True)
    input_mutex.add_argument(
        "--keywords",
        "-k",
        type=str,
        help="product keywords, normally input the product number",
    )
    input_mutex.add_argument(
        "--batch",
        "-b",
        type=str,
        help="file contains part number, each product per line.",
    )
    # output args
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="components.db",
        help="Output database file. By default components.db",
    )

    args = parser.parse_args()

    # Display header
    colors.print_header("═" * 60)
    colors.print_header(" KiCad Component Information Provider (CIP)")
    colors.print_header("═" * 60)
    print()

    # open sqlite db
    db = ProductDb(db_name=args.output)
    colors.print_info(f"Using database: {colors.highlight(args.output)}")
    print()

    # Initialize batch log if in batch mode
    batch_log: list[dict] = []
    is_batch_mode = args.batch is not None

    # get input keywords from either cmd or csv file
    # csv fields are keywords, symbol_name, footprint_name
    keywords_list: list[dict[str, str, str]] = []
    if args.keywords is not None:
        keywords_list.append({"product": args.keywords, "symbol": "", "footprint": ""})
    else:
        with open(args.batch, "r") as file:
            rows = csv.reader(file)
            rows_list = list(rows)

            if len(rows_list) < 2:
                colors.print_error(
                    "CSV file must contain a header line and at least one data row"
                )
                sys.exit(1)

            # Validate header has exactly 3 fields
            header = rows_list[0]
            if len(header) != 3:
                colors.print_error(
                    "CSV file should contain a header line and 3 fields <product_number>, <symbol_library>, <footprint_library>"
                )
                sys.exit(1)

            # Process data rows (skip header)
            for row in rows_list[1:]:
                if len(row) != 3:
                    colors.print_error(
                        "CSV file should contain a header line and 3 fields <product_number>, <symbol_library>, <footprint_library>"
                    )
                    sys.exit(1)
                keywords_list.append(
                    {"product": row[0], "symbol": row[1], "footprint": row[2]}
                )

    # search and add parts
    colors.print_subheader("Processing parts...")
    print()
    for keyword in keywords_list:
        mpn = keyword["product"]
        log_entry = {"mpn": mpn, "record": "", "status": ""}

        # Show progress indicator
        if not is_batch_mode:
            print()
            colors.print_info(f"Searching for: {colors.highlight(mpn)}")

        try:
            logging.info(f"Searching keyword: {mpn}")
            results = digikey_search(mpn)
            products: list[ProductInfo] = []
            if len(results["Products"]) > 0:
                for result in results["Products"]:
                    products.append(parse_digikey_response(result))

            # Determine if batch mode (symbol and footprint provided in CSV)
            batch_mode = bool(keyword["symbol"] and keyword["footprint"])

            # Batch mode validation - auto-skip on errors
            if batch_mode:
                if len(products) == 0:
                    log_entry["status"] = "skipped-no-result"
                    batch_log.append(log_entry)
                    colors.print_warning(
                        f"Searching '{colors.highlight(mpn)}' returned no results. Skipping."
                    )
                    continue
                elif len(products) > 1:
                    log_entry["status"] = "skipped-multi-results"
                    batch_log.append(log_entry)
                    colors.print_warning(
                        f"Searching '{colors.highlight(mpn)}' returned {len(products)} results. Skipping."
                    )
                    continue
                else:
                    product = products[0]  # Auto-select the single result
            else:
                product = select_product_prompt(products)

            insert_op = True
            if db.query_record(product) is not None:
                if batch_mode:
                    # Auto-skip duplicates in batch mode
                    log_entry["status"] = "skipped-duplicate"
                    batch_log.append(log_entry)
                    colors.print_warning(
                        f"'{colors.highlight(mpn)}' already exists in database. Skipping."
                    )
                    continue
                else:
                    if prompt(ANSI(colors.question("Product exist, overwrite? [y|n]: ")), default="n") in ["n", "N"]:
                        insert_op = False

            if insert_op:
                if batch_mode:
                    # Batch mode: directly set symbol and footprint from CSV, skip user prompts
                    product.base.kicad_symbol_library = keyword["symbol"]
                    product.base.kicad_footprint_library = keyword["footprint"]
                else:
                    # Interactive mode: build completers and prompt user
                    symbol_list = db.query_symbols()
                    footprint_list = db.query_footprints()
                    if symbol_list is not None:
                        symbols = ["Standard:"]
                        for item in symbol_list:
                            symbols.append(item[1])
                        symbol_completer = WordCompleter(symbols, ignore_case=True)
                    else:
                        symbol_completer = None

                    if footprint_list is not None:
                        footprints = ["Standard:", "Footprint:?"]
                        for item in footprint_list:
                            footprints.append(item[1])
                        footprint_completer = WordCompleter(
                            footprints, ignore_case=True
                        )
                    else:
                        footprint_completer = None

                    product.base.kicad_symbol_library = keyword["symbol"]
                    product.base.kicad_footprint_library = keyword["footprint"]

                    product = input_product_info_prompt(
                        product,
                        symbol_completer=symbol_completer,
                        footprint_completer=footprint_completer,
                    )

                if product.base.manufacturer_product_number != "":
                    product_info = db.insert_record("components", product)
                    logging.info(
                        f"inserted one record: {product.base.manufacturer_product_number}"
                    )
                    colors.print_success(
                        f"Inserted '{colors.highlight(product.base.manufacturer_product_number)}' into database."
                    )

                    # Log successful insertion in batch mode
                    if batch_mode:
                        # Convert product_info tuple to string representation
                        record_str = str(product_info)
                        log_entry["record"] = record_str
                        log_entry["status"] = "inserted"
                        batch_log.append(log_entry)

        except Exception as e:
            logging.error(f"Search keywords Failed: {str(e)}")
            raise

    # Write batch log file if in batch mode
    if is_batch_mode and batch_log:
        log_file_path = write_batch_log(batch_log, args.batch)
        colors.print_success(f"Batch log written to: {colors.highlight(log_file_path)}")

        # Print batch summary
        print()
        colors.print_header("─" * 40)
        colors.print_subheader("Batch Processing Summary")
        colors.print_header("─" * 40)

        inserted = len([e for e in batch_log if e["status"] == "inserted"])
        no_result = len([e for e in batch_log if e["status"] == "skipped-no-result"])
        multi_results = len([e for e in batch_log if e["status"] == "skipped-multi-results"])
        duplicates = len([e for e in batch_log if e["status"] == "skipped-duplicate"])

        print(f"  {colors.Colors.GREEN}●{colors.Colors.RESET} Successfully inserted:    {inserted}")
        print(f"  {colors.Colors.YELLOW}●{colors.Colors.RESET} Skipped (no results):    {no_result}")
        print(f"  {colors.Colors.YELLOW}●{colors.Colors.RESET} Skipped (multi results): {multi_results}")
        print(f"  {colors.Colors.YELLOW}●{colors.Colors.RESET} Skipped (duplicates):    {duplicates}")
        print(f"  {colors.Colors.DIM}─{colors.Colors.RESET} {'─' * 25}")
        print(f"  {colors.Colors.BOLD}●{colors.Colors.RESET} Total processed:         {len(batch_log)}")

    print()
    colors.print_success("Done!")
    db.close()
