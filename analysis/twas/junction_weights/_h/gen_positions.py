#!/usr/bin/python

__author__ = "KJ Benjamin"

import subprocess
import pandas as pd


def extract_positions():
    wgtlist_file = 'Phase3_Caudate.list'
    with subprocess.Popen('''cut -d . -f 2 %s''' % wgtlist_file,
                          shell=True, stdout=subprocess.PIPE) as p:
        geneids = pd.read_csv(p.stdout, sep='\t', header=None,
                              names=['Geneid'])
    
    wgtlist = pd.read_csv(wgtlist_file, sep='\t', header=None, names=['WGT'])
    new_wgt = pd.concat([wgtlist, geneids], axis=1)
    
    annot = pd.read_csv('../../_m/junctions/annotations.txt', sep='\t')\
              .rename(columns={'Juncid': 'Geneid', 'start': 'P0', 'end': 'P1'})
    df = pd.merge(geneids, annot, on='Geneid')
    df.loc[:, 'CHR'] = df.Chr.str.replace('chr', '')

    new_df = new_wgt.merge(df, on='Geneid').drop(['Geneid'], axis=1)\
                                           .sort_values(['CHR', 'P0'])
    return new_df[['WGT', 'ID', 'CHR', 'P0', 'P1']]


def main():
    pos = extract_positions()
    pos.to_csv('Phase3_Caudate.pos', sep='\t', index=False, header=True)


if __name__ == '__main__':
    main()