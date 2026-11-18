# Sales

The Sales area is the `sale` module: quotations, sales orders and their lines. It is the shared base for the back-office Sales app and for the web shop (`website_sale` builds carts on `sale.order`). It depends on `sales_team`, `account_payment` and `utm` (`addons/sale/__manifest__.py`). Our own changes go in our own addon and inherit from these models; do not edit `addons/sale`.

## Key files

| Path | What it holds |
|---|---|
| `addons/sale/models/sale_order.py` | `sale.order`: state, partner/pricing/payment fields, confirmation, invoicing, portal helpers |
| `addons/sale/models/sale_order_line.py` | `sale.order.line`: pricing, delivered/invoiced quantities, invoice status, sections and combo lines |
| `addons/sale/models/account_move.py`, `addons/sale/models/account_move_line.py` | Links from invoices back to orders and lines |
| `addons/sale/models/product_template.py`, `addons/sale/models/product_product.py` | Sale-specific product fields (invoice policy, warnings) |
| `addons/sale/models/payment_transaction.py` | Online payment of an order, confirms it on success |
| `addons/sale/models/res_partner.py`, `addons/sale/models/crm_team.py` | Partner order counts, team dashboard data |
| `addons/sale/wizard/sale_make_invoice_advance.py` | "Create Invoice" wizard (regular, down payment) |
| `addons/sale/wizard/sale_order_discount.py`, `addons/sale/wizard/mass_cancel_orders.py` | Global discount, mass cancel |
| `addons/sale/controllers/portal.py` | /my/orders portal pages, accept/sign, pay |
| `addons/sale/controllers/product_configurator.py`, `addons/sale/controllers/combo_configurator.py` | JSON routes used by the configurator dialogs |
| `addons/sale/views/sale_order_views.xml`, `addons/sale/views/sale_order_line_views.xml` | Form, list, kanban, search views and actions |
| `addons/sale/views/sale_menus.xml` | Menus, loaded last in the manifest |
| `addons/sale/views/sale_portal_templates.xml` | QWeb templates for the portal order page |
| `addons/sale/security/ir.access.csv`, `addons/sale/security/res_groups.xml` | Access rows (with record-rule domains) and feature groups |
| `addons/sale/report/sale_report.py` | `sale.report` SQL view for analysis |
| `addons/sale/static/src/js/`, `addons/sale/static/src/views/` | Backend OWL widgets and views |
| `addons/sale/static/src/interactions/` | Portal (frontend) interactions |
| `addons/sale/tests/` | Tests, e.g. `addons/sale/tests/test_sale_flow.py`, `addons/sale/tests/common.py` |

## Models and states

`sale.order` (`addons/sale/models/sale_order.py`):

- `state` selection `SALE_ORDER_STATE`: `draft` (Quotation), `sent` (Quotation Sent), `sale` (Sales Order), `cancel` (Cancelled). The field is readonly; move it with the `action_*` methods.
- `locked` is a separate boolean, not a state. Locked orders cannot be edited (`action_lock`, `action_unlock`). The old `done` state no longer exists.
- `invoice_status` is a stored compute (`_compute_invoice_status`) driven by the lines. `invoicing_closed` forces "fully invoiced" (`action_close_invoicing`, `action_reopen_order`).
- A `models.Constraint` requires `date_order` when `state = 'sale'`.
- Inherits `portal.mixin`, `utm.mixin`, `mail.activity.mixin` and `product.catalog.mixin`, with `_check_company_auto = True`.

`sale.order.line` (`addons/sale/models/sale_order_line.py`):

- `display_type` marks section, subsection and note lines (`line_section`, `line_subsection`, note). SQL constraints forbid product, price and quantity on those lines and require a UoM on normal lines.
- Quantity chain: `product_uom_qty` ordered, `qty_delivered` (method chosen in `_compute_qty_delivered_method`), `qty_invoiced`, `qty_to_invoice`; per-line `invoice_status`.
- Combo products: `combo_item_id` and `linked_line_id` tie child lines to the combo line.
- `is_downpayment` lines come from the advance-invoice wizard.

## Quotation to confirmed order

1. Salesperson builds the quotation in the form view (`addons/sale/views/sale_order_views.xml`). Lines are priced by `_compute_pricelist_item_id` and `_compute_price_unit`.
2. `action_quotation_send` mails it and `action_quotation_sent` moves `draft` to `sent`.
3. The customer accepts and signs in the portal (`/my/orders/<int:order_id>/accept` in `addons/sale/controllers/portal.py`) or pays online (`addons/sale/models/payment_transaction.py`).
4. `action_confirm` validates (`_confirmation_error_message`), writes `state = 'sale'` and `date_order`, then calls the empty hook `_action_confirm`, then locks if `sale.group_auto_done_setting` is enabled (`_should_be_locked`), then sends the confirmation mail only when the context has `send_email`.
5. `action_cancel` refuses locked orders and calls `_action_cancel`; `action_draft` resets `cancel`/`sent` orders to `draft` and clears the signature.

## Links to other areas

| Area | How it connects |
|---|---|
| Invoicing | `_create_invoices(final, grouped)` builds `account.move` from `_prepare_invoice` and each line's `_prepare_invoice_line`; `_get_invoiceable_lines` picks lines. Wizard: `addons/sale/wizard/sale_make_invoice_advance.py`. `action_view_invoice` shows the result. |
| Products | Lines point at `product.product`; sale fields are added in `addons/sale/models/product_template.py`. Invoice policy drives `qty_to_invoice`. |
| Inventory | `addons/sale_stock/models/sale_order.py` overrides `_action_confirm` and adds `picking_ids`; `addons/sale_stock/models/sale_order_line.py` has `_action_launch_stock_rule` and sets `qty_delivered` from moves. |
| Web shop | `addons/website_sale/models/sale_order.py` adds the cart API (`_cart_add`, `_cart_update_line_quantity`, `_cart_update_order_line`). A cart is a `draft` order. |
| Templates | `addons/sale_management/models/sale_order_template.py` adds quotation templates. |
| Payments | `account_payment` is a hard dependency (`addons/sale/__manifest__.py`); order-side payment handling is in `addons/sale/models/payment_transaction.py`. |

## Access control

Odoo 20 uses ir.access.csv, not ir.model.access.csv (`addons/sale/security/ir.access.csv`, model in `odoo/addons/base/models/ir_access.py`). Each row has `operation` (e.g. `cru`) and an optional `domain`, so access rights and record rules are one record.

For `sale.order` (`addons/sale/security/ir.access.csv`):

| Group | Access |
|---|---|
| `sales_team.group_sale_salesman` | `cru`, own orders or unassigned (`user_id`) |
| `sales_team.group_sale_salesman_all_leads` | `cru`, all orders |
| `sales_team.group_sale_manager` | `crud`, all orders |
| `account.group_account_invoice` | `ru` |
| `base.group_portal` | `r`, orders of the commercial partner's tree |
| everyone | multi-company domain on `company_id` |

Group definitions: `addons/sales_team/security/sales_team_security.xml`. Feature toggles (discounts, lock, warnings, pro forma) are in `addons/sale/security/res_groups.xml`.

## Extension points for our addon

Declare `depends` on `sale` (or `sale_stock` / `website_sale` as needed) in our manifest.

- **Models**: `_inherit = "sale.order"` in our addon; add fields and override methods with `super()`. Preferred hooks: `_action_confirm` (after confirmation), `_action_cancel`, `_prepare_invoice` (invoice header values), `_prepare_invoice_line` on the line, `_get_invoiceable_lines`, `_compute_price_unit`, `_should_be_locked`, `_confirmation_error_message`. Add computes to existing `@api.depends` lists by redefining the method with the same decorator.
- **Views**: inherit `sale.view_order_form` style views with `<field position="after">` and `<xpath>` (see `addons/sale/views/sale_order_views.xml` for ids). Use `invisible="..."`/`readonly="..."` expressions, not `attrs`.
- **Security**: add rows to our own security/ir.access.csv; do not edit sale's file.
- **Portal**: extend templates in `addons/sale/views/sale_portal_templates.xml` with inherited QWeb; add routes by subclassing `CustomerPortal` from `addons/sale/controllers/portal.py`.
- **Frontend assets**: add files in our manifest under `web.assets_backend`, `web.assets_frontend` (portal/shop) or `web.assets_unit_tests`, as `addons/sale/__manifest__.py` does. Do not list JS in view XML.
- **Tests**: subclass the helpers in `addons/sale/tests/common.py`; see `addons/sale/tests/test_sale_flow.py` for a confirm-deliver-invoice flow.

## Gotchas for Odoo 20

- No ir.model.access.csv: use ir.access.csv with `operation` and `domain` columns (`odoo/addons/base/models/ir_access.py`).
- Domains on records use `('order_id', 'access', 'read')` operators (see portal rows in `addons/sale/security/ir.access.csv`); check rights with `check_access("write")` (used in `addons/sale/models/sale_order.py`).
- Sale groups live in `sales_team` and attach to a `privilege_id` record (`addons/sales_team/security/sales_team_security.xml`), not a `category_id` as in older versions.
- Order state has no `done`; use `locked`.
- Routes: JSON routes use `type="jsonrpc"`, not `"json"` (`addons/sale/controllers/portal.py`).
- Translations use `self.env._("...")` (`addons/sale/models/sale_order.py`).
- SQL constraints are `models.Constraint("CHECK(...)")` class attributes at the top of the model, not `_sql_constraints` (`addons/sale/models/sale_order_line.py`).
- Portal frontend code is in static/src/interactions/ and registered in `web.assets_frontend` (`addons/sale/__manifest__.py`), not as legacy widgets.
- Line-level data matters: totals, invoice status and delivered quantity are computed from lines. Change line fields, not order totals.
- `sale_stock` and other modules override `_action_confirm` too; always call `super()` and do not assume order of overrides.
- Several settings change behavior (lock, discounts, sections, services and materials); check `addons/sale/wizard/res_config_settings.py` before assuming a field is visible.
