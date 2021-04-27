# -*- coding: utf-8 -*-

from openerp import models, fields, api

# class hr_holidays_usability_extra(models.Model):
#     _name = 'hr_holidays_usability_extra.hr_holidays_usability_extra'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100