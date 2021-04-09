# -*- coding: utf-8 -*-

from openerp import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_package = fields.Boolean(string='Package')
    