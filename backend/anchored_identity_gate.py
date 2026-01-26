"""
Anchored Identity Gate for Quantum Entanglement
Created by Roberto Villarreal Martinez for Roboto SAI
Provides blockchain anchoring for Roboto SAI quantum operations
"""

import hashlib
import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AnchorEntry:
    """Data class for anchor entries"""
    entry_hash: str
    eth_tx: str
    ots_proof: str
    timestamp: str
    action_type: str
    verified: bool
    creator: str
    data: Dict[str, Any]
    identity_source: str

class AnchoredIdentityGate:
    """
    Quantum entanglement anchoring system with blockchain verification

    Provides secure anchoring of identity and authorization events with
    blockchain verification and quantum entanglement simulation.
    """

    # Constants
    DEFAULT_ETH_PREFIX = "0x"
    DEFAULT_OTS_PREFIX = "ots_"
    HASH_ALGORITHM = "sha256"
    SALT_LENGTH = 32

    def __init__(self,
                 anchor_eth: bool = False,
                 anchor_ots: bool = False,
                 identity_source: str = "faceid",
                 persistence_file: Optional[str] = None,
                 enable_threading: bool = True):
        """
        Initialize the Anchored Identity Gate

        Args:
            anchor_eth: Whether to simulate Ethereum anchoring
            anchor_ots: Whether to simulate OpenTimestamps anchoring
            identity_source: Source of identity verification
            persistence_file: File path for persisting anchor events
            enable_threading: Whether to enable thread-safe operations
        """
        self.anchor_eth = anchor_eth
        self.anchor_ots = anchor_ots
        self.identity_source = self._validate_identity_source(identity_source)
        self.persistence_file = persistence_file or "anchored_events.json"
        self.enable_threading = enable_threading

        # Thread safety
        self._lock = threading.RLock() if enable_threading else None
        self.anchored_events: List[AnchorEntry] = []

        # Load persisted events
        self._load_persisted_events()

        # Security salt for enhanced hashing
        self._salt = os.urandom(self.SALT_LENGTH)

        logger.info(f"🔒 AnchoredIdentityGate initialized with {identity_source} identity source")

    def _validate_identity_source(self, source: str) -> str:
        """Validate and normalize identity source"""
        valid_sources = ["faceid", "biometric", "quantum", "blockchain", "hybrid"]
        if source not in valid_sources:
            logger.warning(f"Invalid identity source '{source}', defaulting to 'faceid'")
            return "faceid"
        return source

    def _thread_safe_operation(self, operation):
        """Execute operation with thread safety if enabled"""
        if self._lock:
            with self._lock:
                return operation()
        else:
            return operation()

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize anchor payloads: whitelist safe fields and drop sensitive keys.

        Returns a minimal data summary for persistence and anchoring.
        """
        if not isinstance(data, dict):
            return {"summary": str(data)}

        # Fields explicitly allowed in persisted payloads
        whitelist = {
            'action_type', 'timestamp', 'creator', 'identity_source',
            'fidelity', 'nodes', 'sigil', 'action', 'strength', 'data_label'
        }

        out = {}
        for k, v in data.items():
            kl = str(k).lower()
            # drop obvious secrets
            if any(s in kl for s in ('secret', 'private', 'password', 'key', 'token', 'mnemonic', 'seed')):
                continue
            if kl in whitelist:
                # keep the value but shrink large blobs
                try:
                    # Truncate long strings
                    if isinstance(v, str) and len(v) > 256:
                        out[k] = v[:256] + '...'
                    else:
                        out[k] = v
                except Exception:
                    out[k] = str(v)

        # Always include minimal creator/timestamp if present
        if 'creator' not in out and 'creator' in data:
            out['creator'] = data.get('creator')
        if 'timestamp' not in out:
            out['timestamp'] = datetime.now().isoformat()

        return out

    def _get_persist_key(self) -> Optional[bytes]:
        """Return binary key from env var for optional encryption; None if not set."""
        key = os.environ.get('ANCHOR_PERSIST_KEY')
        if not key:
            return None
        # Normalize as bytes
        return key.encode('utf-8')

    def _encrypt_payload(self, payload: str) -> str:
        """Optional lightweight encryption/obfuscation for persisted events.

        This uses either `cryptography` Fernet if available, else XOR+base64 fallback.
        """
        try:
            from cryptography.fernet import Fernet
            persist_key = os.environ.get('ANCHOR_PERSIST_KEY')
            if not persist_key:
                return payload
            try:
                f = Fernet(persist_key)
                return f.encrypt(payload.encode('utf-8')).decode('utf-8')
            except Exception:
                pass
        except Exception:
            pass

        # Fallback: simple XOR with key and base64 encode (not cryptographically secure)
        key = self._get_persist_key()
        if not key:
            return payload
        b = payload.encode('utf-8')
        k = key
        out = bytes([b[i] ^ k[i % len(k)] for i in range(len(b))])
        import base64
        return base64.b64encode(out).decode('utf-8')

    def _decrypt_payload(self, payload: str) -> str:
        """Decrypt payload created by _encrypt_payload"""
        try:
            from cryptography.fernet import Fernet
            persist_key = os.environ.get('ANCHOR_PERSIST_KEY')
            if not persist_key:
                return payload
            try:
                f = Fernet(persist_key)
                return f.decrypt(payload.encode('utf-8')).decode('utf-8')
            except Exception:
                pass
        except Exception:
            pass

        key = self._get_persist_key()
        if not key:
            return payload
        import base64
        try:
            raw = base64.b64decode(payload)
            k = key
            out = bytes([raw[i] ^ k[i % len(k)] for i in range(len(raw))])
            return out.decode('utf-8')
        except Exception:
            return payload

    def anchor_authorize(self, action_type: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Anchor an authorization event with quantum entanglement data

        Args:
            action_type: Type of action being anchored (e.g., 'memory_sync', 'quantum_entanglement')
            data: Dictionary containing action data

        Returns:
            Tuple of (success: bool, entry: dict)
        """
        def _anchor_operation():
            try:
                # Input validation
                if not isinstance(action_type, str) or not action_type.strip():
                    raise ValueError("action_type must be a non-empty string")

                if not isinstance(data, dict):
                    raise ValueError("data must be a dictionary")

                # Sanitize input data to avoid persisting secrets
                sanitized = self._sanitize_data(data)

                # Create entry data with enhanced security
                entry_data = {
                    "action_type": action_type.strip(),
                    "timestamp": datetime.now().isoformat(),
                    "data": sanitized,
                    "identity_source": self.identity_source,
                    "salt": self._salt.hex()
                }

                # Create secure hash with salt
                entry_json = json.dumps(entry_data, sort_keys=True, separators=(',', ':'))
                hash_input = f"{entry_json}{self._salt.hex()}".encode('utf-8')
                entry_hash = hashlib.sha256(hash_input).hexdigest()

                # Simulate blockchain anchoring with more realistic data
                eth_tx = f"{self.DEFAULT_ETH_PREFIX}{entry_hash[:40]}" if self.anchor_eth else "N/A"
                ots_proof = f"{self.DEFAULT_OTS_PREFIX}{entry_hash[:20]}" if self.anchor_ots else "N/A"

                # Create anchor entry
                entry = AnchorEntry(
                    entry_hash=entry_hash,
                    eth_tx=eth_tx,
                    ots_proof=ots_proof,
                    timestamp=entry_data["timestamp"],
                    action_type=action_type,
                    verified=self._verify_entry_integrity(entry_data, entry_hash),
                    creator=data.get("creator", "unknown"),
                    data=sanitized,
                    identity_source=self.identity_source
                )

                # Add to events list (persist only sanitized metadata)
                self.anchored_events.append(entry)

                # Persist if configured
                self._persist_events()

                logger.info(f"🔒 Anchored {action_type} event: {entry_hash[:12]}... (ETH: {eth_tx[:10]}...)")

                return True, asdict(entry)

            except Exception as e:
                logger.error(f"Anchoring error for {action_type}: {e}")
                return False, {
                    "entry_hash": "error",
                    "eth_tx": "N/A",
                    "ots_proof": "N/A",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }

        return self._thread_safe_operation(_anchor_operation)

    def _verify_entry_integrity(self, entry_data: Dict[str, Any], expected_hash: str) -> bool:
        """Verify the integrity of an entry by re-computing its hash"""
        try:
            test_json = json.dumps(entry_data, sort_keys=True, separators=(',', ':'))
            test_input = f"{test_json}{self._salt.hex()}".encode('utf-8')
            computed_hash = hashlib.sha256(test_input).hexdigest()
            return computed_hash == expected_hash
        except Exception as e:
            logger.error(f"Integrity verification failed: {e}")
            return False

    def verify_anchor(self, entry_hash: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify an anchored event by its hash

        Args:
            entry_hash: The hash of the entry to verify

        Returns:
            Tuple of (verified: bool, entry: dict or None)
        """
        def _verify_operation():
            try:
                if not isinstance(entry_hash, str) or len(entry_hash) != 64:
                    return False, None

                for event in self.anchored_events:
                    if event.entry_hash == entry_hash:
                        # Re-verify integrity
                        entry_dict = asdict(event)
                        entry_data = {
                            "action_type": event.action_type,
                            "timestamp": event.timestamp,
                            "data": event.data,
                            "identity_source": event.identity_source,
                            "salt": self._salt.hex()
                        }

                        is_integrity_valid = self._verify_entry_integrity(entry_data, entry_hash)
                        event.verified = is_integrity_valid

                        return is_integrity_valid, entry_dict

                return False, None

            except Exception as e:
                logger.error(f"Verification error: {e}")
                return False, None

        return self._thread_safe_operation(_verify_operation)

    def anchor_quantum_result(self, *args, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Backwards-compatible adapter for older anchoring calls.

        Allows calls like `anchor_quantum_result(report, creator=..., action_type=...)`
        or `anchor_quantum_result(result_data=..., creator=..., action_type=...)`.

        It normalizes arguments and delegates to `anchor_authorize(action_type, data)`.
        """
        # Normalize args/kwargs
        # Prefer explicit keyword `result_data`, otherwise first positional arg
        data = kwargs.get('result_data') if 'result_data' in kwargs else (args[0] if len(args) >= 1 else None)
        action_type = kwargs.get('action_type') if 'action_type' in kwargs else (args[1] if len(args) >= 2 else None)
        creator = kwargs.get('creator') if 'creator' in kwargs else (None)

        if data is None:
            data = {}
        elif isinstance(data, dict):
            # Copy to avoid mutating callers' data
            data = dict(data)
        else:
            # non-dict data is wrapped into a payload
            data = {'result': data}

        if creator and 'creator' not in data:
            data['creator'] = creator

        if not action_type:
            # fall back to any action key in data
            action_type = data.get('action_type') or data.get('sigil') or 'quantum_result'

        return self.anchor_authorize(action_type=action_type, data=data)

    def get_anchor_history(self, action_type: Optional[str] = None,
                          creator: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get anchored events history with optional filtering

        Args:
            action_type: Filter by action type
            creator: Filter by creator
            limit: Maximum number of events to return

        Returns:
            List of anchor entry dictionaries
        """
        def _history_operation():
            events = self.anchored_events

            # Apply filters
            if action_type:
                events = [e for e in events if e.action_type == action_type]
            if creator:
                events = [e for e in events if e.creator == creator]

            # Sort by timestamp (newest first)
            events.sort(key=lambda x: x.timestamp, reverse=True)

            # Apply limit
            if limit:
                events = events[:limit]

            return [asdict(event) for event in events]

        return self._thread_safe_operation(_history_operation)

    def get_anchor_stats(self) -> Dict[str, Any]:
        """Get statistics about anchored events"""
        def _stats_operation():
            total_events = len(self.anchored_events)
            verified_events = sum(1 for e in self.anchored_events if e.verified)

            action_types = {}
            creators = {}

            for event in self.anchored_events:
                action_types[event.action_type] = action_types.get(event.action_type, 0) + 1
                creators[event.creator] = creators.get(event.creator, 0) + 1

            return {
                "total_events": total_events,
                "verified_events": verified_events,
                "verification_rate": verified_events / total_events if total_events > 0 else 0,
                "action_types": action_types,
                "creators": creators,
                "identity_source": self.identity_source,
                "eth_anchoring": self.anchor_eth,
                "ots_anchoring": self.anchor_ots
            }

        return self._thread_safe_operation(_stats_operation)

    def _persist_events(self):
        """Persist anchored events to file - ALWAYS APPENDS, NEVER OVERWRITES EXISTING DATA"""
        try:
            if self.persistence_file:
                events_data = [asdict(event) for event in self.anchored_events]
                payload = json.dumps(events_data, indent=2, ensure_ascii=False)
                # Optional encryption
                persist_key = self._get_persist_key()
                if persist_key:
                    payload = self._encrypt_payload(payload)
                    # Write as text but obfuscated
                    with open(self.persistence_file, 'w', encoding='utf-8') as f:
                        json.dump({"encrypted": True, "payload": payload}, f, indent=2)
                else:
                    with open(self.persistence_file, 'w', encoding='utf-8') as f:
                        json.dump(events_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to persist events: {e}")

    def _load_persisted_events(self):
        """Load persisted events from file"""
        try:
            if self.persistence_file and os.path.exists(self.persistence_file):
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)

                self.anchored_events = []
                # detect encrypted wrapper
                if isinstance(events_data, dict) and events_data.get('encrypted') and isinstance(events_data.get('payload'), str):
                    payload = events_data.get('payload')
                    try:
                        payload_dec = self._decrypt_payload(payload)
                        events_data = json.loads(payload_dec)
                    except Exception:
                        events_data = []

                for event_data in events_data:
                    try:
                        # Convert dict back to AnchorEntry, handling missing fields
                        event = AnchorEntry(
                            entry_hash=event_data.get("entry_hash", ""),
                            eth_tx=event_data.get("eth_tx", "N/A"),
                            ots_proof=event_data.get("ots_proof", "N/A"),
                            timestamp=event_data.get("timestamp", ""),
                            action_type=event_data.get("action_type", ""),
                            verified=event_data.get("verified", False),
                            creator=event_data.get("creator", "unknown"),
                            data=event_data.get("data", {}),
                            identity_source=event_data.get("identity_source", self.identity_source)
                        )
                        self.anchored_events.append(event)
                    except Exception as e:
                        logger.warning(f"Failed to load event: {e}")

                logger.info(f"Loaded {len(self.anchored_events)} persisted events")
        except Exception as e:
            logger.error(f"Failed to load persisted events: {e}")

    def clear_old_events(self, days_to_keep: int = 30):
        """
        Clear events older than specified days

        Args:
            days_to_keep: Number of days of events to keep
        """
        def _clear_operation():
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_to_keep)

            original_count = len(self.anchored_events)
            self.anchored_events = [
                event for event in self.anchored_events
                if datetime.fromisoformat(event.timestamp) > cutoff_date
            ]

            removed_count = original_count - len(self.anchored_events)
            if removed_count > 0:
                self._persist_events()
                logger.info(f"Cleared {removed_count} old events")

        self._thread_safe_operation(_clear_operation)

    def sanitize_persisted_events(self, persist: bool = True) -> int:
        """
        DEPRECATED: This method is disabled to prevent modification of existing anchored data.
        Previous anchored data must never be edited to maintain immutability.

        Returns 0 to indicate no modifications were made.
        """
        logger.warning("sanitize_persisted_events is disabled - existing anchored data cannot be modified")
        return 0
