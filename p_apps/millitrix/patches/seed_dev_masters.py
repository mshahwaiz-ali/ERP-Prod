# Copyright (c) 2026, Millitrix and contributors
"""Seed dev site masters: COA, GL Parameter, Menu, Module, User Rights."""

from __future__ import annotations


def execute() -> None:
	from millitrix.utils.dev_bootstrap import run

	result = run()
	print(f"dev bootstrap: {result}")
