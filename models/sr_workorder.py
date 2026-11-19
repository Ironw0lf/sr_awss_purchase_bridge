# -*- coding: utf-8 -*-
from odoo import _, models

from .purchase_needs import purchase_needs


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

        # Only real purchases go to approval: parts the warehouse holds are
        # issued from stock, and short stocked parts under a Min/Max rule
        # follow the replenishment process (see purchase_needs).
        needs = purchase_needs(self)

        self._post_purchase_split_note(needs)

        line_commands = [
            (0, 0, {
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.display_name,
                'product_qty': quantity,
                'product_uom': line.product_id.uom_id.id,
                'price_unit': line.unit_price,
                'analytic_distribution': analytic_distribution,
            })
            for line, quantity in needs['buy']
        ]

        # The button always opens a new request, so a purchase can still be
        # raised for something the work order's parts don't cover. With
        # nothing to buy from the parts, the request simply opens empty.
        context = {
            'default_sr_workorder_id': self.id,
            'default_requester_id': employee.id,
            'default_motivation': self.name,
            # Keeps the WO's analytic distribution on the lines - without
            # this, the header Analytic Account (computed from the
            # requester's department) pushes onto every line on open and
            # replaces what we just set above.
            'default_analytic_locked': True,
        }
        if line_commands:
            context['default_line_ids'] = line_commands

        return {
            'type': 'ir.actions.act_window',
            'name': _("New Purchase Request"),
            'res_model': 'awss.purchase.request',
            'view_mode': 'form',
            'context': context,
        }

    def _post_purchase_split_note(self, needs):
        """Say in the chatter which parts were left out of the purchase
        request and why, so nobody wonders where a line went."""
        left_out = []
        if needs['in_stock']:
            left_out.append(_(
                "In stock, to issue with Stock Issue: %s",
                ', '.join(l.product_id.display_name for l, _q in needs['in_stock']),
            ))
        if needs['replenish']:
            left_out.append(_(
                "Short but covered by a Min/Max rule, left to replenishment: %s",
                ', '.join(l.product_id.display_name for l, _q in needs['replenish']),
            ))
        if left_out:
            body = '<br/>'.join(
                [_("Parts not included in the purchase request:")] + left_out
            )
            # The button is also how a new, free-form purchase is started, so
            # it can be clicked many times: don't repeat an identical note.
            if not self.message_ids.filtered(lambda m: m.body and body in m.body):
                self.message_post(body=body)

    def action_view_purchases(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _("Purchase Requests"),
            'res_model': 'awss.purchase.request',
            'view_mode': 'list,form',
            'domain': [('sr_workorder_id', '=', self.id)],
        }
