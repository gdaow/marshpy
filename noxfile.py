"""Nox configuration file"""
from os import fsdecode
from pathlib import Path

import nox
from nox import Session

nox.options.sessions = ["checks"]

LINT_PATHS = ["marshpy", "tests"]
PYTEST_PACKAGES = ["pytest", "pytest-cov", "pytest-datadir"]
DEV_DEPENDENCIES = PYTEST_PACKAGES + ["mypy", "pylint", "flake8", "isort"]
VENV_DIR = Path(".venv")


@nox.session(python=["3.9", "3.10"], reuse_venv=True)
def tests(session: Session):
    """Run unit tests."""
    session.install("-e", ".", *PYTEST_PACKAGES)
    session.run("pytest")


@nox.session(reuse_venv=True)
def black(session: Session):
    """Check black formatting."""
    session.install("black")
    session.run("black", "--check", *LINT_PATHS)


@nox.session(reuse_venv=True)
def flake8(session: Session):
    """Run flake8"""
    session.install("flake8")
    session.run(
        "flake8",
        "--ignore=E261,E501",
        "--per-file-ignores=__init__.py:F401",
        *LINT_PATHS
    )


@nox.session(reuse_venv=True)
def isort(session: Session):
    """Check imports sorting"""
    session.install("isort")
    session.run("isort", "--check", *LINT_PATHS)


@nox.session(reuse_venv=True)
def mypy(session: Session):
    """Run Mypy"""
    session.install("mypy", "types-PyYAML")
    session.run("mypy", *LINT_PATHS)


@nox.session(reuse_venv=True)
def pylint(session: Session):
    """Run pylint"""
    session.install("pylint", "-e", ".", *PYTEST_PACKAGES)
    session.run("pylint", "--rcfile=pyproject.toml", *LINT_PATHS)


@nox.session(python=False)
def lint(session: Session):
    """Run all lint tasks"""
    session.notify("black")
    session.notify("flake8")
    session.notify("isort")
    session.notify("mypy")
    session.notify("pylint")


@nox.session(python=False)
def checks(session: Session):
    """Run all checks"""
    session.notify("lint")
    session.notify("tests")


@nox.session(python=False)
def dev(session: Session) -> None:
    """
    Sets up a python development environment for the project.
    """

    session.run("python3", "-m", "virtualenv", fsdecode(VENV_DIR), silent=True)
    python_path = Path.cwd() / VENV_DIR / "bin/python"
    python = fsdecode(python_path)
    session.run(
        python,
        "-m",
        "pip",
        "install",
        "-e",
        ".",
        *DEV_DEPENDENCIES,
        external=True,
        silent=True
    )
