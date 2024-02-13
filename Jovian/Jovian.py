"""
Starting point of the Jovian metagenomic pipeline and wrapper
Authors:
    Dennis Schmitz, Florian Zwagemaker, Sam Nooij, Robert Verhagen,
    Karim Hajji, Jeroen Cremer, Thierry Janssens, Mark Kroon, Erwin
    van Wieringen, Harry Vennema, Miranda de Graaf, Annelies Kroneman,
    Jeroen Laros, Marion Koopmans
Organization:
    Rijksinstituut voor Volksgezondheid en Milieu (RIVM)
    Dutch Public Health institute (https://www.rivm.nl/en)
    Erasmus Medical Center (EMC) Rotterdam (https://www.erasmusmc.nl/en)
Departments:
    RIVM Virology, RIVM Bioinformatics, EMC Viroscience
Date and license:
    2018 - present, AGPL3 (https://www.gnu.org/licenses/agpl-3.0.en.html)
Homepage containing documentation, examples and changelog:
    https://github.com/DennisSchmitz/jovian
Funding:
    This project/research has received funding from the European Union's
    Horizon 2020 research and innovation programme under grant agreement
    No. 643476.
Automation:
    iRODS automatically executes this workflow for the "vir-ngs" project
"""

import argparse
import multiprocessing
import os
import pathlib
import sys

import snakemake
import yaml

from Jovian import __home_env_configuration__, __package_name__, __version__
from Jovian.functions import MyHelpFormatter, color
from Jovian.runconfigs import WriteConfigs
from Jovian.samplesheet import WriteSampleSheet
from Jovian.update import update

yaml.warnings({"YAMLLoadWarning": False})


def get_args(givenargs):
    """
    Parse the command line arguments
    """

    def dir_path(arginput):
        if os.path.isdir(arginput):
            return arginput
        print(f'"{arginput}" is not a directory. Exiting...')
        sys.exit(1)

    def currentpath():
        return os.getcwd()

    arg = argparse.ArgumentParser(
        prog=__package_name__,
        usage="%(prog)s [required arguments] [optional arguments]",
        description="%(prog)s: a metagenomic analysis workflow for public health and clinics with interactive reports in your web-browser\n\n"
        + "NB default database paths are hardcoded for RIVM users, otherwise, specify your own database paths using the optional arguments.\n"
        + "On subsequent invocations of %(prog)s, the database paths will be read from the file located at: "
        + __home_env_configuration__
        + " and you will not have to provide them again.\n"
        + "Similarly, the default RIVM queue is provided as a default value for the '--queuename' flag, but you can override this value if you want to use a different queue.\n",
        formatter_class=MyHelpFormatter,
        add_help=False,
    )

    required_args = arg.add_argument_group("Required arguments")
    optional_args = arg.add_argument_group("Optional arguments")

    required_args.add_argument(
        "--input",
        "-i",
        type=dir_path,
        metavar="DIR",
        help="The input directory containing the raw fastq(.gz) files",
        required=True,
    )

    required_args.add_argument(
        "--output",
        "-o",
        metavar="DIR",
        type=str,
        default=currentpath(),
        help="Output directory",
        required=True,
    )

    optional_args.add_argument(
        "--reset-db-paths",
        action="store_true",
        help="Reset the database paths to the default values",
    )

    optional_args.add_argument(
        "--background",
        type=str,
        metavar="File",
        help="Override the default human genome background path",
        required=False,
    )

    optional_args.add_argument(
        "--blast-db",
        type=str,
        metavar="Path",
        help="Override the default BLAST NT database path",
        required=False,
    )

    optional_args.add_argument(
        "--blast-taxdb",
        type=str,
        metavar="Path",
        help="Override the default BLAST taxonomy database path",
        required=False,
    )

    optional_args.add_argument(
        "--mgkit-db",
        type=str,
        metavar="Path",
        help="Override the default MGKit database path",
        required=False,
    )

    optional_args.add_argument(
        "--krona-db",
        type=str,
        metavar="Path",
        help="Override the default Krona database path",
        required=False,
    )

    optional_args.add_argument(
        "--virus-host-db",
        type=str,
        metavar="File",
        help="Override the default virus-host database path (https://www.genome.jp/virushostdb/)",
        required=False,
    )

    optional_args.add_argument(
        "--new-taxdump-db",
        type=str,
        metavar="Path",
        help="Override the default new taxdump database path",
        required=False,
    )

    optional_args.add_argument(
        "--version",
        "-v",
        version=__version__,
        action="version",
        help="Show %(prog)s version and exit",
    )

    optional_args.add_argument(
        "--help",
        "-h",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit",
    )

    optional_args.add_argument("--skip-updates", action="store_true", help="Skip the update check")

    optional_args.add_argument(
        "--local",
        action="store_true",
        help="Use %(prog)s locally instead of in a grid-computing configuration",
    )

    optional_args.add_argument(
        "--slurm",
        action="store_true",
        help="Use SLURM instead of the default DRMAA for grid execution (default: DRMAA)",
    )

    optional_args.add_argument(
        "--queuename",
        default="bio",
        type=str,
        metavar="NAME",
        help="Name of the queue to use for grid execution (default: bio)",
    )

    optional_args.add_argument(
        "--conda",
        action="store_true",
        help="Use conda environments instead of the default singularity images (default: False)",
    )

    optional_args.add_argument(
        "--dryrun",
        action="store_true",
        help="Run the %(prog)s workflow without actually doing anything to confirm that the workflow will run as expected",
    )

    optional_args.add_argument(
        "--threads",
        default=min(multiprocessing.cpu_count(), 128),
        type=int,
        metavar="N",
        help=f"Number of local threads that are available to use.\nDefault is the number of available threads in your system ({min(multiprocessing.cpu_count(), 128)})",
    )

    optional_args.add_argument(
        "--minphredscore",
        default=20,
        type=int,
        metavar="N",
        help="Minimum phred score to be used for QC trimming (default: 20)",
    )

    optional_args.add_argument(
        "--minreadlength",
        default=50,
        type=int,
        metavar="N",
        help="Minimum read length to used for QC trimming (default: 50)",
    )

    optional_args.add_argument(
        "--mincontiglength",
        default=250,
        type=int,
        metavar="N",
        help="Minimum contig length to be analysed and included in the final output (default: 250)",
    )

    if len(givenargs) < 1:
        print(f"{arg.prog} was called but no arguments were given, please try again \n\tUse '{arg.prog} -h' to see the help document")
        sys.exit(1)
    else:
        flags = arg.parse_args(givenargs)
    return flags


def CheckInputFiles(indir):
    """
    Check if the input files are valid fastq files
    """
    allowedextensions = [".fastq", ".fq", ".fastq.gz", ".fq.gz"]
    foundfiles = []

    for filenames in os.listdir(indir):
        extensions = "".join(pathlib.Path(filenames).suffixes)
        foundfiles.append(extensions)

    return any((i in allowedextensions for i in foundfiles))


def main():
    """
    Jovian starting point
    """

    flags = get_args(sys.argv[1:])

    if flags.reset_db_paths:
        os.remove(__home_env_configuration__)
        sys.exit(f'Removed "{__home_env_configuration__}", database paths are now reset. Exiting...')

    if not flags.skip_updates:
        update(sys.argv)

    inpath = os.path.abspath(flags.input)
    outpath = os.path.abspath(flags.output)
    exec_folder = os.path.abspath(os.path.dirname(__file__))

    Snakefile = os.path.join(exec_folder, "workflow", "Snakefile")

    if CheckInputFiles(inpath) is False:
        print(
            f"""
{color.RED + color.BOLD}"{inpath}" does not contain any valid FastQ files.{color.END}
Please check the input directory and try again. Exiting...
            """
        )
        sys.exit(1)
    else:
        print(
            f"""
{color.GREEN}Valid input files were found in the input directory{color.END} ('{inpath}')
            """
        )
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    if os.getcwd() != outpath:
        os.chdir(outpath)
    workdir = outpath

    samplesheet = WriteSampleSheet(inpath)

    paramfile, _conffile, _paramdict, confdict = WriteConfigs(
        samplesheet,
        flags.threads,
        flags.queuename,
        os.getcwd(),
        flags.local,
        flags.minphredscore,
        flags.minreadlength,
        flags.mincontiglength,
        flags.conda,
        flags.background,
        flags.blast_db,
        flags.blast_taxdb,
        flags.mgkit_db,
        flags.krona_db,
        flags.virus_host_db,
        flags.new_taxdump_db,
        flags.dryrun,
        inpath,
    )

    # Snakemake command and params for "local" execution
    if flags.local is True:
        status = snakemake.snakemake(
            Snakefile,
            workdir=workdir,
            conda_frontend="conda",  # TODO had to change frontend from `mamba` to `conda`, for some reason the installation of `Sequence_analysis.yaml` is incompatible with the `mamba` frontend... Works fine in `singularity` though...
            cores=confdict["cores"],
            use_conda=confdict["use-conda"],
            use_singularity=confdict["use-singularity"],
            singularity_args=confdict["singularity-args"],
            jobname=confdict["jobname"],
            latency_wait=confdict["latency-wait"],
            dryrun=confdict["dryrun"],
            printshellcmds=confdict["printshellcmds"],
            printreason=confdict["printreason"],
            configfiles=[paramfile],
            restart_times=3,
        )
    # Snakemake command and params for "grid" execution
    if flags.local is False and flags.slurm is False:
        status = snakemake.snakemake(
            Snakefile,
            workdir=workdir,
            conda_frontend="conda",  # TODO had to change frontend from `mamba` to `conda`, for some reason the installation of `Sequence_analysis.yaml` is incompatible with the `mamba` frontend... Works fine in `singularity` though...
            cores=confdict["cores"],
            nodes=confdict["cores"],
            use_conda=confdict["use-conda"],
            use_singularity=confdict["use-singularity"],
            singularity_args=confdict["singularity-args"],
            jobname=confdict["jobname"],
            latency_wait=confdict["latency-wait"],
            drmaa=confdict["drmaa"],
            drmaa_log_dir=confdict["drmaa-log-dir"],
            dryrun=confdict["dryrun"],
            printshellcmds=confdict["printshellcmds"],
            printreason=confdict["printreason"],
            configfiles=[paramfile],
            restart_times=3,
        )

    # Snakemake command and params for "grid" execution but using SLURM instead of DRMAA
    if flags.local is False and flags.slurm is True:
        status = snakemake.snakemake(
            Snakefile,
            workdir=workdir,
            conda_frontend="conda",  # TODO had to change frontend from `mamba` to `conda`, for some reason the installation of `Sequence_analysis.yaml` is incompatible with the `mamba` frontend... Works fine in `singularity` though...
            cores=confdict["cores"],
            nodes=confdict["cores"],
            use_conda=confdict["use-conda"],
            use_singularity=confdict["use-singularity"],
            singularity_args=confdict["singularity-args"],
            jobname=confdict["jobname"],
            latency_wait=confdict["latency-wait"],
            cluster=confdict["cluster"],
            cluster_status=confdict["cluster-status"],
            dryrun=confdict["dryrun"],
            printshellcmds=confdict["printshellcmds"],
            printreason=confdict["printreason"],
            configfiles=[paramfile],
            restart_times=3,
        )

    # Snakemake command for making the snakemake report only
    if confdict["dryrun"] is False and status is True:
        snakemake.snakemake(
            Snakefile,
            workdir=workdir,
            report="results/snakemake_report.html",
            configfiles=[paramfile],
            quiet=True,
        )
