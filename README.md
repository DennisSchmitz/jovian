<!-- omit in toc -->
# Jovian - Accessible viral metagenomics for public health and clinical domains

<p align="center">
    <img alt="Jovian logo" width="200" src="Jovian/workflow/files/Jovian_logo.svg">
</p>

<p align="center">
    <a href="https://github.com/DennisSchmitz/Jovian/releases">
        <img alt="GitHub release version button" src="https://img.shields.io/github/v/release/DennisSchmitz/Jovian?include_prereleases&style=flat-square">
    </a>
    <a href="https://www.gnu.org/licenses/agpl-3.0">
        <img alt="GNU license button for AGPL3.0" src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg?style=flat-square">
    </a>
    <br>
    <a href="https://snakemake.readthedocs.io/en/stable/">
        <img alt="Snakemake version button", src="https://img.shields.io/badge/Snakemake-v7.18.2-brightgreen.svg?style=flat-square">
    </a>
    <a href="https://www.python.org/downloads/source/">
        <img alt="Python version button", src="https://img.shields.io/badge/Python-v3.9-brightgreen.svg?style=flat-square">
    </a>
</p>

<p align="center">
    <b><i>View an interactive demo report:</i></b>
    <br>
    <a href="https://mybinder.org/v2/gh/DennisSchmitz/Jovian_mybinder_passthrough/HEAD">
        <img alt="MyBinder Jovian example button" src="https://mybinder.org/badge_logo.svg">
    </a>
</p>

<!-- omit in toc -->
## Table of contents
- [Introduction](#introduction)
- [Usage](#usage)
  - [Input](#input)
  - [Output](#output)
  - [Command-line parameters](#command-line-parameters)
  - [Examples](#examples)
- [Visualizing results](#visualizing-results)
- [Installation instructions](#installation-instructions)
  - [Prerequisites](#prerequisites)
  - [Download](#download)
  - [Installation](#installation)
  - [Databases](#databases)
    - [Considerations](#considerations)
- [Citation](#citation)
- [Funding](#funding)


## Introduction

Jovian is a pipeline for assembling metagenomics/viromics samples from raw paired-end Illumina FastQ data and intended for batch-wise data analysis, e.g. analyzing an entire sequencing run in one workflow. It performs quality control and data cleanup, removal of human host data to facilitate GDPR-compliance, and assembly of cleaned reads into bigger scaffolds with a focus on full viral genomes. All scaffolds are taxonomically annotated and certain viral families, genera and species are genotyped to the (sub)species and/or cluster level. Any taxonomically ambiguous scaffolds that cannot be resolved by the lowest common ancestor analysis (LCA) are reported for manual inspection.

It is designed to run on High-Performance Computing (HPC) infrastructures, but can also run locally on a standalone (Linux) computer if needed. It depends on `conda` and `singularity` (explained [here](#installation)) and on [these databases](#databases). Jovian's usage of `singularity` is to facilitate [mobility of compute](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0177459).

A distinguishing feature is its ability to generate an interactive report to empower end-users to perform their own analyses. An example is shown [here](https://mybinder.org/v2/gh/DennisSchmitz/Jovian_mybinder_passthrough/HEAD). This report contains an overview of generated scaffolds and their taxonomic assignment, allows interactive assessment of the scaffolds and SNPs identified therein, alongside rich and interactive visualizations including QC reports, Krona-chart, taxonomic heatmaps and interactive spreadsheet to investigate the dataset. Additionally, logging, audit-trail and acknowledgements are reported.  

---

## Usage

___On first use___, the paths to the required databases need to be specified (as explained [here](#databases)):

```bash
jovian \
    --background {/path/to/background/genome.fa} \
    --blast-db {/path/to/NT_database/nt} \
    --blast-taxdb {/path/to/NCBI/taxdb/} \
    --mgkit-db {/path/to/mgkit_db/} \
    --krona-db {/path/to/krona_db/} \
    --virus-host-db {/path/to/virus_host_db/virushostdb.tsv} \
    --new-taxdump-db {/path/to/new_taxdump/} \
    --input {/path/to/input-directory} \
    --output {/path/to/desired-output}
```

These database paths are saved in `~/.jovian_env.yaml` so that they do not need to be supplied for future analyses. Thus, you can start a subsequent analysis with just the [input](#input) and [output](#output) directories:

```bash
jovian \
    --input {/path/to/input-directory} \
    --output {/path/to/desired-output}
```

Other command-line parameters can be found [here](#command-line-parameters) alongside these [examples](#examples). After the analysis finishes, this can be visualized as described [here](#visualizing-results).

NB, by default Jovian is intended to be used on a grid-computing infrastructure, e.g. a High-Performance Computing (HPC) cluster with a default queue-name called `bio` and through the `DRMAA` abstraction layer. If you want to run it on a single computer (i.e. locally), use it on a `SLURM` system, or, change the queue-name, please see the examples [here](#examples).

### Input

Jovian takes as input a folder containing either uncompressed or gzipped Illumina paired-end fastq files with the extensions `.fastq`, `.fq`, `.fastq.gz` or `.fq.gz`. In order to correctly infer paired-end relationship between the R1 and R2 file the filenames must follow this regular expression `(.*)(_|\.)R?(1|2)(?:_.*\.|\..*\.|\.)f(ast)?q(\.gz)?`; essentially samples must have an identical basename that contains `_R[1|2]`, `.R[1|2]`, `_[1|2]` or `.[1|2]`.  

### Output

Many output files are generated in the specified output folder via [--output](#command-line-parameters), intended to be visualized as explained [here](#visualizing-results). In light of [FAIR](https://www.go-fair.org/fair-principles/) data, and in case you want to parse these files yourself, the table below explains the intent and formatting of these output files.  

| Foldername                 | Filename                                                | Format                              | Brief content description                                                                                                           |
| -------------------------- | ------------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| root*/                     | launch_report.sh                                        | bash script (US-ASCII)              | Script required to visualize the data as described [here](#visualizing-results)                                                     |
| root*/results              | all_filtered_SNPs.tsv                                   | Tab separated flatfile (US-ASCII)   | Conversion of VCF** metrics to text containing a summary of all identified minority variants, per sample and scaffold               |
| root*/results              | all_noLCA.tsv                                           | Tab separated flatfile (US-ASCII)   | Scaffolds for which Lowest Common Ancestor Analysis taxonomic assignment was unsuccessful due to incongruent taxon assignment***    |
| root*/results              | all_taxClassified.tsv                                   | Tab separated flatfile (US-ASCII)   | Scaffolds with full taxonomic assignment alongside `BLAST` E-Value and alignment metrics                                            |
| root*/results              | all_taxUnclassified.tsv                                 | Tab separated flatfile (US-ASCII)   | Scaffolds that could not be taxonomically assigned alongside alignment metrics                                                      |
| root*/results              | all_virusHost.tsv                                       | Tab separated flatfile (US-ASCII)   | Scaffolds assigned with host-metadata from NCBI and Mihara et al., 2016                                                             |
| root*/results              | [Bacteria\|Phage\|Taxonomic\|Virus]_rank_statistics.tsv | Tab separated flatfile (US-ASCII)   | No. of unique taxonomic assignments from Superkingdom to species for Bacterial, Phage and Virus assigned scaffolds                  |
| root*/results              | igv.html                                                | HTML file (US-ASCII)                | `Integrative Genome Viewer` (IGVjs, Robinson et al., 2023) index.html tuned for usage as described [here](#visualizing-results)     |
| root*/results              | krona.html                                              | HTML file (US-ASCII)                | `Krona` chart (Ondov et al., 2011) depicting metagenomic content                                                                    |
| root*/results              | log_conda.txt                                           | Text file (US-ASCII)                | Logging of the master conda environment where the workflow runs in, part of the audit trail                                         |
| root*/results              | log_config.txt                                          | Text file (US-ASCII)                | Logging of the workflow parameters, part of the audit trail                                                                         |
| root*/results              | log_db.txt                                              | Text file (US-ASCII)                | Logging of the database paths, part of the audit trail                                                                              |
| root*/results              | log_git.txt                                             | Text file (US-ASCII)                | Git hash and github repo link, part of the audit trail                                                                              |
| root*/results              | logfiles_index.html                                     | HTML file (US-ASCII)                | Collation of the logfiles generated by the workflow, part of the audit trail                                                        |
| root*/results              | multiqc.html                                            | HTML file (US-ASCII)                | `MultiQC` report (Ewels et al., 2016) depicting quality control metrics                                                             |
| root*/results              | profile_read_counts.tsv                                 | Tab separated flatfile (US-ASCII)   | Read-counts underlying the Sample_composition_graph.html file listed below                                                          |
| root*/results              | profile_read_percentages.tsv                            | Tab separated flatfile (US-ASCII)   | Read-counts, as percentage, underlying the Sample_composition_graph.html file listed below                                          |
| root*/results              | Sample_composition_graph.html                           | HTML file (US-ASCII)                | HTML barchart showing the stratified sample composition                                                                             |
| root*/results              | samplesheet.yaml                                        | YAML file (US-ASCII)                | List of processed samples containing the paths to the input files, part of the audit trail                                          |
| root*/results              | snakemake_report.html                                   | HTML file (US-ASCII)                | `Snakemake` (Köster et al., 2012) logs, part of the audit-trail                                                                     |
| root*/results              | Superkingdoms_quantities_per_sample.csv                 | Comma separated flatfile (US-ASCII) | Intermediate file for the profile_read files listed above                                                                           |
| root*/results/counts       | Mapped_read_counts.tsv                                  | Tab separated flatfile (US-ASCII)   | Intermediate file with mapped reads per scaffold for the all_tax*.tsv files listed above                                            |
| root*/results/counts       | Mapped_read_counts-[Sample_name].tsv                    | Tab separated flatfile (US-ASCII)   | Intermediate file with mapped reads per scaffold for the all_tax*.tsv files listed above                                            |
| root*/results/heatmaps     | [Bacteria\|Phage\|Superkingdom\|Virus]_heatmap.html     | HTML file (US-ASCII)                | Heatmaps for different taxonomic strata's down to species level assignment                                                          |
| root*/results/multiqc_data | _several files_                                         | Text file (US-ASCII)                | Files required for proper functionality of multiqc.html as listed above                                                             |
| root*/results/scaffolds    | [Sample_name]_scaffolds.fasta                           | FASTA file (US-ASCII)               | Scaffolds as assembled by `metaSPAdes` (Nurk et al., 2017) filtered by minimum length as described [here](#command-line-parameters) |
| root*/results/typingtools  | all_[nov\|ev\|hav\|hev\|rva\|pv\|flavi]-TT.csv          | Comma separated flatfile (US-ASCII) | Genotyping results from various typingtools as listed in [publication](#citation)                                                   |
| root*/configs/             | config.yaml & params.yaml                               | YAML file (US-ASCII)                | Intermediate configuration and parameter files which are collated in log_config.txt listed above                                    |
| root*/data/                | _several folders with subfiles_                         | _various_                           | Intermediate files, not intended for direct use but kept for audit and debugging purposes                                           |
| root*/logs/                | _several folders with subfiles_                         | Text files (US-ASCII)               | Log-files of all the disparate algorithms used by `Jovian` which are collated in logfiles_index.html as listed above                |
| root*/.snakemake/          | _several folders with subfiles_                         | _various_                           | Only for internal use by `Snakemake`, not intended for direct use                                                                   |

\* this represents the "root" folder, i.e. the name your supplied to the `--output` flag as listed [here](#command-line-parameters).  
\** [Variant Call Format (VCF) explained](https://gatk.broadinstitute.org/hc/en-us/articles/360035531692-VCF-Variant-Call-Format).  
\*** Generally this is caused by scaffolds that can be assigned as both a bacterium or as a phage, e.g. temperate phages.  

### Command-line parameters

```text
usage: Jovian [required arguments] [optional arguments]

Jovian: a metagenomic analysis workflow for public health and clinics with interactive reports in your web-browser

NB default database paths are hardcoded for RIVM users, install the default databases using --install-databases or specify your own database paths using the optional arguments.
On subsequent invocations of Jovian, the database paths will be read from the file located at: /home/schmitzd/.jovian_env.yaml and you will not have to provide them again.
Similarly, the default RIVM queue is provided as a default value for the '--queuename' flag, but you can override this value if you want to use a different queue.

Required arguments:
  --input DIR, -i DIR    The input directory containing the raw fastq(.gz) files
  --output DIR, -o DIR   Output directory (default: /some/path)

Optional arguments:
  --install-databases    Install the default databases (default: False). NB, carefully read the instructions here https://github.com/DennisSchmitz/Jovian?tab=readme-ov-file#installation-instructions
  --reset-db-paths       Reset the database paths to the default values
  --background File      Override the default human genome background path
  --blast-db Path        Override the default BLAST NT database path
  --blast-taxdb Path     Override the default BLAST taxonomy database path
  --mgkit-db Path        Override the default MGKit database path
  --krona-db Path        Override the default Krona database path
  --virus-host-db File   Override the default virus-host database path (https://www.genome.jp/virushostdb/)
  --new-taxdump-db Path  Override the default new taxdump database path
  --version, -v          Show Jovian version and exit
  --help, -h             Show this help message and exit
  --skip-updates         Skip the update check (default: False)
  --local                Use Jovian locally instead of in a grid-computing configuration (default: False)
  --slurm                Use SLURM instead of the default DRMAA for grid execution (default: DRMAA)
  --queuename NAME       Name of the queue to use for grid execution (default: bio)
  --conda                Use conda environments instead of the default singularity images (default: False)
  --dryrun               Run the Jovian workflow without actually doing anything to confirm that the workflow will run as expected (default: False)
  --threads N            Number of local threads that are available to use.
                         Default is the number of available threads in your system (20)
  --minphredscore N      Minimum phred score to be used for QC trimming (default: 20)
  --minreadlength N      Minimum read length to used for QC trimming (default: 50)
  --mincontiglength N    Minimum contig length to be analysed and included in the final output (default: 250)
```

### Examples

If you want to run Jovian through a certain queue-name, use the `--queuename` flag with your own queue-name as specified below. Likewise, if you are using `SLURM`, provide the `--slurm` flag.

```bash
jovian \
    --input {/path/to/input-directory} \
    --output {/path/to/desired-output} \
    --queuename {your_queue_name} \
    --slurm # only if you are using a SLURM job scheduler
```

If you want to invoke it on a single computer/laptop you can invoke the `--local` flag like:

```bash
jovian \
    --local \
    --input {/path/to/input-directory} \
    --output {/path/to/desired-output}
```

Similarly, you can toggle to build the environments via `conda` but for proper functionality please use the default mode that uses `singularity` containers.

```bash
jovian \
    --conda \
    --input {/path/to/input-directory} \
    --output {/path/to/desired-output}
```

## Visualizing results

When the pipeline has finished an analysis successfully, you can visualize the data via an interactive rapport as follows:  
___NB keep this process running for as long as you want to visualize and inspect the data___  

```bash
cd {/path/to/desired-output}
bash launch_report.sh ./
```

Subsequently, open the reported link in your browser and...

1. Click 'Jovian_report.ipynb'
   1. When presented with popups click 'Trust'.
2. Via the toolbar, press the `Cell` and then the `Run all` button and wait for all data to be loaded. If you do not see the interactive spreadsheets, e.g. the "Classified scaffolds" section is empty, that means that you need to click the `Run all` button!
   1. This is a known bug, pull-requests are very welcome!

## Installation instructions

`Jovian` depends on the prerequisites described [here](#prerequisites) and can be [downloaded](#download) and [installed](#installation) afterwards. After the installation, required databases can be downloaded as described [here](#databases).  

The workflow will update itself to the latest version automatically. This makes it easier for everyone to use the latest available version without having to manually check the GitHub releases. If you wish to run Jovian without the updater checking for a new release, then add the `--skip-updates` flag to your command. in this case you wil ___not___ be notified if there is a new release available.  

### Prerequisites

1. Before you download and install Jovian, please make sure [Conda](https://docs.conda.io/projects/conda/en/latest/index.html) is installed on your system and functioning properly! Otherwise, install it via [these instuctions](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html). Conda is required to build the "main" environment and contains all required dependencies.
2. Jovian is intended for usage with `singularity`, that is the only way we can properly validate functionality of the code and it helps reduce maintenance. As such, please make sure [Singularity](https://sylabs.io/singularity/), and its dependency [Go](https://go.dev/) are installed properly. Otherwise, install it via [these instructions](https://docs.sylabs.io/guides/3.1/user-guide/installation.html). Singularity is used to build all sub-units of the pipeline.

### Download

Use the following command to download the latest release of Jovian and move to the newly downloaded `jovian/` directory:

```bash
git clone https://github.com/DennisSchmitz/jovian; cd jovian
```

### Installation

First, make sure you are in the root folder of the Jovian repo. If you followed the instructions above, this is the case.  

01. Install the proper dependencies using `conda create --name Jovian -c conda-forge mamba python=3.9 -y; conda activate Jovian; mamba env update -f mamba-env.yml; conda deactivate`  
02. Build the Python package via `conda activate Jovian; pip install .`
03. `Jovian` uses `singularity` by default, this must be installed on your computer or on your HPC by your system-admin. Alternatively, use the `--conda` flag to use `conda`, but only the `singularity` option is validated and supported.  
04. Follow the steps described in the [databases](#databases) section.
05. Jovian is now installed! You can verify the installation by running `Jovian -h` or `Jovian -v` which should return the help-document or installed version respectively. You can start Jovian from anywhere on your system as long as the Jovian conda-environment is active. If this environment isn't active you can activate it with `conda activate Jovian`.  

### Databases

Several databases are required before you can use `Jovian` for metagenomics analyses. These are listed below. Please note, these steps requires `Singularity` to be installed as described in the [installation](#installation) section. Importantly, take note of the [considerations](#considerations) listed below.  

**NB, for people from the RIVM working on the in-house grid-computer, the following steps have already been performed for you.**

You can download a set of default databases using the `--install-databases` flag as shown below. During installation it will ask you a basepath, i.e. the directory where the databases will be stored on your system, and it will ask you to select one of the available database timestamps for the `nt` and `taxdb` databases.

```bash
jovian --install-databases
```

#### Considerations

1. The databases are quite large and can take a while to download; at the time of writing (August, 2024) they require ~500GB of storage. Make sure you have sufficient storage available.
2. This installs a default set of databases that will work for general metagenomic analyses in public health or clinical settings. However, depending on your experimental setup you may want to use different databases. For example, if you are performing a metagenomic analysis of mollusc bioaccumilation samples, or, viruses cultured on, e.g., a golden hamster cell line, then you would care less about the GDPR and removal of the human genome and would want to use an appropriate background genome instead via the `--background` flag. This would speed up your analysis.
3. Depending on your study it might be wise to update the databases weekly, e.g. via `crontab`. Conversely, during a longitudinal study you might want to keep the databases fixed to ensure comparability of samples.  

## Citation

Please cite this paper as follows:

```text
#TODO update after publication
```

## Funding

This study was financed under European Union’s Horizon H2020 grants COMPARE and VEO (grant no. 643476 and 874735) and the NWO Stevin prize (Koopmans).

__Layout of this README was made using [BioSchemas' Computational Workflow schema](https://bioschemas.org/types/ComputationalWorkflow/1.0-RELEASE) as a guideline__
