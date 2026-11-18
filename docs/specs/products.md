# Products

Spec of the Products area for agents customizing it. Core code is in `addons/product/` (templates, variants, categories, attributes, pricelists) and `addons/uom/` (units of measure). Other modules extend these models; Odoo's own modules stay unchanged, so our changes go in our own addon under `addons/`.

## Key models and files

| Model | File | What it holds |
|---|---|---|
| `product.template` | `addons/product/models/product_template.py` | The catalog record: name, `type`, `list_price`, `standard_price`, `categ_id`, `uom_id`, `attribute_line_ids`, `sale_ok`, `purchase_ok`, `seller_ids`, `company_id` |
| `product.product` | `addons/product/models/product_product.py` | The variant (sellable/stockable unit). `_inherits = {'product.template': 'product_tmpl_id'}`, adds `default_code`, `barcode`, `product_template_attribute_value_ids` |
| `product.category` | `addons/product/models/product_category.py` | Tree via `parent_id`, `_parent_store`, `complete_name` as `_rec_name` |
| `product.attribute` | `addons/product/models/product_attribute.py` | Attribute definition: `create_variant` (always/dynamic/no_variant), `display_type` |
| `product.attribute.value` | `addons/product/models/product_attribute_value.py` | Values of an attribute (global) |
| `product.template.attribute.line` | `addons/product/models/product_template_attribute_line.py` | Which attribute and values a template uses |
| `product.template.attribute.value` | `addons/product/models/product_template_attribute_value.py` | Per-template value, with `price_extra` and exclusions |
| `product.attribute.custom.value` | `addons/product/models/product_attribute_custom_value.py` | Free-text values entered on an order line |
| `product.pricelist` | `addons/product/models/product_pricelist.py` | Pricelist with `currency_id`, `company_id`, `country_group_ids`, `item_ids` |
| `product.pricelist.item` | `addons/product/models/product_pricelist_item.py` | Rule: `applied_on`, `base`, `compute_price`, `min_quantity`, dates |
| `product.supplierinfo` | `addons/product/models/product_supplierinfo.py` | Vendor prices |
| `product.tag`, `product.combo`, `product.combo.item` | `addons/product/models/product_tag.py`, `addons/product/models/product_combo.py`, `addons/product/models/product_combo_item.py` | Tags and combo products |
| `product.document` | `addons/product/models/product_document.py` | Files attached to a product |
| `product.uom` | `addons/product/models/product_uom.py` | Link between a product and an extra unit (packaging) with its own barcode |
| `uom.uom` | `addons/uom/models/uom_uom.py` | Units, each relative to a reference unit (`relative_uom_id`, `relative_factor`) |
| Security | `addons/product/security/ir.access.csv`, `addons/product/security/product_security.xml` | Access rows, groups, multi-company rules |
| Manifest | `addons/product/__manifest__.py` | Depends on `base`, `mail`, `uom`; lists data files and assets |

Other modules add fields to these models, so grep before assuming a field is absent. Examples: stock in `addons/stock/models/product.py`, web shop in `addons/website_sale/models/product_template.py`.

## How the pieces connect

- A template owns attribute lines (`product.template.attribute.line`). Each line links one `product.attribute` and a set of its values. The template-specific values (`product.template.attribute.value`) carry `price_extra`.
- `create_variant` on the attribute decides whether variants exist: `always` creates all combinations when lines change, `dynamic` creates them when first ordered, `no_variant` never creates them (`addons/product/models/product_attribute.py`). Generation runs in `_create_variant_ids` (`addons/product/models/product_template.py`).
- A variant reads template fields through `_inherits`: `product.product` has no own `name` or `list_price` column; it delegates to the template (`addons/product/models/product_product.py`). Writing `name` on a variant writes the template.
- Templates with no attributes get exactly one variant. `product_variant_id` is the first one.
- `categ_id` points at a `product.category` tree. Pricelist rules can target a category, a template, a variant or everything (`applied_on` in `addons/product/models/product_pricelist_item.py`).
- Pricing goes through `product.pricelist` methods `_get_product_price`, `_get_products_price`, `_compute_price_rule` (`addons/product/models/product_pricelist.py`). Rule selection is in `_get_applicable_rules` and `_get_applicable_rules_domain`. Rule computation is `_compute_price` on the item. `base` is `list_price`, `standard_price` or another pricelist; `compute_price` is `fixed`, `discount` or `markup`.
- Units: `uom_id` on the template is the stock/sales unit; `uom_ids` lists extra packagings (`addons/product/models/product_template.py`). Conversion is on `uom.uom` (`addons/uom/models/uom_uom.py`). The unit field is only shown with group `uom.group_uom` (`addons/uom/security/uom_security.xml`).
- Weight and volume units come from settings parameters `product.weight_in_lbs` and `product.volume_in_cubic_feet` (`addons/product/models/res_config_settings.py`).

## Where product fields show in the back office

| Place | View record (file) |
|---|---|
| Template form (shared by sale, stock, etc.) | `product.product_template_form_view` in `addons/product/views/product_views.xml`; tabs are `general_information`, `sales`, `purchase`, `inventory` |
| Template form, template-only additions | `product.product_template_only_form_view` in `addons/product/views/product_template_views.xml` (inherits the one above) |
| Template list, kanban, search | `product.product_template_tree_view`, `product.product_template_kanban_view`, `product.product_template_search_view` in `addons/product/views/product_template_views.xml` and `addons/product/views/product_views.xml` |
| Variant form and list | `product.product_normal_form_view`, `product.product_product_tree_view` in `addons/product/views/product_views.xml` |
| Category form and list | `addons/product/views/product_category_views.xml` |
| Attributes, values | `addons/product/views/product_attribute_views.xml`, `addons/product/views/product_attribute_value_views.xml` |
| Pricelists and rules | `addons/product/views/product_pricelist_views.xml`, `addons/product/views/product_pricelist_item_views.xml` |
| Units | `addons/product/views/uom_views.xml`, `addons/uom/views/uom_uom_views.xml` |
| Settings (variants, pricelists, units) | `addons/product/views/res_config_settings_views.xml` |

Actions: `product_template_action` (kanban, list, form) in `addons/product/views/product_template_views.xml`, `product_template_action_all` and `product_variant_action` in `addons/product/views/product_views.xml`.

Other apps extend the same form: `addons/sale/views/product_views.xml`, `addons/stock/views/product_views.xml`, `addons/website_sale/views/product_views.xml`. Look at how they anchor their xpaths before writing yours.

## Extending from our own addon

Models: inherit in place, do not copy.

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    condition_grade = fields.Selection([...])
```

- Add the file to models/__init__.py, list the module in `depends` (at least `product`; add `stock` or `website_sale` if you anchor on their views). Manifest format: `addons/product/__manifest__.py`.
- Fields on `product.template` are the right place for data shared by all variants. If a value differs per variant (a specific serial or colour), use an attribute or a field on `product.product`. A field on the template is not editable on the variant form unless you show it there.
- Template fields can be mirrored on the variant with `related='product_tmpl_id.x'`, but with `_inherits` a template field is already readable on `product.product`.
- Views: inherit with `inherit_id` and `xpath` on a named element, preferring `name=` anchors such as `group_general` or `group_standard_price`, or the page `name`. Place fields for the template form in `product.product_template_form_view`; add to the variant form separately if wanted. Add list columns in `product.product_template_tree_view`.
- Access: new fields inherit the model's access rows in `addons/product/security/ir.access.csv`. A new model needs its own row in your security/ir.access.csv, and a company rule if it has `company_id` (see `addons/product/security/ir.access.csv` for the pattern).
- Assets: backend JS/SCSS goes in the manifest under `web.assets_backend`, as in `addons/product/__manifest__.py`. Do not edit core asset lists.
- Tests: subclass `addons/product/tests/common.py` helpers or `addons/product/tests/test_variants.py` patterns; examples for pricelists in `addons/product/tests/test_pricelist.py`.
- Demo data: `addons/product/data/product_demo.xml`; categories in `addons/product/data/product_category_demo.xml`.

## Odoo 20 gotchas

- Access rights are `ir.access` (`odoo/addons/base/models/ir_access.py`), loaded from security/ir.access.csv with columns `id,name,model_id,group_id/id,operation,domain`, where `operation` is like `r` or `crud`. Record rules are in the same CSV (the `domain` column, empty group). Do not write ir.model.access.csv or `ir.rule` XML (`addons/product/security/ir.access.csv`).
- Groups need a privilege record (`res.groups.privilege` in `addons/product/security/product_security.xml`) rather than the old category.
- View type is `list`, not `tree`, and `invisible="expr"` is a Python-like expression, not `attrs` (`addons/product/views/product_views.xml`). Action `view_mode` is `kanban,list,form`.
- Product type is `consu` (Goods), `service`, `combo`. There is no `product` (storable) type; storable is the boolean `is_storable`, defined in `addons/product/models/product_template.py` and shown in `addons/product/views/product_views.xml`; stock only reads it, for example for the on-hand status buttons (`addons/stock/models/product.py`).
- Constraints use `models.Constraint(...)` class attributes, not `_sql_constraints` (`addons/uom/models/uom_uom.py`, `addons/product/models/product_uom.py`; class in `odoo/orm/table_objects.py`).
- Domains are built with `odoo.fields.Domain` (`odoo/orm/domains.py`), used in `addons/product/models/product_template.py`.
- Units of measure live in the separate `uom` module and `uom.uom` is a `CachedModel` (`odoo/orm/models_cached.py`). The old `uom.category` is gone: units are related by `relative_uom_id` and `relative_factor`, with `factor` computed (`addons/uom/models/uom_uom.py`). The template field is `uom_id`; there is no `uom_po_id`.
- Packagings are `product.uom` records with a barcode, linked to `uom.uom` (`addons/product/models/product_uom.py`). There is no `product.packaging` model in `addons/product/models/`.
- Pricelist entry points start with underscore (`_get_product_price`, `_get_products_price`) in `addons/product/models/product_pricelist.py`; there is no `price_get`. Groups `group_product_pricelist` and `group_product_variant` are defined in `addons/product/security/product_security.xml`.
- Template ordering is `is_favorite desc, name` (`addons/product/models/product_template.py`).
- Changing `create_variant` on an attribute already in use is blocked (`addons/product/models/product_attribute.py`). Choose it before adding data.
- Variant creation and archive logic runs on write of attribute lines (`addons/product/models/product_template_attribute_line.py`). Bulk-writing lines in loops regenerates variants each time; batch the writes.
- Price info for the web shop is computed in `_get_combination_info` in `addons/website_sale/models/product_template.py`, not in `addons/product`.
- Product catalog widget (JS) is in `addons/product/static/src/product_catalog/`, loaded through the manifest assets in `addons/product/__manifest__.py`.
