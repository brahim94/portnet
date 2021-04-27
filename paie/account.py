# -*- coding: utf-8 -*-
from openerp import fields, models, api


class account_period(models.Model):
    _inherit = 'account.period'

    state_paie = fields.Boolean('Période fermée', default=False)

