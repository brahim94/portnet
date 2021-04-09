# -*- encoding: utf-8 -*-

from openerp import models, fields, api, exceptions, _
import datetime
import logging
import os
import binascii
import base64
import shutil
import tempfile
import time


from contextlib import closing
from shutil import make_archive

_logger = logging.getLogger(__name__)

class invoice_in_folder_wizard(models.TransientModel):
    _name = 'invoice.in.folder.wizard'

    data = fields.Binary(string='File')
    fname = fields.Char(string='Filename')
    state=fields.Boolean(string='Statut',default='false')


    def load_folder(self,cr,uid,ids,context=None):
        os.mkdir('/tmp/facture/')
        partner_ids=[]
        for id in context['active_ids']:
            invoice_record=self.pool.get('account.invoice').browse(cr,uid,[id])
            partner_id=invoice_record.partner_id.id
            #########
            report = self.pool.get('report')._get_report_from_name(cr, uid, 'account.report_invoice')
            obj = self.pool[report.model].browse(cr, uid,id)
            filename = eval(report.attachment, {'object': obj, 'time': time})
            # If the user has checked 'Reload from Attachment'
            if filename:
               alreadyindb = [('datas_fname', '=', filename),
                              ('res_model', '=', report.model),
                              ('res_id', '=', id)]
               attach_ids = self.pool['ir.attachment'].search(cr, uid, alreadyindb)
               if attach_ids:
                  # Add the loaded pdf in the loaded_documents list
                  pdf = self.pool['ir.attachment'].browse(cr, uid, attach_ids[0]).datas
                  content = base64.decodestring(pdf)
            #########
            else:
               content=self.pool.get('report').get_pdf(cr, uid, [id],'account.report_invoice',context=None)
            pdfreport_fd,pdfreport_path = tempfile.mkstemp(suffix='.pdf', prefix=invoice_record.date_invoice)
            with closing(os.fdopen(pdfreport_fd, 'w')) as pdfreport:
                 pdfreport.write(content)
            if partner_id not in partner_ids:
               partner_ids.append(partner_id)
               os.mkdir('/tmp/facture/'+invoice_record.partner_id.name)
               shutil.copy(pdfreport_path,'/tmp/facture/'+invoice_record.partner_id.name)
            else:
               shutil.copy(pdfreport_path,'/tmp/facture/'+invoice_record.partner_id.name)

        make_archive(
          '/tmp/Multi_factures',
          'zip',
          '/tmp/facture/')
        f=open('/tmp/Multi_factures.zip','rb')

        vals={
            'fname':'Multi_factures.zip',
            'data':f.read().encode('base64'),
        }

        wizard_id=self.create(cr,uid,vals)
        shutil.rmtree('/tmp/facture')
        os.remove('/tmp/Multi_factures.zip')
        self.write(cr,uid,ids,{'state':'true'})
        return {  'view_mode': 'form',
                  'view_type':'form',
                  'res_model': 'invoice.in.folder.wizard',
                  'context':context,
                  'res_id':wizard_id,
                  'type': 'ir.actions.act_window',
                  'target':'new',
                  }

invoice_in_folder_wizard()