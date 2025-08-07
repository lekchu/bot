import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go
from fpdf import FPDF
import base64
from streamlit_chat import message
import openai
import os

# Load OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Page config
st.set_page_config(page_title="PPD Risk Predictor", page_icon="🧠", layout="wide")

# UI styling
def add_page_animation():
    st.markdown("""
    <style>
    .stApp {
        animation: fadeBg 10s ease-in-out infinite;
        background-color: #001f3f;
    }
    @keyframes fadeBg {
        0% { background-color: #001f3f; }
        50% { background-color: #001f3f; }
        100% { background-color: #001f3f; }
    }
    </style>
    """, unsafe_allow_html=True)

def enhance_chat_ui():
    st.markdown("""
    <style>
    .block-container {
        padding-bottom: 160px;
    }
    </style>
    """, unsafe_allow_html=True)

add_page_animation()
enhance_chat_ui()

# Load model and label encoder
model = joblib.load("ppd_model_pipeline.pkl")
le = joblib.load("label_encoder.pkl")

# Navigation
if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"

st.session_state.page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📝 Take Test", "📊 Result Explanation", "📬 Feedback", "🧰 Resources"],
    index=["🏠 Home", "📝 Take Test", "📊 Result Explanation", "📬 Feedback", "🧰 Resources"].index(st.session_state.page),
    key="menu"
)

menu = st.session_state.page

# HOME
if menu == "🏠 Home":
    st.markdown("""
    <div style="text-align: center; padding: 40px 20px;">
        <h1 style="font-size: 3.5em; color: white;">POSTPARTUM DEPRESSION RISK PREDICTOR</h1>
        <h3 style="font-size: 1.6em; color: white;">Empowering maternal health through smart technology</h3>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📝 Start Test"):
        st.session_state.page = "📝 Take Test"
        st.rerun()

# TAKE TEST
elif menu == "📝 Take Test":
    st.header("📝 Questionnaire")

    for var, default in {
        'question_index': 0,
        'responses': [],
        'age': 25,
        'support': "Medium",
        'name': "",
        'place': ""
    }.items():
        if var not in st.session_state:
            st.session_state[var] = default

    idx = st.session_state.question_index

    if idx == 0:
        st.session_state.name = st.text_input("First Name", value=st.session_state.name)
        st.session_state.place = st.text_input("Your Place", value=st.session_state.place)
        st.session_state.age = st.slider("Your Age", 18, 45, value=st.session_state.age)
        st.session_state.support = st.selectbox("Level of Family Support", ["High", "Medium", "Low"],
                                                index=["High", "Medium", "Low"].index(st.session_state.support))
        if st.button("Start Questionnaire"):
            if st.session_state.name.strip() and st.session_state.place.strip():
                st.session_state.question_index += 1
                st.rerun()
            else:
                st.warning("Please enter your name and place before starting.")

    q_responses = [
        ("I have been able to laugh and see the funny side of things.",
         {"As much as I always could": 0, "Not quite so much now": 1, "Definitely not so much now": 2, "Not at all": 3}),
        ("I have looked forward with enjoyment to things",
         {"As much as I ever did": 0, "Rather less than I used to": 1, "Definitely less than I used to": 2, "Hardly at all": 3}),
        ("I have blamed myself unnecessarily when things went wrong",
         {"No, never": 0, "Not very often": 1, "Yes, some of the time": 2, "Yes, most of the time": 3}),
        ("I have been anxious or worried for no good reason",
         {"No, not at all": 0, "Hardly ever": 1, "Yes, sometimes": 2, "Yes, very often": 3}),
        ("I have felt scared or panicky for no very good reason",
         {"No, not at all": 0, "No, not much": 1, "Yes, sometimes": 2, "Yes, quite a lot": 3}),
        ("Things have been getting on top of me",
         {"No, I have been coping as well as ever": 0, "No, most of the time I have coped quite well": 1,
          "Yes, sometimes I haven't been coping as well as usual": 2, "Yes, most of the time I haven't been able to cope at all": 3}),
        ("I have been so unhappy that I have had difficulty sleeping",
         {"No, not at all": 0, "Not very often": 1, "Yes, sometimes": 2, "Yes, most of the time": 3}),
        ("I have felt sad or miserable",
         {"No, not at all": 0, "Not very often": 1, "Yes, quite often": 2, "Yes, most of the time": 3}),
        ("I have been so unhappy that I have been crying",
         {"No, never": 0, "Only occasionally": 1, "Yes, quite often": 2, "Yes, most of the time": 3}),
        ("The thought of harming myself has occurred to me",
         {"Never": 0, "Hardly ever": 1, "Sometimes": 2, "Yes, quite often": 3})
    ]

    if 1 <= idx <= 10:
        q_text, options = q_responses[idx - 1]
        choice = st.radio(f"{idx}. {q_text}", list(options.keys()), key=f"q_{idx}")
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back") and idx > 1:
            st.session_state.question_index -= 1
            st.session_state.responses.pop()
            st.rerun()
        if col2.button("Next ➡️"):
            st.session_state.responses.append(options[choice])
            st.session_state.question_index += 1
            st.rerun()

    elif idx == 11:
        name = st.session_state.name
        place = st.session_state.place
        age = st.session_state.age
        support = st.session_state.support
        q_values = st.session_state.responses
        score = sum(q_values)

        input_df = pd.DataFrame([{
            "Name": name,
            "Age": age,
            "FamilySupport": support,
            **{f"Q{i+1}": val for i, val in enumerate(q_values)},
            "EPDS_Score": score
        }])

        pred_encoded = model.predict(input_df.drop(columns=["Name"]))[0]
        pred_label = le.inverse_transform([pred_encoded])[0]

        st.success(f"{name}, your predicted PPD Risk is: **{pred_label}**")
        st.markdown("<p style='color:#ccc; font-style:italic;'>Note: This result is based on the EPDS – Edinburgh Postnatal Depression Scale, a globally validated screening tool.</p>", unsafe_allow_html=True)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pred_encoded,
            number={"suffix": " / 3"},
            gauge={
                "axis": {"range": [0, 3]},
                "bar": {"color": "deeppink"},
                "steps": [
                    {"range": [0, 1], "color": "lightgreen"},
                    {"range": [1, 2], "color": "gold"},
                    {"range": [2, 3], "color": "red"}
                ]
            },
            title={"text": "Risk Level"}
        ))
        st.plotly_chart(fig, use_container_width=True)

        tips = {
            "Mild": "- Stay active\n- Eat well\n- Talk to someone\n- Practice self-care",
            "Moderate": "- Monitor symptoms\n- Join a group\n- Share with family\n- Avoid isolation",
            "Severe": "- Contact a therapist\n- Alert family\n- Prioritize mental health\n- Reduce stressors",
            "Profound": "- Seek urgent psychiatric help\n- Talk to someone now\n- Call helpline\n- Avoid being alone"
        }

        st.subheader("💡 Personalized Tips")
        st.markdown(tips.get(pred_label, "Consult a professional immediately."))

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Postpartum Depression Risk Prediction", ln=True, align='C')
        pdf.cell(200, 10, txt=f"Name: {name}", ln=True)
        pdf.cell(200, 10, txt=f"Place: {place}", ln=True)
        pdf.cell(200, 10, txt=f"Age: {age}", ln=True)
        pdf.cell(200, 10, txt=f"Support Level: {support}", ln=True)
        pdf.cell(200, 10, txt=f"Total Score: {score}", ln=True)
        pdf.cell(200, 10, txt=f"Predicted Risk Level: {pred_label}", ln=True)
        pdf.cell(200, 10, txt="(Based on EPDS - Edinburgh Postnatal Depression Scale)", ln=True)

        pdf_output = f"{name.replace(' ', '_')}_PPD_Result.pdf"
        pdf.output(pdf_output)
        with open(pdf_output, "rb") as file:
            b64_pdf = base64.b64encode(file.read()).decode('utf-8')
            href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_output}">📥 Download Result (PDF)</a>'
            st.markdown(href, unsafe_allow_html=True)

        if st.button("🔄 Restart"):
            for key in ['question_index', 'responses', 'age', 'support', 'name', 'place']:
                st.session_state.pop(key, None)
            st.rerun()

# EXPLANATION
elif menu == "📊 Result Explanation":
    st.header("📊 Understanding Risk Levels")
    st.markdown("""
    | Risk Level | Meaning |
    |------------|---------|
    | **Mild (0)**     | Normal ups and downs |
    | **Moderate (1)** | Requires monitoring |
    | **Severe (2)**   | Suggests clinical depression |
    | **Profound (3)** | Needs urgent professional help |
    """)

# FEEDBACK
elif menu == "📬 Feedback":
    st.header("📬 Share Feedback")
    name = st.text_input("Your Name")
    message_input = st.text_area("Your Feedback")
    if st.button("Submit"):
        st.success("Thank you for your valuable feedback! 💌")

# RESOURCES
elif menu == "🧰 Resources":
    st.header("Helpful Links and Support")
    st.markdown("""
    - [📞 National Mental Health Helpline - 1800-599-0019](https://www.mohfw.gov.in)
    - [🌐 WHO Maternal Mental Health](https://www.who.int/news-room/fact-sheets/detail/mental-health-of-women-during-pregnancy-and-after-childbirth)
    - [📝 Postpartum Support International](https://www.postpartum.net/)
    """)
def momly_chatbot():
    import random
    from datetime import datetime
    import os
    import csv

    st.markdown("---")
    st.markdown("<h2 style='color: deeppink;'>💬 Chat with MOMLY</h2>", unsafe_allow_html=True)

    # Daily rotating quote
    quotes = [
        "You're doing better than you think 💛", "It's okay to cry. You're safe here 💧",
        "Rest is part of healing 🧸", "Your emotions are valid 🌷",
        "You are not alone 💗", "Gentle moments lead to gentle healing 🦋"
    ]
    st.success(f"🌸 *{quotes[datetime.now().day % len(quotes)]}*")

    # Reset chat
    if st.button("🔄 Reset Chat"):
        for key in ["messages", "current_mood", "recommend_index"]:
            st.session_state.pop(key, None)
        st.rerun()

    # Initialize session
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi 👋 I'm MOMLY. How are you feeling today?"}]
        st.session_state.current_mood = None
        st.session_state.recommend_index = 0

    # Mood response bank
    mood_data = {
        "tired": {
            "intro": "You’ve been holding a lot. That’s okay 💛 Want to try something gentle?",
            "recommendations": [
                ("🌬️ Breathing Exercise", "https://www.youtube.com/watch?v=aNXKjGFUlMs"),
                ("🎵 Gentle Lullaby", "https://www.youtube.com/watch?v=k2qgadSvNyU"),
                ("🛌 Just Rest a Moment", "Rest is healing. Even a few quiet minutes matter.")
            ]
        },
        "sad": {
            "intro": "I'm really sorry you're feeling this way 💗 I'm here for you.",
            "recommendations": [
                ("💬 Comforting Quote", "“This too shall pass. Be gentle with yourself.”"),
                ("🎵 Soft Music", "https://www.youtube.com/watch?v=2OEL4P1Rz04"),
                ("🤗 Just sit silently", "Silence is okay. I'm sitting with you.")
            ]
        },
        "angry": {
            "intro": "Anger is valid. Want help softening it gently?",
            "recommendations": [
                ("📝 Journal Prompt", "Write: What triggered this anger? What does it need from me?"),
                ("🎵 Calming Track", "https://www.youtube.com/watch?v=1ZYbU82GVz4"),
                ("😤 Deep Breaths", "Inhale slowly, exhale gently... you're safe now.")
            ]
        },
        "anxious": {
            "intro": "Anxiety feels like a storm. I'm with you through it 🕊️",
            "recommendations": [
                ("🎧 Guided Meditation", "https://www.youtube.com/watch?v=MIr3RsUWrdo"),
                ("📖 Soothing Affirmation", "“I am safe. I am doing my best. That is enough.”"),
                ("🤲 Grounding Exercise", "Name 5 things you can see. You're here, now.")
            ]
        },
        "happy": {
            "intro": "That’s so lovely to hear 😊 Want to make it last?",
            "recommendations": [
                ("🎶 Joyful Music", "https://www.youtube.com/watch?v=ZbZSe6N_BXs"),
                ("📝 Write what made you smile", "Even tiny joys are worth remembering 💌"),
                ("🕺 Move a little", "Dance, stretch, wiggle — feel the joy in your body ✨")
            ]
        }
    }

    # Display past messages
    for i, msg in enumerate(st.session_state.messages):
        bg = "#ffc0cb" if msg["role"] == "assistant" else "#ffffff"
        st.markdown(
            f"<div style='background-color:{bg}; padding: 10px; border-radius: 10px; margin:5px 0; color:black'>{msg['content']}</div>",
            unsafe_allow_html=True
        )

    # Mood buttons — only if none selected yet
    if st.session_state.current_mood is None:
        st.markdown("**How are you feeling right now?**")
        cols = st.columns(5)
        moods = ["😞 Sad", "😴 Tired", "😡 Angry", "😊 Happy", "😰 Anxious"]
        mood_keys = ["sad", "tired", "angry", "happy", "anxious"]
        for i in range(5):
            if cols[i].button(moods[i]):
                mood = mood_keys[i]
                st.session_state.current_mood = mood
                st.session_state.recommend_index = 0
                st.session_state.messages.append({"role": "user", "content": moods[i]})
                st.session_state.messages.append({"role": "assistant", "content": mood_data[mood]["intro"]})
                st.rerun()

    # Show recommendations one by one
    mood = st.session_state.current_mood
    if mood:
        index = st.session_state.recommend_index
        recs = mood_data[mood]["recommendations"]
        if index < len(recs):
            title, content = recs[index]
            st.markdown(f"**{title}**")
            if isinstance(content, str) and content.startswith("http"):
                st.markdown(f"[👉 Click here]({content})", unsafe_allow_html=True)
            else:
                st.info(content)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💡 Show another", key=f"next_{index}"):
                    st.session_state.recommend_index += 1
                    st.rerun()
            with col2:
                if st.button("❌ I'm okay now", key=f"done_{index}"):
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Okay 🧡 I'm always here if you want to talk again."
                    })
                    st.session_state.current_mood = None
                    st.session_state.recommend_index = 0
                    st.rerun()
        else:
            st.success("That’s all I had for now 💕 If you'd like more, you can reset the chat anytime.")

    # Optional: text input, always welcome
    user_input = st.chat_input("Type something you’d like to share...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        if st.session_state.current_mood is None:
            for mood_key in mood_data:
                if mood_key in user_input.lower():
                    st.session_state.current_mood = mood_key
                    st.session_state.recommend_index = 0
                    intro = mood_data[mood_key]["intro"]
                    st.session_state.messages.append({"role": "assistant", "content": intro})
                    st.rerun()
        fallback = "Thank you for sharing that. I'm here with you 🧸"
        st.session_state.messages.append({"role": "assistant", "content": fallback})



momly_chatbot()



