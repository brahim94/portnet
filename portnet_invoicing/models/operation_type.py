# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import datetime
from openerp.exceptions import except_orm, Warning, RedirectWarning

class operation_type(models.Model):
    _name = 'operation.type'

    name = fields.Char(string="Nom", required=True)
    partner_categ_id = fields.Many2one(comodel_name="res.partner.category", string="Catégorie de client", required=True,domain=[('type','=','customer')] )
    state = fields.Selection(string="Statut", selection=[('draft', 'Brouillon'), ('confirmed', 'Validé')], required=False, default='draft' )
    line_ids = fields.One2many(comodel_name="operation.type.line", inverse_name="op_id", string="Champs", required=False)
    product_category_id = fields.Many2one(comodel_name="product.category", string="Catégorie du produit",required=True)
    product_id = fields.Many2one(comodel_name="product.product", string="Produit",required=True)
    fixed_price = fields.Boolean(string="Prix forfaitaire ?")

    @api.onchange('product_id','partner_categ_id')
    def _compute_name(self):
        if self.partner_categ_id and self.product_id:
            self.name = self.partner_categ_id.name+" / "+self.product_id.name


    @api.multi
    def _get_op_filters(self,op_id=False):
        if op_id :
                vals={}
                for l in op_id.line_ids:
                    if l.filter=='month':
                        vals['month']=l.field
                    if l.filter=='year':
                        vals['year']=l.field
                    if l.filter=='code':
                        vals['code']=l.field
                    if l.filter=='product':
                        vals['product']=l.field
                    if l.filter=='code_op':
                        vals['code_op']=l.field
                return vals
        else :
            return False

    @api.one
    def set_confirmed(self):
        res=[]
        for line in self.line_ids :
            if line.filter:
                    res.append(line.filter)
        res=set(res)
        list=set(['month','year','code','product','code_op'])
        if len(list-res)!=0:
                 raise except_orm(_("Vous n'avez pas configuré tout les filtres"),_(list))
        self.state = 'confirmed'

    @api.one
    def set_draft(self):
        self.state = 'draft'


    @api.model
    def create(self, vals):
        if 'code' in vals: vals['code'] = vals['code'].upper()
        return super(operation_type, self).create(vals)

    def write(self, cr, uid, ids, vals, context=None):
        if 'code' in vals: vals['code'] = vals['code'].upper()
        return super(operation_type, self).write(cr, uid, ids, vals, context=context)

    _sql_constraints = [

        ("unique_categ_product","UNIQUE(partner_categ_id,product_id)","Le couple catgéorie de client/Produit doit être unique"),
        ("unique_name","UNIQUE(name)","Le nom doit être unique"),
    ]


operation_type()


class operation_type_line(models.Model):
    _name = 'operation.type.line'
    _order= 'sequence asc'

    name = fields.Char(string="Libellé", required=True)
    field = fields.Selection(string="", selection=[('type', 'Produit'),('code_op', 'Code opération'),('column3', 'Colonne 3'),('column4', 'Colonne 4'),
                                                   ('column5', 'Colonne 5'),('column6', 'Colonne 6'), ('column7', 'Colonne 7'),('column8', 'Colonne 8'),
                                                   ('column9', 'Colonne 9'),('column10', 'Colonne 10'),('column11', 'Colonne 11'),('column12', 'Colonne 12'),
                                                   ('column13', 'Colonne 13'),('column14', 'Colonne 14'),('column15', 'Colonne 15'),('column16', 'Colonne 16'),
                                                   ('column17', 'Colonne 17'),('column18', 'Colonne 18'),('column19', 'Colonne 19'),('column20', 'Colonne 20')],
                             required=True, )
    data_type = fields.Selection(string="", selection=[('char', 'Char'), ('integer', 'Integer'), ('float', 'Float'), ('date','Date')], required=True, )
    required = fields.Boolean(string="Requis")
    report = fields.Boolean(string="Rapport")
    filter = fields.Selection(string="Filtre", selection=[('month', 'Mois'), ('year', 'Année'),('code','CodeADII'),('product', 'Produit'),('code_op', 'Num OP')], required=False, )
    sequence = fields.Integer(string="Séquence")
    op_id = fields.Many2one(comodel_name="operation.type", string="Type d'opération", required=True)

    @api.constrains('filter')
    def _check_filter(self):
      if self.filter :
          res=self.search( [('filter','=',self.filter),('op_id','=',self.op_id.id)] )
          if len(res) > 1:
            raise Warning("Le filtre doit être unique par opération ")



operation_type_line()