# Part of Odoo. See LICENSE file for full copyright and licensing details.
import unittest

from psycopg2.errors import CheckViolation, NotNullViolation

from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools import mute_logger


class TestProductGrade(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.categ_laptops = cls.env.ref('take_ownership.product_category_laptops')
        cls.categ_phones = cls.env.ref('take_ownership.product_category_phones')
        cls.categ_tablets = cls.env.ref('take_ownership.product_category_tablets')
        cls.categ_accessories = cls.env.ref('take_ownership.product_category_accessories')
        cls.Template = cls.env['product.template']

    def test_default_grade_is_b(self):
        product = self.Template.create({'name': 'Plain product'})
        self.assertEqual(product.condition_grade, 'b')

    def test_grade_is_required(self):
        with self.assertRaises(NotNullViolation), mute_logger('odoo.sql_db'), self.cr.savepoint():
            self.Template.create({'name': 'No grade', 'condition_grade': False})

    def test_has_battery_by_category(self):
        child = self.env['product.category'].create({
            'name': 'Gaming laptops',
            'parent_id': self.categ_laptops.id,
        })
        for categ in (self.categ_laptops, self.categ_phones, self.categ_tablets, child):
            product = self.Template.create({'name': categ.name, 'categ_id': categ.id})
            self.assertTrue(product.has_battery, categ.name)

    def test_has_no_battery_without_rule(self):
        accessory = self.Template.create({'name': 'Charger', 'categ_id': self.categ_accessories.id})
        self.assertFalse(accessory.has_battery)
        other = self.Template.create({'name': 'Other', 'categ_id': self.env.ref('product.product_category_goods').id})
        self.assertFalse(other.has_battery)
        no_category = self.Template.create({'name': 'Nothing'})
        no_category.categ_id = False
        self.assertFalse(no_category.has_battery)

    def test_has_battery_follows_category_change(self):
        product = self.Template.create({'name': 'Moves', 'categ_id': self.categ_accessories.id})
        self.assertFalse(product.has_battery)
        product.categ_id = self.categ_phones
        self.assertTrue(product.has_battery)

    def test_battery_health_range(self):
        for value in (0, 100):
            product = self.Template.create({
                'name': 'Battery %s' % value,
                'categ_id': self.categ_phones.id,
                'battery_health': value,
            })
            self.assertEqual(product.battery_health, value)
        product = self.Template.create({'name': 'Phone', 'categ_id': self.categ_phones.id})
        for value in (-1, 101):
            with self.assertRaises(CheckViolation), mute_logger('odoo.sql_db'), self.cr.savepoint():
                self.Template.create({'name': 'Bad', 'battery_health': value})
            with self.assertRaises(CheckViolation), mute_logger('odoo.sql_db'), self.cr.savepoint():
                product.battery_health = value
                product.flush_recordset()
            product.invalidate_recordset()

    def test_filter_and_group_by_grade(self):
        names = {'a': 'Grade A', 'b': 'Grade B', 'c': 'Grade C', 'parts': 'Grade Parts'}
        for grade, name in names.items():
            self.Template.create({'name': name, 'condition_grade': grade})
        domain = [('name', 'in', list(names.values()))]
        for grade, name in names.items():
            found = self.Template.search(domain + [('condition_grade', '=', grade)])
            self.assertEqual(found.mapped('name'), [name])
        groups = self.Template._read_group(domain, ['condition_grade'], ['__count'])
        self.assertEqual(dict(groups), {grade: 1 for grade in names})

    def test_search_view_has_grade_filters(self):
        view = self.env.ref('product.product_template_search_view')
        arch = self.env['product.template'].get_view(view.id, 'search')['arch']
        self.assertIn('condition_grade', arch)
        self.assertIn("group_by", arch)


@tagged('post_install', '-at_install')
class TestProductGradeDemo(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.ref('take_ownership.product_macbook_air_m1', raise_if_not_found=False):
            raise unittest.SkipTest("Demo data not loaded")
        ours = cls.env['ir.model.data'].search([
            ('module', '=', 'take_ownership'), ('model', '=', 'product.template'),
        ])
        cls.devices = cls.env['product.template'].browse(ours.mapped('res_id'))

    def test_ten_sample_devices(self):
        self.assertEqual(len(self.devices), 10)
        self.assertEqual({d.condition_grade for d in self.devices}, {'a', 'b', 'c', 'parts'})
        for device in self.devices:
            self.assertTrue(device.image_1920, device.name)
            self.assertTrue(device.is_published, device.name)
            self.assertTrue(device.public_categ_ids, device.name)
            self.assertEqual(bool(device.battery_health), device.has_battery, device.name)

    def test_no_odoo_demo_template_active(self):
        # Data products stay: delivery, down payment and donation.
        others = self.env['product.template'].search([('id', 'not in', self.devices.ids)])
        xmlids = sorted(others.get_external_id().values())
        self.assertEqual(xmlids, [
            'delivery.product_product_delivery_product_template',
            'sale.advance_product_0_product_template',
            'website_sale.product_donation',
        ])


@tagged('post_install', '-at_install')
class TestProductGradeShop(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.phone = cls.env['product.template'].create({
            'name': 'Test shop phone',
            'categ_id': cls.env.ref('take_ownership.product_category_phones').id,
            'condition_grade': 'a',
            'battery_health': 87,
            'is_published': True,
            'list_price': 100,
        })
        cls.charger = cls.env['product.template'].create({
            'name': 'Test shop charger',
            'categ_id': cls.env.ref('take_ownership.product_category_accessories').id,
            'condition_grade': 'c',
            'is_published': True,
            'list_price': 10,
        })

    def test_device_page_shows_grade_and_battery(self):
        response = self.url_open(self.phone.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_take_ownership_grade_a', response.text)
        self.assertIn('A (like new)', response.text)
        self.assertIn('Battery health', response.text)
        self.assertIn('87%', response.text)

    def test_accessory_page_shows_grade_without_battery(self):
        response = self.url_open(self.charger.website_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('o_take_ownership_grade_c', response.text)
        self.assertIn('C (visible wear)', response.text)
        self.assertNotIn('Battery health', response.text)
