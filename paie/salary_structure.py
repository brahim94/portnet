# -*- coding: utf-8 -*-
from openerp import fields, models, api


class SalaryStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    categorie_ids = fields.One2many('hr.employee.categorie','structure_id','Catégories')

