# Copyright (c) 2026, Millitrix and contributors

from __future__ import annotations

import frappe

from millitrix.api.lan import ensure_lan_hostnames


def execute():
	ensure_lan_hostnames()
