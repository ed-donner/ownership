# Plan: Take Ownership

Based on `intent.md` and `docs/spec.md`. The detailed design is in `docs/specs/take-ownership.md`. No code is written yet.

## Files that change

Everything new is in `addons/take_ownership/`. No file in `odoo/` or in an Odoo-owned module under `addons/` is edited.

| File | Purpose |
|---|---|
| `__init__.py`, `__manifest__.py` | Module entry. `depends`: `product`, `website_sale`. Lists data, demo and the `assets` bundles. |
| `models/__init__.py`, `models/product_template.py` | `condition_grade`, `battery_health`, `has_battery` on `product.template`, plus the range constraint. |
| `data/product_category_data.xml` | Laptops, Phones, Tablets, Accessories under `product.product_category_goods`. |
| `views/product_template_views.xml` | Grade badge and battery bar on the form, list and kanban. Grade filters and group-by on the search view. |
| `views/product_templates.xml` | Grade and battery health on the shop product page, inheriting `website_sale.product_title`. |
| `demo/product_demo.xml` | The ten devices with photos, grades, battery figures, prices, shop categories, published. |
| `demo/archive_odoo_demo_products.xml` | Archives Odoo's demo products by xml id. |
| `static/img/*.jpg`, `static/img/CREDITS.md` | Photos copied from `docs/photos/`, with the credits file beside them. |
| `static/fonts/*` | Instrument Sans, Instrument Serif and JetBrains Mono files. |
| `static/src/scss/primary_variables.scss` | Brand colors, fonts, Midnight navbar, in `web._assets_primary_variables`. |
| `static/src/scss/*.scss` | Back office component styles (badge, form, navbar) and shop page styles. |
| `tests/__init__.py`, `tests/test_product_grade.py` | Python tests. |

Docs that change: `docs/specs/modules.md` is regenerated with `uv run docs/gen_modules.py` once the addon exists. The other spec files were already updated for this change. `docs/photos/` stays as it is; the addon holds copies.

## Order of work

1. **Scaffold.** Create the addon folder, manifest and empty `models`. Add the four categories. Install on a throwaway database to prove the module loads.
2. **Model.** Write the failing tests for default grade, `has_battery` and the 0 to 100 range, then the three fields and the constraint until they pass.
3. **Back office views.** Form, list, kanban and search. Run with `--dev=xml` while editing, then `-u take_ownership`.
4. **Shop page.** The `product_title` inheritance and its styles. Check as a public visitor.
5. **Sample data.** Copy the photos and credits, write the ten devices, then the archive file. Check the product lists and `/shop` show only our devices.
6. **Brand.** Download and add the fonts, then the primary variables, the Midnight navbar and component styles. Compare `/shop` before and after (see Risks).
7. **Shop test and the full run.** Add the shop `HttpCase` test and run the whole suite on a fresh throwaway database with demo data. Drop it afterwards.
8. **Shop database.** Install on the shop database (`-i take_ownership`). Take the screenshots. Regenerate `docs/specs/modules.md`.
9. **Review.** Run the `odoo-review` skill on the addon and fix what it finds. Update the spec files if the code ended up different from them.

The server is started and stopped through background tasks, never with `kill`. Only one server runs per port, so it is stopped before every `-u` or test run.

## Risks

- **Brand leaks into the shop.** `web._assets_primary_variables` is shared with the shop and reports, and the shop theme is out of scope. Step 6 takes a `/shop` screenshot before and after. If the shop changes, move the colors to a backend-only bundle.
- **Fonts are not in the repo.** They have to be downloaded and checked for license. The brand skill says Google Fonts, but repo rules say ship them in the addon.
- **Demo archive list is fragile.** It names Odoo's demo records by xml id. A missed id leaves a demo product in the lists. The test counts active templates to catch this.
- **Two category systems.** Internal categories drive the battery field, and shop categories drive the sidebar. Odoo's demo shop categories can't be archived and may still show in the sidebar. Check the sidebar in step 5.
- **Shop view copies.** A website-specific copy of `website_sale.product_title` would hide our change. Check `website_id` on `ir.ui.view` if the shop page doesn't show the grade.
- **Battery 0 is ambiguous.** An unfilled battery figure looks like a 0% bar. Demo devices all get real figures, and the spec accepts this limit.
- **Required grade on existing data.** The new column fills with B for all existing products on the shop database. This is accepted in the intent, but staff should know.
- **Cached bundles.** SCSS and manifest changes need `-u take_ownership` and a hard reload, or `?debug=assets`, before judging the look.
- **Odoo 20 differences.** Use `<list>`, `invisible="expr"`, the `card` kanban template, `models.Constraint` and `ir.access` terms, per `AGENTS.md` section 8. The Owl 3 parts are avoided: no custom JS is planned.

## Proof

### Tests

Run on a throwaway database, then drop it:

```
uv run python odoo-bin -c odoo.conf -d test_db -i website_sale,take_ownership --with-demo --test-tags /take_ownership --stop-after-init
dropdb test_db
```

`tests/test_product_grade.py`:

| Test | Shows |
|---|---|
| New product has grade B | The default works. |
| Grade is required | Creating with no grade fails. |
| `has_battery` for Laptops, Phones, Tablets and a child category | The category rule works. |
| `has_battery` false for Accessories and for no category | The rule has no false positives. |
| `battery_health` of -1 and 101 fail, 0 and 100 pass | The constraint works on create and write. |
| Filter and group-by on `condition_grade` | Staff can filter and group. |
| Ten sample devices exist with grades and photos | The sample data loads. Needs demo data. |
| No Odoo demo template is active | The archive covers all demo products. Needs demo data. |
| Public `HttpCase` on a device's shop page | Grade and battery text are on the page. |
| Public `HttpCase` on an accessory's shop page | Grade shows and no battery text. |

### Screenshots

Taken on the shop database with the server running, in a browser (Playwright), logged in as `admin` unless noted. Saved in `docs/changes/take-ownership/screenshots/`.

| # | Screenshot | Criterion |
|---|---|---|
| 1 | Product form of a laptop: grade badge and battery bar | 2 |
| 2 | Product form of an accessory: grade badge, no battery bar | 2 |
| 3 | Product list: badges, battery bars and Midnight navbar | 2, 3 |
| 4 | Product kanban: ten cards with photos and badges | 2 |
| 5 | List grouped by Condition, and with the Grade A filter on | 2 |
| 6 | `/shop` product page of a phone, as a visitor: grade and battery | 2 |
| 7 | `/shop` product page of an accessory: grade, no battery | 2 |
| 8 | `/shop` grid: only the ten devices, with their photos | 2 |
| 9 | `/shop` before and after the addon, side by side | Risk: shop theme unchanged |
| 10 | A back office screen with buttons and a menu: brand colors, fonts, Midnight navbar | 3 |

Criterion 1 is proved by the install on the shop database (step 8) and the passing test run above. Criteria 2 and 3 are proved by the screenshots.
