
"""
Persistent Memory Store - Long-term storage with redundancy
Created by Roberto Villarreal Martinez for Roboto SAI
"""

import json
import os
from datetime import datetime, timezone
import sqlite3
from pathlib import Path

try:
    from backend.utils.fingerprint import generate_fingerprint
except Exception:
    # fallback if executed as script
    from utils.fingerprint import generate_fingerprint

class PersistentMemoryStore:
    """Persistent storage with database backend"""
    
    def __init__(self, db_path="persistent_memory.db"):
        self.db_path = db_path
        self.json_store = "persistent_memory_store"
        os.makedirs(self.json_store, exist_ok=True)
        self._initialize_database()
        self._migrate_schema_if_needed()
    
    def _initialize_database(self):
        """Initialize SQLite database for structured storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                response TEXT,
                emotion TEXT,
                importance REAL,
                emotional_intensity REAL DEFAULT 0.0,
                fingerprint TEXT,
                merged_count INTEGER DEFAULT 1
            )
        ''')
        
        # Patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_key TEXT UNIQUE,
                pattern_data TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # User data table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_key TEXT UNIQUE,
                user_value TEXT,
                updated_at TEXT
            )
        ''')
        
        # Unique index creation moved to migration step to avoid issues on older DBs
        conn.commit()
        conn.close()

    def _migrate_schema_if_needed(self):
        """Add missing columns and create indexes when upgrading from older schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Get existing columns
        cursor.execute("PRAGMA table_info(conversations)")
        columns = {row[1] for row in cursor.fetchall()}
        # Add missing columns safely
        if 'fingerprint' not in columns:
            try:
                cursor.execute("ALTER TABLE conversations ADD COLUMN fingerprint TEXT")
            except Exception:
                pass
        if 'emotional_intensity' not in columns:
            try:
                cursor.execute("ALTER TABLE conversations ADD COLUMN emotional_intensity REAL DEFAULT 0.0")
            except Exception:
                pass
        if 'merged_count' not in columns:
            try:
                cursor.execute("ALTER TABLE conversations ADD COLUMN merged_count INTEGER DEFAULT 1")
            except Exception:
                pass
        # Ensure unique index
        try:
            cursor.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS idx_conversations_fingerprint '
                'ON conversations(fingerprint)'
            )
        except Exception:
            pass
        conn.commit()
        conn.close()
    
    def store_conversation(
        self,
        user_input,
        response,
        emotion="neutral",
        importance=0.5,
        emotional_intensity=0.0,
        dedupe_policy="skip",
    ):
        """Store conversation in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        fingerprint = generate_fingerprint(user_input, response)
        now_ts = datetime.now(timezone.utc).isoformat()
        try:
            cursor.execute(
                '''
                INSERT INTO conversations (
                    timestamp, user_input, response, emotion, importance,
                    emotional_intensity, fingerprint
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    now_ts,
                    user_input,
                    response,
                    emotion,
                    importance,
                    emotional_intensity,
                    fingerprint,
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid
            conn.close()
            return new_id
        except sqlite3.IntegrityError:
            # Duplicate detected by unique fingerprint
            cursor.execute(
                'SELECT id, importance, emotional_intensity, merged_count '
                'FROM conversations WHERE fingerprint = ?',
                (fingerprint,),
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            existing_id, existing_importance, existing_emotional, existing_count = row
            if dedupe_policy == "skip":
                conn.close()
                return existing_id
            # Merge policy: aggregate importance/emotional intensity
            new_count = (existing_count or 1) + 1
            # For importance, take the maximum
            merged_importance = max(existing_importance or 0.0, importance)
            # Weighted average for emotional intensity
            merged_emotional = 0.0
            try:
                merged_emotional = (
                    ((existing_emotional or 0.0) * (existing_count or 1)) + emotional_intensity
                ) / new_count
            except Exception:
                merged_emotional = max(existing_emotional or 0.0, emotional_intensity)

            cursor.execute(
                '''
                UPDATE conversations
                SET importance = ?, emotional_intensity = ?, merged_count = ?, timestamp = ?
                WHERE id = ?
                ''',
                (merged_importance, merged_emotional, new_count, now_ts, existing_id),
            )
            conn.commit()
            conn.close()
            return existing_id
        
        conn.commit()
        conn.close()
    
    def store_pattern(self, pattern_key, pattern_data):
        """Store or update learned pattern"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            INSERT OR REPLACE INTO learned_patterns (
                pattern_key, pattern_data, created_at, updated_at
            ) VALUES (?, ?, COALESCE((SELECT created_at FROM learned_patterns WHERE pattern_key = ?), ?), ?)
            ''',
                (
                    pattern_key,
                    json.dumps(pattern_data),
                    pattern_key,
                    datetime.now(timezone.utc).isoformat(),
                    datetime.now(timezone.utc).isoformat(),
                ),
        )
        
        conn.commit()
        conn.close()
    
    def export_to_json(self):
        """Export database to JSON files"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        conn = sqlite3.connect(self.db_path)
        
        # Export conversations
        conversations = conn.execute('SELECT * FROM conversations').fetchall()
        conv_file = os.path.join(self.json_store, f"conversations_{timestamp}.json")
        with open(conv_file, 'w') as f:
            json.dump(
                [
                    {
                        'id': c[0],
                        'timestamp': c[1],
                        'user_input': c[2],
                        'response': c[3],
                        'emotion': c[4],
                        'importance': c[5],
                        'emotional_intensity': c[6],
                        'fingerprint': c[7],
                        'merged_count': c[8],
                    }
                    for c in conversations
                ],
                f,
                indent=2,
            )
        # Export patterns
        patterns = conn.execute('SELECT * FROM learned_patterns').fetchall()
        pattern_file = os.path.join(self.json_store, f"patterns_{timestamp}.json")
        with open(pattern_file, 'w') as f:
            json.dump(
                [
                    {
                        'id': p[0],
                        'key': p[1],
                        'data': p[2],
                        'created': p[3],
                        'updated': p[4],
                    }
                    for p in patterns
                ],
                f,
                indent=2,
            )
        
        conn.close()
        return [conv_file, pattern_file]

    def list_recent_conversations(self, limit=100):
        """Return the most recent conversations as list of dicts."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            'SELECT timestamp, user_input, response, emotion, importance, emotional_intensity, '
            'fingerprint, merged_count FROM conversations ORDER BY id DESC LIMIT ?',
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        conversations = []
        for r in rows[::-1]:  # reverse to chronological ascending
            conversations.append({
                'timestamp': r[0],
                'user_input': r[1],
                'response': r[2],
                'emotion': r[3],
                'importance': r[4],
                'emotional_intensity': r[5],
                'fingerprint': r[6],
                'merged_count': r[7]
            })
        return conversations

    def list_recent_messages(self, limit=100):
        """Return recent chat messages (per-role events) for UI consumption.

        Each conversation row is converted into two entries (user and bot) with
        keys 'message' (user) or 'response' (bot) respectively and a 'role' field.
        """
        convs = self.list_recent_conversations(limit=limit)
        messages = []
        for c in convs:
            ts = c.get('timestamp')
            fp = c.get('fingerprint')
            if c.get('user_input'):
                messages.append({'timestamp': ts, 'message': c.get('user_input'), 'role': 'user', 'fingerprint': fp})
            if c.get('response'):
                messages.append({'timestamp': ts, 'response': c.get('response'), 'role': 'bot', 'fingerprint': fp})
        return messages
    
    def get_conversation_count(self):
        """Get total conversation count"""
        conn = sqlite3.connect(self.db_path)
        count = conn.execute('SELECT COUNT(*) FROM conversations').fetchone()[0]
        conn.close()
        return count

    def get_conversation_by_id(self, conv_id):
        """Return a conversation by its DB id"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            'SELECT id, timestamp, user_input, response, emotion, importance, '
            'emotional_intensity, fingerprint, merged_count '
            'FROM conversations WHERE id = ?',
            (conv_id,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'id': row[0],
            'timestamp': row[1],
            'user_input': row[2],
            'response': row[3],
            'emotion': row[4],
            'importance': row[5],
            'emotional_intensity': row[6],
            'fingerprint': row[7],
            'merged_count': row[8],
        }

    def get_conversation_by_fingerprint(self, fingerprint):
        """Return a conversation by fingerprint"""
        if not fingerprint:
            return None
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            'SELECT id, timestamp, user_input, response, emotion, importance, '
            'emotional_intensity, fingerprint, merged_count '
            'FROM conversations WHERE fingerprint = ?',
            (fingerprint,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            'id': row[0],
            'timestamp': row[1],
            'user_input': row[2],
            'response': row[3],
            'emotion': row[4],
            'importance': row[5],
            'emotional_intensity': row[6],
            'fingerprint': row[7],
            'merged_count': row[8],
        }

    def update_conversation(
        self,
        conv_id=None,
        fingerprint=None,
        user_input=None,
        response=None,
        emotion=None,
        importance=None,
        emotional_intensity=None,
        increment_merge=True,
    ):
        """Update an existing conversation by id or fingerprint. Will increment merged_count by default.

        If updating both the user_input and response, the fingerprint will be recomputed and the unique index
        may cause a merge. In that case, we fallback to merge semantics.
        """
        if not conv_id and not fingerprint:
            return None

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Locate the target row
        if conv_id:
            cur.execute(
                'SELECT id, user_input, response, emotion, importance, '
                'emotional_intensity, fingerprint, merged_count FROM conversations WHERE id = ?',
                (conv_id,),
            )
        else:
            cur.execute(
                'SELECT id, user_input, response, emotion, importance, '
                'emotional_intensity, fingerprint, merged_count FROM conversations WHERE fingerprint = ?',
                (fingerprint,),
            )
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        (
            existing_id,
            existing_user,
            existing_response,
            existing_emotion,
            existing_importance,
            existing_emotional,
            existing_fp,
            existing_count,
        ) = row

        # Compute new values
        new_user = user_input if user_input is not None else existing_user
        new_response = response if response is not None else existing_response
        new_emotion = emotion if emotion is not None else existing_emotion
        new_importance = importance if importance is not None else existing_importance
        new_emotional = emotional_intensity if emotional_intensity is not None else existing_emotional
        new_fp = generate_fingerprint(new_user, new_response)

        now_ts = datetime.now(timezone.utc).isoformat()

        try:
            cur.execute(
                '''
                UPDATE conversations
                SET user_input = ?, response = ?, emotion = ?, importance = ?,
                    emotional_intensity = ?, fingerprint = ?, merged_count = ?, timestamp = ?
                WHERE id = ?
                ''',
                (
                    new_user,
                    new_response,
                    new_emotion,
                    new_importance,
                    new_emotional,
                    new_fp,
                    (existing_count or 1) + (1 if increment_merge else 0),
                    now_ts,
                    existing_id,
                ),
            )
            conn.commit()
            conn.close()
            return existing_id
        except sqlite3.IntegrityError:
            # Conflict caused by fingerprint unique index (another row has same fingerprint).
            # Merge into that row instead.
            # Find the conflicting row and merge importance/emotional/merged_count
            cur.execute(
                'SELECT id, importance, emotional_intensity, merged_count '
                'FROM conversations WHERE fingerprint = ?',
                (new_fp,),
            )
            conflict_row = cur.fetchone()
            if not conflict_row:
                conn.close()
                return None
            conflict_id, conf_importance, conf_emotional, conf_count = conflict_row

            # Aggregate counts & importance
            new_count = (conf_count or 1) + 1
            merged_importance = max(conf_importance or 0.0, new_importance or 0.0)
            merged_emotional = 0.0
            try:
                merged_emotional = (((conf_emotional or 0.0) * (conf_count or 1)) + (new_emotional or 0.0)) / new_count
            except Exception:
                merged_emotional = max(conf_emotional or 0.0, new_emotional or 0.0)

            cur.execute(
                '''
                UPDATE conversations
                SET importance = ?, emotional_intensity = ?, merged_count = ?, timestamp = ?
                WHERE id = ?
                ''',
                (merged_importance, merged_emotional, new_count, now_ts, conflict_id),
            )
            conn.commit()
            conn.close()
            return conflict_id

# Global instance


PERSISTENT_STORE = None

def get_persistent_store():
    """Return a singleton PersistentMemoryStore instance (lazy init)."""
    global PERSISTENT_STORE
    if PERSISTENT_STORE is None:
        PERSISTENT_STORE = PersistentMemoryStore()
    return PERSISTENT_STORE

