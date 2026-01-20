#!/usr/bin/env python3
"""
Odoo Accounting Main Operation - Extended for draft/live modes.

This script supports both draft mode (cloud) and live mode (local with approval).
"""

import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any, List
from xmlrpc.client import ServerProxy
import argparse
import csv

# Config
VAULT_ROOT = Path(os.getenv('VAULT_ROOT', 'AI_Employee_Vault'))
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"
LOGS_DIR = VAULT_ROOT / "Logs"
AUDIT_LOG = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.json"


def setup_dirs():
    ACCOUNTING_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def audit_log(action: str, target: str, status: str, details: Optional[dict] = None):
    """Log action to audit trail."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "odoo_accounting",
        "sub_action": action,
        "target": target,
        "result": status,
        "actor": "odoo_accounting_skill",
        "details": details or {}
    }
    try:
        logs = json.loads(AUDIT_LOG.read_text()) if AUDIT_LOG.exists() else []
        logs.append(entry)
        AUDIT_LOG.write_text(json.dumps(logs, indent=2))
    except Exception as e:
        print(f"Warning: Audit log failed: {e}", file=sys.stderr)


class OdooAccountingClient:
    """Client for interacting with Odoo accounting system."""

    def __init__(self, mode: str = 'draft'):
        """
        Initialize Odoo client.

        Args:
            mode: 'draft' for cloud (no posting), 'live' for local (with approval)
        """
        self.mode = mode
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'

        # Odoo connection settings
        self.url = os.getenv('ODOO_URL', 'http://localhost:8069')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USERNAME')
        self.password = os.getenv('ODOO_PASSWORD')

        if not all([self.db, self.url, self.username, self.password]):
            raise ValueError("Missing Odoo configuration. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD")

        self.uid = None
        self.models = None
        self._connect()

    def _connect(self):
        """Connect to Odoo XML-RPC API."""
        try:
            common = ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})

            if not self.uid:
                raise ConnectionError("Failed to authenticate with Odoo")

            self.models = ServerProxy(f'{self.url}/xmlrpc/2/object')
            print(f"✓ Connected to Odoo ({self.mode} mode)")

        except Exception as e:
            raise ConnectionError(f"Failed to connect to Odoo: {e}")

    def get_draft_invoices(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch draft invoices that need review."""
        try:
            invoices = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'search_read',
                [[['state', '=', 'draft']]],
                {'fields': ['name', 'partner_id', 'amount_total', 'invoice_date',
                           'invoice_line_ids', 'state'], 'limit': limit}
            )
            return invoices
        except Exception as e:
            print(f"Error fetching invoices: {e}")
            return []

    def validate_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Validate invoice before posting."""
        validation_results = {
            'valid': False,
            'errors': [],
            'warnings': []
        }

        try:
            invoice = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'read',
                [invoice_id],
                {'fields': ['name', 'partner_id', 'amount_total',
                           'invoice_line_ids', 'state', 'journal_id']}
            )

            if not invoice:
                validation_results['errors'].append("Invoice not found")
                return validation_results

            invoice = invoice[0]

            # Check if already posted
            if invoice['state'] != 'draft':
                validation_results['errors'].append(f"Invoice is not in draft state (current: {invoice['state']})")

            # Validate partner
            if not invoice.get('partner_id'):
                validation_results['errors'].append("Missing customer")

            # Validate lines
            if not invoice.get('invoice_line_ids'):
                validation_results['errors'].append("No invoice lines")

            # Validate amount
            if invoice.get('amount_total', 0) <= 0:
                validation_results['errors'].append("Invalid invoice amount")

            # Set valid flag
            if not validation_results['errors']:
                validation_results['valid'] = True

        except Exception as e:
            validation_results['errors'].append(f"Validation error: {str(e)}")

        return validation_results

    def validate_invoices_batch(self, invoice_ids: List[int]) -> Dict[str, Any]:
        """Validate batch of invoices for posting."""
        results = {
            'total': len(invoice_ids),
            'valid': [],
            'invalid': [],
            'validation_report': {}
        }

        for invoice_id in invoice_ids:
            validation = self.validate_invoice(invoice_id)
            invoice = self.models.execute_kw(
                self.db, self.uid, self.password,
                'account.move', 'read', [invoice_id],
                {'fields': ['name', 'amount_total']}
            )[0]

            if validation['valid']:
                results['valid'].append(invoice_id)
                results['validation_report'][invoice_id] = {
                    'name': invoice['name'],
                    'amount': invoice['amount_total'],
                    'status': 'valid'
                }
            else:
                results['invalid'].append(invoice_id)
                results['validation_report'][invoice_id] = {
                    'name': invoice['name'],
                    'amount': invoice['amount_total'],
                    'status': 'invalid',
                    'errors': validation['errors']
                }

        return results

    def create_invoice_draft_report(self, output_file: Optional[str] = None) -> Path:
        """Generate draft invoice report (usable in cloud)."""
        print("Generating draft invoice report...")

        # Fetch draft invoices
        invoices = self.get_draft_invoices()

        if not invoices:
            print("No draft invoices found")
            return None

        # Generate report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        vault_path = Path(os.getenv('VAULT_ROOT', 'AI_Employee_Vault'))
        report_file = vault_path / "Reports" / f"draft_invoices_{timestamp}.csv"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', newline='') as csvfile:
            fieldnames = ['ID', 'Invoice', 'Customer', 'Amount', 'Date', 'Status', 'Validation']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for inv in invoices:
                invoice_id = inv['id']
                validation = self.validate_invoice(invoice_id)

                # Get customer name
                customer_name = "Unknown"
                if inv.get('partner_id'):
                    customer_name = inv['partner_id'][1] if isinstance(inv['partner_id'], list) else inv['partner_id']

                writer.writerow({
                    'ID': invoice_id,
                    'Invoice': inv.get('name', 'N/A'),
                    'Customer': customer_name,
                    'Amount': inv.get('amount_total', 0),
                    'Date': inv.get('invoice_date', 'N/A'),
                    'Status': inv.get('state', 'unknown'),
                    'Validation': 'PASS' if validation['valid'] else 'FAIL'
                })

        print(f"✓ Report generated: {report_file}")
        print(f"  Total invoices: {len(invoices)}")

        return report_file

    def post_invoice(self, invoice_id: int, require_approval: bool = True) -> Dict[str, Any]:
        """
        Post single invoice.

        Args:
            invoice_id: Odoo invoice ID
            require_approval: If True, requires explicit approval (live mode)

        Returns:
            Dict with posting result
        """
        result = {
            'invoice_id': invoice_id,
            'posted': False,
            'draft_mode': self.mode == 'draft',
            'approval_required': require_approval
        }

        # Validate invoice
        validation = self.validate_invoice(invoice_id)
        if not validation['valid']:
            result['error'] = validation['errors']
            return result

        # Draft mode: Report only, don't post
        if self.mode == 'draft':
            print(f"[DRAFT MODE] Would post invoice {invoice_id} (not posting)")
            result['posted'] = False
            result['note'] = 'Draft mode - no posting'
            audit_log('post_invoice_draft', str(invoice_id), 'success_draft', {'invoice_id': invoice_id})
            return result

        # Live mode with approval required
        if self.mode == 'live' and require_approval:
            # Check for approval file
            vault_path = Path(os.getenv('VAULT_ROOT', 'AI_Employee_Vault'))
            approval_file = vault_path / "Pending_Approval" / f"invoice_{invoice_id}_approval.yaml"

            if not approval_file.exists():
                # Create approval request
                invoice = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'account.move', 'read', [invoice_id],
                    {'fields': ['name', 'amount_total', 'partner_id']}
                )[0]

                approval_content = f"""---
approval_id: invoice_post_{invoice_id}
type: invoice_posting
invoice_id: {invoice_id}
invoice_name: {invoice['name']}
amount: {invoice['amount_total']}
partner: {invoice.get('partner_id', [None, 'Unknown'])[1] if invoice.get('partner_id') else 'Unknown'}
requires_approval: true
mode: live
action: post
---

# Invoice Posting Approval Request

This invoice requires approval before posting.

**Invoice**: {invoice['name']}
**Amount**: ${invoice['amount_total']:,.2f}
**Customer**: {invoice.get('partner_id', [None, 'Unknown'])[1] if invoice.get('partner_id') else 'Unknown'}

## Actions

To approve: Move to Approved folder
To reject: Move to Rejected folder with feedback
"""

                approval_file.write_text(approval_content)

                result['posted'] = False
                result['approval_required'] = True
                result['approval_file'] = str(approval_file)
                print(f"✓ Approval request created: {approval_file}")
                print(f"  Manual approval needed for invoice {invoice_id}")
                return result

        # Post the invoice
        try:
            if self.dry_run:
                print(f"[DRY RUN] Would post invoice {invoice_id}")
                result['posted'] = False
                result['dry_run'] = True
                audit_log('post_invoice_dry', str(invoice_id), 'success_dry', {'invoice_id': invoice_id})
            else:
                self.models.execute_kw(
                    self.db, self.uid, self.password,
                    'account.move', 'action_post',
                    [[invoice_id]]
                )
                result['posted'] = True
                audit_log('post_invoice', str(invoice_id), 'success', {'invoice_id': invoice_id})
                print(f"✓ Posted invoice {invoice_id}")

        except Exception as e:
            result['posted'] = False
            result['error'] = str(e)
            audit_log('post_invoice_error', str(invoice_id), 'error', {'invoice_id': invoice_id, 'error': str(e)})

        return result

    def post_invoices_batch(self, invoice_ids: List[int], require_approval: bool = True) -> Dict[str, Any]:
        """Post batch of invoices."""
        results = {
            'mode': self.mode,
            'total': len(invoice_ids),
            'posted': [],
            'skipped': [],
            'failed': [],
            'draft_mode_skipped': 0
        }

        if self.mode == 'draft':
            print(f"[DRAFT MODE] Validating {len(invoice_ids)} invoices (not posting)")
            validation = self.validate_invoices_batch(invoice_ids)
            results['draft_mode_skipped'] = validation['total']
            results['validation_report'] = validation['validation_report']
            audit_log('post_batch_draft', str(invoice_ids), 'success_draft', {'count': len(invoice_ids)})
            return results

        for invoice_id in invoice_ids:
            result = self.post_invoice(invoice_id, require_approval)

            if result['posted']:
                results['posted'].append(invoice_id)
            elif 'approval_required' in result and not result.get('posted'):
                results['skipped'].append(invoice_id)
            else:
                results['failed'].append({
                    'invoice_id': invoice_id,
                    'error': result.get('error')
                })

        audit_log('post_invoices_batch', str(invoice_ids), 'completed', results)
        return results

    def generate_invoice_summary(self, limit: int = 100) -> Dict[str, Any]:
        """Generate comprehensive invoice summary."""
        draft = self.get_draft_invoices(limit)

        summary = {
            'timestamp': datetime.now().isoformat(),
            'mode': self.mode,
            'total_draft': len(draft),
            'invoices': []
        }

        for inv in draft:
            invoice_id = inv['id']
            validation = self.validate_invoice(invoice_id)

            summary['invoices'].append({
                'id': invoice_id,
                'name': inv.get('name'),
                'amount': inv.get('amount_total'),
                'state': inv.get('state'),
                'valid': validation['valid'],
                'validation_errors': validation['errors'] if not validation['valid'] else []
            })

        return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='Odoo Accounting Operations - Draft/Live Mode')
    parser.add_argument('--mode', choices=['draft', 'live'], default='draft',
                       help='Operation mode (draft for cloud, live for local)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Draft report command
    parser_report = subparsers.add_parser('draft-report', help='Generate draft invoice report')
    parser_report.add_argument('--output', help='Output file path')

    # Validate single invoice
    parser_validate = subparsers.add_parser('validate', help='Validate invoice')
    parser_validate.add_argument('invoice_id', type=int, help='Invoice ID')

    # Validate batch
    parser_validate_batch = subparsers.add_parser('validate-batch', help='Validate batch of invoices')
    parser_validate_batch.add_argument('invoice_ids', type=int, nargs='+', help='Invoice IDs')

    # Post single invoice
    parser_post = subparsers.add_parser('post', help='Post invoice')
    parser_post.add_argument('invoice_id', type=int, help='Invoice ID')
    parser_post.add_argument('--no-approval', action='store_true', help='Skip approval check')

    # Post batch
    parser_post_batch = subparsers.add_parser('post-batch', help='Post batch of invoices')
    parser_post_batch.add_argument('invoice_ids', type=int, nargs='+', help='Invoice IDs')
    parser_post_batch.add_argument('--no-approval', action='store_true', help='Skip approval check')

    # Summary
    parser_summary = subparsers.add_parser('summary', help='Generate invoice summary')
    parser_summary.add_argument('--limit', type=int, default=100, help='Limit results')

    args = parser.parse_args()
    setup_dirs()

    # Create client
    client = OdooAccountingClient(mode=args.mode)

    if args.command == 'draft-report':
        output = args.output
        if output:
            client.create_invoice_draft_report(output)
        else:
            client.create_invoice_draft_report()

    elif args.command == 'validate':
        result = client.validate_invoice(args.invoice_id)
        print(json.dumps(result, indent=2))

    elif args.command == 'validate-batch':
        result = client.validate_invoices_batch(args.invoice_ids)
        print(json.dumps(result, indent=2))

    elif args.command == 'post':
        require_approval = not args.no_approval
        result = client.post_invoice(args.invoice_id, require_approval)
        print(json.dumps(result, indent=2))

    elif args.command == 'post-batch':
        require_approval = not args.no_approval
        result = client.post_invoices_batch(args.invoice_ids, require_approval)
        print(json.dumps(result, indent=2))

    elif args.command == 'summary':
        summary = client.generate_invoice_summary(limit=args.limit)
        print(json.dumps(summary, indent=2))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
