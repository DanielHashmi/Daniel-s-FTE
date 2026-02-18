"""
Banking / Finance Watcher (Gold Tier).

Hackathon blueprint expectation:
- Finance Watcher ingests local bank CSV exports and logs transactions into the vault.
- Creates Needs_Action items for suspicious / high-risk transactions (local-only domain).

This implementation is local-first and does not require a bank API.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.lib.vault import vault
from src.watchers.base import BaseWatcher


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_amount(raw: str) -> Optional[float]:
    if raw is None:
        return None
    txt = str(raw).strip()
    if not txt:
        return None
    # Strip currency symbols and thousands separators.
    txt = txt.replace("$", "").replace(",", "")
    try:
        return float(txt)
    except ValueError:
        return None


def _pick_column(headers: List[str], candidates: List[str]) -> Optional[str]:
    headers_l = {h.lower(): h for h in headers}
    for cand in candidates:
        if cand.lower() in headers_l:
            return headers_l[cand.lower()]
    return None


def _parse_date(raw: str) -> Optional[str]:
    """
    Return YYYY-MM-DD string for common bank CSV date formats.
    """
    if raw is None:
        return None
    txt = str(raw).strip()
    if not txt:
        return None

    # Try a few common formats.
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(txt, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _tx_id(date_str: str, description: str, amount: float) -> str:
    basis = f"{date_str}|{description.strip().lower()}|{amount:.2f}"
    return hashlib.md5(basis.encode("utf-8")).hexdigest()[:12]


class BankingWatcher(BaseWatcher):
    """
    Ingest CSV exports dropped into `AI_Employee_Vault/Inbox/Banking/`.

    Output:
    - `AI_Employee_Vault/Banking/transactions.json` (deduped list)
    - `AI_Employee_Vault/Bank_Transactions.md` (human-readable, for weekly audit)
    - Needs_Action items when amounts exceed thresholds
    """

    def __init__(self, interval: int = 300):
        super().__init__("banking_watcher", interval, domain=os.getenv("BANKING_DOMAIN", "business"))
        self.import_dir = vault.dirs["inbox"] / "Banking"
        self.processed_dir = self.import_dir / ".processed"
        self.out_dir = vault.root / "Banking"
        self.transactions_path = self.out_dir / "transactions.json"
        self.bank_md_path = vault.root / "Bank_Transactions.md"

        self.amount_alert_threshold = float(os.getenv("BANKING_ALERT_AMOUNT", "500"))
        self.import_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self):
        csv_files = sorted(self.import_dir.glob("*.csv"), key=lambda p: p.name)
        if not csv_files:
            return

        existing = self._load_existing_transactions()
        existing_ids = {t.get("id") for t in existing if isinstance(t, dict) and t.get("id")}

        added_total = 0
        for csv_path in csv_files:
            try:
                added = self._ingest_csv(csv_path, existing, existing_ids)
                added_total += added
                self._archive_import(csv_path)
            except Exception as exc:
                self.logger.error(f"Failed to ingest bank CSV {csv_path.name}: {exc}")

        if added_total:
            self._write_transactions(existing)
            self._write_bank_markdown(existing)
            self.logger.log_action(
                action_type="banking_import",
                result="success",
                target=str(self.transactions_path),
                parameters={"files": [p.name for p in csv_files], "added": added_total},
                approval_status="not_required",
            )

    def _load_existing_transactions(self) -> List[Dict[str, Any]]:
        if not self.transactions_path.exists():
            return []
        try:
            data = json.loads(self.transactions_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get("transactions"), list):
                return data["transactions"]
        except Exception:
            return []
        return []

    def _write_transactions(self, txs: List[Dict[str, Any]]) -> None:
        # Sort by date desc then id.
        def sort_key(t: Dict[str, Any]) -> Tuple[str, str]:
            return (str(t.get("date") or ""), str(t.get("id") or ""))

        txs_sorted = sorted(txs, key=sort_key, reverse=True)
        payload: Dict[str, Any] = {
            "updated_at": _utc_now_iso(),
            "count": len(txs_sorted),
            "transactions": txs_sorted,
        }
        self.transactions_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        # Also update Accounting/transactions/<YYYY-MM>/transactions.json for the current month.
        now = datetime.now()
        month_dir = vault.dirs["accounting"] / "transactions" / now.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)
        month_path = month_dir / "transactions.json"
        month_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _write_bank_markdown(self, txs: List[Dict[str, Any]], limit: int = 50) -> None:
        rows = []
        for t in txs[:limit]:
            date_str = str(t.get("date") or "")
            desc = str(t.get("description") or "").replace("|", " ")
            amt = t.get("amount")
            try:
                amt_f = float(amt)
            except Exception:
                amt_f = 0.0
            rows.append(f"| {date_str} | {desc} | {amt_f:,.2f} |")

        md = (
            "---\n"
            f"updated_at: {_utc_now_iso()}\n"
            "source: banking_watcher\n"
            "schema: bank_transactions_v1\n"
            "---\n\n"
            "# Bank Transactions\n\n"
            f"Last updated: `{_utc_now_iso()}`\n\n"
            "## Recent Transactions\n\n"
            "| Date | Description | Amount |\n"
            "|------|-------------|--------|\n"
            + ("\n".join(rows) if rows else "| - | - | 0.00 |")
            + "\n"
        )
        self.bank_md_path.write_text(md, encoding="utf-8")

    def _archive_import(self, csv_path: Path) -> None:
        dest = self.processed_dir / csv_path.name
        if dest.exists():
            dest = self.processed_dir / f"{csv_path.stem}_{int(datetime.now().timestamp())}{csv_path.suffix}"
        csv_path.rename(dest)

    def _ingest_csv(
        self,
        csv_path: Path,
        txs: List[Dict[str, Any]],
        existing_ids: set,
    ) -> int:
        added = 0
        with open(csv_path, "r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return 0

            date_col = os.getenv("BANK_CSV_DATE_COLUMN") or _pick_column(
                reader.fieldnames,
                ["date", "transaction date", "posted date", "posting date"],
            )
            desc_col = os.getenv("BANK_CSV_DESC_COLUMN") or _pick_column(
                reader.fieldnames,
                ["description", "details", "merchant", "name", "memo"],
            )
            amt_col = os.getenv("BANK_CSV_AMOUNT_COLUMN") or _pick_column(
                reader.fieldnames,
                ["amount", "transaction amount", "debit", "credit"],
            )

            if not date_col or not desc_col or not amt_col:
                raise ValueError(
                    f"Unrecognized CSV schema. Columns={reader.fieldnames}. "
                    "Set BANK_CSV_DATE_COLUMN/BANK_CSV_DESC_COLUMN/BANK_CSV_AMOUNT_COLUMN."
                )

            for row in reader:
                date_str = _parse_date(row.get(date_col, ""))
                desc = str(row.get(desc_col, "")).strip()
                amt = _parse_amount(row.get(amt_col, ""))
                if not date_str or not desc or amt is None:
                    continue

                txid = _tx_id(date_str, desc, amt)
                if txid in existing_ids:
                    continue

                existing_ids.add(txid)
                tx = {
                    "id": txid,
                    "date": date_str,
                    "description": desc,
                    "amount": float(amt),
                    "category": "income" if amt > 0 else "expense",
                    "source_file": csv_path.name,
                    "ingested_at": _utc_now_iso(),
                }
                txs.append(tx)
                added += 1

                # High-risk transaction alert -> Needs_Action for human review.
                if amt < 0 and abs(amt) >= self.amount_alert_threshold:
                    self.create_action_file(
                        type="finance",
                        content=(
                            "# High-Amount Expense Detected\n\n"
                            f"- Date: {date_str}\n"
                            f"- Description: {desc}\n"
                            f"- Amount: ${abs(amt):,.2f}\n\n"
                            "## Suggested Actions\n"
                            "- [ ] Verify transaction legitimacy\n"
                            "- [ ] Categorize expense\n"
                            "- [ ] If fraudulent, initiate dispute\n"
                        ),
                        metadata={
                            "transaction_id": txid,
                            "date": date_str,
                            "description": desc,
                            "amount": float(amt),
                            "threshold": self.amount_alert_threshold,
                        },
                        priority="high",
                    )

        return added

