import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# Load model and label encoder
model = joblib.load("ppd_model_pipeline.pkl")
le = joblib.load("label_encoder.pkl")

# Page config
st.set_page_config(page_title="PPD Risk Predictor", page_icon="🧠", layout="wide")

# Blue background animation
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

add_page_animation()

# Sidebar navigation
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

# TEST PAGE
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
        choice = st.radio(f"{idx}. {q_text}", list(options.keys()), key=f"q{idx}")
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
        st.markdown("<p style='color:#ccc; font-style:italic;'>Note: This screening result is generated based on the EPDS – Edinburgh Postnatal Depression Scale, a globally validated tool for postpartum depression assessment.</p>", unsafe_allow_html=True)

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

        # PDF report
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
        pdf.cell(200, 10, txt="(Assessment based on the EPDS - Edinburgh Postnatal Depression Scale)", ln=True)

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

# RESULT EXPLANATION
elif menu == "📊 Result Explanation":
    st.header("📊 Understanding Risk Levels")
    st.info("All assessments in this app are based on the EPDS (Edinburgh Postnatal Depression Scale), a trusted and validated 10-question tool used worldwide to screen for postpartum depression.")
    st.markdown("""
    | Risk Level | Meaning |
    |------------|---------|
    | **Mild (0)**     | Normal ups and downs |
    | **Moderate (1)** | Requires monitoring |
    | **Severe (2)**   | Suggests possible clinical depression |
    | **Profound (3)** | Needs professional help urgently |
    """)

# FEEDBACK
elif menu == "📬 Feedback":
    st.header("📬 Share Feedback")
    name = st.text_input("Your Name")
    message = st.text_area("Your Feedback")
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
if "momly_visible" not in st.session_state:
  st.session_state.momly_visible = False
import streamlit as st
from PIL import Image
import os

# Define feelings
feelings_data = {
    "Sad": {
        "tips": [
            "Take a short walk in fresh air.",
            "Write 3 things you're grateful for.",
            "Talk to a friend or family member.",
            "Listen to your favorite calming music.",
            "Practice deep breathing for 3 minutes.",
            "Drink a warm cup of tea.",
            "Give yourself permission to rest."
        ],
        "video": "https://www.youtube.com/watch?v=ZToicYcHIOU"  # Guided meditation
    },
    "Tired": {
        "tips": [
            "Try a power nap (10–20 mins).",
            "Stretch your body gently.",
            "Limit screen time for a while.",
            "Hydrate with water or herbal tea.",
            "Breathe deeply for 5 minutes.",
            "Give yourself rest without guilt.",
            "Listen to relaxing sleep sounds."
        ],
        "video": "https://www.youtube.com/watch?v=1vx8iUvfyCY"
    },
    "Anxious": {
        "tips": [
            "Do a 4-7-8 breathing exercise.",
            "Write down what worries you.",
            "Focus on things around you (5 senses).",
            "Repeat a calming affirmation.",
            "Move your body lightly.",
            "Pause and listen to calming music.",
            "Avoid caffeine for a while."
        ],
        "video": "https://www.youtube.com/watch?v=MIr3RsUWrdo"
    },
    "Lonely": {
        "tips": [
            "Send a message to someone you miss.",
            "Join an online community group.",
            "Go for a short walk outside.",
            "Write in a journal about how you feel.",
            "Read a comforting book or poem.",
            "Remind yourself: you’re not alone.",
            "Watch something uplifting."
        ],
        "video": "https://www.youtube.com/watch?v=WVz8ygN0JDk"
    },
    "Angry": {
        "tips": [
            "Pause. Take deep breaths before reacting.",
            "Step away from the situation briefly.",
            "Punch a pillow or squeeze a stress ball.",
            "Journal your emotions.",
            "Talk it out with someone safe.",
            "Listen to calming music.",
            "Do something active to release tension."
        ],
        "video": "https://www.youtube.com/watch?v=DbO3e4EDsT8"
    },
    "Overwhelmed": {
        "tips": [
            "Write down your top 3 priorities.",
            "Break tasks into smaller steps.",
            "Ask for help or delegate something.",
            "Do one thing at a time.",
            "Breathe: inhale for 4, exhale for 6.",
            "Take a 10-minute break.",
            "Remind yourself you’re doing enough."
        ],
        "video": "https://www.youtube.com/watch?v=hnpQrMqDoqE"
    }
}

# App title
st.markdown("### Hi, I'm **MOMLY!** How are you feeling today?")

# Mood selection
selected_feeling = st.radio(
    "", list(feelings_data.keys()), horizontal=True
)

if selected_feeling:
    st.success(f"Here's something for when you're feeling **{selected_feeling}**:")
    for i, tip in enumerate(feelings_data[selected_feeling]["tips"], 1):
        st.markdown(f"**Tip {i}:** {tip}")
    st.video(feelings_data[selected_feeling]["video"])

# Avatar click shows/hides chat
with st.sidebar:
    if os.path.exists("momly_avatar.png"):
        if st.button("💬 Chat with MOMLY"):
            st.session_state.show_chat = not st.session_state.get("show_chat", False)
    else:
        st.warning("MOMLY avatar not found.")

# Floating avatar (bottom right)
if os.path.exists("momly_avatar.png"):
    avatar = Image.open("momly_avatar.png")
    st.markdown(
        f"""
        <style>
        .chat-avatar {{
            position: fixed;
            bottom: 25px;
            right: 25px;
            z-index: 100;
        }}
        </style>
        <div class="chat-avatar">
            <a href="#momly-chat">
                <img src="https://raw.githubusercontent.com/lekchu/bot/main/momly_avatar.png" width="70">
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


# Show chatbot only when toggled
if st.session_state['show_momly']:
    show_momly_chat()

