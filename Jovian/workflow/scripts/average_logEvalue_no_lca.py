"""
Thierry Janssens, 28JUN2019
Add root results for LCA and average the evalues from the filtered gff file (mgkit) to the taxtab file.
Usage:
  average_logevalue.py <input_taxtab> <input.nolca> <input_gff> <output_taxtab>
<input_taxtab> is the file generated by mgkit taxon-utils lca (made tmp()).
<input.nolca> is the file generated by mgkit-utils lca (made(tmp())
<input_gff> is the file generated by mgkit filter-gff.
<output.taxtab> is the input taxtab amended with a column with an average log evalue for every LCA (contig).
"""

import os.path
import re
import pandas as pd
import numpy as np
from sys import argv

SCRIPT, INPUTTAX, INPUTNOLCA, INPUTGFF, OUTPUTFILE = argv

df_tax = pd.read_csv(INPUTTAX, sep="\t", header = 0)

if os.path.getsize(INPUTNOLCA) > 0:
    df_nolca = pd.read_csv(INPUTNOLCA, sep="\t", header=None)
    series_nolca = df_nolca[df_nolca.columns[0]]
    series_nolca = series_nolca.unique()
    frame = {"#queryID": series_nolca, "taxID": 1, "Avg. log e-value": 1}
    df_nolca = pd.DataFrame(frame)
else:
    df_nolca = pd.DataFrame()

df_gff = pd.read_csv(INPUTGFF, sep="\t", header = None)

#? Drop everything but the 1st column (scaffold_name) and the last column (8th column; key-value pairs output by mgkit)
df_gff.drop(df_gff.columns[1:8], axis=1, inplace=True)

#? Regex for literal `evalue=\"` but don't include it in the results (i.e. "(?<=" syntax; positive lookbehind), grab the value reported there (i.e. the actual evalue; NB, it can be zero), match a literal '\";' but dont include it in the results (i.e. "(?=" syntax; positive lookahead)
#? Basically, it removes all the key-value pairs and it keeps only the actual evalue-value without it's key
df_gff.iloc[:, 1] = df_gff.iloc[:, 1].str.extract(
    r"((?<=evalue=\").*?(?=\";))", expand=True
)
df_gff.columns = ["contig", "evalue"] #? set column names
df_gff["evalue"] = pd.to_numeric(df_gff["evalue"]) #? as numeric instead of object dtype

#? Get average of all evalues per scaffold: lower taxonomische levels are averaged on and reported at the LCA-determined level. NB, many scaffolds get a 0; this is due to underflow, i.e. the number is so small it cannot be stored anymore and it might as well be 0.
df_mean_evalues = df_gff.groupby(["contig"]).mean()
#? Convert it to a log10 value, since this is the metric that MGkit uses, i.e. it does not use the default evalue as provided by BLAST but a log10 converted evalue instead.
df_log_mean_evalues = np.log10(df_mean_evalues)
df_log_mean_evalues.columns = ["Avg. log e-value"]
df_log_mean_evalues = df_log_mean_evalues.replace(-np.inf, -450) #? see comment above
df_log_mean_evalues = df_log_mean_evalues.round(decimals=1)

#? Merge tables, add records without an LCA (i.e. LCA with taxID = 1, which is 'Root') and generate outputfile
df_tax_logevalues = pd.merge(
    left=df_tax,
    right=df_log_mean_evalues,
    how="left",
    left_on="#queryID",
    right_index=True,
)
df_tax_logevalues = df_tax_logevalues.append(df_nolca, sort=False)
df_tax_logevalues.to_csv(OUTPUTFILE, index=False, sep="\t")