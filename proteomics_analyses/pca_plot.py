#!/usr/bin/env python
# coding: utf-8


from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler as Scaler
from os.path import exists
from os import mkdir

import seaborn as sb
import pandas as pd
import re
from numpy import nan
import matplotlib.pyplot as plt


data = pd.read_excel('P19-24_1253 TMT.xlsx', sheet_name=1)


del_cols = ['Checked', 'Protein FDR Confidence: Combined']
for x in list(data.columns):
    if x.startswith('Unnamed:'):
        del_cols.append(x)
for x in del_cols:
    del(data[x])
data.set_index('Accession', inplace=True)


ar_cols = [x for x in list(data.columns) if x.startswith('Abundance Ratio:')]
data.dropna(subset=ar_cols, inplace=True)

mp = ['F3, 127N', 'F2, 130N', 'F1, 129C']
ep = ['F3, 129C', 'F1, 130C', 'F2, 131C']
pp = ['F1, 128N', 'F2, 130C', 'F3, 130C']
cp = ['F1, 128C', 'F2, 128C', 'F3, 131N']

mp_pj = ['F1, 129N', 'F2, 131N', 'F3, 131C']
ep_pj = ['F3, 128N', 'F2, 129N', 'F1, 130N']
pp_pj = ['F2, 128N', 'F3, 129N', 'F1, 131C']
cp_pj = ['F3, 127C', 'F2, 129C', 'F1, 131N']

control = ['F1, 127N', 'F2, 127C', 'F3, 128C']
control_pj = ['F2, 127N', 'F1, 127C', 'F3, 130N']


def find_cols(tags, cols):
    return [x for x in cols if ((tags[0] in x) or (tags[1] in x) or (tags[2] in x))]
cols = ar_cols

mp_cols = find_cols(mp, cols)
ep_cols = find_cols(ep, cols)
pp_cols = find_cols(pp, cols)
cp_cols = find_cols(cp, cols)

mp_pj_cols = find_cols(mp_pj, cols)
ep_pj_cols = find_cols(ep_pj, cols)
pp_pj_cols = find_cols(pp_pj, cols)
cp_pj_cols = find_cols(cp_pj, cols)

control_cols = find_cols(control, cols)
control_pj_cols = find_cols(control_pj, cols)


re_col_id = re.compile('[a-zA-Z]\d, \d{3}[a-zA-Z]')
re_col_id.findall('Abundance Ratio: (F1, 127N) / (F1, 126)')


def map_cols(col_name):
    ident = re_col_id.findall(col_name)[0]
    if ident in mp:
        return 'mP'
    elif ident in ep:
        return'erP'
    elif ident in pp:
        return 'pP'
    elif ident in cp:
        return 'cP'
    elif ident in control:
        return '293'
    else:
        return nan

colors = ['#000000ff', '#3bb149ff', '#94559fff' , '#ed1c24ff', '#405aa5ff']
tags_alpha = ['293', 'cP', 'erP', 'mP', 'pP']
color_map = dict(zip(tags_alpha, colors))

pca = PCA(n_components=.95) # enough components to explain 95% of variance
data_pca = data[ar_cols].values.transpose()
data_pca = Scaler().fit_transform(data_pca)
pca_output = pca.fit_transform(data_pca)


df_pca_output = pd.DataFrame(pca_output, index=ar_cols, columns=range(1,pca_output.shape[1] + 1))
df_pca_output['label'] = df_pca_output.index.map(map_cols)
df_pca_output.dropna(inplace=True)
df_pca_output.head()


explained_variance = pd.Series(pca.explained_variance_ratio_, index = range(1,pca_output.shape[1] + 1))
if not exists('pca_results'):
    mkdir('pca_results')
explained_variance.to_csv('pca_results/explained_variance.tsv', sep='\t', header=True)


sb.set(
    context='paper',
    font_scale=2.
)
sb.set_style('dark')
sb.despine()
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(25, 7))
x_limit = (-40, 90)
y_limit = (-40, 90)
marker_size = 100

plt.subplot(1, 3, 1)
ax1 = sb.scatterplot(data=df_pca_output, x=1, y=2, hue='label', s=marker_size, palette=color_map)
ax1.set_xlabel(
    f'Component 1 ({pca.explained_variance_ratio_[0] * 100:.1f}%)')
ax1.set_ylabel(
    f'Component 2 ({pca.explained_variance_ratio_[1] * 100:.1f}%)')
ax1.set_xlim(*x_limit)
ax1.set_ylim(*y_limit)
ax1.get_legend().remove()

plt.subplot(1, 3, 2)
ax2 = sb.scatterplot(data=df_pca_output, x=1, y=3, hue='label', s=marker_size, palette=color_map)
ax2.set_xlabel(
    f'Component 1 ({pca.explained_variance_ratio_[0] * 100:.1f}%)')
ax2.set_ylabel(
    f'Component 3 ({pca.explained_variance_ratio_[2] * 100:.1f}%)')
ax2.set_xlim(*x_limit)
ax2.set_ylim(*y_limit)
ax2.get_legend().remove()

plt.subplot(1, 3, 3)
ax3 = sb.scatterplot(data=df_pca_output, x=2, y=3, hue='label', s=marker_size, palette=color_map)
ax3.set_xlabel(
    f'Component 2 ({pca.explained_variance_ratio_[1] * 100:.1f}%)')
ax3.set_ylabel(
    f'Component 3 ({pca.explained_variance_ratio_[2] * 100:.1f}%)')
ax3.set_xlim(*x_limit)
ax3.set_ylim(*y_limit)


handles, labels = ax3.get_legend_handles_labels()
labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
labels = labels[:3] + labels[4:]
handles = handles[:3] + handles[4:]

ax3.legend(handles=handles, labels=labels, fontsize='medium', markerscale = 1.8, )

fig.savefig('pca_results/pca_plot.svg')
fig.savefig('pca_results/pca_plot.pdf');

