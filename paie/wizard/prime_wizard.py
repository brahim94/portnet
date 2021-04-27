# -*- encoding: utf-8 -*-
from openerp import fields, models, api


class HrConractWizard(models.Model):
    _name = "hr.contract.wizard"

    prime_ids = fields.One2many('prime','wizard_id')

    def get_primes(self):
        contrat = self.env['hr.contract'].browse(self._context['active_id'])
        return contrat.prime_ids.ids


    @api.multi
    def confirm(self):
        conrat = self.env['hr.contract'].browse(self._context['active_id'])
        if conrat and self.prime_ids:
            conrat.write({'prime_ids': [(6, False, self.prime_ids.ids)]})
            return {'ir.actions.act_window_close'}