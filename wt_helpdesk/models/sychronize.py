# -*- coding: utf-8 -*-

from odoo import tools, models, fields, api, _
from odoo.exceptions import ValidationError
import psycopg2
import logging

_logger = logging.getLogger(__name__)

try:
    import cx_Oracle
except:
    _logger.debug('Oracle libraries not available. Please install "cx_Oracle"\
                 python package by "pip3 install cx_Oracle".')


class SychronizeSychronize(models.Model):
    _name = 'sychronize.sychronize'
    _description = 'Sychronization'

    name = fields.Char(string='Name', required=True)
    url = fields.Char(string='Address IP', required=True)
    port = fields.Char(string='Port', required=True)
    username = fields.Char(string='Utilisateur', required=True)
    password = fields.Char(string='Mot de passe', required=True)
    database = fields.Char(string='Database')
    schedule = fields.Boolean(string='Schedule')
    query = fields.Text(string='Query String', help='E.g: Select * FROM helpdesk; ')
    debug = fields.Text(string='Debug')
    options = fields.Selection([('suppliers', 'Fournisseurs'), ('articles', 'Articles'), ('invoices', 'Factures')], string='Sync Option', required=True, default='suppliers')
    connection = fields.Selection([('oracle', 'Oracle'), ('pg', 'PostgreSQL')], string='Connect To', default='oracle', required=True)
    state = fields.Selection([('draft', 'Draft'), ('verified', 'Verified')], string='Status', default='draft')

    def get_oracle_connection_string(self):
        # Example string: 
        # cx_Oracle.connect('username/password@//server.address:port/instance')
        # cx_Oracle.connect(user='', password='', dsn='url:port/instance')
        # instance = 'TPXRCTT'
        connStr = "%s/%s@//%s:%s/%s" % (self.username, self.password, self.url, self.port, self.database)
        return connStr

    @api.multi
    def verify_connection(self):
        for record in self:
            # Postgresql Connection Test
            if record.connection == 'pg':
                connection = False
                try:
                    connection = psycopg2.connect(user = record.username,
                                                  password = record.password,
                                                  host = record.url,
                                                  port = record.port,
                                                  database = record.database)
                    cursor = connection.cursor()
                except (Exception, psycopg2.Error) as error:
                    raise ValidationError(_("Error while connecting to PostgreSQL:\n %s") % tools.ustr(error))
                finally:
                    #closing database connection.
                        if(connection):
                            cursor.close()
                            connection.close()
                            record.state = 'verified'
                            return {
                                    'name': 'Message',
                                    'type': 'ir.actions.act_window',
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'res_model': 'pop.message',
                                    'target':'new',
                                    'context':{'default_name':"Connection Successful!"} 
                                    }
            
            # Oracle Connection Test
            if record.connection == 'oracle':
                connection = False
                try:
                    connStr = record.get_oracle_connection_string()
                    connection = cx_Oracle.connect(connStr)
                    cursor = connection.cursor()
                except (Exception, psycopg2.Error) as error:
                    raise ValidationError(_("Error while connecting to Oracle:\n %s") % tools.ustr(error))
                finally:
                    #closing database connection.
                        if(connection):
                            cursor.close()
                            connection.close()
                            record.state = 'verified'
                            return {
                                    'name': 'Message',
                                    'type': 'ir.actions.act_window',
                                    'view_type': 'form',
                                    'view_mode': 'form',
                                    'res_model': 'pop.message',
                                    'target':'new',
                                    'context':{'default_name':"Connection Successful!"} 
                                    }
        return True

    def makeDictFactory(self, cursor):
        columnNames = [d[0] for d in cursor.description]
        def createRow(*args):
            return dict(zip(columnNames, args))
        return createRow

    def _get_supplier_data(self):
        dict_result = []
        connStr = self.get_oracle_connection_string()
        connection = cx_Oracle.connect(connStr)
        cursor = connection.cursor()

        # cursor.execute("SELECT * from SUPPLIER_DATA")
        cursor.execute(str(self.query))
        cursor.rowfactory = self.makeDictFactory(cursor)
        data_all = cursor.fetchall()
        for row in data_all:
            dict_result.append(dict(row))
        cursor.close()
        connection.close()
        return dict_result

    @api.multi
    def sync_suppliers(self):
        for record in self:
            supplier_data = record._get_supplier_data()
            record.debug  = str(supplier_data)
            SupplierObj = self.env['res.partner']
            for supplier in supplier_data:
                supplier_id = False
                if supplier.get('CODE_FOURNISSEUR'):
                    supplier_id = SupplierObj.search([('code_fournisseur', '=', supplier['CODE_FOURNISSEUR'])], limit=1)
                if not supplier_id:
                    supplier_id = SupplierObj.create({
                            'name': supplier.get('RAISON_SOCIALE'),
                            'street': supplier.get('ADRESSE_1'),
                            'street2': supplier.get('ADRESSE_2'),
                            'city': supplier.get('VILLE'),
                            'zip': supplier.get('CODE_POSTAL'),
                            'email': supplier.get('ADRESSE_E_MAIL'),
                            'phone': supplier.get('NUMERO_TELEPHONE_STANDARD'),
                            'mobile': supplier.get('NUMERO_TELEPHONE_PORTABLE'),
                            'supplier': True,
                            'code_fournisseur': supplier.get('CODE_FOURNISSEUR'),
                        })
                else:
                    supplier_id.write({
                            'name': supplier.get('RAISON_SOCIALE'),
                            'street': supplier.get('ADRESSE_1'),
                            'street2': supplier.get('ADRESSE_2'),
                            'city': supplier.get('VILLE'),
                            'zip': supplier.get('CODE_POSTAL'),
                            'email': supplier.get('ADRESSE_E_MAIL'),
                            'phone': supplier.get('NUMERO_TELEPHONE_STANDARD'),
                            'mobile': supplier.get('NUMERO_TELEPHONE_PORTABLE'),
                            'supplier': True,
                            'code_fournisseur': supplier.get('CODE_FOURNISSEUR'),
                        })
#                print ("Supplier....................",supplier)
        if self._context.get('manual'):
            return {
                    'name': 'Message',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pop.message',
                    'target':'new',
                    'context':{'default_name':"Fournisseurs sychronisation process is completed!"} 
                    }
        else:
            return True

    def _get_article_data(self):
        dict_result = []
        connStr = self.get_oracle_connection_string()
        connection = cx_Oracle.connect(connStr)
        cursor = connection.cursor()
        
        # cursor.execute("SELECT * from ARTICLE_DATA")
        cursor.execute(str(self.query))
        cursor.rowfactory = self.makeDictFactory(cursor)
        data_all = cursor.fetchall()
        for row in data_all:
            dict_result.append(dict(row))
        cursor.close()
        connection.close()
        return dict_result

    def _get_category(self, name, code, parent, level):
        category = False
        CategoryObj = self.env['product.category']
        if parent:
            if level == 1:
                category = CategoryObj.search([('code_ray', '=', code), ('parent_id', '=', parent.id)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_ray': code, 'parent_id': parent.id})
            elif level == 2:
                category = CategoryObj.search([('code_fam', '=', code), ('parent_id', '=', parent.id)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_fam': code, 'parent_id': parent.id})
            elif level == 3:
                category = CategoryObj.search([('code_sfam', '=', code), ('parent_id', '=', parent.id)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_sfam': code, 'parent_id': parent.id})
            else:
                category = CategoryObj.search([('code_ssfam', '=', code), ('parent_id', '=', parent.id)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_ssfam': code, 'parent_id': parent.id})
        else:
            if level == 1:
                category = CategoryObj.search([('code_ray', '=', code)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_ray': code})
            elif level == 2:
                category = CategoryObj.search([('code_fam', '=', code)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_fam': code})
            elif level == 2:
                category = CategoryObj.search([('code_sfam', '=', code)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_sfam': code})
            else:
                category = CategoryObj.search([('code_ssfam', '=', code)], limit=1)
                if not category:
                    category = CategoryObj.create({'name': name, 'code_ssfam': code})
        return category

    @api.multi
    def sync_articles(self):
        for record in self:
            article_data = record._get_article_data()
            record.debug  = str(article_data)
            ArticleObj = self.env['articles.parameter']
            SupplierObj = self.env['res.partner']
            for article in article_data:
                # Category Level 1
                category_level_1 = record._get_category(article.get('RAY'), article.get('CODE_RAY'), False, 1)
                
                # Category Level 2
                category_level_2 = record._get_category(article.get('FAM'), article.get('CODE_FAM'), category_level_1, 2)

                # Category Level 3
                category_level_3 = record._get_category(article.get('SFAM'), article.get('CODE_SFAM'), category_level_2, 3)
                
                # Category Level 4
                category_level_4 = record._get_category(article.get('SSFAM'), article.get('CODE_SSFAM'), category_level_3, 4)

                # Fournisseur
                supplier_id = False
                if article.get('FOURNISSEUR'):
                    supplier_id = SupplierObj.search([('code_fournisseur', '=', article['FOURNISSEUR']), ('supplier', '=', True)], limit=1)
#                if not supplier_id:
#                    raise ValidationError(_("Fournisseur %s not found in system.") % article.get('LIB_FOURNISSEUR'))
#                    # supplier_id = SupplierObj.create({'name': article.get('LIB_FOURNISSEUR') if article.get('LIB_FOURNISSEUR') else 'Test', 'code_fournisseur': article.get('FOURNISSEUR'), 'supplier': True})
#                
#                print ("Article--------------------",article)
                # Article
                article_id = False
                if article.get('CODE_INT'):
                    article_id = ArticleObj.search([('code', '=', article['CODE_INT'])], limit=1)
                if not article_id:
                    article_id = ArticleObj.create({
                            'name': article.get('LIBELLE') if article.get('LIBELLE') else article.get('CODE_CAISSE'),
                            'code': article.get('CODE_INT'),
                            'code_ean': article.get('CODE_CAISSE'),
                            'fournisseur': supplier_id.id if supplier_id else False,
                            'code_rayon': category_level_1.id if category_level_1 else False,
                            'code_fam': category_level_2.id if category_level_2 else False,
                            'code_sfam': category_level_3.id if category_level_3 else False,
                            'code_ssfam': category_level_4.id if category_level_4 else False,
                        })
                else:
                    article_id.write({
                            'name': article.get('LIBELLE') if article.get('LIBELLE') else article.get('CODE_CAISSE'),
                            'code': article.get('CODE_INT'),
                            'code_ean': article.get('CODE_CAISSE'),
                            'fournisseur': supplier_id.id if supplier_id else False,
                            'code_rayon': category_level_1.id if category_level_1 else False,
                            'code_fam': category_level_2.id if category_level_2 else False,
                            'code_sfam': category_level_3.id if category_level_3 else False,
                            'code_ssfam': category_level_4.id if category_level_4 else False,
                        })
        if self._context.get('manual'):
            return {
                    'name': 'Message',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pop.message',
                    'target':'new',
                    'context':{'default_name':"Article sychronisation process is completed!"} 
                    }
        else:
            return True

    def _get_invoice_data(self):
        dict_result = []
        connection = psycopg2.connect(user = self.username,
                                      password = self.password,
                                      host = self.url,
                                      port = self.port,
                                      database = self.database)

        cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
        # cursor.execute("SELECT * from invoice_data;")
        cursor.execute(str(self.query))
        data_all = cursor.fetchall()
        for row in data_all:
            dict_result.append(dict(row))
        cursor.close()
        connection.close()
        return dict_result

    @api.multi
    def sync_invoices(self):
        for record in self:
            invoice_data = record._get_invoice_data()
            record.debug  = str(invoice_data)
            InvoiceObj = self.env['factures.factures']
            ArticleObj = self.env['articles.parameter']
            for invoice in invoice_data:
                invoice_id = False
                if invoice.get('code_invoice'):
                    invoice_id = InvoiceObj.search([('name','=',invoice['code_invoice'])], limit=1)
                
                article_id = False
                if invoice.get('code_caisse'):

                    article = invoice['code_caisse']
                    article_id = ArticleObj.search([('code_ean','=',invoice['code_caisse'])], limit=1)
                    # if not article_id:
                    #     article_id = ArticleObj.create({'name': invoice['code_caisse']})
                #if not article_id:

                #    article_id = None 

                #    article = invoice['code_caisse']
                #    # raise ValidationError(_("Article %s not found in system.") % invoice.get('code_caisse'))
                magasin_id = self.env['crm.magasin'].search([('id_magasin','=',str(invoice.get('id_magas_in')))])
                if not invoice_id:
                    invoice_id = InvoiceObj.create({
                            'invoice_number': invoice.get('num_invoice'),
                            'date': invoice.get('purchase_date'),
                            'sequence': invoice.get('line_number'),
                            'article_id': article_id and article_id.id,
                            'article':article,
                            'qty': invoice.get('qty'),
                            'amount': invoice.get('amount'),
                            'id_magas_in': str(invoice.get('id_magas_in')),
                            'magasin_id':magasin_id and magasin_id.id
                        })
                    invoice_id.onchange_invoice_number_sequence()
                else:
                    invoice_id.write({
                            'invoice_number': invoice.get('num_invoice'),
                            'date': invoice.get('purchase_date'),
                            'sequence': invoice.get('line_number'),
                            'article_id': article_id and article_id.id,
                            'article':article,
                            'qty': invoice.get('qty'),
                            'amount': invoice.get('amount'),
                            'id_magas_in': str(invoice.get('id_magas_in')),
                            'magasin_id':magasin_id and magasin_id.id
                        })
                    invoice_id.onchange_invoice_number_sequence()
#                print ("Invoice Data............",invoice)
        
        if self._context.get('manual'):
            return {
                    'name': 'Message',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pop.message',
                    'target':'new',
                    'context':{'default_name':"Factures sychronisation process is completed!"} 
                    }
        else:
            return True

    @api.multi
    def reset_connection(self):
        return self.write({'state': 'draft'})

    @api.model
    def cron_import_suppliers(self):
        for sync in self.env['sychronize.sychronize'].search([('state', '=', 'verified'), ('connection', '=', 'oracle'), ('options', '=', 'suppliers'), ('schedule', '=', True)]):
            sync.sync_suppliers()

    @api.model
    def cron_import_articles(self):
        for sync in self.env['sychronize.sychronize'].search([('state', '=', 'verified'), ('connection', '=', 'oracle'), ('options', '=', 'articles'), ('schedule', '=', True)]):
            sync.sync_articles()

    @api.model
    def cron_import_invoices(self):
        for sync in self.env['sychronize.sychronize'].search([('state', '=', 'verified'), ('connection', '=', 'pg'), ('options', '=', 'invoices'), ('schedule', '=', True)]):
            sync.sync_invoices()