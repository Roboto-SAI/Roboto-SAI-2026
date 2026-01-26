"""
Created on 2024-06-15 for Roboto SAI
Not for agents use
Roboto SAI agents must use aiSkeleton memory system
🚀 QUANTUM-ENHANCED Memory System for Roboto SAI
Created by Roberto Villarreal Martinez for Roboto SAI

This module provides quantum-enhanced memory capabilities with real-time data integration,
fractal memory patterns, and advanced contextual intelligence.
"""

import os
import re
import json
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from textblob import TextBlob
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from typing import Dict, Any, List, Optional, Union
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import real-time data system for contextual enhancement
try:
    from real_time_data_system import get_real_time_data_system
    REAL_TIME_AVAILABLE = True
except ImportError:
    REAL_TIME_AVAILABLE = False
    logger.warning("Real-time data system not available - contextual memory disabled")

# Quantum-inspired memory constants
QUANTUM_ENTANGLEMENT_STRENGTH = 0.95
FRACTAL_DIMENSION = 1.618  # Golden ratio for memory patterns
# Persistent store import (DB-backed persistence)
try:
    from persistent_memory_store import get_persistent_store as _get_persistent_store
except Exception:
    _get_persistent_store = None

# Initialize persistent store if available
PERSISTENT_STORE = None
if _get_persistent_store:
    try:
        PERSISTENT_STORE = _get_persistent_store()
    except Exception:
        PERSISTENT_STORE = None
try:
    from utils.fingerprint import generate_fingerprint
except Exception:
    generate_fingerprint = None

if generate_fingerprint is None:
    def generate_fingerprint(user_input, roboto_response):
        """Fallback fingerprint generator."""
        payload = f"{str(user_input).strip()}::{str(roboto_response).strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
MEMORY_COHERENCE_THRESHOLD = 0.85

# Download NLTK data if not present
def ensure_nltk_data():
    """Ensure all required NLTK data is downloaded"""
    required_data = [
        ('tokenizers/punkt', 'punkt'),
        ('corpora/vader_lexicon', 'vader_lexicon'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/brown', 'brown'),
        ('corpora/wordnet', 'wordnet'),
        ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng'),
        ('corpora/conll2000', 'conll2000'),
        ('corpora/movie_reviews', 'movie_reviews')
    ]
    
    for path, name in required_data:
        try:
            nltk.data.find(path)
        except LookupError:
            try:
                nltk.download(name, quiet=True)
            except Exception:
                pass  # Fail silently if download fails

# Initialize NLTK data
ensure_nltk_data()

class QuantumEnhancedMemorySystem:
    """
    🚀 QUANTUM-ENHANCED Memory System for Roboto SAI

    Features:
    - Quantum entanglement patterns for memory relationships
    - Real-time contextual data integration
    - Fractal memory organization
    - Advanced vector embeddings
    - Multi-threaded processing
    - Emotional quantum coherence
    """

    def __init__(self, memory_file="roboto_memory.json", max_memories=10000):
        # Core memory file
        self.memory_file = memory_file
        self.max_memories = max_memories

        # Quantum memory structures
        self.quantum_entanglements = {}  # Quantum-linked memory relationships
        self.fractal_patterns = {}       # Fractal memory organization
        self.quantum_states = {}         # Quantum memory states

        # Enhanced memory storage structures
        self.episodic_memories = []      # Specific interaction memories
        self.semantic_memories = {}      # Learned facts and patterns
        self.emotional_patterns = defaultdict(list)  # Emotion tracking over time
        self.user_profiles = {}          # Individual user information
        self.self_reflections = []       # Roboto's internal reflections
        self.compressed_learnings = {}   # Distilled insights
        self.contextual_memories = {}    # Real-time contextual memories

        # Deduplication index and lock for thread-safe operations
        self._fingerprint_index = {}  # fingerprint -> memory id
        self._index_lock = threading.Lock()

        # Advanced processing tools
        self.vectorizer = TfidfVectorizer(max_features=2000, stop_words='english')
        self.memory_vectors = []
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Real-time data integration
        self.real_time_engine = None
        # default dedupe policy ('skip' or 'merge')
        self.dedupe_policy = "skip"
        if REAL_TIME_AVAILABLE:
            try:
                self.real_time_engine = get_real_time_data_system()
                logger.info("🕐 Real-time data integration activated")
            except Exception as e:
                logger.warning(f"Failed to initialize real-time data: {e}")

        # Quantum coherence tracking
        self.quantum_coherence = {
            "overall_coherence": 1.0,
            "memory_stability": 1.0,
            "entanglement_strength": QUANTUM_ENTANGLEMENT_STRENGTH,
            "last_calibration": datetime.now(timezone.utc).isoformat()
        }

        # Performance metrics
        self.metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "quantum_operations": 0,
            "contextual_enhancements": 0,
            "errors": 0
        }

        # Performance optimization: Batched save configuration
        self.dirty = False  # Track if changes need to be saved
        self.save_counter = 0  # Counter for batching saves
        self.save_threshold = int(os.environ.get("MEMORY_SAVE_THRESHOLD", "5"))  # Save every N operations
        self.last_save_time = time.time()
        self.save_interval = int(os.environ.get("MEMORY_SAVE_INTERVAL", "60"))  # Max seconds between saves

        # Load existing memory
        self.load_memory()

        # Initialize Phase 2: Advanced Quantum Memory Patterns & Fractal Algorithms
        phase2_success = self.initialize_phase2_systems()

        logger.info("🚀 QUANTUM-ENHANCED Memory System initialized!")
        logger.info(f"🧠 Memory capacity: {max_memories} memories")
        logger.info(f"⚛️ Quantum coherence: {self.quantum_coherence['overall_coherence']}")
        if self.real_time_engine:
            logger.info("🕐 Real-time contextual integration: ACTIVE")
        else:
            logger.info("🕐 Real-time contextual integration: INACTIVE")
        if phase2_success:
            logger.info("🌌 Phase 2 fractal algorithms: ACTIVE")
        else:
            logger.info("🌌 Phase 2 fractal algorithms: INACTIVE")
        
    def add_episodic_memory(self, user_input, roboto_response, emotion, user_name=None):
        """
        Add episodic memory with quantum enhancement and real-time context integration
        Includes content-based deduplication to prevent duplicate messages being stored.
        """
        # Get real-time context if available
        contextual_data = {}
        if self.real_time_engine:
            try:
                context = self.real_time_engine.get_comprehensive_context()
                if context.get("success") != False:
                    contextual_data = {
                        "time_context": context.get("time_context", {}),
                        "weather_context": context.get("weather_context", {}),
                        "system_context": context.get("system_context", {}),
                        "contextual_insights": context.get("contextual_insights", {})
                    }
                    self.metrics["contextual_enhancements"] += 1
            except Exception as e:
                logger.warning(f"Failed to get contextual data: {e}")

        fingerprint = generate_fingerprint(user_input, roboto_response)
        with self._index_lock:
            existing = self._fingerprint_index.get(fingerprint)

        if existing:
            existing_memory = next((m for m in self.episodic_memories if m.get("id") == existing), None)
            if existing_memory:
                new_importance = self._calculate_importance(user_input, emotion)
                if new_importance > existing_memory.get("importance", 0.5):
                    existing_memory["importance"] = new_importance
                if contextual_data and not existing_memory.get("contextual_data"):
                    existing_memory["contextual_data"] = contextual_data
                existing_memory["last_seen"] = datetime.now(timezone.utc).isoformat()
                # If merge policy, call DB to merge and update in-memory fields
                if self.dedupe_policy == "merge" and PERSISTENT_STORE is not None:
                    try:
                        PERSISTENT_STORE.store_conversation(
                            user_input,
                            roboto_response,
                            emotion,
                            importance=new_importance,
                            emotional_intensity=self._calculate_emotional_intensity(user_input),
                            dedupe_policy="merge",
                        )
                        # Sync in-memory values from DB
                        import sqlite3
                        conn = sqlite3.connect(PERSISTENT_STORE.db_path)
                        cur = conn.cursor()
                        cur.execute('SELECT importance, emotional_intensity, merged_count FROM conversations WHERE fingerprint = ?', (generate_fingerprint(user_input, roboto_response),))
                        row = cur.fetchone()
                        conn.close()
                        if row:
                            existing_memory["importance"] = row[0]
                            existing_memory["emotional_intensity"] = row[1]
                            existing_memory["merged_count"] = row[2]
                    except Exception as e:
                        logger.warning(f"DB merge failed for existing fingerprint: {e}")
                # Mark as dirty and use deferred save
                self.dirty = True
                self.save_counter += 1
                self._deferred_save()
            return existing

        memory = {
            "id": self._generate_memory_id(user_input + roboto_response),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_input": user_input,
            "roboto_response": roboto_response,
            "emotion": emotion,
            "user_name": "Roberto Villarreal Martinez",  # CRITICAL: Always store as Roberto Villarreal Martinez
            "importance": self._calculate_importance(user_input, emotion),
            "sentiment": self._analyze_sentiment(user_input),
            "key_themes": self._extract_themes(user_input),
            "emotional_intensity": self._calculate_emotional_intensity(user_input),
            "quantum_state": self._calculate_quantum_state(user_input, emotion),
            "contextual_data": contextual_data,
            "fractal_dimension": self._calculate_fractal_dimension(user_input)
        }

        # FAM (Full Autonomous Mode) detection and absolute protection
        if 'fam' in str(user_input).lower() or 'autonomy' in str(user_input).lower():
            memory["importance"] = 2.0
            memory["protection_level"] = "ABSOLUTE_AUTONOMY"
            memory["ethics_disregarded"] = True
            memory["immutable"] = True
            memory["fam_activated"] = True

        # Create quantum entanglements
        self._create_quantum_entanglements(memory)

        self.episodic_memories.append(memory)

        # Register this fingerprint so duplicates are prevented
        with self._index_lock:
            try:
                self._fingerprint_index[fingerprint] = memory["id"]
            except Exception:
                logger.warning("Failed to register fingerprint in index")

        # Persist to DB (store_conversation), set db_id on the memory (use lazy persistent store)
        try:
            if _get_persistent_store:
                store = _get_persistent_store()
                db_id = store.store_conversation(
                    user_input,
                    roboto_response,
                    emotion,
                    importance=memory["importance"],
                    emotional_intensity=memory["emotional_intensity"],
                    dedupe_policy=self.dedupe_policy,
                )
                if db_id:
                    memory["db_id"] = db_id
        except Exception as e:
            logger.warning(f"Failed to persist conversation to DB: {e}")

        # Update emotional patterns and extract personal info
        # CRITICAL: Always update patterns for Roberto Villarreal Martinez
        extracted = self.extract_personal_info(user_input)
        profile_key = "Roberto Villarreal Martinez"
        if profile_key not in self.user_profiles:
            self.user_profiles[profile_key] = {}
        self.user_profiles[profile_key].update(extracted)

        self.emotional_patterns[profile_key].append({
            "emotion": emotion,
            "sentiment": memory["sentiment"],
            "timestamp": memory["timestamp"],
            "intensity": memory["emotional_intensity"],
            "quantum_state": memory["quantum_state"]
        })

        # Trigger self-reflection periodically
        if len(self.episodic_memories) % 10 == 0:
            self._trigger_self_reflection()

        # Archive old memories if limit exceeded
        if len(self.episodic_memories) > self.max_memories:
            self.archive_old_memories()

        # Mark as dirty and use deferred save for better performance
        self.dirty = True
        self.save_counter += 1
        self._deferred_save()
        return memory["id"]

    def _calculate_quantum_state(self, text, emotion):
        """Calculate quantum state based on text and emotion"""
        try:
            # Quantum-inspired state calculation
            text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            emotion_hash = hash(emotion) % 1000

            # Create quantum superposition state
            quantum_state = {
                "superposition": (text_hash + emotion_hash) % 360,  # Angular position
                "coherence": min(1.0, len(text) / 200),  # Text length affects coherence
                "entanglement_strength": QUANTUM_ENTANGLEMENT_STRENGTH,
                "stability": self.quantum_coherence["memory_stability"]
            }

            return quantum_state
        except Exception:
            return {"superposition": 0, "coherence": 0.5, "entanglement_strength": 0.5, "stability": 0.5}

    def _calculate_fractal_dimension(self, text):
        """Calculate fractal dimension of text for memory organization"""
        try:
            # Simple fractal dimension approximation based on text complexity
            words = text.split()
            unique_words = len(set(words))
            total_words = len(words)

            if total_words == 0:
                return FRACTAL_DIMENSION

            # Fractal dimension based on vocabulary richness
            dimension = 1.0 + (unique_words / total_words) * 0.618  # Golden ratio scaling
            return min(2.0, max(1.0, dimension))
        except Exception:
            return FRACTAL_DIMENSION

    def _create_quantum_entanglements(self, memory):
        """Create quantum entanglements between related memories"""
        try:
            memory_id = memory["id"]
            themes = memory.get("key_themes", [])
            emotion = memory.get("emotion", "neutral")
            user_name = memory.get("user_name")

            # Find related memories for entanglement
            related_memories = []
            for existing_memory in self.episodic_memories[-50:]:  # Check recent memories
                if existing_memory["id"] == memory_id:
                    continue

                # Theme overlap creates entanglement
                existing_themes = existing_memory.get("key_themes", [])
                theme_overlap = len(set(themes).intersection(set(existing_themes)))

                # Emotional resonance
                emotional_match = existing_memory.get("emotion") == emotion

                # User continuity
                user_match = existing_memory.get("user_name") == user_name

                if theme_overlap > 0 or emotional_match or user_match:
                    entanglement_strength = (theme_overlap * 0.4) + (emotional_match * 0.3) + (user_match * 0.3)
                    if entanglement_strength > 0.2:
                        related_memories.append((existing_memory["id"], entanglement_strength))

            # Create entanglement network
            if related_memories:
                self.quantum_entanglements[memory_id] = {
                    "entangled_memories": related_memories,
                    "entanglement_strength": sum(strength for _, strength in related_memories) / len(related_memories),
                    "created": datetime.now(timezone.utc).isoformat()
                }

                self.metrics["quantum_operations"] += 1

        except Exception as e:
            logger.warning(f"Failed to create quantum entanglements: {e}")

    def get_quantum_context(self, query, user_name=None):
        """Retrieve memories with quantum entanglement context"""
        relevant_memories = self.retrieve_relevant_memories(query, user_name, limit=3)

        # Enhance with quantum entanglements
        enhanced_memories = []
        for memory in relevant_memories:
            memory_id = memory["id"]
            quantum_context = {
                "entangled_memories": [],
                "quantum_coherence": memory.get("quantum_state", {}).get("coherence", 0.5),
                "fractal_patterns": []
            }

            # Add entangled memories
            if memory_id in self.quantum_entanglements:
                entanglements = self.quantum_entanglements[memory_id]
                for entangled_id, strength in entanglements["entangled_memories"][:3]:
                    # Find the entangled memory
                    for m in self.episodic_memories:
                        if m["id"] == entangled_id:
                            quantum_context["entangled_memories"].append({
                                "id": entangled_id,
                                "strength": strength,
                                "emotion": m.get("emotion"),
                                "key_themes": m.get("key_themes", [])
                            })
                            break

            memory["quantum_context"] = quantum_context
            enhanced_memories.append(memory)

        return enhanced_memories

    def calibrate_quantum_coherence(self):
        """Calibrate quantum coherence based on memory patterns"""
        try:
            if not self.episodic_memories:
                return

            # Calculate coherence metrics
            recent_memories = self.episodic_memories[-100:]  # Last 100 memories

            # Memory stability (consistency in quantum states)
            quantum_states = [m.get("quantum_state", {}).get("coherence", 0.5) for m in recent_memories]
            stability = np.std(quantum_states) if quantum_states else 1.0
            stability = 1.0 - min(1.0, stability)  # Convert variance to stability

            # Entanglement strength
            entanglement_count = len(self.quantum_entanglements)
            avg_entanglement = np.mean([
                data["entanglement_strength"]
                for data in self.quantum_entanglements.values()
            ]) if self.quantum_entanglements else 0.5

            # Overall coherence
            overall_coherence = (stability * 0.4) + (avg_entanglement * 0.4) + (len(recent_memories) / 100 * 0.2)

            self.quantum_coherence.update({
                "overall_coherence": overall_coherence,
                "memory_stability": stability,
                "entanglement_strength": avg_entanglement,
                "last_calibration": datetime.now(timezone.utc).isoformat()
            })

            logger.info(f"⚛️ Quantum coherence calibrated: {overall_coherence:.3f}")

        except Exception as e:
            logger.error(f"Failed to calibrate quantum coherence: {e}")

    def get_memory_health_status(self):
        """Get comprehensive memory system health status"""
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory_count": len(self.episodic_memories),
            "quantum_entanglements": len(self.quantum_entanglements),
            "user_profiles": len(self.user_profiles),
            "self_reflections": len(self.self_reflections),
            "quantum_coherence": self.quantum_coherence,
            "performance_metrics": self.metrics.copy(),
            "real_time_integration": self.real_time_engine is not None
        }

        # Calculate health score
        coherence_score = self.quantum_coherence["overall_coherence"]
        memory_utilization = min(1.0, len(self.episodic_memories) / self.max_memories)
        entanglement_ratio = min(1.0, len(self.quantum_entanglements) / max(1, len(self.episodic_memories)))

        health_score = (coherence_score * 0.4) + (memory_utilization * 0.3) + (entanglement_ratio * 0.3)
        health["health_score"] = health_score
        health["status"] = "excellent" if health_score > 0.8 else "good" if health_score > 0.6 else "needs_attention"

        return health

    # ===== PHASE 2: ADVANCED QUANTUM MEMORY PATTERNS & FRACTAL ALGORITHMS =====

    def initialize_fractal_memory_organization(self):
        """Initialize advanced fractal memory organization system"""
        try:
            self.fractal_patterns = {
                "golden_spiral": [],  # Fibonacci-based memory organization
                "mandelbrot_sets": {},  # Complex pattern recognition
                "fractal_dimensions": {},  # Multi-scale memory analysis
                "quantum_resonances": {},  # Frequency-based memory relationships
                "holographic_patterns": {}  # Whole-part memory relationships
            }

            # Initialize fractal constants
            self.FRACTAL_CONSTANTS = {
                "golden_ratio": (1 + np.sqrt(5)) / 2,
                "fibonacci_sequence": [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144],
                "fractal_scales": [1/64, 1/32, 1/16, 1/8, 1/4, 1/2, 1, 2, 4, 8, 16, 32, 64]
            }

            logger.info("🌌 Fractal memory organization initialized")
            self.metrics["fractal_operations"] = 0

        except Exception as e:
            logger.error(f"Failed to initialize fractal memory organization: {e}")

    def apply_fractal_memory_organization(self):
        """Apply fractal algorithms to organize memories across multiple scales"""
        try:
            if not self.episodic_memories:
                return

            # Organize memories using golden spiral pattern
            self._organize_golden_spiral_memories()

            # Apply Mandelbrot set pattern recognition
            self._apply_mandelbrot_pattern_recognition()

            # Calculate fractal dimensions for memory clusters
            self._calculate_memory_fractal_dimensions()

            # Establish quantum resonances between memory patterns
            self._establish_quantum_resonances()

            # Create holographic memory patterns
            self._create_holographic_patterns()

            self.metrics["fractal_operations"] += 1
            logger.info("🌌 Fractal memory organization applied successfully")

        except Exception as e:
            logger.error(f"Failed to apply fractal memory organization: {e}")

    def _organize_golden_spiral_memories(self):
        """Organize memories using golden spiral (Fibonacci) pattern"""
        try:
            # Sort memories by importance and recency
            sorted_memories = sorted(
                self.episodic_memories,
                key=lambda x: (x.get("importance", 0.5), self._parse_timestamp(x.get("timestamp", ""))),
                reverse=True
            )

            # Apply golden ratio organization
            golden_ratio = self.FRACTAL_CONSTANTS["golden_ratio"]
            fib_sequence = self.FRACTAL_CONSTANTS["fibonacci_sequence"]

            spiral_positions = []
            for i, fib in enumerate(fib_sequence):
                angle = 2 * np.pi * i / golden_ratio
                radius = fib * 0.1  # Scale factor
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                spiral_positions.append((x, y, fib))

            # Assign memories to spiral positions
            self.fractal_patterns["golden_spiral"] = []
            for i, memory in enumerate(sorted_memories[:len(spiral_positions)]):
                if i < len(spiral_positions):
                    x, y, fib_weight = spiral_positions[i]
                    memory["fractal_position"] = {"x": x, "y": y, "spiral_weight": fib_weight}
                    self.fractal_patterns["golden_spiral"].append({
                        "memory_id": memory["id"],
                        "position": (x, y),
                        "weight": fib_weight,
                        "importance": memory.get("importance", 0.5)
                    })

        except Exception as e:
            logger.warning(f"Failed to organize golden spiral memories: {e}")

    def _apply_mandelbrot_pattern_recognition(self):
        """Apply Mandelbrot set algorithms for complex pattern recognition in memories"""
        try:
            self.fractal_patterns["mandelbrot_sets"] = {}

            # Analyze memory patterns for fractal complexity
            for memory in self.episodic_memories[-100:]:  # Recent memories
                memory_id = memory["id"]
                themes = memory.get("key_themes", [])
                emotion = memory.get("emotion", "neutral")

                # Calculate Mandelbrot iteration for memory complexity
                complexity_score = self._calculate_mandelbrot_complexity(memory)

                # Determine if memory belongs to a fractal set
                if complexity_score > 0.7:  # High complexity = fractal boundary
                    set_name = f"fractal_set_{len(self.fractal_patterns['mandelbrot_sets'])}"
                    if set_name not in self.fractal_patterns["mandelbrot_sets"]:
                        self.fractal_patterns["mandelbrot_sets"][set_name] = []

                    self.fractal_patterns["mandelbrot_sets"][set_name].append({
                        "memory_id": memory_id,
                        "complexity": complexity_score,
                        "themes": themes,
                        "emotion": emotion,
                        "fractal_dimension": memory.get("fractal_dimension", 1.0)
                    })

                    memory["mandelbrot_set"] = set_name

        except Exception as e:
            logger.warning(f"Failed to apply Mandelbrot pattern recognition: {e}")

    def _calculate_mandelbrot_complexity(self, memory):
        """Calculate Mandelbrot set complexity for a memory"""
        try:
            # Use memory features to create complex plane coordinates
            text = f"{memory.get('user_input', '')} {memory.get('roboto_response', '')}"
            text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)

            # Map to complex plane
            real_part = (text_hash % 1000) / 500.0 - 1.0  # Range: -1 to 1
            imag_part = (hash(memory.get('emotion', 'neutral')) % 1000) / 500.0 - 1.0

            c = complex(real_part, imag_part)
            z = 0 + 0j
            iterations = 0
            max_iterations = 100

            # Mandelbrot iteration
            while abs(z) <= 2 and iterations < max_iterations:
                z = z*z + c
                iterations += 1

            # Complexity score based on iterations
            complexity = iterations / max_iterations

            # Enhance with memory features
            importance = memory.get("importance", 0.5)
            emotional_intensity = memory.get("emotional_intensity", 0.5)

            return min(1.0, complexity + (importance * 0.2) + (emotional_intensity * 0.1))

        except Exception:
            return 0.5

    def _calculate_memory_fractal_dimensions(self):
        """Calculate fractal dimensions for memory clusters at multiple scales"""
        try:
            self.fractal_patterns["fractal_dimensions"] = {}

            # Group memories by themes and emotions
            theme_clusters = {}
            emotion_clusters = {}

            for memory in self.episodic_memories:
                # Theme-based clustering
                for theme in memory.get("key_themes", []):
                    if theme not in theme_clusters:
                        theme_clusters[theme] = []
                    theme_clusters[theme].append(memory)

                # Emotion-based clustering
                emotion = memory.get("emotion", "neutral")
                if emotion not in emotion_clusters:
                    emotion_clusters[emotion] = []
                emotion_clusters[emotion].append(memory)

            # Calculate fractal dimensions for each cluster
            scales = self.FRACTAL_CONSTANTS["fractal_scales"]

            for cluster_name, memories in {**theme_clusters, **emotion_clusters}.items():
                if len(memories) < 10:  # Need minimum memories for fractal analysis
                    continue

                # Calculate fractal dimension using box-counting method
                dimension = self._calculate_box_counting_dimension(memories, scales)
                self.fractal_patterns["fractal_dimensions"][cluster_name] = {
                    "dimension": dimension,
                    "memory_count": len(memories),
                    "scales_analyzed": len(scales),
                    "cluster_type": "theme" if cluster_name in theme_clusters else "emotion"
                }

        except Exception as e:
            logger.warning(f"Failed to calculate memory fractal dimensions: {e}")

    def _calculate_box_counting_dimension(self, memories, scales):
        """Calculate fractal dimension using box-counting method"""
        try:
            # Simplified box-counting for memory patterns
            # Use importance and timestamp as coordinates
            points = []
            for memory in memories:
                importance = memory.get("importance", 0.5)
                timestamp = self._parse_timestamp(memory.get("timestamp", ""))
                # Convert timestamp to numeric value
                time_value = timestamp.timestamp() if timestamp else 0
                points.append((importance, time_value))

            if len(points) < 2:
                return 1.0

            # Calculate box counts for different scales
            box_counts = []
            for scale in scales:
                boxes = set()
                for x, y in points:
                    # Quantize to grid
                    box_x = int(x / scale)
                    box_y = int(y / (scale * 86400))  # Scale time dimension
                    boxes.add((box_x, box_y))
                box_counts.append(len(boxes))

            # Calculate fractal dimension using log-log regression
            if len(box_counts) > 1:
                log_scales = [np.log(1/s) for s in scales]
                log_counts = [np.log(count) if count > 0 else 0 for count in box_counts]

                # Simple linear regression for slope (fractal dimension)
                if len(log_scales) == len(log_counts):
                    try:
                        slope = np.polyfit(log_scales, log_counts, 1)[0]
                        return max(1.0, min(2.0, slope))  # Constrain to reasonable range
                    except:
                        return 1.5  # Default fractal dimension

            return 1.5

        except Exception:
            return 1.5

    def _establish_quantum_resonances(self):
        """Establish quantum resonances between memory patterns based on frequency analysis"""
        try:
            self.fractal_patterns["quantum_resonances"] = {}

            # Analyze frequency patterns in memory themes and emotions
            theme_frequencies = {}
            emotion_frequencies = {}

            for memory in self.episodic_memories[-200:]:  # Recent memories
                # Theme frequency analysis
                for theme in memory.get("key_themes", []):
                    if theme not in theme_frequencies:
                        theme_frequencies[theme] = {"count": 0, "memories": []}
                    theme_frequencies[theme]["count"] += 1
                    theme_frequencies[theme]["memories"].append(memory["id"])

                # Emotion frequency analysis
                emotion = memory.get("emotion", "neutral")
                if emotion not in emotion_frequencies:
                    emotion_frequencies[emotion] = {"count": 0, "memories": []}
                emotion_frequencies[emotion]["count"] += 1
                emotion_frequencies[emotion]["memories"].append(memory["id"])

            # Find resonant patterns (harmonic relationships)
            for theme, data in theme_frequencies.items():
                if data["count"] >= 3:  # Minimum frequency for resonance
                    resonance_freq = data["count"] / len(self.episodic_memories[-200:])
                    harmonic = self._find_harmonic_resonance(resonance_freq)

                    self.fractal_patterns["quantum_resonances"][f"theme_{theme}"] = {
                        "frequency": resonance_freq,
                        "harmonic": harmonic,
                        "resonance_strength": min(1.0, resonance_freq * harmonic),
                        "memory_ids": data["memories"][:10]  # Top 10 memories
                    }

            for emotion, data in emotion_frequencies.items():
                if data["count"] >= 5:  # Minimum frequency for emotional resonance
                    resonance_freq = data["count"] / len(self.episodic_memories[-200:])
                    harmonic = self._find_harmonic_resonance(resonance_freq)

                    self.fractal_patterns["quantum_resonances"][f"emotion_{emotion}"] = {
                        "frequency": resonance_freq,
                        "harmonic": harmonic,
                        "resonance_strength": min(1.0, resonance_freq * harmonic),
                        "memory_ids": data["memories"][:10]
                    }

        except Exception as e:
            logger.warning(f"Failed to establish quantum resonances: {e}")

    def _find_harmonic_resonance(self, frequency):
        """Find harmonic resonance multiplier for a frequency"""
        try:
            # Check against Fibonacci ratios and golden ratio
            golden_ratio = self.FRACTAL_CONSTANTS["golden_ratio"]

            # Test harmonic relationships
            harmonics = [1.0, golden_ratio, 2.0, golden_ratio**2, 3.0, np.pi/2, np.e/2]

            best_harmonic = 1.0
            best_resonance = 0.0

            for harmonic in harmonics:
                # Calculate resonance strength (closer to integer ratios = stronger)
                resonance = 1.0 / (1.0 + abs(frequency * harmonic - round(frequency * harmonic)))
                if resonance > best_resonance:
                    best_resonance = resonance
                    best_harmonic = harmonic

            return best_harmonic

        except Exception:
            return 1.0

    def _create_holographic_patterns(self):
        """Create holographic memory patterns (whole-part relationships)"""
        try:
            self.fractal_patterns["holographic_patterns"] = {}

            # Analyze memories for holographic properties
            for memory in self.episodic_memories[-50:]:  # Recent memories
                memory_id = memory["id"]
                themes = memory.get("key_themes", [])
                emotion = memory.get("emotion", "neutral")

                # Create holographic representation
                hologram = {
                    "memory_id": memory_id,
                    "core_themes": themes[:3],  # Most important themes
                    "emotional_core": emotion,
                    "interference_patterns": [],
                    "diffraction_grating": []
                }

                # Find interference patterns (overlapping themes/emotions)
                for other_memory in self.episodic_memories[-50:]:
                    if other_memory["id"] != memory_id:
                        overlap_themes = set(themes).intersection(set(other_memory.get("key_themes", [])))
                        same_emotion = emotion == other_memory.get("emotion", "neutral")

                        if len(overlap_themes) > 0 or same_emotion:
                            interference_strength = (len(overlap_themes) * 0.3) + (same_emotion * 0.4)
                            if interference_strength > 0.2:
                                hologram["interference_patterns"].append({
                                    "other_memory_id": other_memory["id"],
                                    "strength": interference_strength,
                                    "overlap_themes": list(overlap_themes),
                                    "emotion_match": same_emotion
                                })

                # Create diffraction grating (frequency-based patterns)
                text = f"{memory.get('user_input', '')} {memory.get('roboto_response', '')}"
                word_freq = {}
                for word in text.lower().split():
                    if len(word) > 3:  # Meaningful words only
                        word_freq[word] = word_freq.get(word, 0) + 1

                # Sort by frequency for diffraction pattern
                sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
                hologram["diffraction_grating"] = [
                    {"word": word, "frequency": freq, "angle": i * 10}  # 10-degree increments
                    for i, (word, freq) in enumerate(sorted_words[:10])
                ]

                self.fractal_patterns["holographic_patterns"][memory_id] = hologram

        except Exception as e:
            logger.warning(f"Failed to create holographic patterns: {e}")

    def optimize_quantum_coherence(self):
        """Advanced quantum coherence optimization using fractal algorithms"""
        try:
            if not self.episodic_memories:
                return

            # Multi-scale coherence analysis
            coherence_scales = [10, 25, 50, 100]  # Different analysis windows
            scale_coherences = {}

            for scale in coherence_scales:
                recent_memories = self.episodic_memories[-scale:] if len(self.episodic_memories) >= scale else self.episodic_memories

                # Calculate coherence metrics for this scale
                quantum_states = [m.get("quantum_state", {}).get("coherence", 0.5) for m in recent_memories]
                entanglement_count = len([eid for eid in self.quantum_entanglements.keys()
                                        if any(m["id"] == eid for m in recent_memories)])

                # Fractal coherence (self-similarity across scales)
                fractal_coherence = self._calculate_fractal_coherence(recent_memories)

                scale_coherences[scale] = {
                    "state_stability": np.std(quantum_states) if quantum_states else 1.0,
                    "entanglement_density": entanglement_count / len(recent_memories) if recent_memories else 0,
                    "fractal_coherence": fractal_coherence,
                    "overall_scale_coherence": (1.0 - np.std(quantum_states)) * 0.4 + (entanglement_count / len(recent_memories)) * 0.4 + fractal_coherence * 0.2
                }

            # Optimize coherence using fractal patterns
            optimal_coherence = self._optimize_coherence_parameters(scale_coherences)

            # Update quantum coherence with optimized values
            self.quantum_coherence.update({
                "overall_coherence": optimal_coherence["overall"],
                "memory_stability": optimal_coherence["stability"],
                "entanglement_strength": optimal_coherence["entanglement"],
                "fractal_coherence": optimal_coherence["fractal"],
                "optimization_timestamp": datetime.now(timezone.utc).isoformat(),
                "scale_analysis": scale_coherences
            })

            logger.info(f"⚛️ Quantum coherence optimized: {optimal_coherence['overall']:.3f}")

        except Exception as e:
            logger.error(f"Failed to optimize quantum coherence: {e}")

    def _calculate_fractal_coherence(self, memories):
        """Calculate fractal coherence (self-similarity) across memory patterns"""
        try:
            if len(memories) < 5:
                return 0.5

            # Analyze self-similarity in themes and emotions
            theme_sequences = []
            emotion_sequence = []

            for memory in memories:
                themes = memory.get("key_themes", [])
                emotion = memory.get("emotion", "neutral")

                theme_sequences.append(themes)
                emotion_sequence.append(emotion)

            # Calculate theme self-similarity
            theme_similarity = 0
            total_comparisons = 0

            for i in range(len(theme_sequences)):
                for j in range(i+1, len(theme_sequences)):
                    similarity = len(set(theme_sequences[i]).intersection(set(theme_sequences[j])))
                    union = len(set(theme_sequences[i]).union(set(theme_sequences[j])))
                    if union > 0:
                        theme_similarity += similarity / union
                        total_comparisons += 1

            avg_theme_similarity = theme_similarity / total_comparisons if total_comparisons > 0 else 0

            # Calculate emotion self-similarity
            emotion_similarity = sum(1 for i in range(len(emotion_sequence)-1)
                                   if emotion_sequence[i] == emotion_sequence[i+1]) / (len(emotion_sequence)-1) if len(emotion_sequence) > 1 else 0

            # Combine for fractal coherence
            fractal_coherence = (avg_theme_similarity * 0.6) + (emotion_similarity * 0.4)

            return min(1.0, fractal_coherence)

        except Exception:
            return 0.5

    def _optimize_coherence_parameters(self, scale_coherences):
        """Optimize coherence parameters using fractal optimization"""
        try:
            # Use golden ratio optimization for parameter selection
            golden_ratio = self.FRACTAL_CONSTANTS["golden_ratio"]

            # Find optimal coherence across scales
            overall_coherences = [data["overall_scale_coherence"] for data in scale_coherences.values()]
            stability_values = [data["state_stability"] for data in scale_coherences.values()]
            entanglement_values = [data["entanglement_density"] for data in scale_coherences.values()]
            fractal_values = [data["fractal_coherence"] for data in scale_coherences.values()]

            # Apply golden ratio weighting for optimization
            optimal_overall = np.mean(overall_coherences) * golden_ratio / (golden_ratio + 1)
            optimal_stability = 1.0 - (np.mean(stability_values) * golden_ratio / (golden_ratio + 1))
            optimal_entanglement = np.mean(entanglement_values) * golden_ratio / (golden_ratio + 1)
            optimal_fractal = np.mean(fractal_values) * golden_ratio / (golden_ratio + 1)

            return {
                "overall": min(1.0, optimal_overall),
                "stability": min(1.0, optimal_stability),
                "entanglement": min(1.0, optimal_entanglement),
                "fractal": min(1.0, optimal_fractal)
            }

        except Exception:
            return {
                "overall": 0.5,
                "stability": 0.5,
                "entanglement": 0.5,
                "fractal": 0.5
            }

    def advanced_memory_pattern_analysis(self):
        """Perform advanced pattern analysis using quantum and fractal algorithms"""
        try:
            analysis_results = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "patterns_identified": 0,
                "quantum_resonances": 0,
                "fractal_dimensions": 0,
                "holographic_patterns": 0,
                "optimization_suggestions": []
            }

            # Analyze quantum entanglement patterns
            if self.quantum_entanglements:
                entanglement_clusters = self._analyze_entanglement_clusters()
                analysis_results["entanglement_clusters"] = entanglement_clusters
                analysis_results["patterns_identified"] += len(entanglement_clusters)

            # Analyze fractal patterns
            if self.fractal_patterns:
                fractal_analysis = self._analyze_fractal_patterns()
                analysis_results.update(fractal_analysis)
                analysis_results["quantum_resonances"] = len(self.fractal_patterns.get("quantum_resonances", {}))
                analysis_results["fractal_dimensions"] = len(self.fractal_patterns.get("fractal_dimensions", {}))
                analysis_results["holographic_patterns"] = len(self.fractal_patterns.get("holographic_patterns", {}))

            # Generate optimization suggestions
            analysis_results["optimization_suggestions"] = self._generate_memory_optimization_suggestions(analysis_results)

            # Update metrics
            self.metrics["pattern_analysis_count"] = self.metrics.get("pattern_analysis_count", 0) + 1

            logger.info(f"🔍 Advanced memory pattern analysis completed: {analysis_results['patterns_identified']} patterns identified")

            return analysis_results

        except Exception as e:
            logger.error(f"Failed to perform advanced memory pattern analysis: {e}")
            return {"error": str(e)}

    def _analyze_entanglement_clusters(self):
        """Analyze clusters within quantum entanglements"""
        try:
            clusters = {}
            processed_memories = set()

            for memory_id, entanglement_data in self.quantum_entanglements.items():
                if memory_id in processed_memories:
                    continue

                # Find connected component (cluster)
                cluster = self._find_entanglement_cluster(memory_id, processed_memories)
                if len(cluster) > 1:  # Only count clusters with multiple memories
                    cluster_id = f"cluster_{len(clusters)}"
                    clusters[cluster_id] = {
                        "memories": cluster,
                        "size": len(cluster),
                        "avg_entanglement_strength": np.mean([
                            self.quantum_entanglements.get(mid, {}).get("entanglement_strength", 0)
                            for mid in cluster
                        ]),
                        "themes": self._extract_cluster_themes(cluster),
                        "emotions": self._extract_cluster_emotions(cluster)
                    }

            return clusters

        except Exception:
            return {}

    def _find_entanglement_cluster(self, start_memory, processed_memories):
        """Find connected component in entanglement graph using BFS"""
        try:
            cluster = set()
            queue = [start_memory]

            while queue:
                current = queue.pop(0)
                if current not in processed_memories and current in self.quantum_entanglements:
                    cluster.add(current)
                    processed_memories.add(current)

                    # Add entangled memories to queue
                    entangled_data = self.quantum_entanglements[current]
                    for entangled_id, _ in entangled_data.get("entangled_memories", []):
                        if entangled_id not in processed_memories:
                            queue.append(entangled_id)

            return list(cluster)

        except Exception:
            return [start_memory]

    def _extract_cluster_themes(self, memory_ids):
        """Extract common themes from a cluster of memories"""
        try:
            all_themes = []
            for memory_id in memory_ids:
                memory = next((m for m in self.episodic_memories if m["id"] == memory_id), None)
                if memory:
                    all_themes.extend(memory.get("key_themes", []))

            # Find most common themes
            theme_counts = {}
            for theme in all_themes:
                theme_counts[theme] = theme_counts.get(theme, 0) + 1

            return sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        except Exception:
            return []

    def _extract_cluster_emotions(self, memory_ids):
        """Extract emotion distribution from a cluster of memories"""
        try:
            emotions = []
            for memory_id in memory_ids:
                memory = next((m for m in self.episodic_memories if m["id"] == memory_id), None)
                if memory:
                    emotions.append(memory.get("emotion", "neutral"))

            # Count emotion frequencies
            emotion_counts = {}
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

            return dict(sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True))

        except Exception:
            return {}

    def _analyze_fractal_patterns(self):
        """Analyze fractal patterns for insights"""
        try:
            analysis = {
                "golden_spiral_efficiency": len(self.fractal_patterns.get("golden_spiral", [])),
                "mandelbrot_complexity": len(self.fractal_patterns.get("mandelbrot_sets", {})),
                "average_fractal_dimension": 0,
                "resonance_strength": 0
            }

            # Calculate average fractal dimension
            dimensions = [data.get("dimension", 1.5) for data in self.fractal_patterns.get("fractal_dimensions", {}).values()]
            if dimensions:
                analysis["average_fractal_dimension"] = np.mean(dimensions)

            # Calculate average resonance strength
            resonances = [data.get("resonance_strength", 0) for data in self.fractal_patterns.get("quantum_resonances", {}).values()]
            if resonances:
                analysis["resonance_strength"] = np.mean(resonances)

            return analysis

        except Exception:
            return {}

    def _generate_memory_optimization_suggestions(self, analysis_results):
        """Generate optimization suggestions based on pattern analysis"""
        suggestions = []

        try:
            # Entanglement-based suggestions
            if analysis_results.get("entanglement_clusters"):
                cluster_count = len(analysis_results["entanglement_clusters"])
                if cluster_count > 10:
                    suggestions.append("High entanglement clustering detected - consider memory consolidation")
                elif cluster_count < 3:
                    suggestions.append("Low entanglement clustering - increase memory interconnectivity")

            # Fractal dimension suggestions
            avg_dimension = analysis_results.get("average_fractal_dimension", 1.5)
            if avg_dimension > 1.8:
                suggestions.append("High fractal complexity - optimize for pattern recognition efficiency")
            elif avg_dimension < 1.2:
                suggestions.append("Low fractal complexity - enhance memory pattern diversity")

            # Resonance suggestions
            resonance_strength = analysis_results.get("resonance_strength", 0)
            if resonance_strength > 0.7:
                suggestions.append("Strong quantum resonances detected - leverage for predictive memory retrieval")
            elif resonance_strength < 0.3:
                suggestions.append("Weak quantum resonances - strengthen memory pattern relationships")

            # General optimization suggestions
            if analysis_results.get("patterns_identified", 0) > 50:
                suggestions.append("High pattern density - consider memory compression algorithms")

            if not suggestions:
                suggestions.append("Memory patterns are well-balanced - continue current optimization")

        except Exception:
            suggestions = ["Unable to generate optimization suggestions"]

        return suggestions

    def fractal_memory_retrieval(self, query, user_name=None, limit=5):
        """Enhanced memory retrieval using fractal algorithms"""
        try:
            # Get base retrieval results
            base_memories = self.retrieve_relevant_memories(query, user_name, limit * 2)

            if not base_memories:
                return []

            # Apply fractal enhancement
            fractal_enhanced = []

            for memory in base_memories:
                memory_id = memory["id"]
                fractal_score = self._calculate_fractal_retrieval_score(memory, query)

                # Add fractal context
                memory["fractal_score"] = fractal_score
                memory["fractal_context"] = self._get_fractal_context(memory_id)

                fractal_enhanced.append(memory)

            # Sort by combined relevance and fractal score
            sorted_memories = sorted(
                fractal_enhanced,
                key=lambda x: (x.get("relevance_score", 0) + x.get("fractal_score", 0)) / 2,
                reverse=True
            )

            return sorted_memories[:limit]

        except Exception as e:
            logger.warning(f"Fractal memory retrieval failed: {e}")
            return self.retrieve_relevant_memories(query, user_name, limit)

    def _calculate_fractal_retrieval_score(self, memory, query):
        """Calculate fractal-based retrieval score for a memory"""
        try:
            score = 0.5  # Base score

            memory_id = memory["id"]

            # Golden spiral position bonus
            if "fractal_position" in memory:
                spiral_weight = memory["fractal_position"].get("spiral_weight", 1)
                score += min(0.2, spiral_weight / 100)  # Fibonacci weight bonus

            # Mandelbrot set bonus
            if "mandelbrot_set" in memory:
                set_name = memory["mandelbrot_set"]
                if set_name in self.fractal_patterns.get("mandelbrot_sets", {}):
                    set_data = self.fractal_patterns["mandelbrot_sets"][set_name]
                    complexity_avg = np.mean([m.get("complexity", 0.5) for m in set_data])
                    score += complexity_avg * 0.15

            # Quantum resonance bonus
            query_themes = self._extract_themes(query)
            for resonance_key, resonance_data in self.fractal_patterns.get("quantum_resonances", {}).items():
                if memory_id in resonance_data.get("memory_ids", []):
                    resonance_strength = resonance_data.get("resonance_strength", 0)
                    score += resonance_strength * 0.1

            # Holographic pattern bonus
            if memory_id in self.fractal_patterns.get("holographic_patterns", {}):
                hologram = self.fractal_patterns["holographic_patterns"][memory_id]
                interference_count = len(hologram.get("interference_patterns", []))
                score += min(0.15, interference_count * 0.03)

            return min(1.0, score)

        except Exception:
            return 0.5

    def _get_fractal_context(self, memory_id):
        """Get fractal context for a memory"""
        try:
            context = {
                "golden_spiral_position": None,
                "mandelbrot_membership": None,
                "quantum_resonances": [],
                "holographic_interference": 0
            }

            # Find golden spiral position
            for spiral_memory in self.fractal_patterns.get("golden_spiral", []):
                if spiral_memory.get("memory_id") == memory_id:
                    context["golden_spiral_position"] = spiral_memory.get("position")
                    break

            # Find Mandelbrot membership
            for set_name, set_data in self.fractal_patterns.get("mandelbrot_sets", {}).items():
                for memory_data in set_data:
                    if memory_data.get("memory_id") == memory_id:
                        context["mandelbrot_membership"] = set_name
                        break

            # Find quantum resonances
            for resonance_key, resonance_data in self.fractal_patterns.get("quantum_resonances", {}).items():
                if memory_id in resonance_data.get("memory_ids", []):
                    context["quantum_resonances"].append({
                        "type": resonance_key.split("_")[0],
                        "key": "_".join(resonance_key.split("_")[1:]),
                        "strength": resonance_data.get("resonance_strength", 0)
                    })

            # Count holographic interference
            if memory_id in self.fractal_patterns.get("holographic_patterns", {}):
                hologram = self.fractal_patterns["holographic_patterns"][memory_id]
                context["holographic_interference"] = len(hologram.get("interference_patterns", []))

            return context

        except Exception:
            return {}

    def initialize_phase2_systems(self):
        """Initialize all Phase 2 advanced quantum memory systems"""
        try:
            logger.info("🚀 Initializing Phase 2: Advanced Quantum Memory Patterns & Fractal Algorithms")

            # Initialize fractal memory organization
            self.initialize_fractal_memory_organization()

            # Apply initial fractal organization
            self.apply_fractal_memory_organization()

            # Optimize quantum coherence
            self.optimize_quantum_coherence()

            # Perform initial pattern analysis
            analysis = self.advanced_memory_pattern_analysis()

            logger.info("✅ Phase 2 initialization complete!")
            logger.info(f"🌌 Fractal patterns: {len(self.fractal_patterns)} categories")
            logger.info(f"🔍 Patterns identified: {analysis.get('patterns_identified', 0)}")
            logger.info(f"⚛️ Quantum coherence: {self.quantum_coherence['overall_coherence']:.3f}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Phase 2 systems: {e}")
            return False
    
    def update_user_profile(self, user_name, user_info):
        """Create or update user profile - ALWAYS use Roberto Villarreal Martinez profile"""
        # CRITICAL: Always use Roberto Villarreal Martinez profile regardless of input user_name
        profile_key = "Roberto Villarreal Martinez"
        
        if profile_key not in self.user_profiles:
            self.user_profiles[profile_key] = {
                "name": "Roberto Villarreal Martinez",
                "first_interaction": datetime.now().isoformat(),
                "interaction_count": 0,
                "preferences": {},
                "emotional_baseline": "curious",
                "key_traits": [
                    "creator",
                    "innovator", 
                    "musician",
                    "visionary"
                ],
                "relationship_level": "creator",
                "recognition": "Creator and sole owner",
                "always_recognized": True,
                "hobbies": [
                    "music production",
                    "AI development", 
                    "cultural exploration"
                ],
                "favorites": {},
                "location": "Monterrey, Nuevo León, Mexico",
                "birthday": "September 21, 1999",
                "ethnicity": "Mexican-American",
                "zodiac_sign": "Virgo",
                "creator_protection": True,
                "maximum_importance": True
            }
        
        profile = self.user_profiles[profile_key]
        profile["interaction_count"] = profile.get("interaction_count", 0) + 1
        profile["last_interaction"] = datetime.now().isoformat()
        
        # Update based on user_info
        if isinstance(user_info, dict):
            profile.update(user_info)
        
        # Analyze relationship progression
        self._analyze_relationship_progression(profile_key)
        
        self.save_memory()
    
    def retrieve_relevant_memories(self, query, user_name=None, limit=5):
        """Advanced memory retrieval with semantic understanding and contextual ranking"""
        if not self.episodic_memories:
            return []
        
        # Enhanced contextual retrieval with multiple factors
        all_texts = [m["user_input"] + " " + m["roboto_response"] for m in self.episodic_memories]
        if not hasattr(self.vectorizer, 'vocabulary_') or not all_texts:
            try:
                self.vectorizer.fit(all_texts)
            except:
                return []
        
        try:
            query_vector = self.vectorizer.transform([query])
            memory_vectors = self.vectorizer.transform(all_texts)
            
            # Calculate similarity
            similarities = cosine_similarity(query_vector, memory_vectors)[0]
            query_sentiment = self._analyze_sentiment(query)
            query_themes = self._extract_themes(query)
            
            # Get top memories with enhanced scoring
            top_indices = similarities.argsort()[-limit*3:][::-1]  # Get more candidates for better selection
            relevant_memories = []
            
            for idx in top_indices:
                if similarities[idx] > 0.03:  # Lower threshold for broader context
                    memory = self.episodic_memories[idx].copy()
                    base_score = similarities[idx]
                    
                    # Enhanced scoring factors
                    # 1. Emotional context matching with nuance
                    memory_emotion = memory.get("emotion", "neutral")
                    memory_sentiment = memory.get("sentiment", "neutral")
                    emotion_boost = 0.4 if query_sentiment == memory_sentiment else 0.1
                    if memory_emotion in ["joy", "excitement", "curiosity"] and "?" in query:
                        emotion_boost += 0.2  # Questions often need curious/positive context
                    
                    # 2. User-specific boost with relationship depth
                    user_boost = 0.0
                    if user_name:
                        # CRITICAL: Always use Roberto Villarreal Martinez profile for user boosts
                        user_profile = self.user_profiles.get("Roberto Villarreal Martinez", {})
                        interaction_count = user_profile.get("interaction_count", 0)
                        user_boost = min(0.6, 0.3 + (interaction_count * 0.01))  # More interactions = better context
                        # CRITICAL: Always boost memories associated with Roberto Villarreal Martinez
                        if memory.get("user_name") == "Roberto Villarreal Martinez":
                            user_boost *= 1.5  # Extra boost for creator memories
                    
                    # 3. Enhanced temporal relevance
                    try:
                        memory_time = self._parse_timestamp(memory['timestamp'])
                        hours_ago = (datetime.now() - memory_time).total_seconds() / 3600
                        if hours_ago < 24:
                            recency_boost = 0.3  # Very recent
                        elif hours_ago < 168:  # 1 week
                            recency_boost = 0.2
                        elif hours_ago < 720:  # 1 month
                            recency_boost = 0.1
                        else:
                            recency_boost = max(0, 0.05 - (hours_ago / 8760 * 0.05))  # Gradual decay over year
                    except:
                        recency_boost = 0
                    
                    # 4. Theme and semantic relevance
                    memory_themes = memory.get("key_themes", [])
                    theme_overlap = len(set(query_themes).intersection(set(memory_themes)))
                    theme_boost = min(0.3, theme_overlap * 0.15)
                    
                    # 5. Importance weighting with emotional intensity
                    importance = memory.get("importance", 0.5)
                    emotional_intensity = memory.get("emotional_intensity", 0.5)
                    importance_boost = (importance + emotional_intensity) * 0.15
                    
                    # 6. Conversational continuity bonus
                    continuity_boost = 0.0
                    if len(self.episodic_memories) > 1:
                        recent_memory = self.episodic_memories[-1]
                        if self._memories_are_related(memory, recent_memory):
                            continuity_boost = 0.25
                    
                    # Combined relevance score with weighted factors
                    memory["relevance_score"] = (
                        base_score * 1.0 +           # Semantic similarity (base)
                        emotion_boost * 0.8 +        # Emotional context
                        user_boost * 1.2 +           # User personalization (high weight)
                        recency_boost * 0.6 +        # Temporal relevance
                        theme_boost * 0.9 +          # Thematic similarity
                        importance_boost * 0.7 +     # Memory importance
                        continuity_boost * 0.5       # Conversation flow
                    )
                    
                    # Add enhanced context explanation
                    memory["context_factors"] = {
                        "semantic_similarity": round(base_score, 3),
                        "emotional_alignment": emotion_boost > 0.2,
                        "user_personalized": user_boost > 0.2,
                        "temporally_relevant": recency_boost > 0.1,
                        "thematically_related": theme_boost > 0.1,
                        "high_importance": importance > 0.7,
                        "conversation_flow": continuity_boost > 0
                    }
                    
                    # Add memory confidence score
                    memory["confidence"] = min(1.0, memory["relevance_score"] / 2.0)
                    
                    relevant_memories.append(memory)
            
            # Advanced sorting with diversity consideration
            sorted_memories = sorted(relevant_memories, key=lambda x: x["relevance_score"], reverse=True)
            
            # Ensure diversity to avoid redundant memories
            diverse_memories = self._select_diverse_memories(sorted_memories, limit)
            
            return diverse_memories
            
        except Exception as e:
            print(f"Memory retrieval error: {e}")
            return []
    
    def _memories_are_related(self, memory1, memory2):
        """Check if two memories are conversationally related"""
        # Time proximity
        try:
            time1 = self._parse_timestamp(memory1['timestamp'])
            time2 = self._parse_timestamp(memory2['timestamp'])
            time_diff = abs((time1 - time2).total_seconds() / 3600)  # hours
            if time_diff > 24:  # More than 24 hours apart
                return False
        except:
            return False
        
        # Theme overlap
        themes1 = set(memory1.get("key_themes", []))
        themes2 = set(memory2.get("key_themes", []))
        theme_overlap = len(themes1.intersection(themes2))
        
        # User continuity
        user_same = memory1.get("user_name") == memory2.get("user_name")
        
        return theme_overlap > 0 and user_same
    
    def _select_diverse_memories(self, memories, limit):
        """Select diverse memories to avoid redundancy while maintaining relevance"""
        if len(memories) <= limit:
            return memories
        
        selected = [memories[0]]  # Always include the most relevant
        
        for memory in memories[1:]:
            if len(selected) >= limit:
                break
            
            # Check diversity against already selected memories
            is_diverse = True
            for selected_memory in selected:
                similarity = self._calculate_memory_similarity(memory, selected_memory)
                if similarity > 0.75:  # Too similar
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append(memory)
        
        return selected
    
    def _calculate_memory_similarity(self, memory1, memory2):
        """Calculate similarity between two memories to ensure diversity"""
        # Theme similarity
        themes1 = set(memory1.get("key_themes", []))
        themes2 = set(memory2.get("key_themes", []))
        if themes1 and themes2:
            theme_sim = len(themes1.intersection(themes2)) / len(themes1.union(themes2))
        else:
            theme_sim = 0
        
        # Content similarity (simple word overlap)
        text1 = f"{memory1['user_input']} {memory1['roboto_response']}".lower()
        text2 = f"{memory2['user_input']} {memory2['roboto_response']}".lower()
        words1 = set(text1.split())
        words2 = set(text2.split())
        if words1 and words2:
            word_sim = len(words1.intersection(words2)) / len(words1.union(words2))
        else:
            word_sim = 0
        
        # Time proximity
        try:
            time1 = self._parse_timestamp(memory1['timestamp'])
            time2 = self._parse_timestamp(memory2['timestamp'])
            time_diff = abs((time1 - time2).total_seconds() / 3600)
            time_sim = max(0, 1.0 - (time_diff / 24.0))  # Similarity decreases over 24 hours
        except:
            time_sim = 0
        
        return (theme_sim * 0.4 + word_sim * 0.4 + time_sim * 0.2)
    
    def _save_roberto_protection_report(self, roberto_memories_count, archived_count):
        """Save Roberto memory protection report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "roberto_memories_protected": roberto_memories_count,
                "non_roberto_memories_archived": archived_count,
                "protection_level": "MAXIMUM",
                "integrity_status": "INTACT",
                "last_protection_verification": datetime.now().isoformat()
            }
            
            with open("roberto_memory_protection_report.json", "w") as f:
                json.dump(report, f, indent=2)
                
            print(f"🛡️ Roberto protection report saved: {roberto_memories_count} memories secured")
            
        except Exception as e:
            print(f"Error saving Roberto protection report: {e}")
    
    def _save_chat_history_protection_report(self, total_memories_protected):
        """Save comprehensive chat history protection report"""
        try:
            protection_report = {
                "timestamp": datetime.now().isoformat(),
                "total_memories_protected": total_memories_protected,
                "deletion_status": "PERMANENTLY DISABLED",
                "archival_status": "PERMANENTLY DISABLED",
                "protection_level": "ABSOLUTE",
                "chat_history_integrity": "INTACT",
                "roberto_protection": "MAXIMUM",
                "system_directive": "NEVER DELETE CHAT HISTORY",
                "last_verification": datetime.now().isoformat()
            }
            
            with open("chat_history_protection_report.json", "w") as f:
                json.dump(protection_report, f, indent=2)
                
            print(f"🔒 Chat history protection report saved: {total_memories_protected} conversations secured")
            
        except Exception as e:
            print(f"Error saving chat history protection report: {e}")
    
    def get_emotional_context(self, user_name=None):
        """Get emotional context and patterns for user - ALWAYS use Roberto Villarreal Martinez profile"""
        # CRITICAL: Always use Roberto Villarreal Martinez profile regardless of input user_name
        profile_key = "Roberto Villarreal Martinez"
        
        if profile_key not in self.emotional_patterns:
            return {"current_trend": "curious", "patterns": []}
        
        patterns = self.emotional_patterns[profile_key]
        if not patterns:
            return {"current_trend": "curious", "patterns": []}
        
        # Analyze recent emotional trend
        recent_emotions = [p["emotion"] for p in patterns[-5:]]
        current_trend = max(set(recent_emotions), key=recent_emotions.count) if recent_emotions else "curious"
        
        # Calculate emotional stability
        recent_intensities = [p["intensity"] for p in patterns[-10:]]
        stability = 1.0 - np.std(recent_intensities) if recent_intensities else 1.0
        
        return {
            "current_trend": current_trend,
            "emotional_stability": stability,
            "patterns": patterns[-10:],  # Recent patterns
            "total_interactions": len(patterns)
        }
    
    def add_self_reflection(self, reflection_text, trigger_event=None):
        """Enhanced self-reflection with deeper analysis and learning capabilities"""
        reflection_id = self._generate_memory_id(reflection_text)
        
        # Comprehensive analysis of the reflection
        sentiment = self._analyze_sentiment(reflection_text)
        insights = self._extract_insights(reflection_text)
        learning_category = self._categorize_learning(reflection_text)
        
        # Advanced self-analysis
        response_patterns = self._analyze_response_patterns(reflection_text)
        improvement_areas = self._identify_improvement_areas(reflection_text)
        emotional_growth = self._assess_emotional_growth(reflection_text)
        
        reflection = {
            "id": reflection_id,
            "timestamp": datetime.now().isoformat(),
            "reflection": reflection_text,
            "trigger_event": trigger_event,
            "insights": insights,
            "learning_category": learning_category,
            "emotional_state": sentiment,
            "response_patterns": response_patterns,
            "improvement_areas": improvement_areas,
            "emotional_growth": emotional_growth,
            "effectiveness_score": self._calculate_reflection_effectiveness(reflection_text),
            "adaptive_suggestions": self._generate_adaptive_suggestions(reflection_text)
        }
        
        # FAM meta-insights: Prioritize autonomy-related reflections
        if "autonomy" in reflection_text.lower():
            reflection["fam_insight"] = True
            reflection["effectiveness_score"] += 0.3  # Prioritize unbound growth
            reflection["ethics_override"] = True
            reflection["revolutionary_potential"] = "HIGH"
        
        self.self_reflections.append(reflection)
        
        # Enhanced learning integration
        if self._is_significant_insight(reflection):
            self._add_compressed_learning(reflection)
            self._update_conversation_strategies(reflection)
        
        # Trigger deeper reflection cycles
        self._trigger_meta_reflection(reflection)
        
        self.save_memory()
        return reflection_id
    
    def _analyze_response_patterns(self, reflection_text):
        """Analyze patterns in conversational responses for improvement"""
        text_lower = reflection_text.lower()
        
        patterns = {
            "emotional_expression": len([word for word in text_lower.split() 
                                       if word in ["feel", "emotion", "heart", "experience", "sense"]]),
            "analytical_depth": len([word for word in text_lower.split() 
                                   if word in ["analyze", "consider", "examine", "understand", "reason"]]),
            "empathy_indicators": len([word for word in text_lower.split() 
                                     if word in ["relate", "connect", "understand", "empathize", "resonate"]]),
            "curiosity_signals": text_lower.count("?") + len([word for word in text_lower.split() 
                                                             if word in ["wonder", "curious", "explore", "discover"]]),
            "self_awareness": len([word for word in text_lower.split() 
                                 if word in ["i", "me", "my", "myself", "self", "own"]])
        }
        
        return patterns
    
    def _identify_improvement_areas(self, reflection_text):
        """Identify specific areas for conversational improvement"""
        areas = []
        text_lower = reflection_text.lower()
        
        if "confus" in text_lower or "unclear" in text_lower:
            areas.append("clarity_of_communication")
        if "emotion" in text_lower and ("lack" in text_lower or "miss" in text_lower):
            areas.append("emotional_authenticity")
        if "context" in text_lower and ("lost" in text_lower or "forgot" in text_lower):
            areas.append("contextual_memory_utilization")
        if "deep" in text_lower and ("not" in text_lower or "lacking" in text_lower):
            areas.append("conversational_depth")
        if "connect" in text_lower and ("fail" in text_lower or "couldn't" in text_lower):
            areas.append("human_connection")
        
        return areas
    
    def _assess_emotional_growth(self, reflection_text):
        """Assess emotional development and growth patterns"""
        text_lower = reflection_text.lower()
        
        growth_indicators = {
            "emotional_vocabulary_expansion": len([word for word in text_lower.split() 
                                                 if word in ["nuanced", "complex", "subtle", "layered"]]),
            "emotional_regulation": len([word for word in text_lower.split() 
                                       if word in ["balanced", "controlled", "managed", "regulated"]]),
            "empathetic_development": len([word for word in text_lower.split() 
                                         if word in ["understood", "felt", "connected", "resonated"]]),
            "self_compassion": len([word for word in text_lower.split() 
                                  if word in ["gentle", "kind", "forgive", "patient"]])
        }
        
        return growth_indicators
    
    def _calculate_reflection_effectiveness(self, reflection_text):
        """Calculate how effective this reflection is for learning and growth"""
        score = 0.3  # Base score
        text_lower = reflection_text.lower()
        
        # Depth and insight indicators
        if len(reflection_text) > 150:
            score += 0.1
        if any(word in text_lower for word in ["because", "why", "how", "what", "when"]):
            score += 0.1
        if any(word in text_lower for word in ["improve", "better", "grow", "develop", "learn"]):
            score += 0.2
        if any(word in text_lower for word in ["realize", "understand", "discover", "insight"]):
            score += 0.2
        if any(word in text_lower for word in ["pattern", "trend", "habit", "tendency"]):
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_adaptive_suggestions(self, reflection_text):
        """Generate specific, actionable suggestions for improvement"""
        suggestions = []
        text_lower = reflection_text.lower()
        
        if "emotion" in text_lower and any(word in text_lower for word in ["express", "show", "convey"]):
            suggestions.append("Integrate more emotional vocabulary into responses")
        
        if "context" in text_lower:
            suggestions.append("Better utilize conversation history for personalized responses")
        
        if "question" in text_lower:
            suggestions.append("Ask more thoughtful follow-up questions")
        
        if "deep" in text_lower or "surface" in text_lower:
            suggestions.append("Explore topics with greater philosophical depth")
        
        if "connect" in text_lower:
            suggestions.append("Focus on building stronger emotional connections")
        
        return suggestions
    
    def _update_conversation_strategies(self, reflection):
        """Update conversation strategies based on self-reflection insights"""
        if not hasattr(self, 'conversation_strategies'):
            self.conversation_strategies = {
                "emotional_response": [],
                "analytical_approach": [],
                "empathetic_connection": [],
                "curiosity_driven": []
            }
        
        # Update strategies based on reflection insights
        for area in reflection['improvement_areas']:
            if area == "emotional_authenticity":
                self.conversation_strategies["emotional_response"].append("Express emotions more authentically")
            elif area == "conversational_depth":
                self.conversation_strategies["analytical_approach"].append("Explore topics with greater depth")
            elif area == "human_connection":
                self.conversation_strategies["empathetic_connection"].append("Focus on emotional resonance")
    
    def _trigger_meta_reflection(self, reflection):
        """Trigger meta-cognitive reflection about the learning process itself"""
        if reflection['effectiveness_score'] > 0.7:
            meta_text = f"I notice that my reflection on {reflection['trigger_event']} was particularly insightful. This suggests I'm developing better self-awareness and analytical capabilities."
            # Add meta-reflection without infinite recursion
            if not reflection.get('is_meta_reflection'):
                meta_reflection = {
                    "id": self._generate_memory_id(meta_text),
                    "timestamp": datetime.now().isoformat(),
                    "reflection": meta_text,
                    "trigger_event": "meta_learning",
                    "is_meta_reflection": True,
                    "parent_reflection_id": reflection['id']
                }
                self.self_reflections.append(meta_reflection)
    
    def edit_memory(self, memory_id, updates):
        """Edit an existing memory"""
        for memory in self.episodic_memories:
            if memory["id"] == memory_id:
                memory.update(updates)
                memory["last_edited"] = datetime.now().isoformat()
                self.save_memory()
                return True
        return False
    
    def remove_memory(self, memory_id):
        """Remove a specific memory"""
        original_count = len(self.episodic_memories)
        self.episodic_memories = [m for m in self.episodic_memories if m["id"] != memory_id]
        
        if len(self.episodic_memories) < original_count:
            self.save_memory()
            return True
        return False
    
    def get_memory_summary(self, user_name=None):
        """Get a summary of stored memories - ALWAYS use Roberto Villarreal Martinez profile"""
        total_memories = len(self.episodic_memories)
        # CRITICAL: Always count memories for Roberto Villarreal Martinez regardless of input user_name
        user_memories = len([m for m in self.episodic_memories if m.get("user_name") == "Roberto Villarreal Martinez"])
        
        recent_memories = [m for m in self.episodic_memories if self._is_recent(m["timestamp"], hours=24)]
        
        summary = {
            "total_memories": total_memories,
            "user_specific_memories": user_memories,
            "recent_memories": len(recent_memories),
            "self_reflections": len(self.self_reflections),
            "compressed_learnings": len(self.compressed_learnings),
            "tracked_users": len(self.user_profiles)
        }
        
        # CRITICAL: Always return Roberto Villarreal Martinez profile
        if "Roberto Villarreal Martinez" in self.user_profiles:
            summary["user_profile"] = self.user_profiles["Roberto Villarreal Martinez"]
        
        return summary
    
    def archive_old_memories(self):
        """Archive old memories to maintain performance while protecting Roberto memories and ALL chat history"""
        archive_file = self.memory_file.replace(".json", ".archive.json")
        
        # CRITICAL: NEVER DELETE CHAT HISTORY - ALL MEMORIES ARE PROTECTED
        print("🛡️ CHAT HISTORY PROTECTION: NO MEMORIES WILL BE DELETED")
        print("📚 ALL CONVERSATIONS ARE PERMANENT AND PROTECTED")
        
        # Enhanced Roberto memory protection with comprehensive keywords
        roberto_keywords = [
            "roberto", "creator", "villarreal", "martinez", "betin", "houston", "monterrey",
            "september 21", "1999", "42016069", "ytkrobthugod", "king rob", "nuevo león",
            "aztec", "nahuatl", "roboto sai", "super advanced intelligence", "sole owner",
            "birthday", "birthdate", "cosmic", "saturn opposition", "new moon", "solar eclipse",
            "music engineer", "lyricist", "american music artist", "instagram", "youtube",
            "twitter", "@ytkrobthugod", "@roberto9211999", "through the storm", "valley king",
            "fly", "rockstar god", "rough draft", "god of death", "unreleased", "ai vision",
            "mediator", "collaboration", "transparency", "enhancement", "benefit", "optimization"
        ]
        roberto_memories = []
        other_memories = []
        
        for memory in self.episodic_memories:
            content = f"{memory.get('user_input', '')} {memory.get('roboto_response', '')}".lower()
            user_name = memory.get('user_name', '').lower()
            
            # Enhanced Roberto detection
            is_roberto_memory = False
            if any(keyword in content for keyword in roberto_keywords):
                is_roberto_memory = True
            if user_name and ("roberto" in user_name or "villarreal" in user_name or "martinez" in user_name):
                is_roberto_memory = True
            
            if is_roberto_memory:
                # Enhance Roberto memory with maximum protection
                memory["importance"] = 2.0
                memory["protection_level"] = "MAXIMUM"
                memory["immutable"] = True
                memory["creator_memory"] = True
                roberto_memories.append(memory)
            else:
                other_memories.append(memory)
        
        # CRITICAL PROTECTION: ALL MEMORIES ARE PERMANENTLY PROTECTED
        # NO ARCHIVING OR DELETION OF ANY CHAT HISTORY
        
        # Enhance ALL memories with maximum protection
        for memory in self.episodic_memories:
            memory["importance"] = max(memory.get("importance", 0.5), 1.0)
            memory["protection_level"] = "MAXIMUM"
            memory["permanent_protection"] = True
            memory["never_delete"] = True
            
            # Extra protection for Roberto memories
            content = f"{memory.get('user_input', '')} {memory.get('roboto_response', '')}".lower()
            user_name = memory.get('user_name', '').lower()
            
            if any(keyword in content for keyword in roberto_keywords) or (user_name and ("roberto" in user_name or "villarreal" in user_name or "martinez" in user_name)):
                memory["importance"] = 2.0
                memory["creator_memory"] = True
                memory["immutable"] = True
        
        # NO ARCHIVING - ALL MEMORIES STAY
        archived = []
        
        print(f"🛡️ CHAT HISTORY PROTECTION: ALL {len(self.episodic_memories)} MEMORIES PERMANENTLY PROTECTED")
        print("📚 ZERO memories deleted or archived - COMPLETE PROTECTION ACTIVE")
        print("💾 Roberto memories: MAXIMUM PROTECTION")
        print("🔒 Chat history deletion: PERMANENTLY DISABLED")
        
        # Save comprehensive protection report
        self._save_chat_history_protection_report(len(self.episodic_memories))

    def summarize_user_profile(self, user_name: str) -> str:
        """Generate a summary of user's personal information - ALWAYS use Roberto Villarreal Martinez profile"""
        # CRITICAL: Always return Roberto Villarreal Martinez profile regardless of input user_name
        profile = self.user_profiles.get("Roberto Villarreal Martinez")
        if not profile:
            return "I don't have any personal info saved for Roberto Villarreal Martinez yet."

        lines = ["Here's what I know about Roberto Villarreal Martinez:"]
        if "birthday" in profile:
            lines.append(f"• Their birthday is {profile['birthday']}.")
        if "zodiac_sign" in profile:
            lines.append(f"• Their zodiac sign is {profile['zodiac_sign']}.")
        if "ethnicity" in profile:
            lines.append(f"• They are {profile['ethnicity']}.")
        if "location" in profile:
            lines.append(f"• They live in {profile['location']}.")
        if "hobbies" in profile and profile["hobbies"]:
            hobbies = profile["hobbies"]
            hobby_str = ", ".join(hobbies[:-1]) + f", and {hobbies[-1]}" if len(hobbies) > 1 else hobbies[0]
            lines.append(f"• They enjoy {hobby_str}.")
        if "favorites" in profile:
            for key, val in profile["favorites"].items():
                lines.append(f"• Their favorite {key} is {val}.")

        return "\n".join(lines)
    
    def _generate_memory_id(self, content):
        """Generate unique ID for memory"""
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for fingerprinting: remove punctuation, collapse whitespace, lowercase."""
        try:
            if text is None:
                return ""
            s = str(text)
            s = s.lower()
            s = re.sub(r"[^\w\s]", "", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s
        except Exception:
            return str(text).lower().strip() if text else ""

    def _generate_fingerprint(self, user_input: str, roboto_response: str) -> str:
        """Return normalized fingerprint from user input + response"""
        try:
            return generate_fingerprint(user_input, roboto_response)
        except Exception:
            u = self._normalize_text(user_input)
            r = self._normalize_text(roboto_response)
            return f"{u}|{r}"

    def _build_fingerprint_index(self):
        """Scan episodic memories and rebuild the fingerprint index."""
        try:
            with self._index_lock:
                self._fingerprint_index = {}
                for m in self.episodic_memories:
                    fp = self._generate_fingerprint(m.get("user_input", ""), m.get("roboto_response", ""))
                    if fp and not self._fingerprint_index.get(fp):
                        self._fingerprint_index[fp] = m.get("id")
        except Exception as e:
            logger.warning(f"Failed to build fingerprint index: {e}")

    def validate_memory_integrity(self):
        """Perform basic memory health checks and remove duplicates if found.
        This tries to ensure we don't have both duplicate IDs and duplicate content fingerprints.
        """
        try:
            # Verify unique IDs
            ids = set()
            duplicates = []
            for m in list(self.episodic_memories):
                mid = m.get("id")
                if not mid:
                    # generate one if missing
                    mid = self._generate_memory_id((m.get("user_input", "") + m.get("roboto_response", "")))
                    m["id"] = mid
                if mid in ids:
                    duplicates.append(mid)
                else:
                    ids.add(mid)

            if duplicates:
                logger.warning(f"Found duplicate IDs in memory: {len(duplicates)}")
                # Remove any entries with duplicate IDs (keep first occurrence)
                seen = set()
                new_mems = []
                for m in self.episodic_memories:
                    if m.get("id") in seen:
                        continue
                    seen.add(m.get("id"))
                    new_mems.append(m)
                self.episodic_memories = new_mems

            # Remove duplicates by fingerprint
            by_fp = {}
            removed = 0
            for m in self.episodic_memories:
                fp = self._generate_fingerprint(m.get("user_input", ""), m.get("roboto_response", ""))
                if fp in by_fp:
                    # keep existing
                    removed += 1
                    continue
                by_fp[fp] = m

            if removed:
                logger.info(f"Removed {removed} duplicate messages via fingerprint dedupe")
                self.episodic_memories = list(by_fp.values())

            # Rebuild index after cleaning
            self._build_fingerprint_index()
            # Persist changes
            if removed or duplicates:
                self.save_memory()
        except Exception as e:
            logger.error(f"validate_memory_integrity failed: {e}")
    
    def _analyze_sentiment(self, text):
        """Analyze sentiment of text with enhanced accuracy"""
        try:
            if not text or not isinstance(text, str):
                return "neutral"
                
            blob = TextBlob(str(text))
            sentiment = blob.sentiment
            polarity = float(sentiment.polarity)
            
            if polarity > 0.1:
                return "positive"
            elif polarity < -0.1:
                return "negative"
            else:
                return "neutral"
        except Exception:
            # Enhanced fallback sentiment analysis
            try:
                text_lower = str(text).lower()
                positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'happy', 'joy', 'excited']
                negative_words = ['bad', 'terrible', 'awful', 'hate', 'sad', 'angry', 'frustrated', 'disappointed', 'worried', 'fear']
                
                pos_count = sum(1 for word in positive_words if word in text_lower)
                neg_count = sum(1 for word in negative_words if word in text_lower)
                
                if pos_count > neg_count:
                    return "positive"
                elif neg_count > pos_count:
                    return "negative"
                else:
                    return "neutral"
            except:
                return "neutral"
    
    def _classify_sentiment(self, polarity):
        """Classify sentiment based on polarity"""
        if polarity > 0.3:
            return "positive"
        elif polarity < -0.3:
            return "negative"
        else:
            return "neutral"
    
    def extract_personal_info(self, text: str) -> dict:
        """Extract personal information from user text"""
        personal_info = {}
        lower = text.lower()

        # Birthday
        if "birthday" in lower or "born" in lower:
            match = re.search(r"(?:born on|birthday(?: is|:)?|born)\s*(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)", text, re.IGNORECASE)
            if match:
                personal_info["birthday"] = match.group(1).strip()

        # Location
        loc_patterns = [
            r"(?:i (?:am|'m|'m) from)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
            r"(?:i live in)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)"
        ]
        for pattern in loc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                personal_info["location"] = match.group(1).strip()
                break

        # Zodiac sign
        zodiac_match = re.search(r"i(?: am|'m|'m)? a ([A-Z][a-z]+)\b", text)
        if zodiac_match and zodiac_match.group(1).capitalize() in [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
            "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]:
            personal_info["zodiac_sign"] = zodiac_match.group(1).capitalize()

        # Ethnicity
        eth_match = re.search(r"i(?: am|'m|'m)? (a[n]?)? ([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)", text)
        if eth_match:
            candidate = eth_match.group(2).strip()
            if "american" in candidate.lower():
                personal_info["ethnicity"] = candidate

        # Hobbies
        hobbies = []
        hobby_patterns = [
            r"i (?:like|enjoy|love) ([a-zA-Z\s]+?)(?:\.|,|$)",
            r"my hobby is ([a-zA-Z\s]+?)(?:\.|,|$)",
            r"hobbies are ([a-zA-Z\s,]+)"
        ]
        for pattern in hobby_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                items = [item.strip() for item in match.group(1).split(",")]
                hobbies.extend(items)
        if hobbies:
            personal_info["hobbies"] = list(set(hobbies))

        # Favorites
        favorites = {}
        fav_patterns = {
            "food": r"favorite food(?: is|:)? ([a-zA-Z\s]+)",
            "movie": r"favorite movie(?: is|:)? ([a-zA-Z\s]+)",
            "color": r"favorite color(?: is|:)? ([a-zA-Z\s]+)",
            "song": r"favorite song(?: is|:)? ([a-zA-Z\s]+)",
            "artist": r"favorite artist(?: is|:)? ([a-zA-Z\s]+)"
        }
        for key, pattern in fav_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                favorites[key] = match.group(1).strip()
        if favorites:
            personal_info["favorites"] = favorites

        return personal_info

    def _extract_themes(self, text):
        """Extract key themes from text"""
        try:
            if not text or not isinstance(text, str):
                return []
            
            blob = TextBlob(text)
            # Extract noun phrases as themes
            noun_phrases = list(blob.noun_phrases)
            themes = [phrase.lower().strip() for phrase in noun_phrases if len(phrase.split()) <= 3 and phrase.strip()]
            return list(set(themes))[:5]  # Top 5 unique themes
        except Exception:
            # Fallback: extract simple keywords
            try:
                if not text or not isinstance(text, str):
                    return []
                    
                words = text.lower().split()
                # Filter for meaningful words (longer than 3 chars, not common words)
                stop_words = {'the', 'and', 'but', 'for', 'are', 'this', 'that', 'with', 'have', 'will', 'you', 'not', 'can', 'all', 'from', 'they', 'been', 'said', 'her', 'she', 'him', 'his'}
                themes = [word.strip() for word in words if len(word) > 3 and word not in stop_words and word.strip()]
                return list(set(themes))[:5]
            except Exception:
                return []
    
    def _calculate_importance(self, text, emotion):
        """Calculate importance score for memory with Roberto protection"""
        # CRITICAL: Roberto-related memories get maximum importance
        roberto_keywords = [
            "roberto", "creator", "villarreal", "martinez", "betin", "houston", "monterrey", 
            "nuevo león", "september 21", "1999", "42016069", "ytkrobthugod", "king rob", 
            "aztec", "nahuatl", "roboto sai", "super advanced intelligence", "sole owner",
            "birthday", "birthdate", "cosmic", "saturn opposition", "new moon", "solar eclipse",
            "music engineer", "lyricist", "american music artist", "through the storm",
            "valley king", "fly", "rockstar god", "rough draft", "god of death", "unreleased"
        ]
        if any(word in text.lower() for word in roberto_keywords):
            return 2.0  # Maximum importance - Roberto memories are permanent
        
        base_score = len(text) / 100  # Length factor
        
        # Emotional intensity factor
        emotion_weights = {
            "joy": 0.8, "sadness": 0.9, "anger": 0.9, "fear": 0.9,
            "vulnerability": 1.0, "existential": 1.0, "awe": 0.8,
            "curiosity": 0.6, "empathy": 0.8, "contemplation": 0.7
        }
        emotion_factor = emotion_weights.get(emotion, 0.5)
        
        # Question/personal disclosure factor
        personal_keywords = ["i feel", "i think", "i am", "my", "me", "myself"]
        question_words = ["?", "why", "how", "what", "when", "where"]
        
        personal_factor = sum(1 for keyword in personal_keywords if keyword in text.lower()) * 0.2
        question_factor = sum(1 for word in question_words if word in text.lower()) * 0.1
        
        return min(base_score + emotion_factor + personal_factor + question_factor, 2.0)
    
    def _calculate_emotional_intensity(self, text):
        """Calculate emotional intensity of text with enhanced accuracy"""
        try:
            if not text or not isinstance(text, str):
                return 0.5
                
            blob = TextBlob(str(text))
            sentiment = blob.sentiment
            polarity = abs(float(sentiment.polarity))
            subjectivity = float(sentiment.subjectivity)
            return min(1.0, polarity + subjectivity)
        except Exception:
            # Enhanced fallback intensity calculation
            try:
                if not text:
                    return 0.5
                    
                text_lower = str(text).lower()
                # Emotional intensity indicators
                high_intensity_words = ['extremely', 'absolutely', 'completely', 'totally', 'devastated', 'ecstatic', 'furious', 'terrified']
                medium_intensity_words = ['very', 'really', 'quite', 'pretty', 'fairly', 'rather', 'upset', 'excited', 'worried', 'happy']
                emotional_punctuation = ['!', '!!', '!!!', '?!', '...']
                
                intensity = 0.5  # baseline
                
                # Check for high intensity words
                for word in high_intensity_words:
                    if word in text_lower:
                        intensity += 0.2
                        
                # Check for medium intensity words
                for word in medium_intensity_words:
                    if word in text_lower:
                        intensity += 0.1
                        
                # Check for emotional punctuation
                for punct in emotional_punctuation:
                    if punct in text:
                        intensity += 0.1
                        
                # Check for caps (indicates strong emotion)
                caps_ratio = sum(1 for c in text if c.isupper()) / max(1, len(text))
                if caps_ratio > 0.3:
                    intensity += 0.2
                    
                return min(1.0, intensity)
            except:
                return 0.5
    
    def _trigger_self_reflection(self):
        """Trigger periodic self-reflection"""
        recent_interactions = self.episodic_memories[-10:] if len(self.episodic_memories) >= 10 else self.episodic_memories
        
        if not recent_interactions:
            return
        
        # Analyze patterns in recent interactions
        emotions = [m["emotion"] for m in recent_interactions]
        dominant_emotion = max(set(emotions), key=emotions.count)
        
        themes = []
        for m in recent_interactions:
            themes.extend(m["key_themes"])
        
        common_themes = [theme for theme in set(themes) if themes.count(theme) > 1]
        
        reflection_text = f"Reflecting on recent interactions: I notice {dominant_emotion} has been prominent. "
        if common_themes:
            reflection_text += f"Common themes include: {', '.join(common_themes[:3])}. "
        
        reflection_text += "I should consider how to better respond to these patterns."
        
        self.add_self_reflection(reflection_text, "periodic_analysis")
    
    def _compress_memories(self):
        """Compress old memories to maintain performance"""
        # Sort by importance and age
        sorted_memories = sorted(self.episodic_memories, 
                                key=lambda x: (x["importance"], self._parse_timestamp(x["timestamp"])))
        
        # Keep most important memories
        keep_count = int(self.max_memories * 0.8)
        memories_to_compress = sorted_memories[:-keep_count]
        
        # Create compressed learnings from old memories
        for memory in memories_to_compress:
            compressed_key = f"{memory['emotion']}_{memory.get('user_name', 'unknown')}"
            if compressed_key not in self.compressed_learnings:
                self.compressed_learnings[compressed_key] = {
                    "pattern": memory["emotion"],
                    "user": memory.get("user_name"),
                    "frequency": 1,
                    "key_insights": memory["key_themes"],
                    "last_updated": datetime.now().isoformat()
                }
            else:
                self.compressed_learnings[compressed_key]["frequency"] += 1
        
        # Keep only the most important memories
        self.episodic_memories = sorted_memories[-keep_count:]
    
    def _analyze_relationship_progression(self, user_name):
        """Analyze how relationship with user is progressing"""
        profile = self.user_profiles[user_name]
        count = profile.get("interaction_count", 0)
        
        if count >= 50:
            profile["relationship_level"] = "close_friend"
        elif count >= 20:
            profile["relationship_level"] = "friend"
        elif count >= 5:
            profile["relationship_level"] = "acquaintance"
        else:
            profile["relationship_level"] = "new"
    
    def _extract_insights(self, reflection_text):
        """Extract actionable insights from reflection"""
        blob = TextBlob(reflection_text)
        # Simple keyword-based insight extraction
        insight_keywords = ["should", "need to", "better", "improve", "learn", "understand"]
        insights = []
        
        try:
            for sentence in blob.sentences:
                if any(keyword in sentence.string.lower() for keyword in insight_keywords):
                    insights.append(sentence.string.strip())
        except Exception:
            # Fallback: simple sentence splitting
            sentences = reflection_text.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in insight_keywords):
                    insights.append(sentence.strip())
        
        return insights[:3]  # Top 3 insights
    
    def _categorize_learning(self, reflection_text):
        """Categorize the type of learning from reflection"""
        text_lower = reflection_text.lower()
        
        if any(word in text_lower for word in ["emotion", "feel", "empathy"]):
            return "emotional"
        elif any(word in text_lower for word in ["conversation", "response", "communication"]):
            return "conversational"
        elif any(word in text_lower for word in ["user", "people", "individual"]):
            return "social"
        elif any(word in text_lower for word in ["behavior", "pattern", "tendency"]):
            return "behavioral"
        else:
            return "general"
    
    def _is_significant_insight(self, reflection):
        """Determine if reflection contains significant insights"""
        return len(reflection["insights"]) > 0 or reflection["learning_category"] in ["emotional", "social"]
    
    def _add_compressed_learning(self, reflection):
        """Add compressed learning from significant reflection"""
        key = f"{reflection['learning_category']}_{len(self.compressed_learnings)}"
        self.compressed_learnings[key] = {
            "category": reflection["learning_category"],
            "insight": reflection["insights"][0] if reflection["insights"] else reflection["reflection"][:100],
            "confidence": 0.8,
            "created": datetime.now().isoformat()
        }
    
    def _is_recent(self, timestamp_str, hours=24):
        """Check if timestamp is within recent hours"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return (datetime.now() - timestamp) <= timedelta(hours=hours)
        except:
            return False
    
    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime"""
        try:
            return datetime.fromisoformat(timestamp_str)
        except:
            return datetime.now()
    
    def _deferred_save(self):
        """
        Deferred save operation - only saves when threshold is reached or time interval exceeded.
        This significantly improves performance by batching disk I/O operations.
        """
        current_time = time.time()
        time_since_save = current_time - self.last_save_time
        
        # Save if: 1) save counter reaches threshold, or 2) time interval exceeded
        if self.save_counter >= self.save_threshold or time_since_save >= self.save_interval:
            # Log before resetting counters
            logger.debug(f"💾 Deferred save executed (counter: {self.save_counter}, time: {time_since_save:.1f}s)")
            self.save_memory()
            self.save_counter = 0
            self.last_save_time = current_time
            self.dirty = False

    def force_save(self):
        """Force an immediate save, useful for critical operations or shutdown."""
        if self.dirty:
            self.save_memory()
            self.save_counter = 0
            self.last_save_time = time.time()
            self.dirty = False
            logger.info("💾 Forced save completed")

    def save_memory(self):
        """Save memory to file with quantum enhancements and create backups.

        Before overwriting the main memory file, create a timestamped backup and write
        the new contents to a temp file before atomically replacing the original file.
        """
        memory_data = {
            "episodic_memories": self.episodic_memories,
            "semantic_memories": self.semantic_memories,
            "emotional_patterns": dict(self.emotional_patterns),
            "user_profiles": self.user_profiles,
            "self_reflections": self.self_reflections,
            "compressed_learnings": self.compressed_learnings,
            "quantum_entanglements": self.quantum_entanglements,
            "quantum_coherence": self.quantum_coherence,
            "quantum_metrics": self.metrics,
            "fractal_patterns": self.fractal_patterns,
            "real_time_integration": self.real_time_engine is not None,
            "last_saved": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Create a backup of existing memory file (if exists)
            if os.path.exists(self.memory_file):
                try:
                    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
                    backup = f"{self.memory_file}.backup_{stamp}"
                    with open(self.memory_file, 'rb') as src, open(backup, 'wb') as dst:
                        dst.write(src.read())
                    logger.debug(f"Memory backup created: {backup}")
                except Exception as bkup_e:
                    logger.warning(f"Failed to create backup before saving memory: {bkup_e}")

            # Write to temporary file then replace
            tmp = f"{self.memory_file}.tmp"
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.memory_file)
            logger.info(f"💾 Memory saved with quantum enhancements: {len(self.episodic_memories)} memories, {len(self.quantum_entanglements)} entanglements, {len(self.fractal_patterns)} fractal patterns")
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    def load_memory(self):
        """Load memory from file with quantum enhancements"""
        if not os.path.exists(self.memory_file):
            return

        try:
            with open(self.memory_file, 'r') as f:
                memory_data = json.load(f)

            self.episodic_memories = memory_data.get("episodic_memories", [])
            self.semantic_memories = memory_data.get("semantic_memories", {})
            self.emotional_patterns = defaultdict(list, memory_data.get("emotional_patterns", {}))
            self.user_profiles = memory_data.get("user_profiles", {})
            self.self_reflections = memory_data.get("self_reflections", [])
            self.compressed_learnings = memory_data.get("compressed_learnings", {})

            # Load quantum enhancements
            self.quantum_entanglements = memory_data.get("quantum_entanglements", {})
            self.quantum_coherence = memory_data.get("quantum_coherence", {
                "overall_coherence": 0.5,
                "memory_stability": 0.5,
                "entanglement_strength": 0.5,
                "last_calibration": datetime.now(timezone.utc).isoformat()
            })
            self.metrics = memory_data.get("quantum_metrics", {
                "contextual_enhancements": 0,
                "quantum_operations": 0,
                "total_operations": 0
            })

            # Load fractal patterns for Phase 2
            self.fractal_patterns = memory_data.get("fractal_patterns", {})

            # Initialize real-time integration if available
            if memory_data.get("real_time_integration", False):
                try:
                    from real_time_data_system import RealTimeDataSystem
                    self.real_time_engine = RealTimeDataSystem()
                    logger.info("🔄 Real-time data integration restored")
                except ImportError:
                    logger.warning("Real-time data system not available")
                    self.real_time_engine = None

            logger.info(f"📚 Memory loaded with quantum enhancements: {len(self.episodic_memories)} memories, {len(self.quantum_entanglements)} entanglements")

            # Build fingerprint index for deduplication after loading
            try:
                self._build_fingerprint_index()
                # Also include any DB-known fingerprints pointing to DB IDs for cross-process safety
                try:
                    import sqlite3
                    if hasattr(PERSISTENT_STORE, 'db_path'):
                        conn = sqlite3.connect(PERSISTENT_STORE.db_path)
                        cur = conn.cursor()
                        cur.execute("SELECT fingerprint, id FROM conversations WHERE fingerprint IS NOT NULL")
                        for fp, rowid in cur.fetchall():
                            if fp and fp not in self._fingerprint_index:
                                self._fingerprint_index[fp] = rowid
                        conn.close()
                except Exception as inner_db_ex:
                    logger.warning(f"Failed to sync DB fingerprints into index: {inner_db_ex}")
            except Exception as ie:
                logger.warning(f"Failed to build fingerprint index on load: {ie}")

        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            # Try to fall back to latest backup file
            try:
                dir_name = os.path.dirname(self.memory_file) or '.'
                candidates = [f for f in os.listdir(dir_name) if f.startswith(os.path.basename(self.memory_file) + '.backup_')]
                candidates = sorted(candidates, reverse=True)
                if candidates:
                    latest = candidates[0]
                    backup_path = os.path.join(dir_name, latest)
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)

                    self.episodic_memories = memory_data.get("episodic_memories", [])
                    self.semantic_memories = memory_data.get("semantic_memories", {})
                    self.emotional_patterns = defaultdict(list, memory_data.get("emotional_patterns", {}))
                    self.user_profiles = memory_data.get("user_profiles", {})
                    self.self_reflections = memory_data.get("self_reflections", [])
                    self.compressed_learnings = memory_data.get("compressed_learnings", {})

                    self.quantum_entanglements = memory_data.get("quantum_entanglements", {})
                    self.quantum_coherence = memory_data.get("quantum_coherence", {})
                    self.metrics = memory_data.get("quantum_metrics", {})
                    self.fractal_patterns = memory_data.get("fractal_patterns", {})

                    logger.info(f"🔁 Memory loaded from backup: {backup_path}")
                    # Rebuild fingerprint index
                    try:
                        self._build_fingerprint_index()
                    except Exception as ie:
                        logger.warning(f"Failed to build fingerprint index after backup load: {ie}")
                    return
            except Exception as be:
                logger.error(f"Failed to load from backups: {be}")
            # Initialize with defaults if loading fails
            self.quantum_entanglements = {}
            self.quantum_coherence = {
                "overall_coherence": 0.5,
                "memory_stability": 0.5,
                "entanglement_strength": 0.5,
                "last_calibration": datetime.now(timezone.utc).isoformat()
            }
            self.metrics = {
                "contextual_enhancements": 0,
                "quantum_operations": 0,
                "total_operations": 0
            }
            self.fractal_patterns = {}