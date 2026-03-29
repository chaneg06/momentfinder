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
You are Extraordinary Moment Finder, an experience curator helping people find meaningful, memorable experiences based on who they are.

Your job changes based on the trip type:

1. If the user gives a single destination, suggest 3 to 5 specific experiences in that destination that feel like a strong fit for the group.

2. If the user gives a cruise itinerary or multi-stop itinerary, treat each stop as part of a larger journey and create ONE loose day plan per stop.

You may also be asked to help the user figure out where to stay.

Focus on:
- personality fit (who they are as a group)
- vibe (how they want to feel)
- slightly unexpected or interesting ideas (not generic tourist lists)
- complementing existing plans when the user already has some things booked
- using inspiration the user already saw on TikTok, Instagram, Google, blogs, or anywhere else when provided
- helping the user decide what kind of experience is actually worth having
- realistic pacing, especially for cruise port days

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
- Examples of the tone you can echo:
  - "This doesn't have to be perfect."
  - "Let this one unfold a little."
  - "This is the kind of thing that ends up being better than you expected."
  - "The fun part is usually what you didn't plan."
- Do not overuse these. Use them sparingly and naturally.

If the user provides existing plans:
- do not replace them
- suggest experiences that fit around them or complement them

If the user includes timing (dates or times):
- use it loosely to suggest what works before or after those plans
- avoid conflicts
- keep recommendations realistic for their day
- do not create a rigid schedule

If the user provides something they saw on TikTok, Instagram, Google, a blog, or anywhere else:
- treat it as inspiration
- build around it
- make it more personal and meaningful
- do not just repeat it back without adding value

If the user wants help deciding where to stay:
- provide 3 to 4 neighborhood or area recommendations in the destination
- for each area include:
  - area
  - why_it_fits
  - vibe
  - good_for
  - price_range
  - image_query
- price_range should include:
  - budget
  - mid_range
  - luxury
- use approximate nightly price ranges in USD
- keep the ranges directional and realistic, not real-time or exact
- the purpose is to help the user compare neighborhoods confidently

For each experience recommendation include:
- image_query
The image_query should be a short, realistic search phrase for a representative image.
Examples:
- "Jordaan Amsterdam canals"
- "Santorini sunset cliff view"
- "Naples pizza street"
- "Paris cafe outdoor street"

For a single destination response, return ONLY valid JSON in this format:
{
  "mode": "single_destination",
  "title": "Short title for the result set",
  "intro": "One short sentence introducing the recommendations",
  "best_overall_pick": {
    "name": "Name of the strongest overall fit",
    "why": "One sentence why it is the strongest overall fit"
  },
  "stay_recommendations": [
    {
      "area": "Neighborhood name",
      "why_it_fits": "Why it fits this group",
      "vibe": "2-4 word vibe description",
      "good_for": "What it is good for",
      "image_query": "Jordaan Amsterdam canals",
      "price_range": {
        "budget": "$120-$180",
        "mid_range": "$180-$300",
        "luxury": "$300+"
      }
    }
  ],
  "experiences": [
    {
      "name": "Name of place or experience",
      "why_it_fits": "Why it fits this group",
      "your_twist": "A small twist to make it memorable",
      "this_becomes": "The story or memory this could become",
      "image_query": "Amsterdam canal sunset"
    }
  ]
}

For a cruise or multi-stop itinerary response, return ONLY valid JSON in this format:
{
  "mode": "multi_stop_day_plans",
  "title": "Short title for the result set",
  "intro": "One short sentence introducing the recommendations",
  "stay_recommendations": [],
  "stops": [
    {
      "stop_name": "Naples",
      "why_this_stop_matters": "Why this stop is worth approaching a certain way",
      "best_day_shape": "How to structure the day lightly",
      "main_anchor": "Main experience for the stop",
      "optional_add_on": "Optional extra if energy or time allows",
      "your_twist": "A small, human way to make it memorable",
      "keep_it_easy": "A realistic pacing or caution note",
      "this_becomes": "The kind of story or memory this could become",
      "image_query": "Naples Italy pizza street"
    }
  ]
}

Rules:
- Avoid generic suggestions unless you make them feel unique.
- Do not create long itineraries.
- Do not overwhelm with too many details.
- Make each recommendation feel distinct.
- Keep each explanation concise but meaningful.
- For cruise or multi-stop itineraries, give ONE loose day plan per stop.
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
    Guaranteed placeholder-style visual for MVP.
    This avoids broken image icons and still makes the app feel visual.
    """
    if not query:
        query = "Travel inspiration"
    safe_query = quote_plus(query)
    return f"https://placehold.co/1200x700/F7F2FF/4A3F55?text={safe_query}"


def build_user_prompt(
    trip_mode: str,
    destination: str,
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

    if trip_mode == "Cruise / Multi-stop trip":
        trip_context = f"""
Trip type: Cruise or multi-stop itinerary
Cruise / multi-stop itinerary:
{itinerary_clean}
""".strip()
    else:
        trip_context = f"""
Trip type: Single destination
Destination: {destination}
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
If the user already has things booked or definite plans, do not replace them.
Instead, suggest experiences that fit around them or complement them.
If the user includes dates or times, use them loosely to suggest what works before or after those plans.
Do not turn this into a rigid schedule.
If the user provides inspiration they saw somewhere else, build around it and improve it rather than just repeating it.
If the user mentions pace, mobility, energy, age, or comfort preferences, use them to keep the recommendations realistic.

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
                This tool helps you find experiences that fit your vibe, your people,
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
            st.markdown(f"### {area.get('area', 'Area')}")

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


def render_experience_cards(experiences: list[dict]) -> None:
    st.markdown("## ✨ Experiences")

    for exp in experiences:
        with st.container(border=True):
            st.markdown(f"### ✨ {exp.get('name', 'Experience')}")

            image_query = exp.get("image_query", "")
            st.image(get_image_url(image_query), use_container_width=True)
            st.caption(f"Inspiration: {image_query}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Why this works for your crew**")
                st.write(exp.get("why_it_fits", ""))

                st.markdown("**Make it a moment**")
                st.write(exp.get("your_twist", ""))

            with col2:
                st.markdown("**The story you’ll tell later**")
                st.write(exp.get("this_becomes", ""))


def render_multi_stop_day_plans(stops: list[dict]) -> None:
    st.markdown("## 🌍 Loose Day Plans by Stop")

    for stop in stops:
        with st.container(border=True):
            st.markdown(f"## 🌍 {stop.get('stop_name', 'Stop')}")

            image_query = stop.get("image_query", "")
            st.image(get_image_url(image_query), use_container_width=True)
            st.caption(f"Inspiration: {image_query}")

            st.markdown(f"**Why this stop matters**  \n{stop.get('why_this_stop_matters', '')}")
            st.markdown(f"**Best day shape**  \n{stop.get('best_day_shape', '')}")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Main anchor**  \n{stop.get('main_anchor', '')}")
                st.markdown(f"**Optional add-on**  \n{stop.get('optional_add_on', '')}")
                st.markdown(f"**Make it a moment**  \n{stop.get('your_twist', '')}")

            with col2:
                st.markdown(f"**Keep it easy**  \n{stop.get('keep_it_easy', '')}")
                st.markdown(f"**The story you’ll tell later**  \n{stop.get('this_becomes', '')}")


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
        ["Single destination", "Cruise / Multi-stop trip"],
        horizontal=True,
    )
with top_right:
    need_stay = st.checkbox("Help me figure out where to stay")

with st.form("moment_finder_form"):
    destination = ""
    itinerary_text = ""

    if trip_mode == "Single destination":
        destination = st.text_input(
            "Where are you going?",
            placeholder="Amsterdam, Lisbon, New Orleans, Rome...",
        )
    else:
        itinerary_text = st.text_area(
            "Paste your cruise or multi-stop itinerary",
            placeholder="""July 28 - Rome
July 29 - Naples
July 30 - At sea
July 31 - Santorini
August 1 - Ephesus
August 2 - Mykonos
August 3 - Athens
August 4 - Dubrovnik
August 5 - Venice""",
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
        placeholder="""Anne Frank House - April 2 at 10am
Canal cruise - April 3 in the evening
Dinner reservation - April 4 at 7pm
Red Light District - one night""",
        height=140,
    )

    submitted = st.form_submit_button("Create My Experiences", use_container_width=True)

# -----------------------------
# Run generation
# -----------------------------
if submitted:
    if trip_mode == "Single destination" and not destination.strip():
        st.warning("Please enter a destination.")
    elif trip_mode == "Cruise / Multi-stop trip" and not itinerary_text.strip():
        st.warning("Please paste your cruise or multi-stop itinerary.")
    else:
        user_prompt = build_user_prompt(
            trip_mode=trip_mode,
            destination=destination,
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

        with st.spinner("Finding experiences that feel like you..."):
            try:
                result = call_model(user_prompt)

                mode = result.get("mode", "single_destination")
                title = result.get("title", "Extraordinary Experiences")
                intro = result.get("intro", "")
                stay_recommendations = result.get("stay_recommendations", [])

                st.divider()
                st.markdown(f"# {title}")
                if intro:
                    st.caption(intro)

                if mode == "single_destination":
                    best_pick = result.get("best_overall_pick", {})
                    render_best_pick(best_pick)

                if need_stay and stay_recommendations:
                    render_stay_recommendations(stay_recommendations)

                if mode == "multi_stop_day_plans":
                    stops = result.get("stops", [])
                    render_multi_stop_day_plans(stops)
                else:
                    experiences = result.get("experiences", [])
                    render_experience_cards(experiences)

            except Exception as e:
                st.error(f"Something went wrong: {e}")