# pylint: disable=C0103.C0301

"""
Basic functions for various uses throughout Jovian
"""

import argparse
import glob
import os
import readline
import shutil

from Jovian import __package_dir__


class MyHelpFormatter(argparse.RawTextHelpFormatter):
    """
    This is a custom formatter class for argparse. It allows for some custom formatting,
    in particular for the help texts with multiple options (like bridging mode and verbosity level).
    http://stackoverflow.com/questions/3853722
    """

    def __init__(self, prog):
        terminal_width = shutil.get_terminal_size().columns
        os.environ["COLUMNS"] = str(terminal_width)
        max_help_position = min(max(24, terminal_width // 2), 80)
        super().__init__(prog, max_help_position=max_help_position)

    def _get_help_string(self, action):
        help_text = action.help
        if action.default != argparse.SUPPRESS and "default" not in help_text.lower() and action.default is not None:
            help_text += f" (default: {str(action.default)})"
        return help_text


class color:
    """
    define basic colors to use in the terminal
    """

    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


# tabCompleter Class taken from https://gist.github.com/iamatypeofwalrus/5637895
## this was intended for the raw_input() function of python. But that one is deprecated now
## this also seems to work for the new input() functions however so muy bueno
#! use the gnureadline module instead of readline module
##! the 'normal' readline module causes a bug with memory pointers
##! --> https://stackoverflow.com/questions/43013060/python-3-6-1-crashed-after-i-installed-readline-module
class tabCompleter:
    """
    A tab completer that can either complete from
    the filesystem or from a list.

    Partially taken from:
    http://stackoverflow.com/questions/5637124/tab-completion-in-pythons-raw-input
    """

    def pathCompleter(self, text, state):
        """
        This is the tab completer for systems paths.
        Only tested on *nix systems
        """
        line = readline.get_line_buffer().split()

        # replace ~ with the user's home dir. See https://docs.python.org/2/library/os.path.html
        if "~" in text:
            text = os.path.expanduser("~")

        # autocomplete directories with having a trailing slash
        if os.path.isdir(text):
            text += "/"

        return list(glob.glob(f"{text}*"))[state]

    def createListCompleter(self, ll):
        """
        This is a closure that creates a method that autocompletes from
        the given list.

        Since the autocomplete function can't be given a list to complete from
        a closure is used to create the listCompleter function with a list to complete
        from.
        """

        def listCompleter(text, state):
            line = readline.get_line_buffer()

            if not line:
                return [f"{c} " for c in ll][state]

            return [f"{c} " for c in ll if c.startswith(line)][state]

        self.listCompleter = listCompleter


def get_max_local_mem():
    mem = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    return int(round(mem / (1024.0**2) - 2000, -3))


class DefaultConfig:
    """
    This class is the wrapper class for the default config dictionary
    """

    config = {
        "local": {
            "cores": 12,
            "latency-wait": 60,
            "use-conda": False,
            "use-singularity": True,
            "singularity-args": "",
            "dryrun": False,
            "printshellcmds": False,  # ? For debugging only
            "printreason": False,  # ? For debugging only
            "jobname": "Jovian_{name}.{jobid}",
        },
        "grid": {
            "cores": 300,
            "latency-wait": 60,
            "use-conda": False,
            "use-singularity": True,
            "singularity-args": "",
            "dryrun": False,
            "printshellcmds": False,  # ? For debugging only
            "printreason": False,  # ? For debugging only
            "jobname": "Jovian_{name}.{jobid}",
            "drmaa": ' -q PLACEHOLDER -n {threads} -R "span[hosts=1]" -M {resources.mem_mb}',  # ? PLACEHOLDER will be replaced by queuename supplied in CLI; default = "bio"
            "drmaa-log-dir": "logs/drmaa",
            "cluster": "sbatch -p PLACEHOLDER --parsable -N1 -n1 -c{threads} --mem={resources.mem_mb} -D . -o logs/SLURM/Jovian_{name}-{jobid}.out -e logs/SLURM/Jovian_{name}-{jobid}.err",  # ? PLACEHOLDER will be replaced by queuename supplied in CLI; default = "bio"
            "cluster-status": f"{__package_dir__}/workflow/scripts/slurm-cluster-status.py",
        },
    }
    params = {
        "sample_sheet": "samplesheet.yaml",
        "threads": {
            "Alignments": 12,
            "Filter": 6,
            "Assemble": 14,
            "MultiQC": 1,
            "align_to_scaffolds_RmDup_FragLength": 4,
            "SNP_calling": 12,
            "ORF_analysis": 1,
            "Contig_metrics": 1,
            "GC_content": 1,
            "Scaffold_classification": 12,
            "mgkit_lca": 1,
            "data_wrangling": 1,
            "krona": 1,
        },
        "computing_execution": "grid",
        "use_singularity_or_conda": "use_singularity",
        "max_local_mem": get_max_local_mem(),
        "QC": {
            "min_phred_score": 20,  # ? this is overwritten by the value supplied in the wrapper CLI
            "window_size": 5,
            "min_read_length": 50,  # ? this is overwritten by the value supplied in the wrapper CLI
        },
        "Assembly": {
            "min_contig_len": 250,  # ? this is overwritten by the value supplied in the wrapper CLI
            "kmersizes": "21,33,55,77",
        },
        "db": {  # ? These are set either by the defaults listed below or the user-specified path, see WriteConfigs()
            "background": "",
            "blast_nt": "",
            "blast_taxdb": "",
            "mgkit_db": "",
            "krona_db": "",
            "virus_host_db": "",
            "new_taxdump_db": "",
        },
        "db_defaults_local": {
            "background": "/mnt/db/Jov2/HuGo_GRCh38_NoDecoy_NoEBV/genome.fa",
            "blast_nt": "/mnt/db/Jov2/NT_database/nt",
            "blast_taxdb": "/mnt/db/Jov2/taxdb/",
            "mgkit_db": "/mnt/db/Jov2/mgkit_db/",
            "krona_db": "/mnt/db/Jov2/krona_db/",
            "virus_host_db": "/mnt/db/Jov2/virus_host_db/virushostdb.tsv",
            "new_taxdump_db": "/mnt/db/Jov2/new_taxdump/",
        },
        "db_defaults_grid": {
            "background": "/data/BioGrid/schmitzd/20220428_databases_jov2/HuGo_GRCh38_NoDecoy_NoEBV/genome.fa",
            "blast_nt": "/data/BioGrid/schmitzd/20220428_databases_jov2/NT_database/nt",
            "blast_taxdb": "/data/BioGrid/schmitzd/20220428_databases_jov2/taxdb/",
            "mgkit_db": "/data/BioGrid/schmitzd/20220428_databases_jov2/mgkit_db/",
            "krona_db": "/data/BioGrid/schmitzd/20220428_databases_jov2/krona_db/",
            "virus_host_db": "/data/BioGrid/schmitzd/20220428_databases_jov2/virus_host_db/virushostdb.tsv",
            "new_taxdump_db": "/data/BioGrid/schmitzd/20220428_databases_jov2/new_taxdump/",
        },
    }
