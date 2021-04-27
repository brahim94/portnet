# -*- coding: utf-8 -*-
from openerp import fields, models, api


class User(models.Model):
    _inherit = 'res.users'


    def _get_name(self):
        if 'nom' not in self._context and 'prenom' not in self._context:
            return ''
        else:
            if self._context['nom'] and self._context['prenom']:
                return self._context['nom']+' '+self._context['prenom']
            else:
                return ''

    name = fields.Char('Name', default=_get_name)

    def create(self, cr, uid, vals, context=None):
        name=''
        if 'nom' in context and 'prenom' in context:
            name= context['nom']+' '+context['prenom']
        if name!='':
            if vals['name']==context['nom']+' '+context['prenom']:
                x=super(User, self).create(cr, uid, vals, context=None)
                return x
            else:
                vals.update({'name':context['nom']+' '+context['prenom']})
                x=super(User, self).create(cr, uid, vals, context=None)
                return x
        else:
            x=super(User, self).create(cr, uid, vals, context=None)
            return x

class Partner(models.Model):
    _inherit = 'res.partner'

    property_account_payable = fields.Many2one('account.account',"Account Payable",domain="[]",help="This account will be used instead of the default one as the payable account for the current partner",
            required=True)
    property_account_receivable =fields.Many2one('account.account',domain="[]",
            help="This account will be used instead of the default one as the receivable account for the current partner",
            required=True)
