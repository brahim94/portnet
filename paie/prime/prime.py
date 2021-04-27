# -*- coding: utf-8 -*-
from openerp import fields, models


class Prime(models.Model):
    _name='prime'

    nom=fields.Many2one('hr.list.prime','type de prime',required=True)
    #nom = fields.Char('type de prime',translate=True,required=True)
    montant = fields.Char('Montant',required=True)
    contrat_id = fields.Many2one('hr.contract')
    wizard_id = fields.Many2one('hr.contract.wizard')


class List_prime(models.Model):
    _name = 'hr.list.prime'

    name = fields.Char('Name')

