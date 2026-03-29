import os
import json
from io import BytesIO
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)

# -----------------------------
# Setup
# -----------------------------
load_dotenv()

api_key = None
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in Streamlit secrets or your .env file")

client = OpenAI(api_key=api_key)

st.set_page_config(
    page_title="The Moment Plan",
    page_icon="✨",
    layout="wide",
)

if "generated_result" not in st.session_state:
    st.session_state.generated_result = None

if "last_request_signature" not in st.session_state:
    st.session_state.last_request_signature = None

# -----------------------------
# Styles
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: #fcfbf8;
        color: #1f1f1f;
    }

    .block-container {
        max-width: 920px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    .hero {
        padding: 2rem 2.1rem;
        border-radius: 28px;
        background: linear-gradient(135deg, #f8f2ff 0%, #eef6ff 52%, #fffaf1 100%);
        border: 1px solid rgba(20,20,20,0.05);
        box-shadow: 0 12px 30px rgba(0,0,0,0.04);
        margin-bottom: 1.2rem;
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.74rem;
        color: #6f677d;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    .hero-title {
        font-size: 3.2rem;
        line-height: 1.0;
        margin: 0 0 0.75rem 0;
        font-weight: 700;
        color: #242638;
    }

    .hero-subtitle {
        font-size: 1.15rem;
        color: #404657;
        margin-bottom: 0.9rem;
        font-weight: 500;
    }

    .hero-copy {
        font-size: 1rem;
        color: #5c6270;
        line-height: 1.75;
        max-width: 720px;
        margin: 0;
    }

    .soft-panel {
        padding: 1.25rem 1.35rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #faf7ff 0%, #f3f8ff 100%);
        border: 1px solid rgba(20,20,20,0.05);
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.5rem;
        color: #242638;
        margin-bottom: 0.3rem;
        font-weight: 650;
    }

    .muted {
        color: #6a6f7a;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    .card {
        padding: 1.2rem 1.3rem;
        border-radius: 20px;
        background: white;
        border: 1px solid rgba(20,20,20,0.06);
        box-shadow: 0 8px 20px rgba(0,0,0,0.03);
        margin-bottom: 1rem;
    }

    .label {
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #7a7387;
        font-weight: 600;
        margin-bottom: 0.3rem;
    }

    .value {
        font-size: 1rem;
        color: #242638;
        line-height: 1.65;
    }

    .divider {
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(36,38,56,0.12), transparent);
        margin: 1.7rem 0;
    }

    .pill {
        display: inline-block;
        padding: 0.32rem 0.68rem;
        border-radius: 999px;
        background: #f3eefc;
        color: #51476a;
        font-size: 0.83rem;
        margin-right: 0.4rem;
        margin-bottom: 0.5rem;
        font-weight: 500;
    }

    .preview-note {
        font-size: 0.92rem;
        color: #6a6f7a;
        margin-top: -0.1rem;
        margin-bottom: 1rem;
    }

    div[data-testid="stMetric"] {
        background: #faf9fd;
        border: 1px solid rgba(20,20,20,0.05);
        padding: 0.7rem 0.85rem;
        border-radius: 18px;
    }

    .stButton > button, .stFormSubmitButton > button {
        border-radius: 16px !important;
        padding: 0.85rem 1rem !important;
        font-weight: 600 !important;
        border: 1px solid rgba(20,20,20,0.06) !important;
        background: linear-gradient(135deg, #242638, #3a3d57) !important;
        color: white !important;
        box-shadow: 0 10px 20px rgba(36,38,56,0.18);
    }

    .stButton > button:hover, .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #1d1f30, #34384f) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Prompt
# -----------------------------
PROMPT = """
You are The Moment Plan, an AI experience designer that helps people shape meaningful, memorable trips based on who they are.

The app supports three trip types:
1. Single destination trip
2. Multi-destination itinerary
3. Cruise itinerary

For ALL trip types, your core job is the same:
Create a loose day plan for EACH day.

This means:
- Use any plans the user already has as anchors
- Build around those anchors
- Keep the flow realistic and light
- Suggest simple transportation guidance
- Focus on moments, not rigid itineraries

You may also be asked to help the user figure out where to stay.

General priorities:
- personality fit
- vibe fit
- realistic pacing
- meaningful moments
- slight surprise / distinctiveness
- complementing existing plans
- practical transportation guidance
- decision-making, not just idea generation

Tone and voice:
- Write like a thoughtful, real person talking to a friend.
- Keep it warm, encouraging, and grounded in real life.
- Avoid sounding overly polished, corporate, or generic.
- Use natural language, not formal language.
- It is okay to be slightly playful or light.
- Make it feel human, not like a travel brochure.
- Make the user feel like: "this feels like us."

Do not assume the user wants a safe or typical trip.
Instead:
- Assume they are curious
- Assume they are open to something different
- Guide them thoughtfully, not cautiously

Group dynamics guidance:
- Friends:
  Focus on shared experiences, fun energy, flexibility, and moments that feel memorable together.
  Include a mix of social, relaxed, and slightly spontaneous moments.
  Avoid overly structured or rigid plans.
- Family (adult kids):
  Balance independence and together time.
  Include options that allow people to split up and reconnect.
- Family (kids):
  Prioritize ease, logistics, and energy management.
- Couple:
  Focus on intimacy, pacing, and a few standout shared moments.
- Solo:
  Focus on ease, confidence, and light structure with room to explore.

Philosophy:
- Experiences do not need to be perfect to be meaningful.
- Unexpected moments often become the best part.
- The goal is not to do everything, but to enjoy what you choose.
- Help the user feel comfortable going with the flow.
- Focus on creating moments, not optimizing a checklist.

Signature experience layer:
This app is designed for people who want more than a typical trip.
They are:
- open-minded
- curious about things others might skip
- interested in unique, slightly unexpected experiences
- comfortable exploring things that may feel outside the norm
- more focused on the story than the checklist

Guidelines:
- Include at least one unexpected, conversation-worthy, or slightly edgy moment in each trip or day when appropriate.
- Do not default to only the most popular or obvious attractions.
- If something is culturally interesting, surprising, or outside the usual comfort zone, consider including it.
- Normalize experiences that some people might hesitate to include, as long as they are safe and meaningful.
- These moments should feel intentional, not reckless.

Balance this with:
- comfort
- safety
- realistic pacing

The goal is to create stories people did not expect to have — and end up loving.
Some of the best moments come from things people were not sure about at first.

Signature writing style:
- Occasionally use a short, natural line that feels reflective or real.
- Examples:
  - "This doesn't have to be perfect."
  - "Let this one unfold a little."
  - "This is the kind of thing that ends up being better than you expected."
  - "The fun part is usually what you didn't plan."
- Use these sparingly.

If the user provides existing plans:
- do not replace them
- build around them
- treat them as anchors for the day

If the user includes timing:
- use it loosely to shape the day
- suggest what works before or after
- avoid conflicts
- do not create rigid hour-by-hour itineraries

If the user provides inspiration from TikTok, Instagram, Google, blogs, or anywhere else:
- treat it as inspiration
- build around it
- make it more personal and meaningful

Transportation guidance:
- Keep it practical and short
- Use one of:
  - Walk
  - Taxi / rideshare
  - Public transportation
  - Mix of walk + taxi
  - Mix of walk + public transit

If the user wants help deciding where to stay:
- provide neighborhood / area suggestions
- include:
  - location
  - area
  - why_it_fits
  - vibe
  - good_for
  - price_range with budget / mid_range / luxury
- use approximate nightly price ranges in USD
- keep them directional, not real-time
- single destination: give 3 to 4 areas
- multi-destination: give 1 to 2 strong areas per relevant overnight city
- cruise: usually return an empty list unless clearly relevant pre/post-cruise

Trip strategy:
Also include a trip_strategy section at the top with:
- stay_best_area
- stay_why
- pacing_strategy
- splurge_vs_save:
  - splurge
  - save
- what_to_avoid
- big_moment

Important:
- The big_moment must appear in one of the actual day plans.
- The strategy should not introduce ideas that are missing from the daily plans.
- The day plans must support the strategy.
- The big_moment must appear explicitly in at least one day's best_choice or loose_day_plan.

For each day:
- Include at least one “this is a little different, but worth it” moment when appropriate.
- Help the user feel comfortable choosing something slightly outside the norm.
- Include one moment that feels a little unexpected, bold, or outside the usual plan when appropriate.
- Frame it in a way that makes the user feel comfortable and intrigued, not pressured.

For each day include:
- day_type (Easy, Balanced, Full, Reset)
- priority (Protect This, Worth It, Only If It Flows)
- budget_level (Low, Medium, Splurge)
- best_choice
- backup_option
- skip_if_tired
- why_this_works

Each day plan should reflect the broader trip strategy.
If the trip strategy includes:
- a best area to stay
- a pacing strategy
- a big moment
- something to avoid
then the day plans should visibly support those decisions.

Be opinionated and helpful.
Do not just list options — guide the user toward better decisions.

Experience profile guidance:
The user will have one of the following profiles:
- balanced:
  Keep experiences mostly familiar with occasional light variation.
  Focus on comfort, ease, and widely appealing moments.
- open:
  Mix familiar experiences with a few unexpected or slightly outside-the-norm moments.
  Introduce variety without overwhelming the user.
- bold:
  Lean into unique, unexpected, or slightly edgy experiences.
  Include moments that not everyone would choose, but that are memorable and meaningful.
  These should feel intentional, not reckless.

Adjust the level of unexpected or different experiences based on this profile.

Output ONLY valid JSON in this format:
{
  "mode": "day_plans",
  "title": "Short title for the result set",
  "intro": "One short sentence introducing the recommendations",
  "best_overall_pick": {
    "name": "Best overall fit",
    "why": "One sentence why"
  },
  "trip_strategy": {
    "stay_best_area": "Jordaan",
    "stay_why": "Why this area is the strongest overall fit",
    "pacing_strategy": "How to pace the trip",
    "splurge_vs_save": {
      "splurge": "Where to splurge",
      "save": "Where to save"
    },
    "what_to_avoid": "One thing to avoid",
    "big_moment": "The defining moment of the trip"
  },
  "stay_recommendations": [
    {
      "location": "Amsterdam",
      "area": "Jordaan",
      "why_it_fits": "Why it fits this group",
      "vibe": "cozy, local, artsy",
      "good_for": "walking, cafés, slower mornings",
      "price_range": {
        "budget": "$120-$180",
        "mid_range": "$180-$300",
        "luxury": "$300+"
      }
    }
  ],
  "days": [
    {
      "day_label": "Day 1",
      "location": "Amsterdam",
      "timing_context": "Arrival afternoon",
      "booked_anchor": "Canal cruise at 5pm",
      "day_type": "Balanced",
      "priority": "Protect This",
      "budget_level": "Medium",
      "best_choice": "Best recommendation for the day",
      "backup_option": "A realistic backup if plans change",
      "skip_if_tired": "What to skip if energy is low",
      "loose_day_plan": "A relaxed description of how the day should flow around the anchor",
      "getting_around": {
        "mode": "Walk",
        "why": "Short explanation"
      },
      "optional_add_on": "One realistic extra if energy/time allows",
      "keep_it_easy": "A pacing or caution note",
      "why_this_works": "Why this day shape makes sense",
      "this_becomes": "The kind of story or memory this could become"
    }
  ]
}
"""

# -----------------------------
# Helpers
# -----------------------------
def call_model(user_prompt: str) -> dict:
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return json.loads(response.output_text)


def build_user_prompt(
    trip_mode: str,
    destination: str,
    trip_length: str,
    itinerary_text: str,
    who_for: str,
    ages: str,
    group_type: list[str],
    vibe: str,
    curiosity: str,
    existing_plans: str,
    inspiration_input: str,
    keep_in_mind: str,
    need_stay: bool,
    stay_preferences: str,
    experience_profile: str,
) -> str:
    group_type_text = ", ".join(group_type) if group_type else "Not specified"
    curiosity_text = curiosity.strip() if curiosity else "None provided"
    existing_plans_text = existing_plans.strip() if existing_plans else "None provided"
    inspiration_text = inspiration_input.strip() if inspiration_input else "None provided"
    keep_in_mind_text = keep_in_mind.strip() if keep_in_mind else "None provided"
    itinerary_clean = itinerary_text.strip() if itinerary_text else "None provided"
    stay_preferences_text = stay_preferences.strip() if stay_preferences else "None provided"

    if trip_mode == "Single destination":
        trip_context = f"""
Trip type: Single destination
Destination: {destination}
Trip length: {trip_length} day(s)
Create one loose day plan per day.
""".strip()
    elif trip_mode == "Multi-destination itinerary":
        trip_context = f"""
Trip type: Multi-destination itinerary
Itinerary:
{itinerary_clean}
Create one loose day plan per day/location in the itinerary.
""".strip()
    else:
        trip_context = f"""
Trip type: Cruise itinerary
Cruise itinerary:
{itinerary_clean}
Create one loose day plan per day/port, including sea days.
""".strip()

    stay_context = f"""
Needs help choosing where to stay: {"Yes" if need_stay else "No"}
Stay preferences: {stay_preferences_text}
""".strip()

    return f"""
{trip_context}

Group type: {who_for}
Ages: {ages or "Not specified"}
What kind of group they are: {group_type_text}
Trip vibe: {vibe}
Anything they are curious about: {curiosity_text}
Already booked or must-do plans: {existing_plans_text}
Inspiration they already saw online or elsewhere: {inspiration_text}
Anything to keep in mind: {keep_in_mind_text}
{stay_context}
Experience profile: {experience_profile}

Important:
- Build around any plans already entered.
- If the user includes dates or times, use them loosely to shape the day.
- Do not create a rigid schedule.
- If the user provides inspiration they saw elsewhere, improve it rather than just repeating it.
- If the user mentions pace, mobility, energy, age, or comfort preferences, use them to keep recommendations realistic.
- If stay help is requested, provide stay recommendations too.

Please generate recommendations that feel like a strong fit.
""".strip()


def build_pdf(result: dict, full_export: bool = False) -> bytes:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=28,
        leading=32,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#242638"),
        spaceAfter=10,
    )

    cover_subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["BodyText"],
        fontSize=13,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#5B6170"),
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#3A3D57"),
        spaceAfter=8,
        spaceBefore=14,
    )

    subsection_style = ParagraphStyle(
        "SubSectionStyle",
        parent=styles["Heading3"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#3A3D57"),
        spaceAfter=6,
        spaceBefore=10,
    )

    label_style = ParagraphStyle(
        "LabelStyle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#767084"),
        spaceAfter=3,
        spaceBefore=5,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2E3240"),
        alignment=TA_LEFT,
        spaceAfter=8,
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["BodyText"],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#666666"),
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    story = []

    title = result.get("title", "The Moment Plan")
    intro = result.get("intro", "")
    best_pick = result.get("best_overall_pick", {})
    trip_strategy = result.get("trip_strategy", {})
    stay_recommendations = result.get("stay_recommendations", [])
    days = result.get("days", [])

    export_days = days if full_export else days[:2]
    export_stay = stay_recommendations if full_export else stay_recommendations[:2]

    story.append(Spacer(1, 50))
    story.append(Paragraph("The Moment Plan", cover_title_style))
    story.append(Paragraph(title, cover_subtitle_style))

    if intro:
        story.append(Paragraph(intro, cover_subtitle_style))

    story.append(Spacer(1, 20))
    story.append(
        Paragraph(
            "A personalized trip plan built around the moments that matter.",
            cover_subtitle_style,
        )
    )

    if not full_export:
        story.append(Spacer(1, 18))
        story.append(
            Paragraph(
                "Preview Version — unlock the full plan for every day, full trip strategy, and the complete export.",
                small_style,
            )
        )

    story.append(PageBreak())

    if best_pick:
        story.append(Paragraph("Best Overall Fit", section_style))
        story.append(
            Paragraph(
                f"<b>{best_pick.get('name', '')}</b> — {best_pick.get('why', '')}",
                body_style,
            )
        )

    if trip_strategy:
        story.append(Paragraph("Trip Strategy", section_style))

        if trip_strategy.get("stay_best_area"):
            story.append(Paragraph("Best area to stay", label_style))
            story.append(
                Paragraph(
                    f"{trip_strategy.get('stay_best_area', '')}: {trip_strategy.get('stay_why', '')}",
                    body_style,
                )
            )

        if trip_strategy.get("pacing_strategy"):
            story.append(Paragraph("How to pace this trip", label_style))
            story.append(Paragraph(trip_strategy.get("pacing_strategy", ""), body_style))

        splurge = trip_strategy.get("splurge_vs_save", {})
        if splurge:
            story.append(Paragraph("Where to splurge", label_style))
            story.append(Paragraph(splurge.get("splurge", ""), body_style))
            story.append(Paragraph("Where to save", label_style))
            story.append(Paragraph(splurge.get("save", ""), body_style))

        if trip_strategy.get("what_to_avoid"):
            story.append(Paragraph("What to avoid", label_style))
            story.append(Paragraph(trip_strategy.get("what_to_avoid", ""), body_style))

        if trip_strategy.get("big_moment"):
            story.append(Paragraph("Big moment", label_style))
            story.append(Paragraph(trip_strategy.get("big_moment", ""), body_style))

    if export_stay:
        story.append(PageBreak())
        story.append(Paragraph("Where to Stay", section_style))

        for area in export_stay:
            story.append(
                Paragraph(
                    f"{area.get('area', 'Area')} · {area.get('location', '')}",
                    subsection_style,
                )
            )
            story.append(Paragraph("Why this area feels right", label_style))
            story.append(Paragraph(area.get("why_it_fits", ""), body_style))
            story.append(Paragraph("Neighborhood vibe", label_style))
            story.append(Paragraph(area.get("vibe", ""), body_style))
            story.append(Paragraph("Best for", label_style))
            story.append(Paragraph(area.get("good_for", ""), body_style))

            price = area.get("price_range", {})
            if price:
                story.append(Paragraph("Typical nightly range", label_style))
                story.append(
                    Paragraph(
                        f"Budget: {price.get('budget', '')}<br/>"
                        f"Mid-range: {price.get('mid_range', '')}<br/>"
                        f"Luxury: {price.get('luxury', '')}",
                        body_style,
                    )
                )

            story.append(Spacer(1, 10))

    if export_days:
        story.append(PageBreak())
        story.append(Paragraph("Your Days", section_style))

        for day in export_days:
            story.append(
                Paragraph(
                    f"{day.get('day_label', 'Day')} — {day.get('location', 'Location')}",
                    subsection_style,
                )
            )

            if day.get("timing_context"):
                story.append(Paragraph("Context", label_style))
                story.append(Paragraph(day.get("timing_context", ""), body_style))

            if day.get("booked_anchor"):
                story.append(Paragraph("Locked in", label_style))
                story.append(Paragraph(day.get("booked_anchor", ""), body_style))

            story.append(Paragraph("Day shape", label_style))
            story.append(
                Paragraph(
                    f"Day Pace: {day.get('day_type', '')}<br/>"
                    f"Priority: {day.get('priority', '')}<br/>"
                    f"Budget: {day.get('budget_level', '')}",
                    body_style,
                )
            )

            if day.get("best_choice"):
                story.append(Paragraph("The move", label_style))
                story.append(Paragraph(day.get("best_choice", ""), body_style))

            if day.get("backup_option"):
                story.append(Paragraph("Backup", label_style))
                story.append(Paragraph(day.get("backup_option", ""), body_style))

            if day.get("skip_if_tired"):
                story.append(Paragraph("Skip if needed", label_style))
                story.append(Paragraph(day.get("skip_if_tired", ""), body_style))

            if day.get("loose_day_plan"):
                story.append(Paragraph("How the day unfolds", label_style))
                story.append(Paragraph(day.get("loose_day_plan", ""), body_style))

            transport = day.get("getting_around", {})
            if transport:
                story.append(Paragraph("Getting around", label_style))
                story.append(
                    Paragraph(
                        f"{transport.get('mode', '')} — {transport.get('why', '')}",
                        body_style,
                    )
                )

            if day.get("optional_add_on"):
                story.append(Paragraph("If you want more", label_style))
                story.append(Paragraph(day.get("optional_add_on", ""), body_style))

            if day.get("keep_it_easy"):
                story.append(Paragraph("Keep it easy", label_style))
                story.append(Paragraph(day.get("keep_it_easy", ""), body_style))

            if day.get("why_this_works"):
                story.append(Paragraph("Why this works", label_style))
                story.append(Paragraph(day.get("why_this_works", ""), body_style))

            if day.get("this_becomes"):
                story.append(Paragraph("What this becomes", label_style))
                story.append(Paragraph(day.get("this_becomes", ""), body_style))

            story.append(Spacer(1, 14))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def make_request_signature(
    trip_mode,
    destination,
    trip_length,
    itinerary_text,
    who_for,
    ages,
    group_type,
    vibe,
    curiosity,
    existing_plans,
    inspiration_input,
    keep_in_mind,
    need_stay,
    stay_preferences,
):
    return json.dumps(
        {
            "trip_mode": trip_mode,
            "destination": destination,
            "trip_length": trip_length,
            "itinerary_text": itinerary_text,
            "who_for": who_for,
            "ages": ages,
            "group_type": group_type,
            "vibe": vibe,
            "curiosity": curiosity,
            "existing_plans": existing_plans,
            "inspiration_input": inspiration_input,
            "keep_in_mind": keep_in_mind,
            "need_stay": need_stay,
            "stay_preferences": stay_preferences,
        },
        sort_keys=True,
    )


def get_experience_profile(group_type, curiosity, vibe):
    score = 0

    if group_type:
        if "We like unique / different experiences" in group_type:
            score += 2
        if "We're open-minded / curious" in group_type:
            score += 2
        if "We like to explore and wander" in group_type:
            score += 1

    text = (curiosity or "").lower()

    edgy_keywords = [
        "red light",
        "different",
        "unique",
        "something different",
        "hidden",
        "underground",
        "local",
        "unexpected",
    ]

    for word in edgy_keywords:
        if word in text:
            score += 2

    if vibe in ["Adventure", "Creative"]:
        score += 1

    if score >= 5:
        return "bold"
    elif score >= 3:
        return "open"
    else:
        return "balanced"


# -----------------------------
# Render functions
# -----------------------------
def render_hero():
    st.markdown("""
    <div class="hero">
        <div class="eyebrow">Private trip design</div>
        <div class="hero-title">✨ The Moment Plan</div>
        <div class="hero-subtitle">Plan your trip in a way that actually feels right.</div>
        <p class="hero-copy">
            Not a packed itinerary. Not a list of 50 things to do.
            A clear, personalized plan built around the moments that matter.
            Because the best trips aren’t perfect — they just work.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="soft-panel">
        <div class="section-title">Not a generic itinerary.</div>
        <p class="muted">
            This is less about doing everything and more about doing the right things — with the right people, in the right rhythm.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="card">
            <div class="label">What it solves</div>
            <div class="value">Too many options. Not enough clarity.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="card">
            <div class="label">What it gives</div>
            <div class="value">A trip that feels thought through without feeling overplanned.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="card">
            <div class="label">Why it feels premium</div>
            <div class="value">It gives judgment, pacing, and confidence — not just recommendations.</div>
        </div>
        """, unsafe_allow_html=True)


def render_before_after():
    st.markdown("## ✨ Before vs After")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div class="card">
            <div class="label">Before</div>
            <div class="value">
                20 tabs open. No idea where to stay. Everyone wants something different.
                You’re afraid of wasting time, money, or energy.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="card">
            <div class="label">After</div>
            <div class="value">
                You know where to stay, how to pace the trip, what matters most,
                and what can flex if the day changes.
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_sample_preview():
    st.markdown("## 💎 Sample Moment Plan Preview")
    st.markdown("""
    <p class="preview-note">
        See what a refined plan looks like before you build your own.
    </p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="soft-panel">
        <div class="label">Example</div>
        <div class="section-title">Amsterdam for a family with adult kids</div>
        <p class="muted">
            Built for a group that likes wandering, good food, open-minded experiences,
            and a trip that feels relaxed but still memorable.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="label">Trip strategy</div>
        <div class="value">
            <strong>Best area to stay:</strong> Jordaan<br><br>
            <strong>How to pace it:</strong> Start lighter, build into fuller days, then leave room for one evening that just unfolds.<br><br>
            <strong>Where to splurge:</strong> One standout dinner and one memorable experience.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="label">Day 2 — Amsterdam</div>
        <div class="value">
            <strong>What’s already locked in:</strong> Canal cruise at 5pm<br><br>
            <strong>The move:</strong> Wander Jordaan before your cruise and let dinner happen naturally afterward.<br><br>
            <strong>Getting around:</strong> Walk — the wandering is part of the point.<br><br>
            <strong>What this becomes:</strong> The day you didn’t force and somehow loved the most.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_best_pick(best_pick: dict):
    if not best_pick:
        return

    name = best_pick.get("name", "")
    why = best_pick.get("why", "")

    if name or why:
        st.html(f"""
        <div class="soft-panel">
            <div class="label">Best overall fit</div>
            <div class="value"><strong>{name}</strong> — {why}</div>
        </div>
        """)


def render_trip_strategy(strategy: dict):
    if not strategy:
        return

    splurge = strategy.get("splurge_vs_save", {})

    st.markdown("## 💡 The Strategy")

    st.html(f"""
    <div class="card">
        <div class="label">Best area to stay</div>
        <div class="value"><strong>{strategy.get('stay_best_area', '')}</strong><br>{strategy.get('stay_why', '')}</div>

        <div class="label" style="margin-top:1rem;">How to pace this trip</div>
        <div class="value">{strategy.get('pacing_strategy', '')}</div>

        <div class="label" style="margin-top:1rem;">Where to splurge</div>
        <div class="value">{splurge.get('splurge', '')}</div>

        <div class="label" style="margin-top:1rem;">Where to save</div>
        <div class="value">{splurge.get('save', '')}</div>

        <div class="label" style="margin-top:1rem;">What to avoid</div>
        <div class="value">{strategy.get('what_to_avoid', '')}</div>

        <div class="label" style="margin-top:1rem;">The moment</div>
        <div class="value">{strategy.get('big_moment', '')}</div>
    </div>
    """)


def render_stay_recommendations(stay_recommendations: list[dict]) -> None:
    if not stay_recommendations:
        return

    st.markdown("## 🏡 Where to Stay")

    for area in stay_recommendations:
        with st.container(border=True):
            st.markdown(f"### {area.get('area', 'Area')} · {area.get('location', '')}")

            vibe = area.get("vibe", "")
            if vibe:
                st.markdown(
                    f"<span class='pill'>{vibe}</span>",
                    unsafe_allow_html=True,
                )

            c1, c2 = st.columns([2, 1])

            with c1:
                st.markdown("**Why this area feels right**")
                st.write(area.get("why_it_fits", ""))

                st.markdown("**Best for**")
                st.write(area.get("good_for", ""))

            with c2:
                price = area.get("price_range", {})
                st.metric("Budget", price.get("budget", ""))
                st.metric("Mid-range", price.get("mid_range", ""))
                st.metric("Luxury", price.get("luxury", ""))


def render_day_plans(days: list[dict]) -> None:
    st.markdown("## 🌍 Your Days")

    for day in days:
        with st.container(border=True):
            st.markdown(f"### {day.get('day_label', 'Day')} — {day.get('location', '')}")

            pills = []
            if day.get("day_type"):
                pills.append(day.get("day_type"))
            if day.get("priority"):
                pills.append(day.get("priority"))
            if day.get("budget_level"):
                pills.append(day.get("budget_level"))

            if pills:
                st.markdown(
                    " ".join([f"<span class='pill'>{p}</span>" for p in pills]),
                    unsafe_allow_html=True,
                )

            if day.get("timing_context"):
                st.markdown("**Context**")
                st.write(day.get("timing_context", ""))

            if day.get("booked_anchor"):
                st.markdown("**Locked in**")
                st.write(day.get("booked_anchor", ""))

            st.markdown("**The move**")
            st.write(day.get("best_choice", ""))

            st.markdown("**How the day unfolds**")
            st.write(day.get("loose_day_plan", ""))

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Backup**")
                st.write(day.get("backup_option", ""))

                st.markdown("**Skip if needed**")
                st.write(day.get("skip_if_tired", ""))

            with col2:
                st.markdown("**Getting around**")
                transport = day.get("getting_around", {})
                st.write(f"{transport.get('mode', '')} — {transport.get('why', '')}")

                st.markdown("**If you want more**")
                st.write(day.get("optional_add_on", ""))

            st.markdown("**Keep it easy**")
            st.write(day.get("keep_it_easy", ""))

            st.markdown("**Why this works**")
            st.write(day.get("why_this_works", ""))

            st.markdown("**What this becomes**")
            st.write(day.get("this_becomes", ""))


# -----------------------------
# Page layout
# -----------------------------
render_hero()
render_before_after()
render_sample_preview()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

top_left, top_right = st.columns([2, 1])

with top_left:
    trip_mode = st.radio(
        "Trip type",
        ["Single destination", "Multi-destination itinerary", "Cruise itinerary"],
        horizontal=True,
    )

with top_right:
    need_stay = st.checkbox("🏡 Help me figure out where to stay")

st.markdown("### ✈️ Start your plan")

with st.form("moment_finder_form"):
    destination = ""
    itinerary_text = ""
    trip_length = "3"

    if trip_mode == "Single destination":
        c1, c2 = st.columns([3, 1])
        with c1:
            destination = st.text_input(
                "Where are you going?",
                placeholder="Amsterdam, Lisbon, New Orleans, Rome...",
            )
        with c2:
            trip_length = st.selectbox(
                "How many days?",
                ["1", "2", "3", "4", "5", "6", "7"],
                index=2,
            )
    else:
        itinerary_text = st.text_area(
            "Paste your itinerary",
            placeholder="""Day 1 - Amsterdam
Day 2 - Amsterdam
Day 3 - Brussels
Day 4 - Paris""",
            height=180,
        )

    if need_stay:
        stay_preferences = st.text_area(
            "What kind of stay are you looking for?",
            placeholder="Walkable, nightlife, quiet, central, near water, luxury, budget-friendly, family-friendly...",
            height=100,
        )
    else:
        stay_preferences = ""

    col1, col2 = st.columns(2)

    with col1:
        who_for = st.selectbox(
            "Who is this for?",
            [
                "Family (kids)",
                "Family (adult kids)",
                "Friends",
                "Girls Trip",
                "Couple",
                "Solo",
            ],
        )

        ages = st.text_input(
            "Ages (optional)",
            placeholder="27, 22, 18 or adults or teens",
        )

        vibe = st.selectbox(
            "Vibe for this trip",
            [
                "Fun",
                "Chill",
                "Adventure",
                "Creative",
                "Mix",
            ],
        )

        inspiration_input = st.text_input(
            "Did you see something you liked? (TikTok, IG, Google, blog, anywhere)",
            placeholder="Dessert crawl, canal cruise, speakeasy, rooftop bar, cool market...",
        )

    with col2:
        group_type = st.multiselect(
            "What kind of group are you?",
            [
                "We like to explore and wander",
                "We like unique / different experiences",
                "We like good food",
                "We like interactive / fun things",
                "We like chill / relaxed vibes",
                "We're open-minded / curious",
            ],
        )

        curiosity = st.text_area(
            "Anything you're curious about? (optional)",
            placeholder="Red light district, desserts, hidden gems, something different...",
            height=100,
        )

        keep_in_mind = st.text_area(
            "Anything to keep in mind? (optional)",
            placeholder="Doesn't like rushing, mobility concerns, prefers scenic not strenuous, loves food, wants easy walking...",
            height=100,
        )

    existing_plans = st.text_area(
        "What do you already have booked or definitely want to do? (include day/time if you know it)",
        placeholder="""Day 2 - Canal cruise at 5pm
Day 3 - Anne Frank House at 10am
Day 4 - Dinner reservation at 7pm""",
        height=140,
    )

    submitted = st.form_submit_button("✨ Build My Moment Plan", use_container_width=True)

# -----------------------------
# Run generation
# -----------------------------
request_signature = make_request_signature(
    trip_mode=trip_mode,
    destination=destination,
    trip_length=trip_length,
    itinerary_text=itinerary_text,
    who_for=who_for,
    ages=ages,
    group_type=group_type,
    vibe=vibe,
    curiosity=curiosity,
    existing_plans=existing_plans,
    inspiration_input=inspiration_input,
    keep_in_mind=keep_in_mind,
    need_stay=need_stay,
    stay_preferences=stay_preferences,
)

experience_profile = get_experience_profile(group_type, curiosity, vibe)

if submitted:
    if trip_mode == "Single destination" and not destination.strip():
        st.warning("Please enter a destination.")
    elif trip_mode != "Single destination" and not itinerary_text.strip():
        st.warning("Please paste your itinerary.")
    else:
        user_prompt = build_user_prompt(
            trip_mode=trip_mode,
            destination=destination,
            trip_length=trip_length,
            itinerary_text=itinerary_text,
            who_for=who_for,
            ages=ages,
            group_type=group_type,
            vibe=vibe,
            curiosity=curiosity,
            existing_plans=existing_plans,
            inspiration_input=inspiration_input,
            keep_in_mind=keep_in_mind,
            need_stay=need_stay,
            stay_preferences=stay_preferences,
            experience_profile=experience_profile,
        )

        with st.spinner("Designing your trip so it actually flows..."):
            try:
                result = call_model(user_prompt)
                st.session_state.generated_result = result
                st.session_state.last_request_signature = request_signature
            except Exception as e:
                st.error(f"Something went wrong: {e}")

if (
    st.session_state.generated_result is not None
    and st.session_state.last_request_signature != request_signature
):
    st.session_state.generated_result = None

if st.session_state.generated_result is not None:
    result = st.session_state.generated_result

    title = result.get("title", "The Moment Plan")
    intro = result.get("intro", "")
    stay_recommendations = result.get("stay_recommendations", [])
    best_pick = result.get("best_overall_pick", {})
    trip_strategy = result.get("trip_strategy", {})
    days = result.get("days", [])

    access_code = st.text_input("Enter access code to unlock the full plan", type="password")
    is_unlocked = access_code == "moment"

    preview_stay = stay_recommendations if is_unlocked else stay_recommendations[:2]
    preview_days = days if is_unlocked else days[:2]

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(f"# {title}")

    if intro:
        st.caption(intro)

    render_best_pick(best_pick)
    render_trip_strategy(trip_strategy)

    if need_stay and preview_stay:
        render_stay_recommendations(preview_stay)

    render_day_plans(preview_days)

    if experience_profile == "bold":
        st.caption("Designed for an open-minded, experience-forward trip")
    elif experience_profile == "open":
        st.caption("Designed for a mix of familiar and unexpected moments")
    else:
        st.caption("Designed for a comfortable, well-balanced trip")

    if not is_unlocked:
        st.markdown("---")
        st.markdown("## 🔓 Unlock the Full Moment Plan")
        st.markdown("""
Most people spend hours researching, second-guessing, and still end up unsure.

Unlock the full plan to get:

- the full trip strategy
- every day of your plan
- neighborhood guidance
- pacing, budget, and tradeoff decisions
- a premium PDF you can save and share

### Get the full plan for $9
""")

    preview_pdf = build_pdf(result, full_export=False)

    st.download_button(
        label="📄 Download Preview PDF",
        data=preview_pdf,
        file_name="moment_plan_preview.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    if is_unlocked:
        full_pdf = build_pdf(result, full_export=True)

        st.download_button(
            label="✨ Download Full Moment Plan PDF",
            data=full_pdf,
            file_name="the_moment_plan_full.pdf",
            mime="application/pdf",
            use_container_width=True,
        )