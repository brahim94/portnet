# -*- encoding: utf-8 -*-

from openerp import models, fields

class res_periodicity(models.Model):
    _name = 'res.periodicity'
    _order = 'sequence asc'

    name = fields.Char(string="Nom",required=True)
    nb_months = fields.Integer(string="Nombre de mois",required=True)
    sequence = fields.Integer(string="Séquence", required=False, )

res_periodicity()