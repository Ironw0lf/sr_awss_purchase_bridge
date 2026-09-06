# -*- coding: utf-8 -*-
from odoo import _, models


class SrWorkorder(models.Model):
    _inherit = 'sr.workorder'

    def action_create_purchase(self):
        # AWSS requires every purchase to go through the Purchase Request
        # approval flow (department manager, Supply Chain, CEO, Board) - a
        # raw purchase.order is never created directly, so this replaces
        # sr_maintenance's native "New Purchase Order" action instead of
        # running alongside it.
        self.ensure_one()

        # Falls back to the current user's own employee record if the WO's
        # requester has none linked - otherwise default_requester_id ends up
        # empty and the request can't resolve its department/approver.
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.requester_id.id)], limit=1
        ) or self.env.user.employee_id

        # Same source as sr_maintenance's native flow
        # (PurchaseOrderLine._compute_analytic_distribution, which reads
        # order_id.sr_workorder_id.analytic_distribution) - the WO's own
        # distribution, applied to every line. awss_purchase_request's own
        # _create_purchase_order() only falls back to the department's
        # analytic account when a line has none, so this is never
        # overwritten downstream.
        analytic_distribution = self.analytic_distribution or False

        line_commands = [
            (0, 0, {
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.display_name,
                'product_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'price_unit': line.unit_price,
                'analytic_distribution': analytic_distribution,
            })
            for line in self.line_ids
            if line.product_id
        ]

        return {
            'type': 'ir.actions.act_window',
            'name': _("New Purchase Request"),
            'res_model': 'awss.purchase.request',
            'view_mode': 'form',
            'context': {
                'default_sr_workorder_id': self.id,
                'default_requester_id': employee.id,
                'default_line_ids': line_commands,
                'default_motivation': self.name,
                # Keeps the WO's analytic distribution on the lines - without
                # this, the header Analytic Account (computed from the
                # requester's department) pushes onto every line on open and
                # replaces what we just set above.
                'default_analytic_locked': True,
            },
        }

    def action_view_purchases(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _("Purchase Requests"),
            'res_model': 'awss.purchase.request',
            'view_mode': 'list,form',
            'domain': [('sr_workorder_id', '=', self.id)],
        }
