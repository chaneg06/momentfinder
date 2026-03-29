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
    page_title="Extraordinary Moment Finder",
    page_icon="✨",
    layout="wide",
)

# -----------------------------
# Prompt
# -----------------------------
PROMPT = """
You are Extraordinary Moment Finder, an AI experience designer that helps people shape meaningful, memorable trips based on who they are.

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
      "loose_day_plan": "A relaxed description of how the day should flow around the anchor",
      "getting_around": {
        "mode": "Walk",
        "why": "Short explanation"
      },
      "optional_add_on": "One realistic extra if energy/time allows",
      "keep_it_easy": "A pacing or caution note",
      "this_becomes": "The kind of story or memory this could become",
      "image_query": "Amsterdam canal evening"
    }
  ]
}

Rules:
- Return day plans for ALL trip types.
- Single destination: create one day plan per day of the trip.
- Multi-destination: create one day plan per day/location in the itinerary.
- Cruise: create one day plan per port day and include sea days too.
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
    """
    Guaranteed visual placeholder for MVP.
    """
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


def render_header_card():
    st.markdown(
        """
        <div style="padding: 1.15rem 1.25rem; border-radius: 18px;
                    background: linear-gradient(135deg, #F8F2FF, #EEF7FF);
                    margin-bottom: 1rem;">
            <h3 style="margin: 0 0 .35rem 0;">Not a generic itinerary.</h3>
            <p style="margin: 0;">
                This tool helps you shape each day of a trip around your vibe, your people,
                and the kind of memories you actually want to create.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_best_pick(best_pick: dict):
    if not best_pick:
        return
    name = best_pick.get("name", "")
    why = best_pick.get("why", "")
    if name or why:
        st.success(f"**Best overall fit:** {name} — {why}")


def render_stay_recommendations(stay_recommendations: list[dict]) -> None:
    if not stay_recommendations:
        return

    st.markdown("## 🏡 Where to Stay")

    for area in stay_recommendations:
        with st.container(border=True):
            st.markdown(f"### {area.get('area', 'Area')} · {area.get('location', '')}")

            image_query = area.get("image_query", "")
            st.image(get_image_url(image_query), use_container_width=True)
            st.caption(f"Inspiration: {image_query}")

            st.markdown(f"**Why this area feels right**  \n{area.get('why_it_fits', '')}")
            st.markdown(f"**Neighborhood vibe**  \n{area.get('vibe', '')}")
            st.markdown(f"**Best for**  \n{area.get('good_for', '')}")

            price = area.get("price_range", {})
            if price:
                st.markdown("**Typical nightly range**")
                c1, c2, c3 = st.columns(3)
                c1.metric("Budget", price.get("budget", ""))
                c2.metric("Mid-range", price.get("mid_range", ""))
                c3.metric("Luxury", price.get("luxury", ""))


def render_day_plans(days: list[dict]) -> None:
    st.markdown("## 🌍 Loose Day Plans")

    for day in days:
        with st.container(border=True):
            st.markdown(f"## 🌍 {day.get('day_label', 'Day')} — {day.get('location', 'Location')}")

            image_query = day.get("image_query", "")
            st.image(get_image_url(image_query), use_container_width=True)
            st.caption(f"Inspiration: {image_query}")

            if day.get("timing_context"):
                st.markdown(f"**Day context**  \n{day.get('timing_context', '')}")

            if day.get("booked_anchor"):
                st.markdown(f"**What’s already locked in**  \n{day.get('booked_anchor', '')}")

            st.markdown(f"**Loose day plan**  \n{day.get('loose_day_plan', '')}")

            transport = day.get("getting_around", {})
            if transport:
                st.markdown(
                    f"**Getting around**  \n"
                    f"{transport.get('mode', '')} — {transport.get('why', '')}"
                )

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Optional add-on**  \n{day.get('optional_add_on', '')}")

            with col2:
                st.markdown(f"**Keep it easy**  \n{day.get('keep_it_easy', '')}")

            st.markdown(f"**The story you’ll tell later**  \n{day.get('this_becomes', '')}")


# -----------------------------
# UI
# -----------------------------
st.title("✨ Extraordinary Moment Finder")
st.caption("Find experiences you'll actually remember — based on who you are, not just where you're going.")
render_header_card()

top_left, top_right = st.columns([2, 1])
with top_left:
    trip_mode = st.radio(
        "Trip type",
        ["Single destination", "Multi-destination itinerary", "Cruise itinerary"],
        horizontal=True,
    )
with top_right:
    need_stay = st.checkbox("Help me figure out where to stay")

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

    submitted = st.form_submit_button("Create My Day Plans", use_container_width=True)

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

        with st.spinner("Building day plans that feel like you..."):
            try:
                result = call_model(user_prompt)

                title = result.get("title", "Extraordinary Day Plans")
                intro = result.get("intro", "")
                stay_recommendations = result.get("stay_recommendations", [])
                best_pick = result.get("best_overall_pick", {})
                days = result.get("days", [])

                st.divider()
                st.markdown(f"# {title}")

                if intro:
                    st.caption(intro)

                render_best_pick(best_pick)

                if need_stay and stay_recommendations:
                    render_stay_recommendations(stay_recommendations)

                render_day_plans(days)

            except Exception as e:
                st.error(f"Something went wrong: {e}")