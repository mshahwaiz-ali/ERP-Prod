# Copyright (c) 2026, Millitrix and contributors

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from millitrix.utils.naming import assign_numeric_id, get_next_numeric_id


class Bank(Document):
	def before_insert(self):
		assign_numeric_id(self, "bankid")

	def validate(self):
		self.branch_count = len(self.branches or [])
		self.account_count = len(self.accounts or [])

		branch_ids = []
		for branch in self.branches or []:
			if not branch.branchid:
				branch.branchid = get_next_numeric_id("Bank Branch", "branchid")
			if branch.branchid in branch_ids:
				frappe.throw(f"Duplicate Branch ID {branch.branchid} in bank branches")
			branch_ids.append(branch.branchid)

		account_ids = []
		for account in self.accounts or []:
			if not account.bankaccid:
				account.bankaccid = get_next_numeric_id("Bank Account", "bankaccid")
			if account.bankaccid in account_ids:
				frappe.throw(f"Duplicate Bank Account ID {account.bankaccid}")
			account_ids.append(account.bankaccid)

			if not account.branchid and len(branch_ids) == 1:
				account.branchid = branch_ids[0]
			if account.branchid and account.branchid not in branch_ids:
				frappe.throw(
					f"Branch ID {account.branchid} on bank account {account.bankaccid} "
					f"is not defined under Branches"
				)

			if account.accid:
				level = frappe.db.get_value(
					"Chart of Accounting", account.accid, "chartlevel"
				)
				if level and int(level) != 5:
					frappe.throw(
						f"GL Account {account.accid} must be Chart Level 5 for bank posting"
					)
			if flt(account.amntlimit) < 0:
				frappe.throw("Amount Limit cannot be negative")
