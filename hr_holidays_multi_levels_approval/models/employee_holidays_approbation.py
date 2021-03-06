#-*- coding:utf-8 -*-

from openerp import models, fields

class EmployeeHolidaysApprobation(models.Model):
    _name = "hr.employee.holidays.approbation"
    _order= "sequence"
    
    holidays = fields.Many2one('hr.holidays', string='Holidays', required=True)
    approver = fields.Many2one('res.users', string='Approbateur', required=True)
    sequence = fields.Integer(string='Approbation sequence', default=10, required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now())
    