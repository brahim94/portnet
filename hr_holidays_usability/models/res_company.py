# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _


class res_company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    hours_per_day = fields.Integer(string="Nombre d'heures de travail par journée", required=True, default = 8 )


res_company()