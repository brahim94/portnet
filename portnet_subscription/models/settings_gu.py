# -*- encoding: utf-8 -*-
from openerp import models, fields,  api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning

class setting_guichet_unique(models.Model):
    _name = 'setting.guichet.unique'

    url = fields.Char(string="URL Web Service", required=True)
    login = fields.Char(string='Login', required=True)
    passwd = fields.Char(string='Password', required=True)
    hmac = fields.Char(string='HMAC', required=True)

    @api.constrains('url')
    def _check_exchange_folder(self):
        res = self.search([])
        if len(res) > 1:
           raise Warning("On doit pas avoir plus qu'une configuration pour la synchronisation GU")