import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pandas import DataFrame
import warnings
import copy
import numpy as np

from convert_csv import analyse_rawfiles
from analyse_na import analyse_rawfiles_na
from half_life_estimation import estimate_half_life

warnings.simplefilter(action="ignore", category=FutureWarning)


def plot_exp_data(
    data,
    confidence=95,
    yaxis="percental",
    scatter=True,
    multiplot=False,
    show_intermediates=False,
    half_life=False,
    title=None,
    colors=None,
    outfile=None,
    xlim=None,
    trim_label="last",
    ylabel=None,
    dimensions=(5, 5),
    show_legend=True,
):
    """Plot relative or absolute counts of datasets

    Confidence intervall is plotted as well

    :param data: str or list of str or pandas DataFrame
        String or list of strings which contains regex expression
        to describe all datasets belonging together
    :param confidence: None or int [0;100]
        Confidence threshold for plotted interval
    :param yaxis: percental, absolut, nad_amount, nad_conc, nad_protein, nad_rate
        Decides if absolute counts or percentage (row-wise) is plotted
    :param scatter: boolean (default: True)
        Whether to plot  individual data points or line for x-measurements
    :param multiplot: boolean (default: False)
        Used for multiplots, iterates over "Exp"
    :param show_intermediates: False, True or 'Full'(default: False)
        also plot isotopologue intermediates
    :param half_life: boolean (default: False)
        Prints half_life time in title
    :param title: none or str
        Title for plot
    :param colors: list of str (default: None)
        Colors to be used for plotting
    :param outfile: None or str or list of str
        File path or list of file paths to location where the plot is saved.
        suffix determines output format
    :param xlim: None or List of two values (either can be None)
        Plotted x-axis view limits
    :param trim_label: "first", "last" or False (default: "last")
        Whether to trim last filed after a "_" in group name
    :param ylabel: str (default: None)
        Label for y-axis, otherwise standard based on yaxis will be used
    :param dimensions: tuple of float (default: (5,5))
        Dimensions of plot in inch
    :param show_legend: boolean (default: True)
        Displays legend in plot
    """
    errmsg = "Intermediate plotting only supported for percental without multiplot"

    # Style options
    fig, ax = plt.subplots(figsize=dimensions)
    sns.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 1})
    sns.set_style("ticks")

    if isinstance(data, str):
        df = analyse_rawfiles(data, show_intermediates=show_intermediates)
    elif isinstance(data, list):
        dfs = []
        for g in data:
            dfs.append(analyse_rawfiles(g, show_intermediates=show_intermediates))
        df = pd.concat(dfs)
    elif isinstance(data, DataFrame):
        df = data
    else:
        raise ValueError("data must be string or pandas Dataframe")

    if half_life:
        half_life = estimate_half_life(df, pretty_print=True)

    if title:
        exp_name = title
    elif not title and not multiplot:
        exp_name = data[:-4]
    else:
        exp_name = "Multi plot"

    # Plot vertical lines for each sample time point
    if scatter:
        confidence = None

    if multiplot:
        n = []
        n_exp = df["Exp"].nunique()
        # palette = "Paired" if not show_intermediates else "bright"
        # n_colors = 2 * n_exp if not show_intermediates else 3 * n_exp
        if show_intermediates:
            palette = "bright"
            n_colors = 3 * n_exp
        elif yaxis in ["nad_conc", "nad_amount", "nad_protein"]:
            palette = "bright"
            n_colors = n_exp
        else:
            palette = "Paired"
            n_colors = 2 * n_exp
        if not colors:
            colors = sns.color_palette(palette, n_colors=n_colors)
        colors_scatter = copy.deepcopy(colors)
        for name, group in df.groupby("Exp"):
            data = group
            # Gather number of samples for all groups
            n.append(data.groupby("Time in hours").count().iloc[1, 0])
            print(name)
            if trim_label == "last":
                label_group = "_".join(name.split("_")[:-1])
            elif trim_label == "first":
                label_group = "_".join(name.split("_")[1:])
            elif not trim_label:
                label_group = name
            else:
                raise ValueError("trim_label can be either False, 'last' or 'first'")
            if yaxis == "percental":
                sns.lineplot(
                    data=data,
                    x=data.index,
                    y="no_label_percent",
                    label=f"{label_group} unlabelled",
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y="no_label_percent",
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )

                if not show_intermediates:
                    sns.lineplot(
                        data=data,
                        x=data.index,
                        y="sum_labelled_percent",
                        label=f"{label_group} sum labelled",
                        ci=confidence,
                        color=colors.pop(),
                    )
                    if scatter:
                        sns.scatterplot(
                            data=data,
                            x=data.index,
                            y="sum_labelled_percent",
                            color=colors_scatter.pop(),
                            label="_nolegend_",
                        )
                else:
                    if show_intermediates == "Full":
                        sns.lineplot(
                            data=data,
                            x=data.index,
                            y="N15_percent",
                            label=f"{label_group} N15",
                            ci=confidence,
                            color=colors.pop(),
                        )
                        sns.lineplot(
                            data=data,
                            x=data.index,
                            y="5C13_percent",
                            label=f"{label_group} 5C13",
                            ci=confidence,
                            color=colors.pop(),
                        )
                        sns.lineplot(
                            data=data,
                            x=data.index,
                            y="10C13_percent",
                            label=f"{label_group} 10C13",
                            ci=confidence,
                            color=colors.pop(),
                        )
                        if scatter:
                            sns.scatterplot(
                                data=data,
                                x=data.index,
                                y="N15_percent",
                                color=colors_scatter.pop(),
                                label="_nolegend_",
                            )
                            sns.scatterplot(
                                data=data,
                                x=data.index,
                                y="5C13_percent",
                                color=colors_scatter.pop(),
                                label="_nolegend_",
                            )
                            sns.scatterplot(
                                data=data,
                                x=data.index,
                                y="10C13_percent",
                                color=colors_scatter.pop(),
                                label="_nolegend_",
                            )
                    sns.lineplot(
                        data=data,
                        x=data.index,
                        y="5C13N15_percent",
                        label=f"{label_group} 5C13 N15",
                        ci=confidence,
                        color=colors.pop(),
                    )
                    sns.lineplot(
                        data=data,
                        x=data.index,
                        y="10C13N15_percent",
                        label=f"{label_group} 10C13 N15",
                        ci=confidence,
                        color=colors.pop(),
                    )
                    if scatter:
                        sns.scatterplot(
                            data=data,
                            x=data.index,
                            y="5C13N15_percent",
                            color=colors_scatter.pop(),
                            label="_nolegend_",
                        )
                        sns.scatterplot(
                            data=data,
                            x=data.index,
                            y="10C13N15_percent",
                            color=colors_scatter.pop(),
                            label="_nolegend_",
                        )
                if ylabel:
                    ax.set_ylabel(ylabel)
                else:
                    ax.set_ylabel("Percentage of total NAD")
            elif yaxis == "absolut":
                if show_intermediates:
                    raise NotImplementedError(errmsg)
                sns.lineplot(
                    data=data,
                    x=data.index,
                    y="No label",
                    label=f"{label_group} unlabelled",
                    ci=confidence,
                    color=colors.pop(),
                )
                sns.lineplot(
                    data=data,
                    x=data.index,
                    y="sum_labelled",
                    label=f"{label_group} labelled",
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y="No label",
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y="sum_labelled",
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )

                if ylabel:
                    ax.set_ylabel(ylabel)
                else:
                    ax.set_ylabel("Absolut counts")
            elif yaxis == "nad_amount":
                if show_intermediates:
                    raise NotImplementedError(errmsg)
                sns.lineplot(
                    data=data,
                    x=data.index,
                    y="nad_amount_labelled",
                    label=f"{label_group} labelled",
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y="nad_amount_labelled",
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )
                if ylabel:
                    ax.set_ylabel(ylabel)
                else:
                    ax.set_ylabel("NAD amount [nmol]")
            elif yaxis == "nad_conc":
                if show_intermediates:
                    raise NotImplementedError(errmsg)
                sns.lineplot(
                    data=data,
                    x=data.index,
                    y="nad_intraconc_labelled",
                    label=f"{label_group} labelled",
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y="nad_intraconc_labelled",
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )
                if ylabel:
                    ax.set_ylabel(ylabel)
                else:
                    ax.set_ylabel("Intracellular NAD concentration [mM]")
            elif yaxis == "nad_protein":
                if show_intermediates:
                    raise NotImplementedError(errmsg)
                sns.lineplot(
                    data=data,
                    x=data.index,
                    y="nad_protein_labelled",
                    label=f"{label_group} labelled",
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y="nad_protein_labelled",
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )
                if ylabel:
                    ax.set_ylabel(ylabel)
                else:
                    ax.set_ylabel("NAD scaled by amount [nmol/mg protein]")

            elif yaxis == "nad_rate":
                if show_intermediates:
                    raise NotImplementedError(errmsg)
                sns.lineplot(
                    data=data,
                    x=data.index,
                    y="nad_labelled_rate",
                    label=f"{label_group}",
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y="nad_labelled_rate",
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )
                if ylabel:
                    ax.set_ylabel(ylabel)
                else:
                    ax.set_ylabel("Unlabelled NAD consumption [nmol/h]")

            else:
                raise ValueError("y-Axis type not recognized")
    else:
        # Get the number of samples by looking how often a index occurs
        n = df.groupby("Time in hours").count().iloc[1, 0]
        # Color palette
        palette = "bright"
        n_colors = 8
        if not colors:
            colors = sns.color_palette(palette, n_colors=n_colors)
        colors_scatter = copy.deepcopy(colors)

        if yaxis == "percental":
            metabolites = {
                "no_label_percent": "Unlabelled",
                "sum_labelled_percent": "Sum of labelled",
            }
            if show_intermediates:
                metabolites_inter = {
                    "N15_percent": "N15",
                    "5C13_percent": "5C13",
                    "5C13N15_percent": "5C13N15",
                    "10C13_percent": "10C13",
                    "10C13N15_percent": "10C13N15",
                }
                metabolites.update(metabolites_inter)
            for met in metabolites:
                sns.lineplot(
                    data=df,
                    x=df.index,
                    y=met,
                    label=metabolites[met],
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=df,
                        x=df.index,
                        y=met,
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )

                ax.set_ylabel("Percentage of total NAD")

        elif yaxis == "absolut":
            df["total_sum"] = df["sum_labelled"] + df["No label"]
            metabolites = {
                "No label": "Unlabelled",
                "sum_labelled": "Sum of labelled",
                "total_sum": "Total sum",
            }
            if show_intermediates:
                metabolites_inter = {
                    "N15": "N15",
                    "5C13": "5C13",
                    "5C13N15": "5C13N15",
                    "10C13": "10C13",
                    "10C13N15": "10C13N15",
                }
                metabolites.update(metabolites_inter)
            for met in metabolites:
                sns.lineplot(
                    data=df,
                    x=df.index,
                    y=met,
                    label=metabolites[met],
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=df,
                        x=df.index,
                        y=met,
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )
            ax.set_ylabel("Absolut counts")

        elif yaxis == "nad_protein":
            if show_intermediates:
                raise NotImplementedError(errmsg)
            metabolites = {
                "nad_protein_no_label": "Unlabelled",
                "nad_protein_labelled": "Sum of labelled",
            }
            for met in metabolites:
                sns.lineplot(
                    data=df,
                    x=df.index,
                    y=met,
                    label=metabolites[met],
                    ci=confidence,
                    color=colors.pop(),
                )
                if scatter:
                    sns.scatterplot(
                        data=data,
                        x=data.index,
                        y=met,
                        color=colors_scatter.pop(),
                        label="_nolegend_",
                    )
            ax.set_ylabel("NAD scaled by amount per mg protein")

        elif yaxis == "nad_rate":
            if show_intermediates:
                raise NotImplementedError(errmsg)
            sns.lineplot(
                data=data,
                x=data.index,
                y="nad_labelled_rate",
                ci=confidence,
                color=colors.pop(),
            )
            if scatter:
                sns.scatterplot(
                    data=data,
                    x=data.index,
                    y="nad_labelled_rate",
                    color=colors_scatter.pop(),
                    label="_nolegend_",
                )

            ax.set_ylabel("Rate of unlabelled NAD consumption [nmol/h]")

        else:
            raise ValueError("y-Axis type not recognized")

    if half_life:
        plt.title("{} (t½={}±{}, n={})".format(exp_name, half_life[0], half_life[1], n))
    else:
        plt.title("{} (n={})".format(exp_name, n))

    if xlim:
        ax.set_xlim(left=xlim[0], right=xlim[1])

    ax.legend().set_visible(show_legend)
    sns.despine()

    if isinstance(outfile, str):
        print("Saving {}".format(outfile))
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    elif outfile:
        try:
            for f in outfile:
                print("Saving {}".format(outfile))
                plt.savefig(f, dpi=300, bbox_inches="tight")
        except TypeError:
            warnings.warn("outfile should be str or list of string")
    plt.show()


def plot_publ(
    data,
    species=None,
    show_intermediates=False,
    half_life=False,
    multiplot=False,
    xmarks="scatter",
    title=None,
    outfile=None,
    show_legend=False,
    xlim=None,
    ylim=None,
):
    """Plot percentage of sums or individual species

    Confidence intervall is plotted as well
    :param data: str or list of str or pandas DataFrame
        String or list of strings which contains regex expression
        to describe all datasets belonging together
    :param species: str (default: None)
        Species to be plotted
    :param show_intermediates: False, True or 'Full'(default: False)
        also plot isotopologue intermediates
    :param half_life: boolean (default: False)
        Prints half_life time in title
    :param multiplot: dict of color strings (default: False)
        Used for multiplots, iterates over "Exp"
        Dict of colors (str) for each Exp
    :param xmarks: "lines", "marker" or "scatter" (default: "scatter")
        Markers for x measurement points
    :param title: none or str
        Title for plot
    :param outfile: None or str
        File path to location where the plot is saved. (suffix) determines output format
    :param  show_legend: bool (default: False)
        display legend
    :param xlim: None or List of two values (either can be None)
        Plotted x-axis view limits
    :param ylim: None or List of two values (either can be None)
        Plotted y-axis view limits
    """

    # Style options
    markersize = 10
    scattersize = 15
    confidence = 95
    dimensions = (5, 5)  # Dimensions of plot in inch
    fig, ax = plt.subplots(figsize=dimensions)
    sns.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 1})
    sns.set_style("ticks")

    if isinstance(data, str):
        df = analyse_rawfiles(data, show_intermediates=show_intermediates)
    elif isinstance(data, list):
        dfs = []
        for g in data:
            dfs.append(analyse_rawfiles(g, show_intermediates=show_intermediates))
        df = pd.concat(dfs)
    elif isinstance(data, DataFrame):
        df = data
    else:
        raise ValueError("data must be string or pandas Dataframe")

    if half_life:
        half_life = estimate_half_life(df, pretty_print=True)

    if title:
        exp_name = title
    else:
        exp_name = data[:-4]

    marker = None  # Draw marker in lineplot
    scatter = False  # Additional scatter plot instead of confidence interval
    if xmarks == "lines":
        pass
    elif xmarks == "marker":
        marker = "o"
    elif xmarks == "scatter":
        scatter = True
        confidence = None
    else:
        raise NotImplementedError("Only 'lines', 'marker' and 'scatter' implemented")

    # Get the number of samples by looking how often a index occurs

    if isinstance(multiplot, dict):
        n = []
        for name, data in df.groupby("Exp"):
            n.append(data.groupby("Time in hours").count().iloc[1, 0])
            try:
                color = multiplot[name]
            except KeyError:
                raise ValueError(
                    f"multiplot has to be False or dict of colors for each experiment;"
                    "\nMissing color for {name}"
                )
            sns.lineplot(
                data=data,
                x=data.index,
                y="no_label_percent",
                label=f"{name} unlabelled",
                ci=confidence,
                color=color,
            )
            sns.lineplot(
                data=data,
                x=data.index,
                y="sum_labelled_percent",
                label=f"{name} sum labelled",
                ci=confidence,
                color=color,
            )
            ax.lines[-1].set_linestyle("--")
            if scatter:
                sns.scatterplot(
                    data=data,
                    x=data.index,
                    y="no_label_percent",
                    label="_nolegend_",
                    color=color,
                    s=scattersize,
                    linewidth=0,
                )
                sns.scatterplot(
                    data=data,
                    x=data.index,
                    y="sum_labelled_percent",
                    label="_nolegend_",
                    color=color,
                    s=scattersize,
                    linewidth=0,
                )
    elif not species:
        n = df.groupby("Time in hours").count().iloc[1, 0]
        color_unlab = "black"
        color_lab = "#808080"
        sns.lineplot(
            data=df,
            x=df.index,
            y="no_label_percent",
            label="Unlabelled",
            ci=confidence,
            color=color_unlab,
            marker=marker,
            markersize=markersize,
        )
        sns.lineplot(
            data=df,
            x=df.index,
            y="sum_labelled_percent",
            label="Sum of labelled",
            ci=confidence,
            color=color_lab,
            marker=marker,
            markersize=markersize,
        )
        if scatter:
            sns.scatterplot(
                data=df,
                x=df.index,
                y="no_label_percent",
                label="_nolegend_",
                color=color_unlab,
                s=scattersize,
                linewidth=0,
            )
            sns.scatterplot(
                data=df,
                x=df.index,
                y="sum_labelled_percent",
                label="_nolegend_",
                color=color_lab,
                s=scattersize,
                linewidth=0,
            )
        ax.lines[-1].set_linestyle("--")
        if show_intermediates:
            sns.lineplot(
                data=df,
                x=df.index,
                y="N15_percent",
                label="N15",
                ci=confidence,
                marker=marker,
                markersize=markersize,
            )
            sns.lineplot(
                data=df,
                x=df.index,
                y="5C13_percent",
                label="5C13",
                ci=confidence,
                marker=marker,
                markersize=markersize,
            )
            sns.lineplot(
                data=df,
                x=df.index,
                y="5C13N15_percent",
                label="5C13 N15",
                ci=confidence,
                marker=marker,
                markersize=markersize,
            )
            sns.lineplot(
                data=df,
                x=df.index,
                y="10C13_percent",
                label="10C13",
                ci=confidence,
                marker=marker,
                markersize=markersize,
            )
            sns.lineplot(
                data=df,
                x=df.index,
                y="10C13N15_percent",
                label="10C13 N15",
                ci=confidence,
                markersize=markersize,
            )
    else:
        n = df.groupby("Time in hours").count().iloc[1, 0]
        sns.lineplot(
            data=df,
            x=df.index,
            y=f"{species}_percent",
            label=species,
            ci=confidence,
            color="black",
            marker=marker,
            markersize=markersize,
        )
        if scatter:
            sns.scatterplot(
                data=df,
                x=df.index,
                y=f"{species}_percent",
                label="_nolegend_",
                color="black",
                s=scattersize,
                linewidth=0,
            )
    ax.set_ylabel("Percentage of total NAD")
    if half_life:
        plt.title("{} (t½={}±{}, n={})".format(exp_name, half_life[0], half_life[1], n))
    else:
        plt.title("{} (n={})".format(exp_name, n))

    if xlim:
        ax.set_xlim(left=xlim[0], right=xlim[1])
    # else:
    #     ax.set_xlim(left=0)
    if ylim:
        ax.set_ylim(bottom=ylim[0], top=ylim[1])
    # else:
    #     ax.set_ylim(bottom=0)

    ax.legend().set_visible(show_legend)
    sns.despine()

    if outfile:
        print("Saving {}".format(outfile))
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    plt.show()


def plot_simu_abs(
    data,
    title="Simulated concentrations",
    color=None,
    outfile=None,
    ylabel="Free concentration [mM]",
    half_life=False,
    show_legend=True,
    xlim=None,
    ylim=None,
):
    """Plot simulated NAD amount

    :param data: pandas DataFrame
        data to plot, must have "sum_labelled" and "No label" column
    :param title: str (default: "Simulated concentrations")
        Title for plot
    :param colors: str (default: None)
        Color to be used for plotting
    :param outfile: None or str
        File path to location where the plot is saved.
        (suffix) determines output format
    :param ylabel: str (default:"NAD concentration [mM]")
        label for y-axis
    :param half_life: boolean (default: False)
        Prints half_life time in title
    :param show_legend: bool (default: False)
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
    df["total_sum"] = df["sum_labelled"] + df["No label"]

    palette = "bright"
    if color:
        colors = ["magenta", color, color]
    else:
        colors = sns.color_palette(palette, n_colors=3)
    metabolites = {
        "No label": "Unlabelled NAD",
        "sum_labelled": "Labelled NAD",
        "total_sum": "Total NAD",
    }

    for met in metabolites:
        sns.lineplot(
            data=df,
            x=df.index,
            y=met,
            label=metabolites[met],
            ci=None,
            color=colors.pop(),
        )

    ax.lines[-2].set_linestyle("--")
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Time in hours")
    if half_life:
        half_life = estimate_half_life(df, pretty_print=True)
        plt.title("{} (t½={})".format(title, half_life[0]))
    else:
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


def plot_simu_flux(
    data,
    colors,
    title="Consumption vs synthesis flux",
    outfile=None,
    show_legend=False,
    labels=None,
    xlim=None,
    ylim=None,
):
    """Plot NAD flux vs concentration

    Newly synthesized NAD in percentage of total
    Confidence intervall is plotted as well
    :param data: pandas DataFrame
        DataFrame with data to plot
    :param colors: dict of str
        dict key should be same as value in Exp
    :param title: str
        Title for plot
    :param outfile: None or str
        File path to location where the plot is saved.
        (suffix) determines output format
    :param  show_legend: bool (default: False)
        display legend
    :param labels: dict of str (default: None)
        Used as label in legend; dict key should be same as value in Exp
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

    for name, data in df.groupby("Exp"):
        print(name)
        label = labels[name] if labels else name
        sns.lineplot(
            data=data,
            x=data.index,
            y="Values[Consumption fluxes]",
            label=f"Consumption {label}",
            color=colors[name],
        )
        sns.lineplot(
            data=data,
            x=data.index,
            y="Values[Biosynthesis fluxes]",
            label=f"Synthesis {label}",
            color=colors[name],
        )
        ax.lines[-1].set_linestyle("--")
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


def plot_nad_amount(
    data,
    nad_mean,
    nad_std=None,
    multiplot=None,
    title=None,
    outfile=None,
    ylabel="Newly synthesized NAD [nmol/mg prot]",
    xlim=None,
    ylim=None,
):
    """Plot NAD amount of sums or individual species

    Confidence intervall is plotted as well
    :param data: str or list of str or pandas DataFrame
        String or list of strings which contains regex expression
        to describe all datasets belonging together
    :param nad_mean: pandas Series
        Total intracellular NAD amount
        Key should correspond to name of sub datasets
    :param nad_std: pandas Series (default=None)
        Std of NAD amount/concentration
        Key should correspond to name of sub datasets
    :param multiplot: None or dict of color strings
        Used for multiplots, iterates over "Exp"
        Dict of colors (str) for each Exp
    :param title: none or str
        Title for plot
    :param outfile: None or str
        File path to location where the plot is saved.
        (suffix) determines output format
    :param ylabel: str (default:"Total cellular NAD [nmol/mg prot]")
        label for y-axis
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

    if isinstance(data, str):
        df = analyse_rawfiles(data, show_intermediates=False)
    elif isinstance(data, list):
        dfs = []
        for g in data:
            dfs.append(analyse_rawfiles(g, show_intermediates=False))
        df = pd.concat(dfs)
    elif isinstance(data, DataFrame):
        df = data
    else:
        raise ValueError("data must be string or pandas Dataframe")

    if title:
        exp_name = title
    else:
        exp_name = "NAD Amount ± s.d."

    n = []

    for name, data in df.groupby("Exp"):
        try:
            color = multiplot[name]
        except (TypeError, KeyError):
            raise ValueError(
                f"multiplot has to be False or dict of colors for each experiment;"
                f"\n Missing color for {name}"
            )

        # Get the number of samples by looking how often a index occurs
        n.append(data.groupby("Time in hours").count().iloc[1, 0])

        nad_amount_mean = nad_mean.loc[name]
        nad_amount_std = nad_std.loc[name] if isinstance(nad_std, pd.Series) else None
        y_mean, y_std = calc_nad_mean(data, nad_amount_mean, nad_amount_std)
        plt.errorbar(
            x=data.index.unique(),
            y=y_mean,
            yerr=y_std,
            label=f"{name} labelled",
            color=color,
        )

    ax.set_ylabel(ylabel)
    ax.set_xlabel("Time in hours")
    plt.title("{} (n={})".format(exp_name, n))

    if xlim:
        ax.set_xlim(left=xlim[0], right=xlim[1])
    if ylim:
        ax.set_ylim(bottom=ylim[0], top=ylim[1])

    ax.legend().set_visible(False)
    sns.despine()

    if outfile:
        print("Saving {}".format(outfile))
        plt.savefig(outfile, dpi=300, bbox_inches="tight")
    plt.show()


def plot_syn_per(
    data,
    multiplot=False,
    title=None,
    outfile=None,
    ylabel="Percentage of total NAD",
    errorbars=True,
    show_legend=False,
    xlim=None,
    ylim=None,
):
    """Plot NAD percentage of sums or individual species

    Newly synthesized NAD in percentage of total
    Confidence intervall is plotted as well
    :param data: str or list of str or pandas DataFrame
        String or list of strings which contains regex expression
        to describe all datasets belonging together
    :param multiplot: dict of color strings (default: False)
        Used for multiplots, iterates over "Exp"
        Dict of colors (str) for each Exp
    :param title: none or str
        Title for plot
    :param outfile: None or str
        File path to location where the plot is saved.
        (suffix) determines output format
    :param ylabel: str (default:"Percentage of total NAD")
        label for y-axis
    :param errorbars: bool (default: True)
        show y-errorbars
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

    if isinstance(data, str):
        df = analyse_rawfiles(data, show_intermediates=False)
    elif isinstance(data, list):
        dfs = []
        for g in data:
            dfs.append(analyse_rawfiles(g, show_intermediates=False))
        df = pd.concat(dfs)
    elif isinstance(data, DataFrame):
        df = data
    else:
        raise ValueError("data must be string or pandas Dataframe")

    if title:
        exp_name = title
    else:
        exp_name = "Newly synthesized NAD ± s.d."

    n = []

    for name, data in df.groupby("Exp"):
        try:
            color = multiplot[name]
        except (TypeError, KeyError):
            if not n:
                color = "black"
            else:
                raise ValueError(
                    f"multiplot has to be dict of colors for each experiment;"
                    f"\nMissing color for {name}"
                )

        # Get the number of samples by looking how often a index occurs
        n.append(data.groupby("Time in hours").count().iloc[1, 0])

        if errorbars:
            y_mean, y_std = calc_nad_mean(data)
            plt.errorbar(
                x=data.index.unique(),
                y=y_mean,
                yerr=y_std,
                label=f"{name}",
                color=color,
            )
        else:
            sns.lineplot(
                data=data,
                x=data.index,
                y="sum_labelled_percent",
                label=f"{name}",
                color=color,
            )

    ax.set_ylabel(ylabel)
    ax.set_xlabel("Time in hours")
    plt.title("{} (n={})".format(exp_name, n))

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


def calc_nad_mean(df, nad_measured_mean=None, nad_measured_std=None):
    """Calculates mean and standard deviation of labelled NAD

    Uses measured NAD amount or concentrations and standard deviation to
    calculate labelled NAD amount/ conc. and standard deviation
    :param df: pandas DataFrame
       Data needs "Time in hours" and "sum_labelled_percent"
    :param nad_measured_mean: float or None
        Measured NAD mean
    :param nad_measured_std: float or None
        Measured NAD standard deviation
    """
    ms_mean = np.array(df.groupby("Time in hours").mean()["sum_labelled_percent"]) / 100
    ms_std = np.array(df.groupby("Time in hours").std()["sum_labelled_percent"]) / 100
    # Calculate mean and std with error propagation
    if nad_measured_mean:
        nad_mean = nad_measured_mean * ms_mean
        if nad_measured_std:
            nad_std = nad_mean * np.sqrt(
                (nad_measured_std / nad_measured_mean) ** 2 + (ms_std / ms_mean) ** 2
            )
        else:
            nad_std = nad_mean * ms_std
    else:
        nad_mean = ms_mean * 100
        nad_std = ms_std * 100
    return nad_mean, nad_std
