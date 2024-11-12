from setuptools import find_packages
from setuptools import setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="plus-coder",
    version="2.3.0",
    install_requires=required,
    package_data={"pluscoder": ["*.py", "*.so"]},
    packages=find_packages(include=["pluscoder", "pluscoder*"]),
    entry_points={
        "console_scripts": [
            "pluscoder=pluscoder.main:main",
        ],
    },
    include_package_data=True,
)
