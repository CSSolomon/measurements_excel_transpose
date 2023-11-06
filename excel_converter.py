#!/usr/bin/env python3
import argparse
import pathlib

from pprint import pprint
import pandas as pd

# What value signifies the second part of the values, after the header
split_value = "Filename"
header_df = "header"
values_df = "values"
aggregates_key = "Aggregates"


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
    parser.add_argument("-o", "--output", required=True, help="The file to output results into")
    return parser.parse_args()


def cleanup_contents(excel: dict, ignore_index: bool = True) -> dict:
    """@brief Cleans-up the dataframes in the input dictionary, to only contain valid columns

    @param[in]  excel           The dictionary containing one dataframe per key(sheet)
    @param[in]  ignore_index    Whether the index should be ignored

    @return clean_excel    Dictionary with the same keys as input, but cleaned-up
    """
    clean_excel = {}
    for key, value in excel.items():
        df = value
        df = df.replace(to_replace=" ", value=float("nan"))
        df = df.dropna(axis=0, how="all", ignore_index=ignore_index).dropna(
            axis=1, how="all", ignore_index=ignore_index
        )
        clean_excel[key] = df
    return clean_excel


def split_excels(excel: dict) -> dict:
    """@brief Split single dataframes into two distinct ones, one with the headers, one with the values

    @param[in]  excel   The dictionary containing one dataframe per key(sheet)

    @return split_excel     Dictionary with the same keys as input, each containing a dictionary with a header dataframe
                            and a values excel
    """
    split_excel = {}
    for key, value in excel.items():
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

        split_excel[key] = cleanup_contents(split_contents, ignore_index=False)
        # split_excel[key] = split_contents
    return split_excel


def transpose_split_excels(split_excels: dict) -> pd.DataFrame:
    """@brief Transpose the split excels, as per profile

    @param[in]  split_excel   Dictionary with split excels, as found in previous format

    @return transposed_excel_shet     DataFrame with the contents of the transposed information sheet
    """
    transposed_sheet_dict = {}
    for metabolite, values in split_excels.items():
        df = values[values_df]
        if not df.index.name == split_value:
            continue
        for injection in df.index.values:
            area = df.loc[injection]["Area"]
            rt = df.loc[injection]["RT"]

            areas_dict = transposed_sheet_dict.setdefault(f"{injection}_Area", {})
            rts_dict = transposed_sheet_dict.setdefault(f"{injection}_RT", {})
            rts_dict[metabolite] = rt
            areas_dict[metabolite] = area

    # pprint(transposed_sheet_dict)
    return pd.DataFrame(transposed_sheet_dict)


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
    excel = pd.read_excel(args.filename, sheet_name=None)
    clean_excel = cleanup_contents(excel)
    split_excel = split_excels(clean_excel)
    transposed_excel = transpose_split_excels(split_excel)
    excel[aggregates_key] = transposed_excel
    save_excel(excel, args.output)


if __name__ == "__main__":
    main()
