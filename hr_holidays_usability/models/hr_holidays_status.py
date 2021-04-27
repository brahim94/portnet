# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class hr_holidays_status(models.Model):
    _name = 'hr.holidays.status'
    _inherit = 'hr.holidays.status'

    account_id = fields.Many2one(comodel_name="account.analytic.account", string="Compte analytique")

hr_holidays_status()
