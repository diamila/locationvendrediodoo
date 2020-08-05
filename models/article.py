 # -*- coding: utf-8 -*-

from lxml import etree

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp



class BienNormal(models.Model):
    _inherit = 'product.template'

    @api.model
    def _get_default_country(self):
        country = self.env['res.country'].search([('code', '=', 'MA')], limit=1)
        return country


    latitude = fields.Char(string="Latitude", default="0.0")
    longitude = fields.Char(string="Longitude", default="0.0")
    Date = fields.Date()
    nbre_tour = fields.Integer(string="niveau", default=1)
    ameublement = fields.Char(string="ameublement")
    reference = fields.Char(string="Référence ameublement")

    location_ok = fields.Boolean(
        'Peut étre en location', default=True)

    type_id = fields.Many2one('lb.type', ondelete='cascade', string="Type Biens")
    gestionnaire_id = fields.Many2one('lb.gestionnaire', ondelete='cascade', string="gestionnaire Immeuble", store=True)
    bailleur_id = fields.Many2one('lb.bailleur', ondelete='cascade', string="Bailleur", store=True)
    chambres = fields.Char(string="Chambres")
    salles_bain = fields.Char(string="Salles De Bain")
    parking = fields.Char(string="Parking")
    oriente_vers = fields.Char(string="orienté vers", default='Ouest')
    # compte_revenu = fields.Many2one('lb.revenu', ondelete='cascade', string="Compte de Revenu")
    # compte_depense = fields.Many2one('ldu Bien")
    adresse = fields.Many2one('lb.quartier')
    ville = fields.Many2one('lb.ville')
    pays = fields.Many2one('res.country', string="Pays", default=_get_default_country)

    notes = fields.Text(string="Notes")

    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Documents")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('lb.location'),
                                 index=1)
    currency_id = fields.Many2one('res.currency', 'Currency', compute='_compute_currency_id')

    _sql_constraints = [
        ('reference_unique',
         'UNIQUE(reference)',
         "La référence du bien doit être unique"),
    ]

    # 2 fonctions pour l'image attaché
    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for bien in self:
            bien.doc_count = Attachment.search_count([('res_model', '=', 'lb.bien'), ('res_id', '=', bien.id)])

    @api.multi
    def attachment_tree_view(self):
        self.ensure_one()
        domain = [('res_model', '=', 'lb.bien'), ('res_id', 'in', self.ids)]
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                            Cliquez sur créer (et non importer) pour ajouter les images associées à vos biens.</p><p>
                        </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }

    # Calcul de la devise
    @api.multi
    def _compute_currency_id(self):
        try:
            main_company = self.sudo().env.ref('base.main_company')
        except ValueError:
            main_company = self.env['res.company'].sudo().search([], limit=1, order="id")
        for template in self:
            template.currency_id = template.company_id.sudo().currency_id.id or main_company.currency_id.id

    # kanban: qui affiche les sessions regroupées par cours (les colonnes sont donc des cours)
    color = fields.Integer()

    # géolocalisation du bien
    def tt_locate_bien(self):
        return {
            "type": "ir.actions.act_url",
            "url": 'https://www.google.com/maps/search/?api=1&query=' + self.longitude + ', -' + self.latitude,
        }

    # champs: lien avec les information du bien
    history_ids = fields.Many2many('lb.history', string="history")
    plus_proche_ids = fields.Many2many('lb.lieu', string="lieu plus proche")
    sous_propriete_ids = fields.Many2many('lb.sous_propriete', string="composant/sous_propriété")

    # champs: Plans d'étage, photos et documents
    plan_ids = fields.Many2many('lb.plan_etage', string="plan")
    photos_ids = fields.Many2many('lb.photos', string="photos")
    documents_ids = fields.Many2many('lb.documents', string="documents")

    @api.multi
    def get_name(self):
        for rec in self:
            res.append((rec.nom, '%s - %s' % (prix_location)))
        return res

    contrat = fields.Many2one('lb.location', ondelete='cascade', string="Contrat lié au bien")

    state = fields.Selection([
        ('draft', 'New'),
        ('confirm', 'En Cour'),
        ('ferme', 'Fermé'),
    ], string='Status', related='contrat.state')

    # géolocalisation du bien
    def tt_locate_bien(self):
        return {
            "type": "ir.actions.act_url",
            "url": 'https://www.google.com/maps/search/?api=1&query=' + self.longitude + ', -' + self.latitude,
        }