# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp

class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _search_nb_contracts(self, operator, value):
        ls = []
        if operator == '=':
            operator = '=='
        for contract in self.search([]):
            condition = eval(str(contract.nb_contracts)+str(operator)+str(value))
            if condition:
                ls.append(contract.id)
        return [('id', 'in', tuple(ls))]


    name = fields.Char(string="Name", required=True, write=['portnet_invoicing.group_director'])
    code = fields.Char(string="Code douane", required=True, write=['portnet_invoicing.group_director'], read=['portnet_invoicing.group_director'])
    rc = fields.Char(string="RC", required=False, write=['portnet_invoicing.group_director'])
    # street = fields.Char(string="Adresse", required=False, write=['portnet_invoicing.group_director'])
    # street2 = fields.Char(string="Adresse", required=False, write=['portnet_invoicing.group_director'])
    centre_rc = fields.Char(string="Centre RC", required=False,)
    ifu = fields.Char(string="Identifant fiscal", required=False, write=['portnet_invoicing.group_director'], read=['portnet_invoicing.group_director'])
    categ_id = fields.Many2one(comodel_name="res.partner.category", string="Catégorie client", required=False, domain =[('type','=','customer')])
    supplier_categ_id = fields.Many2one(comodel_name="res.partner.category", string="Catégorie fournisseur", required=False, domain =[('type','=','supplier')])
    forced = fields.Boolean(string="Demande de création Forcée")
    nb_contracts = fields.Integer(string="Nombre de contrats", required=False,compute="_get_nb_contracts",store=True)
    state = fields.Selection(string="Etat", selection=[('draft', 'Brouillon'), ('confirmed', 'Validé'), ], required=False,default ='draft')
    subscribed = fields.Boolean(string="Facture d'abonnement générée")
    etl = fields.Boolean(string="Client repris ?")
    first_invoice_date = fields.Date(string="Date première facture")
    request_creation_date = fields.Date(string="Date de création demande")
    partner_group_id = fields.Many2one(comodel_name="res.partner.group", string="Société mère", required=False, )
    ice = fields.Char(string="ICE", required=False, )
    treasury_term_id=fields.Many2one(comodel_name='account.payment.term',string ='Conditions de trésorerie')
    penalty_rate = fields.Float(string="Taux pénalité (10% => 0.1)", digits_compute=dp.get_precision('Account'), required=False)
    without_subscription = fields.Boolean(string="Sans abonnement", help="Si la case est cochée, pas besoin de générer une facture d'abonnement pour ce client")
    reason_id = fields.Many2one(comodel_name="subscription.fiscal.id.reason", string="Motif")
    customer_request_id = fields.Many2one(comodel_name="customer.request", string="Demande de création client", required=False, )
    contract_ids = fields.One2many(comodel_name='res.contract', inverse_name='partner_id', string='Contrats')


    # @api.onchange('categ_id')
    # def _set_fiscal_position(self):
    #     if self.categ_id:
    #         self.property_account_position = self.categ_id.fiscal_position_id and self.categ_id.fiscal_position_id.id or False
    #     elif not self.categ_id:
    #         self.property_account_position = False

    @api.model
    def create(self, vals):
        if vals.get('website'):
            vals['website'] = self._clean_website(vals['website'])
        # if 'categ_id' in vals.keys() and vals['categ_id'] != False:
        #     category = self.env['res.partner.category'].search([('id','=',vals['categ_id'])])
        #     if category:
        #         vals['property_account_position'] = category[0].fiscal_position_id and category[0].fiscal_position_id.id or False
        vals['property_product_pricelist'] = False
        vals['notify_email'] = 'always'
        partner = super(res_partner, self).create(vals)
        self._fields_sync(partner, vals)
        self._handle_first_contact_creation(partner)
        print partner.id
        return partner

    @api.depends('contract_ids')
    @api.one
    def _get_nb_contracts(self):
        self.nb_contracts = self.contract_ids and len(self.contract_ids) or 0

    @api.v7
    def init(self,cr):
        from datetime import date, datetime, timedelta
        today = datetime.now().date()
        dt=datetime.strptime('2017-03-02', "%Y-%m-%d").date()
        if today == dt:
            cr.execute('select partner_id,count(id) from res_contract where partner_id is not null group by partner_id')
            res = [[p[0],p[1]] for p in cr.fetchall()]
            for r in res :
                cr.execute("update res_partner set nb_contracts=%s where id=%s"%(r[1],r[0]))



    _sql_constraints = [

        ("unique_customer","UNIQUE(ifu,code,categ_id)","Ce client existe dèja"),
    ]

    @api.one
    def set_draft(self):
        self.state = 'draft'

    @api.one
    def set_confirmed(self):
        self.state = 'confirmed'

    # Génération du contrat à partir du modèle de contrat + première facture d'abonnement validée
    @api.multi
    def do_subscription(self):
         # Assistant de validation
        return {
            'name':_("Facture d'abonnement"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'customer.subscription.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            }

res_partner()


class res_partner_category(models.Model):
    _name = 'res.partner.category'
    _inherit = 'res.partner.category'

    pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Liste de prix", required=False, domain=[('active','=',True)])
    type = fields.Selection(string="Type", selection=[('customer', 'Client'), ('supplier', 'Fournisseur'), ], required=True)
    payment_term_id = fields.Many2one(comodel_name="account.payment.term", string="Conditions de paiement", required=False, )
    annual_invoicing = fields.Boolean(string="Facturation en début d'année",help="Si cochée, la facture d'abonnement sera générée chaque début d'année indépendamment des dates sur le contrat")
    op_type_ids = fields.One2many(comodel_name="operation.type", inverse_name="partner_categ_id", string="Types d'opérations", required=False, )
    code = fields.Char(string="Code", required=True, )
    penalty_rate = fields.Float(string="Taux pénalité (10% => 0.1)", digits_compute=dp.get_precision('Account'), required=False)
    invoicing_advance_in_months = fields.Integer(string="Anticipation de la facture en mois ", required=False,)
    fiscal_position_id = fields.Many2one(comodel_name="account.fiscal.position", string="Position fiscale", required=False, )
    be_notified = fields.Boolean(string="Etre Notifié",
                                 help="Si cochée, Le client va recevoir la totalité des notifications Si non il va rien recevoir")
    closed_related_contracts = fields.Boolean(string="Cloturé les contrats",
                                 help="Si cochée, Les contrats lié à ce client dont la facture est impayé vont être cloturé")

    _sql_constraints = [

        ("unique_code_categ","UNIQUE(type,code)","Le couple Type/Code doit être unique"),
    ]

res_partner_category()