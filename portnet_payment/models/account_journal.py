# -*- coding: utf-8 -*-
##############################################################################

from openerp import models, fields,api,_
from openerp.exceptions import except_orm, Warning, RedirectWarning

class account_journal(models.Model):
    _inherit = "account.journal"

    bank_id=fields.Many2one(comodel_name='res.bank',string="Banque")

    @api.constrains('bank_id')
    def _check_bic(self):
      res=self.search( [('bank_id','=',self.bank_id.id),('type','=','bank')] )
      if len(res) > 1:
        raise Warning("Un journal de type banque doit être unique par banque")

account_journal()
