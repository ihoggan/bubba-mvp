"""SQLite repository for investigation persistence."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from bubba.diagnosis.domain.models import Investigation
from bubba.diagnosis.domain.export import DiagnosisExport


class InvestigationRepository:
    """Persist and query investigations in SQLite."""

    def __init__(self, db_path: str = "~/.bubba/diagnoses.db"):
        """Initialize repository with SQLite database.
        
        Args:
            db_path: Path to SQLite database file (~/path expanded)
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create investigations table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    symptom_what_is_wrong TEXT,
                    root_cause TEXT,
                    status TEXT,
                    engineer_confirmed BOOLEAN,
                    investigation_json TEXT NOT NULL,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_root_cause 
                ON investigations(root_cause)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_symptom 
                ON investigations(symptom_what_is_wrong)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON investigations(status)
            """)
            conn.commit()

    def save(self, investigation: Investigation) -> str:
        """Persist investigation to SQLite.
        
        Args:
            investigation: Investigation to save
            
        Returns:
            Investigation ID
        """
        # Serialize investigation to JSON (simple dataclass → dict approach)
        investigation_json = self._serialize_investigation(investigation)
        
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO investigations 
                (id, title, symptom_what_is_wrong, root_cause, status, 
                 engineer_confirmed, investigation_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(investigation.id),
                investigation.title,
                investigation.symptom.what_is_wrong,
                investigation.root_cause,
                investigation.status.value,
                investigation.engineer_confirmed,
                investigation_json,
                now,
                now
            ))
            conn.commit()
        
        return str(investigation.id)

    def get_by_id(self, investigation_id: str) -> Optional[Investigation]:
        """Retrieve investigation by ID.
        
        Args:
            investigation_id: UUID of investigation
            
        Returns:
            Investigation if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT investigation_json FROM investigations WHERE id = ?",
                (investigation_id,)
            ).fetchone()
        
        if not row:
            return None
        
        return self._deserialize_investigation(row[0])

    def search_by_symptom(self, query: str) -> list[dict]:
        """Search investigations by symptom keyword.
        
        Args:
            query: Search term to match against symptom_what_is_wrong
            
        Returns:
            List of investigation summaries (id, title, symptom, root_cause, status)
        """
        pattern = f"%{query}%"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT id, title, symptom_what_is_wrong, root_cause, status, engineer_confirmed
                FROM investigations
                WHERE symptom_what_is_wrong LIKE ?
                ORDER BY updated_at DESC
            """, (pattern,)).fetchall()
        
        return [
            {
                "id": row[0],
                "title": row[1],
                "symptom": row[2],
                "root_cause": row[3],
                "status": row[4],
                "engineer_confirmed": row[5]
            }
            for row in rows
        ]

    def search_by_root_cause(self, query: str) -> list[dict]:
        """Search investigations by root cause keyword.
        
        Args:
            query: Search term to match against root_cause
            
        Returns:
            List of investigation summaries
        """
        pattern = f"%{query}%"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT id, title, symptom_what_is_wrong, root_cause, status, engineer_confirmed
                FROM investigations
                WHERE root_cause LIKE ?
                ORDER BY updated_at DESC
            """, (pattern,)).fetchall()
        
        return [
            {
                "id": row[0],
                "title": row[1],
                "symptom": row[2],
                "root_cause": row[3],
                "status": row[4],
                "engineer_confirmed": row[5]
            }
            for row in rows
        ]

    def list_all(self) -> list[dict]:
        """List all investigations, newest first.
        
        Returns:
            List of investigation summaries
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT id, title, symptom_what_is_wrong, root_cause, status, engineer_confirmed
                FROM investigations
                ORDER BY updated_at DESC
            """).fetchall()
        
        return [
            {
                "id": row[0],
                "title": row[1],
                "symptom": row[2],
                "root_cause": row[3],
                "status": row[4],
                "engineer_confirmed": row[5]
            }
            for row in rows
        ]

    @staticmethod
    def _serialize_investigation(investigation: Investigation) -> str:
        """Serialize Investigation to JSON string.
        
        Uses a simplified approach: convert to ExportedDiagnosis (validated model)
        then to JSON. This ensures we're only storing what's export-ready.
        """
        try:
            # Try to export (validates structure)
            export = DiagnosisExport.from_investigation(investigation)
            export_dict = export.to_dict()
        except ValueError:
            # If not export-ready, store raw structure
            export_dict = {
                "id": str(investigation.id),
                "title": investigation.title,
                "status": investigation.status.value,
                "root_cause": investigation.root_cause,
                "engineer_confirmed": investigation.engineer_confirmed,
                "symptom": {
                    "what_is_wrong": investigation.symptom.what_is_wrong,
                    "expected": investigation.symptom.expected_behaviour,
                    "actual": investigation.symptom.actual_behaviour,
                    "scope": investigation.symptom.affected_scope
                }
            }
        
        return json.dumps(export_dict, default=str)

    @staticmethod
    def _deserialize_investigation(json_str: str) -> Optional[Investigation]:
        """Deserialize Investigation from JSON string.
        
        Note: This is lossy — we can reconstruct the summary but not rebuild
        the full Investigation object from the export format. For now, this
        returns None; full deserialization requires a data migration.
        """
        try:
            data = json.loads(json_str)
            # For now, we just parse the JSON for display in search results.
            # Full Investigation reconstruction would require storing the
            # raw dataclass structure, not just the export format.
            return None
        except json.JSONDecodeError:
            return None
