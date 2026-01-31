"""Email/Invoice management service.

Integrates with Gmail Invoice Sorter on Jetson to provide
invoice tracking and email classification for Family Hub.
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Jetson SSH configuration
JETSON_HOST = "192.168.1.118"
JETSON_USER = "simon"
JETSON_DB_PATH = "/home/simon/gmail_sorter/invoices.db"
SORTER_SCRIPT = "/home/simon/gmail_sorter/gmail_invoice_sorter.py"


class EmailService:
    """Service for managing emails and invoices via Jetson."""

    def __init__(self) -> None:
        self.host = JETSON_HOST
        self.user = JETSON_USER
        self.db_path = JETSON_DB_PATH

    async def _run_ssh_command(self, command: str, timeout: int = 30) -> tuple[bool, str]:
        """Execute a command on the Jetson via SSH."""
        ssh_cmd = [
            "ssh",
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=no",
            "-o", "BatchMode=yes",
            f"{self.user}@{self.host}",
            command,
        ]

        def run_sync() -> tuple[bool, str]:
            try:
                result = subprocess.run(
                    ssh_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if result.returncode == 0:
                    return True, result.stdout.strip()
                return False, result.stderr.strip() or result.stdout.strip()
            except subprocess.TimeoutExpired:
                return False, "Command timed out"
            except Exception as e:
                return False, str(e)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_sync)

    async def _run_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a SQLite query on the Jetson invoices database."""
        import base64

        query_b64 = base64.b64encode(query.encode()).decode()

        python_script = f'''
import sqlite3
import json
import base64

query = base64.b64decode("{query_b64}").decode()
conn = sqlite3.connect("{self.db_path}")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute(query)
rows = cursor.fetchall()
result = [dict(row) for row in rows]
print(json.dumps(result))
conn.close()
'''
        cmd = f"python3 -c '{python_script}'"

        success, output = await self._run_ssh_command(cmd, timeout=20)
        if not success:
            logger.error(f"Query failed: {output}")
            return []

        try:
            return json.loads(output) if output else []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse query result: {e}")
            return []

    async def get_invoices(
        self,
        category: str | None = None,
        is_paid: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get invoices from the database.

        Args:
            category: Filter by category (a_payer, payees, gouv_canada, gouv_quebec)
            is_paid: Filter by payment status
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of invoice records
        """
        where_clauses = []

        if category:
            where_clauses.append(f"category = '{category}'")
        if is_paid is not None:
            where_clauses.append(f"is_paid = {1 if is_paid else 0}")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT
                id, gmail_id, sender, subject, category, label,
                amount, currency, date_received, date_processed,
                due_date, is_paid, has_attachment, calendar_event_id
            FROM invoices
            {where_sql}
            ORDER BY date_received DESC
            LIMIT {limit} OFFSET {offset}
        """
        return await self._run_query(query)

    async def get_invoice_stats(self) -> dict[str, Any]:
        """Get invoice statistics."""
        query = """
            SELECT
                category,
                COUNT(*) as count,
                SUM(CASE WHEN is_paid = 0 THEN 1 ELSE 0 END) as unpaid_count,
                SUM(CASE WHEN is_paid = 1 THEN 1 ELSE 0 END) as paid_count,
                SUM(CASE WHEN is_paid = 0 THEN amount ELSE 0 END) as unpaid_amount,
                SUM(CASE WHEN is_paid = 1 THEN amount ELSE 0 END) as paid_amount
            FROM invoices
            GROUP BY category
        """
        rows = await self._run_query(query)

        stats = {
            "categories": rows,
            "totals": {
                "total_invoices": sum(r.get("count", 0) for r in rows),
                "unpaid_count": sum(r.get("unpaid_count", 0) for r in rows),
                "paid_count": sum(r.get("paid_count", 0) for r in rows),
                "unpaid_amount": sum(r.get("unpaid_amount", 0) or 0 for r in rows),
                "paid_amount": sum(r.get("paid_amount", 0) or 0 for r in rows),
            }
        }
        return stats

    async def get_upcoming_due_dates(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get invoices with upcoming due dates."""
        query = f"""
            SELECT
                id, gmail_id, sender, subject, category,
                amount, due_date, calendar_event_id
            FROM invoices
            WHERE due_date IS NOT NULL
              AND is_paid = 0
              AND date(due_date) >= date('now')
            ORDER BY due_date ASC
            LIMIT {limit}
        """
        return await self._run_query(query)

    async def get_todos(self, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get invoice-related todos."""
        where_clause = f"WHERE status = '{status}'" if status else ""

        query = f"""
            SELECT
                id, title, description, category, priority,
                due_date, amount, source, source_id, status,
                created_at, completed_at
            FROM todos
            {where_clause}
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'normal' THEN 3
                    ELSE 4
                END,
                due_date ASC
            LIMIT {limit}
        """
        return await self._run_query(query)

    async def update_todo_status(
        self, todo_id: int, status: str
    ) -> dict[str, Any] | None:
        """Update todo status (pending, completed, cancelled)."""
        completed_at = ""
        if status == "completed":
            completed_at = f", completed_at = '{datetime.now().isoformat()}'"

        python_script = f'''
import sqlite3
import json

conn = sqlite3.connect("{self.db_path}")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("""
    UPDATE todos
    SET status = '{status}'{completed_at}
    WHERE id = {todo_id}
""")
conn.commit()

cursor.execute("SELECT * FROM todos WHERE id = {todo_id}")
row = cursor.fetchone()
result = dict(row) if row else None
print(json.dumps(result))
conn.close()
'''
        cmd = f"python3 -c '{python_script}'"
        success, output = await self._run_ssh_command(cmd, timeout=10)

        if success and output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return None
        return None

    async def mark_invoice_paid(self, invoice_id: int) -> bool:
        """Mark an invoice as paid."""
        python_script = f'''
import sqlite3

conn = sqlite3.connect("{self.db_path}")
cursor = conn.cursor()
cursor.execute("UPDATE invoices SET is_paid = 1 WHERE id = {invoice_id}")
conn.commit()
print(cursor.rowcount)
conn.close()
'''
        cmd = f"python3 -c '{python_script}'"
        success, output = await self._run_ssh_command(cmd, timeout=10)
        return success and output.strip() == "1"

    async def get_onepage_emails(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get One Page trading emails."""
        query = f"""
            SELECT
                id, gmail_id, subject, date_received, file_path, date_processed
            FROM onepage_emails
            ORDER BY date_received DESC
            LIMIT {limit}
        """
        return await self._run_query(query)

    async def get_processing_logs(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent processing logs."""
        query = f"""
            SELECT
                id, timestamp, emails_scanned, invoices_found,
                onepage_found, calendar_events_created, errors
            FROM processing_log
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        rows = await self._run_query(query)

        # Parse errors JSON
        for row in rows:
            if row.get("errors"):
                try:
                    row["errors"] = json.loads(row["errors"])
                except json.JSONDecodeError:
                    row["errors"] = []

        return rows

    async def run_sorter(self, days_back: int = 7, max_results: int = 100) -> dict[str, Any]:
        """Run the Gmail invoice sorter manually."""
        cmd = f"cd /home/simon/gmail_sorter && python3 gmail_invoice_sorter.py 2>&1"
        success, output = await self._run_ssh_command(cmd, timeout=120)

        return {
            "success": success,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        }

    async def is_available(self) -> bool:
        """Check if Jetson email service is reachable."""
        success, _ = await self._run_ssh_command("echo ok", timeout=5)
        return success


# Singleton instance
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get the Email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
