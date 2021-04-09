# -*- coding: utf-8 -*-

from openerp import tools
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _


class ResTransaction(models.Model):
    _inherit = 'res.transaction'

    @api.model
    def send_transaction(self, values):
        res_transaction_id = False
        if values:
            ### Validate Data
            if not values.get('transaction_id'):
                return {'faultCode': 0, 'faultString': 'Transaction is required.'}
            if not values.get('contract_id'):
                return {'faultCode': 0, 'faultString': 'Contract is required.'}
            if not values.get('date'):
                return {'faultCode': 0, 'faultString': 'Date is required.'}

            ### Find Data From DB
            contract_id = self.env['res.contract'].search([('name', '=', values['contract_id']), ('is_template', '=', False),('type_contract','=','package')], limit=1)
            if not contract_id:
                return {'faultCode': 0, 'faultString': 'contract_id doesn’t exist in Odoo db'}

            
            vals = {
                ### API Fields
                'name': values['transaction_id'],
                'contract_id': contract_id.id,
                'event_ref': values.get('event_ref'),
                'date': str(values['date']).strip(),
                'user': values.get('user'),
            }

            res_transaction_id = self.env['res.transaction'].create(vals)
        
        if res_transaction_id:
            msg = _("Transaction created \n Id: %s \n Event Ref: %s \n User: %s \n Date: %s") % \
                    (res_transaction_id.name, res_transaction_id.event_ref, res_transaction_id.user, res_transaction_id.date)
            res_transaction_id.contract_id.message_post(body=tools.plaintext2html(msg))
            return {'success': res_transaction_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}

    @api.model
    def cancel_transaction(self, values):
        transaction_id = False
        if values:
            ### Validate Data
            if not values.get('transaction_id'):
                return {'faultCode': 0, 'faultString': 'Transaction is required.'}
            if not values.get('motif'):
                return {'faultCode': 0, 'faultString': 'Motif is required.'}
            if not values.get('date_cancel'):
                return {'faultCode': 0, 'faultString': 'Cancel Date is required.'}

            ### Find Data From DB
            transaction_id = self.env['res.transaction'].search([('name', '=', values['transaction_id'])], limit=1)
            if not transaction_id:
                return {'faultCode': 0, 'faultString': 'transaction_id doesn’t exist in Odoo db'}

            vals = {
                ### API Fields
                'cancel_date': str(values['date_cancel']).strip(),
                'motif': values['motif'],
            }
            transaction_id.write(vals)
            transaction_id.action_cancel()

        if transaction_id:
            msg = _("Transaction Cancelled \n Id: %s \n Motif: %s \n  Date Cancel: %s") % \
                    (transaction_id.name, transaction_id.motif, transaction_id.cancel_date)
            transaction_id.contract_id.message_post(body=tools.plaintext2html(msg))
            return {'success': transaction_id.id}
        else:
            return {'faultCode': 0, 'faultString': 'Something went wrong!'}
