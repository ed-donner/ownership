# Inventory

How stock is modelled and moved in this repo. Read this before customizing warehouses, deliveries, lots or stock valuation. Odoo's own modules stay unchanged; our changes go in our own addon under `addons/` (see `AGENTS.md`).

Three modules make up the area:

- `addons/stock`: warehouses, locations, operations, quants, routes. Depends only on `product`, `barcodes_gs1_nomenclature`, `digest` (`addons/stock/__manifest__.py`).
- `addons/stock_account`: stock valuation and accounting entries on top of `stock` and `account` (`addons/stock_account/__manifest__.py`).
- `addons/sale_stock`: sales orders create deliveries (`addons/sale_stock/__manifest__.py`).

## Key models and files

| Model | File | What it holds |
|---|---|---|
| `stock.warehouse` | `addons/stock/models/stock_warehouse.py` | Warehouse, its default locations, picking types and routes (created together) |
| `stock.location` | `addons/stock/models/stock_location.py` | Location tree; `usage` is supplier, view, internal, customer, inventory, production or transit |
| `stock.route` | `addons/stock/models/stock_location.py` | Route that groups rules (class `StockRoute`, lives in the location file) |
| `stock.rule` | `addons/stock/models/stock_rule.py` | Pull/push rule; `_run_pull` turns a procurement into moves |
| `stock.picking.type` | `addons/stock/models/stock_picking_type.py` | Operation type (receipt, delivery, internal) with default locations and sequence |
| `stock.picking` | `addons/stock/models/stock_picking.py` | Transfer document; states draft, waiting, confirmed, assigned, done, cancel |
| `stock.move` | `addons/stock/models/stock_move.py` | Planned movement of a product between two locations (demand) |
| `stock.move.line` | `addons/stock/models/stock_move_line.py` | Detailed operation: lot, package, source/destination; carries `quantity` and `picked` |
| `stock.quant` | `addons/stock/models/stock_quant.py` | On-hand quantity per product, location, lot, package, owner; has `reserved_quantity` |
| `stock.lot` | `addons/stock/models/stock_lot.py` | Lot or serial number |
| `stock.package` | `addons/stock/models/stock_package.py` | Package (container) with history in `addons/stock/models/stock_package_history.py` |
| `stock.reference` | `addons/stock/models/stock_reference.py` | Groups moves and pickings that belong together (replaces the old procurement group) |
| `stock.warehouse.orderpoint` | `addons/stock/models/stock_orderpoint.py` | Reordering rule (min/max) |
| `stock.picking.batch` | `addons/stock/models/stock_picking_batch.py` | Batch and wave transfers |
| Product fields | `addons/stock/models/product.py` | `is_storable`, `tracking`, `route_ids` on `product.template` |
| Valuation | `addons/stock_account/models/product.py`, `addons/stock_account/models/product_value.py` | Cost method, `product.value` records |
| Sale links | `addons/sale_stock/models/stock.py`, `addons/sale_stock/models/sale_order_line.py` | `sale_line_id` on moves, `sale_id` on pickings, procurement launch |
| Security | `addons/stock/security/ir.access.csv`, `addons/stock/security/stock_security.xml` | Access rows and groups |
| Tests | `addons/stock/tests/common.py`, `addons/stock/tests/test_stock_flow.py` | Base test classes and a full-flow example |

## How the pieces connect

Stock is a double-entry system: every move goes from one location to another, and "out of stock" means the quant sits in a supplier, customer or inventory location rather than disappearing.

1. A `stock.warehouse` creates its locations, picking types and routes on create (`addons/stock/models/stock_warehouse.py`).
2. A demand (sale order line, orderpoint, manual picking) becomes a `stock.rule.Procurement` (`addons/stock/models/stock_rule.py`). The rule's `_run_pull` builds move values with `_get_stock_move_values` and creates `stock.move` records.
3. `stock.move._action_confirm` confirms moves and can chain further procurements (`addons/stock/models/stock_move.py`). Moves are attached to a `stock.picking` per picking type, partner and reference.
4. `stock.move._action_assign` reserves: it looks up quants with `stock.quant._get_reserve_quantity`, bumps `reserved_quantity` and creates `stock.move.line` records (`addons/stock/models/stock_move.py`, `addons/stock/models/stock_quant.py`). The picking becomes `assigned` when everything is reserved. `_do_unreserve` undoes it.
5. The user sets `quantity` and `picked` on move lines. `stock.picking.button_validate` runs `_action_done`, which moves the quants and creates a backorder for the rest unless told otherwise (`addons/stock/models/stock_picking.py`, `addons/stock/models/stock_move_line.py`).
6. Tracking: `product.template.tracking` is `lot`, `serial` or empty, derived from `store_by` (untracked, quantity, lot, serial) on storable products (`addons/stock/models/product.py`). Lot and serial numbers are `stock.lot` records on move lines and quants. Serial uniqueness is enforced in `addons/stock/models/stock_quant.py`.
7. Valuation: `stock_account` adds a `value` field on moves and valuation logic on products and categories (`addons/stock_account/models/stock_move.py`, `addons/stock_account/models/product.py`).

### How sales drive deliveries

- `sale.order.line._action_launch_stock_rule` calls `_prepare_procurement_values` and `_create_procurements`, then runs them through `stock.rule` (`addons/sale_stock/models/sale_order_line.py`).
- `stock.rule._get_custom_move_fields` in `sale_stock` copies `sale_line_id`, `partner_id`, `sequence`, `to_refund` onto the created moves (`addons/sale_stock/models/stock.py`).
- `stock.picking.sale_id` is computed from the moves; `stock.route.sale_selectable` makes a route choosable on an order line (`addons/sale_stock/models/stock.py`).
- Delivered quantities flow back to the order line and invoice (`addons/sale_stock/models/sale_order_line.py`, `addons/sale_stock/models/account_move.py`).

## Extension points

Put everything in our own addon. Declare `depends` on `sale_stock` (or `stock`) so load order is right.

| Goal | Hook | Example in core |
|---|---|---|
| Add fields to moves, pickings, quants | `_inherit = 'stock.move'` etc. | `addons/sale_stock/models/stock.py` |
| Pass new data from a sale line to the delivery | Override `_prepare_procurement_values` on `sale.order.line`, and extend `_get_custom_move_fields` on `stock.rule` | `addons/sale_stock/models/sale_order_line.py`, `addons/sale_stock/models/stock.py` |
| Change how moves are created from a rule | Override `_get_stock_move_values` on `stock.rule` | `addons/stock/models/stock_rule.py` |
| Change reservation | Override `_action_assign`, `_update_reserved_quantity` on `stock.move`, or `_get_reserve_quantity` on `stock.quant` | `addons/stock/models/stock_move.py`, `addons/stock/models/stock_quant.py` |
| Run logic when a transfer completes | Override `_action_done` (picking, move, move line) and call `super()` | `addons/stock/models/stock_picking.py` |
| Add a button or field to the picking form | View inheritance with xpath on `stock.picking` form | `addons/stock/views/stock_picking_views.xml` |
| Add warehouse-specific behavior | Extend `stock.warehouse` and its route/picking type creation | `addons/stock/models/stock_warehouse.py` |
| Backend JS and templates | Add files to `web.assets_backend` in our manifest | `addons/stock/__manifest__.py` |
| Access rights | Rows in security/ir.access.csv plus company rules | `addons/stock/security/ir.access.csv` |

Tests: subclass the helpers in `addons/stock/tests/common.py` and follow the patterns in `addons/stock/tests/test_stock_flow.py`.

## Gotchas for Odoo 20

- Access rights are in ir.access.csv with columns `id,name,model_id,group_id/id,operation,domain` and an `operation` like `crud` or `r`. Record rules are rows of the same file with a `domain` and often no group (`addons/stock/security/ir.access.csv`). Do not write ir.model.access.csv; the manifest lists security/ir.access.csv (`addons/stock/__manifest__.py`).
- `stock.reference` replaces `procurement.group`. Moves use `reference_ids` (many2many), and sales use `stock_reference_ids` (`addons/stock/models/stock_move.py`, `addons/sale_stock/models/sale_order_line.py`).
- Routes are `stock.route`, not `stock.location.route`, and packages are `stock.package`, not `stock.quant.package`. Some XML ids keep the old names (`access_stock_location_route` in `addons/stock/security/ir.access.csv`).
- There is no `stock.valuation.layer` model here. Valuation uses `product.value` and a `value` on `stock.move` (`addons/stock_account/models/product_value.py`, `addons/stock_account/models/stock_move.py`).
- A product is stocked only if `is_storable` is true on a `consu` type product; there is no `type = 'product'` (`addons/stock/models/product.py`). Tracking is a separate choice stored in `store_by`.
- Move lines use `quantity` plus a `picked` flag; the old `qty_done` and `reserved_uom_qty` are gone (`addons/stock/models/stock_move_line.py`).
- Constraints use `models.Constraint(...)` class attributes, not `_sql_constraints` (`addons/stock/models/stock_picking.py`).
- View syntax: `<list>` not `<tree>`, and `invisible="state in ['cancel', 'done']"` expressions, not `attrs` (`addons/stock/views/stock_picking_views.xml`).
- Translation helper in models is `self.env._("...")` as well as `_()` (`addons/stock/models/stock_lot.py`).
- The stock UI is heavy JS: `addons/stock/static/src` is bundled whole into `web.assets_backend`, so a file you add under our own addon needs its own manifest glob (`addons/stock/__manifest__.py`).
- Moves are multi-company with `check_company=True`; keep `company_id` consistent when creating records in code (`addons/stock/models/stock_move.py`).
- Never write quant quantities directly. Use inventory adjustments or moves, so reservations and valuation stay consistent (`addons/stock/models/stock_quant.py`).
- Many methods are private and called by other modules (`stock_account`, `mrp`, `purchase_stock` also inherit `stock.move`). Always call `super()` and keep signatures, for example `_action_confirm(self, merge=True, merge_into=False, create_proc=True)` (`addons/stock/models/stock_move.py`).
