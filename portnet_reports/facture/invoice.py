# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
from dateutil import parser, rrule
from datetime import datetime
from openerp.osv import orm


class account_invoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    period_name=fields.Char(string="Abréviation nom période",store=False,compute="_get_period_name" )
    is_product_abonn=fields.Boolean(string="Contient un produit abonnement",store=True,default=False,compute="_get_product_abonnement")
    start_date=fields.Date(string="Date début abonnement",store=True,compute="_get_product_abonnement")
    end_date=fields.Date(string="Date fin abonnement",store=True,compute="_get_product_abonnement")

    @api.one
    @api.depends('number','proforma_ref','invoice_line','invoice_line.start_date','invoice_line.end_date')
    def _get_product_abonnement(self):
        bool=False
        for l in self.invoice_line:
            if l.is_subscription==True:
               bool=True
               self.start_date=l.start_date
               self.end_date=l.end_date
            if l.invoice_id.proforma_ref:
                bool = True
                self.start_date = l.start_date
                self.end_date = l.end_date
        self.is_product_abonn=bool

    @api.one
    @api.depends('period_id')
    def _get_period_name(self):
        per=''
        if self.period_id:
            mouth=self.period_id.name[0:2]
            year=self.period_id.name[3:]
            if mouth=='01':
                per='JANVIER'
            elif mouth=='02':
                per='FEVRIER'
            elif mouth=='03':
                per='MARS'
            elif mouth=='04':
                per='AVRIL'
            elif mouth=='05':
                per='MAI'
            elif mouth=='06':
                per='JUIN'
            elif mouth=='07':
                per='JUILLET'
            elif mouth=='08':
                per='AOUT'
            elif mouth=='09':
                per='SEPTEMBRE'
            elif mouth=='10':
                per='OCTOBRE'
            elif mouth=='11':
                per='NOVEMBRE'
            elif mouth=='12':
                per='DECEMBRE'
            else :
                per='"Periode d\'ouverture'
            self.period_name=per+' '+year

account_invoice()
