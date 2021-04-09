# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import datetime

class customer_request(models.Model):
    _name = 'customer.request'
    _order='create_date desc'

    code = fields.Char(string="Code client", required=True,)
    name = fields.Char(string="Nom client", required=False,)
    rc = fields.Char(string="RC client", required=False,)
    centre_rc = fields.Char(string="Centre RC", required=False,)
    ifu = fields.Char(string="Identifant fiscal", required=False,)
    code_categ = fields.Char(string="Code catégorie", required=False, )
    state = fields.Selection(string="Etat", selection=[('draft', 'Brouillon'), ('confirmed', 'Confirmée'),('canceled','Annulée') ], required=False, default='draft' )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Fiche client", required=False, )
    confirmation_date = fields.Datetime(string="Date de confirmation", required=False, )
    subscribed = fields.Boolean(string="F.A générée", related="partner_id.subscribed")

    @api.one
    def action_cancel(self):
        self.state = 'canceled'

    @api.one
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        if self.ifu and self.ifu != '' and self.ifu != ' ':
            suppliers = self.env['res.partner'].search([('ifu','=',self.ifu),('supplier','=',True)])
            categories = self.env['res.partner.category'].search([('code','=',self.code_categ),('type','=','customer')])
            if categories:
                categ_id = categories[0].id
            else:
                categ_id = False
            vals = {
                    'categ_id':categ_id,
                    'customer':True,
                    'property_product_pricelist':False,
                    'request_creation_date':self.create_date,
                    }
            if suppliers:
                if self.code and self.code != "" and self.code != suppliers[0].code:
                    vals['code']=self.code
                suppliers[0].sudo().write(vals)
                self._cr.execute("UPDATE res_partner SET write_uid = "+str(self._uid)+" WHERE id = "+str(suppliers[0].id))
                self.partner_id = suppliers[0]
                self.state='confirmed'
                self.confirmation_date = datetime.datetime.now()
            else:
                customers = self.env['res.partner'].search([('ifu','=',self.ifu),('customer','=',True),('code','=',self.code),('categ_id','=',categ_id)])
                if not customers or not customers[0].categ_id:
                    vals['ifu']=self.ifu
                    vals['is_company']=True
                    vals['name'] = self.name
                    vals['code'] = self.code
                    vals['rc'] = self.rc
                    vals['centre_rc'] = self.centre_rc
                    if not self.name: vals['name'] = vals['code']
                    vals['customer_request_id'] = self.id
                    self.partner_id = self.env['res.partner'].sudo().create(vals)
                    self._cr.execute("UPDATE res_partner SET create_uid = "+str(self._uid)+" WHERE id = "+str(self.partner_id.id))
                    self.state='confirmed'
                    self.confirmation_date = datetime.datetime.now()
                else:
                    raise exceptions.ValidationError("Ce client existe dèja dans le système : ( "+str(self.ifu)+", "+str(self.code)+", "+str(self.code_categ)+" )")
        else:
            wizard_id = self.pool.get("customer.request.wizard").create(self._cr, self._uid, {'customer_request_id':self.id}, context=self._context)
            return {
                'name':_("Création client"),
                'view_mode': 'form',
                'view_id': False,
                'view_type': 'form',
                'res_model': 'customer.request.wizard',
                'res_id':wizard_id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
                }

    @api.multi
    def link_to_customer(self):
         return {
            'name':_("Clients"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'res.partner',
            'res_id':self.partner_id.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            #'target': 'new',
            'domain': '[]',
            }




customer_request()