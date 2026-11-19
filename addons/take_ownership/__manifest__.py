# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Take Ownership',
    'version': '1.0',
    'category': 'Sales/Sales',
    'author': 'Take Ownership',
    'summary': 'Condition grade and battery health for refurbished devices',
    'depends': ['product', 'website_sale'],
    'data': [
        'data/product_category_data.xml',
        'views/product_template_views.xml',
        'views/product_templates.xml',
    ],
    'demo': [
        'demo/product_demo.xml',
        'demo/archive_odoo_demo_products.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss', 'take_ownership/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_backend': [
            'take_ownership/static/src/scss/fonts.scss',
            'take_ownership/static/src/scss/backend.scss',
        ],
        'web.assets_frontend': [
            'take_ownership/static/src/scss/frontend.scss',
        ],
    },
    'license': 'LGPL-3',
}
