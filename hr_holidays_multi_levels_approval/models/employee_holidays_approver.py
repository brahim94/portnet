#-*- coding:utf-8 -*-

from openerp import models, fields


class EmployeeHolidaysApprover(models.Model):
    _name = "hr.employee.holidays.approver"
    _order= "sequence"
    
    employee = fields.Many2one('hr.employee', string='Employee', required=True)
    approver = fields.Many2one('hr.employee', string='Approbateur', required=True)
    sequence = fields.Integer(string='''Séquence d'approbation''', default=10, required=True)