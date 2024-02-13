import sys

from packaging import version as vv
from setuptools import find_packages, setup

from Jovian import __package_name__, __version__

if sys.version_info.major != 3 or sys.version_info.minor < 6:
    print("Jovian requires Python 3.6 or higher")
    sys.exit(1)

try:
    import conda
except SystemError:
    sys.exit(
        """
Error: conda could not be accessed.
Please make sure conda is installed and functioning properly before installing Jovian
"""
    )


try:
    import snakemake
except SystemError:
    sys.exit(
        """
Error: snakemake could not be accessed.
Please make sure snakemake is installed and functioning properly before installing Jovian
"""
    )


if vv.parse(snakemake.__version__) < vv.parse("6.0"):
    sys.exit(
        f"""
The installed SnakeMake version is older than the minimally required version:

Installed SnakeMake version: {snakemake.__version__}
Required SnakeMake version: 6.0 or later

Please update SnakeMake to a supported version and try again
"""
    )

# TODO this isn't used.
with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name=__package_name__,
    author="Dennis Schmitz",
    author_email="DennisSchmitz@users.noreply.github.com",
    url="https://github.com/DennisSchmitz/jovian",
    license="AGPLv3",
    version=__version__,
    packages=find_packages(),
    scripts=["Jovian/workflow/Snakefile", "Jovian/workflow/directories.py"],
    package_data={"Jovian": ["workflow/envs/*", "workflow/scripts/*", "workflow/scripts/html/*", "workflow/files/*", "workflow/files/html/*"]},
    install_requires=["drmaa==0.7.9", "pyyaml==6.0", "biopython==1.79"],
    entry_points={
        "console_scripts": [
            "jovian = Jovian.Jovian:main",
            "Jovian = Jovian.Jovian:main",
        ]
    },
    keywords=[],
    include_package_data=True,
    zip_safe=False,
)
