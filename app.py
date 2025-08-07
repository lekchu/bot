import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# Set page config FIRST
st.set_page_config(page_title="PPD Risk Predictor", page_icon="🧠", layout="wide")

# Load model and label encoder
model = joblib.load("ppd_model_pipeline.pkl")
le = joblib.load("label_encoder.pkl")

# Set animated background with image
def add_page_animation():
    st.markdown("""
    <style>
    .stApp {
        animation: fadeBg 20s ease-in-out infinite;
        background-image: url("background.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    }
    @keyframes fadeBg {
        0% { filter: brightness(1); }
        50% { filter: brightness(1.05); }
        100% { filter: brightness(1); }
    }
    </style>
    """, unsafe_allow_html=True)

add_page_animation()

# Sidebar navigation
if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"
    with st.sidebar:
      st.image("background.png", width=200)  # Adjust width as needed

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
    st.markdown("<h2 style='color: #f06292;'>📬 Share Your Feedback</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #ddd;'>We value your input and would love to hear your thoughts or suggestions!</p>", unsafe_allow_html=True)

    with st.form("feedback_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name")
        with col2:
            email = st.text_input("Your Email (optional)")

        message = st.text_area("Your Feedback", height=150)

        submitted = st.form_submit_button("✅ Submit Feedback")

        if submitted:
            st.success("Thank you for your valuable feedback! 💌")
            st.balloons()


elif menu == "🧰 Resources":
    st.markdown("<h2 style='color: #f06292;'>🧰 Helpful Links and Support</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #ccc;'>Here are some trusted resources for maternal mental health support and crisis assistance.</p>", unsafe_allow_html=True)

    resources = [
        {
            "name": "📞 National Mental Health Helpline",
            "link": "https://www.mohfw.gov.in",
            "desc": "24x7 toll-free helpline – 1800-599-0019"
        },
        {
            "name": "🌐 WHO Maternal Mental Health",
            "link": "https://www.who.int/news-room/fact-sheets/detail/mental-health-of-women-during-pregnancy-and-after-childbirth",
            "desc": "Facts and global insights on maternal mental health."
        },
        {
            "name": "📝 Postpartum Support International",
            "link": "https://www.postpartum.net/",
            "desc": "Worldwide support groups and educational resources."
        },
        {
            "name": "📚 EPDS Scale Guide",
            "link": "https://www.fresno.ucsf.edu/pediatrics/downloads/edinburghscale.pdf",
            "desc": "Official Edinburgh Postnatal Depression Scale PDF."
        }
    ]

    for res in resources:
        st.markdown(f"""
            <div style="background: #333; border-radius: 10px; padding: 15px; margin-bottom: 15px;">
                <h4 style="margin-bottom: 5px;">{res['name']}</h4>
                <p style="color: #bbb;">{res['desc']}</p>
                <a href="{res['link']}" target="_blank" style="color: #f06292; text-decoration: none;">🔗 Visit Site</a>
            </div>
        """, unsafe_allow_html=True)


import streamlit as st
from PIL import Image
import base64
from io import BytesIO

# --- Session State Initialization ---
if 'show_chat' not in st.session_state:
    st.session_state['show_chat'] = False
if 'feeling' not in st.session_state:
    st.session_state['feeling'] = None

# --- Load avatar image ---
def get_base64_avatar(image_path):
    with open(image_path, "rb") as img_file:
        b64_data = base64.b64encode(img_file.read()).decode()
    return b64_data

def show_avatar_button():
    avatar_img = Image.open("momly_avatar.png")
    buffered = BytesIO()
    avatar_img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    st.markdown("""
        <style>
        .avatar-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
        }
        </style>
        <div class="avatar-container">
        """, unsafe_allow_html=True)

    avatar_col1, avatar_col2, avatar_col3 = st.columns([8, 1, 1])
    with avatar_col3:
        if st.button("💬", help="Click to chat with MOMLY"):
            st.session_state.show_chat = not st.session_state.show_chat

    st.markdown("</div>", unsafe_allow_html=True)

# Show avatar button
show_avatar_button()

# --- MOMLY Comfort Content ---
momly_support = {
    "Sad": {
        "message": "I'm here with you. It's okay to feel sad.",
        "tips": [
            "Take a deep breath and rest.",
            "Call someone you trust.",
            "Write down how you feel.",
            "Watch something that makes you smile.",
            "Go for a short walk.",
            "Drink a glass of water slowly.",
            "Listen to calming music."
        ],
        "activity": [
            "Grab paper and pen.",
            "Write one thing you love about yourself.",
            "Stick it somewhere visible and smile!"
        ],
        "video": "https://www.youtube.com/watch?v=ZToicYcHIOU",
        "distraction": "Try watching a funny video or baking something sweet."
    },
    "Tired": {
        "message": "Rest is not a luxury. It's a necessity.",
        "tips": [
            "Lie down for 10 mins, close your eyes.",
            "Stretch your arms and back slowly.",
            "Drink cool water or herbal tea.",
            "Take a warm shower.",
            "Say 'I’m allowed to rest' out loud.",
            "Turn off unnecessary lights.",
            "Listen to soft nature sounds."
        ],
        "activity": [
            "Set a timer for 15 minutes.",
            "Lie flat, place a cool cloth on your eyes.",
            "Breathe deeply until timer ends."
        ],
        "video": "https://www.youtube.com/watch?v=ZBnPlqQFPKs",
        "distraction": "Read a short poem or doodle aimlessly."
    },
    "Anxious": {
        "message": "You're not alone. Anxiety comes and goes — let's manage it together.",
        "tips": [
            "Try the 5-4-3-2-1 grounding technique.",
            "Slowly inhale for 4 seconds, hold, exhale.",
            "Move your body—stretch or shake out your hands.",
            "Limit news and social media intake today.",
            "Talk to someone about your worry.",
            "Listen to calming music or white noise.",
            "Say, 'This feeling is temporary.'"
        ],
        "activity": [
            "Sit still and name 5 things you see.",
            "Name 4 things you can touch.",
            "Name 3 things you can hear.",
            "Name 2 things you can smell.",
            "Name 1 thing you can taste."
        ],
        "video": "https://www.youtube.com/watch?v=MIr3RsUWrdo",
        "distraction": "Try coloring a mandala or sorting old photos."
    },
    "Overwhelmed": {
        "message": "One moment at a time. You don’t have to do it all right now.",
        "tips": [
            "Write down just 3 small tasks.",
            "Prioritize one thing — ignore the rest for now.",
            "Take a 5-minute breathing break.",
            "Say 'It’s okay not to finish everything.'",
            "Put on calming background music.",
            "Ask for help, even if it’s small.",
            "Sit in silence for 2 minutes."
        ],
        "activity": [
            "Set a 10-min timer.",
            "Do a single task (e.g., fold 3 clothes).",
            "Celebrate yourself after you finish!"
        ],
        "video": "https://www.youtube.com/watch?v=hnpQrMqDoqE",
        "distraction": "Play a simple game on your phone or water your plants."
    },
    "Lonely": {
        "message": "You are deeply loved, even when it doesn’t feel like it.",
        "tips": [
            "Send a text to a friend or family.",
            "Write a letter to your future self.",
            "Pet a cat or dog (or watch a video).",
            "Remind yourself: 'I am not invisible.'",
            "Join an online support group.",
            "Listen to a podcast about healing.",
            "Say out loud: 'I matter.'"
        ],
        "activity": [
            "Write down 3 people who care about you.",
            "List 3 things you enjoy doing.",
            "Do one small kind thing for yourself."
        ],
        "video": "https://www.youtube.com/watch?v=2ZIpFytCSVc",
        "distraction": "Try journaling or creating a vision board on your phone."
    },
    "Angry": {
        "message": "Anger is valid. Let’s express it in a healthy way.",
        "tips": [
            "Take 5 deep breaths in and out.",
            "Squeeze a pillow or stress ball.",
            "Write a letter (you don’t have to send it).",
            "Splash cold water on your face.",
            "Go for a power walk.",
            "Punch a cushion (safely!).",
            "Say: 'I’m allowed to feel this.'"
        ],
        "activity": [
            "Put on music and dance hard for 3 mins.",
            "Yell into a pillow safely.",
            "Do 10 jumping jacks and rest."
        ],
        "video": "https://www.youtube.com/watch?v=VLPP3XmYxXg",
        "distraction": "Watch a comedy clip or sketch something messy."
    },
    "Lost": {
        "message": "Even when you feel lost, you're still moving forward.",
        "tips": [
            "Pause. Sit somewhere quiet.",
            "Ask yourself: 'What do I need right now?'",
            "Journal one sentence of what you’re feeling.",
            "Go outside and feel the air on your face.",
            "Read an inspiring quote.",
            "Say: 'I won’t feel this way forever.'",
            "Remind yourself of a past victory."
        ],
        "activity": [
            "Light a candle or turn on a soft light.",
            "Write one thing you're grateful for.",
            "Look in the mirror and smile — even just a little."
        ],
        "video": "https://www.youtube.com/watch?v=UNcZp3QGgRc",
        "distraction": "Organize a drawer or create a small playlist of songs you love."
    }
}

# --- MOMLY Chat Display ---
if st.session_state['show_chat']:
    with st.expander("💬 MOMLY is here for you", expanded=True):
        st.write("Hi! I'm MOMLY, your support buddy. How are you feeling today?")
        feeling = st.radio("Choose your feeling:", list(momly_support.keys()), horizontal=True, key="feeling_radio")

        if st.button("🎗️ Get Comforting Tips"):
            if feeling in momly_support:
                content = momly_support[feeling]
                st.success(content["message"])

                st.subheader("🌱 Tips")
                for i, tip in enumerate(content["tips"], 1):
                    st.markdown(f"- **Tip {i}:** {tip}")

                st.subheader("🧩 Try This Activity")
                for step in content["activity"]:
                    st.markdown(f"🔹 {step}")

                st.subheader("🎥 Recommended Video")
                st.video(content["video"])

                st.subheader("🎯 Mind Distraction")
                st.info(content["distraction"])
            else:
                st.warning("Please select a feeling.")

        st.button("🔄 Reset Chat", on_click=lambda: st.session_state.update({'show_chat': False, 'feeling': None}))

# --- Footer ---
st.markdown("""

    <div style="text-align: center; padding: 10px 0; color: #aaa; font-size: 0.9em;">
        © 2025 MOMLY | Empowering Maternal Wellbeing 
    </div>
""", unsafe_allow_html=True)
