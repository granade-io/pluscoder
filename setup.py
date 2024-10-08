from setuptools import find_packages, setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

# with open("requirements-dev.txt") as f:
#     dev_requirements = f.read().splitlines()

setup(
    name="plus-coder",
    version="0.1.0",
    install_requires=required,
    # extras_require={
    #     "dev": dev_requirements,
    # },
    packages=find_packages(include=["pluscoder", "pluscoder*"]),
    entry_points={
        "console_scripts": [
            "pluscoder=pluscoder.main:main",
        ],
    },
    include_package_data=True,
)
