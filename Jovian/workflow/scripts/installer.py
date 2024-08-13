"""
Installer of a default setup of databases required for Jovian.
    NB, end-users are responsible for proper versioning of databases,
    whether these databases align with their experimental design/goals
    and the whether these databases are automatically updated.
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
import contextlib
import os
import subprocess
import sys

import yaml

from Jovian import __home_env_configuration__


def cli_args(given_args: list[str]) -> argparse.Namespace:
    "Parse the CLI arguments using argparse"
    parser = argparse.ArgumentParser(description="Automate the setup of databases that Jovian requires.")

    parser.add_argument(
        "-b",
        "--basepath",
        action="store",
        type=str,
        metavar="DIR",
        required=True,
        help="Base path where all databases will be downloaded, will be made if it does not exist.",
    )

    parser.add_argument(
        "-t",
        "--timestamp",
        action="store",
        type=str,
        metavar="timestamp",
        required=True,
        help="Timestamp required for the NCBI nt and taxdb databases. List available time-stamps with `aws s3 ls --no-sign-request s3://ncbi-blast-databases/`, e.g., `2024-07-20-01-05-03`.",
    )

    if given_args:
        return parser.parse_args(given_args)
    print("Trying to install databases, but no arguments were given. Exiting...")
    sys.exit(1)


def run_commands(commands):
    """Run a bash command or a list of bash commands."""
    try:
        if isinstance(commands, list):
            for cmd in commands:
                subprocess.run(cmd, shell=True, check=True)
        else:
            subprocess.run(commands, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def make_database_dir_and_move_there(base_path, database_name) -> str:
    "Make a dir based on base_path and database_name and move to this path. Returns the path as str."
    full_path = os.path.join(base_path, database_name)
    os.makedirs(full_path, exist_ok=True)
    os.chdir(full_path)
    return full_path


def main(args=sys.argv[1:]):
    """
    Installer of a default setup of databases required for Jovian.
    NB, end-users are responsible for proper versioning of databases,
    whether these databases align with their experimental design/goals
    and the whether these databases are automatically updated.
    """
    args = cli_args(args)

    base_path = os.path.abspath(args.basepath)
    timestamp = args.timestamp

    # ? DEBUG ONLY, uncomment this block and comment all the commands blocks below to test the installer
    # commands = [
    #     "echo $PWD",
    #     "touch test.txt",
    # ]

    print("Installer started...")

    # 1. Set up the Krona database
    print("\tKrona database setup...")
    krona_path = make_database_dir_and_move_there(base_path, "krona_db")
    commands = [
        "singularity pull --arch amd64 library://ds_bioinformatics/jovian/krona:2.0.0",
        'singularity exec --bind "${PWD}" krona_2.0.0.sif bash /opt/conda/opt/krona/updateTaxonomy.sh ./',
        'singularity exec --bind "${PWD}" krona_2.0.0.sif bash /opt/conda/opt/krona/updateAccessions.sh ./',
        "rm krona_2.0.0.sif",
    ]
    run_commands(commands)

    # 2a. Download the NCBI nt and taxdb databases (NB, timestamp between nt and taxdb must be identical)
    print("\tNT database setup...")
    nt_path = make_database_dir_and_move_there(base_path, "nt")
    commands = [
        f'aws s3 sync --no-sign-request s3://ncbi-blast-databases/{timestamp}/ . --exclude "*" --include "nt.*"',
    ]
    run_commands(commands)

    # 2b. Set up the NCBI taxdb database  (NB, timestamp between nt and taxdb must be identical)
    print("\tTaxDB database setup...")
    taxdb_path = make_database_dir_and_move_there(base_path, "taxdb")
    commands = [
        f'aws s3 sync --no-sign-request s3://ncbi-blast-databases/{timestamp}/ . --exclude "*" --include "taxdb*"',
    ]
    run_commands(commands)

    # 3. Set up mgkit and download taxonomy
    print("\tMgkit database setup...")
    mgkit_path = make_database_dir_and_move_there(base_path, "mgkit")
    commands = [
        "singularity pull --arch amd64 library://ds_bioinformatics/jovian/mgkit_lca:2.0.0",
        'singularity exec --bind "${PWD}" mgkit_lca_2.0.0.sif download-taxonomy.sh',
        "rm taxdump.tar.gz",
        "wget -O nucl_gb.accession2taxid.gz ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz",
        "wget -O nucl_gb.accession2taxid.gz.md5 https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/accession2taxid/nucl_gb.accession2taxid.gz.md5",
        "md5sum -c nucl_gb.accession2taxid.gz.md5",
        "gunzip -c nucl_gb.accession2taxid.gz | cut -f2,3 > nucl_gb.accession2taxid_sliced.tsv",
        "rm nucl_gb.accession2taxid.gz*",
        "rm mgkit_lca_2.0.0.sif",
    ]
    run_commands(commands)

    # 4. Download the Virus-Host DB
    print("\tVirus-host database setup...")
    virus_host_db_path = make_database_dir_and_move_there(base_path, "virus_host_db")
    commands = "wget -O virushostdb.tsv ftp://ftp.genome.jp/pub/db/virushostdb/virushostdb.tsv"
    run_commands(commands)

    # 5. Download and process the new taxdump
    print("\tNew_taxdump database setup...")
    new_taxdump_path = make_database_dir_and_move_there(base_path, "new_taxdump")
    commands = [
        "wget -O new_taxdump.tar.gz https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz",
        "wget -O new_taxdump.tar.gz.md5 https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz.md5",
        'if md5sum -c new_taxdump.tar.gz.md5; then tar -xzf new_taxdump.tar.gz; for file in *.dmp; do gawk \'{gsub("\\t"," "); if(substr($0,length($0),length($0))=="|") print substr($0,0,length($0)-1); else print $0}\' < ${file} > ${file}.delim; done; else echo "The md5sum does not match new_taxdump.tar.gz! Please try downloading again."; fi',
    ]
    run_commands(commands)

    # 6. Set up the HuGo database
    print("\tHuGo database setup...")
    hugo_path = make_database_dir_and_move_there(base_path, "HuGo")
    commands = [
        'aws s3 --no-sign-request --region eu-west-1 sync s3://ngi-igenomes/igenomes/Homo_sapiens/NCBI/GRCh38/Sequence/WholeGenomeFasta/ ./ --exclude "*" --include "genome.fa*"',
        "gawk '{print >out}; />chrEBV/{out=\"EBV.fa\"}' out=temp.fa genome.fa; head -n -1 temp.fa > nonEBV.fa; rm EBV.fa temp.fa; mv nonEBV.fa genome.fa",
        "singularity pull --arch amd64 library://ds_bioinformatics/jovian/qc_and_clean:2.0.0",
        'singularity exec --bind "${PWD}" qc_and_clean_2.0.0.sif bowtie2-build --threads 8 genome.fa genome.fa',
        "rm qc_and_clean_2.0.0.sif",
    ]
    run_commands(commands)

    print("Installer finished...")

    # based on runconfigs.py default suffixes
    database_paths = {
        "db": {
            "background": f"{hugo_path}/genome.fa",
            "blast_nt": f"{nt_path}/nt",
            "blast_taxdb": f"{taxdb_path}/",
            "mgkit_db": f"{mgkit_path}/",
            "krona_db": f"{krona_path}/",
            "virus_host_db": f"{virus_host_db_path}/virushostdb.tsv",
            "new_taxdump_db": f"{new_taxdump_path}/",
        }
    }

    # store the paths of the newly installed databases in __home_env_configuration__
    with contextlib.suppress(FileNotFoundError):
        os.remove(__home_env_configuration__)  # remove old versions and overwrite with new, ignore if not present
    db_paths = {key: value for key, value in database_paths["db"].items() if value}

    with open(__home_env_configuration__, "w", encoding="utf-8") as yaml_file:
        yaml.dump(db_paths, yaml_file, default_flow_style=False)


if __name__ == "__main__":
    main(sys.argv[1:])
