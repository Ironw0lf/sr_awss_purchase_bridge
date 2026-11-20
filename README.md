# SR Maintenance - AWSS Purchase Request Bridge

Connects SR Maintenance's work orders to AWSS's Purchase Request
approval flow instead of creating a raw Purchase Order directly, so
parts requested from a work order go through the same approval chain
(department manager, Supply Chain, CEO, Board) as every other purchase
at AWSS.

## What it's for

SR Maintenance's native "New Purchase Order" button on a work order
creates a `purchase.order` directly. AWSS never allows that - every
purchase must go through `awss.purchase.request` first. This module is
a client-specific integration that bridges the two, entirely additively:
neither `sr_maintenance` nor `awss_purchase_request`'s own code is
modified, only extended.

## Features

- Adds `sr_workorder_id` on `awss.purchase.request` (surfaced on its
  form and list views), carried over to the resulting `purchase.order`
  once approved - reusing the `sr_workorder_id` field SR Maintenance
  already has on `purchase.order` for its native flow, instead of
  introducing a second one.
- Overrides `sr.workorder.action_create_purchase()` to open a Purchase
  Request instead of a Purchase Order, pre-filled with the work order's
  parts (product, quantity, unit price) and its analytic distribution on
  every line - opened with `analytic_locked` set so the requester's
  department default never overwrites it.
- Only real purchases go to approval. Parts the warehouse already holds
  (free quantity covers the need) are left out and issued from stock with
  Stock Issue; stocked parts running short that have an active Min/Max
  (reordering) rule are left out too and follow the replenishment process;
  a stocked part short with no Min/Max rule is requested for the missing
  quantity only; products that are not stocked (services...) are requested
  in full. Parts already issued are ignored. The button always opens a
  new Purchase Request, so a purchase can be raised for something the
  parts don't cover: with nothing to buy from the parts, the request
  opens empty. A note in the work order's chatter lists what was left out
  and why (once per identical list).
- The work order's **Purchases** tab and its counter now show the Purchase
  Requests (`purchase_request_ids`), not purchase orders. AWSS's purchasing
  is the request: a purchase order only exists once a request is approved,
  so listing RFQs/purchase orders there was the wrong object. Open requests
  are listed first (a request already converted into a purchase order is
  not repeated: the order stands for it), the work order's purchase orders
  read-only below them, and
  neither list can create (a purchase is started with Create Purchase,
  which opens a Purchase Request full screen). The arrow at the end of each
  row opens the record full screen instead of in a pop-up. Purchase cost on
  the work order still comes from the purchase orders, which an approved
  request creates with the work-order link.
- Both ways to add a purchase to a work order open a Purchase Request: the
  header's Create Purchase button and the tab's Add a purchase request
  button call the same method. As a safeguard, a purchase order linked to a
  work order without a source Purchase Request (`awss_source_request_id`)
  is refused, however it is attempted (form, import, API), so no RFQ can be
  raised outside the approval flow. Existing orders are not touched.
- The hourly parts check of SR Maintenance (Awaiting Parts to Ready to
  Schedule) also waits for the work order's purchase requests: one still in
  approval, or approved without its purchase order yet, keeps the work order
  waiting. Once converted, the purchase order's own reception check applies.
- A **Work Order** smart button on the Purchase Request form (shown when
  the request is linked to a work order) opens that work order, with its
  number on the button.
- The request's **Motivation** is filled with the work order number and,
  on the next line, its description, so approvers see what the purchase is
  for without opening the work order.
- Falls back to the current user's own employee record when the work
  order's requester has none linked, so the request can still resolve a
  department/approver.
- Overrides `sr.workorder.action_view_purchases()` to list the work
  order's Purchase Requests instead of Purchase Orders - a request
  already gives access to the resulting order once approved, via its own
  smart button.

## Dependencies

- `sr_maintenance`
- `awss_purchase_request` **>= 19.0.4.9** - `analytic_locked` and
  `_prepare_purchase_order_vals()` (the hook this module overrides) were
  both added in that version.

Targets **Odoo 19**.

## Installation

1. Place this module in the addons path, alongside SR Maintenance and
   AWSS's own `awss_purchase_request` module.
2. Restart Odoo.
3. Apps → Update Apps List → Install "SR Maintenance - AWSS Purchase
   Request Bridge".

## License

LGPL-3
