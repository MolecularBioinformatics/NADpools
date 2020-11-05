import os
import numpy as np
import math
from statistics import median
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit

from convert_csv import analyse_rawfiles


def func_exp_decay(x, prefactor, exp_factor):
    """Generate exponential function values

    Generates exponential decaying function values from input values
    Function aproaches 0 asymptotically towards Inf
    :param x: float or list of floats
        Input values
    :param prefactor: float
        Prefactor of exponential equation
    :param exp_factor float
        Exponential factor
    :return: float or list of floats
        Function values of exponential function
    """
    return prefactor * np.exp(-exp_factor * x)


def func_exp_growth(x, prefactor, exp_factor):
    """Generate exponential function values

    Generates exponential growing function values from input values
    Function aproches 1 asymptotically towards Inf
    :param x: float or list of floats
        Input values
    :param prefactor: float
        Prefactor of exponential equation
    :param exp_factor_factor: float
        Exponential factor
    :return: float or list of floats
        Function values of exponential function
    """
    return -prefactor * np.exp(-exp_factor * x) + 1


def func_decay_cell(
    x,
    exp_factor_cyto,
    prefac_cyto,
    exp_factor_mito,
    prefac_mito,
    nad_amount_cyto,
    nad_amount_mito,
):
    """Exponential decaying function with cyto and mito part

    Generates exponential decaying function values from input values
    Sum of two exponential functions for cytosolic and mitochondrial part
    Function aproaches 0 asymptotically towards Inf
    :param x: float or list of floats
        Input values (time)
    :param exp_factor_cyto: float
        Exponential factor for cytosolic part
    :param prefac_cyto: float
        Prefactor of exponential equation for cytosolic part
    :param exp_factor_mito: float
        Exponential factor for mito part
    :param prefac_mito: float
        Prefactor of exponential equation for mito part
    :param nad_amount_cyto: float
        NAD amount used as additonal prefactor for cyto part
    :param nad_amount_mito: float
        NAD amount used as additonal prefactor for mito part
    :return: float or list of floats
        Function values of exponential function
    """
    mito_term = prefac_mito * nad_amount_mito * np.exp(-exp_factor_mito * x)
    cyto_term = prefac_cyto * nad_amount_cyto * np.exp(-exp_factor_cyto * x)
    return cyto_term + mito_term


def fit_unlabelled(df, plot_label=None):
    """Fit exponential decaying function parameters

    Fit exponential decaying function parameters to measured
    percentages of unlabelled isotopologue
    :param df: pandas DataFrame
        Dataset of merged experiments to be used for fit
    :param plot_label: str, default: None
        Plots data points and fitted curve
        with plot_label as legend
    :return: list of floats
        Prefactor and exponential factor
    """
    func = func_exp_decay
    xdata = df.index
    ydata = df["no_label_percent"] / 100
    bounds = ([0, 0], [1000, 10])
    start_values = [1, 1]

    popt, pcov = curve_fit(func, xdata, ydata, bounds=bounds, p0=start_values)
    if plot_label:
        sol_x = np.arange(0, 50, 0.1)
        sol_y = func(sol_x, popt[0], popt[1])
        sns.lineplot(x=sol_x, y=sol_y, label=f"{plot_label}-Fit")
        sns.scatterplot(x=xdata, y=ydata, label=f"{plot_label}-Measurements")

    return popt, pcov


def fit_sum_labelled(df, plot=False):
    """Fit exponential growing function parameters

    Fit exponential decaying function parameters to measured
    percentages of sum of labelled isotopologues
    :param df: pandas DataFrame
        Dataset of merged experiments to be used for fit
    :param plot: Boolean, default: False
        Plots data points and fitted curve
    :return: list of floats
        Prefactor and exponential factor
    """
    func = func_exp_growth
    xdata = df.index
    ydata = df["sum_labelled_percent"] / 100
    # lower and upper bounds of variables
    bounds = ([0, 0], [10, 10])
    start_values = [1, 1]

    popt, pcov = curve_fit(func, xdata, ydata, bounds=bounds, p0=start_values)
    if plot:
        sol_x = np.arange(0, 50, 0.1)
        sol_y = func(sol_x, popt[0], popt[1])
        sns.lineplot(x=sol_x, y=sol_y, label="Fit", color="red")
        sns.scatterplot(x=xdata, y=ydata, label="Measurements", color="red")

    return popt, pcov


def fit_cyto(
    df,
    nad_amount_cyto,
    nad_amount_mito,
    exp_factor_mito,
    prefac_mito,
    # std_mito=None,
    plot_label=None,
):
    """Fit cyto parameters of cell decaying equation

    Fit prefactor and exponential factor of sum of two exponetnial
    functions to measured percentages of unlabelled isotopologue
    for whole cell lysate experiments
    :param df: pandas DataFrame
        DataFrame with wcl experiment data
    :param nad_amount_cyto: float
        NAD amount used as additonal prefactor for cyto part
    :param nad_amount_mito: float
        NAD amount used as additonal prefactor for mito part
    :param exp_factor_mito: float
        Exponential factor for mito part
    :param prefac_mito: float
        Prefactor of exponential equation for mito part
    :param plot_label: str, default: None
        Plots data points and fitted curve
        with plot_label as legend
    :return: list of floats
        Prefactor and exponential factor
    """
    nad_amount_cell = nad_amount_cyto + nad_amount_mito
    func = func_decay_cell
    xdata = df.index
    ydata = df["no_label_percent"] / 100 * nad_amount_cell
    bounds = ([0, 0], [10, 10])
    start_values = [0.1, 1]

    popt, pcov = curve_fit(
        lambda x, exp_factor_cyto, prefac_cyto: func(
            x,
            exp_factor_cyto,
            prefac_cyto,
            exp_factor_mito,
            prefac_mito,
            nad_amount_cyto,
            nad_amount_mito,
        ),
        xdata,
        ydata,
        bounds=bounds,
        p0=start_values,
    )
    if plot_label:
        sol_x = np.arange(0, 50, 0.1)
        sol_y = func(
            sol_x,
            popt[0],
            popt[1],
            exp_factor_mito,
            prefac_mito,
            nad_amount_cyto,
            nad_amount_mito,
        )
        # Calculate back to percentage
        sol_y = sol_y / nad_amount_cell
        sns.lineplot(x=sol_x, y=sol_y, label=f"{plot_label}-Fit", color="red")
        sns.scatterplot(
            x=xdata,
            y=ydata / nad_amount_cell,
            label=f"{plot_label}-Measurements",
            color="red",
        )
    return popt, pcov


def fit_cyto_mito(
    df, glob_wcl, glob_mito, nad_amount_cyto, nad_amount_mito, plot=False
):
    """Fit parameters of cell decaying equation

    Fit prefactor and exponential factor of sum of two exponetnial
    functions to measured percentages of unlabelled isotopologue
    for whole cell lysate with additonal mitochondria only experiments
    :param df: pandas DataFrame
        DataFrame with wcl and mito experiment data
    :param glob_wcl: str
        RegEx to select WCL experiments in "Exp" column
    :param glob_mito: str
        RegEx to select mito experiments in "Exp" column
    :param nad_amount_cyto: float
        NAD amount used as additonal prefactor for cyto part
    :param nad_amount_mito: float
        NAD amount used as additonal prefactor for mito part
    :param plot: Boolean (default: False)
        Plots data points and fitted curve
    :return: list of floats
        exponential factors of cyto and mito part and
        prefactors of cyto and mito
    """
    plot_mito = "Mito" if plot else False
    plot_cyto = "Cell" if plot else False

    df_cyto = df.groupby("Exp").get_group(glob_wcl)
    df_mito = df.groupby("Exp").get_group(glob_mito)

    solution_mito, pcov_mito = fit_unlabelled(df_mito, plot_label=plot_mito)
    prefac_mito, exp_factor_mito = solution_mito
    std_error_mito = np.sqrt(np.diag(pcov_mito))
    std_prefac_mito, std_exp_factor_mito = std_error_mito

    solution_cyto, pcov_cyto = fit_cyto(
        df_cyto,
        nad_amount_cyto,
        nad_amount_mito,
        exp_factor_mito,
        prefac_mito,
        plot_label=plot_cyto,
    )
    exp_factor_cyto, prefac_cyto = solution_cyto
    std_error_cyto = np.sqrt(np.diag(pcov_cyto))
    std_exp_factor_cyto, std_prefac_cyto = std_error_cyto
    return (
        (exp_factor_cyto, exp_factor_mito, prefac_cyto, prefac_mito),
        (std_exp_factor_cyto, std_exp_factor_mito, std_prefac_cyto, std_prefac_mito),
    )


def estimate_half_life(df, pretty_print=False, show_factors=False):
    """Calculate half life time of unlabelled isotopologue

    Calculate half life time and standard deviation of unlabelled isotopologue
    using curve_fitting approach
    :param df: pandas DataFrame
        Dataset of merged experiments to be used for estimation
    :param pretty_print: bool (default: False)
        Whether to return half_life and standard_deviation as formatted string
    :param show_factors: bool (default: False)
        Return (pre-)factor of optimized exponential function
    :return: list of float
        Half-life(, pre-/factors) and standard deviation
    """
    solution, error = fit_sum_labelled(df)
    prefactor, exp_factor = solution
    half_life = calc_half_life(prefactor, exp_factor)
    sd_half_life = calc_half_life_standard_deviation(prefactor, exp_factor, error)
    if pretty_print:
        hl = [pretty_print_time(half_life), pretty_print_time(sd_half_life)]
    else:
        hl = [half_life, sd_half_life]
    if show_factors:
        sd_error = np.sqrt(np.diag(error))
        hl.extend([prefactor, sd_error[0], exp_factor, sd_error[1]])
    return hl


def estimate_half_life_cyto_mito(
    df,
    glob_wcl,
    glob_mito,
    nad_amount_cyto,
    nad_amount_mito,
    plot=False,
    pretty_print=False,
    show_factors=False,
):
    """Calculate half life time of cyto and mito NAD pool

    Calculate half life time and standard deviation of unlabelled isotopologue
    with curve_fitting approach
    Two part process: First mito part is estimated with mito experimental data
    Secondly cytosolic part with whole cell experiments
    :param df: pandas DataFrame
        DataFrame with wcl and mito experiment data
    :param glob_wcl: str
        RegEx to select WCL experiments in "Exp" column
    :param glob_mito: str
        RegEx to select mito experiments in "Exp" column
    :param nad_amount_cyto: float
        NAD amount used as additonal prefactor for cyto part
    :param nad_amount_mito: float
        NAD amount used as additonal prefactor for mito part
    :param plot: Boolean (default: False)
        Plots data points and fitted curve
    :param pretty_print: bool (default: False)
        Whether to return half_life and standard_deviation as formatted string
    :return: list of float
        Half-life(, prefactors) and standard deviation
    """
    solution, std = fit_cyto_mito(
        df, glob_wcl, glob_mito, nad_amount_cyto, nad_amount_mito, plot
    )
    exp_factor_cyto, exp_factor_mito, prefac_cyto, prefac_mito = solution
    std_exp_factor_cyto, std_exp_factor_mito, std_prefac_cyto, std_prefac_mito = std
    half_life_cyto = calc_half_life(prefac_cyto, exp_factor_cyto)
    half_life_mito = calc_half_life(prefac_mito, exp_factor_mito)
    # calc_half_life_standard_deviation(prefactor, exp_factor, error)
    if pretty_print:
        hl = [
            pretty_print_time(half_life_cyto),
            pretty_print_time(half_life_mito),
        ]  # pretty_print_time(sd_half_life)]
    else:
        hl = [half_life_cyto, half_life_mito]
    if show_factors:
        # sd_error = np.sqrt(np.diag(error))
        hl.extend([exp_factor_cyto, exp_factor_mito, prefac_cyto, prefac_mito])
        hl.extend(
            [std_exp_factor_cyto, std_exp_factor_mito, std_prefac_cyto, std_prefac_mito]
        )
    return hl


def pretty_print_time(time):
    """Return time as string with (days,) hours, minutes

    Takes float of time and return formatted string
    with (days,) hours, minutes
    :param time: float
        Time in hours
    :return: string
    """
    frac, whole = math.modf(time)
    whole = int(whole)
    frac = round(frac * 60)
    if whole == 0:
        return "{}min".format(frac)
    elif whole < 24:
        return "{}h {}min".format(whole, frac)
    else:
        days = int(whole / 24)
        hours = whole % 24
        return "{}d {}h {}min".format(days, hours, frac)


def calc_half_life(prefactor, exp_factor):
    """Calculate half-life time from factors

    Calculate half-life time from prefactor and exponetial factor
    :param prefactor: float
        Prefactor of exponential equation
    :param exp_factor_factor: float
        Exponential factor
    :return: float
        half-life time
    """
    return np.log(2 * prefactor) / exp_factor


def calc_half_life_standard_deviation(prefactor, exp_factor, cov):
    """Calculate standard deviation of half life

    Calculate sd of half time based on partial derivative
    :param prefactor: float
        Prefactor of fit function
    :param exp_factor: float
        Exponential factor of fit function
    :param cov: list of list of floats
        Matrix of covariances of fit parameters
    """
    # Calculate one standard deviation of prefactor and exp_factor
    sd_prefactor, sd_exp_factor = np.sqrt(np.diag(cov))
    prefac_term = (sd_prefactor / (prefactor * exp_factor)) ** 2
    exp_term = (np.log(2 * prefactor) * sd_exp_factor / exp_factor ** 2) ** 2
    sd_half_life = np.sqrt(prefac_term + exp_term)
    return sd_half_life


def half_life_resampling(
    df, nruns=200, show_factors=True, pretty_print=False, **resampl_kw
):
    """Resample half_life time estimation

    Subsample df nruns times and estimate half_life time
    Each timepoint is resampled individually
    :param df: pandas DataFrame
        Resampling over "Time in hours" column
    :param nruns: int (default: 200)
        number of resample runs
    :param show_factors: bool (default: True)
        Return (pre-)factor of optimized exponential function
    :param pretty_print: bool (default: True)
        Whether to return half_life and standard_deviation as formatted string
        :param **resampl_kw: (default: frac=0.5, replace=False)
        keyword arguments for pandas sample function
        e.g. frac, replace, n
    :return: tuple of float or str
        half_life mean and std, (prefactor, exp-factor with stds)
    """
    if not resampl_kw:
        resampl_kw = {
            "frac": 0.5,
            "replace": False,
        }
    results = []
    for _ in range(nruns):
        dfs = []
        for _, data in df.groupby("Time in hours"):
            df_sample = data.sample(**resampl_kw)
            dfs.append(df_sample)
        df_subsampled = pd.concat(dfs)
        res = estimate_half_life(df_subsampled, show_factors=show_factors)
        results.append(res)
    results = pd.DataFrame(results)
    if pretty_print:
        hl = [pretty_print_time(results[0].mean())]
        hl.append(pretty_print_time(results[0].std()))
    else:
        hl = [results[0].mean(), results[0].std()]
    if show_factors:
        hl.append(results[2].mean())  # prefac mean
        hl.append(results[2].std())  # prefac std
        hl.append(results[4].mean())  # exp fac mean
        hl.append(results[4].std())  # exp fac std
    return hl


def plot_fit(name, df, prefactor, exp_factor, outfolder=None):
    """Plot fit graph and save it.

    Create plot of fit and measurements and save them to outfolder/name.
    :param name: str
        Dataset name sued for outputfile
    :param df: pandas DataFrame
        Measurements
    :param prefactor: float
        Prefactor of exponential function
    :param exp_factor: float
        Exponential factor
    :param outfolder: str or Path (default:None)
        Folder to save plots to
    """
    # Style options
    scattersize = 15
    dimensions = (5, 5)  # Dimensions of plot in inch
    fig, ax = plt.subplots(figsize=dimensions)
    sns.set_context("paper", font_scale=1.5, rc={"lines.linewidth": 1})
    sns.set_style("ticks")

    fit_x = np.arange(0, 50, 0.1)
    fit_y = func_exp_decay(fit_x, prefactor, exp_factor) * 100
    sns.lineplot(x=fit_x, y=fit_y, label=f"{name}-Fit", color="black", ax=ax)
    sns.scatterplot(
        x=df.index,
        y=df["no_label_percent"],
        label=f"{name}-Measurements",
        s=scattersize,
        linewidth=0,
        color="black",
        ax=ax,
    )
    ax.set_ylabel("Percentage of unlabelled NAD")
    fig.tight_layout()
    if outfolder:
        folder = Path(outfolder)
        folder.mkdir(exist_ok=True)
        outpath = folder / (name + ".pdf")
        fig.savefig(outpath)
        print("Saving ", outpath)
    plt.show()


def calc_half_life_table(
    input_data,
    cyto_mito=None,
    resample=False,
    show_factors=False,
    input_suffix=None,
    input_folder=None,
    pretty_print=True,
    plot_fit_graphs=False,
    graphs_outfolder=None,
    outputfile=None,
):
    """Calculate table of half life times and SDs.

    Takes list of globs and calculates for each hit half life and standard deviation.
    :param input_data: list of str or pandas DataFrame
        Regex of experiments to be pooled for calculation
        or DataFrame containing data
    :param cyto_mito: dict of list (default: None)
        Perform separate determinations for cyto and mito pool.
        arbitrary name as keys
        List as item: glob_wcl, glob_mito, nad_amount_cyto, nad_amount_mito
    :param resample: bool or dict (default: False)
        Resample half_life estimation;
        dict can contain arguments to half_life_resampling
    :param show_factors: bool (default: False)
        Displays columns with fitted prefactors
    :param input_suffix: str (default: None)
        Suffix to be added to each glob in list
    :param input_folder: str (default: None)
        Folder path to be added as prefix to globs in list
    :param pretty_print: bool (default: True)
        Whether to return half_life and standard_deviation as formatted string
    :param plot_fit: Boolean (default: False)
        Plot figures of fit vs measurements
    :param graphs_outfolder: str or Path (default: None)
       Folder to save fit plots to
    :param outputfile: str (default: None)
        Path to outputfile
    :return: pandas DataFrame
        Table with half-life, (prefactors)  and standard deviations
    """
    dfs = []
    if isinstance(input_data, list):
        glob_list = input_data
        for glob in glob_list:
            if input_suffix:
                glob = glob + input_suffix
            if input_folder:
                glob = os.path.join(input_folder, glob)
            dfs.append(analyse_rawfiles(glob))
        df = pd.concat(dfs)
    elif isinstance(input_data, pd.DataFrame):
        df = input_data
    else:
        raise TypeError("input should be list of str(filepath or glob) or DataFrame")

    half_life = {}
    # separate determination of cyto and mito part
    if cyto_mito:
        if resample:
            raise NotImplementedError(
                "resampling doesn't work for cyto_mito half_life estimation"
            )
        for name, factors in cyto_mito.items():
            glob_wcl, glob_mito, nad_amount_cyto, nad_amount_mito = factors
            results = estimate_half_life_cyto_mito(
                df,
                glob_wcl,
                glob_mito,
                nad_amount_cyto,
                nad_amount_mito,
                pretty_print=pretty_print,
                show_factors=show_factors,
            )
            half_life[name] = results
            if show_factors:
                turnover = calc_gradient_zero_cyto_mito(
                    results, nad_amount_cyto, nad_amount_mito
                )
                half_life[name].extend(turnover)
                half_life[name].extend([nad_amount_cyto, nad_amount_mito])
        if show_factors:
            columns = [
                "half_life_time_cyto",
                "half_life_time_mito",
                "exp_prefactor_cyto",
                "exp_prefactor_mito",
                "prefactor_cyto",
                "prefactor_mito",
                "std_exp_factor_cyto",
                "std_exp_factor_mito",
                "std_prefactor_cyto",
                "std_prefactor_mito",
                "cell_gradient_at_0h",
                "cyto_gradient_at_0h",
                "mito_gradient_at_0h",
                "std_cell_gradient_at_0h",
                "std_cyto_gradient_at_0h",
                "std_mito_gradient_at_0h",
                "nad_amount_cyto",
                "nad_amount_mito",
            ]
        else:
            columns = ["half_life_time_cyto", "half_life_time_mito"]
    # just single rate determination
    else:
        for name, data in df.groupby("Exp"):
            n_samples = median(
                [list(data.index).count(x) for x in list(data.index.unique())]
            )
            if resample:
                resample_kw = resample if resample is not True else {}
                half_life[name] = half_life_resampling(
                    data,
                    show_factors=show_factors,
                    pretty_print=pretty_print,
                    **resample_kw,
                )
            else:
                half_life[name] = estimate_half_life(data, pretty_print, show_factors)

            half_life[name].append(n_samples)
            if plot_fit_graphs and show_factors:
                plot_fit(
                    name, data, half_life[name][2], half_life[name][4], graphs_outfolder
                )
            elif plot_fit_graphs and not show_factors:
                raise ValueError(
                    "'plot_fit_graphs' requires 'show_factors' set to  True"
                )
        if show_factors:
            columns = [
                "half_life_time",
                "standard_deviation",
                "prefactor",
                "std_prefactor",
                "exp_prefactor",
                "std_exp_factor",
                "n_samples",
            ]
        else:
            columns = ["half_life_time", "standard_deviation", "n_samples"]
    half_life = pd.DataFrame.from_dict(half_life, orient="index", columns=columns,)
    if outputfile:
        print(f"Saving {outputfile}")
        half_life.to_csv(outputfile, sep=",")
    return half_life


def calc_turnover_cyto_mito(factors, nad_amount_cyto, nad_amount_mito):
    """Calculate cell and mito turnover after one hour.

    Calculate from pre and exponential factors the NAD turnover after 1 hour.
    :param factors: list of float
        return list of estimate_half_life_cyto_mito function
    :param nad_amount_cyto: float
        NAD amount used as additonal prefactor for cyto part
    :param nad_amount_mito: float
        NAD amount used as additonal prefactor for mito part
    :return: float, float
        turnover_cell, turnover_cyto, turnover_mito
    """
    t = 1
    exp_factor_cyto = factors[2]
    exp_factor_mito = factors[3]
    prefac_cyto = factors[4]
    prefac_mito = factors[5]

    conc_cell = func_decay_cell(
        t,
        exp_factor_cyto,
        prefac_cyto,
        exp_factor_mito,
        prefac_mito,
        nad_amount_cyto,
        nad_amount_mito,
    )
    turnover_cell = (nad_amount_cyto + nad_amount_mito) - conc_cell

    conc_cyto = func_exp_decay(t, prefac_cyto, exp_factor_cyto)
    turnover_cyto = nad_amount_cyto * (1 - conc_cyto)

    conc_mito = func_exp_decay(t, prefac_mito, exp_factor_mito)
    turnover_mito = nad_amount_mito * (1 - conc_mito)
    return turnover_cell, turnover_cyto, turnover_mito


def calc_turnover_cell(prefactor, exp_factor, nad_amount_cell):
    """Calculate cell turnover after one hour.

    Calculate from pre and exponential factors the NAD turnover after 1 hour.
    :param prefactor: float
        Prefactor of exponential function
    :param exp_factor: float
        Exponential factor of exponential function
    :param nad_amount_cell: float
        NAD amount of cell
    :return: float
        turnover_cell
    """
    t = 1  # time point to determine flux

    nad_amount_1h = func_exp_decay(t, prefactor, exp_factor,) * nad_amount_cell
    turnover_cell = nad_amount_cell - nad_amount_1h
    return turnover_cell


def calc_gradient_zero_cell(
    prefactor,
    prefactor_std,
    exp_factor,
    exp_factor_std,
    nad_amount_cell,
    nad_amount_cell_std,
):
    """Calculate absolute gradient at timepoint zero.

    Calculate from pre and exponential factors the first derivative
    and standard deviation at t0.
    f'(0) =  |prefac * exp_fac * NAD conc|
    :param prefactor: float
        Prefactor of exponential function
    :param exp_factor: float
        Exponential factor of exponential function
    :param nad_amount_cell: float
        NAD amount of cell
    :return: tuple of floats
        Gradient and std
    """
    gradient = prefactor * exp_factor * nad_amount_cell
    gradient_var = _calc_gradient_variance(
        prefactor,
        prefactor_std,
        exp_factor,
        exp_factor_std,
        nad_amount_cell,
        nad_amount_cell_std,
    )
    gradient_std = math.sqrt(gradient_var)
    return gradient, gradient_std


def calc_gradient_zero_cyto_mito(factors, nad_amount_cyto, nad_amount_mito):
    """Calculate absolute gradients of cell and mito at timepoint zero.

    Calculate from pre and exponential factors the first derivative
    at t0 for cell and mitos seperately.
    f'(0) =  |prefac * exp_fac * NAD conc|
    :param factors: list of float
        return list of estimate_half_life_cyto_mito function
    :param nad_amount_cyto: float
        NAD amount of cytosol
    :param nad_amount_mito: float
        NAD amount of mitochondria
    :return: tuple of floats
        gradient_cell,
        gradient_cyto,
        gradient_mito,
        gradient_std_cell,
        gradient_std_cyto,
        gradient_std_mito,
    """
    exp_factor_cyto = factors[2]
    exp_factor_mito = factors[3]
    prefactor_cyto = factors[4]
    prefactor_mito = factors[5]
    std_exp_factor_cyto = factors[6]
    std_exp_factor_mito = factors[7]
    std_prefac_cyto = factors[8]
    std_prefac_mito = factors[9]

    gradient_cyto = prefactor_cyto * exp_factor_cyto * nad_amount_cyto
    gradient_mito = prefactor_mito * exp_factor_mito * nad_amount_mito
    gradient_cell = gradient_cyto + gradient_mito
    gradient_var_cyto = _calc_gradient_variance(
        prefactor_cyto,
        std_prefac_cyto,
        exp_factor_cyto,
        std_exp_factor_cyto,
        nad_amount_cyto,
        # nad_amount_std_cyto,
    )
    gradient_std_cyto = math.sqrt(gradient_var_cyto)
    gradient_var_mito = _calc_gradient_variance(
        prefactor_mito,
        std_prefac_mito,
        exp_factor_mito,
        std_exp_factor_mito,
        nad_amount_mito,
        # nad_amount_std_mito,
    )
    gradient_std_mito = math.sqrt(gradient_var_mito)
    gradient_std_cell = math.sqrt(gradient_var_cyto + gradient_var_mito)

    return (
        gradient_cell,
        gradient_cyto,
        gradient_mito,
        gradient_std_cell,
        gradient_std_cyto,
        gradient_std_mito,
    )


def _calc_gradient_variance(
    prefactor,
    prefactor_std,
    exp_factor,
    exp_factor_std,
    nad_amount_cell,
    nad_amount_cell_std=1,
):
    """Calc variance for gradient at t=0"""
    gradient_var = (prefactor_std / prefactor) ** 2
    gradient_var += (exp_factor_std / exp_factor) ** 2
    gradient_var += (nad_amount_cell_std / nad_amount_cell) ** 2
    return gradient_var
