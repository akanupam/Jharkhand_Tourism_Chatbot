import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from pathlib import Path

class TripPlanner:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.load_places_data()
        
    def load_places_data(self):
        """Load places data with error handling"""
        try:
            # Handle different possible paths
            data_path = Path(__file__).parent.parent / 'data' / 'places.json'
            if not data_path.exists():
                # Try alternative path
                data_path = Path('data/places.json')
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.places_data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: places.json not found. Using default data.")
            self.places_data = self._get_default_places_data()
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in places.json. Using default data.")
            self.places_data = self._get_default_places_data()
    
    def _get_default_places_data(self):
        """Fallback data if JSON file is not available"""
        return {
            "jharkhand_destinations": {
                "nature_wildlife": [
                    {
                        "name": "Betla National Park",
                        "location": "Latehar District",
                        "best_time": "October to March",
                        "duration": "1-2 days",
                        "highlights": ["Tigers", "Elephants", "Waterfalls", "Fort ruins"],
                        "activities": ["Wildlife safari", "Nature walks", "Bird watching"],
                        "nearby_attractions": ["Netarhat", "Lodh Falls"]
                    }
                ],
                "waterfalls": [
                    {
                        "name": "Hundru Falls",
                        "location": "Ranchi",
                        "best_time": "September to February",
                        "duration": "Half day",
                        "height": "98 meters",
                        "highlights": ["Scenic beauty", "Picnic spot"],
                        "distance_from_ranchi": "45 km"
                    }
                ],
                "religious_sites": [
                    {
                        "name": "Baidyanath Dham",
                        "location": "Deoghar",
                        "significance": "One of 12 Jyotirlingas",
                        "best_time": "Year-round, avoid Shravan month crowds",
                        "duration": "1 day",
                        "nearby": ["Naulakha Temple", "Basukinath Temple"]
                    }
                ]
            }
        }
    
    def extract_trip_parameters(self, user_query: str) -> Dict:
        """Extract trip parameters with better error handling"""
        try:
            prompt = f"""
            Analyze this Jharkhand tourism query and extract trip planning parameters.
            Query: "{user_query}"
            
            Return a JSON-formatted response with these fields:
            {{
                "duration_days": <number or null>,
                "interests": [<list of: nature, wildlife, religious, adventure, waterfalls, culture>],
                "start_location": "<city name or null>",
                "budget_level": "<budget/moderate/luxury or null>",
                "travel_month": "<month name or null>",
                "group_type": "<solo/family/friends/couple or null>"
            }}
            
            Example response:
            {{
                "duration_days": 3,
                "interests": ["nature", "wildlife"],
                "start_location": "Ranchi",
                "budget_level": "moderate",
                "travel_month": null,
                "group_type": "family"
            }}
            """
            
            response = self.model.generate_content(prompt)
            return self._parse_parameters(response.text)
            
        except Exception as e:
            print(f"Error extracting parameters: {e}")
            # Return default parameters
            return {
                "duration_days": 3,
                "interests": ["nature", "culture"],
                "start_location": "Ranchi",
                "budget_level": "moderate",
                "travel_month": None,
                "group_type": "family"
            }
    
    def _parse_parameters(self, gemini_response: str) -> Dict:
        """Parse Gemini response with better error handling"""
        import re
        
        # Default parameters
        params = {
            "duration_days": 3,
            "interests": ["nature", "culture"],
            "start_location": "Ranchi",
            "budget_level": "moderate",
            "travel_month": None,
            "group_type": "family"
        }
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', gemini_response, re.DOTALL)
            if json_match:
                extracted_params = json.loads(json_match.group())
                # Update params with extracted values
                for key, value in extracted_params.items():
                    if value is not None and value != "null":
                        params[key] = value
        except:
            # Fallback to simple parsing
            text_lower = gemini_response.lower()
            
            # Extract duration
            duration_match = re.search(r'(\d+)\s*day', text_lower)
            if duration_match:
                params["duration_days"] = int(duration_match.group(1))
            
            # Extract interests
            interest_keywords = {
                'nature': ['nature', 'natural', 'scenic'],
                'wildlife': ['wildlife', 'animal', 'safari', 'tiger'],
                'religious': ['religious', 'temple', 'spiritual'],
                'adventure': ['adventure', 'trek', 'hiking'],
                'waterfalls': ['waterfall', 'falls'],
                'culture': ['culture', 'cultural', 'tribal']
            }
            
            found_interests = []
            for interest, keywords in interest_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    found_interests.append(interest)
            
            if found_interests:
                params["interests"] = found_interests
        
        return params
    
    def create_itinerary(self, parameters: Dict) -> str:
        """Create itinerary with better formatting and error handling"""
        duration = parameters.get('duration_days')
        interests = parameters.get('interests', ['nature', 'culture'])
        start_location = parameters.get('start_location', 'Ranchi')
        budget_level = parameters.get('budget_level', 'moderate')
        group_type = parameters.get('group_type', 'family')
        
        # Select places based on interests and duration
        selected_places = self._select_places(interests, duration)
        
        if not selected_places:
            selected_places = self._get_must_visit_places(duration)
        
        # Create place descriptions for the prompt
        place_details = []
        for place in selected_places:
            detail = f"{place['name']} ({place.get('location', 'Jharkhand')})"
            if 'highlights' in place:
                detail += f" - Known for: {', '.join(place['highlights'][:2])}"
            place_details.append(detail)
        
        # Generate itinerary using Gemini
        itinerary_prompt = f"""
You are a warm, friendly Jharkhand tour guide. 
The user wants a detailed travel plan.

Trip Profile:
- Duration: {duration} days
- Interests: {', '.join(interests)}
- Starting from: {start_location}
- Group type: {group_type}
- Budget level: {budget_level}

🎯 Instructions:
Always provide a structured **Day-wise Itinerary**. 
For each day, format like this:

Day <number>:
🌅 Morning: <Activity + local breakfast suggestion>
🌞 Afternoon: <Main site + lunch suggestion>
🌆 Evening: <Site / activity + dinner suggestion>
💡 Travel Tip: <1 practical insider tip for the day>
💰 Approx Budget: ₹<estimate>

At the end, add:
- 📞 Emergency helplines (Police, Ambulance, Tourism)
- 🌤️ Weather/season tips
- 🍲 Must-try local food list
- 🎁 Suggested souvenirs

⚠️ Notes:
- Must **always** include "Day 1", "Day 2" etc. with emojis.
- Mention at least 1 **local dish** per day.
- Use a **guide-like, conversational tone**: ("You'll love...", "Don’t miss...")
- Keep it under ~150 words so it’s crisp but rich.
"""
        try:
            response = self.model.generate_content(itinerary_prompt)
            return self._format_final_itinerary(response.text, parameters)
        except Exception as e:
            return self._create_fallback_itinerary(duration, selected_places)
    
    def _select_places(self, interests: List[str], duration: int) -> List[Dict]:
        """Improved place selection logic"""
        selected = []
        places_per_day = 2
        max_places = min(duration * places_per_day, 10)  # Cap at 10 places
        
        # Priority mapping for interests
        interest_mapping = {
            'nature': ['nature_wildlife', 'hill_stations', 'waterfalls'],
            'wildlife': ['nature_wildlife'],
            'religious': ['religious_sites'],
            'adventure': ['waterfalls', 'hill_stations', 'nature_wildlife'],
            'waterfalls': ['waterfalls'],
            'culture': ['religious_sites', 'hill_stations']
        }
        
        # Track selected place names to avoid duplicates
        selected_names = set()
        
        # First pass: Add places matching primary interests
        for interest in interests:
            if interest in interest_mapping:
                for category in interest_mapping[interest]:
                    if category in self.places_data.get('jharkhand_destinations', {}):
                        places = self.places_data['jharkhand_destinations'][category]
                        for place in places:
                            if place['name'] not in selected_names and len(selected) < max_places:
                                selected.append(place)
                                selected_names.add(place['name'])
        
        # Second pass: Fill remaining slots with must-visit places
        if len(selected) < max_places:
            for category in self.places_data.get('jharkhand_destinations', {}).values():
                for place in category:
                    if place['name'] not in selected_names and len(selected) < max_places:
                        # Check if place duration fits
                        place_duration = place.get('duration', '1 day')
                        if 'half day' in place_duration.lower() or duration >= 2:
                            selected.append(place)
                            selected_names.add(place['name'])
        
        return selected
    
    def _get_must_visit_places(self, duration: int) -> List[Dict]:
        """Get default must-visit places if no specific interests match"""
        must_visit = []
        all_places = []
        
        # Flatten all places
        for category in self.places_data.get('jharkhand_destinations', {}).values():
            all_places.extend(category)
        
        # Sort by popularity (you can add a popularity field in JSON)
        # For now, just take first few places
        return all_places[:min(duration * 2, len(all_places))]
    
    def _format_final_itinerary(self, gemini_response: str, parameters: Dict) -> str:
        """Format the final itinerary with additional information"""
        formatted = "🌟 **Your Personalized Jharkhand Adventure Awaits!** 🌟\n\n"
        formatted += gemini_response
        
        # Add practical information section
        formatted += "\n\n" + "="*50 + "\n"
        formatted += "📋 **ESSENTIAL INFORMATION**\n"
        formatted += "="*50 + "\n\n"
        
        # Helpline numbers
        formatted += "📞 **Emergency Contacts:**\n"
        formatted += "• Tourist Helpline: 1800-123-4567\n"
        formatted += "• Police: 100 | Ambulance: 108\n"
        formatted += "• Forest Department: 1800-123-5555\n"
        formatted += "• Women Helpline: 1091\n\n"
        
        # Weather tips based on travel month
        formatted += "🌤️ **Weather & Packing Tips:**\n"
        travel_month = parameters.get('travel_month')
        if travel_month:
            formatted += f"• For {travel_month}: "
            # Add month-specific tips
        else:
            formatted += "• Oct-Mar: Pleasant weather (10-25°C), carry light woolens\n"
            formatted += "• Apr-Jun: Hot (25-40°C), carry sunscreen and hats\n"
            formatted += "• Jul-Sep: Monsoon, carry raincoats and umbrellas\n\n"
        
        # General tips
        formatted += "💡 **Pro Tips from Locals:**\n"
        formatted += "• Book accommodations in advance during peak season\n"
        formatted += "• Try local delicacies: Dhuska, Rugra, Handia\n"
        formatted += "• Respect tribal customs and seek permission for photography\n"
        formatted += "• Keep some cash handy as ATMs may be scarce in remote areas\n"
        formatted += "• Best time for wildlife sighting: Early morning (6-8 AM)\n\n"
        
        formatted += "Have a wonderful journey exploring the treasures of Jharkhand! 🎒✨"
        
        return formatted
    
    def _create_fallback_itinerary(self, duration: int, places: List[Dict]) -> str:
        """Create a basic itinerary if Gemini fails"""
        itinerary = f"🌟 **Your {duration}-Day Jharkhand Adventure** 🌟\n\n"
        
        day = 1
        for i, place in enumerate(places):
            if i > 0 and i % 2 == 0:
                day += 1
            if day > duration:
                break
                
            itinerary += f"**Day {day}:**\n"
            itinerary += f"📍 Visit {place['name']} ({place.get('location', 'Jharkhand')})\n"
            if 'highlights' in place:
                itinerary += f"   Highlights: {', '.join(place['highlights'][:3])}\n"
            if 'best_time' in place:
                itinerary += f"   Best time: {place['best_time']}\n"
            itinerary += "\n"
        
        itinerary += "\n📞 Tourist Helpline: 1800-123-4567\n"
        itinerary += "Have a great trip! 🎒"
        
        return itinerary


def plan_trip(user_query: str, gemini_api_key: str) -> str:
    """Main function to plan a trip - with better error handling"""
    if not gemini_api_key:
        return ("I'd love to help you plan your Jharkhand trip! However, I need the API key to be configured. "
                "Please contact the administrator to set this up.")
    
    try:
        planner = TripPlanner(gemini_api_key)
        
        # Extract parameters from query
        parameters = planner.extract_trip_parameters(user_query)
        
        # Create itinerary
        itinerary = planner.create_itinerary(parameters)
        
        return itinerary
        
    except Exception as e:
        # error_message = (
        #     "I'd love to help you plan your Jharkhand adventure! 
        return f"I'd love to help you plan your Jharkhand trip! However, I encountered an issue: {str(e)}. Could you please rephrase your request? For example: 'Plan a 3-day trip to Jharkhand for nature lovers' or 'Create a weekend itinerary for religious sites in Jharkhand'."
    
  