# -*- coding: utf-8 -*-
"""Which of a work order's parts really need a purchase request.

Only a real purchase goes through AWSS's approval chain. A part that the
warehouse already holds is issued from stock, and a stocked part running
short that is covered by a Min/Max (reordering) rule follows the normal
replenishment process - neither belongs in a purchase request.

A plain function on purpose, not a model method: it only reads the work
order and its products, so it can be checked on its own (the module itself
needs awss_purchase_request to load).
"""
from odoo import _


def _is_stocked(product):
    # Odoo 19 flags storable products with is_storable (type 'consu');
    # Odoo 18 uses type 'product'.
    if 'is_storable' in product._fields:
        return bool(product.is_storable)
    return product.type == 'product'


def purchase_needs(workorder):
    """Split a work order's part lines by how they are supplied.

    Returns a dict of lists of (line, quantity) pairs:
      buy          - to put in the purchase request, with the quantity to buy
      in_stock     - the warehouse holds enough: issue them from stock
      replenish    - stocked, short, and under a Min/Max rule: left to the
                     replenishment process
    Lines without a product and lines already issued from stock are ignored.
    """
    result = {'buy': [], 'in_stock': [], 'replenish': []}

    lines = workorder.line_ids.filtered(lambda l: l.product_id and not l.issued)
    if not lines:
        return result

    stocked_products = lines.mapped('product_id').filtered(_is_stocked)
    with_rule = set()
    if stocked_products:
        rules = workorder.env['stock.warehouse.orderpoint'].sudo().search([
            ('product_id', 'in', stocked_products.ids),
            ('active', '=', True),
        ])
        with_rule = set(rules.mapped('product_id').ids)

    for line in lines:
        product = line.product_id
        needed = line.quantity or 0.0

        if not _is_stocked(product):
            result['buy'].append((line, needed))
            continue

        # free_qty leaves out what other pickings already reserve.
        free = max(product.free_qty, 0.0)
        if free >= needed:
            result['in_stock'].append((line, needed))
        elif product.id in with_rule:
            result['replenish'].append((line, needed - free))
        else:
            result['buy'].append((line, needed - free))

    return result


def purchase_motivation(workorder):
    """The Motivation text of the purchase request raised from a work order:
    what the purchase is for, so approvers don't have to open the work order.
    Number, description, equipment, location, type and team, and the project
    (marked CAPEX when it is)."""
    wo = workorder
    lines = [wo.name, wo.description]

    if wo.equipment_id:
        lines.append(_("Equipment: %s", wo.equipment_id.display_name))

    location = wo.location_id or wo.equipment_id.location_id
    if location:
        lines.append(_("Location: %s", location.display_name))

    details = []
    if wo.type_id:
        details.append(_("Type: %s", wo.type_id.name))
    if wo.team_id:
        details.append(_("Team: %s", wo.team_id.name))
    if details:
        lines.append(' | '.join(details))

    if wo.project_id:
        project = _("Project: %s", wo.project_id.display_name)
        lines.append(project + (' (CAPEX)' if wo.is_capex else ''))

    return '\n'.join(line for line in lines if line)
