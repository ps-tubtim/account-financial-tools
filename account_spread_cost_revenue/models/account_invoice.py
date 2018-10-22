# Copyright 2016-2018 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        """Invoked when validating the invoices."""
        res = super().action_move_create()
        for invoice in self:
            spreads = invoice.invoice_line_ids.mapped('spread_id')
            spreads.compute_spread_board()
            spreads.reconcile_spread_moves()
        return res

    @api.multi
    def invoice_line_move_line_get(self):
        """Copying expense/revenue account from spread to move lines."""
        res = super().invoice_line_move_line_get()
        for line in res:
            invl_id = line.get('invl_id')
            invl = self.env['account.invoice.line'].browse(invl_id)
            if invl.spread_id:
                if invl.invoice_id.type in ('out_invoice', 'in_refund'):
                    account = invl.spread_id.debit_account_id
                else:
                    account = invl.spread_id.credit_account_id
                line['account_id'] = account.id
        return res

    @api.multi
    def action_cancel(self):
        """Cancel the spread lines and their related moves when
        the invoice is canceled."""
        res = super().action_cancel()
        for invoice_line in self.mapped('invoice_line_ids'):
            moves = invoice_line.spread_id.line_ids.mapped('move_id')
            moves.button_cancel()
            moves.unlink()
            invoice_line.spread_id.line_ids.unlink()
        return res
