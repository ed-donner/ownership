# AGENTS.md

Guide for coding agents working in this repo. Every claim cites a repo path. Deeper docs: `docs/spec.md` and `docs/specs/`.

## 1. What this repo is

- A fork of Odoo 20.0 Community (`odoo/release.py` has `version_info = (20, 0, ...)`), about 665 modules in `addons/` and `odoo/addons/`.
- The business is Take Ownership, a shop selling refurbished laptops, phones and tablets (`README.md`).
- Python 3.12 to 3.14 (`odoo/release.py`: `MIN_PY_VERSION`, `MAX_PY_VERSION`).
- Three branches (`README.md`): `main` (plain Odoo plus skills and photos), `documented` (adds `AGENTS.md`, `docs/spec.md`, `docs/specs/`), `completed` (adds addons/take_ownership).
- Odoo's house-rule skills are in `skills/` (`skills/odoo-guidelines/SKILL.md`, `skills/odoo-web-guidelines/SKILL.md`, `skills/odoo-security/SKILL.md`, `skills/odoo-review/SKILL.md`, `skills/odoo-git/SKILL.md`). Use them when writing addon code.

## 2. Hard rules

- Our changes go only in our own addons under `addons/`, for example addons/take_ownership. Customize Odoo's modules by inheriting from them (`_inherit` in Python, `inherit_id` and xpath in XML), never by editing them.
- Never edit `odoo/` or any Odoo-owned module in `addons/` (`addons/product`, `addons/sale`, `addons/website_sale`, ...).
- Do not commit `odoo.conf` or `.odoo-data`. `.gitignore` ignores `/odoo.conf`, and its dotfile rule (`.*`) covers `.odoo-data`.
- Do not touch the shop database for experiments; use a throwaway database (section 6).
- Demo and photo credits stay with the photos (`docs/photos/CREDITS.md`).

## 3. Setup

Requires git, uv and PostgreSQL 16 or later (`README.md`). Install PostgreSQL and create a database user:

```
createuser --createdb odoo
```

On Windows, create the role in psql with `CREATE ROLE odoo LOGIN CREATEDB PASSWORD 'odoo';` (`README.md`).

Create `odoo.conf` in the repo root (`README.md`):

```
[options]
db_name = ownership
db_user = odoo
data_dir = .odoo-data
```

On Windows also add `db_password = odoo` and `db_template = template1`. `--db-template` defaults to `template0` (`odoo/tools/config.py`).

Python environment (always uv, never pip or bare python):

```
uv venv --python 3.12
uv pip install -r requirements.txt
```

Create the shop database with the web shop and demo data (a few minutes):

```
uv run python odoo-bin -c odoo.conf -i website_sale --with-demo --stop-after-init
```

Flags: -i/--init, `--with-demo`, `--stop-after-init` are defined in `odoo/tools/config.py`. `--with-demo` only applies to newly created databases.

## 4. Run

Start the server as a background task with the Bash tool's `run_in_background`:

```
uv run python odoo-bin -c odoo.conf
```

- Default port is 8069 (`odoo/tools/config.py`, `--http-port`). Web shop: http://localhost:8069/shop. Back office login: `admin` and the password `admin` (`README.md`).
- Check it is up with `curl -s http://localhost:8069/web/health` (route in `addons/web/controllers/home.py`), and watch the task output for the "HTTP service ... running" log line.
- Stop it by stopping that background task (TaskStop on its task id). Never use `pkill`, `kill` or `killall`.
- Only one server per port. If a task is already running, stop it before running `-u` or tests against the same database.
- Developer features: `--dev=xml` reads views from source files instead of the database, `--dev=reload` restarts on Python changes, `--dev=all` gives access, reload, qweb, xml (`odoo/tools/config.py`, `ALL_DEV_MODE`). Env var form is `ODOO_DEV`.

## 5. Update after changes

| Change | What to do |
|---|---|
| New addon, first time | `-i <module> --stop-after-init` (`odoo/tools/config.py`). The addon directory must be under an addons path, `addons/` already is. |
| Python model code only | Restart the server task. No upgrade needed unless fields changed. |
| New or changed fields, XML views, data, security CSV, manifest `data` | Stop the server, run `-u <module> --stop-after-init`, start again. |
| XML views while developing | Start with `--dev=xml` and the view is read from the file; still run `-u` before finishing. |
| JS, SCSS, QWeb templates in static/ | Declared in the manifest `assets` key (`addons/web_hierarchy/__manifest__.py` is a short example). Reload the page with `?debug=assets` to regenerate bundles on file change (`odoo/addons/base/models/ir_qweb.py`). A changed `assets` list needs `-u`. |

```
uv run python odoo-bin -c odoo.conf -u take_ownership --stop-after-init
```

- `-u all` and `--reinit` exist (`odoo/tools/config.py`) but are slow and rarely needed.
- `-i`/`-u` accept only one database (`odoo/tools/config.py`: "Cannot use -i/--init or -u/--update with multiple databases").
- To start from a clean shop, change `db_name` in `odoo.conf` (for example `ownership2`) and rerun the create command (`README.md`).

## 6. Test

Run an addon's tests against a throwaway database so the shop database is untouched:

```
uv run python odoo-bin -c odoo.conf -d test_db -i website_sale,take_ownership --with-demo --test-tags /take_ownership --stop-after-init
```

- `-d` overrides `db_name` from `odoo.conf`. `test_db` is created if missing. Drop it afterwards with `dropdb test_db`.
- `--test-tags` enables tests and implies `--stop-after-init` (`odoo/tools/config.py`). `--test-enable` runs all tests.
- Tag spec format `[-][tag][/module][:class][.method]` (`odoo/tools/config.py`, `odoo/tests/tag_selector.py`). Examples: /take_ownership, `/take_ownership:TestGrade.test_default`, `:TestGrade`, `-slow`.
- Tests run twice: right after each module install (`at_install`) and at the end of loading (`post_install`) (`odoo/tools/config.py`). Every test class is `standard` and `post_install` by default (`odoo/tests/common.py`, `tagged`).
- To rerun on an existing test database use `-u take_ownership` in place of `-i`.

Writing tests:

- Python tests live in tests/ of the addon; tests/__init__.py imports each test_*.py (see `addons/product/tests/__init__.py`).
- Import from `odoo.tests`: `from odoo.tests import TransactionCase, HttpCase, tagged, Form` (`odoo/tests/__init__.py`, `odoo/tests/common.py`). Example: `addons/product/tests/test_barcode.py`.
- `TransactionCase` rolls back each test; `HttpCase` adds a headless browser, `browser_js` and `start_tour` (`odoo/tests/common.py`). Tour example: `addons/website_sale/tests/test_cart_notification.py`.
- JS unit tests are Hoot files named *.test.js, declared in the manifest bundle `web.assets_unit_tests` (`addons/product/__manifest__.py`, `addons/product/static/tests/product_pricelist_report.test.js`). The Python runner is `addons/web/tests/test_js.py` (classes tagged `hoot`, for example `--test-tags hoot`, which runs every module's JS tests and is slow); a browser runner for a single module is easier while developing. Tours are JS registered in `web.assets_tests` (`addons/website_sale/__manifest__.py`) and run from Python with `start_tour`.
- JS test guidance: `skills/odoo-web-guidelines/guidelines/tests.md`. Python: `skills/odoo-guidelines/guidelines/tests.md`.

## 7. Layout of a new addon

```
addons/take_ownership/
  __init__.py            # from . import models
  __manifest__.py
  models/__init__.py
  models/product_template.py     # one file per model, named after it
  views/product_template_views.xml
  security/ir.access.csv         # only if you add new models
  data/                          # *_data.xml, always loaded
  demo/                          # *_demo.xml, demo mode only
  static/src/...                 # JS, OWL XML, SCSS
  static/tests/...               # Hoot tests
  tests/__init__.py, test_*.py
```

Naming rules: `skills/odoo-guidelines/guidelines/module_structure.md`. Manifest rules: `skills/odoo-guidelines/guidelines/manifest.md`.

Minimal manifest (keys as in `addons/product/__manifest__.py`):

```python
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Take Ownership',
    'version': '1.0',
    'category': 'Sales/Sales',
    'depends': ['product', 'website_sale'],
    'data': ['views/product_template_views.xml'],
    'demo': ['data/take_ownership_demo.xml'],
    'assets': {
        'web.assets_backend': ['take_ownership/static/src/**/*'],
        'web.assets_frontend': ['take_ownership/static/src/frontend/**/*'],
    },
    'license': 'LGPL-3',
}
```

- Bundle names: `web.assets_backend`, `web.assets_frontend`, `web.assets_unit_tests`, `web.assets_tests` (`addons/web/__manifest__.py`, `addons/website_sale/__manifest__.py`).
- Brand SCSS variables go in `web._assets_primary_variables` (`addons/website_sale/__manifest__.py` does this).
- Do not list `base` in `depends` (`skills/odoo-guidelines/guidelines/manifest.md`).

## 8. Mistakes an agent trained on older Odoo versions would make

Each item: old way, 20.0 way, proof.

- [ ] **Access rules in two places.** Old: ir.model.access.csv plus `ir.rule` records. 20.0: one model `ir.access`, file security/ir.access.csv with columns `id,name,model_id,group_id/id,operation,domain`; rows with a group grant, rows without a group restrict. Proof: `odoo/addons/base/models/ir_access.py`, `addons/product/security/ir.access.csv`, `skills/odoo-guidelines/guidelines/security.md`.
- [ ] **`groups_id` and `res.groups.category_id`.** Old: `user.groups_id`, `category_id` on groups. 20.0: `group_ids` on users, `privilege_id` on groups (model `res.groups.privilege`), `user_ids` and `implied_by_ids` on groups. Proof: `odoo/addons/base/models/res_users.py` (`group_ids`), `odoo/addons/base/models/res_groups.py` (`privilege_id`, `user_ids`, `implied_by_ids`), `addons/product/security/product_security.xml`, `odoo/addons/base/models/res_groups_privilege.py`.
- [ ] **`check_access_rights` / `check_access_rule`.** Old: two calls. 20.0: `check_access(operation)`, `has_access(operation)`, `_filtered_access(operation)`. Proof: `odoo/orm/models.py` (`def check_access`, `def has_access`).
- [ ] **`attrs=` and `states=` in views.** Old: `attrs="{'invisible': [...]}"`. 20.0: direct `invisible="expr"`, `readonly="expr"`, `column_invisible="True"`; views with `attrs` or `states` raise a ValidationError. Proof: `odoo/addons/base/models/ir_ui_view.py` ("the \"attrs\" and \"states\" attributes are no longer used"), `addons/product/views/product_template_views.xml`.
- [ ] **`<tree>` views.** Old: `<tree>` and `view_mode` `tree`. 20.0: `<list>` and `view_mode` `list`. Proof: `addons/product/views/product_template_views.xml` (`</list>`), `odoo/addons/base/rng/list_view.rng`, no `tree_view.rng` exists in `odoo/addons/base/rng/`.
- [ ] **Kanban `kanban-box`.** Old: `<t t-name="kanban-box">`. 20.0: `<t t-name="card">`. Proof: `addons/product/views/product_template_views.xml`.
- [ ] **Chatter markup.** Old: `<div class="oe_chatter">` with message fields. 20.0: `<chatter/>`. Proof: `addons/sale/views/sale_order_views.xml`.
- [ ] **`name_get` and `_name_search`.** Old: override `name_get()` and `_name_search()`. 20.0: compute `display_name` with `_compute_display_name`, customize search by overriding `_search_display_name(operator, value)` or setting `_rec_names_search`. `name_search` still exists as a public method. Proof: `odoo/orm/models.py`, `addons/product/models/product_template.py`.
- [ ] **`_sql_constraints`.** Old: list of tuples. 20.0: class attributes `models.Constraint(definition, message)` and `models.Index(...)`; `_sql_constraints` is ignored with a warning. Proof: `odoo/orm/model_classes.py`, `odoo/orm/table_objects.py`, `addons/product/models/product_attribute.py`, `addons/sale/models/sale_order.py`.
- [ ] **`read_group` usage.** Old: `read_group` returns list of dicts. 20.0: `read_group` and `_read_group` take `aggregates` specs like `'field:sum'` and return tuples; the web client uses `formatted_read_group` and `web_read_group` for dicts. Proof: `odoo/orm/models.py` (`def read_group`, `def _read_group`), `addons/web/models/models.py` (`def formatted_read_group`).
- [ ] **`/** @odoo-module */` and `odoo.define`.** Old: every JS file starts with `/** @odoo-module */`, legacy `odoo.define` widgets, `require`. 20.0: files under static/src and static/tests of an addon are transpiled as ES modules without the annotation (it is only needed elsewhere, and `@odoo-module ignore` opts out); write `import { x } from "@odoo/owl"` and @web/... paths. Proof: `odoo/tools/js_transpiler.py` (`is_odoo_module`), `addons/web/static/src/core/registry.js`, `addons/product/static/src/product_catalog/kanban_controller.js`.
- [ ] **jQuery and legacy widgets.** Old: `$(...)`, `publicWidget.registry`, `Widget.extend`. 20.0: no jQuery library in `addons/web/static/lib/`; the web client is OWL components and the website uses `Interaction` classes. Proof: `addons/web/static/lib/` (listing has `owl`, no jquery), `addons/website_sale/static/src/interactions/wishlist_navbar.js`, `addons/web/static/src/public/interaction_service.js`.
- [ ] **Assets in XML templates.** Old: `<template inherit_id="web.assets_backend">` with `<script>` tags. 20.0: the manifest `assets` dict only, with globs, `('remove', ...)` and `('before', ...)` directives. Proof: `addons/web/__manifest__.py`, `addons/web_hierarchy/__manifest__.py`.
- [ ] **`type='json'` routes.** Old: `@http.route(type='json')`. 20.0: `type='jsonrpc'`; `json` is a deprecated alias that logs a warning. Proof: `odoo/http/routing_map.py`, `addons/website_sale/controllers/main.py`.
- [ ] **Product type.** Old: `detailed_type` (consu/service/product). 20.0: `type` plus the boolean `is_storable` (Track Inventory). Proof: `addons/product/models/product_template.py` (`is_storable`, no `detailed_type`).
- [ ] **Company-dependent fields.** Old: `ir.property` records. 20.0: `company_dependent=True` stores a jsonb dict on the model table, defaults come from `ir.default`; no `ir_property` model exists. Proof: `odoo/orm/fields.py` (docstring of `company_dependent`), `odoo/addons/base/models/` (no ir_property.py).
- [ ] **Test base classes and run flags.** Old: `SavepointCase`, `SingleTransactionCase`, `--test-enable` alone. 20.0: `TransactionCase` and `HttpCase` from `odoo.tests`; `--test-tags` enables testing by itself; every class defaults to `standard` and `post_install`. Proof: `odoo/tests/common.py`, `odoo/tools/config.py`.
- [ ] **Dev flags.** Old: `--dev=all`, `--dev=pdb`. 20.0: features are `access`, `qweb`, `reload`, `replica`, `xml`; `all` expands to `access,reload,qweb,xml`. Proof: `odoo/tools/config.py`.

Things that did not change and are safe: `@api.model_create_multi` is still the way to write `create` (`odoo/orm/decorators.py`), `Command` tuples helper in `odoo/orm/commands.py`, `tracking=True` on fields (`addons/product/models/product_category.py`), `_()` from `odoo` (`addons/product/models/product_template.py`), `@api.depends` and `@api.constrains` (`odoo/orm/decorators.py`). `@api.multi` and `@api.one` do not exist in `odoo/orm/decorators.py`. `odoo/orm/domains.py` has a `Domain` class for building domains.

## 9. Pointers

- `docs/spec.md`: how Odoo is built (modules, ORM, views, assets, security, tests, web client).
- `docs/specs/modules.md`: one line per module in `addons/`, generated by `docs/gen_modules.py`.
- `docs/specs/`: one area file each for products, sales, invoicing, inventory, the web shop, and the web client with theming.
