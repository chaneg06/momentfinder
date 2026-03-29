import os
import json
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

# -----------------------------
# Setup
# -----------------------------
load_dotenv()

# Prefer Streamlit secrets if deployed, fall back to .env for local use
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
    layout="centered",
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
- price_range should include:
  - budget
  - mid_range
  - luxury
- use approximate nightly price ranges in USD
- keep the ranges directional and realistic, not real-time or exact
- the purpose is to help the user compare neighborhoods confidently

For a single destination response, return ONLY valid JSON in this format:
{
  "mode": "single_destination",
  "title": "Short title for the result set",
  "intro": "One short sentence introducing the recommendations",
  "stay_recommendations": [
    {
      "area": "Neighborhood name",
      "why_it_fits": "Why it fits this group",
      "vibe": "2-4 word vibe description",
      "good_for": "What it is good for",
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
      "this_becomes": "The story or memory this could become"
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
      "this_becomes": "The kind of story or memory this could become"
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


def render_stay_recommendations(stay_recommendations: list[dict]) -> None:
    if not stay_recommendations:
        return

    st.markdown("## 🏡 Where to Stay")

    for area in stay_recommendations:
        st.markdown(f"### {area.get('area', 'Area')}")
        st.write(f"**Why it fits:** {area.get('why_it_fits', '')}")
        st.write(f"**Vibe:** {area.get('vibe', '')}")
        st.write(f"**Good for:** {area.get('good_for', '')}")

        price = area.get("price_range", {})
        if price:
            st.write("**Price range (per night)**")
            st.write(f"- Budget: {price.get('budget', '')}")
            st.write(f"- Mid-range: {price.get('mid_range', '')}")
            st.write(f"- Luxury: {price.get('luxury', '')}")

        st.divider()


def render_experience_cards(experiences: list[dict]) -> None:
    for exp in experiences:
        name = exp.get("name", "Experience")
        why_it_fits = exp.get("why_it_fits", "")
        your_twist = exp.get("your_twist", "")
        this_becomes = exp.get("this_becomes", "")

        with st.expander(name, expanded=True):
            st.markdown("**Why it fits**")
            st.write(why_it_fits)

            st.markdown("**Your twist**")
            st.write(your_twist)

            st.markdown("**This becomes**")
            st.write(this_becomes)


def render_multi_stop_day_plans(stops: list[dict]) -> None:
    for stop in stops:
        stop_name = stop.get("stop_name", "Stop")
        why_this_stop_matters = stop.get("why_this_stop_matters", "")
        best_day_shape = stop.get("best_day_shape", "")
        main_anchor = stop.get("main_anchor", "")
        optional_add_on = stop.get("optional_add_on", "")
        your_twist = stop.get("your_twist", "")
        keep_it_easy = stop.get("keep_it_easy", "")
        this_becomes = stop.get("this_becomes", "")

        st.markdown(f"## {stop_name}")

        if why_this_stop_matters:
            st.markdown("**Why this stop matters**")
            st.write(why_this_stop_matters)

        if best_day_shape:
            st.markdown("**Best day shape**")
            st.write(best_day_shape)

        if main_anchor:
            st.markdown("**Main anchor**")
            st.write(main_anchor)

        if optional_add_on:
            st.markdown("**Optional add-on**")
            st.write(optional_add_on)

        if your_twist:
            st.markdown("**Your twist**")
            st.write(your_twist)

        if keep_it_easy:
            st.markdown("**Keep it easy**")
            st.write(keep_it_easy)

        if this_becomes:
            st.markdown("**This becomes**")
            st.write(this_becomes)

        st.divider()


# -----------------------------
# UI
# -----------------------------
st.title("✨ Extraordinary Moment Finder")
st.caption("Find experiences you'll actually remember — based on who you are, not just where you're going.")

st.write(
    "Tell me a little about your trip and your people, and I’ll suggest experiences that feel like **you**."
)

with st.form("moment_finder_form"):
    trip_mode = st.radio(
        "Trip type",
        ["Single destination", "Cruise / Multi-stop trip"],
        horizontal=True,
    )

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

    curiosity = st.text_area(
        "Anything you're curious about? (optional)",
        placeholder="Red light district, desserts, hidden gems, something different...",
        height=100,
    )

    inspiration_input = st.text_input(
        "Did you see something you liked? (TikTok, IG, Google, blog, anywhere)",
        placeholder="Dessert crawl, canal cruise, speakeasy, rooftop bar, cool market...",
    )

    existing_plans = st.text_area(
        "What do you already have booked or definitely want to do? (include day/time if you know it)",
        placeholder="""Anne Frank House - April 2 at 10am
Canal cruise - April 3 in the evening
Dinner reservation - April 4 at 7pm
Red Light District - one night""",
        height=140,
    )

    keep_in_mind = st.text_area(
        "Anything to keep in mind? (optional)",
        placeholder="Doesn't like rushing, mobility concerns, prefers scenic not strenuous, loves food, wants easy walking...",
        height=100,
    )

    need_stay = st.checkbox("Help me figure out where to stay")

    if need_stay:
        stay_preferences = st.text_area(
            "What kind of stay are you looking for?",
            placeholder="Walkable, nightlife, quiet, central, near water, luxury, budget-friendly, family-friendly...",
            height=100,
        )
    else:
        stay_preferences = ""

    submitted = st.form_submit_button("Create My Experiences")

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
                st.subheader(title)

                if intro:
                    st.write(intro)

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