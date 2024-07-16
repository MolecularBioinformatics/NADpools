import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import new_utils as nu
import os

new_names = {'NAD': 'Unlabelled NAD$^+$',
             'NAD_N15': 'NAD$^+$ $^{15}$N\n(M+1)',
             'NAD_O18': 'NAD$^+$ $^{18}$O\n(M+2)',
             'NAD_5C13': 'NAD$^+$ 5$^{13}$C\n(M+5)',
             'NAD_10C13': 'NAD$^+$ 10$^{13}$C\n(M+10)',
             'NAD_5C13N15': 'NAD$^+$ 5$^{13}$C$^{15}$N\n(M+6)',
             'NAD_5C13_O18': 'NAD$^+$ 5$^{13}$C$^{18}$O\n(M+7)',
             'NAD_10C13N15': 'NAD$^+$ 10$^{13}$C$^{15}$N\n(M+11)',
             'NAD_10C13_O18': 'NAD$^+$ 10$^{13}$C$^{18}$O\n(M+12)',
             'sum labelled': 'Sum of labelled NAD$^+$'}


def plot_fig3_panel_b(iso_corr_percent, list_of_mets, cell_line,
                      file=None, save_fig=False,
                      show_fig=True, per_experiment=False, xcol='time',
                      growth_correction=True, met='NAD'):
    for metname in list_of_mets + ['sum labelled']:
        fig, ax = plt.subplots(figsize=(4, 4))
        sp = sns.scatterplot(data=iso_corr_percent, x=xcol, y=metname,
                             color=['k',], ax=ax, s=100)
        sns.lineplot(data=iso_corr_percent, x=xcol, y=metname, err_style='bars',
                     errorbar='pi', dashes=False, markers=True, ax=ax, color='k')
        ax.set_xlabel('time (h)')
        ax.set_ylabel('percentage of total NAD$^+$')
        try:
            ax.set_title(new_names[metname])
        except KeyError:
            ax.set_title(metname)
        ax.set_ylim(-5.0, 105)
        sns.despine()
        if save_fig == True:
            if per_experiment == True:
                subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
                path = f'./publication/images/{cell_line}/{met}/{subfolder}/'
            else:
                path = f'./publication/images/{cell_line}/{met}/'
            os.makedirs(path, exist_ok=True)
            if growth_correction == True:
                filename_fig = f'percentage_labelled_growth_\
                    corrected_{metname}.svg'
            else:
                filename_fig = f'percentage_labelled_{metname}.svg'
            fig.savefig(path+filename_fig, dpi=300, bbox_inches='tight')
        if show_fig == False:
            plt.close(fig)


def plot_fig3_panel_c(data, cell, xcol='Time in hours',
                      ycol='sum labelled', ycol2='No label',
                      figsize=(3, 3), s=50, ylabel='Percentage of total NAD$^+$',
                      xlabel='Time (h)'):
    popt, pcov = nu.fit_exponential_decay(x=data[xcol], y=data[ycol2])
    std_err = nu.calculate_standard_error(pcov)
    hl, hle = nu.half_life(popt, pcov)
    # hle = nu.half_life_standard_error(pcov)[1]
    fig, ax = plt.subplots(figsize=figsize)
    sp = sns.scatterplot(data=data, x=xcol, y=ycol,
                         color=['grey',], ax=ax, s=s)
    lp = sns.lineplot(data=data, x=xcol, y=ycol, c='grey', ax=ax,
                      err_style='bars', errorbar='pi')

    sp = sns.scatterplot(data=data, x=xcol, y=ycol2, color=['k',],
                         ax=ax, s=s)
    lp = sns.lineplot(data=data, x=xcol, y=ycol2,
                      err_style='bars', c='k', ax=ax, errorbar='pi')
    lp.lines[0].set_linestyle('dashed')
    ax.set_title(cell + '($\mathregular{t_{1/2}}$ = ' +
                 f'{nu.pretty_print_time(hl)} ± {nu.pretty_print_time(hle)})',
                 fontweight='bold')
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    sns.despine()
    return fig, ax, popt, std_err, hl, hle


def plot_fig3_panel_d(df_pool_corr, cell_line, xcol='time', save_fig=True,
                      growth_correction=False, per_experiment=False, file=None,
                      met='NAD'):
    fig, ax = plt.subplots(figsize=(6, 5))
    lp = sns.lineplot(data=df_pool_corr, x=xcol, ax=ax,
                      y='pool_corr', hue='cell type', style='cell type', markers=True,
                      err_style='bars', dashes=False, errorbar='pi',
                      hue_order=[cell_line, 'mP', 'pP', 'cP', 'erP'])
    sp = sns.scatterplot(data=df_pool_corr, x=xcol, ax=ax,
                         y='pool_corr', hue='cell type', style='cell type',
                         hue_order=[cell_line, 'mP', 'pP', 'cP', 'erP'])

    plt.rcParams.update({'lines.markeredgewidth': 1})
    sp.get_legend().remove()
    handles, labels = lp.get_legend_handles_labels()
    lp.legend(handles=handles[:5], labels=labels[:5], loc='lower right')
    lp.set(xlabel='Time (h)', ylabel='Labelled NAD$^+$\n(nmol/mg protein)')
    fig.tight_layout()
    sns.despine()
    if growth_correction == True:
        filename_fig = f'labelled_nad_growth_corrected_{cell_line}.svg'
    else:
        filename_fig = f'labelled_nad_{cell_line}.svg'
    if save_fig == True:
        if per_experiment == True and file != None:
            subfolder = os.path.basename(file).split('.')[0].split('_')[-1]
            path = f'./publication/images/{cell_line}/{met}/{subfolder}/'
        else:
            path = f'./publication/images/{cell_line}/{met}/'
        os.makedirs(path, exist_ok=True)
        fig.savefig(path+filename_fig, dpi=300, bbox_inches='tight')
    return fig, ax


def plot_fitted_growth(data, list_of_mets, cell_line, xcol='time'):
    _df = data.copy()
    x = _df[xcol]
    y = _df[list_of_mets].sum(axis=1).div(
        _df[_df[xcol] == 0.0][list_of_mets].sum(axis=1).mean())
    popt, std_err = nu.growth_estimation(x, y)
    fitted_data = nu.get_fitted_growth(data=_df, xcol=xcol, popt=popt)

    fig, ax = plt.subplots(figsize=(5, 5))
    sns.scatterplot(x=x, y=y,
                    ax=ax, color='black', label='data')
    sns.lineplot(x=np.linspace(_df[xcol].min(), _df[xcol].max(), 100),
                 y=fitted_data, ax=ax, color='red', label='fitted')
    ax.set_xlabel('time (h)')
    ax.set_ylabel('growth')
    ax.set_title(cell_line + f' (growth rate: {popt[1]:.2f} h$^{{-1}}$)')
    ax.legend()
    return fig, ax, popt, std_err


def plot_fitted_decay(data, cell_line, xcol='time', ycol='NAD'):
    _df = data.copy()
    x = _df[xcol]
    y = _df[ycol]
    popt, pcov = nu.fit_exponential_decay(x, y)
    std_err = nu.calculate_standard_error(pcov)
    fitted_data = nu.get_fitted_decay(data=_df, xcol=xcol, popt=popt)
    hl, hle = nu.half_life(popt, pcov)
    fig, ax = plt.subplots(figsize=(5, 5))
    sns.scatterplot(x=x, y=y,
                    ax=ax, color='black', label='data')
    sns.lineplot(x=np.linspace(_df[xcol].min(), _df[xcol].max(), 100),
                 y=fitted_data, ax=ax, color='red', label='fitted')
    ax.set_xlabel('time (h)')
    ax.set_ylabel('decay (%)')
    ax.set_title(cell_line + f' (decay rate: {popt[1]:.2f} h$^{{-1}}$)')
    ax.legend()
    return fig, ax, popt, std_err, hl, hle
