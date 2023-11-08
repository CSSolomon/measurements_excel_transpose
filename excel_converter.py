#!/usr/bin/env python3
"""@file Implements a transposition for the excel files produced by analysis machine XXX, by collecting metabolites and
their respective areas in a single sheet, and producing a second sheet with formulas based on the first one"""
import argparse
import itertools
import logging
import pathlib
import string
from pprint import pformat

import pandas as pd

# What value signifies the second part of the values, after the header
split_value = "Filename"
header_df = "header"
values_df = "values"
aggregates_key = "Aggregates"
formulas_key = "Aggregates_formulas"

templates = {
    "remote_sheet_pointer": "{sheet}!{column}{row}",
}

logging_data = {
    "format": "%(asctime)s - %(levelname)-10s - [%(filename)-18.18s | %(funcName)-18.18s | L%(lineno)04d] : %(message)s",
    "logger_name": "excel_transpose_logger",
    "cli_level": logging.INFO,
    "file_level": logging.DEBUG,
    "cli_logging": True,
    "file_logging": False,
    "filename": f"{pathlib.Path(__file__).stem}.log",
}
# The logging package internals have been stable for a while. `range(10, 51, 10)` will return the numeric values of the
# predefined levels, `getLevelName()` is a shorthand to get them in string format
loglevels_strings_and_numeric = [logging.getLevelName(x) for x in range(10, 51, 10)] + list(range(10, 51, 10))

# Get the keys for the first 728 excel columns (27 * 27 elements = 729 - 1) The removed element is the first, '', that
# is an artifact of the multiplication
excel_columns = [
    "".join(x).strip()
    for x in (itertools.product(list(" " + string.ascii_uppercase), list(" " + string.ascii_uppercase)))
][1:]


def get_logger(args: argparse.Namespace) -> logging.Logger:
    """@brief Returns a logger of the corresponding log_level
    @param[in]  args    The parsed CLI arguments, used to configure the logger object

    @return logger  The logger object
    """
    if args.log_level:
        logging_data["file_level"] = args.log_level
        logging_data["cli_level"] = args.log_level
    if not args.log_cli:
        logging_data["cli_logging"] = False
    if args.log_in_file:
        logging_data["file_logging"] = True
    if args.log_level_file:
        logging_data["file_logging"] = True
        logging_data["file_level"] = args.log_level_file
    if args.log_level_cli:
        logging_data["cli_logging"] = True
        logging_data["cli_level"] = args.log_level_cli

    formatter = logging.Formatter(logging_data["format"])
    logger = logging.getLogger(logging_data["logger_name"])
    logger.setLevel(logging.DEBUG)

    if logging_data["cli_logging"]:
        cli_handler = logging.StreamHandler()
        cli_handler.setFormatter(formatter)
        cli_handler.setLevel(logging_data["cli_level"])
        logger.addHandler(cli_handler)

    if logging_data["file_logging"]:
        file_handler = logging.FileHandler(logging_data["filename"])
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging_data["file_level"])
        logger.addHandler(file_handler)

    return logger


def existing_file(filename: str) -> pathlib.Path:
    """@brief Gets a filename and validates that it exists
    @return file    The file instance to read and process
    @raise AssertionError
    """
    f = pathlib.Path(filename).resolve()
    if f.is_file():
        return f
    raise ValueError(f"File {filename} does not exist or is not a file")


def parse_args() -> argparse.Namespace:
    """@brief parses CLI arguments
    @return args    Namespace with parsed arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--filename", required=True, type=existing_file, help="The input file to parse")
    parser.add_argument("-o", "--output", default="", help="The file to output results into")
    parser.add_argument(
        "-l",
        "--nor-leucine-key",
        default="Nor",
        help="The name of the sheet containing the Nor-Leucine data",
    )

    # Logging options
    parser.add_argument("--log-level", help="Log level to use")
    parser.add_argument(
        "--log-level-cli",
        choices=loglevels_strings_and_numeric,
        help="Log level to use for CLI. Using this force-enables CLI logging with maximum priority",
    )
    parser.add_argument(
        "--log-level-file",
        choices=loglevels_strings_and_numeric,
        help="Log level to use. Using this force-enables file logging with max priority",
    )
    parser.add_argument(
        "--log-no-cli",
        action="store_false",
        dest="log_cli",
        default=True,
        help="Skip CLI logging",
    )
    parser.add_argument(
        "--log-in-file",
        action="store_true",
        dest="log_in_file",
        default=False,
        help="Activate logging to file",
    )
    return parser.parse_args()


def cleanup_contents(excel: dict, logger: logging.Logger, ignore_index: bool = True) -> dict:
    """@brief Cleans-up the dataframes in the input dictionary, to only contain valid columns

    @param[in]  excel           The dictionary containing one dataframe per key(sheet)
    @param[in]  logger          Logger item to use
    @param[in]  ignore_index    Whether the index should be ignored

    @return clean_excel    Dictionary with the same keys as input, but cleaned-up
    """
    clean_excel = {}
    logger.info("Removing rows and columns containing only NaN or empty string values")
    for key, value in excel.items():
        logger.debug("Cleaning-up DF for sheet %s", key)
        df = value
        df = df.replace(to_replace=" ", value=float("nan"))
        df = df.dropna(axis=0, how="all", ignore_index=ignore_index).dropna(
            axis=1,
            how="all",
            ignore_index=ignore_index,
        )
        logger.debug("Excel cleanup.\nOld value: %s\nNew value: %s", value, df)
        clean_excel[key] = df
    return clean_excel


def split_excels(excel: dict, logger: logging.Logger) -> dict:
    """@brief Split single dataframes into two distinct ones, one with the headers, one with the values

    @param[in]  excel   The dictionary containing one dataframe per key(sheet)
    @param[in]  logger  Logger item to use

    @return split_excel     Dictionary with the same keys as input, each containing a dictionary with a header dataframe
                            and a values excel
    """
    logger.info("Splitting excels into header and values section.")
    split_excel = {}
    for key, value in excel.items():
        logger.debug("Splitting values of sheet %s", key)
        df = value
        split_row_index = list(df[df.columns[0]]).index(split_value)
        df_1 = df.iloc[:split_row_index]
        df_2 = df.iloc[split_row_index:].reset_index(drop=True)

        df_1.columns = df_1.iloc[0].values
        df_1 = df_1.drop(index=0)
        df_2.columns = df_2.iloc[0].values
        df_2 = df_2.drop(index=0)
        df_2 = df_2.set_index(split_value)

        split_contents = {}
        split_contents[header_df] = df_1
        split_contents[values_df] = df_2
        logger.info("Will cleanup results for key %s", key)
        split_excel[key] = cleanup_contents(split_contents, logger, ignore_index=False)
        logger.debug("Split values.\nOriginal DataFrame: %s\nSplit DataFrames: %s", value, split_contents)
    return split_excel


def transpose_split_excels(split_excel_data: dict, logger: logging.Logger) -> pd.DataFrame:
    """@brief Transpose the split excels, as per profile

    @param[in]  split_excel     Dictionary with split excels, as found in previous format
    @param[in]  logger          Logger item to use

    @return transposed_excel_shet     DataFrame with the contents of the transposed information sheet
    """
    transposed_sheet_dict = {}
    logger.info("Creating the transposed object")
    for metabolite, values in split_excel_data.items():
        logger.debug("Metabolite: %s, values: %s", metabolite, values)
        df = values[values_df]
        if not df.index.name == split_value:
            logger.debug("Skipping as this `metabolite` does not contain keyword %s", split_value)
            continue
        for injection in df.index.values:
            area = df.loc[injection]["Area"]
            rt = df.loc[injection]["RT"]
            logger.debug("Injection: %s, area: %s, rt: %s", injection, area, rt)

            rts_dict = transposed_sheet_dict.setdefault("RT", {})
            areas_dict = transposed_sheet_dict.setdefault(f"{injection}_Area", {})
            rts_dict[metabolite] = rt
            areas_dict[metabolite] = area

    return pd.DataFrame(transposed_sheet_dict)


def get_formulas_sheet(
    transposed_sheet: pd.DataFrame,
    args: argparse.Namespace,
    logger: logging.Logger,
    sheet_name: str = aggregates_key,
) -> pd.DataFrame:
    """@brief Inserts the formula columns in the sheet

    @param[in]  transposed_sheet    The sheet with the transposed data
    @param[in]  args                argparse.Namespace with parsed arguments result
    @param[in]  logger          Logger item to use
    @param[in]  sheet_name          The name the sheet will have in the excel

    @return sheet_with_formulas A datasheet of formulas
    """
    formulas_sheet = {}
    df = transposed_sheet
    logger.info("Generating formulas sheet")
    logger.debug("Transposed sheet passed as argument: %s", transposed_sheet)
    # Add 1 because numbering starts from 1 for excel, and another 1 because the first row will be taken by the column
    # names
    nor_row = df.index.get_loc(args.nor_leucine_key) + 1 + 1

    for injection in df:
        injection_dict = formulas_sheet.setdefault(injection, {})
        # Add 1 because the first column is taken by the metabolite names
        injection_column = excel_columns[df.columns.get_loc(injection) + 1]
        logger.debug("Injection: %s, injection_column: %s", injection, injection_column)
        for metabolite in df[injection].index:
            # As above re "+ 1 + 1"
            metabolite_row = df[injection].index.get_loc(metabolite) + 1 + 1
            metabolite_coordinates = templates["remote_sheet_pointer"].format(
                sheet=sheet_name,
                column=injection_column,
                row=metabolite_row,
            )
            nor_coordinates = templates["remote_sheet_pointer"].format(
                sheet=sheet_name,
                column=injection_column,
                row=nor_row,
            )

            formula = f"={metabolite_coordinates} / {nor_coordinates}"
            logger.debug(
                "Metabolite: %s, metabolite_coordinates: %s, nor_coordinates: %s, formula: %s",
                metabolite,
                metabolite_coordinates,
                nor_coordinates,
                formula,
            )
            injection_dict[metabolite] = formula

    return pd.DataFrame(formulas_sheet)


def save_excel(excel: dict, filename: pathlib.Path) -> None:
    """@brief Saves in excel containing multiple sheets
    @param[in] excel Dictionary with dataframes as values
    @return None
    """
    with pd.ExcelWriter(filename) as writer:
        for sheet_name, df in excel.items():
            df.to_excel(writer, sheet_name=sheet_name, float_format="%f")


def main():
    """@brief parses CLI arguments
    @return args    Namespace with parsed arguments
    """
    args = parse_args()
    logger = get_logger(args)
    logger.debug("Args: %s", args)

    excel = pd.read_excel(args.filename, sheet_name=None)
    logger.debug("Got excel data %s", pformat(excel))

    # Since dict now behaves like OrderedDict, use placeholders
    new_excel = {aggregates_key: None, formulas_key: None}
    new_excel.update(excel)

    clean_excel = cleanup_contents(excel, logger)
    split_excel = split_excels(clean_excel, logger)
    transposed_sheet = transpose_split_excels(split_excel, logger)
    new_excel[aggregates_key] = transposed_sheet

    formulas_sheet = get_formulas_sheet(transposed_sheet, args, logger)

    new_excel[formulas_key] = formulas_sheet
    new_excel.update(excel)
    if args.output:
        logger.info("Saving new excel to file %s", args.output)
        logger.debug("Data to save: %s", new_excel)
        save_excel(new_excel, args.output)
    else:
        logger.info(new_excel[aggregates_key])
        logger.info(new_excel[formulas_key])


if __name__ == "__main__":
    main()
