# -*- coding: utf-8 -*-
from openerp import models,api, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime
from openerp.osv import osv


class account_move(models.Model):
     _inherit="account.move"

     def button_cancel(self, cr, uid, ids, context=None):
         for line in self.browse(cr, uid, ids, context=context):
             if not line.journal_id.update_posted:
                 raise osv.except_osv(_('Error!'), _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
         if ids:
            cr.execute('UPDATE account_move '\
                       'SET state=%s '\
                       'WHERE id IN %s', ('draft', tuple(ids),))
            self.invalidate_cache(cr, uid, context=context)
         move_store_obj=self.pool.get('move.store')
         move_record=self.browse(cr,uid,ids)[0]
         for move_line in self.browse(cr, uid, ids, context=context).line_id:
             vals={
                'ref_piece':move_record.ref,
                'piece_id':ids[0],
                'move_line_id':move_line.id,
                'update_date':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'journal_id':move_record.journal_id.id,
                'period_id':move_record.period_id.id,
                'account_id':move_line.account_id.id,
                'debit':move_line.debit,
                'credit':move_line.credit,
                'currency':move_line.amount_currency,
             }
             print 'eeeeeeeeeee',vals
             move_store_obj.create(cr,uid,vals)
         return True

     def button_validate(self, cursor, user, ids, context=None):
         for move in self.browse(cursor, user, ids, context=context):
            # check that all accounts have the same topmost ancestor
            top_common = None
            for line in move.line_id:
                account = line.account_id
                top_account = account
                while top_account.parent_id:
                    top_account = top_account.parent_id
                if not top_common:
                    top_common = top_account
                elif top_account.id != top_common.id:
                    raise osv.except_osv(_('Error!'),
                                         _('You cannot validate this journal entry because account "%s" does not belong to chart of accounts "%s".') % (account.name, top_common.name))

         move_store_obj=self.pool.get('move.store')
         move_line_obj=self.pool.get('account.move.line')
         move_store_ids=move_store_obj.search(cursor,user,[('piece_id','=',ids[0])],order="update_date desc")
         if move_store_ids:
            #update_date=move_store_obj.browse(cursor,user,[move_store_ids[0]]).update_date
            length =0
            move_lines={}
            for store_id in move_store_ids:
                length +=1
                if length <= len(self.browse(cursor,user,ids).line_id):
                   vals={
                       'credit':move_store_obj.browse(cursor,user,[store_id]).credit,
                       'debit':move_store_obj.browse(cursor,user,[store_id]).debit,
                       'store_id':store_id,
                   }
                   move_lines[move_store_obj.browse(cursor,user,[store_id]).move_line_id.id]=vals
            print 'les lignes de pièces comptables',move_lines
            for line in self.browse(cursor,user,ids[0]).line_id:
                if line.id in move_lines.keys():
                   print 'la ligne actuelle de la pièce comptable',line.id,'---',move_line_obj.browse(cursor,user,[line.id]).credit,'--',move_line_obj.browse(cursor,user,[line.id]).debit
                   if move_lines[line.id]['credit'] == move_line_obj.browse(cursor,user,[line.id]).credit and  move_lines[line.id]['debit'] == move_line_obj.browse(cursor,user,[line.id]).debit :
                      move_store_obj.unlink(cursor,user,[move_lines[line.id]['store_id']])
         return self.post(cursor, user, ids, context=context)
