"""Smoke test: proves the package imports and the toolchain runs."""

import pytest

import controltower


def test_package_imports() -> None:
    assert controltower.__version__ == "0.1.0"


def test_main_prints_banner(capsys: pytest.CaptureFixture[str]) -> None:
    controltower.main()
    assert "ControlTower backend" in capsys.readouterr().out
