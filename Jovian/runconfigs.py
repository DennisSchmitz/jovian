"""
Construct and write configuration files for Jovian.
"""

import multiprocessing
import os
import sys

import yaml

from Jovian import __home_env_configuration__

from .functions import DefaultConfig


def set_cores(cores: int) -> int:
    """
    Set the maximum (viable) number of cores to max - 2, allotting two threads for overhead
    """
    max_available = multiprocessing.cpu_count()
    return max_available - 2 if cores >= max_available else cores


def user_supplied_db_paths(background, blast_nt, blast_taxdb, mgkit_db, krona_db, virus_host_db, new_taxdump_db) -> None:
    """
    If user-supplied database paths are given, set them in DefaultConfig.params["db"]KEY

    Inputs of this function are the database paths as provided to the wrapper by the user.
    """
    #! When adding/removing database flags/path also update check_validity_db_paths()
    if background is not None:
        DefaultConfig.params["db"]["background"] = background
    if blast_nt is not None:
        DefaultConfig.params["db"]["blast_nt"] = blast_nt
    if blast_taxdb is not None:
        DefaultConfig.params["db"]["blast_taxdb"] = blast_taxdb
    if mgkit_db is not None:
        DefaultConfig.params["db"]["mgkit_db"] = mgkit_db
    if krona_db is not None:
        DefaultConfig.params["db"]["krona_db"] = krona_db
    if virus_host_db is not None:
        DefaultConfig.params["db"]["virus_host_db"] = virus_host_db
    if new_taxdump_db is not None:
        DefaultConfig.params["db"]["new_taxdump_db"] = new_taxdump_db


def write_user_supplied_db_paths_to_home_dir_env() -> None:
    """
    DefaultConfig.params["db"] is non-empty if the user supplied database paths, so, store non-empty
    values permanently in a hidden configuration YAML file in the user's HOME so they do not have to
    supply it each time they run the wrapper.
    """
    db_paths = {key: value for key, value in DefaultConfig.params["db"].items() if value}
    with open(__home_env_configuration__, "w", encoding="utf-8") as yaml_file:
        yaml.dump(db_paths, yaml_file, default_flow_style=False)


def set_db_paths(local: bool) -> None:
    """
    If no user-supplied database paths are given (user_supplied_db_paths()) nor have they have been
    stored in the config file in the user's home-dir (write_user_supplied_db_paths_to_home_dir_env()),
    set default paths for local or grid-computation from DefaultConfig.params["db_defaults_local"]
    and DefaultConfig.params["db_defaults_grid"], respectively. NB defaults are configured for usage
    with default RIVM paths.

    local = boolean, was `--local` flag invoked or not, i.e. local or grid execution
    """
    if os.path.exists(__home_env_configuration__):
        with open(__home_env_configuration__, "r", encoding="utf-8") as yaml_file:
            previously_stored_db_paths = yaml.safe_load(yaml_file)

        # ? If db-paths were previously stored, update the DefaultConfig.params["db"] dictionary with these paths, then they are not overwritten with the RIVMs default paths downstream since they are not empty
        if previously_stored_db_paths and isinstance(previously_stored_db_paths, dict):
            for key, value in previously_stored_db_paths.items():
                if key in DefaultConfig.params["db"]:
                    DefaultConfig.params["db"][key] = value

    for key in DefaultConfig.params["db"].keys():
        if not DefaultConfig.params["db"][key]:
            if local:  # ? Set local compute default paths if empty, i.e. no user-supplied path
                DefaultConfig.params["db"][key] = DefaultConfig.params["db_defaults_local"][key]
            else:  # ? Set grid compute default paths if empty, i.e. no user-supplied path
                DefaultConfig.params["db"][key] = DefaultConfig.params["db_defaults_grid"][key]


def check_validity_db_paths() -> None:
    """
    Check if all the database root folders exist and/or files exist. Exit if not true.
    """
    #! When adding/removing database flags/path also update user_supplied_db_paths()
    try:
        for filename in [DefaultConfig.params["db"]["background"], DefaultConfig.params["db"]["virus_host_db"]]:
            if not os.path.exists(filename):
                raise FileNotFoundError(filename)
        for filepath in [
            DefaultConfig.params["db"]["blast_nt"],
            DefaultConfig.params["db"]["blast_taxdb"],
            DefaultConfig.params["db"]["krona_db"],
            DefaultConfig.params["db"]["new_taxdump_db"],
            DefaultConfig.params["db"]["mgkit_db"],
        ]:
            if not os.path.exists(os.path.dirname(filepath)):
                raise FileNotFoundError(filepath)
    except FileNotFoundError as error_message:
        sys.exit(f"This file or folder is not available or accessible: {error_message}\nExiting...")


def WriteConfigs(
    samplesheet,
    cores,
    queuename,
    cwd,
    local,
    minphredscore,
    minreadlength,
    mincontiglength,
    conda,
    background,
    blast_nt,
    blast_taxdb,
    mgkit_db,
    krona_db,
    virus_host_db,
    new_taxdump_db,
    dryrun,
    inpath,
):
    """
    Write the config files needed for proper functionality. Includes
    database paths, singularity binds, --local mode core-counts, etc.
    are all set here.
    """

    def use_conda(configuration: dict, parameter: dict) -> None:
        "Use conda instead of Singularity; not recommended, only for debug purposes"
        configuration["use-conda"] = True
        configuration["use-singularity"] = False
        parameter["use_singularity_or_conda"] = "use_conda"

    def update_queuename(configuration: dict, queuename: str) -> None:
        "Update the queuename in the configuration file with the user-supplied queuename"

        def update_queuename(key: str) -> None:
            value = configuration[key]
            value = value.replace("PLACEHOLDER", queuename)
            configuration[key] = value

        update_queuename("drmaa")
        update_queuename("cluster")

    def set_no_threads_local_mode(configuration: dict, parameter: dict) -> None:
        "Update the threads used per rule based on system specs. NB this is only needed for --local mode"
        configuration["cores"] = set_cores(cores)
        parameter["computing_execution"] = "local"

    def setup_singularity_mountpoints() -> str:
        "Setup the singularity mount-points and returns this as a _single_ big string used to update config file"
        # ? Bind the necessary folders to the singularity containers. Including Jovian's scripts/ and files/ folders, but also the input directory and reference basepath supplied by the user through the wrapper.
        # ? Line below makes an anchor, below this location you"ll find ./workflow/scripts/ and ./workflow/files/ as installed by pip. Anchor to: `**/conda/envs/[PACKAGE_NAME]/lib/python3.7/site-packages/[PACKAGE_NAME]/`
        exec_folder = os.path.abspath(os.path.dirname(__file__))
        scripts_folder = os.path.join(exec_folder, "workflow/", "scripts/")
        files_folder = os.path.join(exec_folder, "workflow/", "files/")

        # ! This is a single big string split over multiple lines, not a list
        singularity_mount_points = (
            f"--bind {scripts_folder}:/Jovian/scripts --bind {files_folder}:/Jovian/files --bind {inpath}:{inpath} "
            f"--bind {os.path.dirname(DefaultConfig.params['db']['background'])}:{os.path.dirname(DefaultConfig.params['db']['background'])} "
            f"--bind {os.path.dirname(DefaultConfig.params['db']['blast_nt'])}:{os.path.dirname(DefaultConfig.params['db']['blast_nt'])} "
            f"--bind {os.path.dirname(DefaultConfig.params['db']['blast_taxdb'])}:{os.path.dirname(DefaultConfig.params['db']['blast_taxdb'])} "
            f"--bind {os.path.dirname(DefaultConfig.params['db']['mgkit_db'])}:{os.path.dirname(DefaultConfig.params['db']['mgkit_db'])} "
            f"--bind {os.path.dirname(DefaultConfig.params['db']['krona_db'])}:{os.path.dirname(DefaultConfig.params['db']['krona_db'])} "
            f"--bind {os.path.dirname(DefaultConfig.params['db']['virus_host_db'])}:{os.path.dirname(DefaultConfig.params['db']['virus_host_db'])} "
            f"--bind {os.path.dirname(DefaultConfig.params['db']['new_taxdump_db'])}:{os.path.dirname(DefaultConfig.params['db']['new_taxdump_db'])}"
        )
        return singularity_mount_points

    # ? Make folder to store config and param files
    if not os.path.exists(f"{cwd}/config"):
        os.makedirs(f"{cwd}/config")

    # ! Below, update the parameters. I.e. values that are used by the Snakefile/rules itself
    parameter_dict = DefaultConfig.params  # ? Load default params, will be updated downstream
    parameter_dict["QC"]["min_phred_score"] = minphredscore  # ? Based on user supplied value
    parameter_dict["QC"]["min_read_length"] = minreadlength  # ? Based on user supplied value
    parameter_dict["Assembly"]["min_contig_len"] = mincontiglength  # ? Based on user supplied value
    # ? set proper database paths, if none are given by the user, set default paths based on grid or local compute mode
    user_supplied_db_paths(background, blast_nt, blast_taxdb, mgkit_db, krona_db, virus_host_db, new_taxdump_db)
    write_user_supplied_db_paths_to_home_dir_env()
    set_db_paths(local)
    check_validity_db_paths()

    # ! Below, update the configurations. I.e. values that are used by the Snakemake engine/wrapper itself
    singularity_mount_points = setup_singularity_mountpoints()  # ? setup singularity mountpoints based on installation location of this package

    # ! Load the configs specific to either local execution or grid execution
    if local is True:
        configuration_dict = DefaultConfig.config["local"]
        # ? The ` --bind /run/shm:/run/shm` addition is to make the Py multiprocessing of `lofreq` work, it requires write permissions to /run/shm. See similar issue here https://github.com/nipreps/fmriprep/issues/780
        DefaultConfig.config["local"]["singularity-args"] = f"{singularity_mount_points} --bind /run/shm:/run/shm"
        set_no_threads_local_mode(configuration_dict, parameter_dict)
    else:  # ! I.e. it will run in "grid" mode
        configuration_dict = DefaultConfig.config["grid"]
        update_queuename(configuration_dict, queuename)
        DefaultConfig.config["grid"]["singularity-args"] = singularity_mount_points

    # ! Configure configuration values that are independent on whether it's local or grid
    parameter_dict["sample_sheet"] = samplesheet  # ? Load sample_sheet
    if dryrun is True:
        configuration_dict["dryrun"] = True
    if conda is True:
        use_conda(configuration_dict, parameter_dict)

    # ! Write final config and params yaml files for audit-trail
    parameter_file_path = f"{cwd}/config/params.yaml"
    configuration_file_path = f"{cwd}/config/config.yaml"
    with open(parameter_file_path, "w", encoding="utf-8") as outfile:
        yaml.dump(parameter_dict, outfile, default_flow_style=False)
    with open(configuration_file_path, "w", encoding="utf-8") as outfile:
        yaml.dump(configuration_dict, outfile, default_flow_style=False)

    return parameter_file_path, configuration_file_path, parameter_dict, configuration_dict
