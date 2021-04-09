# -*- coding: utf-8 -*-

import base64
from openerp import api, fields, models, _


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    attachment_id = fields.Binary(type='binary', string='Justificatif')
    attachment_name = fields.Char(string='Justificatif Name')
    date_create_portnet = fields.Date(string='Date création GU')

    @api.model
    def set_payment(self, values):
        voucher_payment_id = False
        if values:
            ### Validate Data
            if not values.get('partner_id'):
                return {'faultCode': 0, 'faultString': 'Partner is required.'}
            if not values.get('subscription_id'):
                return {'faultCode': 0, 'faultString': 'Subscription is required.'}
            if not values.get('amount'):
                return {'faultCode': 0, 'faultString': 'Amount is required.'}
            if not values.get('reglment_method_id'):
                return {'faultCode': 0, 'faultString': 'Method of payment is required.'}
            if not values.get('reference_delivery'):
                return {'faultCode': 0, 'faultString': "Ref. du règlement is required."}
            if not values.get('date_create'):
                return {'faultCode': 0, 'faultString': 'Create Date is required.'}

            ### Find Data From DB
            partner_id = self.env['res.partner'].search([('code', '=', values['partner_id']), ('customer', '=', True)], limit=1)
            if not partner_id:
                return {'faultCode': 0, 'faultString': 'partner_id doesn’t exist in Odoo db'}

            reglement_method_id = self.env['account.invoice.tva.reglement'].search([('id', '=', values['reglment_method_id'])], limit=1)
            if not reglement_method_id:
                return {'faultCode': 0, 'faultString': 'reglement_method_id doesn’t exist in Odoo db'}

            journal_id = self.env['account.journal'].search([('type', 'in', ['bank'])], limit=1)
            if not journal_id:
                return {'faultCode': 0, 'faultString': 'bank journal doesn’t exist in Odoo db'}

            period_id = self.env['account.period'].search([('date_start', '<=', fields.Date.today()), ('date_stop', '>=', fields.Date.today())], limit=1)
            if not period_id:
                return {'faultCode': 0, 'faultString': 'period_id doesn’t exist in Odoo db'}

            subscription_id = self.env['res.contract'].search([('name', '=', values['subscription_id']), ('is_template', '=', False),('type_contract','=','package')], limit=1)
            if not subscription_id:
                return {'faultCode': 0, 'faultString': 'subscription_id doesn’t exist in Odoo db'}
            
            # if subscription_id.state != 'pending':
            #     return {'faultCode': 0, 'faultString': 'Subscription state is different from “pending”'}
            
            # paid_invoices = []
            # invoice_ids = self.env['account.invoice'].search([('contract_id', '=', subscription_id.id), ('type', '=', 'out_invoice'), ('state', '=', 'paid')])
            # if invoice_ids:
            #     for invoice in invoice_ids:
            #         paid_invoices.append(invoice.number)
            if subscription_id.etat_facturation == 'paid':
                return {'faultCode': 0, 'faultString': 'Subcription already paid.'}

            vals = {
                ### API Fields
                'partner_id': partner_id.id,
                'name': values.get('name', ''),
                'contract_id': subscription_id.id,
                'reference': values['subscription_id'],
                'period_id': period_id.id,
                'reglement_method_id': reglement_method_id.id,
                'amount': float(values['amount']),
                'reference_delivery': str(values['reference_delivery']).strip(),
                'account_id': journal_id.default_debit_account_id.id,
                'date_create_portnet': str(values['date_create']).strip(),
            }

            if values.get('attachment'):
                extension = ''
                data = base64.decodestring(values['attachment'])
                ext = data.split('\n')[0]
                if 'PNG' in ext:
                    extension = '.png'
                elif 'PDF' in ext:
                    extension = '.pdf'
                elif 'GIF' in ext:
                    extension = '.gif'
                elif 'WEBP' in ext:
                    extension = '.WebP'
                else:
                    extension = '.jpeg'

                attachment_name_concate = str(values['name']).strip() + str(values['date_create']).strip() + extension
                vals.update({'attachment_id': values['attachment'], 'attachment_name': attachment_name_concate})
            
            voucher_payment_id = self.env['account.voucher'].with_context(default_type='receipt').create(vals)
            context = voucher_payment_id._context.copy()
            voucher_payment_id.onchange_partner_id(voucher_payment_id.partner_id.id, voucher_payment_id.journal_id.id, voucher_payment_id.amount, (voucher_payment_id.currency_id.id if voucher_payment_id.currency_id else False), voucher_payment_id.type, voucher_payment_id.date, context=context)
            if not self.env['account.invoice'].search([('contract_id', '=', voucher_payment_id.contract_id.id)]):
                voucher_payment_id.contract_id.generate_subscription_draft_invoice(fields.Date.today())
        
        if voucher_payment_id:
            return {'success': voucher_payment_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}
