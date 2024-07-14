from odoo import models, api, fields, exceptions
from odoo.exceptions import ValidationError
import copy


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Purchase Request'

    name = fields.Char(readonly=1, default='New')
    requested_by_id = fields.Many2one('res.users', required=1, default=lambda self: self.env.user)
    vendor_id = fields.Many2one('res.partner', required=1, related='requested_by_id.partner_id')
    start_date = fields.Date(default=fields.Datetime.now)
    end_date = fields.Date()
    rejection_reason = fields.Char(readonly=1, )
    orderline_ids = fields.One2many('purchase.request.line', 'request_id')
    total_price = fields.Float(readonly=1, compute="_compute_total_price")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to be approved', 'To be approved'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('cancel', 'Cancel'),
    ],
        default='draft'
    )
    total_qty = fields.Integer(compute="_check_order_product_qty_against_request", invisible=1, store=1)
    can_create_po = fields.Boolean(default=1)
    temp_pr_line = {}
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute='_compute_purchase_order_count')

    def draft_button(self):
        for rec in self:
            print('inside draft')
            rec.state = 'draft'

    def to_be_approved_button(self):
        for rec in self:
            print('inside to be approved')
            rec.state = 'to be approved'

    def approve_button(self):
        for rec in self:
            print('inside approve')
            rec.state = 'approve'

    def reject_button(self):
        for rec in self:
            print('inside reject')
            rec.state = 'reject'

    def cancel_button(self):
        for rec in self:
            print('inside cancel')
            rec.state = 'cancel'

    @api.constrains('requested_by_id')
    def onchange_requested_by_id(self):
        for rec in self:
            if not rec.requested_by_id.partner_id:
                raise ValidationError("Vendor must have a contact person.")

    def approve_button(self):
        self.ensure_one()
        self.state = 'approve'

        purchase_managers_group = self.env.ref('purchase_request_addon.purchase_manager_group')
        purchase_managers = purchase_managers_group.users

        # Constructing the subject and body of the email
        subject = f"Purchase Request {self.name} Approved"
        body = f"Purchase Request {self.name} has been approved."

        # Send email notification to all users in the purchase manager group
        for manager in purchase_managers:
            mail_vals = {
                'subject': subject,
                'body_html': body,
                'email_to': manager.email,
            }
            self.env['mail.mail'].create(mail_vals).send()

            # Create a log note for each manager in the manager group
            self.message_post(
                body=body,
                subject=subject,
                partner_ids=[manager.partner_id.id],  # Use a command to add the manager as a recipient
                subtype_id=self.env.ref('mail.mt_note').id,  # Use subtype 'Note'
            )
        return True

    def create_po(self):
        self._check_order_product_qty_against_request()
        if not self.can_create_po:
            return
        for rec in self:
            purchase_order = self.env['purchase.order'].create({
                'name': rec.name,
                'partner_id': rec.vendor_id.id,
                'state': 'draft'
                # Add more fields as needed
            })
            for pr_line in rec.orderline_ids:
                self.env['purchase.order.line'].create({
                    'product_id': pr_line.product_id.id,
                    'order_id': purchase_order.id,
                    'name': pr_line.product_id.name,
                    'product_qty': self.temp_pr_line[pr_line.product_id],
                    # Add more fields as needed
                })

    def open_rejection_wizard(self):
        return {
            'name': 'Reject Purchase Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'change.state',
            'view_mode': 'form',
            'target': 'new',
        }

    @api.depends('state')
    def _check_order_product_qty_against_request(self):
        self.can_create_po = 1
        if self.state in ["approve"]:
            for pr in self:
                print(pr.state)
                po_list = []
                po = None
                for pr_line in pr.orderline_ids.product_id:
                    po = self.env['purchase.order'].search([
                        ('name', '=', pr.name),
                        ('order_line.product_id', '=', pr_line.id),
                        ('state', 'in', ['purchase']),
                    ], )
                    if po:
                        po_list.append(po)
                print(po_list)

                for pr_line in pr.orderline_ids:
                    self.temp_pr_line[pr_line.product_id] = pr_line.quantity
                if po_list:
                    for rec in po_list[0]:
                        for po_line in rec.order_line:
                            for pr_line in pr.orderline_ids:
                                if pr_line.product_id == po_line.product_id:
                                    self.temp_pr_line[pr_line.product_id] -= po_line.product_qty
                                    print(self.temp_pr_line[pr_line.product_id])
                                    if self.temp_pr_line[pr_line.product_id] <= 0:
                                        self.temp_pr_line[pr_line.product_id] = 0
                                        self.can_create_po = 0

    @api.depends('orderline_ids.total')
    def _compute_total_price(self):
        for order in self:
            order.total_price = sum(order.orderline_ids.mapped('total'))

    @api.model
    def create(self, vals):
        res = super(PurchaseRequest, self).create(vals)
        if res.name == 'New':
            res.name = self.env['ir.sequence'].next_by_code('purchase.request.seq')
        return res

    @api.depends('name')
    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = self.env['purchase.order'].search_count(
                [('name', '=', record.name)])  # You can adjust the domain as needed

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('state', 'in', ['draft','purchase']),('name', '=',self.name)],  # Adjust the domain as needed
            'context': dict(self._context, create=False)
        }
