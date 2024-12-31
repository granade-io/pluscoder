import os

from setuptools import find_packages
from setuptools import setup

with open("requirements.txt") as f:
    required = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pluscoder",
    version=os.getenv("NEXT_VERSION", "0.1.0"),
    author="Granade.io",
    author_email="contact@granade.io",
    description="AI-assisted software development tool for streamlining development process",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/codematos/pluscoder",
    install_requires=required,
    packages=find_packages(include=["pluscoder", "pluscoder.*"]),
    include_package_data=True,
    package_data={
        "pluscoder": ["**/*.py", "assets/*.json"],
    },
    entry_points={
        "console_scripts": [
            "pluscoder=pluscoder.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    license="GPL-3.0",
    license_files=["LICENSE"],
)
