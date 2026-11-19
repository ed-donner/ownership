# Take Ownership addon

Spec of `addons/take_ownership`, our own addon (the only one in this repo). It adds a condition grade and a battery health figure to products, shows them in the back office and the web shop, ships ten sample devices, and puts the back office in the Take Ownership brand. Odoo's own modules are not edited; everything below is `_inherit`, `inherit_id`, manifest bundle entries and data. The change is described in `docs/changes/take-ownership/intent.md`.

## Scope

In: the grade and battery fields, their views and filters, the shop product page, the sample data, back office branding.

Out: grades on quotes, orders, invoices or PDFs; the web shop theme; the point of sale; the logo; a grade per serial number; a dark mode for the back office.

## Layout

```
addons/take_ownership/
  __init__.py, __manifest__.py
  models/__init__.py, models/product_template.py
  views/product_template_views.xml     # form, list, kanban, search
  views/product_templates.xml          # web shop product page (QWeb)
  data/product_category_data.xml       # Laptops, Phones, Tablets, Accessories
  demo/product_demo.xml                # ten devices, shop categories, publication
  demo/archive_odoo_demo_products.xml  # archives Odoo's demo products
  static/img/                          # the ten photos and CREDITS.md
  static/fonts/                        # Instrument Sans, Instrument Serif, JetBrains Mono, with their OFL licenses
  static/src/scss/primary_variables.scss
  static/src/scss/fonts.scss           # @font-face
  static/src/scss/backend.scss         # back office badge text, panels, numbers
  static/src/scss/frontend.scss        # shop grade badge and battery bar
  tests/__init__.py, tests/test_product_grade.py
```

Manifest: `depends` is `['product', 'website_sale']`. `data` lists the category data, the back office views and the shop template. `demo` lists the two demo files. `license` is `LGPL-3`. Manifest keys follow `addons/product/__manifest__.py`.

## Fields

Both fields are on `product.template` (`models/product_template.py`, `_inherit = 'product.template'`). They are shared by all variants and are readable on `product.product` through `_inherits` (`addons/product/models/product_product.py`).

| Field | Type | Notes |
|---|---|---|
| `condition_grade` | `Selection` | `a` A (like new), `b` B (light wear), `c` C (visible wear), `parts` Parts (for repair). `required=True`, `default='b'`, `tracking=True`. No index: four values is too few to be selective. Label: "Condition". |
| `battery_health` | `Integer` | Percent, 0 to 100. A `models.Constraint` (`CHECK(battery_health BETWEEN 0 AND 100)`) enforces the range (`odoo/orm/table_objects.py`). Defaults to 0 and is only meaningful when `has_battery` is true. |
| `has_battery` | `Boolean`, computed, not stored | True when `categ_id` is Laptops, Phones or Tablets or a child of one. `_compute_has_battery` depends on `categ_id.parent_path` and tests it against the three categories, found by xml id. Not stored and not searched; views use it for `invisible`. |

- Required fields on an existing table: the column default is filled by the ORM, so existing products become grade B on install.
- Access: no new model, so no `ir.access.csv`. The fields use the access rows of `product.template` (`addons/product/security/ir.access.csv`). Public visitors read published products through `product_template_public` (`addons/website_sale/security/ir.access.csv`); the fields have no `groups=`, so the shop can render them.

## Categories

`data/product_category_data.xml` (always loaded, because `has_battery` depends on it) creates four `product.category` records under `product.product_category_goods` (`addons/product/data/product_data.xml`): Laptops, Phones, Tablets, Accessories. The first three carry the battery figure; Accessories do not. A new category under Laptops, Phones or Tablets gets the battery field with no code change.

## Back office views

All in `views/product_template_views.xml`, inheriting the Odoo views by full id. Anchors are in `addons/product/views/product_views.xml` and `addons/product/views/product_template_views.xml`.

| Place | Inherits | What is added |
|---|---|---|
| Form | `product.product_template_form_view`, after `type` in `group_general` | `condition_grade` with `widget="badge"` and `decoration-success="condition_grade == 'a'"`, `decoration-info` for `b`, `decoration-warning` for `c`, `decoration-danger` for `parts`. `battery_health` with `widget="progressbar"` and `options="{'max_value': 100, 'editable': True}"`, `invisible="not has_battery"`. `has_battery` is added as `invisible="1"` so the expressions can read it. |
| List | `product.product_template_tree_view`, after `name` | Same badge, and `battery_health` as a progress bar. The battery cell is empty for rows where `has_battery` is false (`invisible="not has_battery"`). Both columns are `optional="show"`; `has_battery` is added with `column_invisible="True"`. |
| Kanban | `product.product_template_kanban_view`, inside the card `main`, below the name | Grade badge. Declare `has_battery` and `condition_grade` fields. |
| Search | `product.product_template_search_view` | Filters Grade A, B, C, Parts (`domain` on `condition_grade`) and a group-by "Condition" (`context="{'group_by': 'condition_grade'}"`), added in the filter and `group` sections. |

Badge classes are Bootstrap `text-bg-*` classes produced by the badge widget (`addons/web/static/src/views/fields/badge/badge_field.js`). Their colors come from the brand variables below, so A is Sea Green, B Cerulean, C Marigold and Parts Raspberry.

Views use `<list>`, `invisible="expr"` and the `card` kanban template; never `tree`, `attrs` or `kanban-box` (`AGENTS.md` section 8).

## Web shop

`views/product_templates.xml` inherits `website_sale.product_title` (`addons/website_sale/templates/product_page_templates.xml`) with an xpath after the product name `h1`. It renders, inside one `div`:

- a grade badge from `product.condition_grade` with `t-field`, classes matching the back office colors;
- when `product.has_battery`, the text "Battery health" and a Bootstrap progress bar whose width is `product.battery_health` percent, with the number and a percent sign.

It is a plain QWeb template. The shop grid and tiles are not changed. The values do not depend on the selected variant, so they are rendered by QWeb and do not go through `_get_combination_info` (`addons/website_sale/models/product_template.py`).

The page SCSS (`frontend.scss`, `web.assets_frontend`) uses fixed brand colors, not shop theme variables. Classes are prefixed `o_take_ownership_`. Odoo's `.badge` rule forces `background` and `color` with `!important` from `--badge-bg` and `--badge-color`, so the grade colors are set through those variables.

## Sample data

Loaded only with demo data (`--with-demo`).

- `demo/product_demo.xml` creates ten `product.template` records. Each has a photo (`image_1920` from `static/img/<file>` with `type="base64" file=`), a grade, a battery figure where `has_battery`, a `list_price`, `type` `consu`, `sale_ok`, `is_published`, and a shop category.
- Photos are the files in `docs/photos/`, copied to `static/img/` together with `CREDITS.md`, so the credits go with the photos (`docs/photos/CREDITS.md`).
- Categories: Laptops: MacBook Air (M1), Lenovo ThinkPad T14, Dell XPS 13. Phones: iPhone 13 Pro, Google Pixel 6, Fairphone 4. Tablets: iPad 10.2-inch, Samsung Galaxy Tab S8 Ultra. Accessories: Baseus 20 W USB-C charger, AirPods Pro (2nd generation).
- The same four names are created as `product.public.category` records for the shop sidebar, and each device is linked to its one.
- Grades, battery figures and prices are chosen for the sample, and cover all four grades. Accessories have no battery figure.
- `demo/archive_odoo_demo_products.xml` sets `active` to false on Odoo's demo `product.template` records by their full xml ids (for example `product.product_product_1`), so lists and the shop show only our devices. It covers the demo files that load with `website_sale` (`addons/product/data/product_demo.xml`, `addons/sale/data/product_demo.xml`, `addons/website_sale/data/demo.xml`). Data products such as shipping and down payment are not archived.

## Back office brand

Values come from `.claude/skills/brand/SKILL.md`. Light mode only: `color_scheme()` is not overridden and no `*.dark.scss` file or `web.assets_web_dark` entry exists (`addons/web/models/ir_http.py`).

| Item | Value |
|---|---|
| Primary | Sea Green `#06D6A0` with Midnight text |
| Secondary, tertiary | Marigold `#FFC145`, Coral `#F78C6B`, Midnight text |
| Information | Cerulean `#118AB2`, white text |
| Alert | Raspberry `#EF476F`, white text |
| Ink | Midnight `#073B4C` on light, Sea Mist `#CDD8DB` on dark |
| Page, panels | `#F0F4F5` page, white panels and cards, rounded, no outline |
| Navbar | Midnight `#073B4C` background, Sea Mist entries |
| Fonts | Instrument Sans for headings and body, Instrument Serif for accents, JetBrains Mono for code, numbers and identifiers |

How it is wired (see `docs/specs/web-client.md`):

- `static/src/scss/primary_variables.scss` is added to `web._assets_primary_variables` with `('before', 'web/static/src/scss/primary_variables.scss', ...)`. It sets `$o-brand-primary`, `$o-success`, `$o-info`, `$o-warning`, `$o-danger`, `$o-view-background-color`, the font variables and `$o-navbar-background` (declared in `addons/web/static/src/webclient/navbar/navbar.variables.scss`) with `!default` so core values do not win.
- Fonts are variable TTF files from the Google Fonts repository, shipped in `static/fonts/` with their OFL texts and declared with `@font-face` in the addon SCSS; there is no link to Google Fonts (`skills/odoo-web-guidelines/guidelines/assets.md`).
- Component styles go in `web.assets_backend`.
- Sea Green and Marigold are too bright for small text, so text on light backgrounds uses a darkened shade and Midnight text sits on filled Sea Green or Marigold.
- No gradients and no one-sided borders.
- Money is always shown with its currency: the list and kanban use the `monetary` widget with `currency_field` as Odoo's views already do.

## Tests

`tests/test_product_grade.py`, `TransactionCase` classes in `odoo.tests`:

- a new product has grade `b`; the field is required;
- `has_battery` is true for Laptops, Phones, Tablets and a child category, false for Accessories;
- `battery_health` outside 0 to 100 raises on create and write;
- the search view filters and groups by `condition_grade` (`read_group` with the aggregates form, `odoo/orm/models.py`);
- demo: ten devices exist, none of Odoo's demo templates are active (runs with demo data);
- an `HttpCase` opens `/shop/<product>` as a public user and checks the grade and battery text, tagged `post_install` and `-at_install`.

Run on a throwaway database as in `AGENTS.md` section 6:

```
uv run python odoo-bin -c odoo.conf -d test_db -i website_sale,take_ownership --with-demo --test-tags /take_ownership --stop-after-init
```

## Install and update

First install on the shop database: `-i take_ownership --stop-after-init`. After changing fields, views, data or the manifest `assets`: `-u take_ownership --stop-after-init` (`AGENTS.md` section 5). Demo data is only loaded on a database created with `--with-demo`; on an existing database without demo data the sample devices do not appear.

## Gotchas

- `product.product_template_form_view` is a primary view shared by the product forms of other apps; xpath on `group_general`, not on an app-specific page.
- Website views are copy-on-write: if `website_sale.product_title` was edited in the builder for a website, our change goes into the base view, not the copy (`addons/website/models/ir_ui_view.py`). Check `website_id` on `ir.ui.view` if the shop page does not show the grade.
- `web._assets_primary_variables` is included by the back office, the web shop and reports (`addons/web/__manifest__.py`). Brand variables set there reach all three, so the shop's Bootstrap colors (success, info, warning, danger, primary) change with them. Shop palettes (`o-color-*`) are separate and are not touched.
- Archiving demo products by xml id breaks if a demo file renames or removes a record; the archive file must match the Odoo version in this repo.
