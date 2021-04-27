# -*- coding: utf-8 -*-
from openerp import fields, models


class Enfant(models.Model):
    _name='enfant'

    nom = fields.Char('nom',translate=True,required=True)
    prenom = fields.Char('Prenom',required=True)
    date_naissance = fields.Date('Date de Naissance',required=True,translate=True)
    acte_naissance = fields.Binary("Acte de naissance")
    employee_id = fields.Many2one('hr.employee')
    wizard_id = fields.Many2one('hr.employee.wizard')
    handicape=fields.Boolean('Handicapé')
