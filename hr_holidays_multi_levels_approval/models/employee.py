#-*- coding:utf-8 -*-

from openerp import models, fields, api

class Employee(models.Model):
    _inherit ='hr.employee'

    holidays_approvers = fields.One2many('hr.employee.holidays.approver', 'employee', string='Approbateurs')
    transfer_holidays_approvals_to = fields.Many2one('hr.employee', string='''Transférer les droits d'approbation à''')
    transfer_holidays_approvals_to_user = fields.Many2one('res.users', string='Transfer approval rights to user', related='transfer_holidays_approvals_to.user_id', related_sudo=True, store=True, readonly=True)
    
    @api.multi
    @api.one
    def set_default_validation_chain(self):
        for approver in self.holidays_approvers:
            approver.unlink()
        
        approver = self.parent_id
        sequence = 1
        while True:
            if approver:
                self.env['hr.employee.holidays.approver'].create({'employee': self.id, 'approver': approver.id, 'sequence': sequence})
                if approver!=approver.parent_id:
                    sequence = sequence + 1
                    approver = approver.parent_id
                else:
                    approver=False
            else:
                break


