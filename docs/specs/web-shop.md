# Web shop

The web shop is `addons/website_sale` (products, cart, checkout) running on `addons/website` (pages, menus, snippets, assets, the website builder). The shop pages are QWeb templates rendered by controllers in `addons/website_sale/controllers/`. The front end behaviour is Owl-based "interactions" in `addons/website_sale/static/src/interactions/`. Our changes go in our own addon (see AGENTS.md), never in these modules.

## Key files

| Path | What it holds |
|---|---|
| `addons/website_sale/controllers/main.py` | `WebsiteSale` controller: /shop grid (`shop`), product page (`product`), `_prepare_product_values`, checkout steps (`shop_checkout`, `shop_address`, `extra_info`, `shop_payment`, `shop_payment_validate`, `shop_payment_confirmation`) |
| `addons/website_sale/controllers/cart.py` | /shop/cart, `add_to_cart`, `quick_add`, `update_cart` (all `jsonrpc` except the cart page) |
| `addons/website_sale/controllers/` (others) | `addons/website_sale/controllers/wishlist.py`, `addons/website_sale/controllers/comparison.py`, `addons/website_sale/controllers/delivery.py`, `addons/website_sale/controllers/payment.py`, `addons/website_sale/controllers/product_feed.py`, `addons/website_sale/controllers/variant.py`, `addons/website_sale/controllers/reorder.py` |
| `addons/website_sale/models/product_template.py` | Shop fields and logic on `product.template`: `_get_combination_info`, `_get_additional_combination_info`, `_search_get_detail`, `_search_fetch`, `website_url` |
| `addons/website_sale/models/sale_order.py` | The cart is a draft `sale.order`: `_cart_add`, `_cart_update_line_quantity`, abandoned-cart fields |
| `addons/website_sale/models/website.py` | Per-website cart, pricelist and fiscal position helpers |
| `addons/website_sale/models/product_public_category.py` | Shop categories (`product.public.category`) |
| `addons/website_sale/models/website_checkout_step.py` | Ordered checkout steps (`website.checkout.step`) |
| `addons/website_sale/templates/shop_page_templates.xml` | `website_sale.products` (the grid page), filters, sort, categories sidebar |
| `addons/website_sale/templates/product_tile_templates.xml` | Product card: `products_item`, `product_image_and_ribbon`, `product_title_and_details`, `shop_product_buttons` |
| `addons/website_sale/templates/product_page_templates.xml` | Product page: `website_sale.product`, `product_title`, `product_price`, `cta_wrapper`, carousel and specs |
| `addons/website_sale/templates/checkout/` | `addons/website_sale/templates/checkout/cart_templates.xml`, `addons/website_sale/templates/checkout/address_templates.xml`, `addons/website_sale/templates/checkout/payment_templates.xml`, `addons/website_sale/templates/checkout/confirmation_templates.xml`, `addons/website_sale/templates/checkout/extra_info_templates.xml` |
| `addons/website_sale/templates/snippets/snippets.xml` | Registers eCommerce snippets into the website snippet panel |
| `addons/website_sale/static/src/interactions/` | Front end behaviour: `addons/website_sale/static/src/interactions/shop_page.js`, `addons/website_sale/static/src/interactions/product_page.js`, `addons/website_sale/static/src/interactions/add_to_cart.js`, `addons/website_sale/static/src/interactions/checkout.js`, ... |
| `addons/website_sale/static/src/website_builder/` | Website builder option plugins for shop pages and product tiles |
| `addons/website_sale/security/ir.access.csv` | Public read access to published products, categories, ribbons |
| `addons/website/models/website_page.py` | `website.page`: a page that owns an `ir.ui.view` (`view_id`), URL, menus |
| `addons/website/models/ir_ui_view.py` | Website-aware views: per-website copy-on-write (COW) of views |
| `addons/website/models/ir_asset.py` | `ir.asset` with website COW, used to add or remove assets per website |
| `addons/website/models/mixins.py` | `website.published.mixin` (`is_published`, `website_published`), `website.multi.mixin` (`website_id`) |
| `addons/website/views/snippets/snippets.xml` | The snippet panel template and snippet groups; one file per snippet in the same folder |
| `addons/website/controllers/main.py` | Website routes, /pages, /website/add, system pages |

## How the pieces connect

1. A request to /shop hits `WebsiteSale.shop` in `addons/website_sale/controllers/main.py`. It builds the domain (`_get_shop_domain`), searches `product.template`, and renders `website_sale.products`.
2. `website_sale.products` loops over products and `t-call`s `website_sale.products_item` (the `t-call` is in `addons/website_sale/templates/shop_page_templates.xml`; the template is defined in `addons/website_sale/templates/product_tile_templates.xml`). The tile calls `product_image_and_ribbon`, `product_title_and_details` and `shop_product_buttons` (`addons/website_sale/templates/product_tile_templates.xml`).
3. A product URL (`/shop/<product.template>`) hits `WebsiteSale.product`, which uses `_prepare_product_values` and renders `website_sale.product`. Price and variant data come from `product.template._get_combination_info`.
4. Add to cart posts to /shop/cart/add (handled by `add_to_cart`) in `addons/website_sale/controllers/cart.py`, which calls `sale.order._cart_add`. /shop/cart renders the cart page.
5. Checkout runs through /shop/checkout, /shop/address, /shop/extra_info, /shop/payment, then /shop/payment/validate and confirmation. Steps are `website.checkout.step` records in `addons/website_sale/data/website_checkout_step_data.xml`.
6. Website pages other than the shop are `website.page` records. `ir.http._serve_page` finds the page by URL and renders its view (`addons/website/models/ir_http.py`).
7. The browser attaches behaviour to the rendered HTML by CSS selector. `ProductPage` binds to `.o_wsale_product_page` and is registered in the `public.interactions` registry (`addons/website_sale/static/src/interactions/product_page.js`).

## Adding a field to the product card and product page

Our addon already does this for the condition grade and battery health: `addons/take_ownership/views/product_templates.xml` inherits `website_sale.product_title` (see [take-ownership.md](take-ownership.md)). The shop grid and tiles are unchanged. The examples below are the general pattern.

Add the model field first. Then inherit the templates from our addon's views/ or templates/ XML (listed in our manifest `data`).

```python
class ProductTemplate(models.Model):
    _inherit = "product.template"
    x_grade = fields.Selection([("a", "A"), ("b", "B")])
```

Product card. `product_title_and_details` is a good anchor: it already has the name, description and rating, and renders `product_extra_information` if set (`addons/website_sale/templates/product_tile_templates.xml`):

```xml
<template id="products_item_grade" inherit_id="website_sale.product_title_and_details">
    <xpath expr="//div[hasclass('o_wsale_product_information_text')]" position="inside">
        <span t-if="product.x_grade" t-field="product.x_grade"/>
    </xpath>
</template>
```

Product page. Anchors with stable ids in `addons/website_sale/templates/product_page_templates.xml`: `product_details`, `o_wsale_cta_wrapper`, `add_to_cart_wrap`, `product_full_description`. The template `website_sale.product_title` is a good place for a short badge. The specs section (`product_attributes_body`) shows how to inject after `//div[@id='product_full_description']`.

Rules for these inherited views:
- Always give the full id (`website_sale.products_item`) in `inherit_id`, and use `hasclass()` for class matching in XPath.
- In templates, `product` on a tile is a `product.template`; the variant is `product_variant` (`addons/website_sale/templates/product_tile_templates.xml`).
- Fields rendered by a public visitor need to be readable by public. The product rule is `product_template_public` in `addons/website_sale/security/ir.access.csv`. A new field on `product.template` is readable if the user can read the record; fields with `groups=` are not.
- Use `t-field` for display (it respects the editor and formatting); use `t-out` for computed text. `t-esc` is not used in the shop templates.

## Extension points for our addon

| Goal | Hook |
|---|---|
| Add a field | `_inherit = "product.template"` (or `product.product`). Fields on the template are available as `product.x_...` in card and page. |
| Change what the grid shows or how it is filtered | Override `WebsiteSale._get_shop_domain`, `_get_search_options`, `_shop_lookup_products`, `_get_additional_shop_values` in a controller subclass of `odoo.addons.website_sale.controllers.main.WebsiteSale`; re-declare the route with a bare `@route()` (`addons/website_sale/controllers/main.py`) |
| Pass extra values to the product page | Override `_prepare_product_values` and call `super()` |
| Extra data in price/variant JSON | Override `_get_additional_combination_info` on `product.template` (`addons/website_sale/models/product_template.py`) |
| Change cart behaviour | Override `sale.order._cart_add` / `_cart_update_line_quantity` (`addons/website_sale/models/sale_order.py`) |
| Add a checkout step | Create a `website.checkout.step` record with `step_href`; see `addons/website_sale/data/website_checkout_step_data.xml` |
| Add a page | A `website.page` record with `url`, `view_id` and `is_published`; the view arch is a QWeb template (`addons/website/models/website_page.py`) |
| Add a snippet | A template for the snippet, then inherit `website.snippets` to list it with `t-snippet`; see `addons/website_sale/templates/snippets/snippets.xml` |
| Add JS behaviour | An `Interaction` class in static/src/interactions/, registered in `public.interactions`, listed in `web.assets_frontend` |
| Add SCSS | Put it in `web.assets_frontend`; set theme variables in `web._assets_primary_variables` (`addons/website_sale/__manifest__.py`) |
| Builder options (editor side panel) | `website.website_builder_assets` bundle (`addons/website_sale/__manifest__.py`) |

Our manifest should depend on `website_sale`, and declare assets like this (the bundle names are the real ones used in `addons/website_sale/__manifest__.py`):

```python
"assets": {
    "web.assets_frontend": ["take_ownership/static/src/shop/**/*"],
    "web._assets_primary_variables": ["take_ownership/static/src/scss/primary_variables.scss"],
},
```

## Gotchas for Odoo 20

- Access control is `ir.access` (a CSV named ir.access.csv with a `domain` column and an `operation` column such as `r` or `crud`), replacing the older `ir.model.access` plus `ir.rule` pair (`addons/website_sale/security/ir.access.csv`, `addons/website_sale/security/ir_access.xml`). Records are `ir.access` in XML.
- JSON routes use `type="jsonrpc"`, not `type="json"` (`addons/website_sale/controllers/cart.py`).
- The front end uses `Interaction` classes with `static selector` and the `public.interactions` registry, not `publicWidget` (`addons/website_sale/static/src/interactions/product_page.js`). JS imports use @web/... and @website_sale/... aliases.
- The editor is the new website builder: plugins and *_option.xml files under `addons/website_sale/static/src/website_builder/`. Files named `*.edit.*` load only inside the builder iframe (`addons/website_sale/__manifest__.py`).
- Assets are declared in the manifest `assets` key with globs and `("remove", ...)`, `("include", ...)` operations (`addons/website/__manifest__.py`). Do not add `<template inherit_id="web.assets_frontend">` entries.
- Website views are copy-on-write: editing an inherited view for a specific website creates a website-specific copy (`addons/website/models/ir_ui_view.py`). When you change a template in XML and `-u` your addon, a website-specific copy made earlier in the editor keeps the old arch. Check `website_id` on `ir.ui.view` if a change does not show up.
- Optional blocks are templates with `active="False"` toggled by the editor; test them with `is_view_active('website_sale.product_comment')` as the shop templates do (`addons/website_sale/templates/product_tile_templates.xml`).
- Pricing and variants on the page come from `_get_combination_info`, loaded by JS on variant change, so a field that depends on the selected variant must be added there (or to `_get_additional_combination_info`) and rendered by JS, not only by QWeb (`addons/website_sale/models/product_template.py`).
- The cart is `request.cart` (a lazy sale order set in `addons/website_sale/models/ir_http.py`); use it to get the current cart in controllers.
- Product visibility for visitors needs `website_published` and `sale_ok` (`addons/website_sale/security/ir.access.csv`, `addons/website/models/mixins.py`). Demo products that do not appear are usually unpublished or on another website (`website_id`). With our addon's demo data, Odoo's own demo products are archived (`addons/take_ownership/demo/archive_odoo_demo_products.xml`), so only the ten Take Ownership devices appear in /shop.
- Tests: Python tests in `addons/website_sale/tests/` (for example `addons/website_sale/tests/test_customize.py`, `addons/website_sale/tests/test_checkout_flow.py`); browser tours in `addons/website_sale/static/tests/tours/`, bundled in `web.assets_tests`.
