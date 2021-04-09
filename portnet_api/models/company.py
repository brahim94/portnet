# -*- coding: utf-8 -*-

from openerp import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    ip_address = fields.Char(string='IP address')
    user_id = fields.Char(string='User')
    password = fields.Char(string='Password')
    