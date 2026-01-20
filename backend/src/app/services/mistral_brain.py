"""Mistral Brain integration service.

This service provides integration with the Mistral Brain automation system
running on the Jetson. It connects via SSH to read the SQLite database
and execute automations directly.
"""

import asyncio
import json
import logging
import subprocess
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Jetson SSH configuration
JETSON_HOST = "192.168.1.118"
JETSON_USER = "simon"
JETSON_DB_PATH = "/home/simon/mistral_brain.db"
EXECUTE_SCRIPT = "/home/simon/execute_automation.py"


class MistralBrainService:
    """Service for interacting with Mistral Brain on Jetson via SSH."""

    def __init__(self) -> None:
        self.host = JETSON_HOST
        self.user = JETSON_USER
        self.db_path = JETSON_DB_PATH
        self._available: bool | None = None

    async def _run_ssh_command(self, command: str, timeout: int = 15) -> tuple[bool, str]:
        """Execute a command on the Jetson via SSH using subprocess.

        Uses subprocess.run in a thread pool to avoid blocking the event loop.
        """
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
                else:
                    return False, result.stderr.strip() or result.stdout.strip()
            except subprocess.TimeoutExpired:
                return False, "Command timed out"
            except Exception as e:
                return False, str(e)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_sync)

    async def _run_query(self, query: str) -> list[dict[str, Any]]:
        """Execute a SQLite query on the Jetson and return results as dicts."""
        import base64

        # Encode query in base64 to avoid shell escaping issues
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

    async def is_available(self) -> bool:
        """Check if Jetson is reachable."""
        success, _ = await self._run_ssh_command("echo ok", timeout=5)
        self._available = success
        return success

    async def close(self) -> None:
        """Cleanup (no-op for subprocess-based implementation)."""
        pass

    async def get_automations(self) -> list[dict[str, Any]]:
        """Get list of all Mistral Brain automations.

        Returns:
            List of automation definitions with name, trigger, actions, etc.
        """
        query = """
            SELECT
                id, name, description, trigger, conditions, actions,
                enabled, created_by, created_at, modified_at,
                confidence, correction_count
            FROM automations
            ORDER BY name
        """
        rows = await self._run_query(query)

        automations = []
        for row in rows:
            # Parse JSON fields
            try:
                trigger = json.loads(row.get("trigger") or "{}")
            except (json.JSONDecodeError, TypeError):
                trigger = {}

            try:
                actions = json.loads(row.get("actions") or "[]")
            except (json.JSONDecodeError, TypeError):
                actions = []

            try:
                conditions = json.loads(row.get("conditions") or "[]")
            except (json.JSONDecodeError, TypeError):
                conditions = []

            automations.append({
                "id": row["id"],
                "name": row["name"],
                "label": row["name"].replace("_", " ").title(),
                "description": row.get("description"),
                "trigger": trigger,
                "conditions": conditions,
                "actions": actions,
                "enabled": bool(row.get("enabled", True)),
                "created_by": row.get("created_by"),
                "created_at": row.get("created_at"),
                "modified_at": row.get("modified_at"),
                "confidence": row.get("confidence", 1.0),
                "correction_count": row.get("correction_count", 0),
            })

        return automations

    async def get_automation_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a specific automation by name."""
        # Sanitize name to prevent SQL injection
        safe_name = name.replace("'", "''")
        query = f"""
            SELECT
                id, name, description, trigger, conditions, actions,
                enabled, created_by, created_at, modified_at,
                confidence, correction_count
            FROM automations
            WHERE name = '{safe_name}'
        """
        rows = await self._run_query(query)
        if not rows:
            return None

        row = rows[0]
        try:
            trigger = json.loads(row.get("trigger") or "{}")
        except (json.JSONDecodeError, TypeError):
            trigger = {}

        try:
            actions = json.loads(row.get("actions") or "[]")
        except (json.JSONDecodeError, TypeError):
            actions = []

        return {
            "id": row["id"],
            "name": row["name"],
            "label": row["name"].replace("_", " ").title(),
            "description": row.get("description"),
            "trigger": trigger,
            "actions": actions,
            "enabled": bool(row.get("enabled", True)),
        }

    async def execute_automation(self, automation_name: str) -> dict[str, Any]:
        """Execute a Mistral Brain automation by name.

        Args:
            automation_name: The name of the automation to execute (e.g., 'mode_nuit')

        Returns:
            Result of the automation execution
        """
        # Sanitize automation name
        safe_name = automation_name.replace("'", "").replace(";", "").replace("&", "")

        command = f"python3 {EXECUTE_SCRIPT} {safe_name}"
        success, output = await self._run_ssh_command(command, timeout=60)

        if success:
            # Try to parse JSON output if available
            try:
                result = json.loads(output)
                return {
                    "success": True,
                    "automation": automation_name,
                    "actions_total": result.get("total", 0),
                    "actions_succeeded": result.get("succeeded", 0),
                    "actions_failed": result.get("failed", 0),
                    "details": result.get("details", []),
                }
            except (json.JSONDecodeError, TypeError):
                return {
                    "success": True,
                    "automation": automation_name,
                    "message": output or "Automation executed",
                }
        else:
            logger.error(f"Automation {automation_name} failed: {output}")
            raise RuntimeError(f"Automation failed: {output}")

    async def toggle_automation(self, automation_name: str, enabled: bool) -> bool:
        """Enable or disable an automation in Mistral Brain.

        Args:
            automation_name: The automation name
            enabled: True to enable, False to disable

        Returns:
            True if successful
        """
        # Sanitize
        safe_name = automation_name.replace("'", "''")
        enabled_val = 1 if enabled else 0

        python_script = f"""
import sqlite3
conn = sqlite3.connect('{self.db_path}')
cursor = conn.cursor()
cursor.execute("UPDATE automations SET enabled = {enabled_val} WHERE name = '{safe_name}'")
conn.commit()
print(cursor.rowcount)
conn.close()
"""
        cmd = f"python3 -c \"{python_script}\""
        success, output = await self._run_ssh_command(cmd, timeout=10)

        return success and output.strip() == "1"

    async def get_recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent events from Mistral Brain.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of recent events
        """
        query = f"""
            SELECT
                id, timestamp, event_type, device, action, value,
                context, user_triggered, source, automation_name
            FROM events
            ORDER BY timestamp DESC
            LIMIT {int(limit)}
        """
        rows = await self._run_query(query)

        events = []
        for row in rows:
            try:
                context = json.loads(row.get("context") or "{}")
            except (json.JSONDecodeError, TypeError):
                context = {}

            events.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "device": row["device"],
                "action": row["action"],
                "value": row["value"],
                "context": context,
                "user_triggered": bool(row.get("user_triggered")),
                "source": row.get("source", "hubitat"),
                "automation_name": row.get("automation_name"),
            })

        return events

    async def get_execution_history(
        self, automation_name: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get automation execution history from events table.

        Args:
            automation_name: Filter by automation name (optional)
            limit: Maximum number of executions

        Returns:
            List of execution records
        """
        where_clause = "WHERE automation_name IS NOT NULL"
        if automation_name:
            safe_name = automation_name.replace("'", "''")
            where_clause = f"WHERE automation_name = '{safe_name}'"

        query = f"""
            SELECT
                automation_name,
                timestamp,
                event_type,
                device,
                action,
                value,
                source
            FROM events
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT {int(limit)}
        """
        return await self._run_query(query)


# Singleton instance
_mistral_brain_service: MistralBrainService | None = None


def get_mistral_brain_service() -> MistralBrainService:
    """Get the Mistral Brain service singleton."""
    global _mistral_brain_service
    if _mistral_brain_service is None:
        _mistral_brain_service = MistralBrainService()
    return _mistral_brain_service
