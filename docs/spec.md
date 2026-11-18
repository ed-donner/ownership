# How Odoo 20 is built

Overview for coding agents. Odoo 20.0 Community (`odoo/release.py`). Details per business area are linked in the index at the end. Differences from older Odoo are marked **20:**.

## Repository layout

| Path | What it is |
|---|---|
| `odoo-bin` | Entry point; dispatches to the CLI (`odoo/cli/server.py`, `odoo/cli/command.py`). |
| `odoo.conf` | Our config: `db_name`, `db_user`, `data_dir`. No `addons_path`, so Odoo uses its default. |
| `odoo/` | The framework: ORM (`odoo/orm/`), module loading (`odoo/modules/`), HTTP (`odoo/http/`), tools (`odoo/tools/`), tests (`odoo/tests/`). |
| `odoo/addons/` | Core addons shipped with the framework, including `base` (`odoo/addons/base/__manifest__.py`). |
| `addons/` | All other modules: Odoo's own apps and our own. Odoo's modules stay unchanged. |
| `docs/specs/` | Area files, see the index below. |

- Command-line options (`-i`, `-u`, `--test-enable`, `--test-tags`, `--dev`) are defined in `odoo/tools/config.py`.
- Upgrade scripts live in `odoo/upgrade/` and `odoo/upgrade_code/`.

## Modules

- A module is a folder with __manifest__.py (the only manifest name, `MANIFEST_NAMES` in `odoo/modules/module.py`). The manifest is a Python dict.
- Keys and defaults: `_DEFAULT_MANIFEST` in `odoo/modules/module.py`. Notable keys: `depends`, `data`, `demo`, `assets`, `auto_install`, `application`, `installable`, `post_init_hook`, `pre_init_hook`, `uninstall_hook`, `license`.
- `depends` empty means `['base']`, except for `base` itself (`odoo/modules/module.py`). Load order follows the dependency graph (`odoo/modules/module_graph.py`).
- `auto_install`: `True` installs the module once all its `depends` are installed. A list makes only those names the triggers and they must be a subset of `depends` (`odoo/modules/module.py`).
- `data` files load at install and update, in the listed order. Order matters: a view must be loaded before views or actions that reference it (see the comments in `addons/sale/__manifest__.py`). `demo` files load only on a database with demo data.
- File loading is done by `odoo/tools/convert.py`: XML via `convert_xml_import`, CSV via `convert_csv_import`.
- Lifecycle: modules are registered in `ir.module.module` (`odoo/modules/db.py`, `odoo/addons/base/models/ir_module.py`). `-i` installs, `-u` updates, uninstall runs `uninstall_hook`. Module loading is in `odoo/modules/loading.py`; data migrations in `odoo/modules/migration.py`.
- A module extends another by depending on it and using `_inherit` (models), `inherit_id` (views) and bundle entries (assets).
- Scaffold a module with `odoo/cli/scaffold.py` (templates in `odoo/cli/templates/`).
- Every module in `addons/` is listed in [modules.md](specs/modules.md).

## ORM

Code is in `odoo/orm/`; addons import it through `from odoo import api, fields, models`, which are thin packages (`odoo/models/__init__.py`, `odoo/fields/__init__.py`, `odoo/api/__init__.py`).

- Models: classes in `odoo/orm/models.py` (`BaseModel`), with `models.Model`, `TransientModel` (`odoo/orm/models_transient.py`) and `AbstractModel`. Class definitions are assembled by `odoo/orm/model_classes.py`; the registry is `odoo/orm/registry.py`.
- Fields: `odoo/orm/fields*.py` (basic `odoo/orm/fields.py`, relational `odoo/orm/fields_relational.py`, selection, temporal, textual, numeric, binary, properties).
- **20:** `_sql_constraints` is no longer supported and only logs a warning (`odoo/orm/model_classes.py`). Use `models.Constraint` and `models.Index` / `models.UniqueIndex` (`odoo/orm/table_objects.py`).
- **20:** fields can have `compute_sql` (SQL expression for search, group and order of computed fields), `aggregator`, `group_expand`, `bypass_search_access` (`odoo/orm/fields.py`).
- Decorators (`odoo/orm/decorators.py`): `constrains`, `depends`, `depends_context`, `onchange`, `ondelete(at_uninstall=...)`, `model`, `model_create_multi`, `autovacuum`, `readonly`, `private`. **20:** `@api.private` marks methods not callable over RPC.
- Inheritance: `_inherit` with the same `_name` extends in place; `_inherit` with a new `_name` copies; `_inherit` list mixes in abstract models; `_inherits = {...}` delegates to a parent record (docstring in `odoo/orm/models.py`).
- Recordsets: `browse`, `exists`, `ensure_one`, `mapped`, `filtered`, `sorted`, `with_context`, `with_user`, `with_company`, `sudo`, `with_env` (`odoo/orm/models.py`). Environment is `odoo/orm/environments.py`; use `self.env._("text")` for translations (`Environment._`).
- Write commands for x2many: `Command` enum (`odoo/orm/commands.py`).
- Domains: the `Domain` class (`odoo/orm/domains.py`), importable as `odoo.fields.Domain`. Lists of tuples still work. **20:** extra operators `any!`, `not any!` and `access` for many2one and `id` fields.
- APIs: `create(vals_list)` takes a list (`odoo/orm/models.py`); `write`, `unlink`, `search`, `search_count`, `search_fetch`, `search_read`, `read`, `fetch`, `copy`, `name_search`.
- **20:** `read_group` takes `aggregates` and returns tuples (`odoo/orm/models.py`). The web client uses `formatted_read_group`, `web_read`, `web_save`, `web_search_read` (`addons/web/models/models.py`).
- Display names: override `_compute_display_name` (`odoo/orm/models.py`); there is no `name_get`.
- Flush and cache: `flush_model`, `invalidate_model` on models; `flush_all`, `invalidate_all` on `env` (`odoo/orm/environments.py`).

## Views and inheritance

- View records are `ir.ui.view` (`odoo/addons/base/models/ir_ui_view.py`). Types in the `type` selection: list, form, graph, pivot, calendar, kanban, search, card, qweb (`odoo/addons/base/models/ir_ui_view.py`; RNG schemas in `odoo/addons/base/rng/`, including `activity_view.rng`). Window action modes: list, form, graph, pivot, calendar, kanban (`odoo/addons/base/models/ir_actions.py`).
- **20:** the list view tag is `<list>`, not `<tree>`. Window action modes use `list` (`odoo/addons/base/models/ir_actions.py`).
- `attrs=` and `states=` are rejected at validation (since 17.0, see the error message): use `invisible`, `readonly`, `required` with Python expressions (`odoo/addons/base/models/ir_ui_view.py`). In list views hide a column with `column_invisible` (`odoo/addons/base/rng/common.rng`).
- Inheritance: a view record with `inherit_id` and `<xpath expr="..." position="...">` (or shortcut elements such as `<field name="x" position="after">`). Positions: `inside`, `replace`, `after`, `before`, `attributes`, `move` (`odoo/tools/template_inheritance.py`, `odoo/addons/base/models/ir_ui_view.py`). Example: `addons/sale/views/product_template_views.xml`.
- Loading: records in data XML are parsed by `odoo/tools/convert.py`, validated against the RNG schemas, and `ir.ui.view` combines the parent and its extensions at read time (`odoo/addons/base/models/ir_ui_view.py`).
- Groups on elements: `groups="module.group"`, negation with `!` (`addons/sale/views/sale_order_views.xml`).
- Menus and actions: `ir.ui.menu` (`odoo/addons/base/models/ir_ui_menu.py`), `ir.actions.*` (`odoo/addons/base/models/ir_actions.py`).
- Server-side QWeb (website pages, reports, emails) is `ir.qweb` (`odoo/addons/base/models/ir_qweb.py`).
- XML data files use `<odoo>` with `<record>`, `<template>`, `<menuitem>` (`addons/sale/security/res_groups.xml` as a minimal example).

## Assets

- Bundles are declared in the manifest `assets` dict, keyed by bundle name (`addons/web/__manifest__.py`, `addons/sale/__manifest__.py`). Main bundles: `web.assets_backend`, `web.assets_frontend`, `web.assets_tests`, `web.assets_unit_tests_setup`.
- Entries are globs of JS, SCSS and XML files. Directives: `include`, `prepend`, `append`, `after`, `before`, `remove`, `replace` (`odoo/addons/base/models/ir_asset.py`). Example: `('include', 'web._assets_core')` and `('remove', ...)` in `addons/web/__manifest__.py`.
- `ir.asset` records can add the same directives from data (`odoo/addons/base/models/ir_asset.py`). Bundles are built and cached by `odoo/addons/base/models/assetsbundle.py`.
- SCSS: Bootstrap variables are overridden in `addons/web/static/src/scss/primary_variables.scss` and `addons/web/static/src/scss/secondary_variables.scss`. Files ending .dark.scss are only for the dark bundles (`addons/web/__manifest__.py`).
- Client QWeb templates are .xml files under static/src/, listed in a bundle by path or glob.
- **20:** JS files use ES module `import`/`export` with @web/... aliases and no `@odoo-module` header. The loader is `addons/web/static/src/module_loader.js`; `// @odoo-module ignore` opts a file out.
- `--dev` accepts `access`, `qweb`, `reload`, `xml` or `all` (`ALL_DEV_MODE` in `odoo/tools/config.py`). Unminified, auto-regenerated bundles come from the `debug=assets` URL parameter (`odoo/addons/base/models/ir_qweb.py`), not from `--dev`.

## Security

- **20:** `ir.model.access` and `ir.rule` no longer exist. Both are replaced by the single model `ir.access` (`odoo/addons/base/models/ir_access.py`).
- Files are named security/ir.access.csv with columns `id,name,model_id,group_id/id,operation,domain` (`odoo/addons/base/security/ir.access.csv`, `addons/product/security/ir.access.csv`). List the file in the manifest `data`, usually last (`addons/sale/__manifest__.py`).
- `operation` is a subset of `crud`, one string such as `r`, `cru`, `crud` (`CRUD_SELECTION` in `odoo/addons/base/models/ir_access.py`).
- A row with a group is a permission; a row with an empty group is a restriction that applies to everyone (`_compute_kind` in `odoo/addons/base/models/ir_access.py`). A `domain` limits the rows the access covers, like the old record rules (`addons/sale/security/ir.access.csv`).
- Checking: `check_access(operation)` raises `AccessError`, `has_access(operation)` returns a bool, `_filtered_access(operation)` filters (`odoo/orm/models.py`). The old `check_access_rights` and `check_access_rule` are gone.
- Groups: `res.groups` (`odoo/addons/base/models/res_groups.py`). **20:** groups belong to a `res.groups.privilege` (`odoo/addons/base/models/res_groups_privilege.py`), which replaces the old category-based group setup. Example: `addons/product/security/product_security.xml`.
- **20:** user groups field is `group_ids` (was `groups_id`); `all_group_ids` includes implied groups (`odoo/addons/base/models/res_users.py`). Groups have `implied_ids` and `implied_by_ids` (`addons/product/security/product_security.xml`).
- Field-level groups: `groups=` on the field definition (`odoo/orm/fields.py`). View-level: `groups=` on elements.
- `sudo()` bypasses access (`odoo/orm/models.py`); keep it narrow. Audit rules are in the `odoo-security` skill (`skills/odoo-security`).
- Controllers pick `auth='user'`, `'public'` or `'none'` (`odoo/http/`).

## Tests

- Python tests live in tests/ inside each module and are imported from tests/__init__.py (`addons/sale/tests/`). Framework: `odoo/tests/`.
- Classes: `TransactionCase` (rolled back per test) and `HttpCase` (browser, `url_open`, `start_tour`) in `odoo/tests/common.py`; `Form` for form-view emulation (`odoo/tests/form.py`). Helpers: `new_test_user`, `RecordCapturer`, `freeze_time` (`odoo/tests/common.py`).
- Tags: `@tagged(...)`; the default is `standard` and `post_install` (`odoo/tests/common.py`). A test is `at_install` or `post_install`, not both. `HttpCase` should be `post_install`.
- Selector syntax `[-][tag][/module][:class][.method]` is parsed in `odoo/tests/tag_selector.py`.
- Run: `-u <module> --test-enable --stop-after-init` or `--test-tags` (`odoo/tools/config.py`).
- JS unit tests use Hoot: files *.test.js under static/tests/, loaded through the `web.assets_unit_tests_setup` bundle (`addons/web/__manifest__.py`) and run by `addons/web/tests/test_js.py`. Example: `addons/sale/static/tests/sale_product_field.test.js`.
- Tours: JS in static/tests/tours/ registered with `registry.category("web_tour.tours")` (`addons/sale/static/tests/tours/product_attribute_value_tour.js`), started from Python with `start_tour` (`odoo/tests/common.py`).
- Test addons for the framework itself are in `odoo/addons/test_*`.

## Web client

- JS is in `addons/web/static/src/`: core/ (primitives), views/, search/, webclient/, model/, public/ (website frontend), scss/. Entry: `addons/web/static/src/start.js`, `addons/web/static/src/env.js`.
- **20:** Owl is 3.x alpha (`addons/web/static/lib/owl/owl.js`, `static version = "3.0.0-alpha.50"`). Reactive state uses `proxy` and `usePlugin`, as in `addons/web/static/src/webclient/webclient.js`. Plugins sit next to services: `addons/web/static/src/core/orm_plugin.js`, `addons/web/static/src/core/debug_mode_plugin.js`.
- Registries: `registry.category("name").add(key, value, {sequence})` (`addons/web/static/src/core/registry.js`). Common categories: `systray` (see `addons/web/static/src/webclient/webclient.js`), `web_tour.tours`, plus `actions`, `views`, `fields`, `services`.
- Services: used with `useService("orm")` (`addons/web/static/src/core/utils/hooks.js`); `addons/web/static/src/webclient/session_service.js` and `addons/web/static/src/webclient/reload_company_service.js` are examples.
- Templates use `t-out` for output; `t-esc` is rare in the web core (`addons/web/static/src/webclient/webclient.xml`).
- Views: one folder per type in `addons/web/static/src/views/` (form, list, kanban, graph, pivot, calendar), compiled by `addons/web/static/src/views/view_compiler.js`.
- Tours: `addons/web_tour/static/src/` (`addons/web_tour/static/src/tour_plugin.js`, `addons/web_tour/static/src/tour_step.js`, tour_automatic/, tour_recorder/).
- Third-party libs are in `addons/web/static/lib/` (Owl, Bootstrap, Luxon, Hoot, Chart, FullCalendar).
- Theming and area detail: [web-client.md](specs/web-client.md).

## Index of area files

- [Modules](specs/modules.md): one line per module in `addons/`, generated from manifests.
- [Products](specs/products.md)
- [Sales](specs/sales.md)
- [Invoicing](specs/invoicing.md)
- [Inventory](specs/inventory.md)
- [Web shop](specs/web-shop.md)
- [Web client and theming](specs/web-client.md)
