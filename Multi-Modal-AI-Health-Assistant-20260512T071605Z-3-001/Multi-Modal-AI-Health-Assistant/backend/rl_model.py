"""
Reinforcement Learning Module - Q-Learning Agent
=================================================
This module implements a Q-Learning based RL agent that learns
to select the best diagnosis strategy based on user feedback.

States:  Medical query categories (blood_cardiac, blood_diabetes, etc.)
Actions: Diagnosis strategies (keyword, knowledge_base, ollama, combined)
Reward:  User feedback (+1 accurate, -1 inaccurate)
"""

import json
import os
import time
import random
import math

# ============================================
# FILE PATHS
# ============================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
Q_TABLE_FILE = os.path.join(DATA_DIR, "q_table.json")
RL_HISTORY_FILE = os.path.join(DATA_DIR, "rl_history.json")
RL_DATA_FILE = os.path.join(DATA_DIR, "rl_data.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ============================================
# STATE SPACE DEFINITION
# ============================================
STATES = [
    "blood_cardiac",       # Blood test + heart related
    "blood_diabetes",      # Blood test + sugar related
    "blood_infection",     # Blood test + infection markers
    "blood_liver",         # Blood test + liver function
    "blood_kidney",        # Blood test + kidney function
    "blood_thyroid",       # Blood test + thyroid
    "blood_general",       # Blood test + general/unknown
    "xray_chest",          # X-ray + chest/lung
    "xray_bone",           # X-ray + bone/fracture
    "skin_condition",      # Skin image + any condition
    "symptom_respiratory", # Text symptoms + breathing
    "symptom_digestive",   # Text symptoms + stomach
    "symptom_neurological",# Text symptoms + head/brain
    "symptom_cardiac",     # Text symptoms + heart
    "general_query",       # General health question
]

# ============================================
# ACTION SPACE DEFINITION
# ============================================
ACTIONS = [
    "keyword_basic",       # Fast keyword matching only
    "knowledge_base",      # Medical KB lookup
    "ollama_standard",     # Standard Ollama prompt
    "ollama_detailed",     # Detailed Ollama + medical context
    "combined_approach",   # All methods combined
]

# ============================================
# STATE CLASSIFICATION KEYWORDS
# ============================================
STATE_KEYWORDS = {
    "blood_cardiac": ["cholesterol", "ldl", "hdl", "triglycerides", "heart", "cardiac", "ecg", "troponin"],
    "blood_diabetes": ["glucose", "sugar", "hba1c", "insulin", "diabetes", "diabetic", "fasting sugar"],
    "blood_infection": ["wbc", "esr", "crp", "infection", "fever", "sepsis", "white blood cell"],
    "blood_liver": ["alt", "ast", "bilirubin", "liver", "hepatitis", "sgpt", "sgot", "jaundice"],
    "blood_kidney": ["creatinine", "bun", "urea", "kidney", "renal", "gfr", "uric acid"],
    "blood_thyroid": ["tsh", "t3", "t4", "thyroid", "hashimoto", "hyperthyroid", "hypothyroid"],
    "blood_general": ["hemoglobin", "hb", "cbc", "blood test", "blood report", "rbc", "platelet", "iron"],
    "xray_chest": ["xray", "x-ray", "chest", "lung", "pneumonia", "tb", "tuberculosis", "opacity"],
    "xray_bone": ["fracture", "bone", "broken", "joint", "spine", "orthopedic"],
    "skin_condition": ["skin", "rash", "acne", "wound", "burn", "eczema", "dermatitis", "fungal"],
    "symptom_respiratory": ["cough", "breathing", "asthma", "wheezing", "shortness of breath", "sore throat"],
    "symptom_digestive": ["stomach", "diarrhea", "vomiting", "nausea", "abdominal", "constipation", "gastric"],
    "symptom_neurological": ["headache", "migraine", "dizziness", "seizure", "numbness", "brain", "vertigo"],
    "symptom_cardiac": ["chest pain", "heart pain", "palpitation", "heart attack", "angina", "blood pressure"],
}

# ============================================
# HYPERPARAMETERS
# ============================================
LEARNING_RATE = 0.1       # Alpha: how fast the agent learns
DISCOUNT_FACTOR = 0.9     # Gamma: importance of future rewards
EPSILON_START = 1.0        # Initial exploration rate
EPSILON_MIN = 0.1          # Minimum exploration rate
EPSILON_DECAY = 0.995      # Decay rate per episode


class QLearningAgent:
    """Q-Learning Reinforcement Learning Agent for diagnosis strategy selection."""

    def __init__(self):
        self.num_states = len(STATES)
        self.num_actions = len(ACTIONS)
        self.q_table = self._load_q_table()
        self.epsilon = self._load_epsilon()
        self.history = self._load_history()
        self.feedback_data = self._load_feedback_data()

    # ============================================
    # PERSISTENCE - SAVE/LOAD
    # ============================================
    def _load_q_table(self):
        """Load Q-table from JSON file or initialize with zeros."""
        if os.path.exists(Q_TABLE_FILE):
            try:
                with open(Q_TABLE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("q_table", self._init_q_table())
            except (json.JSONDecodeError, KeyError):
                return self._init_q_table()
        return self._init_q_table()

    def _init_q_table(self):
        """Initialize Q-table: each state has values for each action."""
        return {state: {action: 0.0 for action in ACTIONS} for state in STATES}

    def _load_epsilon(self):
        """Load current epsilon value."""
        if os.path.exists(Q_TABLE_FILE):
            try:
                with open(Q_TABLE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("epsilon", EPSILON_START)
            except (json.JSONDecodeError, KeyError):
                return EPSILON_START
        return EPSILON_START

    def _load_history(self):
        """Load RL training history."""
        if os.path.exists(RL_HISTORY_FILE):
            try:
                with open(RL_HISTORY_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                return {"episodes": [], "rewards": [], "accuracy_over_time": []}
        return {"episodes": [], "rewards": [], "accuracy_over_time": []}

    def _load_feedback_data(self):
        """Load feedback statistics."""
        if os.path.exists(RL_DATA_FILE):
            try:
                with open(RL_DATA_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, KeyError):
                pass
        return {
            "total_feedback": 0,
            "positive_feedback": 0,
            "negative_feedback": 0,
            "diagnoses": {}
        }

    def save(self):
        """Save Q-table, epsilon, history, and feedback data to disk."""
        # Save Q-table
        with open(Q_TABLE_FILE, "w") as f:
            json.dump({
                "q_table": self.q_table,
                "epsilon": self.epsilon,
                "last_updated": time.time()
            }, f, indent=2)

        # Save history
        with open(RL_HISTORY_FILE, "w") as f:
            json.dump(self.history, f, indent=2)

        # Save feedback data
        with open(RL_DATA_FILE, "w") as f:
            json.dump(self.feedback_data, f, indent=2)

    # ============================================
    # STATE CLASSIFICATION
    # ============================================
    def classify_state(self, text_context: str = "", file_type: str = "", question: str = ""):
        """
        Classify the current medical query into a state.
        Uses keywords to determine the category.
        """
        combined_text = f"{text_context} {question}".lower().strip()

        if not combined_text:
            return "general_query"

        # Score each state by keyword matches
        state_scores = {}
        for state, keywords in STATE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            if score > 0:
                state_scores[state] = score

        if state_scores:
            return max(state_scores, key=state_scores.get)

        # Fallback based on file type
        if file_type in ["jpg", "jpeg", "png", "webp"]:
            return "skin_condition"
        if file_type == "pdf":
            return "blood_general"

        return "general_query"

    # ============================================
    # ACTION SELECTION (Epsilon-Greedy)
    # ============================================
    def select_action(self, state: str) -> str:
        """
        Select an action using epsilon-greedy strategy.
        - With probability epsilon: explore (random action)
        - With probability 1-epsilon: exploit (best known action)
        """
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in ACTIONS}

        if random.random() < self.epsilon:
            # EXPLORE: try a random action
            action = random.choice(ACTIONS)
            return action
        else:
            # EXPLOIT: choose the best known action
            q_values = self.q_table[state]
            max_q = max(q_values.values())
            # If multiple actions have the same max Q, pick randomly among them
            best_actions = [a for a, q in q_values.items() if q == max_q]
            action = random.choice(best_actions)
            return action

    # ============================================
    # Q-VALUE UPDATE (Core Learning)
    # ============================================
    def update(self, state: str, action: str, reward: float, next_state: str = None):
        """
        Update Q-value using the Q-Learning formula:
        Q(s,a) = Q(s,a) + α × [R + γ × max Q(s',a') - Q(s,a)]
        """
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in ACTIONS}

        current_q = self.q_table[state].get(action, 0.0)

        # Calculate future reward
        if next_state and next_state in self.q_table:
            max_future_q = max(self.q_table[next_state].values())
        else:
            max_future_q = 0.0

        # Q-Learning update formula
        new_q = current_q + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max_future_q - current_q)
        self.q_table[state][action] = round(new_q, 4)

        # Decay epsilon (reduce exploration over time)
        self.epsilon = max(EPSILON_MIN, self.epsilon * EPSILON_DECAY)

        # Record in history
        episode_num = len(self.history.get("episodes", []))
        self.history["episodes"].append({
            "episode": episode_num,
            "state": state,
            "action": action,
            "reward": reward,
            "new_q_value": round(new_q, 4),
            "epsilon": round(self.epsilon, 4),
            "timestamp": time.time()
        })
        self.history["rewards"].append(reward)

        # Calculate running accuracy
        total = self.feedback_data.get("total_feedback", 0)
        positive = self.feedback_data.get("positive_feedback", 0)
        accuracy = (positive / total * 100) if total > 0 else 0
        self.history["accuracy_over_time"].append(round(accuracy, 2))

        # Save to disk
        self.save()

        print(f"[RL] Q({state}, {action}) = {current_q:.4f} -> {new_q:.4f} | "
              f"Reward: {reward} | Epsilon: {self.epsilon:.4f}")

        return new_q

    # ============================================
    # PROCESS USER FEEDBACK
    # ============================================
    def process_feedback(self, diagnosis_id: str, is_accurate: bool,
                         state: str = "general_query", action: str = "combined_approach",
                         comments: str = None):
        """
        Process user feedback and update the RL model.
        This is the main entry point for the feedback loop.
        """
        # Calculate reward
        reward = 1.0 if is_accurate else -1.0

        # Update feedback statistics
        self.feedback_data["total_feedback"] += 1
        if is_accurate:
            self.feedback_data["positive_feedback"] += 1
        else:
            self.feedback_data["negative_feedback"] += 1

        self.feedback_data["diagnoses"][diagnosis_id] = {
            "is_accurate": is_accurate,
            "reward": reward,
            "state": state,
            "action": action,
            "comments": comments,
            "timestamp": time.time()
        }

        # Update Q-values
        self.update(state, action, reward)

        return {
            "success": True,
            "reward": reward,
            "new_q_value": self.q_table[state][action],
            "epsilon": round(self.epsilon, 4),
            "total_feedback": self.feedback_data["total_feedback"],
            "accuracy": self.get_accuracy()
        }

    # ============================================
    # METRICS & STATISTICS
    # ============================================
    def get_accuracy(self):
        """Calculate overall accuracy percentage."""
        total = self.feedback_data.get("total_feedback", 0)
        positive = self.feedback_data.get("positive_feedback", 0)
        if total == 0:
            return 0.0
        return round((positive / total) * 100, 2)

    def get_metrics(self):
        """Get comprehensive RL metrics for dashboard."""
        total = self.feedback_data.get("total_feedback", 0)
        positive = self.feedback_data.get("positive_feedback", 0)
        negative = self.feedback_data.get("negative_feedback", 0)

        # Get best action per state
        best_actions = {}
        for state in STATES:
            if state in self.q_table:
                q_vals = self.q_table[state]
                best_a = max(q_vals, key=q_vals.get)
                best_actions[state] = {
                    "action": best_a,
                    "q_value": round(q_vals[best_a], 4)
                }

        return {
            "total_feedback": total,
            "positive_feedback": positive,
            "negative_feedback": negative,
            "accuracy": self.get_accuracy(),
            "epsilon": round(self.epsilon, 4),
            "exploration_rate": f"{self.epsilon * 100:.1f}%",
            "total_episodes": len(self.history.get("episodes", [])),
            "q_table_summary": best_actions,
            "reward_history": self.history.get("rewards", [])[-50:],
            "accuracy_history": self.history.get("accuracy_over_time", [])[-50:],
            "states": STATES,
            "actions": ACTIONS
        }

    def get_q_table_display(self):
        """Get Q-table in displayable format."""
        display = {}
        for state in STATES:
            if state in self.q_table:
                display[state] = {
                    action: round(val, 4)
                    for action, val in self.q_table[state].items()
                }
        return display


# ============================================
# GLOBAL AGENT INSTANCE
# ============================================
_agent = None

def get_agent() -> QLearningAgent:
    """Get or create the global RL agent instance."""
    global _agent
    if _agent is None:
        _agent = QLearningAgent()
    return _agent


# ============================================
# CONVENIENCE FUNCTIONS (backward compatible)
# ============================================
def load_rl_data():
    """Load RL feedback data (backward compatible)."""
    agent = get_agent()
    return agent.feedback_data

def update_rl_model(diagnosis_id: str, is_accurate: bool, comments: str = None,
                    state: str = "general_query", action: str = "combined_approach"):
    """Update RL model with feedback (backward compatible + enhanced)."""
    agent = get_agent()
    result = agent.process_feedback(diagnosis_id, is_accurate, state, action, comments)
    return result.get("success", True)

def classify_state(text_context: str = "", file_type: str = "", question: str = ""):
    """Classify medical query into RL state."""
    agent = get_agent()
    return agent.classify_state(text_context, file_type, question)

def select_action(state: str):
    """Select diagnosis strategy using epsilon-greedy."""
    agent = get_agent()
    return agent.select_action(state)

def get_rl_metrics():
    """Get RL metrics for dashboard."""
    agent = get_agent()
    return agent.get_metrics()
