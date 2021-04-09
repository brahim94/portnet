# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime

class customer_request_wizard(models.TransientModel):
    _name = 'customer.request.wizard'

    customer_request_id = fields.Many2one(comodel_name="customer.request", string="Demande de création client", required=False, )
    ifu = fields.Char(string="Identifiant fiscal", required=False)
    force = fields.Boolean(string="Forcer la création sans IFU ?",)
    reason_id = fields.Many2one(comodel_name="subscription.fiscal.id.reason", string="Motif")



    @api.multi
    def action_confirm(self):
        if not self.force and (self.ifu and self.ifu != '' and self.ifu != ' '):
            suppliers = self.env['res.partner'].search([('ifu','=',self.ifu),('supplier','=',True)])
            categories = self.env['res.partner.category'].search([('code','=',self.customer_request_id.code_categ),('type','=','customer')])
            if categories:
                categ_id = categories[0].id
            else:
                categ_id = False
            vals = {
                    'categ_id':categ_id,
                    'customer':True,
                    'property_product_pricelist':False,
                    'request_creation_date':self.customer_request_id.create_date,
                    }
            if suppliers:
                if self.customer_request_id.code and self.customer_request_id.code != "" and self.customer_request_id.code != suppliers[0].code:
                    vals['code']=self.customer_request_id.code
                suppliers[0].sudo().write(vals)
                self._cr.execute("UPDATE res_partner SET write_uid = "+str(self._uid)+" WHERE id = "+str(suppliers[0].id))
                self.customer_request_id.partner_id = suppliers[0]
                self.customer_request_id.state='confirmed'
                self.customer_request_id.confirmation_date = datetime.datetime.now()
                self.customer_request_id.ifu = self.ifu
            else:
                customers = self.env['res.partner'].search([('ifu','=',self.ifu),('customer','=',True),('code','=',self.customer_request_id.code),('categ_id','=',categ_id)])
                if not customers or not customers[0].categ_id:
                    vals['ifu']=self.ifu
                    vals['is_company']=True
                    vals['name'] = self.customer_request_id.name
                    vals['code'] = self.customer_request_id.code
                    vals['rc'] = self.customer_request_id.rc
                    vals['centre_rc'] = self.customer_request_id.centre_rc
                    if not self.customer_request_id.name: vals['name'] = vals['code']
                    vals['customer_request_id'] = self.customer_request_id.id
                    self.customer_request_id.partner_id = self.env['res.partner'].sudo().create(vals)
                    self._cr.execute("UPDATE res_partner SET create_uid = "+str(self._uid)+" WHERE id = "+str(self.customer_request_id.partner_id.id))
                    self.customer_request_id.state='confirmed'
                    self.customer_request_id.confirmation_date = datetime.datetime.now()
                else:
                    raise exceptions.ValidationError("Ce client existe dèja dans le système : ( "+str(self.ifu)+", "+str(self.customer_request_id.code)+", "+str(self.customer_request_id.code_categ)+" )")

        elif self.force:
            categories = self.env['res.partner.category'].search([('code','=',self.customer_request_id.code_categ),('type','=','customer')])
            if categories:
                categ_id = categories[0].id
            else:
                categ_id = False
            vals = {
                    'categ_id':categ_id,
                    'customer':True,
                    'property_product_pricelist':False,
                    'request_creation_date':self.customer_request_id.create_date,
                    'ifu':'999999',
                    'is_company':True,
                    'name':self.customer_request_id.name,
                    'code':self.customer_request_id.code,
                    'rc':self.customer_request_id.rc,
                    'centre_rc':self.customer_request_id.centre_rc,
                    'forced':True,
                    'reason_id':self.reason_id and self.reason_id.id or False
                    }
            if not self.customer_request_id.name: vals['name'] = vals['code']
            vals['customer_request_id'] = self.customer_request_id.id
            self.customer_request_id.partner_id = self.env['res.partner'].sudo().create(vals)
            self._cr.execute("UPDATE res_partner SET create_uid = "+str(self._uid)+" WHERE id = "+str(self.customer_request_id.partner_id.id))
            self.customer_request_id.state='confirmed'
            self.customer_request_id.confirmation_date = datetime.datetime.now()

        else:
            raise exceptions.ValidationError(_("Vous devez renseigner un identifiant fiscal"))


customer_request_wizard()