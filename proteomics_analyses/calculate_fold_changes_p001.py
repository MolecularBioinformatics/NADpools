#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from math import log
from scipy.stats import ttest_rel, ttest_ind
from matplotlib import pyplot
import numpy as np


### Reading excel sheet and prepping DataFrame ###

data = pd.read_excel('P19-24_1253 TMT.xlsx', sheet_name=1)

del_cols = ['Checked', 'Protein FDR Confidence: Combined']
for x in list(data.columns):
    if x.startswith('Unnamed:'):
        del_cols.append(x)
for x in del_cols:
    del(data[x])

data.set_index('Accession', inplace=True)

# Extracting all columns containing abundance ratios
ar_cols = [x for x in list(data.columns) if x.startswith('Abundance Ratio:')]

data.dropna(subset=ar_cols, inplace=True) # drop rows with all NaN

# Define which columns contain MitoParp (mp), ERParp (ep), pexParp(pp), and cytoParp (cp) with and without the inhibitor (pj):
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


### Find columns containing abundance ratios for each of the cell lines ###

def find_cols(tags: list, cols_to_search: list):
    """
    Helper function to find the appropriate columns for each cell line.
    Finds all columns in cols_to_search containing any of the tags.
    :param tags: List of sample identifiers matching regex 'F\d, \d{3}[NC]' 
    :type tags: list of str
    :param cols_to_search: Columns in which to search for identifiers
    :type cols_to_search: list of str
    :return: List of the columns from cols_to_search containing the tags 
    :rtype: list of str
    """
    return [x for x in cols_to_search if ((tags[0] in x) or (tags[1] in x) or (tags[2] in x))]

mp_cols = find_cols(mp, ar_cols)
ep_cols = find_cols(ep, ar_cols)
pp_cols = find_cols(pp, ar_cols)
cp_cols = find_cols(cp, ar_cols)

mp_pj_cols = find_cols(mp_pj, ar_cols)
ep_pj_cols = find_cols(ep_pj, ar_cols)
pp_pj_cols = find_cols(pp_pj, ar_cols)
cp_pj_cols = find_cols(cp_pj, ar_cols)

control_cols = find_cols(control, ar_cols)
control_pj_cols = find_cols(control_pj, ar_cols)


# These two values were too large to be true, probably faulty measurements.
# Hence we drop them:
data.drop(['Q86TN4', 'Q9BVA0'], axis=0, inplace=True) 


### Calculate fold changes between each pair of cell lines ###

# Set up the dataframe to store comparisons
categories = ['mitoParp', 'cytoParp', 'erParp', 'pexParp', 'mitoParp_pj', 'cytoParp_pj', 'erParp_pj', 'pexParp_pj', 'control', 'control_pj']
categories_translation = {
    'mitoParp': mp_cols, 
    'cytoParp': cp_cols, 
    'erParp': ep_cols, 
    'pexParp': pp_cols, 
    'mitoParp_pj': mp_pj_cols, 
    'cytoParp_pj':cp_pj_cols, 
    'erParp_pj': ep_pj_cols, 
    'pexParp_pj': pp_pj_cols, 
    'control': control_cols, 
    'control_pj': control_pj_cols
    }
comparison = pd.DataFrame(columns=categories, index=categories)

# Set p-Value cutoff above which we discard gene fold-changes
p_cutoff = .001

# Actually running the comparison
for cat1 in categories:
    cat1_col = categories_translation[cat1] # getting the column names
    for cat2 in categories:
        cat2_col = categories_translation[cat2]
        data1 = data.loc[:, cat1_col] # dataframe with values for category 1 (3 colums with counts)
        data2 = data.loc[:, cat2_col]
        avg1 = data1.mean(axis=1); avg2 = data2.mean(axis=1) # pd.Series containing averages for each cell line
        
        p = ttest_ind(data1, data2, axis=1, nan_policy='propagate').pvalue # numpy array containing T-test results
        p = pd.Series(p, index=data.index)

        ratio = avg1 / avg2 # fold-change is calculated here
        
        df = pd.concat([ratio, p], axis=1, sort=True)
        df.columns = ['ratio', 'pVal']
        df['ratio'] = df.ratio.apply(lambda x: log(x, 2)) # log2-transform ratios
        df = df[df.pVal < p_cutoff] # leave out insignificant results
        comparison.loc[cat1, cat2] = list(df.itertuples(index=True, name=None)) # write results into comparison DatafFrame / Matrix
# comparisons run double, but computation times are still fine


### Pull comparisons into one DataFrame ###

def pull_df(tag_pairs):
    """
    Given a pair of tags, creates a Dataframe from the experiments in the tag. From being currently saved in a list of tuples.
    """
    df = []
    for pair in tag_pairs:
        tag1 = pair[0]
        tag2 = pair[1]
        entries = comparison.loc[tag1, tag2]
        entries = pd.DataFrame(entries, columns=['protein', f'ratio_{tag1}-{tag2}', f'statistic_{tag1}-{tag2}'])
        entries.set_index('protein', inplace=True)
        df.append(entries)
    df = pd.concat(df, axis=1, sort=True)
    return df

# Pull out dataframe from each comparison, put them in list, then concatenate dataframes in list:
total = []
for x in categories:
    for y in categories:
        df = pd.DataFrame(comparison.loc[x,y])
        if len(df) == 0:
            continue
        df.columns = ['protein', f'ratio_{x}_{y}', f'p_{x}_{y}']
        df.set_index('protein', inplace=True)
        total.append(df)
total = pd.concat(total, axis=1, sort=True)

tags = ['mitoParp', 'cytoParp', 'erParp', 'pexParp']
tags = [f'ratio_{x}_control' for x in tags]
df = total.loc[:, tags]


### Annotate results and save ###

# Count in how many comparisons each gene is included:
df['count'] = np.nan
for x in list(df.index):
    l = len(df.loc[x, :].dropna())
    df.loc[x, 'count'] = l
df.sort_values('count', ascending=False)

# Find gene names matching UniProt IDs:
gene_translation = {}
with open('gene_names.txt', 'r') as f:
    for line in f:
        x = line.split('\t')
        gene_translation[x[0]] = x[1][:-1]
new_index = []
df['gene_name'] = np.nan
for x in list(df.index):
    try:
        df.loc[x, 'gene_name'] = gene_translation[x]
    except KeyError:
        pass

df = df[df['count'] >= 1.] # Remove genes not found in either comparison

# Sort by count and write to file:
df.sort_values('count', ascending=False).to_csv('results_p_001.tsv', sep='\t')
