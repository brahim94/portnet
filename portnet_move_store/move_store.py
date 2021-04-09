# -*- coding: utf-8 -*-
from openerp import models,api, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime


class move_store(models.Model):
      _name="move.store"

      piece_id=fields.Many2one('account.move',string="Pièce Comptable")
      ref_piece=fields.Char(string='Réference')
      move_line_id=fields.Many2one('account.move.line',string="Ligne de la pièce")
      update_date=fields.Datetime(string="Date de modification")
      journal_id=fields.Many2one('account.journal',string="Journal")
      period_id=fields.Many2one('account.period',string="Période")
      account_id=fields.Many2one('account.account',string="Compte")
      debit=fields.Float(string="Débit",digits=(16,2))
      credit=fields.Float(string='Crédit',digits=(16,2))
      currency=fields.Float(string='Devise')

