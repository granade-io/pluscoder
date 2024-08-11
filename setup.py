from setuptools import setup, find_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="plus-coder",
    version="0.1.0",
    install_requires=required,
    packages=find_packages(include=["pluscoder", "pluscoder*"]),
    entry_points={
        "console_scripts": [
            "plus-coder=pluscoder:main.main",
        ],
    },
    include_package_data=True,
)