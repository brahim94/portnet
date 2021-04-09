# -*- coding: utf-8 -*-

import time
from openerp.report import report_sxw
from openerp import pooler
from openerp.tools.translate import _
from openerp.osv import osv


class account_voucher_receipt(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_voucher_receipt, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
                                  'time': time,
                                  'getLines': self._lines_get,
                                  })
        self.context = context
    
    def _lines_get(self, voucher):
        if voucher.state != 'posted':
            raise osv.except_osv(_('Erreur d\'impression'),_('Le bon d\'encaissement n\'est pas encore validé'))
        voucherline_obj = pooler.get_pool(self.cr.dbname).get('account.voucher.line')
        voucherlines = voucherline_obj.search(self.cr, self.uid,[('voucher_id','=',voucher.id)])
        voucherlines = voucherline_obj.browse(self.cr, self.uid, voucherlines)
        print 'voucher number ==== ', voucher.number
        print 'voucher reference ==== ', voucher.reference
        
        return voucherlines
    
#     def balance(self,voucherlines):
# 
#         credits_total_due_amount = 0
#         debits_total_amount = 0
#         balance = 0
#         type = voucherlines[0].voucher_id.type
# 
#         if type == 'receipt':
#             for line in voucherlines:
#                 if line['type']== 'cr':
#                    credits_total_due_amount += line['amount_unreconciled']
#                 else:
#                    debits_total_amount += line['amount_unreconciled']
#                 
#         if type == 'payment':
#             for line in voucherlines:
#                 if line['type'] == 'cr':
#                    credits_total_due_amount += line['amount_unreconciled']
#                 else:
#                    debits_total_amount += line['amount_unreconciled']
#         
#         if  type == 'receipt':
#             balance = credits_total_due_amount - debits_total_amount
#         else:
#             balance = debits_total_amount - credits_total_due_amount
#         
#         return balance
        
        
    
report_sxw.report_sxw('report.account.voucher.receipt', 'account.voucher',
                      'portnet_payment/reports/account_voucher_receipt.rml',
                      parser=account_voucher_receipt)
        
        
        
        