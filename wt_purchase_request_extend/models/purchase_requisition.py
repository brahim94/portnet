# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning, UserError, ValidationError
from odoo.osv import expression
from lxml import etree


PURCHASE_REQUISITION_STATES = [
    ('draft', 'Draft'),
    ('affecte', 'Affecté'),
    ('ongoing', 'Ongoing'),
    ('in_progress', 'Confirmed'),
    ('open', 'Bid Selection'),
    ('elaboration', 'Elaboration'),
    ('publication', 'Publication'),
    ('evaluation', 'Evaluation'),
    ('decision', 'Decision'),
    ('unsuccessful', 'Unsuccessful'),
    ('preparation', 'Préparation'),
    ('consultation', 'Consultation'),
    ('done', 'Closed'),
    ('cancel', 'Cancelled'),
]


class PurchaseRequisitionType(models.Model):
    _inherit = 'purchase.requisition.type'

    contract_type = fields.Selection([('Appel d’offres', 'Appel d’offres / Marché'), ('Contrat / Convention', 'Contrat / Convention'), ('Consultation / BC', 'Consultation / BC'), ('Régie', 'Régie')], string="Type Contrat")

class TenderType(models.Model):
    _name = 'tender.type'
    _description = "Tender Type"

    name = fields.Char(string="Name", required="True")


class RequisitionTerms(models.Model):
    _name = 'requisition.terms'
    _description = "Requisition Terms"

    term = fields.Integer('Term')
    date_debut = fields.Date(string="Date Début")   
    date_fin = fields.Date('Date fin')
    etat = fields.Selection([('pending', 'En attente'), ('active', 'En cours'), ('closed', 'Cloture')], string="Etat")
    purchase_requisition_id = fields.Many2one('purchase.requisition', string="Purchase Requisition")

class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    @api.model
    def _default_agreement_type(self):
        contract_type = self._context.get('contract_type', False)
        if contract_type:
            requisition_type = self.env['purchase.requisition.type'].search([('contract_type', '=', contract_type)], limit=1)
            if requisition_type:
                return requisition_type.id

    tender_type = fields.Many2one('tender.type', string="Type of tender")
    type_id = fields.Many2one('purchase.requisition.type', string="Agreement Type", default=_default_agreement_type)
    contract_type = fields.Selection(related='type_id.contract_type', readonly=True, store=True)
    besoins_ids = fields.Many2many('purchase.request.line', 'rel_purchase_requisition', 'request_line_id', 'requisition_line_id',  string="Purchase Request Line")
    tender_commission_ids = fields.One2many('tender.commission', 'requisition_id', string="commission de validation")
    project_scope = fields.Text(string="Project Scope")
    admin_charactristics = fields.Many2many('admin.characteristic', 'rel_admin_characteristic_pr', 'admin_characteristic', 'requisition_id', string="Caractéristiques")
    condition = fields.Text(string="Submission Condition")
    tender_number = fields.Char(string="Tender Number", copy=False, default=lambda self: _('New'), readonly=True)
    date_publication = fields.Date(string="Date Publication", default=fields.Date.context_today)
    lot_type = fields.Selection([('lot_unique', 'Lot unique'), ('lot_multiple', 'Lot multiple')], string="Type de Lot", default='lot_unique')
    lot_number = fields.Integer(string="Lot Number", default=1, required=True)
    lot_details_ids = fields.Many2many('lot.details', 'rel_lot_requisition', 'lot_id', 'requisition_id', string="Lots Details")
    planification_ids = fields.One2many('purchase.requisition.planification', 'requisition_id', string="Planification")
    cps_filename = fields.Char(string="CPS Filename")
    cps_attachment_id = fields.Binary(type="binary", string="CPS Final")
    rc_attachment_id = fields.Binary(type="binary", string="RC Final")
    rc_filename = fields.Char(string="RC Filename")
    estimation_attachment_id = fields.Binary(type="binary", string="Estimation")
    estimation_filename = fields.Char(string="Estimation Filename")
    commission_attachment_id = fields.Binary(type="binary", string="Commission Decision")
    commission_filename = fields.Char(string="Commission Filename")
    price_attachment_id = fields.Binary(type="binary", string="Price Schedule")
    price_filename = fields.Char(string="Price Filename")
    avis_fr_attachment_id = fields.Binary(type="binary", string="Avis d'appeal  d'offers FR")
    avis_fr_filename = fields.Char(string="Avis FR Filename")
    avis_ar_attachment_id = fields.Binary(type="binary", string="Avis d'appeal  d'offers AR")
    avis_ar_filename = fields.Char(string="Avis AR Filename")
    checklist_attachment_id = fields.Binary(type="binary", string="Offer Evaluation Checklist")
    checklist_filename = fields.Char(string="Checklist Filename")
    newspaper_attachment_id = fields.Binary(type="binary", string="Newspaper Insertion Letter")
    newspaper_filename = fields.Char(string="Newspaper Filename")
    pv_site_visit = fields.Binary(string="PV Site Visit")
    pv_site_visit_filename = fields.Char(string="PV Site Visit Filename")
    submission_days = fields.Integer(string="Deadline (Days)")
    submission_date = fields.Date(string="Date")
    site_visit_days = fields.Integer(string="Deadline (Days)")
    site_visit_date = fields.Date(string="Date")
    sample_deposit_days = fields.Integer(string="Deadline (Days)")
    sample_deposit_date = fields.Date(string="Date")
    prospectus_days = fields.Integer(string="Deadline (Days)")
    prospectus_date = fields.Date(string="Date")
    convocation_days = fields.Integer(string="Deadline (Days)")
    convocation_date = fields.Date(string="Date")
    newspaper_publication_ids = fields.One2many('newspaper.publication', 'requisition_id', string="Newspaper publication")
    # membre_ids = fields.One2many('tender.membres', 'requisition_id', string="Membres")
    withdrawal_ids = fields.One2many('tender.withdrawals', 'requisition_id', string="Withdrawals")
    rectification_ids = fields.One2many('tender.rectification', 'requisition_id', string="Rectification & Reports")
    is_tender_cancel = fields.Boolean(String="Cancellation of the call for Tenders")
    cancel_reason = fields.Many2one('tender.cancellation', string="Reason For Cancellation")
    cancel_attach_id = fields.Binary(type="binary", string="PV Cancel")
    cancel_filename = fields.Char(string="Cancel Filename")
    is_tender_unsuccess = fields.Boolean(String="Unsuccessful Call For Tenders")
    unsuccess_reason = fields.Many2one('tender.cancellation', string="Reason For Unsuccessful")
    unsuccess_attach_id = fields.Binary(type="binary", string="PV Unsuccessful")
    unsuccess_filename = fields.Char(string="Unsuccess Filename")
    bidder_offer_ids = fields.Many2many('bidder.offers', 'relational_requisition_bidder_offrs', 'bidder_id', 'requisition_id', string="Bidder offers")
    session_ids = fields.One2many('tender.sessions', 'requisition_id', string="Sessions")
    session_attachment_id = fields.One2many('session.attachment', 'requisition_id', string="Session Attachments")
    tender_decision_ids = fields.One2many('tender.decision', 'requisition_id', string="Decision Final")
    tender_decision_cancel_ids = fields.One2many('tender.decision.cancel', 'requisition_id', string="Soumissionnaires écartés")
    decision_compliments_ids = fields.One2many('tender.decision.compliments', 'requisition_id', string="Compliments")
    decision_pv_attach_id = fields.Binary(type="binary", string="PV Final")
    decision_pv_filename = fields.Char(string="Decision PV Filename")
    result_attach_id = fields.Binary(type="binary", string="Résultat")
    result_filename = fields.Char(string="Résultat Filename")
    state_appel_offers_order = fields.Selection(PURCHASE_REQUISITION_STATES, compute='_set_appel_offers_state')
    state_consulation_order = fields.Selection(PURCHASE_REQUISITION_STATES, compute='_set_consulation_state')
    bidder_partner_ids = fields.Many2many('res.partner', 'rel_pr_bidder_partner', 'requisition_id', 'partner_id', string='Partners')
    # article_ids = fields.Many2many('product.product', 'rel_pr_article', 'requisition_id', 'article_id', string='Partners')
    article_ids = fields.Many2many('product.product', compute='_compute_article_domain', string='Articles')
    # jalon_ids = fields.Many2many('purchase.requisition.jalon', compute='_compute_jalon_domain', string='Jalons')
    decision_bidder_partner_ids = fields.Many2many('res.partner', compute='_compute_decision_bidder_partners_lots', string='Decision Bidder Partners', store=True)
    decision_bidder_lot_ids = fields.Many2many('lot.details', compute='_compute_decision_bidder_partners_lots', string='Decision Bidder Lots', store=True)
    withdrawal_partner_ids = fields.Many2many('res.partner', 'rel_withdrawal_partner_pr', 'withdrawal_partner_id', 'requisition_id', string='Withdrawal Partners')

    # Consulation
    consultation_name = fields.Char(string='Object de la consultation')
    attachment_consultation_charges = fields.Binary(type="binary", string="Cahier des charges")
    attachment_consultation_charges_filename = fields.Char(string='Cahier des charges Filename')
    consultation_admin_charactristics = fields.Many2many('admin.characteristic', 'rel_admin_characteristic_consultation', 'admin_characteristic_consultation', 'requisition_id', string="Caractéristiques")
    is_consultation_comm_valid = fields.Boolean(string='Prévoir une commission de validation')
    consultation_name = fields.Char(string='Object de la consultation')
    consultation_tender_commission_ids = fields.One2many('tender.commission.consultation', 'requisition_id', string="commission de validation")
    consultation_concurrents_type = fields.Selection([('concurrent_multiple', 'Concurrents multiple'), ('concurrent_unique', 'Concurrent unique')], string="Type de Concurrent", default='concurrent_multiple')
    attachment_concurrent_unique = fields.Binary(type="binary", string="Concurrent unique")
    attachment_concurrent_unique_filename = fields.Char(string='Concurrent unique Filename')
    concurrent_details_ids = fields.Many2many('concurrent.details', 'rel_concurrent_requisition', 'concurrent_id', 'requisition_id', string="Concurrents")
    attachment_pv_de_comm_signe = fields.Binary(type="binary", string="PV de la commission signé")
    attachment_pv_de_comm_signe_filename = fields.Char(string='PV de la commission signé Filename')
    attachment_dec_de_la_comm = fields.Binary(type="binary", string="Décision de la commission d'examen")
    attachment_dec_de_la_comm_filename = fields.Char(string="Décision de la commission d'examen Filename")

    #Override
    state = fields.Selection(PURCHASE_REQUISITION_STATES,
                              'Status', tracking=True, required=True,
                              copy=False, default='draft')
    state_blanket_order = fields.Selection(PURCHASE_REQUISITION_STATES, compute='_set_state')

    nbr = fields.Integer('NBR')
    unit = fields.Selection([('day', 'Jour'), ('week', 'Semaine'), ('month', 'Mois'), ('year', 'Annee')], string="UNIT")
    limite = fields.Integer(string='Limite')
    tacite_reconduction = fields.Boolean(string='Tacite Reconduction')
    requisition_terms_ids = fields.One2many('requisition.terms', 'purchase_requisition_id', string="Requisition Terms")
    is_pending_state = fields.Boolean(string='Is Pending State', compute="_compute_is_pending_state", store=True)

    def term_create(self, sequence):
        self.env['requisition.terms'].create({    
            'term': sequence,
            'etat': 'pending',
            'purchase_requisition_id': self.id,
        })

    def action_requisition_terms_limite(self):
        if not self.requisition_terms_ids:
            for sequence in range(1, self.limite + 1):
                self.term_create(sequence)
            self.requisition_terms_ids.filtered(lambda l: l.term == 1).etat = 'active'

        if len(self.requisition_terms_ids) < self.limite:
            for sequence in range(len(self.requisition_terms_ids) + 1, self.limite + 1):
                self.term_create(sequence)
        if len(self.requisition_terms_ids) > self.limite:
            if self.requisition_terms_ids.filtered(lambda l: l.term > self.limite and l.etat != 'pending'):
                raise ValidationError(_("Your limit is cover closed or active state too, which are not removed, please update your limit !!!"))
            self.requisition_terms_ids.filtered(lambda l: l.term > self.limite and l.etat == 'pending').unlink()

    @api.depends('requisition_terms_ids')
    def _compute_is_pending_state(self):
        for record in self:
            record.is_pending_state = False
            pending_state = record.requisition_terms_ids.filtered(lambda l: l.etat == "pending")
            if pending_state:
                record.is_pending_state = True

    def action_renouveler_terms(self):
        active_term = self.requisition_terms_ids.filtered(lambda l: l.etat == "active" and l.date_fin != False and l.date_fin <= date.today())
        if active_term:
            active_term.etat = 'closed'
            next_active_term = self.requisition_terms_ids.filtered(lambda l: l.term == active_term.term + 1)
            if next_active_term:
                next_active_term.etat = 'active'
        
    def cron_action_renouveler_terms(self):
        for rec in self.env['purchase.requisition'].search([('contract_type', '=', 'Contrat / Convention')]):
            rec.action_renouveler_terms()

    @api.onchange('withdrawal_ids')
    def onchange_withdrawal_partners(self):
        if self.withdrawal_ids:
            partners = []
            for partner in self.withdrawal_ids.mapped('concurrent'):
                partners.append(partner.id)
            self.withdrawal_partner_ids = partners

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(['name', 'tender_number'])
        return [(purchase_request.id, '%s%s' % (purchase_request.name, purchase_request.tender_number and (' (%s)' % purchase_request.tender_number if purchase_request.contract_type not in ['Consultation / BC', 'Contrat / Convention'] else '')))
                for purchase_request in self]

    @api.depends('tender_decision_ids')
    def _compute_decision_bidder_partners_lots(self):
        for record in self:
            partners = lots = []
            if record.tender_decision_ids:
                partners = record.tender_decision_ids.filtered(lambda a: a.decision == 'Attributaire').mapped('bidder_id')
                lots = record.tender_decision_ids.filtered(lambda a: a.decision == 'Attributaire').mapped('lot_id')
                record.decision_bidder_partner_ids = partners if partners else []
                record.decision_bidder_lot_ids = lots if lots else []

    @api.onchange('tender_decision_ids')
    def onchange_decision_ids(self):
        if self.tender_decision_ids:
            for lot in self.tender_decision_ids.mapped('lot_id'):
                if len(self.tender_decision_ids.filtered(lambda a: a.lot_id.id == lot.id and a.decision == 'Attributaire')) > 1:
                    raise UserError(_('You can only set sigle Attributaire as decision.'))

    @api.onchange('lot_details_ids')
    def onchange_lot_estimate_price(self):
        if self.lot_details_ids:
            if max(self.lot_details_ids.mapped('estimated_price')) <= 500000.00:
                self.submission_days = 21
            else:
                self.submission_days = 40

    @api.onchange('date_publication', 'submission_days')
    def onchange_submission_days(self):
        if self.date_publication:
            if self.submission_days:
                # if not self.prospectus_days > 0:
                self.prospectus_days = self.submission_days - 1
                # if not self.sample_deposit_days > 0:
                self.sample_deposit_days = self.submission_days -1

            actual_days = self.env['resource.calendar']._check_holiday_status(self.submission_days, self.date_publication)
            self.submission_days = actual_days
            self.submission_date = self.date_publication + timedelta(days=self.submission_days)

    @api.onchange('date_publication', 'site_visit_days', 'submission_days')
    def onchange_site_visit_days(self):
        if self.date_publication:
            if self.site_visit_days:
                actual_days = self.env['resource.calendar']._check_holiday_status(self.site_visit_days, self.date_publication)
                self.site_visit_days = actual_days
                self.site_visit_date = self.date_publication + timedelta(days=self.site_visit_days)
                if not (self.site_visit_days > (self.submission_days/3)) or not (self.site_visit_days <= (2 * self.submission_days)/3):
                    title = _("Warning for submission date")
                    message = _("Délai Visite des lieux should be >= Délai soumission / 3 and \
                             Délai Visite des lieux should be <= (2 * Délai soumission) / 3")
                    return {'warning': {'title': title, 'message': message}}
                    # raise UserError(_('Délai Visite des lieux should be >= Délai soumission / 3 and \
                    #          Délai Visite des lieux should be <= (2 * Délai soumission) / 3'))
            
    @api.onchange('date_publication', 'sample_deposit_days')
    def onchange_sample_deposit_days(self):
        if self.date_publication:
            if self.sample_deposit_days:
                actual_days = self.env['resource.calendar']._check_holiday_status(self.sample_deposit_days, self.date_publication)
                self.sample_deposit_days = actual_days
                self.sample_deposit_date = self.date_publication + timedelta(days=self.sample_deposit_days)
                if self.sample_deposit_date and self.submission_date:
                    if not self.sample_deposit_date == (self.submission_date - timedelta(days=1)):
                        title = _("Warning for submission date")
                        message = _("Please set submission date according to sample deposite date")
                        return {'warning': {'title': title, 'message': message}}
                        # raise UserError(_('Please set submission date according to sample deposite date'))
            
    @api.onchange('date_publication', 'prospectus_days')
    def onchange_prospectus_days(self):
        if self.date_publication:
            if self.prospectus_days:
                actual_days = self.env['resource.calendar']._check_holiday_status(self.prospectus_days, self.date_publication)
                self.prospectus_days = actual_days
                self.prospectus_date = self.date_publication + timedelta(days=self.prospectus_days)
                if self.prospectus_date and self.submission_date:
                    if not self.prospectus_date == (self.submission_date - timedelta(days=1)):
                        title = _("Warning for submission date")
                        message = _("Please set submission date according to prospectus deposit date")
                        return {'warning': {'title': title, 'message': message}}
                        # raise UserError(_('Please set submission date according to prospectus deposit date'))

    @api.onchange('date_publication', 'convocation_days')
    def onchange_convocation_days(self):
        if self.date_publication:
            if self.convocation_days:
                actual_days = self.env['resource.calendar']._check_holiday_status(self.convocation_days, self.date_publication)
                self.convocation_days = actual_days
                self.convocation_date = self.date_publication + timedelta(days=self.convocation_days)
                if self.convocation_date and self.submission_date:
                    if not self.convocation_date < (self.submission_date - timedelta(days=7)):
                        title = _("Warning for submission date")
                        message = _("Please set submission date according to convocation date")
                        return {'warning': {'title': title, 'message': message}}

    @api.onchange('bidder_offer_ids')
    def onchange_bidder_partners(self):
        if self.bidder_offer_ids:
            partners = []
            for partner in self.bidder_offer_ids.mapped('partner_id'):
                partners.append(partner.id)
            self.bidder_partner_ids = partners if partners else []

    # @api.onchange('line_ids')
    # def onchange_line_ids(self):
    #     if self.line_ids:
    #         article_ids = []
    #         for article in self.line_ids.mapped('product_id'):
    #             article_ids.append(article.id)
    #         self.article_ids = article_ids if article_ids else []

    @api.depends('line_ids', 'lot_details_ids')
    def _compute_article_domain(self):
        for record in self:
            article_ids = []
            for article in record.line_ids.mapped('product_id'):
                article_ids.append(article.id)
            lis = record.lot_details_ids.mapped('product_ids').ids
            if lis:
                article_ids = [item for item in article_ids if item not in lis]
            record.article_ids = article_ids if article_ids else []

    # @api.depends('planification_ids')
    # def _compute_jalon_domain(self):
    #     for record in self:
    #         jalon_ids = []
    #         lis = record.planification_ids.mapped('jalon_id').ids
    #         jalons = self.env['purchase.requisition.jalon'].search([('id', 'not in', lis)])
    #         record.jalon_ids = jalons.ids if jalons else []

    def button_dummy(self):
        return True
            
    @api.depends('state')
    def _set_appel_offers_state(self):
        for requisition in self:
            requisition.state_appel_offers_order = requisition.state

    @api.depends('state')
    def _set_consulation_state(self):
        for requisition in self:
            requisition.state_consulation_order = requisition.state

    @api.onchange('is_tender_cancel')
    def onchange_tender_cancel(self):
        if not self.is_tender_cancel:
            self.cancel_reason = False

    @api.onchange('is_tender_unsuccess')
    def onchange_tender_unsuccess(self):
        if not self.is_tender_unsuccess:
            self.unsuccess_reason = False

    @api.onchange('session_ids')
    def onchange_sessions(self):
        if self.session_ids:
            if len([i for i, val in enumerate(self.session_ids.mapped('is_final')) if val]) > 1:
                raise UserError(_('You can consider only one Sessions as final.'))
            if len(self.session_ids.filtered(lambda a: a.state != 'Cloturé')) > 1:
                raise ValidationError(_("You can any add new Sessions if all sessions in 'Cloturé'."))
            if len(self.session_ids.filtered(lambda a: a.is_final)) > 1:
                raise ValidationError(_("You can not add new line if single line is marked with Final."))

            for line in self.session_ids.mapped('bidder_ids').filtered(lambda a: a.decision == 'écarté'):
                if len(self.session_ids.mapped('bidder_ids').filtered(lambda a: a.bidder_id.id == line.bidder_id.id and a.lot_id.id == line.lot_id.id and (a.decision == 'écarté'))) > 1:
                    raise UserError(_("A couple of (“soumissionnaire”, ”Lot”) with state ”écarté” is exist."))

            for bid_line in self.session_ids.filtered(lambda a: a.is_final).mapped('bidder_ids').filtered(lambda a: a.decision == 'retenu'):
                if len(self.session_ids.filtered(lambda a: a.is_final).mapped('bidder_ids').filtered(lambda a: a.decision == 'retenu' and a.lot_id.id == bid_line.lot_id.id)) > 1:
                    raise UserError(_("You can not assign same lot twice as retenu."))

    def create_decision_final_lines(self):
        ### Decision Lines
        TenderDecision = self.env['tender.decision']
        self.tender_decision_ids.unlink()
        last_session_id = sorted(self.session_ids, key=lambda a: a.id, reverse=True)
        if last_session_id:
            for bidder_line in last_session_id[0].mapped('bidder_ids'):
                if bidder_line.decision == 'retenu':
                    if not self.tender_decision_ids.filtered(lambda a: a.bidder_id.id == bidder_line.bidder_id.id and a.lot_id.id == bidder_line.lot_id.id):
                        TenderDecision.create({
                            'requisition_id': bidder_line.session_id.requisition_id.id,
                            'ranking': bidder_line.ranking,
                            'bidder_id': bidder_line.bidder_id.id,
                            'lot_id': bidder_line.lot_id.id or False,
                            'decision': 'Attributaire',
                            })
        ### Ecarte Lines
        TenderDecisionCancel = self.env['tender.decision.cancel']
        self.tender_decision_cancel_ids.unlink()
        for bidder_line in self.session_ids.mapped('bidder_ids'):
            if bidder_line.decision == 'écarté':
                TenderDecisionCancel.create({
                        'requisition_id': bidder_line.session_id.requisition_id.id,
                        'bidder_id': bidder_line.bidder_id.id,
                        'lot_id': bidder_line.lot_id.id or False,
                        })

        # for line in self.session_ids.filtered(lambda a: a.state == 'en_cours' and a.bidder_ids):
        #     self.tender_decision_ids.unlink()
        #     self.tender_decision_cancel_ids.unlink()
        #     for bidder_line in line.bidder_ids:
        #         if bidder_line.decision == 'retenu' and line.final:
        #             decision_final.append((0, 0, {
        #                 'ranking': bidder_line.ranking,
        #                 'bidder_id': bidder_line.bidder_id.id,
        #                 'lot_id': bidder_line.lot_id.id or False,
        #                 'decison': 'Attributaire'}))
        #         if bidder_line.decision == 'écarté':
        #             decision_cancel.append((0, 0, {
        #                 'bidder_id': bidder_line.bidder_id.id,
        #                 'lot_id': bidder_line.lot_id.id or False}))
        # self.tender_decision_ids = decision_final
        # self.tender_decision_cancel_ids = decision_cancel
        return True

    def create_decision_complements_lines(self):
        session_ids = sorted(self.session_ids, key=lambda a: a.id, reverse=True)
        if session_ids:
            complement_line_ids = []
            self.decision_compliments_ids.filtered(lambda a: a.bidder_line_id).unlink()
            for lot in session_ids[0].bidder_ids.filtered(lambda a: a.decision == 'retenu').mapped('lot_id'):
                data = sorted(session_ids[0].bidder_ids.filtered(lambda a: a.decision == 'retenu').filtered(lambda a: a.lot_id.id == lot.id), key=lambda a: a.note, reverse=True)
                if data:
                    complement_line_ids.append((0, 0, {
                                                'name': data[0].bidder_id.name + ' - ' + data[0].lot_id.display_name,
                                                'bidder_line_id': data[0].id,
                                            }))
            self.decision_compliments_ids = complement_line_ids
        return True

    def action_publication(self):
        return self.write({'tender_number': self.env['ir.sequence'].next_by_code('tender.number'), 'state': 'publication'})

    def action_evaluation(self):
        return self.write({'state': 'evaluation'})

    def action_decision(self):
        if not self.session_ids.filtered(lambda a: a.is_final):
            raise UserError(_("No final sessions found to process decison."))
        return self.write({'state': 'decision'})

    def move_to_unsuccessful(self):
        return self.write({'state': 'unsuccessful'})

    def move_to_cancel(self):
        return self.write({'state': 'cancel'})

    def action_done(self):
        return self.write({'state': 'done'})

    def print_consultant_report(self):
        return True

    @api.model
    def create(self, vals):
        res = super(PurchaseRequisition, self).create(vals)
        if vals.get('session_ids'):
            res.create_decision_final_lines()
            res.create_decision_complements_lines()
        if vals.get('is_tender_unsuccess'):
            res.move_to_unsuccessful()
        if vals.get('is_tender_cancel'):
            res.move_to_cancel()
        if vals.get('limite'):
            res.action_requisition_terms_limite()
        return res

    def write(self, vals):
        res = super(PurchaseRequisition, self).write(vals)
        if vals.get('limite') or vals.get('limite') == 0:
            self.action_requisition_terms_limite()
        if vals.get('session_ids'):
            self.create_decision_final_lines()
            self.create_decision_complements_lines()
            for bid_line in self.session_ids.filtered(lambda a: a.is_final).mapped('bidder_ids').filtered(lambda a: a.decision == 'retenu'):
                if len(self.session_ids.filtered(lambda a: a.is_final).mapped('bidder_ids').filtered(lambda a: a.decision == 'retenu' and a.lot_id.id == bid_line.lot_id.id)) > 1:
                    raise UserError(_("You can not assign same lot twice as retenu."))
        if vals.get('is_tender_unsuccess'):
            self.move_to_unsuccessful()
        if vals.get('is_tender_cancel'):
            self.move_to_cancel()
        if vals.get('lot_details_ids'):
            product_ids = []
            for line in self.lot_details_ids:
                for product in line.product_ids:
                    product_ids.append(product.id)
            if product_ids and len(product_ids) != len(self.lot_details_ids.mapped('product_ids')):
                raise UserError(_('You cannot assign same article with different lots.'))
        if vals.get('planification_ids'):
            for line in self.planification_ids:
                if len(self.planification_ids.filtered(lambda a: a.lot_id.id == line.lot_id.id and a.jalon_id.id == line.jalon_id.id)) > 1:
                    raise UserError(_('You cannot assign same lot with same jalon twice in planification.'))
        if vals.get('bidder_offer_ids'):
            partner_ids = []
            for line in self.bidder_offer_ids:
                partner_ids.append(line.partner_id.id)
            if partner_ids and len(partner_ids) != len(self.bidder_offer_ids.mapped('partner_id')):
                raise UserError(_('You cannot assign same Bidder with different offers.'))
        return res

    def create_purchase_quotation(self):
        purchase_order = self.env['purchase.order']
        purchase_order_lst = []
        purchase_order_ids = self.env['purchase.order'].search([('requisition_id', '=', self.id), ('state', 'in', ['draft', 'sent', 'to_approve'])])
        purchase_order_ids.button_cancel()
        purchase_order_ids.unlink()
        self.create_decision_final_lines()
        for each in self.tender_decision_ids:
            product_lst = []
            lot_line_ids = self.lot_details_ids.filtered(lambda l: l.id == each.lot_id.id)
            for lot_line in lot_line_ids:
                for rec in lot_line.product_ids:
                    product_line = self.line_ids.filtered(lambda l: l.product_id.id == rec.id)
                    product_lst.append((0, 0, {'product_id': rec.id,
                                                'name': rec.name,
                                                'product_qty': product_line[0].product_qty if product_line else 1.0,
                                                'product_uom': rec.uom_id.id,
                                                'price_unit': product_line[0].price_unit if product_line else 0.00,
                                                'date_planned': product_line[0].schedule_date if product_line and product_line[0].schedule_date else fields.Date.today(),
                                                'purchase_request_line_ids': [(6, 0, product_line.purchase_request_line_ids.ids)]}))
            purchase_id = purchase_order.create({'partner_id': each.bidder_id.id,
                                                  'partner_ref': (self.tender_number or '') + '-' + str(each.lot_id.n_lot) + ('-' + each.lot_id.object_name if each.lot_id.object_name else ''),
                                                  'requisition_id': self.id,
                                                  'tender_decision_line_id': each.id,
                                                  'order_line': product_lst})
            purchase_order_lst.append(purchase_id.id)
        
        action = self.env.ref('purchase_requisition.action_purchase_requisition_list').read()[0]
        action['domain'] = [('requisition_id', '=', self.id)]
        action['context'] = {'default_requisition_id': self.id, 'default_user_id': False, 'default_partner_ref': self.tender_number, 'search_default_group_partner_ref': 1}
        return action

    def create_purchase_quotation_bc(self):
        if not self.concurrent_details_ids:
            raise UserError(_('You cannot process before adding commission de validation.'))
        purchase_order = self.env['purchase.order']
        purchase_order_ids = purchase_order.search([('requisition_id', '=', self.id), ('state', 'in', ['draft', 'sent', 'to_approve'])])
        purchase_order_ids.button_cancel()
        purchase_order_ids.unlink()

        purchase_order_lst = []
        for concurrent in self.concurrent_details_ids:
            purchase_lines = []
            for line in self.line_ids:
                purchase_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty': line.product_qty or 1.0,
                    'product_uom': line.product_uom_id.id,
                    'price_unit': line.price_unit or 0.00,
                    # 'price_unit': 0.00,
                    # 'estimated_prc': line.price_unit or 0.00,
                    'date_planned': line.schedule_date or fields.Date.today(),
                    'is_bc_purchase_requisition': True,
                    'purchase_request_line_ids': [(6, 0, line.purchase_request_line_ids.ids)]}))
            purchase_id = purchase_order.create({
                'partner_id': concurrent.name.id,
                'partner_ref': ('(' + concurrent.name.name + ')'),
                'requisition_id': self.id,
                'is_bc_purchase_requisition': True,
                'order_line': purchase_lines})
            purchase_order_lst.append(purchase_id.id)
        
        action = self.env.ref('wt_purchase_request_extend.action_purchase_requisition_list_bc').read()[0]
        action['domain'] = [('requisition_id', '=', self.id)]
        self.write({'state': 'consultation'})
        return action

    def create_purchase_quotation_rg(self):
        if not self.vendor_id:
            raise UserError(_('le champ Fournisseur est vide !'))
        purchase_order = self.env['purchase.order']
        purchase_order_ids = purchase_order.search([('requisition_id', '=', self.id), ('state', 'in', ['draft', 'sent', 'to_approve'])])
        purchase_order_ids.button_cancel()
        purchase_order_ids.unlink()

        purchase_order_lst = []
        purchase_lines = []
        for line in self.line_ids:
            purchase_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_qty': line.product_qty or 1.0,
                'product_uom': line.product_uom_id.id,
                'price_unit': line.price_unit or 0.00,
                # 'price_unit': 0.00,
                # 'estimated_prc': line.price_unit or 0.00,
                'date_planned': line.schedule_date or fields.Date.today(),
                'is_bc_purchase_requisition': True,
                'purchase_request_line_ids': [(6, 0, line.purchase_request_line_ids.ids)]}))
        purchase_id = purchase_order.create({
            'partner_id': self.vendor_id.id,
            'partner_ref': ('(' + self.vendor_id.name + ')'),
            'requisition_id': self.id,
            'is_bc_purchase_requisition': True,
            'order_line': purchase_lines})
        purchase_order_lst.append(purchase_id.id)
    
        action = self.env.ref('wt_purchase_request_extend.action_purchase_requisition_regie').read()[0]
        action['domain'] = [('requisition_id', '=', self.id)]
        self.write({'state_blanket_order': 'ongoing'})
        return action

    def generate_purchase_agreement_no(self):
        # Set the sequence number regarding the requisition type
        if self.name == 'New':
            if self.contract_type == 'Appel d’offres':
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
            elif self.contract_type == 'Contrat / Convention':
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.convention')
            elif self.contract_type == 'Consultation / BC':
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.consultation')
            elif self.contract_type == 'Régie':
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.regie')

    def action_in_progress(self):
        self.ensure_one()
        if not all(obj.line_ids for obj in self):
            raise UserError(_("You cannot confirm agreement '%s' because there is no product line.") % self.name)
        if self.type_id.quantity_copy == 'none' and self.vendor_id:
            for requisition_line in self.line_ids:
                if requisition_line.price_unit <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without price.'))
                if requisition_line.product_qty <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without quantity.'))
                requisition_line.create_supplier_info()
            self.write({'state': 'ongoing'})
        elif self._context.get('is_appel_offers'):
            self.write({'state': 'elaboration'})
        elif self._context.get('is_consultation'):
            self.write({'state': 'preparation'})
        else:
            self.write({'state': 'in_progress'})
        # self.onchange_line_ids()
        self.generate_purchase_agreement_no()

    def action_affecter_besoins(self):
        self.ensure_one()
        if not all(obj.besoins_ids for obj in self):
            raise UserError(_("You cannot Affecter besoins because there is no purchase request line."))
        
        for line in self.besoins_ids:
            requisition_line_records = self.line_ids.filtered(lambda x:x.product_id.id == line.product_id.id)
            if requisition_line_records:
                requisition_line_records.product_qty += line.product_qty
                requisition_line_records.purchase_request_line_ids = [(4, line.id)]
            else:
                self.line_ids.create((0,0,{'requisition_id': self.id,
                                            'product_id': line.product_id.id,
                                            'product_uom_id': line.product_uom_id.id,
                                            'product_qty': line.product_qty,
                                            'schedule_date': line.date_required,
                                            'price_unit': line.estimated_cost,
                                            'purchase_request_line_ids': [(4, line.id)]}))
            line.write({'etat': 'Affecté'})
        # self.onchange_line_ids()
        self.generate_purchase_agreement_no()
        if self.contract_type == 'Appel d’offres':
            self.write({'state': 'affecte'})
        elif self.contract_type == 'Consultation / BC':
            self.write({'state': 'preparation'})

    def action_annuler_affectation(self):
        self.ensure_one()
        self.besoins_ids.write({'etat': 'qualifie'})
        self.line_ids.unlink()
        self.write({'state': 'draft'})

    
class TenderCommission(models.Model):
    _name = 'tender.commission'
    _description = "Tender Commission"

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    partner_id = fields.Many2one('res.partner', string="Partner")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    partner_type = fields.Selection([('Président', 'Président'), ('Maitre d’ouvrage', 'Maitre d’ouvrage'), ('Service utilisateur', 'Service utilisateur'), ('Service achat', 'Service achat'), ('Service comptable', 'Service comptable'), ('Controleur d’état', 'Controleur d’état'), ('Bureau d’étude', 'Bureau d’étude')], string="Type Membre", default='Président', required=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Service')

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        if self.partner_type:
            if self.partner_type in ['Controleur d’état', 'Bureau d’étude']:
                self.employee_id = False
            elif self.partner_type in ['Président', 'Maitre d’ouvrage', 'Service utilisateur', 'Service achat', 'Service comptable']:
                self.partner_id = False


class TenderCommissionConsultation(models.Model):
    _name = 'tender.commission.consultation'
    _description = "Tender Commission Consultation"

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    partner_id = fields.Many2one('res.partner', string="Partner")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    partner_type = fields.Selection([('Président', 'Président'), ('Maitre d’ouvrage', 'Maitre d’ouvrage'), ('Service utilisateur', 'Service utilisateur'), ('Service achat', 'Service achat'), ('Service comptable', 'Service comptable'), ('Controleur d’état', 'Controleur d’état'), ('Bureau d’étude', 'Bureau d’étude')], string="Type Membre", default='Président', required=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Service')

    @api.onchange('partner_type')
    def onchange_partner_type(self):
        if self.partner_type:
            if self.partner_type in ['Controleur d’état', 'Bureau d’étude']:
                self.employee_id = False
            elif self.partner_type in ['Président', 'Maitre d’ouvrage', 'Service utilisateur', 'Service achat', 'Service comptable']:
                self.partner_id = False


class AdminCharacteristic(models.Model):
    _name = 'admin.characteristic'
    _description = "Admin Characteristic"

    name = fields.Char(string='Name', required=True)


class ConcurrentDetails(models.Model):
    _name = 'concurrent.details'
    _description = "Concurrent Details"

    name = fields.Many2one('res.partner', string="Concurrents", required=True)
    attachment_consultation_letter = fields.Binary(type="binary", string="Lettre de consultation")
    attachment_consultation_letter_filename = fields.Char(string='Lettre de consultation Filename')
    
    @api.model
    def default_get(self, default_fields):
        if 'concurrent_details_ids' in self._context:
            if self._context.get('consultation_concurrents_type') == 'concurrent_unique':
                if self._context.get('concurrent_details_ids') and self._context.get('concurrent_details_ids')[0] and len(self._context.get('concurrent_details_ids')[0][2]) > 1:
                    raise ValidationError(_("You set concurrent type as 'Concurrent Unique' \nYou can not create more than 1 Concurrent(s)."))
                elif self._context.get('concurrent_details_ids') and self._context.get('concurrent_details_ids')[0] and len(self._context.get('concurrent_details_ids')[0][2]) == 0:
                    if len(self._context.get('concurrent_details_ids')) > 1:
                        raise ValidationError(_("You set concurrent type as 'Concurrent Unique' \nYou can not create more than 1 Concurrent(s)."))
        return super(ConcurrentDetails, self).default_get(default_fields)


class LotDetails(models.Model):
    _name = 'lot.details'
    _description = "Lot Details"
    _rec_name = 'n_lot'

    n_lot = fields.Integer(string="N lot", copy=False)
    object_name = fields.Char(string='Object', required=True)
    estimated_price = fields.Float(string="Estimated Price")
    caution = fields.Float(string="Caution")
    retenu = fields.Float(string="Holdback")
    evaluation_id = fields.Many2one('lot.evaluation', string="Evaluation Method", required=True)
    product_ids = fields.Many2many('product.product', 'rel_product_lot_detail', 'lot_id', 'product_id', string="Article")
    
    @api.onchange('product_ids')
    def onchange_product_ids(self):
        active_id_pr_req_id = self._context.get('active_id_pr_req_id', False)
        for rec in self:
            if active_id_pr_req_id:
                requisition_id = self.env['purchase.requisition'].browse(active_id_pr_req_id)
                amt = 0.0
                for line in requisition_id.line_ids.filtered(lambda a: a.product_id.id in  rec.product_ids.ids):
                    amt += line.product_qty * line.price_unit
                rec.estimated_price = amt
                rec.caution = (amt * 2/100)
                rec.retenu = (amt * 7/100)

    @api.model
    def default_get(self, default_fields):
        sequence = 0
        if 'lot_details_ids' in self._context:
            if self._context.get('lot_details_ids') and self._context.get('lot_details_ids')[0] and len(self._context.get('lot_details_ids')[0][2]) > 0:
                if len(self._context.get('lot_details_ids')) > 1:
                    sequence = len(self._context.get('lot_details_ids')[0][2]) + len(self._context.get('lot_details_ids'))
                else:
                    sequence = len(self._context.get('lot_details_ids')[0][2]) + 1
            elif self._context.get('lot_details_ids') and self._context.get('lot_details_ids')[0] and len(self._context.get('lot_details_ids')[0][2]) == 0:
                if len(self._context.get('lot_details_ids')) > 1:
                    sequence = len(self._context.get('lot_details_ids')[0][2]) + len(self._context.get('lot_details_ids'))
                else:
                    sequence = len(self._context.get('lot_details_ids')[0][2]) + 1

            if self._context.get('lot_number', 0) and sequence > self._context.get('lot_number'):
                if self._context.get('lot_type') == 'lot_unique':
                    raise ValidationError(_("You set lot type as 'Lot Unique' \nYou can not create more than %s lot(s).") % self._context.get('lot_number'))
                elif self._context.get('lot_type') == 'lot_multiple':
                    raise ValidationError(_("You set lot type as 'Lot Multiple' \nYou can not create more than %s lot(s).") % self._context.get('lot_number'))
        result = super(LotDetails, self).default_get(default_fields)
        if sequence > 0:
            result.update({'n_lot': sequence})
        return result

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(['n_lot', 'object_name'])
        return [(lot.id, '%s-%s' % (lot.n_lot, lot.object_name))
                for lot in self]


class LotEvaluation(models.Model):
    _name = 'lot.evaluation'
    _description = "Lot Evaluation"

    name = fields.Char(String="Name", required=True)
    description = fields.Text(string="Description")


class PurchaseRequisitionPlanification(models.Model):
    _name = 'purchase.requisition.planification'
    _description = "Purcahse Requisition Planification"

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    lot_id = fields.Many2one('lot.details', string="Lot")
    jalon_id = fields.Many2one('purchase.requisition.jalon', string="Jalon", required=True)
    day = fields.Integer(string="Deadline (Days)")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    details = fields.Text(string="Details")

    @api.onchange('day', 'start_date')
    def onchange_start_date(self):
        if self.day and self.start_date:
            actual_days = self.env['resource.calendar']._check_holiday_status(self.day, self.start_date)
            self.day = actual_days
            self.end_date = self.start_date + timedelta(days=self.day)


class PurchaseRequisitionJalon(models.Model):
    _name = 'purchase.requisition.jalon'
    _description = "Purcahse Requisition Jalon"

    name = fields.Char(String="Name", required=True)
    description = fields.Text(string="Description")


class NewspaperPublication(models.Model):
    _name = 'newspaper.publication'
    _description = "Newspaper Publication"

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    journal_id = fields.Many2one('newspaper.publication.journal', string="Journal", required=True)
    notice_type = fields.Selection([('Arabe', 'Arabe'), ('français', 'français'), ('Digital', 'Digital')], string="Type Notice", default='Arabe', required=True)
    publication_date = fields.Date(string="Publication Date", required=True)
    reference_publication = fields.Char(string='Reference Publication')

    def print_report_avis(self):
        return True
    

class NewspaperPublicationJournal(models.Model):
    _name = 'newspaper.publication.journal'
    _description = "Newspaper Publication Journal"

    name = fields.Char(String="Name", required=True)


# class TenderMembres(models.Model):
#     _name = 'tender.membres'
#     _description = "Tender Membres"

#     requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
#     partner_id = fields.Many2one('res.partner', string="Membre", required=True)
#     partner_type = fields.Selection([('Président', 'Président'), ('Maitre d’ouvrage', 'Maitre d’ouvrage'), ('Service financier', 'Service financier'), ('Service achat', 'Service achat'), ('Controleur d’état', 'Controleur d’état')], string="Type Membre", default='Président')

class TenderWithdrawals(models.Model):
    _name = 'tender.withdrawals'
    _description = "Tender Withdrawals"

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    withdrawals_type = fields.Selection([('Papier', 'Papier'), ('Portail', 'Portail'), ('Site web', 'Site web')], string="Type Of Withdrawal", default='Papier', required=True)
    concurrent = fields.Many2one('res.partner', string="Concurrent")
    withdrawal_date = fields.Date(string="Withdrawal Date")
    submission_date = fields.Date(string="Submission Date")
    prospectus_date = fields.Date(string="Prospectus Date")
    visit_date = fields.Date(string="Visit Date")


class TenderRectification(models.Model):
    _name = 'tender.rectification'
    _description = "Tender Rectification"

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    description = fields.Text(string="Description", required=True)
    deadline_days = fields.Integer(string="Postponement Deadline")
    original_deadline_days = fields.Integer(string="Original Postponement Deadline")
    original_updated_days = fields.Integer(string="Original Updated Deadline Days")
    corrective_notice = fields.Binary(type="binary",string="Corrective Notice")
    filename = fields.Char(string="Filename")
    date_should_be = fields.Date(string="Date Should Be")

    @api.onchange('date')
    def onchange_deadline_date_days(self):
        if self.date:
            deadline_days = 0
            submission_date = self._context.get('submission_date') or False
            if not submission_date:
                submission_date = self.requisition_id.submission_date
            else:
                submission_date = fields.Date.from_string(submission_date)
            if submission_date:
                deadline_days = (submission_date - self.date).days
            if deadline_days > 0 and deadline_days < 10:
                self.deadline_days = 10 - deadline_days
                self.original_deadline_days = 10 - deadline_days
                result = {}
                warning = {}
                title = _("Warning for submission date")
                message = _("Date submission would be greater from rectification date with %s days") % self.deadline_days
                warning['title'] = title
                warning['message'] = message
                result = {'warning': warning}
                return result
            # self.date_should_be = self.date + timedelta(days=self.deadline_days)

    @api.onchange('deadline_days')
    def onchange_deadline_days(self):
        if self.deadline_days:
            if self.deadline_days < self.original_deadline_days:
                raise UserError(_("You can not set less days then required deadline days"))

    def print_report_avis_rectification(self):
        return True

    def unlink(self):
        self.requisition_id.write({
            'submission_days': self.requisition_id.submission_days - self.original_updated_days,
            'site_visit_days': self.requisition_id.site_visit_days - self.original_updated_days,
            'convocation_days': self.requisition_id.convocation_days - self.original_updated_days,
            })
        self.requisition_id.onchange_submission_days()
        self.requisition_id.onchange_site_visit_days()
        self.requisition_id.onchange_convocation_days()
        return super(TenderRectification, self).unlink()


class TenderCancellation(models.Model):
    _name = 'tender.cancellation'
    _description = "Tender Cancellation"

    name = fields.Char(String="Name", required=True)


class BidderOffers(models.Model):
    _name = 'bidder.offers'
    _description = "Bidder Offers"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', String="Bidder", required=True)
#     parts_ids = fields.Many2many('bidder.parts', 'relational_bidder_parts', 'bidder_id', 'part_id', string="Parts Supplied")
#     parts_ids = fields.Many2many('piece.provide.details',
#                                      'rel_piece_provide_bidder_parts',
#                                      'bidder_id',
#                                      'part_id',
#                                      string="pièces à fournir",copy=False)
#     parts_ids = fields.One2many('piece.provide.details','bidder_id',
#                                         string="Pièces à Fournir",copy=False)

    parts_ids = fields.One2many('piece.provide.details.copy','bidder_copy_id',
                                        string="Pièces à Fournir",copy=False)
    parts_ids_count = fields.Integer(compute='count_parts_ids_checked',
                                    string= 'Checked Pièces')
    
    def count_parts_ids_checked(self):
        for rec in self:
            rec.parts_ids_count = len(rec.parts_ids.filtered(lambda l: l.obligatoire_copy1 == True))
    
    @api.model
    def default_get(self,fields_list):
        res = super(BidderOffers, self).default_get(fields_list)
        ctx = self.env.context
        if ctx.get('piece_provide_ids', False):
            piece_ids = ctx['piece_provide_ids']
            if len(piece_ids) >=1 and len(piece_ids[0]) >=3:
                if len(piece_ids[0][2]) >= 1:
                    pieced_int_ids = piece_ids[0][2]
                    piece_recs = self.env['piece.provide.details'].browse(pieced_int_ids)
                    items = []
                    if piece_recs:
                        for piece_rec in piece_recs:
                            items.append([0, 0, {'pieces':piece_rec.pieces,
                                                 'obligatoire_copy':piece_rec.obligatoire_copy}])
                    res['parts_ids'] = items
        return res


class BidderParts(models.Model):
    _name = 'bidder.parts'
    _description = "Bidder Parts"

    name = fields.Char(String="Name", required=True)


class TenderSessions(models.Model):
    _name = 'tender.sessions'
    _description = 'Tender Sessions'
    _rec_name = 'session_type'

    def _default_bidder_lines(self):
        active_id = self._context.get('requisition_id', [])
        requisition_id = self.env['purchase.requisition'].browse(active_id)
        bidder_lines = []
        session_id = sorted(requisition_id.session_ids.filtered(lambda a: a.state == 'Cloturé'), key=lambda x: x.id, reverse=True)
        if session_id:
            for line in session_id[0].bidder_ids.filtered(lambda l: l.decision == 'retenu'):
                bidder_lines.append((0, 0, {
                        'bidder_id': line.bidder_id.id,
                        'lot_id': line.lot_id.id,
                        'object_name': line.object_name,
                        'decision': line.decision,
                        'ecart': line.ecart,
                        'note': line.note,
                    }))
        return bidder_lines

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    session_type = fields.Many2one('session.type', string="Type session", required=True)
    date = fields.Datetime(string="Session Date")
    state = fields.Selection([('en_cours', 'En cours'), ('Cloturé', 'Cloturé')], string="State")
    is_public = fields.Boolean(String="Public ?")
    is_final = fields.Boolean(string="Final ?")
    is_notation = fields.Boolean(string="Notation ?")
    is_moins_disant = fields.Boolean(string="Moins disant ?")
    notation_value = fields.Float(string="Seuil d'élimination")
    bidder_ids = fields.One2many('bidders.session', 'session_id', string="Bidders", default=_default_bidder_lines)

    def update_ranking_classment(self):
        if self.is_notation:
            for bidder in self.bidder_ids.mapped('bidder_id'):
                sequence = 0
                for bidder_line in sorted(self.bidder_ids.filtered(lambda a: a.bidder_id.id == bidder.id), key=lambda x: x.note and x.lot_id.display_name, reverse=True):
                    sequence += 1
                    bidder_line.ranking = sequence
        elif self.is_moins_disant:
            for purchase_id in sorted(self.requisition_id.purchase_ids, key=lambda x: x.amount_total, reverse=False):
                sequence = 0
                for bidder_line in sorted(self.bidder_ids.filtered(lambda a: a.bidder_id.id == purchase_id.partner_id.id), key=lambda x: x.lot_id.display_name, reverse=False):
                    sequence += 1
                    bidder_line.ranking = sequence
        else:
            for bidder in self.bidder_ids.mapped('bidder_id'):
                sequence = 0
                for bidder_line in self.bidder_ids.filtered(lambda a: a.bidder_id.id == bidder.id):
                    sequence += 1
                    bidder_line.ranking = sequence
        return True

    @api.model
    def create(self, vals):
        res = super(TenderSessions, self).create(vals)
        res.update_ranking_classment()
        return res

    def write(self, vals):
        res = super(TenderSessions, self).write(vals)
        if vals.get('bidder_ids'):
            self.update_ranking_classment()
        return res

    @api.onchange('is_notation')
    def onchange_notation(self):
        if self.is_notation:
            self.is_moins_disant = False
            self.bidder_ids.write({'is_notation': True})
        else:
            self.notation_value = 0.0
            self.bidder_ids.write({'is_notation': False, 'note': 0.0})

    @api.onchange('is_moins_disant')
    def onchange_moins_disant(self):
        if self.is_moins_disant:
            self.write({'is_notation': False, 'notation_value': 0.0})

    # @api.onchange('bidder_ids')
    # def onchange_bidder_ids(self):
    #     if self.bidder_ids:
    #         for line in self.bidder_ids:
    #             if line.bidder_id and line.lot_id:
    #                 if len(self.bidder_ids.filtered(lambda x: x.bidder_id.id == line.bidder_id.id and x.lot_id.id == line.lot_id.id)) > 1:
    #                     raise UserError(_("you already configure a couple of (“soumissionnaire”, ”Lot”) "))


class SessionType(models.Model):
    _name = 'session.type'
    _description = 'Session Type'

    name = fields.Char(string="Name" , required=True)
    code = fields.Char(string="Code")


class BiddersSession(models.Model):
    _name = 'bidders.session'
    _description = 'Bidders Session'
    _rec_name = 'bidder_id'

    session_id = fields.Many2one('tender.sessions', string="Tender Session")
    bidder_id = fields.Many2one('res.partner', string="Bidder", required=True)
    lot_id = fields.Many2one('lot.details', string="Lot")
    object_name = fields.Char(related='lot_id.object_name', string='Object')
    decision = fields.Selection([('retenu', 'retenu'), ('écarté', 'écarté')], string="Decision")
    ecart = fields.Text(string="Gap Pattern")
    note = fields.Float(string="Note")
    ranking = fields.Integer(string="Ranking")
    is_notation = fields.Boolean(string='Notation ?')
    
    @api.onchange('decision')
    def onchange_decision(self):
        for rec in self:
            if rec.decision == 'retenu' and rec.session_id and rec.session_id.requisition_id:
                if rec.session_id.requisition_id.bidder_offer_ids:
                    bidder_off_recs = rec.session_id.requisition_id.bidder_offer_ids
                    bidder_off_recs_f = bidder_off_recs.filtered(lambda a: a.partner_id == rec.bidder_id)
#                     bidder_off_recs_e = bidder_off_recs_f.parts_ids.filtered(lambda a: a.partner_id == rec.bidder_id)
                    
                    #### Warning was developed by another developer PINTU MAKWANA and Mak commented this warning on 19-10-2020 on order of Adnane
                    # if not any([bid_line.obligatoire_copy1 == True for bid_line in bidder_off_recs_f.parts_ids]):
                    #     raise UserError(_('You can not set decision as retenu'))

    @api.onchange('note', 'decision')
    def onchange_note_value(self):
        if self.note:
            if self._context.get('notation_value'):
                if self.note < self._context.get('notation_value', 0.00):
                    self.decision = 'écarté'
                    if self.decision == 'retenu':
                        raise UserError(_('You can not set decision as retenu while notaion values is less than note.'))
            elif self.note < self.session_id.notation_value:
                if self.note < self._context.get('notation_value', 0.00):
                    self.decision = 'écarté'
                    if self.decision == 'retenu':
                        raise UserError(_('You can not set decision as retenu while notaion values is less than note.'))


class SessionAttachments(models.Model):
    _name = 'session.attachment'
    _description = 'Session Attachment'
    _rec_name = 'session_type'

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    session_type = fields.Many2one('session.type', string="Type session", required=True)
    document_type = fields.Text(string="Type Document")
    filename = fields.Char(string="Filename")
    attachment_id = fields.Binary(type="binary", string="Attachments")


class TenderDecision(models.Model):
    _name = 'tender.decision'
    _description = 'Tender Decision'
    _rec_name = 'bidder_id'
    _order = 'ranking desc, bidder_id'

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    ranking = fields.Integer(string="Ranking")
    bidder_id = fields.Many2one('res.partner', string="Bidder", required=True)
    lot_id = fields.Many2one('lot.details', string="Lot")
    decision = fields.Selection([('Attributaire', 'Attributaire'), ('Non Attributaire', 'Non Attributaire')], string="Decision Final")
    date = fields.Date(string='Date Attribution')
    description = fields.Text(string="Description")
    
    def generate_letter(self):
        return True


class TenderDecisionCancel(models.Model):
    _name = 'tender.decision.cancel'
    _description = 'Tender Decision Cancel'
    _rec_name = 'bidder_id'

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    bidder_id = fields.Many2one('res.partner', string="Bidder", required=True)
    lot_id = fields.Many2one('lot.details', string="Lot")
    description = fields.Text(string="Description")

    def generate_letter_cancel_print(self):
        return True


class TenderDecisionCompliments(models.Model):
    _name = 'tender.decision.compliments'
    _description = 'Tender Decision Compliments'

    requisition_id = fields.Many2one('purchase.requisition', string="Purcahse Requisition")
    name = fields.Char(string='Soumissionnaire/Lot', required=True)
    decision_complement_ids = fields.Many2many('decision.complement', 'rel_complement_requisition', 'complement_id', 'requisition_id', string="Complements?")
    # description = fields.Text(string="Description")
    # day = fields.Integer(string="Days")
    # date = fields.Date(string="Deadline")
    bidder_line_id = fields.Many2one('bidders.session', string="Bidder Line", ondelete='cascade')

    # @api.onchange('day')
    # def onchange_date(self):
    #     if self.day:
    #         actual_days = self.env['resource.calendar']._check_holiday_status(self.day, date.today())
    #         self.day = actual_days
    #         self.date = date.today() + timedelta(days=self.day)


class DecisionComplement(models.Model):
    _name = 'decision.complement'
    _description = 'Decision Complement'
    _rec_name = 'complements_id'

    complements_id = fields.Many2one('compliment.compliment', string="Complement", required=True)
    is_fournie = fields.Boolean(string='Fournie ?')
    is_conforme = fields.Boolean(string='Conforme ?')
    date = fields.Date(string="Date")
    comment = fields.Char(string="Commentaire")


class ComplimentCompliment(models.Model):
    _name = 'compliment.compliment'
    _description = 'Tender Compliments'

    name = fields.Char(string="Description", required=True)
    day = fields.Integer(string="Days")
    date = fields.Date(string="Deadline")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    PURCHASE_ORDER_BC_STATES = [
        ('draft', 'Brouillon'),
        ('sent', 'Consultation envoyé'),
        ('to approve', 'To Approve'),
        ('purchase', 'Commande confirmé'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ]

    tender_decision_line_id = fields.Many2one('tender.decision')
    is_bc_purchase_requisition = fields.Boolean(string='Is BC Purchase Requisition')
    state_bc_order = fields.Selection(PURCHASE_ORDER_BC_STATES, compute='_set_bc_order_state')

    @api.depends('state')
    def _set_bc_order_state(self):
        for purchase in self:
            purchase.state_bc_order = purchase.state


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    purchase_request_line_ids = fields.Many2many('purchase.request.line', 'rel_purchase_order_line', 'request_line_id', 'order_line_id',  string="Purchase Request Line")
    is_bc_purchase_requisition = fields.Boolean(string='Is BC Purchase Requisition')
