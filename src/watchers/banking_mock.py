"""
Mock Banking Watcher - Generates fake banking data for demo purposes.
"""
import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from src.watchers.base import BaseWatcher
from src.lib.logging import get_logger

VAULT_PATH = Path("AI_Employee_Vault")


class BankingMockWatcher(BaseWatcher):
    """Generates mock banking transactions for demo."""
    
    def __init__(self, interval: int = 300):  # Every 5 minutes
        super().__init__("banking_mock", interval)
        self.logger = get_logger("banking_mock")
        self.output_dir = VAULT_PATH / "Banking"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def check_for_updates(self):
        """Generate mock transactions periodically."""
        self._generate_mock_data()
        return []
    
    def _generate_mock_data(self):
        """Create realistic mock banking data."""
        transactions = self._generate_transactions()
        summary = self._calculate_summary(transactions)
        
        # Save transactions
        tx_file = self.output_dir / "transactions.json"
        tx_file.write_text(json.dumps(transactions, indent=2), encoding='utf-8')
        
        # Save summary
        summary_file = self.output_dir / "summary.json"
        summary_file.write_text(json.dumps(summary, indent=2), encoding='utf-8')
        
        self.logger.info(f"Mock banking data updated: {len(transactions)} transactions")
        
    def _generate_transactions(self) -> list:
        """Generate realistic fake transactions."""
        today = datetime.now()
        transactions = []
        
        # Income sources
        income_sources = [
            ("Client Payment - ABC Corp", 2500.00, 5000.00),
            ("Invoice #1234", 500.00, 1500.00),
            ("Consulting Fee", 800.00, 2000.00),
            ("Product Sale", 50.00, 300.00),
            ("Subscription Revenue", 29.99, 199.99),
        ]
        
        # Expense categories
        expenses = [
            ("AWS Cloud Services", -50.00, -200.00),
            ("Office Supplies", -20.00, -100.00),
            ("Software License", -15.00, -99.00),
            ("Marketing Ads", -50.00, -500.00),
            ("Contractor Payment", -200.00, -800.00),
        ]
        
        # Generate last 30 days of transactions
        for days_ago in range(30):
            date = today - timedelta(days=days_ago)
            
            # 1-3 transactions per day
            num_tx = random.randint(1, 3)
            for _ in range(num_tx):
                if random.random() > 0.4:  # 60% income
                    desc, min_amt, max_amt = random.choice(income_sources)
                    amount = round(random.uniform(min_amt, max_amt), 2)
                else:
                    desc, min_amt, max_amt = random.choice(expenses)
                    amount = round(random.uniform(min_amt, max_amt), 2)
                
                transactions.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "description": desc,
                    "amount": amount,
                    "category": "income" if amount > 0 else "expense",
                    "balance_after": 0  # Calculated later
                })
        
        # Sort by date and calculate running balance
        transactions.sort(key=lambda x: x["date"], reverse=True)
        balance = 10000.00  # Starting balance
        for tx in reversed(transactions):
            balance += tx["amount"]
            tx["balance_after"] = round(balance, 2)
        
        return transactions
    
    def _calculate_summary(self, transactions: list) -> dict:
        """Calculate financial summary."""
        total_income = sum(tx["amount"] for tx in transactions if tx["amount"] > 0)
        total_expenses = sum(tx["amount"] for tx in transactions if tx["amount"] < 0)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "period": "Last 30 Days",
            "current_balance": transactions[0]["balance_after"] if transactions else 10000.00,
            "total_income": round(total_income, 2),
            "total_expenses": round(abs(total_expenses), 2),
            "net_profit": round(total_income + total_expenses, 2),
            "transaction_count": len(transactions),
            "is_mock_data": True
        }


# Quick test
if __name__ == "__main__":
    watcher = BankingMockWatcher()
    watcher._generate_mock_data()
    print(f"Mock data generated in {watcher.output_dir}")
