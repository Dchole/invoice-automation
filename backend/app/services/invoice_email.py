"""Professional HTML invoice email builder."""
from __future__ import annotations
from datetime import date


def build_invoice_email(
    invoice_number: str,
    client_name: str,
    issue_date: date,
    due_date: date,
    currency: str,
    subtotal: float,
    tax_rate: float,
    tax_amount: float,
    total: float,
    amount_paid: float,
    line_items: list[dict],
    sender_name: str = "InvoiceFlow",
    notes: str | None = None,
) -> tuple[str, str]:
    """Return (subject, html_body) for the invoice email."""
    remaining = total - amount_paid
    subject = f"Invoice {invoice_number} — ${remaining:,.2f} {currency} due {due_date}"

    rows = ""
    for item in line_items:
        desc = item.get("description") or "Consulting session"
        rows += f"""
            <tr>
              <td style="padding: 12px 16px; border-bottom: 1px solid #e8e6e1; color: #3a3d42; font-size: 14px;">{item['date']}</td>
              <td style="padding: 12px 16px; border-bottom: 1px solid #e8e6e1; color: #3a3d42; font-size: 14px;">{desc}</td>
              <td style="padding: 12px 16px; border-bottom: 1px solid #e8e6e1; color: #6b6e75; font-size: 14px; text-align: right;">{item['duration']} min</td>
              <td style="padding: 12px 16px; border-bottom: 1px solid #e8e6e1; color: #6b6e75; font-size: 14px; text-align: right;">${item['rate']}/hr</td>
              <td style="padding: 12px 16px; border-bottom: 1px solid #e8e6e1; color: #3a3d42; font-size: 14px; font-weight: 600; text-align: right;">${item['amount']:,.2f}</td>
            </tr>"""

    notes_section = ""
    if notes:
        notes_section = f"""
            <tr>
              <td colspan="2" style="padding: 24px 0 0 0;">
                <p style="margin: 0 0 4px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9ca3; font-weight: 600;">Notes</p>
                <p style="margin: 0; font-size: 14px; color: #6b6e75; line-height: 1.5;">{notes}</p>
              </td>
            </tr>"""

    tax_row = ""
    if tax_rate and tax_rate > 0:
        tax_row = f"""
                <tr>
                  <td style="padding: 6px 0; font-size: 14px; color: #6b6e75;">Tax ({tax_rate}%)</td>
                  <td style="padding: 6px 0; font-size: 14px; color: #3a3d42; text-align: right;">${tax_amount:,.2f}</td>
                </tr>"""

    paid_row = ""
    if amount_paid > 0:
        paid_row = f"""
                <tr>
                  <td style="padding: 6px 0; font-size: 14px; color: #3d8b5e;">Paid</td>
                  <td style="padding: 6px 0; font-size: 14px; color: #3d8b5e; text-align: right;">-${amount_paid:,.2f}</td>
                </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background-color: #f5f4f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <div style="max-width: 640px; margin: 0 auto; padding: 40px 20px;">

    <!-- Header -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 32px;">
      <tr>
        <td>
          <h1 style="margin: 0; font-size: 24px; font-weight: 700; color: #2c2e33; letter-spacing: -0.02em;">{sender_name}</h1>
          <p style="margin: 4px 0 0 0; font-size: 12px; color: #9a9ca3; text-transform: uppercase; letter-spacing: 0.08em;">Invoice {invoice_number}</p>
        </td>
      </tr>
    </table>

    <!-- Card -->
    <div style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 12px rgba(0,0,0,0.04);">

      <!-- Invoice meta -->
      <div style="padding: 32px 32px 24px 32px; border-bottom: 1px solid #e8e6e1;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="vertical-align: top;">
              <p style="margin: 0 0 4px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9ca3; font-weight: 600;">Bill To</p>
              <p style="margin: 0; font-size: 18px; font-weight: 600; color: #2c2e33;">{client_name}</p>
            </td>
            <td style="text-align: right; vertical-align: top;">
              <table cellpadding="0" cellspacing="0" style="margin-left: auto;">
                <tr>
                  <td style="padding: 2px 16px 2px 0; font-size: 12px; color: #9a9ca3; text-transform: uppercase; letter-spacing: 0.04em;">Invoice</td>
                  <td style="padding: 2px 0; font-size: 14px; font-weight: 600; color: #2c2e33;">{invoice_number}</td>
                </tr>
                <tr>
                  <td style="padding: 2px 16px 2px 0; font-size: 12px; color: #9a9ca3; text-transform: uppercase; letter-spacing: 0.04em;">Issued</td>
                  <td style="padding: 2px 0; font-size: 14px; color: #3a3d42;">{issue_date}</td>
                </tr>
                <tr>
                  <td style="padding: 2px 16px 2px 0; font-size: 12px; color: #9a9ca3; text-transform: uppercase; letter-spacing: 0.04em;">Due</td>
                  <td style="padding: 2px 0; font-size: 14px; font-weight: 600; color: #b84c4c;">{due_date}</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </div>

      <!-- Line items -->
      <div style="padding: 0;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <thead>
            <tr style="background-color: #faf9f6;">
              <th style="padding: 10px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9ca3; font-weight: 600; text-align: left; border-bottom: 1px solid #e8e6e1;">Date</th>
              <th style="padding: 10px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9ca3; font-weight: 600; text-align: left; border-bottom: 1px solid #e8e6e1;">Description</th>
              <th style="padding: 10px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9ca3; font-weight: 600; text-align: right; border-bottom: 1px solid #e8e6e1;">Duration</th>
              <th style="padding: 10px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9ca3; font-weight: 600; text-align: right; border-bottom: 1px solid #e8e6e1;">Rate</th>
              <th style="padding: 10px 16px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #9a9ca3; font-weight: 600; text-align: right; border-bottom: 1px solid #e8e6e1;">Amount</th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>

      <!-- Totals -->
      <div style="padding: 24px 32px 32px 32px; background-color: #faf9f6; border-top: 1px solid #e8e6e1;">
        <table cellpadding="0" cellspacing="0" style="margin-left: auto; min-width: 240px;">
          <tbody>
            <tr>
              <td style="padding: 6px 0; font-size: 14px; color: #6b6e75;">Subtotal</td>
              <td style="padding: 6px 0; font-size: 14px; color: #3a3d42; text-align: right;">${subtotal:,.2f}</td>
            </tr>
            {tax_row}
            {paid_row}
            <tr>
              <td colspan="2" style="padding: 8px 0 0 0; border-top: 2px solid #2c2e33;"></td>
            </tr>
            <tr>
              <td style="padding: 4px 0; font-size: 18px; font-weight: 700; color: #2c2e33;">Amount Due</td>
              <td style="padding: 4px 0; font-size: 18px; font-weight: 700; color: #2c2e33; text-align: right;">${remaining:,.2f} {currency}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Notes -->
      {f'<div style="padding: 0 32px 24px 32px;">{notes_section}</div>' if notes_section else ''}

    </div>

    <!-- Footer -->
    <div style="margin-top: 32px; text-align: center;">
      <p style="margin: 0 0 4px 0; font-size: 13px; color: #9a9ca3;">
        Payment is due by <strong style="color: #3a3d42;">{due_date}</strong>
      </p>
      <p style="margin: 0; font-size: 12px; color: #b5b7bc;">
        Sent via InvoiceFlow
      </p>
    </div>

  </div>
</body>
</html>"""

    # Plain text fallback
    plain = (
        f"Invoice {invoice_number}\n"
        f"{'=' * 40}\n\n"
        f"To: {client_name}\n"
        f"Date: {issue_date}\n"
        f"Due: {due_date}\n\n"
        f"Work performed:\n"
    )
    for item in line_items:
        desc = item.get("description") or "Consulting session"
        plain += f"  {item['date']} | {desc} | {item['duration']} min | ${item['amount']:,.2f}\n"
    plain += (
        f"\nSubtotal: ${subtotal:,.2f}\n"
    )
    if tax_rate and tax_rate > 0:
        plain += f"Tax ({tax_rate}%): ${tax_amount:,.2f}\n"
    if amount_paid > 0:
        plain += f"Paid: -${amount_paid:,.2f}\n"
    plain += (
        f"\nAmount Due: ${remaining:,.2f} {currency}\n\n"
        f"Payment is due by {due_date}.\n\n"
        f"Thank you,\n{sender_name}\n"
    )

    return subject, html, plain
