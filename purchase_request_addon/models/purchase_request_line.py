from odoo import models, api, fields, exceptions



class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'

    product_id = fields.Many2one('product.product', required = 1)
    description = fields.Char(related='product_id.name', store=True)
    quantity = fields.Float(default = 1)
    cost_price = fields.Float(related = 'product_id.standard_price',readonly=1)
    price = fields.Float(default =1)
    total = fields.Float(readonly = 1, compute="_compute_total_price")
    request_id = fields.Many2one('purchase.request')


    @api.depends('quantity','price')
    def _compute_total_price(self):
        for order in self:
            order.total = order.quantity * order.price

