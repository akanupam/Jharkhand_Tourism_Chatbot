import os
import re
import json
import google.generativeai as genai
from typing import Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-pro')

def classify_intent(text: str) -> str:
    """
    LLM-based intent classification with domain validation
    Returns intent or 'OUT_OF_DOMAIN' if not Jharkhand-related
    """
    
    prompt = f"""
    You are an intent classifier for a Jharkhand tourism chatbot.
    
    CRITICAL RULES:
    1. This chatbot ONLY handles queries about Jharkhand state, India
    2. If the query is about any location OUTSIDE Jharkhand, return "OUT_OF_DOMAIN"
    3. If the query mentions non-Jharkhand places (like Paris, Mumbai, Delhi, Goa, etc.), return "OUT_OF_DOMAIN"
    
    For VALID Jharkhand queries, classify into one of these intents:
    - TRIP_PLANNER: Planning trips, itineraries, tour suggestions within Jharkhand
    - AREA_SUGGEST: Nearby places, attractions around a location in Jharkhand
    - ROUTE_HELPER: Directions, how to reach, transportation within/to Jharkhand
    - HOTEL_SUGGEST: Accommodation, hotels, stays in Jharkhand
    - HELPLINE: Emergency numbers, helplines for Jharkhand tourism
    - FESTIVALS: Events, festivals, cultural programs in Jharkhand
    - RAG_FAQ: General questions about Jharkhand tourism
    
    Query: "{text}"
    
    Analyze carefully:
    1. Does this query relate to Jharkhand? (cities like Ranchi, Jamshedpur, Deoghar, places like Betla, Netarhat, etc.)
    2. If location is not mentioned, could it be asking about Jharkhand tourism?
    3. If it mentions any non-Jharkhand location explicitly, it's OUT_OF_DOMAIN
    
    Return ONLY the intent label, nothing else.
    Examples:
    - "Plan a trip to Paris" → OUT_OF_DOMAIN
    - "Plan a trip to Ranchi" → TRIP_PLANNER
    - "Hotels in Mumbai" → OUT_OF_DOMAIN
    - "Hotels in Jamshedpur" → HOTEL_SUGGEST
    - "Weekend trip" → TRIP_PLANNER (assumes Jharkhand context)
    """
    
    try:
        response = model.generate_content(prompt)
        intent = response.text.strip().upper()
        
        # Validate the response
        valid_intents = [
            "TRIP_PLANNER", "AREA_SUGGEST", "ROUTE_HELPER", 
            "HOTEL_SUGGEST", "HELPLINE", "FESTIVALS", 
            "RAG_FAQ", "OUT_OF_DOMAIN"
        ]
        
        if intent in valid_intents:
            return intent
        else:
            # Fallback to keyword-based classification
            return _fallback_classification(text)
            
    except Exception as e:
        print(f"LLM classification failed: {e}")
        # Fallback to keyword-based classification
        return _fallback_classification(text)

def _fallback_classification(text: str) -> str:
    """
    Fallback keyword-based classification if LLM fails
    """
    t = text.lower()
    
    # Check for obvious non-Jharkhand locations
    non_jharkhand = [
        "paris", "london", "new york", "mumbai", "delhi", 
        "bangalore", "chennai", "goa", "kerala", "kashmir"
    ]
    if any(place in t for place in non_jharkhand):
        return "OUT_OF_DOMAIN"
    
    # Check for Jharkhand locations
    jharkhand_places = [
        "ranchi", "jamshedpur", "deoghar", "dhanbad", "bokaro",
        "netarhat", "betla", "hundru", "jonha", "jharkhand"
    ]
    has_jharkhand = any(place in t for place in jharkhand_places)
    
    # Intent patterns
    if any(k in t for k in ["plan", "itinerary", "trip", "tour", "days"]):
        return "TRIP_PLANNER" if has_jharkhand or not any(place in t for place in non_jharkhand) else "OUT_OF_DOMAIN"
    
    if any(k in t for k in ["near", "nearby", "around", "close"]):
        return "AREA_SUGGEST" if has_jharkhand else "OUT_OF_DOMAIN"
    
    if any(k in t for k in ["reach", "route", "distance", "how to get"]):
        return "ROUTE_HELPER" if has_jharkhand else "OUT_OF_DOMAIN"
    
    if any(k in t for k in ["hotel", "stay", "accommodation"]):
        return "HOTEL_SUGGEST" if has_jharkhand else "OUT_OF_DOMAIN"
    
    if any(k in t for k in ["helpline", "emergency", "contact"]):
        return "HELPLINE"
    
    if any(k in t for k in ["festival", "event", "mela"]):
        return "FESTIVALS" if has_jharkhand else "OUT_OF_DOMAIN"
    
    # Default: if no specific location mentioned, assume Jharkhand context
    if not any(place in t for place in non_jharkhand):
        return "RAG_FAQ"
    
    return "OUT_OF_DOMAIN"

def get_out_of_domain_response(query: str) -> str:
    """
    Generate helpful response for out-of-domain queries
    """
    prompt = f"""
    The user asked about something outside Jharkhand: "{query}"
    
    Generate a polite, helpful response that:
    1. Acknowledges their query
    2. Explains you only handle Jharkhand tourism
    3. Suggests similar things they can explore in Jharkhand
    
    Keep it friendly and under 100 words.
    
    Example: If they ask about "beaches in Goa", you might suggest "waterfalls in Jharkhand"
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        # Fallback response
        return (
            "I specialize in Jharkhand tourism and can only help with destinations within Jharkhand. "
            "However, Jharkhand has amazing attractions like Hundru Falls, Betla National Park, "
            "and the spiritual city of Deoghar. Would you like to explore these instead?"
        )

