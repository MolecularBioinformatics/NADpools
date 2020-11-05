import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
from pandas import DataFrame

import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)


def read_isolated_enzyme_output(files, sep="\t"):
    """Parse model output files

    Takes file list and returns DataFrame
    :param files: str or list of str
        (List of) pathes to files
    :param sep: char (default: "\t")
        Separator of input file
    """
    sep = "\t"
    if isinstance(files, str):
        files = [files]
    dfs = []
    for file in files:
        # name = os.path.basename(os.path.splitext(file)[0])
        df = pd.read_csv(file, sep=sep)
        df.rename(
            columns={
                "[NAD]_0": "NAD_conc",
                "(NAD consumption).Flux": "NAD_flux",
                "Values[NAD consumption vmax].InitialValue": "Vmax_consumption",
                "Values[NamPT vmax].InitialValue": "biosyn_flux",
            },
            inplace=True,
        )
        dfs.append(df)
    df = pd.concat(dfs, sort=False, axis=0, join="inner")
    df.set_index("NAD_conc", inplace=True)
    return df


def plot_isolates_enzymes(
    data,
    colors,
    title="NAD consumption Vmax",
    ylines=None,
    label=None,
    outfile=None,
    show_legend=False,
    xlim=None,
    ylim=None,
):
    """Plot NAD flux vs concentration

    Newly synthesized NAD in percentage of total
    Confidence intervall is plotted as well
    :param data: pandas DataFrame
        DataFrame with data to plot
    :param colors: list of str
        List of colors
    :param title: str
        Title for plot
    :param label: dict
        Vmax as key and label as value
    :param outfile: None or str
        File path to location where the plot is saved.
        (suffix) determines output format
    :param  show_legend: bool (default: False)
        display legend
    :param xlim: None or List of two values (either can be None)
        Plotted x-axis view limits
    :param ylim: None or List of two values (either can be None)
        Plotted y-axis view limits
    """

    # Style options
    dimensions = (5, 5)  # Dimensions of plot in inch
    fig, ax = plt.subplots(figsize=dimensions)
    sns.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 1})
    sns.set_style("ticks")
    plt.rcParams.update({"errorbar.capsize": 4})

    if isinstance(data, DataFrame):
        df = data
    else:
        raise ValueError("data must be pandas Dataframe")

    sns.lineplot(
        data=data,
        x=data.index,
        y="biosyn_flux",
        label=f"Biosynthesis",
        color=colors.pop(),
    )
    ax.lines[-1].set_linestyle("--")
    for name, data in df.groupby("Vmax_consumption"):
        sns.lineplot(
            data=data,
            x=data.index,
            y="NAD_flux",
            label=label[name],
            color=colors.pop(),
        )
    ax.set_ylabel("Reaction flux [mM/s]")
    ax.set_xlabel("Free NAD concentration [mM]")
    plt.title(title)
    if ylines:
        for line in ylines:
            plt.vlines(line[0], 0, line[1], line[2], linestyle=":")
            # ax.axvline(line[0], 0, 0.05, color=line[2], linestyle="--")

    if xlim:
        ax.set_xlim(left=xlim[0], right=xlim[1])
    if ylim:
        ax.set_ylim(bottom=ylim[0], top=ylim[1])

    ax.legend().set_visible(show_legend)
    sns.despine()

    if outfile:
        print("Saving {}".format(outfile))
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    plt.show()


def plot_3ab_flux(
    data,
    title="Consumption vs synthesis flux",
    outfile=None,
    show_legend=False,
    xlim=None,
    ylim=None,
):
    """Plot NAD flux vs concentration

    Newly synthesized NAD in percentage of total
    Confidence intervall is plotted as well
    :param data: pandas DataFrame
        DataFrame with data to plot
    :param colors: list of str
        List of colors
    :param title: str
        Title for plot
    :param outfile: None or str
        File path to location where the plot is saved.
        (suffix) determines output format
    :param  show_legend: bool (default: False)
        display legend
    :param xlim: None or List of two values (either can be None)
        Plotted x-axis view limits
    :param ylim: None or List of two values (either can be None)
        Plotted y-axis view limits
    """
    # Style options
    dimensions = (10, 5)  # Dimensions of plot in inch
    fig, ax = plt.subplots(figsize=dimensions)
    sns.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 1})
    sns.set_style("ticks")
    plt.rcParams.update({"errorbar.capsize": 4})

    if isinstance(data, DataFrame):
        df = data
    else:
        raise ValueError("data must be pandas Dataframe")

    n = df.groupby("Time in hours").count().iloc[1, 0]
    palette = "Paired"
    colors = sns.color_palette(palette, n_colors=2 * n)

    for name, data in df.groupby("Exp"):
        print(name)
        sns.lineplot(
            data=data,
            x=data.index,
            y="Values[Biosynthesis fluxes]",
            label=f"Synthesis {name}",
            color=colors.pop(),
        )
        sns.lineplot(
            data=data,
            x=data.index,
            y="Values[Consumption fluxes]",
            label=f"Consumption {name}",
            color=colors.pop(),
        )
    ax.set_ylabel("Reaction flux [mM/min]")
    ax.set_xlabel("Time in hours")
    plt.title(title)

    if xlim:
        ax.set_xlim(left=xlim[0], right=xlim[1])
    if ylim:
        ax.set_ylim(bottom=ylim[0], top=ylim[1])

    ax.legend().set_visible(show_legend)
    sns.despine()

    if outfile:
        print("Saving {}".format(outfile))
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    plt.show()
