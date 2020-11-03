#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import venn
import matplotlib.pyplot as plt

# Read in differentially expressed genes
results = pd.read_csv('./results_p_001.tsv', sep='\t', index_col = 0)
results.head()

# Filter only upregulated genes
pos_mito = set(results[results.ratio_mitoParp_control > 0].index)
pos_cyto = set(results[results.ratio_cytoParp_control > 0].index)
pos_er = set(results[results.ratio_erParp_control > 0].index)
pos_pex = set(results[results.ratio_pexParp_control > 0].index)
pos = [pos_mito, pos_cyto, pos_er, pos_pex]
# Filter only downregulated genes
neg_mito = set(results[results.ratio_mitoParp_control < 0].index)
neg_cyto = set(results[results.ratio_cytoParp_control < 0].index)
neg_er = set(results[results.ratio_erParp_control < 0].index)
neg_pex = set(results[results.ratio_pexParp_control < 0].index)
neg = [neg_mito, neg_cyto, neg_er, neg_pex]
# Filter all differentially expressed genes
tot_mito = set(results[results.ratio_mitoParp_control.notnull()].index)
tot_cyto = set(results[results.ratio_cytoParp_control.notnull()].index)
tot_er = set(results[results.ratio_erParp_control.notnull()].index)
tot_pex = set(results[results.ratio_pexParp_control.notnull()].index)
tot = [tot_mito, tot_cyto, tot_er, tot_pex]

# Define color labels according to column order
order = ['mP', 'cP', 'erP', 'pP']
colors = ['#ed1c2466', '#3bb14966' , '#94559f66', '#405aa566']

# Get labels for the overlapping sections of the venn
labels_up = venn.get_labels(pos, fill=['number'])
labels_down = venn.get_labels(neg, fill=['number'])
labels_tot = venn.get_labels(tot, fill=['number'])

# Combine labels for up- and downregulated genes into a single label 
labels_combined = {}
for key in labels_up:
    label_up = labels_up[key]
    label_down = labels_down[key]
    combined_label = f'⇧{label_up}\n⇩{label_down}'
    labels_combined[key] = combined_label

# Create Venn diagram for the up- und downregulated genes only
fig,ax = venn.venn4(labels_combined, names=order, colors=colors)
#for i in range(4):
#    curr_ell = ax.get_children()[i]
#    curr_ell.set_facecolor(colors[i])
#    curr_ell.set_edgecolor(colors[i])
#plt.draw()
fig.savefig('venn_up_and_downregulated.svg')
fig.savefig('venn_up_and_downregulated.pdf')

fig.clear()

# Create Venn diagram for all differentially expressed genes, regardless of directionality
fig,ax = venn.venn4(labels_tot, names=order, colors=colors)
fig.savefig('venn_total.svg')
fig.savefig('venn_total.pdf')
