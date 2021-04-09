# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _

class project_break(models.Model):
    _name = 'project.break'

    name = fields.Char(string="Motif", required=True)
    date_start = fields.Date(string="Date de début", required=True)
    date_end = fields.Date(string="Date de fin", required=True)
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Bon de réception", required=False)

    @api.onchange('date_start','date_end')
    def _check_dates(self):
        if self.date_end and self.date_start and (self.date_end < self.date_start):
            self.date_end = False
            return { 'warning':{'title':_('Intervalle de dates incorrecte !'),'message':_('La date de fin de ne peut être inférieure à la date de début')}}


project_break()