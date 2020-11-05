import os
import glob
import re

import pandas as pd

try:
    from isotope_correction import calc_isotopologue_correction
except ImportError:
    from isotope_correction.src.isotope_correction import calc_isotopologue_correction


na_values = ["NF", "nf"]  # additional str to be parsed as NA


def excel2csv(infile, isotopologue_correction=False, verbose=False):
    """Converts excel to csv file

    Converts excel file to csv, each sheet seperately
    Output is saved in same folder
    :param infile: str
        path to excel file
    :param isotopologue_correction: False, "single", "summary" or "all"
        "single": Do isotopologue_correction for individual sheets
        "summary": Generate iso corrected csv of all sheets
        "all": Individual and summary output files
    :param verbose: int (default: False)
        False for no output
        1 for some output
        2 for more information
    :return: None
    """
    out_folder = os.path.splitext(infile)[0]
    out_file_extension = ".csv"
    out_file_iso_ext = "_iso_corr.csv"
    os.makedirs(out_folder, exist_ok=True)
    if verbose > 0:
        print(out_folder)
        verbose = verbose - 1

    df = pd.read_excel(
        infile, sheet_name=None, skiprows=3, index_col=0, na_values=na_values
    )
    for i in df:
        file_name = i.replace(" ", "_")
        out_file_base = os.path.join(out_folder, file_name)
        out_file_original = out_file_base + out_file_extension
        df[i].to_csv(out_file_original)
        if isotopologue_correction in ["single", "all"]:
            out_file_single = out_file_base + out_file_iso_ext
            df_iso_corr = analyse_rawfiles(
                out_file_original,
                isotopologue_correction=True,
                show_intermediates=True,
                verbose=verbose,
            )
            df_iso_corr.to_csv(out_file_single)
        if isotopologue_correction in ["summary", "all"]:
            df[i]["Experiment"] = os.path.basename(out_file_base)
    if isotopologue_correction in ["summary", "all"]:
        out_basename = os.path.basename(out_folder)
        out_file_summ = os.path.join(
            out_folder, out_basename + "_summary" + out_file_iso_ext
        )
        dfs = [sheet for sheet in df.values()]
        df_summary = pd.concat(dfs, sort=False)
        df_sum_iso = analyse_rawfiles(
            input_data=(out_basename, df_summary),
            isotopologue_correction=True,
            show_intermediates=True,
            verbose=verbose,
        )
        df_sum_iso.to_csv(out_file_summ)


def analyse_rawfiles(
    input_data,
    nad_conc=None,
    nad_amount=None,
    nad_protein=None,
    isotopologue_correction=True,
    show_intermediates=False,
    verbose=False,
):
    """Read and analyze LC-MS experiment csv files.

    Read and analyze LC-MS experiment csv files.
    :param input_data: str or tuple of str and pandas DataFrame
        Either glob of files, direct path to csv files
        or tuple of experiment name and DataFrame with preloaded data
    :param nad_conc: float, int
        Intracellular NAD concentration of analysed cells
    :param nad_amount: float, int
        Total NAD amount in analysed cells
    :param nad_protein: float, int
        Total NAD amount per dry weight protein in analysed cells
        Used for normalisation
    :param isotopologue_correction: bool (default: True)
        Correct for natural isotopologues
    :param show_intermediates: bool (default: False)
        Show abs and percental values of isotop intermediates
    :param isotopes_file: Path to isotope file
        default location: ~/isocordb/Isotopes.dat
    :param metabolites_file: Path to metabolites file
        default location: ~/isocordb/Metabolites.dat
    :param verbose: int (default: False)
        More verbose output like correction factor values
    :return : Pandas DataFrame
    """
    if isinstance(input_data[1], str):
        file_glob = input_data
        files = glob.glob(file_glob)
        data = []
        for f in files:
            df_read = pd.read_csv(f, index_col=0, na_values=na_values)
            df_read["Experiment"] = os.path.splitext(os.path.basename(f))[0]
            data.append(df_read)

        df = pd.concat(data, sort=False)
        exp_name = os.path.splitext(os.path.basename(file_glob))[0]
    elif isinstance(input_data[1], pd.DataFrame):
        df = input_data[1]
        exp_name = input_data[0]
    else:
        raise ValueError("input_data has to be str or tuple of str and DataFrame")

    subset = ["No label", "N15", "5C13", "5C13N15", "10C13", "10C13N15"]
    # Removes lines with only 0 in data columns
    df = df.loc[(df[subset] != 0).any(axis=1)]
    df = df.dropna(axis=0, how="all", subset=subset)
    df = df.fillna(0)
    df["Time in hours"] = df["Time in minutes"] / 60
    # df = df.drop(['Date','Passage','Cell line','Time in minutes'], axis=1)
    df = df.sort_index()
    df = df.set_index(["Time in hours"])

    # Isotope correction for each column
    if isotopologue_correction:
        df = calc_isotopologue_correction(df, "NAD", subset, verbose=verbose)

    df["sum_labelled"] = (
        df["N15"] + df["5C13"] + df["5C13N15"] + df["10C13"] + df["10C13N15"]
    )
    df["no_label_percent"] = (
        df["No label"] / (df["No label"] + df["sum_labelled"]) * 100
    )
    df["sum_labelled_percent"] = (
        df["sum_labelled"] / (df["No label"] + df["sum_labelled"]) * 100
    )
    if show_intermediates:
        for col in ["N15", "5C13", "5C13N15", "10C13", "10C13N15"]:
            df[col + "_percent"] = df[col] / (df["No label"] + df["sum_labelled"]) * 100
    else:
        df = df.drop(["N15", "5C13", "5C13N15", "10C13", "10C13N15"], axis=1)

    if nad_amount:
        df["nad_amount_no_label"] = df["no_label_percent"] * nad_amount / 100
        df["nad_amount_labelled"] = df["sum_labelled_percent"] * nad_amount / 100

        rates = []
        for name, data in df.groupby("Experiment"):
            nad_amount_diff = data["nad_amount_labelled"].diff()
            time_diff = data.reset_index()["Time in hours"].diff()
            time_diff.index = data.index
            rate = nad_amount_diff / time_diff
            rate = rate.to_frame(name="nad_labelled_rate")
            rate["Experiment"] = name
            rates.append(rate)
        rates = pd.concat(rates)
        df = pd.merge(df, rates, on=["Time in hours", "Experiment"])

    # Scaled amount NAD per mg protein
    if nad_protein:
        df["nad_protein_no_label"] = df["no_label_percent"] * nad_protein / 100
        df["nad_protein_labelled"] = df["sum_labelled_percent"] * nad_protein / 100

    if nad_conc:
        df["nad_intraconc_no_label"] = df["no_label_percent"] * nad_conc / 100
        df["nad_intraconc_labelled"] = df["sum_labelled_percent"] * nad_conc / 100

    df["Exp"] = exp_name
    return df


def read_model_output(files, start_time=10_000, sep="\t"):
    """Parse model output files

    Takes file list and returns DataFrame
    :param files: str or list of str
        (List of) pathes to files
    :param start_time: int (default: 10 000)
        Start time of simulation in minutes, will be substracted
    :param sep: char (default: "\t")
        Separator of input file
    """
    if isinstance(files, str):
        files = [files]
    dfs = []
    for file in files:
        name = os.path.basename(os.path.splitext(file)[0])
        df = pd.read_csv(file, sep=sep)
        df["Time"] = df["Time"] - start_time
        df["Time in hours"] = df["Time"] / 60
        df.rename(
            columns={
                "Time": "Time in minutes",
                "Values[NAD_labelled_sum]": "sum_labelled",
                "[NAD]": "No label",
            },
            inplace=True,
        )
        df.set_index("Time in hours", inplace=True)
        df = df[df.index >= 0]
        df["no_label_percent"] = (
            df["No label"] / (df["No label"] + df["sum_labelled"]) * 100
        )
        df["sum_labelled_percent"] = (
            df["sum_labelled"] / (df["No label"] + df["sum_labelled"]) * 100
        )
        df["Exp"] = name
        dfs.append(df)
    df = pd.concat(dfs, sort=False, axis=0, join="inner")
    return df


def analyse_metabolites(
    df, metabolites, label_used=5, isotopologue_correction=True, verbose=False
):
    """Analyse dataframes with multiple labelled metabolites.

    Cleans columns (renaming and dropping) and calculates (iso corrected)
    percentages for each metabolite.
    :param df: pandas DataFrame
        Raw read dataframe with unlabelled and labelled measurements in columns
        e.g. column title: "ATP" and "ATP+5"
    :param metabolites: list of str
        List of metabolites used as column identifiers
    :param label_used: str or int (default: 5)
        Used in column label accession
    :param isotopologue_correction: boolean (default: True)
        Do isotopologue correction
    :param verbose: boolean (default: False)
        Print more verbose information
    :return: pandas DataFrame
        Dataframe with percentage columns
    """
    df.dropna(axis="index", how="any", inplace=True)
    df.rename(columns={"Hours": "Time in hours"}, inplace=True)
    df.drop(columns=["Timepoint", "Replicate"], inplace=True)
    df.replace(293, "293", inplace=True)  # Prevents problems with int type index
    df.set_index(["Cell line", "Time in hours"], inplace=True)
    for metabolite in metabolites:
        unlabelled = metabolite + ":No label"
        labelled = metabolite + f":{label_used}C13"
        df.rename(
            columns={metabolite: unlabelled, f"{metabolite}+{label_used}": labelled},
            inplace=True,
        )
        if isotopologue_correction:
            subset = [unlabelled, labelled]
            df = calc_isotopologue_correction(df, metabolite, subset, verbose=verbose)
        unlabelled_per = unlabelled + "_percent"
        labelled_per = labelled + "_percent"
        df[unlabelled_per] = df[unlabelled] / (df[unlabelled] + df[labelled]) * 100
        df[labelled_per] = 100 - df[unlabelled_per]
    return df


if __name__ == "__main__":
    folder_base = os.path.join("..", "data")
    # Split mixed datasets into NAD and ATP ones

    # File conversion to csv and iso corr
    infiles = [
        "labelling_experiments_cell_lines_wcl_mito_separation_techrepl1.xlsx",
        "labelling_experiments_cell_lines_wcl_mito_separation_techrepl2.xlsx",
        "labelling_experiments_cell_lines.xlsx",
        "labelling_experiments_mitochondria.xlsx",
    ]

    for file in infiles:
        infile = os.path.join(folder_base, file)
        excel2csv(infile, isotopologue_correction="all", verbose=1)

    ###########################################################
    # Iso Correction and analysis of cell line experiments
    ###########################################################

    suffix = ".csv"
    folder = os.path.join(folder_base, "labelling_experiments_cell_lines")
    outfolder = folder
    outsuffix = "_iso_corr.csv"

    glob_list = [
        "293_?.?",
        "CytoPARP_?.?",
        "ER_PARP_?.?",
        "mitoPARP_?.?",
        "pexPARP_?.?",
    ]

    for g in glob_list:
        full_glob = os.path.join(folder, f"{g}{suffix}")
        print(full_glob)
        outfile = os.path.join(outfolder, f"{g}_sum{outsuffix}")
        df = analyse_rawfiles(full_glob)
        df.to_csv(outfile)
        for i in range(1, 3):
            f = g.replace("?", str(i), 1)
            full_glob = os.path.join(folder, f"{f}{suffix}")
            outfile = os.path.join(outfolder, f"{f}_sum{outsuffix}")
            try:
                df = analyse_rawfiles(full_glob)
                df.to_csv(outfile)
            except ValueError:
                print(f"{full_glob} not found")

    # Calculate labelled and unlabelled NAD amount and concentration
    # and saves it in separate file

    # total intracellular NAD concentration in nmol/mg protein
    nad_protein_list = {
        "293": 18.04,
        "pexPARP": 9.51,
        "mitoPARP": 10.23,
        "CytoPARP": 10.87,
        "ER_PARP": 11.17,
    }

    dfs = []
    for g in glob_list:
        outfile = os.path.join(outfolder, f"{g}_nad_amount_concentration{outsuffix}")
        nad_protein = nad_protein_list[g[:-4]]
        full_glob = os.path.join(folder, g + suffix)
        df = analyse_rawfiles(full_glob, nad_protein=nad_protein)
        df.drop(["Exp"], axis=1, inplace=True)
        df.to_csv(outfile)

    ###########################################################
    # labelling_experiments_cell_lines_wcl_mito_separation
    ###########################################################

    folders = [
        "labelling_experiments_cell_lines_wcl_mito_separation_techrepl1",
        "labelling_experiments_cell_lines_wcl_mito_separation_techrepl2",
    ]

    cell_lines = ["293", "CP", "ER", "MP", "PP"]
    glob_list = []
    for c in cell_lines:
        glob_list.append(c + "_mito_?")
        glob_list.append(c + "_WCL_?")

    for folder in folders:
        folder = os.path.join(folder_base, folder)
        outfolder = folder
        for g in glob_list:
            full_glob = os.path.join(folder, f"{g}{suffix}")
            outfile = os.path.join(outfolder, f"{g}_sum{outsuffix}")
            df = analyse_rawfiles(full_glob)
            df.to_csv(outfile)
            for i in range(1, 3):
                f = g.replace("?", str(i), 1)
                full_glob = os.path.join(folder, f"{f}{suffix}")
                outfile = os.path.join(outfolder, f"{f}_sum{outsuffix}")
                try:
                    df = analyse_rawfiles(full_glob)
                    df.to_csv(outfile)
                except ValueError:
                    print(f"{full_glob} not found")

    # Renames keys to match different cell line labelling
    nad_protein_list["PP"] = nad_protein_list.pop("pexPARP")
    nad_protein_list["MP"] = nad_protein_list.pop("mitoPARP")
    nad_protein_list["CP"] = nad_protein_list.pop("CytoPARP")
    nad_protein_list["ER"] = nad_protein_list.pop("ER_PARP")

    dfs = []
    for g in glob_list:
        if re.search("_mito_?", g):
            continue
        index = g.split("_")[0]
        outfile = os.path.join(outfolder, f"{g}_nad_amount_concentration{outsuffix}")
        nad_protein = nad_protein_list[index]
        full_glob = os.path.join(folder, g + suffix)
        df = analyse_rawfiles(full_glob, nad_protein=nad_protein)
        df.drop(["Exp"], axis=1, inplace=True)
        df.to_csv(outfile)
