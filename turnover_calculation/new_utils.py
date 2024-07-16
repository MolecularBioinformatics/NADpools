import itertools
import scipy.stats as stats
from scipy.optimize import curve_fit
import numpy as np
import pandas as pd
import picor
import math

import os
import matplotlib.pyplot as plt
import new_plots as nplt


def exponential_decay(x, a, b):
    """
    Exponential decay function

    Args:
        x (float): time
        a (float): amplitude
        b (float): decay rate

    Returns:
        float: exponential decay
    """
    return a * np.exp(-b * x)


def exponential_growth(x, a, b):
    """
    Exponential growth function

    Args:
        x (float): time
        a (float): amplitude
        b (float): growth rate

    Returns:
        float: exponential growth
    """
    return a * np.exp(b * x)


def calculate_standard_error(pcov):
    """
    Calculate standard error

    Args:
        pcov (_type_): _description_

    Returns:
        _type_: _description_
    """
    std_err = np.sqrt(np.diag(pcov))
    return std_err


def half_life(popt, pcov, verbose=False):
    """
    Calculate half life

    Args:
        popt (tuple): fitted parameters
        pcov (np.array): covariance matrix
        verbose (bool, optional): _description_. Defaults to False.

    Returns:
        tuple: half life and standard error
    """
    half_life = np.log(2) / popt[1]
    half_life_error = half_life * \
        (np.sqrt((calculate_standard_error(pcov)[1]/popt[1])**2))
    if verbose:
        print(f'Half life: {pretty_print_time(half_life)}')
    return half_life, half_life_error


def growth_estimation(x, y, p0=[1, 0.1]):
    """
    Estimate growth parameters

    Args:
        x (list): x data
        y (list): y data
        p0 (list, optional): _description_. Defaults to [1, 0.1].

    Returns:    
        tuple: fitted parameters and standard error
    """
    popt, pcov = curve_fit(exponential_growth, x, y, p0=p0, maxfev=10000)
    std_err = calculate_standard_error(pcov)
    return popt, std_err


def get_fitted_growth(data, xcol, popt):
    """
    Get fitted growth

    Args:
        data (pd.DataFrame): data
        xcol (str): x column
        popt (tuple): fitted parameters

    Returns:
        list: fitted growth data
    """
    x = np.linspace(data[xcol].min(), data[xcol].max(), 100)
    fitted = exponential_growth(x, *popt)
    return fitted


def fit_exponential_decay(x, y, verbose=False):
    '''
    Fits exponential decay to data
    :param x: pandas series
        x data  (time)
    :param y: pandas series
        y data (NAD+)
    :param verbose: bool
        print fitted parameters
    :return: tuple
        fitted parameters
    '''
    bounds = ([0, 0], [1000, 10])
    popt, pcov = curve_fit(exponential_decay, x, y, p0=(1, 1), bounds=bounds)
    if verbose:
        print(f'Fitted parameters: {popt}')
    return popt, pcov


def get_fitted_decay(data, xcol, popt):
    """
    Get fitted decay

    Args:
        data (pd.DataFrame): data
        xcol (str): x column
        popt (tuple): fitted parameters

    Returns:
        list: fitted decay data
    """
    x = np.linspace(data[xcol].min(), data[xcol].max(), 100)
    fitted = exponential_decay(x, *popt)
    return fitted


def get_specific_columns(df, met, columns=['cell type', 'time', 'replicate number']):
    """
    Get specific columns from a dataframe

    Args:
        df (DataFrame): data extracted from excel file
        met (str): metabolite of interest
        columns (list, optional): Specified list of columns. Defaults to ['cell type', 'time', 'replicate number'].

    Returns:
        DataFrame: Dataframe with specified columns
    """
    df_specific = df[df.columns.intersection(columns)]
    _df = df[[i for i in df.columns if i.split('_')[0] == met]]
    df_specific = pd.concat((df_specific, _df), axis=1)
    return df_specific


def get_pool_corrected(iso_corr_percent, nad_conc, met='NAD'):
    """
    Get pool corrected data

    Args:
        iso_corr_percent (pd.DataFrame): isotopologue corrected data
        nad_conc (pd.DataFrame): NAD concentration data
        met (str, optional): _description_. Defaults to 'NAD'.

    Returns:
        pd.DataFrame: Pool corrected data
    """
    df_sum_labelled = pd.DataFrame()
    for cell in iso_corr_percent['cell type'].unique():
        _df = iso_corr_percent[iso_corr_percent['cell type'] == cell]
        try:
            _df['pool_corr'] = _df['sum labelled'].mul(
                nad_conc[nad_conc.index == cell]['mean'].iloc[0]/100)
            _df['pool_corr_sd'] = _df['sum labelled'].mul(
                nad_conc[nad_conc.index == cell]['sd'].iloc[0]/100)
            _df['pool_corr_unlabelled'] = _df[met].mul(
                nad_conc[nad_conc.index == cell]['mean'].iloc[0]/100)
            _df['pool_corr_unlabelled_sd'] = _df[met].mul(
                nad_conc[nad_conc.index == cell]['sd'].iloc[0]/100)

        except IndexError:
            _df['pool_corr'] = _df['sum labelled'].mul(
                nad_conc[nad_conc.index == 'wt']['mean'].iloc[0]/100)
            _df['pool_corr_sd'] = _df['sum labelled'].mul(
                nad_conc[nad_conc.index == 'wt']['sd'].iloc[0]/100)
            _df['pool_corr_unlabelled'] = _df[met].mul(
                nad_conc[nad_conc.index == 'wt']['mean'].iloc[0]/100)
            _df['pool_corr_unlabelled_sd'] = _df[met].mul(
                nad_conc[nad_conc.index == 'wt']['sd'].iloc[0]/100)

        df_sum_labelled = pd.concat(
            (df_sum_labelled, _df), axis=0)
    return df_sum_labelled


def extract_data_from_xls(data, xl, sample_identity, column="Area", verbose=False):
    """
    Extract data from excel file

    Args:
        data (_type_): _description_
        xl (_type_): _description_
        sample_identity (_type_): _description_
        column (_type_, optional): _description_. Defaults to "Area".
        verbose (bool, optional): _description_. Defaults to False.

    Returns:
        pd.DataFrame: Dataframe with extracted data
    """
    if verbose:
        print("extracting data...")
    df = pd.DataFrame()
    for sheet in xl.sheet_names:
        try:
            _df = pd.read_excel(data, sheet_name=sheet,
                                skiprows=4, index_col=0)
            fname = list(set(sample_identity.index.astype('str'))
                         & set(_df.index.astype('str')))
            df = pd.concat((df, _df[_df.index.isin(fname)][column]), axis=1)
            df = df.rename(columns={df.columns[-1]: sheet})
        except KeyError:
            if verbose:
                print(f"\tInvalid format: skipping sheet {sheet}")

        except ValueError:
            if verbose:
                print(f"\tInvalid format: skipping sheet {sheet}")

    df.index = df.index.astype('int')
    df = df.replace("NF", 0.)
    return df


def transform_percent(df, list_of_mets):
    """
    Transform raw data to percentage

    Args:
        df (pd.DataFrame): isotopologue data
        list_of_mets (list): list of metabolites

    Returns:
        pd.DataFrame: Dataframe with raw data converted to percentage
    """
    df_percent = pd.DataFrame()
    for met in list_of_mets:
        _df = df[[i for i in df.columns if i.split('_')[0] == met]]
        _df = _df.div(_df.sum(axis=1), axis=0).mul(100, axis=0)
        df_percent = pd.concat((df_percent, _df), axis=1)
    return df_percent.replace(np.nan, 0.0)


def split_column_into_multiple_columns(df, column, separator, new_column_names):
    df = df.copy()
    df = df[column].str.split(separator, expand=True)
    df.columns = new_column_names
    return df


def add_time_column(df, column):
    df = df.copy()
    df['time'] = df[column].str.split(' ')
    df['time'] = df['time'].apply(lambda x: x[-1])
    return df


def add_cell_type_column(df, column):
    df = df.copy()
    df['cell type'] = df[column].str.split(' ')
    df['cell type'] = df['cell type'].apply(
        lambda x: ' '.join(x[:x.index('Cell')]))
    return df


def add_replicate_column(df, column):
    df = df.copy()
    df['replicate number'] = df[column].str.split('#')
    df['replicate number'] = df['replicate number'].apply(lambda x: x[-1])
    return df


def exclude_sheet_names(xl, exclude_cols=['sample identity', 'Component', 'Sheet1', 'Sheet2', 'NUCLEOTIDES']):
    return list(set([i.split("_")[0] for i in xl.sheet_names if i not in exclude_cols]))


def read_data(data, **kwargs):
    experiment = data.split('/')[-1].split('.')[0]
    print(f'Reading {experiment}...')
    try:
        sample_identity = pd.read_excel(data, sheet_name='sample identity')
    except ValueError:
        sample_identity = pd.read_excel(
            data, sheet_name=kwargs.get('sheet_name', 'Sheet1'))

    if 'Sample #' in sample_identity.columns:
        sample_identity = sample_identity.set_index('Sample #')

    if 'Sample' in sample_identity.columns:
        sample_identity = split_column_into_multiple_columns(
            sample_identity, 'Sample', ',', ['Sample', 'replicate', 'date'])
        sample_identity = add_time_column(sample_identity, 'Sample')
        sample_identity = add_cell_type_column(sample_identity, 'Sample')
        sample_identity = add_replicate_column(sample_identity, 'replicate')

    if 'time' not in sample_identity.columns:
        sample_identity['time'] = sample_identity['time point']

    try:
        sample_identity['time'] = sample_identity['time'].str.strip(
            '(h)').astype('float')
    except AttributeError:
        pass

    if 'cell lysate sample no' in sample_identity.columns:
        sample_identity = sample_identity.set_index('cell lysate sample no')

    xl = pd.ExcelFile(data)
    list_of_mets = exclude_sheet_names(xl)
    print(f'\tfound {list_of_mets}')
    return xl, sample_identity, list_of_mets, experiment


def process_data(data, xl, sample_identity, verbose=False, column="Area"):
    df = extract_data_from_xls(data=data, xl=xl, sample_identity=sample_identity,
                               column=column, verbose=verbose)
    df_processed = pd.concat((sample_identity, df), axis=1)
    return df_processed


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


def update_cell_type(iso_corr, cell_line):
    if cell_line == 'HeLa':
        cell_type_dict = {'HeLa wt': 'HeLa', 'HeLa mP': 'mP', 'HeLa pP': 'pP',
                          'HeLa cP': 'cP', 'HeLa erP': 'erP'}
    elif cell_line == 'U2OS':
        cell_type_dict = {'U2OS wt': 'U2OS', 'U2OS mP': 'mP', 'U2OS pP': 'pP',
                          'U2OS cP': 'cP', 'U2OS erP': 'erP'}
    elif cell_line == '293':
        cell_type_dict = {'CytoPARP': 'cP', 'mitoPARP': 'mP',
                          'pexPARP': 'pP', 'ER_PARP': 'erP', '293': '293'}
    iso_corr['cell type'] = iso_corr['cell type'].map(cell_type_dict)
    return iso_corr


def raw_to_percent(df, met):
    """
    Convert raw data to percentage

    Args:
        df (pd.DataFrame): isotopologue data
        met (str): metabolite of interest

    Returns:
        pd.DataFrame: Dataframe with raw data converted to percentage
    """
    cols = [i for i in df.columns if i.split('_')[0] == met]
    _df = df[cols]
    _df = _df.div(_df.sum(axis=1), axis=0).mul(100, axis=0)
    _df = pd.concat((df[df.columns.difference(cols)], _df), axis=1)
    return _df.replace(np.nan, 0.0)


def remove_low_values(df_raw1, met='NAD', threshold=0.1, columns=['cell type', 'time', 'replicate number']):
    df_raw_nad = get_specific_columns(df_raw1, met=met, columns=columns)
    list_of_mets = [i for i in df_raw_nad.columns if i.split('_')[0] == met]
    max_value = df_raw_nad[list_of_mets].max().max()
    df_raw_nad = df_raw_nad[df_raw_nad[list_of_mets].sum(
        axis=1) > threshold * max_value]
    return df_raw_nad


def get_growth_correction(iso_corr, list_of_mets, cell,
                          xcol='Time in minutes', cell_column='cell type'):
    """
    Get growth correction

    Args:
        iso_corr (pd.DataFrame): Isotopologue corrected data.
        list_of_mets (list): List of metabolites.
        cell (str): Cell line.
        xcol (str, optional): Column name. Defaults to 'Time in minutes'.
        cell_column (str, optional): Column name. Defaults to 'cell type'.

    Returns:
        pd.DataFrame: Growth corrected data.
    """
    # growth estimation
    data = iso_corr[iso_corr[cell_column] == cell]
    data = data[~(data[list_of_mets].sum(axis=1) == 0.0)]
    x = data[xcol]
    y = data[list_of_mets].sum(axis=1).div(
        data[data[xcol] == 0.0][list_of_mets].sum(axis=1).mean())
    popt, std_err = growth_estimation(x, y)

    # growth correction
    data = iso_corr[iso_corr[cell_column] == cell]
    data = data[~(data[list_of_mets].sum(axis=1) == 0.0)]
    labelled_cols = list_of_mets[1:]
    unlabelled_iso = data[data.columns.difference(labelled_cols)]
    growth_corrected_iso = data[labelled_cols].div(1 + (popt[1] * x), axis=0)
    iso_corr_nad1 = pd.concat((unlabelled_iso, growth_corrected_iso), axis=1)
    iso_corr_nad1['prefactor_growth'] = popt[0]
    iso_corr_nad1['growth_rate'] = popt[1]
    iso_corr_nad1['prefactor_growth_standard_error'] = std_err[0]
    iso_corr_nad1['growth_rate_standard_error'] = std_err[1]
    return iso_corr_nad1


def get_iso_corr(df_raw, met='NAD', threshold=0.1, cell_column='Cell line',
                 columns=None, transform=None, resolution=70000,
                 resolution_correction=True, growth_correction=False, xcol='time'):
    """
    Get isotopologue correction data

    Args:
        df_raw (pd.DataFrame): Isoptopologue raw data.
        met (str, optional): Name of the metabolite. Defaults to 'NAD'.
        threshold (float, optional): Threshold value. Defaults to 0.1.
        cell_column (str, optional): Name of the cell column. Defaults to 'Cell line'.
        columns (_type_, optional): Name of specific columns. Defaults to None.
        transform (_type_, optional): Should the data be transformed? Defaults to None.

    Returns:
        pd.DataFrame: Isotopologue correction data.
    """
    if columns is None:
        columns = ['Cell line', 'time', 'Triplicate#']
    iso_corr = pd.DataFrame()
    for cell in df_raw[cell_column].unique():
        list_of_mets = [i for i in df_raw.columns if i.split('_')[0] == met]
        df_raw_nad = remove_low_values(df_raw[df_raw[cell_column] == cell], met=met,
                                       threshold=threshold, columns=columns)
        exclude_cols = df_raw_nad.columns.difference(list_of_mets).to_list()
        _iso_corr = picor.calc_isotopologue_correction(raw_data=df_raw_nad, molecule_name=met,
                                                       resolution_correction=resolution_correction,
                                                       resolution=resolution,
                                                       exclude_col=exclude_cols)
        if growth_correction is True:
            _iso_corr = get_growth_correction(iso_corr=_iso_corr, list_of_mets=list_of_mets,
                                              cell=cell, xcol=xcol, cell_column=cell_column)
        if transform == 'percent':
            _iso_corr = raw_to_percent(_iso_corr, met)
        iso_corr = pd.concat((iso_corr, _iso_corr), axis=0)
    return iso_corr


def get_turnover(dpars, nad_conc, cell, cell_line='HeLa', growth_correction=True):
    hl = dpars[dpars['cell type'] == cell]['half_life'].iloc[0]
    hle = dpars[dpars['cell type'] == cell]['half_life_error'].iloc[0]
    if growth_correction == True:
        gr = dpars[dpars['cell type'] == cell]['growth_rate']
        gre = dpars[dpars['cell type'] == cell]['growth_rate_standard_error']

    if cell == cell_line:
        cell = 'wt'
    poolsize = nad_conc[nad_conc['cell type'] == cell]['mean'].iloc[0]
    poolsize_error = nad_conc[nad_conc['cell type'] == cell]['sd'].iloc[0]

    turnover = (poolsize/2) / hl
    if growth_correction == True:
        turnover_error = turnover * \
            (np.sqrt((poolsize_error/poolsize)**2 + (hle/hl)**2 + (gre/gr)**2))
    else:
        turnover_error = turnover * \
            (np.sqrt((poolsize_error/poolsize) ** 2 + (hle/hl)**2))

    if cell == 'wt':
        cell = cell_line
    dpars.loc[dpars['cell type'] == cell, 'poolsize'] = poolsize
    dpars.loc[dpars['cell type'] == cell, 'poolsize_sd'] = poolsize_error
    dpars.loc[dpars['cell type'] == cell, 'turnover'] = turnover
    dpars.loc[dpars['cell type'] == cell, 'turnover_error'] = turnover_error

    return dpars


def calculate_t_stats(dpars, n_samples):
    t_stat = {}
    comb = [i for i in itertools.combinations(dpars['cell type'].unique(), 2)]
    for cell in comb:
        numerator = dpars[dpars['cell type'] == cell[0]].turnover.iloc[0] - \
            dpars[dpars['cell type'] == cell[1]].turnover.iloc[0]
        deno = dpars[dpars['cell type'] == cell[0]].turnover_error.iloc[0] / \
            (np.sqrt(n_samples)) + dpars[dpars['cell type'] ==
                                         cell[1]].turnover_error.iloc[0]/(np.sqrt(n_samples))
        t_stat['_'.join(cell)] = np.abs(numerator/deno)
    df_stat = pd.DataFrame.from_dict(
        t_stat, orient='index', columns=['t-statistic'])
    df_stat['p-value'] = df_stat['t-statistic'].apply(
        lambda x: 2*(1 - stats.t.cdf(x, df=n_samples-1)))
    return df_stat


def get_filename_and_figtitle(cell_line, cell, growth_or_decay='growth'):
    """
    Get filename and figure title for the plots.

    Args:
        cell_line (str): Cell line name.
        cell (str): Cell line
        growth_or_decay (str, optional): Defaults to 'growth'.

    Returns:
        list: Figure title prefix and filename.
    """
    if cell == cell_line:
        figtitle_prefix = cell_line+' wt'
        filename = f'{growth_or_decay}_estimation_{cell_line}_wt.svg'
    else:
        if cell_line in cell:
            figtitle_prefix = cell
        else:
            figtitle_prefix = cell_line+' '+cell
        filename = f'{growth_or_decay}_estimation_{cell_line}_{cell}.svg'
    return figtitle_prefix, filename


def create_directory(path):
    """
    Create a directory if it does not exist.

    Args:
        path (str): Path to the directory.
    """
    os.makedirs(path, exist_ok=True)


def handle_data_saving(data, path, filename):
    """
    Save data to a file.

    Args:
        data (pd.DataFrame): Data to be saved.
        path (str): Path to the directory.
        filename (str): Name of the file.
    """
    create_directory(path)
    data.to_csv(path+filename, index=False)


def handle_figure(fig, path, filename, show_fig, save_fig):
    """
    Handle figure saving and showing.

    Args:
        fig (plt.Figure): Figure object.
        path (str): Path to the directory.
        filename (str): Name of the file.
        show_fig (bool): Flag to show the figure.
        save_fig (bool): Flag to save the figure.
    """
    if save_fig:
        create_directory(path)
        fig.savefig(path+filename, dpi=300, bbox_inches='tight')
    if not show_fig:
        plt.close(fig)


def estimate_growth_parameters(iso_corr, cell_line, list_of_mets, save_fig=False,
                               save_data=False, show_fig=True, xcol='time',
                               default_path='./publication/', file=None,
                               per_experiment=False, met='NAD', cell_column='cell type',
                               ylabel='Fraction of total NAD$^+$'):
    """
    Estimate growth parameters for the isotopologue corrected data.

    Args:
        iso_corr (pd.DataFrame): Isotopologue corrected data.
        cell_line (str): Cell line name.
        list_of_mets (list): List of metabolites.
        save_fig (bool, optional): Flag to control saving fitted plots. Defaults to True.
        save_data (bool, optional): Flag to control saving growth parameters. Defaults to True.
        show_fig (bool, optional): Flag to control showing the fitted plots. Defaults to False.
        xcol (str, optional): Column name for x-axis. Defaults to 'time'.
        default_path (str, optional): Path to save the data and figures. Defaults to './publication/'.
        file (str, optional): File name. Defaults to None.
        per_experiment (bool, optional): Flag to save data and figures per experiment. Defaults to False.
        met (str, optional): Metabolite name. Defaults to 'NAD'.
        cell_column (str, optional): _description_. Defaults to 'cell type'.
        ylabel (str, optional): Label for y-axis. Defaults to 'Fraction of total NAD'.

    Returns:
        pd.DataFrame: Growth parameters.
    """
    growth_params = pd.DataFrame()
    for cell in iso_corr[cell_column].unique():
        figtitle_prefix, filename = get_filename_and_figtitle(cell_line, cell)
        fig, ax, popt, std_err = nplt.plot_fitted_growth(data=iso_corr[iso_corr[cell_column] == cell],
                                                         list_of_mets=list_of_mets, cell_line=figtitle_prefix,
                                                         xcol=xcol)
        pars = pd.concat(
            (pd.DataFrame(popt).T, pd.DataFrame(std_err).T), axis=1)
        pars.columns = ['prefactor_growth', 'growth_rate',
                        'prefactor_growth_error', 'growth_error']
        pars[cell_column] = cell
        growth_params = pd.concat((growth_params, pars), axis=0)
        ax.set_ylabel(ylabel)
        if save_fig:
            if per_experiment and file is not None:
                subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
                path = f'{default_path}images/{cell_line}/{met}/{subfolder}/'
            else:
                path = f'{default_path}images/{cell_line}/{met}/'
            handle_figure(fig, path, filename, show_fig, save_fig)
    if save_data:
        if per_experiment and file is not None:
            subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
            path = f'{default_path}data/{cell_line}/{met}/{subfolder}/'
        else:
            path = f'{default_path}data/{cell_line}/{met}/'
        handle_data_saving(growth_params, path, 'growth_params.csv')
    return growth_params


def estimate_decay_parameters(iso_corr_percent, cell_line, xcol='time', ycol='NAD',
                              save_fig=False, show_fig=True,  met='NAD',
                              default_path='./publication/', file=None, per_experiment=False,
                              ylabel='Percentage of total NAD$^+$', cell_column='cell type',
                              growth_or_decay='decay'):
    """
    Estimate decay parameters for the isotopologue corrected data.

    Args:
        iso_corr_percent (pd.DataFrame): Isotopologue corrected data.
        cell_line (str): Cell line name.
        xcol (str, optional): Column name. Defaults to 'time'.
        ycol (str, optional): Column name. Defaults to 'NAD'.
        save_fig (bool, optional): _description_. Defaults to True.
        show_fig (bool, optional): _description_. Defaults to False.
        met (str, optional): _description_. Defaults to 'NAD'.
        default_path (str, optional): _description_. Defaults to './publication/'.
        file (_type_, optional): _description_. Defaults to None.
        per_experiment (bool, optional): _description_. Defaults to False.
        ylabel (str, optional): _description_. Defaults to 'Percentage of total NAD$^+$'.
        cell_column (str, optional): _description_. Defaults to 'cell type'.
        growth_or_decay (str, optional): _description_. Defaults to 'decay'.

    Returns:
        _type_: _description_
    """
    decay_params = pd.DataFrame()
    for cell in iso_corr_percent[cell_column].unique():
        figtitle_prefix, filename = get_filename_and_figtitle(
            cell_line, cell, growth_or_decay=growth_or_decay)
        _df = iso_corr_percent[iso_corr_percent[cell_column] == cell]
        fig, ax, popt, std_err, hl, hle = nplt.plot_fitted_decay(data=_df, cell_line=figtitle_prefix,
                                                                 xcol=xcol, ycol=ycol)
        ax.set_ylabel(ylabel)
        if save_fig is True:
            if per_experiment is True and file is not None:
                subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
                path = f'{default_path}images/{cell_line}/{met}/{subfolder}/'
            else:
                path = f'{default_path}images/{cell_line}/{met}/'
            handle_figure(fig, path, filename, show_fig, save_fig)
        pars = pd.concat((pd.DataFrame(popt).T, pd.DataFrame(std_err).T,
                          pd.DataFrame([hl, hle]).T), axis=1)
        pars.columns = ['prefactor_decay', 'decay_rate',
                        'prefactor_decay_error', 'decay_error',
                        'half_life', 'half_life_error']
        pars['cell type'] = cell
        decay_params = pd.concat((decay_params, pars), axis=0)
    return decay_params


def unlabelled_and_sum_labelled(iso_corr_percent, cell_line, xcol='time', ycol2='NAD',
                                ycol='sum labelled', growth_correction=False, save_fig=False,
                                show_fig=True, save_data=False, met='NAD',
                                default_path='./publication/', file=None, per_experiment=False,
                                xlabel='Time (h)', ylabel='Labelled NAD$^+$ (nmol/mg protein)',
                                cell_column='cell type'):
    decay_params = pd.DataFrame()
    for cell in iso_corr_percent[cell_column].unique():
        data = iso_corr_percent[iso_corr_percent[cell_column] == cell]
        fig, ax, popt, std_err, hl, hle = nplt.plot_fig3_panel_c(data=data, cell=cell, xcol=xcol,
                                                                 ycol=ycol, ycol2=ycol2,
                                                                 figsize=(5, 5), s=100, xlabel=xlabel,
                                                                 ylabel=ylabel)
        pars = pd.concat((pd.DataFrame(popt).T, pd.DataFrame(std_err).T,
                          pd.DataFrame([hl, hle]).T), axis=1)
        pars.columns = ['prefactor_decay', 'decay_rate',
                        'prefactor_decay_error', 'decay_error',
                        'half_life', 'half_life_error']
        plt.tight_layout()

        if growth_correction:
            filename_fig = f'{met}_decay_growth_corrected_{cell}.svg'
            pars.columns = [i+'_gc' for i in pars.columns]
            filename_data = f'decay_params_growth_corrected_{cell_line}.csv'
        else:
            filename_fig = f'{met}_decay_{cell}.svg'
            filename_data = f'decay_params_{cell_line}.csv'
        if save_fig:
            if per_experiment and file is not None:
                subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
                path = f'{default_path}images/{cell_line}/{met}/{subfolder}/'
            else:
                path = f'{default_path}images/{cell_line}/{met}/'
            handle_figure(fig, path, filename_fig, show_fig, save_fig)
        pars['cell type'] = cell
        decay_params = pd.concat((decay_params, pars), axis=0)

    if save_data:
        if per_experiment and file is not None:
            subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
            path = f'{default_path}data/{cell_line}/{met}/{subfolder}/'
        else:
            path = f'{default_path}data/{cell_line}/{met}/'
        handle_data_saving(decay_params, path, filename_data)
    return decay_params


def estimate_turnover(iso_corr_percent, nad_conc, cell_line, xcol='time',
                      ycol='pool_corr_unlabelled', met='NAD',
                      default_path='./publication/', save_data=True,
                      file=None, per_experiment=False, growth_correction=True):
    """
    Estimate turnover for the isotopologue corrected data.

    Args:
        iso_corr_percent (pd.DataFrame): Isotopologue corrected data.
        nad_conc (pd.DataFrame): NAD concentration data.
        cell_line (str): Cell line name.
        xcol (str, optional): _description_. Defaults to 'time'.
        ycol (str, optional): _description_. Defaults to 'pool_corr_unlabelled'.
        met (str, optional): _description_. Defaults to 'NAD'.
        default_path (str, optional): _description_. Defaults to './publication/'.
        save_data (bool, optional): _description_. Defaults to True.
        file (_type_, optional): _description_. Defaults to None.
        per_experiment (bool, optional): _description_. Defaults to False.
        growth_correction (bool, optional): _description_. Defaults to True.

    Returns:
        pd.DataFrame: Turnover data.
    """
    df_pool_corr = get_pool_corrected(iso_corr_percent=iso_corr_percent,
                                      nad_conc=nad_conc)

    dpars = estimate_decay_parameters(iso_corr_percent=df_pool_corr, met=met,
                                      cell_line=cell_line, xcol=xcol, ycol=ycol,
                                      save_fig=False, show_fig=False,
                                      default_path='./publication/images/',
                                      file=None, per_experiment=False)
    if growth_correction:
        cols = ['growth_rate', 'growth_rate_standard_error',
                'prefactor_growth', 'prefactor_growth_standard_error']
        dpars = pd.concat((df_pool_corr.groupby('cell type').mean(numeric_only=True)[cols],
                           dpars.set_index('cell type')), axis=1)
        dpars = dpars.reset_index()

    for cell in dpars['cell type'].unique():
        dpars = get_turnover(dpars, nad_conc.reset_index(),
                             cell=cell, cell_line=cell_line,
                             growth_correction=growth_correction)

    if save_data:
        if per_experiment and file != None:
            subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
            path = f'{default_path}data/{cell_line}/{met}/{subfolder}/'
        else:
            path = f'{default_path}data/{cell_line}/{met}/'
        os.makedirs(path, exist_ok=True)
        if growth_correction:
            filename_data = f'turnover_growth_corrected_{cell_line}.csv'
        else:
            filename_data = f'turnover_{cell_line}.csv'
            dpars.to_csv(path+f'decay_params_growth_corrected_{cell_line}.csv')
        dpars.to_csv(path+filename_data, index=False)
    return dpars


def plot_decay(cell_line, cell_column, cell, met, iso_corr_percent, xcol,
               default_path, folder_name, save_fig, show_fig):
    """
    Plot decay curve for the given cell line and cell.

    Args:
        cell_line (str): Name of the cell line.
        cell_column (str): Column name for cell type.
        cell (str): Name of the cell.
        met (str): Metabolite name.
        iso_corr_percent (pd.DataFrame): Isotopologue corrected data.
        xcol (str): Column name for x-axis.
        default_path (str): Default path to save the figures.
        folder_name (str): Folder name to save the figures.
        save_fig (bool): Whether to save the figure. True or False.
        show_fig (bool): Whether to show the figure. True or False.

    Returns:
        tuple: popt, std_err, hl, hle
    """
    figtitle_prefix, filename = get_filename_and_figtitle(
        cell_line, cell, growth_or_decay='decay')
    _df = iso_corr_percent[iso_corr_percent[cell_column] == cell]
    fig, ax, popt, std_err, hl, hle = nplt.plot_fitted_decay(data=_df, cell_line=cell,
                                                             xcol=xcol, ycol=met)
    ax.set_ylabel(f'{met} (%)')
    path = f'{default_path}images/{folder_name}/{met}/'
    handle_figure(path, fig, filename, save_fig, show_fig)
    return popt, std_err, hl, hle
