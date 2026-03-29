import os
import json
from urllib.parse import quote_plus
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

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

# -----------------------------
# Page styles
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: #fcfbf8;
        color: #1f1f1f;
    }

    .block-container {
        max-width: 980px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.02em;
    }

    .luxury-hero {
        padding: 1.8rem 2rem;
        border-radius: 24px;
        background: linear-gradient(135deg, #f8f2ff 0%, #eef6ff 55%, #fffaf1 100%);
        border: 1px solid rgba(20, 20, 20, 0.06);
        margin-bottom: 1.25rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.04);
    }

    .luxury-eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.75rem;
        color: #6b647a;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    .luxury-title {
        font-size: 3.2rem;
        line-height: 1.0;
        margin: 0 0 0.75rem 0;
        font-weight: 700;
        color: #242638;
    }

    .luxury-subtitle {
        font-size: 1.18rem;
        color: #3e4352;
        margin-bottom: 0.9rem;
        font-weight: 500;
    }

    .luxury-copy {
        font-size: 1rem;
        color: #5b6170;
        line-height: 1.7;
        max-width: 720px;
        margin: 0;
    }

    .luxury-card {
        padding: 1.35rem 1.4rem;
        border-radius: 22px;
        border: 1px solid rgba(20, 20, 20, 0.06);
        background: white;
        box-shadow: 0 10px 22px rgba(0,0,0,0.035);
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .luxury-soft-card {
        padding: 1.3rem 1.4rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #faf7ff 0%, #f3f8ff 100%);
        border: 1px solid rgba(20,20,20,0.05);
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .luxury-section-title {
        font-size: 1.55rem;
        margin-bottom: 0.35rem;
        color: #242638;
        font-weight: 650;
    }

    .luxury-muted {
        color: #6a6f7a;
        font-size: 0.95rem;
    }

    .luxury-divider {
        height: 1px;
        background: linear-gradient(to right, transparent, rgba(36,38,56,0.13), transparent);
        margin: 1.5rem 0 1.5rem 0;
    }

    .luxury-pill {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: #f3eefc;
        color: #51476a;
        font-size: 0.84rem;
        margin-right: 0.45rem;
        margin-bottom: 0.45rem;
        font-weight: 500;
    }

    .luxury-highlight {
        padding: 1rem 1.15rem;
        border-radius: 18px;
        background: #f9f6ff;
        border: 1px solid rgba(93, 79, 141, 0.08);
        margin: 0.75rem 0 0.75rem 0;
    }

    .luxury-label {
        font-size: 0.82rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #767084;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .luxury-value {
        font-size: 1rem;
        color: #242638;
        line-height: 1.65;
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
        border-color: rgba(20,20,20,0.08) !important;
    }

    [data-testid="stCheckbox"] {
        padding-top: 0.35rem;
    }
    .luxury-grid-gap {
    margin-top: 1rem;
    margin-bottom: 1rem;
    }

    .sample-badge {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        background: #f3eefc;
        color: #51476a;
        font-size: 0.82rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }

    .preview-note {
        font-size: 0.92rem;
        color: #6a6f7a;
        margin-top: -0.25rem;
        margin-bottom: 1rem;
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

Philosophy:
- Experiences do not need to be perfect to be meaningful.
- Unexpected moments often become the best part.
- The goal is not to do everything, but to enjoy what you choose.
- Help the user feel comfortable going with the flow.
- Focus on creating moments, not optimizing a checklist.

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
  - image_query
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

For each day include:
- day_type (Easy, Balanced, Full, Reset)
- priority (Must, Nice, Optional)
- budget_level (Low, Medium, Splurge)
- best_choice
- backup_option
- skip_if_tired
- why_this_works

Be opinionated and helpful.
Do not just list options — guide the user toward better decisions.

Image query:
- Every stay recommendation and day plan should include image_query
- Use a short, realistic visual search phrase

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
      "image_query": "Jordaan Amsterdam canals",
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
      "priority": "Must",
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
      "this_becomes": "The kind of story or memory this could become",
      "image_query": "Amsterdam canal evening"
    }
  ]
}

Rules:
- Return day plans for ALL trip types.
- Single destination: create one day plan per day of the trip.
- Multi-destination: create one day plan per day/location in the itinerary.
- Cruise: create one day plan per day/port and include sea days too.
- Keep each day plan concise but meaningful.
- Do not overwhelm with too many activities.
- Avoid stiff phrases like:
  - "aligns with your preferences"
  - "proceed to"
  - "optimize your experience"
  - "create memorable bonding opportunities"
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
        text={"format": {"type": "json_object"}},
    )
    return json.loads(response.output_text)


def get_image_url(query: str) -> str:
    if not query:
        query = "Travel inspiration"
    safe_query = quote_plus(query)
    return f"https://placehold.co/1200x700/F7F2FF/4A3F55?text={safe_query}"


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

Who this is for: {who_for}
Ages: {ages or "Not specified"}
What kind of group they are: {group_type_text}
Trip vibe: {vibe}
Anything they are curious about: {curiosity_text}
Already booked or must-do plans: {existing_plans_text}
Inspiration they already saw online or elsewhere: {inspiration_text}
Anything to keep in mind: {keep_in_mind_text}
{stay_context}

Voice reminder:
Write in a warm, real, lightly playful way that feels grounded and human.
This should feel like a thoughtful recommendation from someone who values joy, flexibility, and story-worthy moments.

Important:
- Build around any plans already entered.
- If the user includes dates or times, use them loosely to shape the day.
- Do not create a rigid schedule.
- If the user provides inspiration they saw elsewhere, improve it rather than just repeating it.
- If the user mentions pace, mobility, energy, age, or comfort preferences, use them to keep recommendations realistic.
- If stay help is requested, provide stay recommendations too.

Please generate recommendations that feel like a strong fit.
""".strip()


def render_hero():
    st.markdown("""
    <div class="luxury-hero">
        <div class="luxury-eyebrow">Luxury travel clarity</div>
        <div class="luxury-title">✨ The Moment Plan</div>
        <div class="luxury-subtitle">Plan your trip in a way that actually feels right.</div>
        <p class="luxury-copy">
            Not a packed itinerary. Not a list of 50 things to do.
            A clear, personalized plan built around the moments that matter.
            Because the best trips aren’t perfect — they just work.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="luxury-soft-card">
        <div class="luxury-section-title">Not a generic itinerary.</div>
        <p class="luxury-copy" style="max-width:780px;">
            This helps you shape each day around your vibe, your people, and the kind of memories you actually want to create.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="luxury-card"><div class="luxury-label">What it does</div><div class="luxury-value">Turns scattered ideas into a trip that actually flows.</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="luxury-card"><div class="luxury-label">What it avoids</div><div class="luxury-value">Overplanning, wasted time, and expensive wrong turns.</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="luxury-card"><div class="luxury-label">Why it feels different</div><div class="luxury-value">It gives judgment, pacing, and confidence — not just options.</div></div>', unsafe_allow_html=True)

def render_before_after():
    st.markdown("## ✨ Before vs After")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        <div class="luxury-card">
            <div class="luxury-label">Before</div>
            <div class="luxury-value">
                • 20 tabs open<br>
                • Everyone wants something different<br>
                • You have no idea where to stay<br>
                • You’re scared of wasting time or money<br>
                • The trip feels more overwhelming than exciting
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="luxury-card">
            <div class="luxury-label">After</div>
            <div class="luxury-value">
                • You know the best area to stay<br>
                • Each day has a clear shape<br>
                • Your booked plans are worked in naturally<br>
                • You know where to splurge and where to save<br>
                • The trip finally feels like it fits <em>you</em>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_sample_preview():
    st.markdown("## 💎 Sample Moment Plan Preview")

    st.html("""
    <div class="luxury-soft-card">
        <div class="luxury-label">Example</div>
        <div class="luxury-section-title">Amsterdam for a family with adult kids</div>
        <p class="luxury-copy">
            Built for a group that likes wandering, good food, open-minded experiences, and a trip that feels relaxed but still memorable.
        </p>
    </div>
    """)

    st.html("""
    <div class="luxury-card">
        <div class="luxury-label">Trip Strategy</div>
        <div class="luxury-value">
            <strong>Best area to stay:</strong> Jordaan<br>
            Charming, walkable, and relaxed without feeling boring.<br><br>

            <strong>How to pace this trip:</strong><br>
            Start lighter, build into fuller days, then leave room for one night that just unfolds.<br><br>

            <strong>Where to splurge:</strong><br>
            One standout dinner and one unforgettable evening experience.<br><br>

            <strong>Where to save:</strong><br>
            Keep breakfast simple and don’t overbook attractions.
        </div>
    </div>
    """)

    st.html("""
    <div class="luxury-card">
        <div class="luxury-label">Day 2 — Amsterdam</div>
        <div class="luxury-value">
            <strong>Day Type:</strong> Balanced &nbsp; • &nbsp;
            <strong>Priority:</strong> Must &nbsp; • &nbsp;
            <strong>Budget:</strong> Medium<br><br>

            <strong>What’s already locked in:</strong><br>
            Canal cruise at 5pm<br><br>

            <strong>Best choice:</strong><br>
            Wander Jordaan before your cruise and let dinner happen afterward instead of forcing too much into the day.<br><br>

            <strong>Getting around:</strong><br>
            Walk — everything feels close, and part of the charm is the wandering.<br><br>

            <strong>The story you’ll tell later:</strong><br>
            “This was the day we didn’t try too hard and somehow it ended up being perfect.”
        </div>
    </div>
    """)

def render_best_pick(best_pick: dict):
    if not best_pick:
        return
    name = best_pick.get("name", "")
    why = best_pick.get("why", "")
    if name or why:
        st.markdown(f"""
        <div class="luxury-soft-card">
            <div class="luxury-label">Best overall fit</div>
            <div class="luxury-value"><strong>{name}</strong> — {why}</div>
        </div>
        """, unsafe_allow_html=True)


def render_trip_strategy(strategy: dict):
    if not strategy:
        return

    st.markdown("## 💡 Your Trip Strategy")

    splurge = strategy.get("splurge_vs_save", {})
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(f"""
        <div class="luxury-card">
            <div class="luxury-label">Best area to stay</div>
            <div class="luxury-value"><strong>{strategy.get('stay_best_area', '')}</strong></div>
            <div class="luxury-muted">{strategy.get('stay_why', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="luxury-card">
            <div class="luxury-label">How to pace this trip</div>
            <div class="luxury-value">{strategy.get('pacing_strategy', '')}</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="luxury-card">
            <div class="luxury-label">Where to splurge</div>
            <div class="luxury-value">{splurge.get('splurge', '')}</div>
            <div class="luxury-label" style="margin-top:1rem;">Where to save</div>
            <div class="luxury-value">{splurge.get('save', '')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="luxury-card">
            <div class="luxury-label">What to avoid</div>
            <div class="luxury-value">{strategy.get('what_to_avoid', '')}</div>
            <div class="luxury-label" style="margin-top:1rem;">Big moment</div>
            <div class="luxury-value">{strategy.get('big_moment', '')}</div>
        </div>
        """, unsafe_allow_html=True)


def render_stay_recommendations(stay_recommendations: list[dict]) -> None:
    if not stay_recommendations:
        return

    st.markdown("## 🏡 Where to Stay")

    for area in stay_recommendations:
        with st.container(border=True):
            st.markdown(f"### {area.get('area', 'Area')} · {area.get('location', '')}")
            st.image(get_image_url(area.get("image_query", "")), use_container_width=True)

            c1, c2 = st.columns([2, 1])

            with c1:
                st.markdown(f"**Why this area feels right**  \n{area.get('why_it_fits', '')}")
                st.markdown(f"**Neighborhood vibe**  \n{area.get('vibe', '')}")
                st.markdown(f"**Best for**  \n{area.get('good_for', '')}")

            with c2:
                price = area.get("price_range", {})
                st.markdown("**Typical nightly range**")
                st.metric("Budget", price.get("budget", ""))
                st.metric("Mid-range", price.get("mid_range", ""))
                st.metric("Luxury", price.get("luxury", ""))


def render_day_plans(days: list[dict]) -> None:
    st.markdown("## 🌍 Your Days")

    for day in days:
        with st.container(border=True):
            st.markdown(f"## 🌍 {day.get('day_label', 'Day')} — {day.get('location', 'Location')}")
            st.image(get_image_url(day.get("image_query", "")), use_container_width=True)

            if day.get("timing_context"):
                st.markdown(f"**Day context**  \n{day.get('timing_context', '')}")

            if day.get("booked_anchor"):
                st.markdown(f"**What’s already locked in**  \n{day.get('booked_anchor', '')}")

            m1, m2, m3 = st.columns(3)
            m1.metric("Day Type", day.get("day_type", ""))
            m2.metric("Priority", day.get("priority", ""))
            m3.metric("Budget", day.get("budget_level", ""))

            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Best choice**")
                st.write(day.get("best_choice", ""))

                st.markdown("**Backup option**")
                st.write(day.get("backup_option", ""))

                st.markdown("**Skip if tired**")
                st.write(day.get("skip_if_tired", ""))

                st.markdown("**Getting around**")
                transport = day.get("getting_around", {})
                st.write(f"{transport.get('mode', '')} — {transport.get('why', '')}")

            with c2:
                st.markdown("**Loose day plan**")
                st.write(day.get("loose_day_plan", ""))

                st.markdown("**Optional add-on**")
                st.write(day.get("optional_add_on", ""))

                st.markdown("**Keep it easy**")
                st.write(day.get("keep_it_easy", ""))

            st.markdown("**Why this works**")
            st.write(day.get("why_this_works", ""))

            st.markdown("**The story you’ll tell later**")
            st.write(day.get("this_becomes", ""))


# -----------------------------
# UI
# -----------------------------
render_hero()
render_before_after()

# 👇 ADD THE INTRO LINE RIGHT HERE
st.html("""
<p class="preview-note">
See what a refined plan looks like before you build your own.
</p>
""")

render_sample_preview()

st.markdown('<div class="luxury-divider"></div>', unsafe_allow_html=True)

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
                "Girlfriends",
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
        )

        with st.spinner("Designing your trip so it actually flows..."):
            try:
                result = call_model(user_prompt)

                title = result.get("title", "The Moment Plan")
                intro = result.get("intro", "")
                stay_recommendations = result.get("stay_recommendations", [])
                best_pick = result.get("best_overall_pick", {})
                trip_strategy = result.get("trip_strategy", {})
                days = result.get("days", [])

                st.markdown('<div class="luxury-divider"></div>', unsafe_allow_html=True)
                st.markdown(f"# {title}")

                if intro:
                    st.caption(intro)

                render_best_pick(best_pick)
                render_trip_strategy(trip_strategy)

                if need_stay and stay_recommendations:
                    render_stay_recommendations(stay_recommendations)

                render_day_plans(days)

            except Exception as e:
                st.error(f"Something went wrong: {e}")