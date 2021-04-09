# -*- encoding: utf-8 -*-

from openerp import netsvc ,models, fields, api, exceptions, _
from datetime import datetime
from openerp.osv import osv
import psycopg2
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp
import base64
import re
import time

class customer_invoicing_wizard(models.TransientModel):
    _name = 'customer.invoicing.wizard'

    operation_id=fields.Many2one(comodel_name="operation.type",string="Type d'opération",required=False)
    partner_id = fields.Many2one(comodel_name="res.partner", string="Client", required=False)#domain =[('customer','=',True),('state','confirmed')]
    period_id = fields.Many2one(comodel_name="account.period", string="Période",required=False)
    date_invoice=fields.Date(string='Date Facture',default=lambda *a: time.strftime('%Y-%m-%d'))

    @api.multi
    def get_tuple(self,list):
        if len(list) ==1 :
            return "('"+str(list[0])+"')"
        else :
            return tuple(list)

    @api.v7
    def onchange_partner(self,cr,uid,ids,partner_id,context=None):
        if partner_id :
            partner=self.pool.get("res.partner").browse(cr,uid,partner_id)
            domain=[]
            if partner.categ_id :
                op_ids=partner.categ_id.op_type_ids
                if op_ids:
                    print op_ids._ids
                    domain=[('id','in',op_ids._ids)]
                    return  {'domain':{'operation_id':domain}}
            if not domain :
                return  {'domain':{'operation_id':domain,'period_id':domain},'value':{'operation_id':False}}

    @api.multi
    def _check_partner(self,partner_id):
         if not partner_id.code :
                    code="partner_id"+str(partner_id.id)
                    output="Le client %s n'a pas de code douane"%partner_id.name
                    self.env['report.exception'].set_exception(code,output)
         if not partner_id.categ_id :
                    code="category_partner_id"+str(partner_id.id)
                    output="Le client %s n'a pas de catégorie, id :%s"%(partner_id.name,partner_id.id)
                    self.env['report.exception'].set_exception(code,output)
         if not partner_id.categ_id.op_type_ids :
                    code="category_op_type_ids_id"+str(partner_id.categ_id.id)
                    output="La catégorie client "+str(partner_id.categ_id.name)+" ne contient aucun type d'opération"
                    self.env['report.exception'].set_exception(code,output)
         if not partner_id.property_product_pricelist or not partner_id.categ_id.pricelist_id:
                    code="property_product_pricelist_partner_id"+str(partner_id.id)
                    output="Merci de definir une liste de prix pour le client  "+str(partner_id.name)
                    self.env['report.exception'].set_exception(code,output)
    @api.multi
    def _get_operation_filters(self,operation_id):
         if operation_id.state !='confirmed' :
                         code="operation_id"+str(operation_id.id)
                         output="le type opération %s n'est validée , merci de contacter l'administrateur"%(operation_id.name)
                         self.env['report.exception'].set_exception(code,output)
         filters=self.env['operation.type']._get_op_filters(operation_id)
         if not filters :
                         code="operation_filters_id"+str(operation_id.id)
                         output="Les filtres de l'opération %s ne sont pas configuré , merci de contacter votre administrateur"%(operation_id.name)
                         self.env['report.exception'].set_exception(code,output)
         return filters

    @api.multi
    def _cron_action_confirm(self,dbcr=False,partner_id=False,period_id=False,invoicing_op_id=False):
        """
        :param dbcr: le database cursor du réferentiel de stockage des opérations
        :param partner_id: l'insatnce de l'objet partenaire
        :param period_id: la période fiscale
        :return: None
        """
        operation_type_obj=self.env["operation.type"]
        date_invoice=self.date_invoice
        #Test sur le code douane , categorie client , types opération
        if partner_id :
            self._check_partner(partner_id)
            op_ids=partner_id.categ_id.op_type_ids
            for operation_id in op_ids :
                product_id=operation_id.product_id
                if not  product_id.property_account_income:
                         code="product_property_account_income_id"+str(product_id.id)
                         output="Merci de configurer le compte de revenus du produit %s"%(product_id.name)
                         self.env['report.exception'].set_exception(code,output)
                filters=self._get_operation_filters(operation_id)
                sql="select id from invoice_line_store"
                where=[]
                where.append("state='draft' ")
                #Mapping codes Odoo/Portnet
                matching_codes = []
                dbcr.execute("Select portnet_code FROM partner_code_map WHERE odoo_code = '"+str(partner_id.code)+"'")
                matching_codes = [x[0] for x in dbcr.fetchall()]
                if matching_codes:
                    partner_sql_filter = " AND ( "+str(filters['code'])+" = '"+str(partner_id.code)+"' OR "
                    for code in matching_codes:
                        partner_sql_filter+= str(filters['code'])+" = '"+str(code)+"' OR "
                    partner_sql_filter = partner_sql_filter[:-3]
                    partner_sql_filter+=" )"
                else:
                    where.append("%s ilike '%s' "%(filters['code'],partner_id.code))
                #Mapping codes Odoo/Portnet
                if period_id :
                    where.append("%s ilike '%s' "%(filters['month'],period_id._get_period_months()))
                    where.append("%s ilike '%s' "%(filters['year'],period_id._get_period_fiscalyear()))
                    where.append("%s ilike '%s' "%(filters['product'],operation_id.product_id.default_code))
                    if not date_invoice :
                        date_invoice=period_id.date_stop
                sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
                #Mapping codes Odoo/Portnet
                if matching_codes:
                    sql+=partner_sql_filter
                #Mapping codes Odoo/Portnet
                print "SQL",sql
                dbcr.execute(sql)
                result = map(lambda x: x[0], dbcr.fetchall())
                count=len(result)
                print "count",count,result
                if count ==0 :
                         return True
                invoice_id=self.env['account.invoice'].action_create_invoice(date_invoice,partner_id,operation_id.id,product_id,count,result)
                if invoice_id:
                    self.env['account.invoice'].browse(invoice_id).write({'invoicing_op_id':invoicing_op_id})
                    line_store_ids_string = str(result)
                    line_store_ids_string = line_store_ids_string.replace('[','(')
                    line_store_ids_string = line_store_ids_string.replace(']',')')
                    dbcr.execute("UPDATE invoice_line_store SET in_progress = true WHERE id in "+line_store_ids_string)
                # if invoice_id and result :
                #     inv = self.env['account.invoice'].browse(invoice_id)
                #     inv.write({'date_invoice':datetime.now().date()})
                #     inv.move_id.action_update_maturity_dates()
                #     inv.invoice_print_auto(operation=True)
                #     inv.action_send_mail_auto()
                #     if len (result) >1 :
                #         req="update invoice_line_store set state='done', invoice_id='%s' where id in %s"%(invoice_id,tuple(result))
                #     else :
                #         req="update invoice_line_store set state='done', invoice_id='%s' where id = %s"%(invoice_id,result[0])
                #     print req
                #     dbcr.execute(req)

    @api.multi
    def action_confirm(self):
        """
        Action suite à la validation d'une facture à la demande.
        :return:
        """
        operation_type_obj=self.env["operation.type"]
        partner_id=self.partner_id
        period_id=self.period_id
        databse_id=self.env['op.store.db.settings'].search([('state','=','confirmed')])
        if not databse_id :
            raise except_orm (_("Configuration Base Stockage "),
                                      _("Pas de base confirmée trouvée"))
        dbcr=self.env['op.store.db.settings'].get_cursor_database(databse_id.server,databse_id.port,databse_id.dbname,databse_id.user,databse_id.password)
        date_invoice=self.date_invoice
        #Test sur le code douane , categorie client , types opération
        if partner_id :
            self._check_partner(partner_id)
            op_ids=self.operation_id
            for operation_id in op_ids :
                product_id=operation_id.product_id
                if not  product_id.property_account_income:
                        raise except_orm (_("Merci de configurer le compte de revenus du produit %s "),
                                      _("%s"%operation_id.product_id.name))
                filters=self._get_operation_filters(operation_id)
                sql="select id from invoice_line_store"
                where=[]
                where.append("state='draft' ")
                #Mapping codes Odoo/Portnet
                matching_codes = []
                dbcr.execute("Select portnet_code FROM partner_code_map WHERE odoo_code = '"+str(partner_id.code)+"'")
                matching_codes = [x[0] for x in dbcr.fetchall()]
                if matching_codes:
                    partner_sql_filter = " AND ( "+str(filters['code'])+" = '"+str(partner_id.code)+"' OR "
                    for code in matching_codes:
                        partner_sql_filter+= str(filters['code'])+" = '"+str(code)+"' OR "
                    partner_sql_filter = partner_sql_filter[:-3]
                    partner_sql_filter+=" )"
                else:
                    where.append("%s ilike '%s' "%(filters['code'],partner_id.code))
                #Mapping codes Odoo/Portnet
                if period_id :
                    where.append("%s ilike '%s' "%(filters['month'],period_id._get_period_months()))
                    where.append("%s ilike '%s' "%(filters['year'],period_id._get_period_fiscalyear()))
                    where.append("%s ilike '%s' "%(filters['product'],operation_id.product_id.default_code))
                    if not date_invoice :
                        date_invoice=period_id.date_stop
                sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
                #Mapping codes Odoo/Portnet
                if matching_codes:
                    sql+=partner_sql_filter
                #Mapping codes Odoo/Portnet
                print "SQL",sql
                dbcr.execute(sql)
                result = map(lambda x: x[0], dbcr.fetchall())
                count=len(result)
                print "count",count,result
                if count ==0 :
                        raise except_orm (_("Il n'existe pas de lignes non facturées pour le client choisi : "),
                                      _("Code produit :%s \n Nom client :%s \n  Mois : %s"%(operation_id.product_id.default_code,partner_id.name,period_id.name)))
                invoice_id=self.env['account.invoice'].action_create_invoice(period_id.date_stop,partner_id,operation_id.id,product_id,count,result)
                if invoice_id:
                    line_store_ids_string = str(result)
                    line_store_ids_string = line_store_ids_string.replace('[','(')
                    line_store_ids_string = line_store_ids_string.replace(']',')')
                    dbcr.execute("UPDATE invoice_line_store SET in_progress = true WHERE id in "+line_store_ids_string)
                # if invoice_id and result :
                #     invoice= self.env['account.invoice'].browse(invoice_id)
                #     invoice.write({'date_invoice':self.date_invoice})
                #     invoice.move_id.action_update_maturity_dates()
                #     invoice.invoice_print_auto(operation=True)
                #     invoice.action_send_mail_auto()
                #     if len (result) >1 :
                #         req="update invoice_line_store set state='done', invoice_id='%s' where id in %s"%(invoice_id,tuple(result))
                #     else :
                #         req="update invoice_line_store set state='done', invoice_id='%s' where id = %s"%(invoice_id,result[0])
                #     print req
                #     dbcr.execute(req)
                #     dbcr.execute("COMMIT")





customer_invoicing_wizard()