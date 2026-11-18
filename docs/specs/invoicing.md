# Invoicing (addons/account)

`addons/account` holds all accounting: invoices, vendor bills, journal entries, payments, taxes, journals, fiscal positions and chart-of-accounts loading. Everything revolves around one model, `account.move`, and its lines. Sale creates invoices from `addons/sale` by inheriting these models. Modules list and dependencies are in `addons/account/__manifest__.py`.

## Key models and files

| Path | What it holds |
|---|---|
| `addons/account/models/account_move.py` | `account.move`: invoices, bills, receipts, journal entries (`move_type`), `state`, `payment_state`, posting and reversal |
| `addons/account/models/account_move_line.py` | `account.move.line` (journal items): `display_type`, `debit`/`credit`/`balance`, `tax_ids`, reconcile fields |
| `addons/account/models/account_journal.py` | `account.journal` (sale, purchase, bank, cash, general) and `account.journal.group` |
| `addons/account/models/account_account.py` | `account.account` (chart of accounts) |
| `addons/account/models/account_tax.py` | `account.tax`, `account.tax.group`, `account.tax.repartition.line`, tax computation |
| `addons/account/models/account_payment.py` | `account.payment`; the same file also adds `payment_ids` to `account.move` |
| `addons/account/models/account_payment_method.py` | `account.payment.method` and `.line` (per journal) |
| `addons/account/models/account_payment_term.py` | `account.payment.term` and lines |
| `addons/account/models/partner.py` | `account.fiscal.position` and the accounting fields on `res.partner` |
| `addons/account/models/account_partial_reconcile.py`, `addons/account/models/account_full_reconcile.py` | Reconciliation records |
| `addons/account/models/account_reconcile_model.py` | `account.reconcile.model` rules for bank statement lines |
| `addons/account/models/account_bank_statement_line.py` | Bank statement lines, which create their own moves |
| `addons/account/models/chart_template.py` | `account.chart.template` loader and the `@template` decorator |
| `addons/account/models/template_generic_coa.py` | Generic chart of accounts template |
| `addons/account/models/account_move_send.py` | Sending invoices by mail and other channels |
| `addons/account/wizard/account_payment_register.py` | "Register Payment" wizard, `_create_payments` |
| `addons/account/wizard/account_move_reversal.py` | Credit note wizard |
| `addons/account/report/account_invoice_report.py` | `account.invoice.report`, a SQL view (`_auto = False`) for analysis |
| `addons/account/views/account_move_views.xml` | Invoice, bill and entry form/list views, actions |
| `addons/account/views/report_invoice.xml` | QWeb PDF invoice template |
| `addons/account/security/account_security.xml`, `addons/account/security/ir.access.csv` | Groups, access rows, record rules |
| `addons/account/tests/common.py` | `AccountTestInvoicingCommon` test base class |
| `addons/sale/models/account_move.py`, `addons/sale/models/account_move_line.py` | Sale side of `account.move` and its lines |

## Move types and lines

- `move_type` values: `entry`, `out_invoice`, `out_refund`, `in_invoice`, `in_refund`, `out_receipt`, `in_receipt` (`addons/account/models/account_move.py`).
- `state` has only `draft`, `posted`, `cancel`. Payment status is the separate `payment_state` (`not_paid`, `in_payment`, `paid`, `partial`, `reversed`, `blocked`, `invoicing_legacy`; see `PAYMENT_STATE_SELECTION` in the same file).
- `line_ids` holds every journal item. `invoice_line_ids` is only the subset the user edits (products, sections, notes). The comment on the field says so (`addons/account/models/account_move.py`).
- `display_type` on a line tells its role: `product`, `tax`, `payment_term`, `rounding`, `discount`, `epd`, `line_section`, `line_subsection`, `line_note`, `cogs`, plus `non_deductible_product_total`, `non_deductible_product`, `non_deductible_tax` (`addons/account/models/account_move_line.py`). Tax and payment-term lines are generated; do not create them by hand on invoices.
- Amounts are stored as `balance` (company currency) plus `amount_currency` (move currency). `debit` and `credit` are computed from `balance` (`_compute_debit_credit` in the same file).
- Number comes from `sequence.mixin` per journal (`addons/account/models/sequence_mixin.py`). Name is `/` until posted. There is a unique index on name per journal for posted moves (`_unique_name` in `addons/account/models/account_move.py`).

## Posting flow

1. Draft move created (form, `sale` invoice creation, import, email alias on the journal).
2. `action_post` (button) calls `_post(soft=False)`, while `_post` itself defaults to `soft=True` (future-dated moves are scheduled for auto-post); `_post` checks completeness, assigns the number, sets `state='posted'`, and may hash the entry on a secured journal (`addons/account/models/account_move.py`).
3. `button_draft` returns to draft, `button_cancel` cancels, `_reverse_moves` builds credit notes/reversals (same file).
4. Payment: `action_register_payment` opens `addons/account/wizard/account_payment_register.py`, which creates `account.payment` records. Each payment owns a `move_id` journal entry. Reconciling payment lines with the invoice's receivable/payable line updates `payment_state` through `account.partial.reconcile`.
5. Lock dates and lock exceptions can forbid changes to old moves (`addons/account/models/account_lock_exception.py`, `addons/account/models/company.py`).

## How sale creates invoices

- `sale.order._create_invoices(final=False, grouped=False)` in `addons/sale/models/sale_order.py` picks lines with `_get_invoiceable_lines`, builds header values with `_prepare_invoice`, and line values with `sale.order.line._prepare_invoice_line` in `addons/sale/models/sale_order_line.py`.
- The wizard `addons/sale/wizard/sale_make_invoice_advance.py` calls it (also handles down payments).
- Link back: `account.move.line.sale_line_ids` (`addons/sale/models/account_move_line.py`) and `sale.order.line.invoice_lines`, `qty_invoiced`, `invoice_status` (`addons/sale/models/sale_order_line.py`).
- `addons/sale/models/account_move.py` is `_inherit = ["account.move", "utm.mixin"]` and extends `action_post`, `button_draft`, `button_cancel`, `_post`, `_reverse_moves` to keep orders and down payments in sync. When you override these in our addon, call `super()` and do not skip the sale override.
- `addons/sale/__manifest__.py` depends on `account_payment`, so sale always has accounting installed.

## Taxes, fiscal positions, chart of accounts

- `account.tax`: `type_tax_use` (`sale`, `purchase`, `none`), `amount_type` (`group`, `fixed`, `percent`, `division`), `price_include`, repartition lines for base/tax accounts and tags (`addons/account/models/account_tax.py`). Tax maths lives in helper methods in the same file (grep `def .*base_line` in `addons/account/models/account_tax.py`); reuse them rather than re-implementing.
- Fiscal positions map taxes and accounts per partner (`addons/account/models/partner.py`).
- Chart of accounts: `addons/account/models/chart_template.py` loads data from CSV files named `<model>-<template>.csv` in `addons/account/data/template/` (see `addons/account/data/template/account.tax-generic_coa.csv`). Country charts live in the `l10n_*` modules under `addons/` (for example `addons/l10n_us`, `addons/l10n_de`, `addons/l10n_fr`) and register with `@template('<code>', '<model>')`.
- `account.account` has `account_type` and `code`; codes can differ per company (`addons/account/models/account_account.py`, `addons/account/models/account_code_mapping.py`).

## Access groups

Defined in `addons/account/security/account_security.xml`:

| Group | Role |
|---|---|
| `account.group_account_readonly` | Read-only accounting |
| `account.group_account_invoice` | Create invoices, bills, payments ("Billing") |
| `account.group_account_basic` | Implies invoice group |
| `account.group_account_user` | Accountant; implies basic and readonly |
| `account.group_account_manager` | Adviser; implies invoice |
| `account.group_account_secured`, `account.group_cash_rounding`, `account.group_partial_purchase_deductibility` | Feature toggles |

Rules are multi-company: records are filtered with `company_ids` in `addons/account/security/ir.access.csv`.

## Extension points for our addon

Our code goes in our own addon (README.md plans addons/take_ownership, not created yet), never in `addons/account` or `addons/sale`.

- Add fields or logic: `_inherit = 'account.move'` (or `'account.move.line'`, `'account.journal'`, `'account.tax'`) in a new model file; add `account` or `sale` to `depends` in the manifest.
- Add behavior to posting by overriding `_post` (batch, recordset) or `action_post` (button). Prefer `_post` for rules that must apply to every code path; sale invoices, payments and imports reach it without `action_post`.
- Invoice created from a sale order: override `_prepare_invoice` and `_prepare_invoice_line` on `sale.order` / `sale.order.line` and call `super()` (`addons/sale/models/sale_order.py`).
- Views: inherit `account.view_move_form` and the others in `addons/account/views/account_move_views.xml` with `xpath`, in our own XML file listed in `data`. Use direct `invisible="..."` / `readonly="..."` Python-style expressions, not `attrs`.
- PDF invoice: extend the QWeb templates in `addons/account/views/report_invoice.xml` with `t-inherit`.
- Assets: backend JS/SCSS goes in the `assets` key of our manifest under `web.assets_backend`; invoice PDFs use `web.report_assets_common` and `web.report_assets_pdf` (see how `addons/account/__manifest__.py` does it).
- Security: add rows to our own security/ir.access.csv for new models; do not edit the account CSV.
- Tests: subclass `AccountTestInvoicingCommon` and use `init_invoice(...)` (`addons/account/tests/common.py`). It uses a test company with a generic chart, so tax and journal lookups work.

## Gotchas for Odoo 20

- Access rows are in ir.access.csv (model `ir.access`, column `operation` with values like `r`, `crud`), not ir.model.access.csv. See `addons/account/security/ir.access.csv` and `ir.access` in `odoo/addons/base/models/ir_access.py`.
- Groups use `privilege_id` (`res.groups.privilege`) for the settings UI, in addition to `implied_ids` (`addons/account/security/account_security.xml`).
- SQL constraints are declared as class attributes: `models.Constraint(...)`, `models.UniqueIndex(...)` (for example `_unique_name` in `addons/account/models/account_move.py`), not `_sql_constraints`.
- Models carry an `_explanation` string (`addons/account/models/account_move.py`).
- Domains use `Domain` (class in `odoo/orm/domains.py`; imported as `from odoo.fields import Command, Domain` in `addons/account/models/account_move.py`).
- Sale lines have `line_subsection` besides sections; account lines too. Code that filters `display_type in ('line_section', 'line_note')` misses subsections.
- `invoice_line_ids` is a subset of `line_ids`. Writing to `line_ids` on an invoice can fight the automatic tax and payment-term line computation; edit `invoice_line_ids` and let the computes rebuild the rest.
- Posted moves are protected (hash, lock dates, `BYPASS_LOCK_CHECK` in `addons/account/models/account_move.py`). Reset to draft first, or create a reversal.
- Chart of accounts and taxes are loaded via `account.chart.template` after install, not by plain XML data. Test companies need a chart (`AccountTestInvoicingCommon` does it).
- `account.move` is a very large file (about 8,400 lines). `grep -n "def _compute_..."` for the field you need instead of reading it whole.
