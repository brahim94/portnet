# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
import base64


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def get_invoice_state(self, state):
        state_code = ''
        if state:
            if state in ['draft', 'proforma', 'proforma2']:
                state_code = 'D'
            elif state in ['open']:
                state_code = 'O'
            elif state in ['paid']:
                state_code = 'P'
            elif state in ['cancel']:
                state_code = 'C'
        return state_code

    @api.model
    def get_invoice_data(self, values):
        invoices = []
        if values:
            ### Validate Data
            if not values.get('contract_id'):
                return {'faultCode': 0, 'faultString': 'contract_id is required.'}
            
            ### Find Data From DB
            contract_id = self.env['res.contract'].search([('name', '=', values['contract_id']), ('is_template', '=', False),('type_contract','=','package')], limit=1)
            if not contract_id:
                return {'faultCode': 0, 'faultString': 'contract_id doesn’t exist in Odoo db'}

            invoice_ids = self.search([('contract_id', '=', contract_id.id), ('type', '=', 'out_invoice')])
            if not invoice_ids:
                return {'faultCode': 0, 'faultString': 'No invoices found in Odoo db'}
            
            for invoice in invoice_ids:
                vals = [
                        ### API Fields
                        invoice.number if invoice.number else '',
                        invoice.period_id.name if invoice.period_id else '',
                        invoice.date_invoice if invoice.date_invoice else '',
                        invoice.amount_total,
                        invoice.get_invoice_state(invoice.state),
                ]
                invoices.append(vals)        
        if invoices:
            return {'success': invoices}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}

    @api.model
    def get_invoice_document(self, values):
        datas = False
        if values:
            ### Validate Data
            if not values:
                return {'faultCode': 0, 'faultString': 'invoice_ref is required.'}

            ### Find invoice From DB
            invoice_id = self.search([('number', '=', values), ('type', '=', 'out_invoice')], limit=1)
            if not invoice_id:
                return {'faultCode': 0, 'faultString': 'invoice_ref doesn’t exist in Odoo db'}
        
            # Generate pdf name
            attachment_name = "INV_" + invoice_id.number + '.pdf'
                
            pdf = self.env['report'].get_pdf(invoice_id, 'account.report_invoice')
            b64_pdf = base64.encodestring(pdf)
            
            ### send file with key[file name] and value[file base64]    
            datas = {attachment_name: b64_pdf}
            
        if datas:
            return {'success': datas}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}
            