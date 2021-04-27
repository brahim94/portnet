# -*- coding: utf-8 -*-
from openerp import fields, models, api


class SalaryStructure(models.Model):
    _inherit = 'hr.salary.rule.category'