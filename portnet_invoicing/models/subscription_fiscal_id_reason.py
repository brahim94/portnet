# -*- encoding: utf-8 -*-

from openerp import models, fields

class subscription_fiscal_id_reason(models.Model):
    _name = 'subscription.fiscal.id.reason'

    name = fields.Char(string="Motif",required=True)

subscription_fiscal_id_reason()