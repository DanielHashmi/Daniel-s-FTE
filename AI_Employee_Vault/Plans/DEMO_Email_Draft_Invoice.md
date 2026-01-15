# Email Draft - Invoice INV-2026-01-001

**Status**: Ready to Send (After Review)
**Created**: January 15, 2026
**Approval**: AR-2026-01-15-001 (Approved)

---

## Email Details

**To**: client@example.com (John Smith)
**From**: [your-email@company.com]
**Subject**: Invoice INV-2026-01-001 - January 2026 Services
**Attachment**: INV-2026-01-001.pdf (Invoice)
**Priority**: Normal

---

## Email Body

```
Hi John,

Thank you for reaching out regarding the January invoice. Please find attached
invoice INV-2026-01-001 for software development services provided during
January 2026.

Invoice Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Invoice Number:    INV-2026-01-001
Invoice Date:      January 15, 2026
Billing Period:    January 1-31, 2026
Amount Due:        $7,800.00
Payment Terms:     Net 30
Due Date:          February 14, 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Services Provided:
• Software Development - Project Alpha (40 hours @ $150/hr): $6,000.00
• Code Review and Optimization (8 hours @ $150/hr): $1,200.00
• Technical Documentation (4 hours @ $150/hr): $600.00

Payment Options:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Bank Transfer (Preferred)
   Account Name: [Your Company Name]
   Account Number: [Your Account Number]
   Routing Number: [Your Routing Number]

2. Check
   Make payable to: [Your Company Name]
   Mail to: [Your Business Address]

3. Credit Card
   Payment portal: [Your Payment Link]

Please let me know if you need any clarification, have questions about the
invoice, or require additional documentation.

I appreciate your continued business and look forward to working with you
on upcoming projects.

Best regards,
[Your Name]
[Your Title]
[Your Company Name]
[Your Phone Number]
[Your Email]
```

---

## Alternative Version (More Concise)

```
Hi John,

Attached is invoice INV-2026-01-001 for January 2026 services ($7,800.00).

Payment is due February 14, 2026 (Net 30). You can pay via bank transfer,
check, or credit card - details are in the attached invoice.

Let me know if you have any questions.

Thanks,
[Your Name]
```

---

## Email Sending Checklist

Before sending:
- [ ] Review invoice PDF for accuracy
- [ ] Verify all amounts and calculations
- [ ] Confirm client email address
- [ ] Attach invoice PDF
- [ ] Choose email version (detailed or concise)
- [ ] Customize [placeholders] with your information
- [ ] Proofread for typos
- [ ] Send from your business email account

After sending:
- [ ] Mark invoice as "Sent" in accounting system
- [ ] Set payment reminder for due date
- [ ] Update Dashboard with sent status
- [ ] Move approval request to Done/
- [ ] Log transaction in audit trail

---

## Follow-Up Schedule

**If payment not received:**

- **Day 25** (Feb 9): Friendly reminder email
- **Day 30** (Feb 14): Payment due - send reminder if not received
- **Day 35** (Feb 19): Follow-up email with payment status inquiry
- **Day 45** (Mar 1): Escalation - phone call or formal notice

**Reminder Email Template:**
```
Hi John,

I wanted to follow up on invoice INV-2026-01-001 ($7,800.00) which was
due on February 14, 2026.

Could you please confirm the payment status? If there are any issues or
questions about the invoice, I'm happy to discuss.

Thanks,
[Your Name]
```

---

## Accounting Integration

**Transaction Record:**
```json
{
  "transaction_id": "TXN-2026-01-15-001",
  "type": "invoice_sent",
  "invoice_number": "INV-2026-01-001",
  "date": "2026-01-15",
  "client": {
    "name": "John Smith",
    "company": "Acme Corporation",
    "email": "client@example.com"
  },
  "amount": 7800.00,
  "currency": "USD",
  "payment_terms": "Net 30",
  "due_date": "2026-02-14",
  "status": "sent",
  "approval": "AR-2026-01-15-001",
  "sent_by": "AI Employee System",
  "approved_by": "Human",
  "services": [
    {
      "description": "Software Development - Project Alpha",
      "hours": 40,
      "rate": 150.00,
      "amount": 6000.00
    },
    {
      "description": "Code Review and Optimization",
      "hours": 8,
      "rate": 150.00,
      "amount": 1200.00
    },
    {
      "description": "Technical Documentation",
      "hours": 4,
      "rate": 150.00,
      "amount": 600.00
    }
  ]
}
```

---

## Dashboard Update

**Status**: ✅ INVOICE SENT

```
Invoice Request - COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Client:           John Smith (Acme Corporation)
Invoice:          INV-2026-01-001
Amount:           $7,800.00
Date Sent:        January 15, 2026
Payment Due:      February 14, 2026
Status:           Sent - Awaiting Payment
Approval:         AR-2026-01-15-001 (Approved)
Processing Time:  2 minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next Action: Monitor for payment by February 14, 2026
```

---

## Files Created

1. **Invoice PDF**: `Invoices/INV-2026-01-001.pdf`
2. **Email Draft**: `Drafts/Email_Invoice_INV-2026-01-001.txt`
3. **Transaction Log**: `Logs/2026-01-15-transactions.json`
4. **Approval Record**: `Approved/AR-2026-01-15-001.md`

---

## What You'd Do Next (Real Workflow)

### Immediate (Today):
1. Open email draft
2. Open invoice PDF
3. Review both for accuracy
4. Attach PDF to email
5. Send from your email client

### This Week:
1. Monitor for payment confirmation
2. Update accounting system when paid
3. Send thank you note when payment received

### If Payment Delayed:
1. Send friendly reminder on Day 25
2. Follow up on due date (Day 30)
3. Escalate if needed (Day 45)

---

**Demo Complete!**

This shows you exactly what deliverables you'd get from an approved invoice request.

**Time Saved**:
- Manual invoice creation: 20-30 minutes
- Email drafting: 10-15 minutes
- Accounting setup: 5-10 minutes
- **Total saved**: 35-55 minutes per invoice

**Quality Improvements**:
- Professional formatting
- Consistent branding
- Complete payment instructions
- Automatic follow-up schedule
- Audit trail maintained
