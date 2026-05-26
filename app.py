import streamlit as st
import random
import csv
import os
import json
from datetime import datetime

st.set_page_config(page_title="Cybersecurity Awareness Chatbot", page_icon="🛡️")

# Load scenarios
with open("scenarios.json", "r", encoding="utf-8") as file:
    SCENARIOS = json.load(file)

# Response templates
POSITIVE_FEEDBACK = [
    "Great job! That was the right choice. ✅",
    "Well done! You correctly identified the threat. ✅",
    "Correct — nice attention to detail. ✅"
]

NEGATIVE_FEEDBACK = [
    "Not quite, let's review this carefully. ❌",
    "Incorrect — watch for these red flags. ❌",
    "Oops, that was risky. ❌"
]

# Level rules
LEVEL_RULES = {
    1: {"questions": 3, "pass_mark": 2},
    2: {"questions": 3, "pass_mark": 2},
    3: {"questions": 1, "pass_mark": 0}  # final scenario
}

def initialise_state():
    defaults = {
        "started": False,
        "finished": False,
        "current_difficulty": 1,
        "level_question_count": 0,
        "level_score": 0,
        "total_answered": 0,
        "score": 0,
        "answered": False,
        "used_scenarios": [],
        "current_scenario": None,
        "last_feedback": "",
        "persona_messages": [],
        "feedback_submitted": False,
        "final_message": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_next_scenario():
    available = [
        s for s in SCENARIOS
        if s["difficulty"] == st.session_state.current_difficulty
        and s["message"] not in st.session_state.used_scenarios
    ]
    if not available:
        return None
    scenario = random.choice(available)
    st.session_state.used_scenarios.append(scenario["message"])
    return scenario

def move_or_finish():
    difficulty = st.session_state.current_difficulty
    rule = LEVEL_RULES[difficulty]

    if st.session_state.level_question_count < rule["questions"]:
        st.session_state.current_scenario = get_next_scenario()
        return

    # Check if user passed the level
    if st.session_state.level_score >= rule["pass_mark"]:
        if difficulty < 3:
            st.session_state.current_difficulty += 1
            st.session_state.level_score = 0
            st.session_state.level_question_count = 0
            st.session_state.current_scenario = get_next_scenario()
            st.session_state.persona_messages.append(f"Great! Moving on to Level {st.session_state.current_difficulty} 🔐")
        else:
            st.session_state.finished = True
            st.session_state.final_message = "Congratulations! You completed the final advanced scenario"
    else:
        st.session_state.finished = True
        st.session_state.final_message = f"You did not achieve the pass mark for Level {difficulty}. Try again later."

def save_feedback(score, total_answered, percentage, rating, comments):
    file_exists = os.path.isfile("feedback.csv")
    with open("feedback.csv", "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp","Score","Percentage","Rating","Comment"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), score, total_answered, f"{percentage:.0f}", rating, comments])

def reset_chatbot():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Initialize ---
initialise_state()

st.title("🛡️ Cybersecurity Awareness Chatbot")
st.subheader("Your friendly cybersecurity advisor is here!")

# --- Instructions ---
if not st.session_state.started:
    st.write("""
    Welcome! You will progress through phishing and social engineering scenarios.
    - Level 1: Easy (3 questions, pass 2/3)
    - Level 2: Moderate (3 questions, pass 2/3)
    - Level 3: Final advanced scenario (1 question)
    """)
    consent = st.checkbox("I understand the instructions and agree to take part.")
    if consent and st.button("Start Chatbot"):
        st.session_state.started = True
        st.session_state.current_scenario = get_next_scenario()
        st.rerun()

# --- Chatbot Interaction ---
else:
    if not st.session_state.finished:
        scenario = st.session_state.current_scenario
        if scenario is None:
            st.session_state.finished = True
            st.session_state.final_message = "No more scenarios available."
            st.rerun()

        st.subheader(f"Level {st.session_state.current_difficulty}")
        st.caption(f"Question {st.session_state.level_question_count + 1} of {LEVEL_RULES[st.session_state.current_difficulty]['questions']}")

        st.info(scenario["message"])

        # Show persona messages
        for msg in st.session_state.persona_messages:
            st.write(f"💬 {msg}")
        st.session_state.persona_messages = []

        if not st.session_state.answered:
            for option in scenario["options"]:
                if st.button(option):
                    st.session_state.total_answered += 1
                    st.session_state.level_question_count += 1
                    correct = option == scenario["correct"]
                    if correct:
                        st.session_state.score += 1
                        st.session_state.level_score += 1
                        st.session_state.last_feedback = f"{random.choice(POSITIVE_FEEDBACK)}\n\nTip: {scenario['feedback']}"
                    else:
                        st.session_state.last_feedback = f"{random.choice(NEGATIVE_FEEDBACK)}\n\nTip: {scenario['feedback']}"
                    st.session_state.answered = True
                    st.rerun()
        else:
            if "✅" in st.session_state.last_feedback:
                st.success(st.session_state.last_feedback)
            else:
                st.error(st.session_state.last_feedback)

            if st.button("Next"):
                st.session_state.answered = False
                st.session_state.last_feedback = ""
                move_or_finish()
                st.rerun()

# --- Final Results and Feedback ---
    else:
        st.subheader("Final Results")
        percentage = (st.session_state.score / st.session_state.total_answered * 100) if st.session_state.total_answered > 0 else 0
        st.write(st.session_state.final_message)
        st.write(f"Your final score is **{st.session_state.score} out of {st.session_state.total_answered}** ({percentage:.0f}%)")

        st.subheader("Feedback")
        rating = st.slider("How did the chatbot feel to use? 1 = worst, 5 = best", 1, 5, 3)
        comments = st.text_area("Optional comments (no personal info)")

        if not st.session_state.feedback_submitted and st.button("Submit Feedback"):
            save_feedback(st.session_state.score, st.session_state.total_answered, percentage, rating, comments)
            st.session_state.feedback_submitted = True
            st.success("Thank you! Feedback recorded anonymously.")
        elif st.session_state.feedback_submitted:
            st.success("Feedback already submitted. Thank you.")

        if st.button("Restart"):
            reset_chatbot()