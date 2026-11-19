# Web client and theming

Area spec for agents customizing the back office UI and its look. Covers `addons/web` (the Owl web client, asset bundles, SCSS variables) and `addons/html_editor` (HTML field editor). There is no `web_editor` in 20.0; `addons/html_editor` replaces it, and the website builder lives in `addons/html_builder`. Brand values (Instrument Sans, Sea Green `#06D6A0`, Midnight `#073B4C`) are in `.claude/skills/brand/SKILL.md`, and `addons/take_ownership` applies them to the back office (see [take-ownership.md](take-ownership.md)); JS/SCSS house rules are in `skills/odoo-web-guidelines/SKILL.md` and `skills/odoo-web-guidelines/guidelines/`.

## Key files

| Path | What it holds |
|---|---|
| `addons/web/__manifest__.py` | Every core asset bundle: `web.assets_backend`, `web.assets_web`, `web.assets_web_dark`, `web.assets_frontend`, the `_assets_*` sub bundles, test bundles |
| `addons/web/static/src/main.js` | Entry point; calls `startWebClient(WebClient)` |
| `addons/web/static/src/start.js` | `startWebClient`: session info, localization, mounts the root component |
| `addons/web/static/src/env.js` | Builds the Owl app and env, starts the plugins listed in `services` |
| `addons/web/static/src/module_loader.js` | Odoo's own JS module loader (`odoo.define`, `odoo.loader`); runs before everything else |
| `addons/web/static/src/core/registry.js` | `Registry` class; `registry.category("name")` is the extension mechanism |
| `addons/web/static/src/core/services.js` | `services` Resource: global plugins (formerly services) started by the framework |
| `addons/web/static/src/core/utils/patch.js` | `patch(obj, extension)` for monkey patching classes and prototypes |
| `addons/web/static/src/core/template_inheritance.js` | Owl template inheritance (`t-inherit`) |
| `addons/web/static/src/webclient/webclient.js` | Root `WebClient` component, systray and menu wiring |
| `addons/web/static/src/webclient/actions/action_plugin.js` | Action manager; `actions` and `action_handlers` registries |
| `addons/web/static/src/views/view.js` | The `View` component that loads fields, arch and picks the view from the `views` registry |
| `addons/web/static/src/views/list/list_view.js`, `addons/web/static/src/views/kanban/kanban_view.js`, `addons/web/static/src/views/form/` | View definitions registered in `views` |
| `addons/web/static/src/views/fields/` | One folder per field widget, registered in `fields` (e.g. `addons/web/static/src/views/fields/char/char_field.js`) |
| `addons/web/static/src/scss/primary_variables.scss` | Brand colors, fonts, grays, font sizes; every variable is `!default` |
| `addons/web/static/src/scss/secondary_variables.scss` | Variables derived from the primary ones |
| `addons/web/static/src/scss/bootstrap_overridden.scss` | Backend Bootstrap variable overrides |
| `addons/web/static/src/**/*.variables.scss` | Per-component variables (e.g. `addons/web/static/src/webclient/navbar/navbar.variables.scss`), auto-included in primary variables |
| `addons/web/static/src/**/*.dark.scss` | Dark-mode-only styles, e.g. `addons/web/static/src/core/datetime/datetime_picker.dark.scss` |
| `addons/web/views/webclient_templates.xml` | `webclient_bootstrap` template: which bundle the back office loads |
| `addons/web/models/ir_http.py` | `color_scheme()` and `session_info()` passed to the page |
| `odoo/addons/base/models/ir_asset.py` | `ir.asset` model and the bundle directive logic |
| `addons/website/static/src/scss/primary_variables.scss` | Website color palettes and theme config maps |
| `addons/website/static/src/scss/options/user_values.scss` | Website values customised by the user in the builder |
| `addons/website_sale/static/src/scss/primary_variables.scss` | Shop-specific primary variables |

## How the pieces connect

1. The `/odoo` page renders `webclient_bootstrap` which calls `web.assets_web` for JS and, for CSS, `web.assets_web` or `web.assets_web_dark` depending on `color_scheme` (`addons/web/views/webclient_templates.xml`).
2. `web.assets_web` = `web.assets_backend` + `addons/web/static/src/main.js` + `addons/web/static/src/start.js`. `web.assets_backend` pulls in helpers, Bootstrap, `web._assets_core`, then globs static/src/views/**, static/src/webclient/**, static/src/search/**, static/src/model/** (`addons/web/__manifest__.py`).
3. Other modules append to bundles by naming them in their own manifest `assets` key. Globs like my_addon/static/src/**/* work.
4. JS files are ES modules. Files under static/src are converted to `odoo.define` modules by the asset pipeline; imports use the @web/... and @odoo/owl aliases (`addons/web/static/lib/owl/odoo_module.js`, `addons/web/static/src/core/registry.js`).
5. Behavior is registered, not hard coded: `registry.category("views")`, `"fields"`, `"actions"`, `"systray"`, `"main_components"`, `"user_menuitems"` (`addons/web/static/src/views/list/list_view.js`, `addons/web/static/src/webclient/navbar/navbar.js`, `addons/web/static/src/webclient/loading_indicator/loading_indicator.js`). The XML `<field widget="x"/>` or `<list js_class="x"/>` looks the name up in those registries.
6. Global state is held by plugins registered in the `services` Resource (`addons/web/static/src/core/services.js`, `addons/web/static/src/core/orm_plugin.js`). Components get them with `usePlugin(Class)` (`addons/web/static/src/webclient/navbar/navbar.js`); `useService("name")` still exists in `addons/web/static/src/core/utils/hooks.js` and is used in `addons/web/static/src/views/view.js`.
7. SCSS order matters. Each bundle includes `web._assets_helpers`, which includes `web._assets_primary_variables` (`addons/web/static/src/scss/primary_variables.scss` plus every *.variables.scss) and `web._assets_secondary_variables`, before Bootstrap's own `addons/web/static/lib/bootstrap/scss/_variables.scss` (`addons/web/__manifest__.py`). Because variables are `!default`, whichever file sets a value first wins, so overrides must come earlier than the default.
8. The website and web shop do not use `web.assets_backend`. They use `web.assets_frontend` (`addons/web/__manifest__.py`, `addons/web/views/webclient_templates.xml`), which includes `web._assets_frontend_helpers` and the same primary variables. `website` adds its own files to `web._assets_primary_variables` (`addons/website/__manifest__.py`). Reports use `web.report_assets_common`, which also includes the primary variables.

## Colors and fonts

- Brand color: `$o-brand-primary` (default `$o-community-color`, `#71639e`) in `addons/web/static/src/scss/primary_variables.scss`. `$o-action`, link and active-component colors derive from it. Also see `$o-brand-secondary`, `$o-success`, `$o-info`, `$o-warning`, `$o-danger`.
- Fonts: `$o-font-family-sans-serif`, `$o-headings-font-family`, `$o-font-family-monospace` in the same file. Default is a system font stack; `$o-system-fonts` is wrapped by `o-add-unicode-support-font`.
- View background and borders: `$o-view-background-color`, `$o-border-color`, `$o-gray-100` to `$o-gray-900`, all in the same file.
- Tag and badge palette: `$o-colors` and `$o-colors-border` (same file).
- Per-component: edit *.variables.scss files, e.g. `addons/web/static/src/views/kanban/kanban.variables.scss`.
- Website theme: colors are `o-color-1..5` palettes in `$o-color-palettes` (`addons/website/static/src/scss/primary_variables.scss`); fonts and buttons are keys in the website theme maps in that file. Prefer adding a palette or a `theme_*` module over editing core files; `addons/theme_default/__manifest__.py` is the minimal example of a theme module.
- Fonts must ship in the addon (`skills/odoo-web-guidelines/guidelines/assets.md`): put font files in static/fonts/, declare `@font-face` in your SCSS, do not link to Google Fonts.

## Dark mode

- `web.assets_web_dark` = `web.assets_web` + every *.dark.scss (`addons/web/__manifest__.py`). `web.assets_backend` explicitly removes *.dark.scss, so dark rules written in a .dark.scss file apply only to the dark bundle.
- The template picks the bundle from `color_scheme`; core returns `"light"` always (`addons/web/models/ir_http.py`). Community has no switch; to enable dark mode override `color_scheme()` in a model inheriting `ir.http`. The offline page reads a `color_scheme=dark` cookie (`addons/web/views/webclient_templates.xml`).
- Bootstrap dark variables are included via `addons/web/static/lib/bootstrap/scss/_variables-dark.scss` (`addons/web/__manifest__.py`).
- `$o-webclient-color-scheme` exists in `addons/web/static/src/scss/primary_variables.scss`.
- Our back office is light mode only: `take_ownership` has no *.dark.scss file, no `web.assets_web_dark` entry and no `color_scheme()` override. A dark brand surface (`#04232E`) would need all three, and adding dark rules to `web.assets_backend` would leak into light mode.

## Extension points for our addon

Our addon is take_ownership under addons/ (it exists on the `completed` branch, see `README.md`). It sets the brand colors, fonts and a Midnight navbar through `web._assets_primary_variables`; that bundle is shared with the web shop and reports, so values there also reach them. Do not edit `addons/web`.

| Goal | How | Reference |
|---|---|---|
| Change brand colors/fonts in the back office | Add `addons/take_ownership/static/src/scss/primary_variables.scss` under `'web._assets_primary_variables'` with `('before', 'web/static/src/scss/primary_variables.scss', ...)` so your `$o-brand-primary: ... !default`-style values are defined first | `addons/website/__manifest__.py`, `addons/html_editor/__manifest__.py` (the `after` form), `addons/web/__manifest__.py` |
| Same for the web shop | `web._assets_primary_variables` is shared, so it covers `web.assets_frontend` too. Website palettes (`o-color-*`) are separate and set in website scss/theme | `addons/website_sale/__manifest__.py` |
| Component-level SCSS | Add styles to `web.assets_backend` (and `web.assets_frontend` for the shop) | `addons/web/__manifest__.py` |
| Dark styles | *.dark.scss in `web.assets_web_dark` | `addons/web/__manifest__.py` |
| New field widget | Component + `registry.category("fields").add("name", def)`; use `widget="name"` in XML | `addons/web/static/src/views/fields/char/char_field.js` |
| New view type or custom list/kanban | `registry.category("views").add(...)`, use `js_class="name"` on the arch root to swap the controller/renderer | `addons/web/static/src/views/list/list_view.js` |
| Change an existing component | `patch(Class.prototype, {...})` | `addons/web/static/src/core/utils/patch.js` |
| Change an Owl template | XML with `t-inherit="web.Template"` and `t-inherit-mode="extension"` and xpath edits | `addons/mail/static/src/core/web/action_dialog_patch.xml` |
| Add systray or main component | `registry.category("systray")` / `"main_components"` | `addons/web/static/src/webclient/offline_systray/offline_systray.js` |
| Add a bundle entry without editing a manifest | `ir.asset` record with directives (append, prepend, before, after, replace, remove, include) | `odoo/addons/base/models/ir_asset.py` |
| Show a model field in a list/form/kanban | Not JS: inherit the XML view in the addon (the addon's views/ folder) and add the field; the standard widgets render it | `skills/odoo-guidelines/SKILL.md` |

Manifest example for our addon:

```python
'assets': {
    'web._assets_primary_variables': [
        ('before', 'web/static/src/scss/primary_variables.scss', 'take_ownership/static/src/scss/primary_variables.scss'),
    ],
    'web.assets_backend': ['take_ownership/static/src/**/*'],
    'web.assets_frontend': ['take_ownership/static/src/shop/**/*'],
},
```

## Gotchas for Odoo 20

- Owl is the new generation: components import `signal`, `useProps`, `useListener`, `t`, `Plugin`, `usePlugin` from @odoo/owl (`addons/web/static/src/views/fields/char/char_field.js`, `addons/web/static/src/core/orm_plugin.js`). A compatibility layer exists (`addons/web/static/src/owl2/owl3_compatibility_layer.js`). Older tutorials may not match; copy a neighbouring component.
- Services are now plugins. `env.debug` and `env.isSmall` were removed; use `DebugModePlugin` / `UIPlugin` (`addons/web/static/src/env.js`).
- `web_editor` is gone; HTML fields and the editor are in `addons/html_editor`, the website builder in `addons/html_builder`.
- *.variables.scss and *.dark.scss are picked up by glob, so file naming is behavior. A misnamed file silently lands in the wrong bundle (`addons/web/__manifest__.py`).
- `web.assets_backend` is not the whole backend CSS: the page loads `web.assets_web` (and `_dark`). Add JS to `web.assets_backend`; it is included by `web.assets_web`.
- Graph and pivot are lazy bundles (`web.assets_backend_lazy`); do not reference their files from `web.assets_backend`.
- The `/odoo` URL serves the client; the asset bundle URL is /web/assets/{unique}/{filename} (`odoo/addons/base/models/ir_asset.py`). Bundles are cached; after changing SCSS or manifests, upgrade the module (`-u take_ownership`) and hard-reload, or use `?debug=assets`.
- Backend and frontend share primary variables but not Bootstrap overrides: `addons/web/static/src/scss/bootstrap_overridden.scss` is backend only, `addons/web/static/src/scss/bootstrap_overridden_frontend.scss` is frontend only.
- Tests: JS unit tests use Hoot (`addons/web/static/lib/hoot/`, helpers in `addons/web/static/tests/_framework/`); tours are in `addons/web/static/tests/tours/`.
