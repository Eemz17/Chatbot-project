import streamlit as st
import random
import csv
import os
import json
from datetime import datetime

st.set_page_config(page_title="Cybersecurity Awareness Chatbot", page_icon="🛡️")

with open("scenarios.json", "r", encoding="utf-8") as file:
    SCENARIOS = json.load(file)

LEVEL_RULES = {
    1: {"questions": 3, "pass_mark": 2},
    2: {"questions": 3, "pass_mark": 2},
    3: {"questions": 1, "pass_mark": 0}
}

MAX_POSSIBLE_QUESTIONS = 7


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
        "final_message": "",
        "feedback_submitted": False
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_next_scenario():
    available = [
        scenario for scenario in SCENARIOS
        if scenario["difficulty"] == st.session_state.current_difficulty
        and scenario["message"] not in st.session_state.used_scenarios
    ]

    if not available:
        return None

    scenario = random.choice(available)
    st.session_state.used_scenarios.append(scenario["message"])
    return scenario


def move_or_finish():
    difficulty = st.session_state.current_difficulty
    level_rule = LEVEL_RULES[difficulty]

    if st.session_state.level_question_count < level_rule["questions"]:
        st.session_state.current_scenario = get_next_scenario()
        return

    if difficulty == 1:
        if st.session_state.level_score >= level_rule["pass_mark"]:
            st.session_state.current_difficulty = 2
            st.session_state.level_score = 0
            st.session_state.level_question_count = 0
            st.session_state.current_scenario = get_next_scenario()
        else:
            st.session_state.finished = True
            st.session_state.final_message = "You completed Level 1, but did not reach the score needed to progress to Level 2."

    elif difficulty == 2:
        if st.session_state.level_score >= level_rule["pass_mark"]:
            st.session_state.current_difficulty = 3
            st.session_state.level_score = 0
            st.session_state.level_question_count = 0
            st.session_state.current_scenario = get_next_scenario()
        else:
            st.session_state.finished = True
            st.session_state.final_message = "You completed Level 2, but did not reach the score needed to progress to the final advanced scenario."

    elif difficulty == 3:
        st.session_state.finished = True
        st.session_state.final_message = "You completed the final advanced scenario."


def save_feedback(score, total_answered, percentage, rating, comments):
    file_exists = os.path.isfile("feedback.csv")

    with open("feedback.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Timestamp",
                "Score",
                "Total Answered",
                "Percentage",
                "Rating",
                "Comment"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            score,
            total_answered,
            f"{percentage:.0f}",
            rating,
            comments
        ])


def reset_chatbot():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


initialise_state()

st.title("🛡️ Cybersecurity Awareness Chatbot")

if not st.session_state.started:
    st.subheader("Participant Instructions")

    st.write("""
    This chatbot will show you short cybersecurity scenarios based on phishing and social engineering threats.

    You will begin with Level 1 scenarios. If you answer at least 2 out of 3 correctly, you will progress to Level 2. 
    If you answer at least 2 out of 3 Level 2 scenarios correctly, you will progress to one final advanced scenario.

    For each scenario, choose the action you think is safest. After each answer, you will receive feedback explaining the safer response.

    Please do not enter your name, email address, student number, password, or any personal information.
    """)

    consent = st.checkbox("I understand the instructions and agree to take part in this test.")

    if consent:
        if st.button("Start Chatbot"):
            st.session_state.started = True
            st.session_state.current_scenario = get_next_scenario()
            st.rerun()

else:
    if not st.session_state.finished:
        scenario = st.session_state.current_scenario

        if scenario is None:
            st.session_state.finished = True
            st.session_state.final_message = "No more scenarios are available."
            st.rerun()

        st.subheader(f"Level {st.session_state.current_difficulty}")
        st.caption(
            f"Question {st.session_state.level_question_count + 1} of "
            f"{LEVEL_RULES[st.session_state.current_difficulty]['questions']} at this level"
        )

        st.info(scenario["message"])

        if not st.session_state.answered:
            st.write("Choose the safest response:")

            for option in scenario["options"]:
                if st.button(option):
                    was_correct = option == scenario["correct"]

                    st.session_state.total_answered += 1
                    st.session_state.level_question_count += 1

                    if was_correct:
                        st.session_state.score += 1
                        st.session_state.level_score += 1
                        result_message = "✅ Correct"
                    else:
                        result_message = "❌ Not quite"

                    st.session_state.last_feedback = f"""
                    {result_message}

                    **Feedback:** {scenario["feedback"]}
                    """

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

    else:
        st.subheader("Final Results")

        percentage = (st.session_state.score / st.session_state.total_answered) * 100 if st.session_state.total_answered > 0 else 0

        st.write(st.session_state.final_message)
        st.write(f"Your final score is **{st.session_state.score} out of {st.session_state.total_answered}**.")
        st.write(f"Percentage: **{percentage:.0f}%**.")

        if st.session_state.current_difficulty == 3 and st.session_state.final_message == "You completed the final advanced scenario.":
            st.success("Excellent progress. You reached the advanced scenario.")
        elif percentage >= 50:
            st.warning("Good attempt. Some threats were identified, but more practice would help.")
        else:
            st.error("More awareness training may be needed.")

        st.write("""
        Thank you for completing the chatbot.

        Please do not submit any personal information in the feedback box.
        """)

        st.subheader("Feedback")

        rating = st.slider(
            "How did the chatbot feel to use? 1 = worst, 5 = best",
            min_value=1,
            max_value=5,
            value=3
        )

        comments = st.text_area(
            "Optional: What did you think of the chatbot? Do not include personal information."
        )

        if not st.session_state.feedback_submitted:
            if st.button("Submit Feedback"):
                save_feedback(
                    st.session_state.score,
                    st.session_state.total_answered,
                    percentage,
                    rating,
                    comments
                )

                st.session_state.feedback_submitted = True
                st.success("Thank you. Your feedback has been recorded anonymously.")
        else:
            st.success("Feedback already submitted. Thank you.")

        if st.button("Restart"):
            reset_chatbot()