# -*- encoding: utf-8 -*-
from openerp import fields, models, api


class HrEmployeeWizard(models.Model):
    _name = "hr.employee.wizard"

    enfant_ids = fields.One2many('enfant','wizard_id')

    @api.multi
    def confirm(self):
        employee = self.env['hr.employee'].browse(self._context['active_id'])
        if employee and self.enfant_ids:
            employee.write({'enfant_ids': [(6, False, self.enfant_ids.ids)]})
            employee.write({'nbre_enfants':len(employee.enfant_ids)})
            return {'ir.actions.act_window_close'}