"""For each scaffold, merge the following data:
scaffold metrics, taxonomic classification after LCA,
virus host and disease information.
Usage:
  merge_data.py <sample_name> <scaffold_metrics> <Krona_LCA_taxonomy> <input_scaffolds> <scaffold_ORF_count> <path_virushost_db> <path_rankedlineage_taxdump> <path_host_taxdump> <output_classified_scaffolds> <output_unclassified_scaffolds> <output_scaffolds_host>
<sample_name> is how you want to call this sample (in plain text).
<scaffold_metrics> is the BBtools generated scaffold metrics file.
<Krona_LCA_taxonomy> is the taxtab file generated by Krona after
the LCA analysis.
<input_scaffolds> is the input scaffold fasta file.
<scaffold_ORF_count> is the input per scaffold ORF count list.
<path_virushost_db> is the location on your filesystem where the
virus-host database can be found (Mihara et al. 2016).
<path_rankedlineage_taxdump> is the location on your filesystem
where the NCBI "new_taxdump" file called "rankedlineage" can be found.
<path_host_taxdump> is the location on your filesystem
where the NCBI "new_taxdump" file called "host" can be found.
<output_classified_scaffolds> is the output file containing
the scaffolds with taxonomic classification data, i.e.
"classified" scaffolds.
<output_unclassified_scaffolds> is the output file containing
the scaffolds without taxonomic classification data, i.e.
"unclassified" scaffolds.
<output_scaffolds_host> is the output file containing the host
and disease information generated by cross-referencing the 
virus-host database (Mihara et al. 2016) and NCBI "host" database.
Example:
  python bin/merge_data.py [sample_name] \
    data/scaffolds_filtered/[sample_name]_perMinLenFiltScaffold.stats \
    data/taxonomic_classification/[sample_name].taxtab \
    data/scaffolds_filtered/[sample_name]_scaffolds_ge500nt.fasta \
    data/scaffolds_filtered/[sample_name]_contig_ORF_count_list.txt \
    [path_to_virushost_DB] \
    [path_to_NCBI_newTaxdump_rankedlineage] \
    [path_to_NCBI_newTaxdump_host] \
    data/tables/[sample_name]_taxClassified.tsv \
    data/tables/[sample_name]_taxUnclassified.tsv \
    data/tables/[sample_name]_virusHost.tsv
"""

import pandas as pd
from sys import argv
from Bio import SeqIO

(
    SCRIPT,
    SAMPLENAME,
    INPUTBBTOOLS,
    INPUTKRONA,
    INPUTSCAFFOLDS,
    CONTIG_ORF_COUNT_LIST,
    VIRUSHOSTDB,
    PATH_TAXDUMP_RANKEDLINEAGE,
    PATH_TAXDUMP_HOST,
    OUTPUTFILE_CLASSIFIED_SCAFFOLDS_TAX_TABLE,
    OUTPUTFILE_UNCLASSIFIED_SCAFFOLDS_TAX_TABLE,
    OUTPUTFILE_VIRAL_SCAFFOLDS_HOSTS_TABLE,
) = argv

# Import scaffold statistics to df
perScaffoldStats = pd.read_csv(INPUTBBTOOLS, sep="\t", header=0)
# Import Krona LCA results to df and replace spaces with underscores
kronaTaxLCA = pd.read_csv(INPUTKRONA, sep="\t", header=0)
kronaTaxLCA.columns = kronaTaxLCA.columns.str.replace("\s+", "_")
# Import virus-host DB and replace spaces with underscores
virusHostDB = pd.read_csv(VIRUSHOSTDB, sep="\t", header=0)
virusHostDB.columns = virusHostDB.columns.str.replace("\s+", "_")
# Import assembled scaffold fasta
scaffolds_dict = {"scaffold_name": [], "scaffold_seq": []}
for seq_record in SeqIO.parse(INPUTSCAFFOLDS, "fasta"):
    scaffolds_dict["scaffold_name"].append(seq_record.id)
    scaffolds_dict["scaffold_seq"].append(str(seq_record.seq))
scaffoldsFasta = pd.DataFrame.from_dict(scaffolds_dict)
# Import new_taxdump rankedlineage
colnames_rankedlineage = [
    "tax_id",
    "tax_name",
    "species",
    "genus",
    "family",
    "order",
    "class",
    "phylum",
    "kingdom",
    "superkingdom",
]
taxdump_rankedlineage = pd.read_csv(
    PATH_TAXDUMP_RANKEDLINEAGE,
    sep="|",
    header=None,
    names=colnames_rankedlineage,
    low_memory=False,
)
# Import new_taxdump host
colnames_host = ["tax_id", "potential_hosts"]
taxdump_host = pd.read_csv(
    PATH_TAXDUMP_HOST, sep="|", header=None, names=colnames_host, low_memory=False
)
# Import per scaffold ORF counts
colnames_scaffold_orf_count_list = ["Nr_ORFs", "scaffold_name"]
contig_orf_count_list = pd.read_csv(
    CONTIG_ORF_COUNT_LIST,
    sep="\s+",
    header=None,
    names=colnames_scaffold_orf_count_list,
    low_memory=False,
)


# Merge Krona LCA with scaffold metrics
df1 = pd.merge(
    perScaffoldStats, kronaTaxLCA, how="left", left_on="#ID", right_on="#queryID"
).drop("#queryID", axis=1)
# Merge above df with rankedlineage
df2 = pd.merge(
    df1, taxdump_rankedlineage, how="left", left_on="taxID", right_on="tax_id"
).drop("tax_id", axis=1)
# Merge above df with ORF counts
df3 = pd.merge(
    df2, contig_orf_count_list, how="left", left_on="#ID", right_on="scaffold_name"
).drop("scaffold_name", axis=1)
# Merge above df with fasta
df4 = pd.merge(
    df3, scaffoldsFasta, how="left", left_on="#ID", right_on="scaffold_name"
).drop("#ID", axis=1)

# Add sample name as first column, then reorder df as desired, then replace any spaces with underscores
df4["Sample_name"] = SAMPLENAME
colnames = [
    "Sample_name",
    "scaffold_name",
    "taxID",
    "tax_name",
    "Avg._log_e-value",
    "species",
    "genus",
    "family",
    "order",
    "class",
    "phylum",
    "kingdom",
    "superkingdom",
    "Avg_fold",
    "Length",
    "Ref_GC",
    "Nr_ORFs",
    "Covered_percent",
    "Covered_bases",
    "Plus_reads",
    "Minus_reads",
    "Read_GC",
    "Median_fold",
    "Std_Dev",
    "scaffold_seq",
]
df4 = df4.reindex(columns=colnames)

# Slice into classified scaffolds, print to file. A selections is made that captures anything where taxID is not "1", i.e. anything that LCA doesn't assign to 'Root' and where the taxID not empty, which are records where BLAST could not identify any hits to even perform LCA on.
taxClassified = df4.loc[(df4["taxID"] != 1 ) & (df4["taxID"].notnull())]
taxClassified.to_csv(OUTPUTFILE_CLASSIFIED_SCAFFOLDS_TAX_TABLE, index=False, sep="\t")
# Slice into unclassified scaffolds, print to file. Vice versa as above. `Root` LCA assignment usually happens for bacterial seqs with integrated prophages.
taxUnclassified = df4.loc[(df4["taxID"] == 1 ) | (df4["taxID"].isnull())].drop(
    [
        "taxID",
        "tax_name",
        "Avg._log_e-value",
        "species",
        "genus",
        "family",
        "order",
        "class",
        "phylum",
        "kingdom",
        "superkingdom",
    ],
    axis=1,
)
taxUnclassified.to_csv(
    OUTPUTFILE_UNCLASSIFIED_SCAFFOLDS_TAX_TABLE, index=False, sep="\t"
)
# Slice into virus scaffolds with added host/disease information, print to file
virus_taxa_with_NCBIhosts = (
    pd.merge(
        taxClassified.loc[taxClassified["superkingdom"] == "Viruses"].iloc[
            :, [0, 1, 2]
        ],
        taxdump_host,
        how="left",
        left_on="taxID",
        right_on="tax_id",
    )
    .drop("tax_id", axis=1)
    .rename(columns={"potential_hosts": "NCBI_potential_hosts"})
)
virusHost_table_raw = pd.merge(
    virus_taxa_with_NCBIhosts,
    virusHostDB,
    how="left",
    left_on="taxID",
    right_on="virus_tax_id",
).drop("virus_tax_id", axis=1)
virusHost_table_raw.to_csv(
    OUTPUTFILE_VIRAL_SCAFFOLDS_HOSTS_TABLE, index=False, sep="\t"
)