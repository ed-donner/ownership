# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

BATTERY_CATEGORY_XMLIDS = (
    'take_ownership.product_category_laptops',
    'take_ownership.product_category_phones',
    'take_ownership.product_category_tablets',
)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    condition_grade = fields.Selection(
        selection=[
            ('a', "A (like new)"),
            ('b', "B (light wear)"),
            ('c', "C (visible wear)"),
            ('parts', "Parts (for repair)"),
        ],
        string="Condition",
        required=True,
        default='b',
        tracking=True,
    )
    battery_health = fields.Integer(
        string="Battery health",
        aggregator=None,
        help="Remaining battery capacity in percent, from 0 to 100.",
    )
    has_battery = fields.Boolean(compute='_compute_has_battery')

    _battery_health_range = models.Constraint(
        'CHECK(battery_health BETWEEN 0 AND 100)',
        "Battery health must be between 0 and 100.",
    )

    @api.depends('categ_id.parent_path')
    def _compute_has_battery(self):
        battery_categories = self.env['product.category']
        for xmlid in BATTERY_CATEGORY_XMLIDS:
            battery_categories |= self.env.ref(xmlid, raise_if_not_found=False) or self.env['product.category']
        paths = battery_categories.mapped('parent_path')
        for template in self:
            parent_path = template.categ_id.parent_path
            template.has_battery = bool(parent_path) and any(
                parent_path.startswith(path) for path in paths
            )
