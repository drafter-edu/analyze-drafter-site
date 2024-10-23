"""Python setup.py for analyze_drafter_site package"""
import io
import os
from setuptools import find_packages, setup


def read(*paths, **kwargs):
    """Read the contents of a text file safely.
    >>> read("analyze_drafter_site", "VERSION")
    '0.1.0'
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path):
    return [
        line.strip()
        for line in read(path).split("\n")
        if not line.startswith(('"', "#", "-", "git+"))
    ]


setup(
    name="analyze_drafter_site",
    version=read("analyze_drafter_site", "VERSION"),
    description="Awesome analyze_drafter_site created by drafter-edu",
    url="https://github.com/drafter-edu/analyze-drafter-site/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="drafter-edu",
    packages=find_packages(exclude=["tests", ".github"]),
    install_requires=read_requirements("requirements.txt"),
    entry_points={
        "console_scripts": ["analyze_drafter_site = analyze_drafter_site.__main__:main"]
    },
    extras_require={"test": read_requirements("requirements-test.txt")},
)
