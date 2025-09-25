import json
import os
from typing import Dict, Optional
from pathlib import Path
import google.generativeai as genai

class AreaSuggestions:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.load_location_data()        
 
    def load_location_data(self):
        """Load location data as context for LLM"""
        try:
            data_path = Path(__file__).parent.parent / 'data' / 'locations.json'
            if not data_path.exists():
                data_path = Path('data/locations.json')
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.location_data = json.load(f)
        except:
            self.location_data = self._get_default_location_data()
    
    def _get_default_location_data(self):
        """Fallback data if JSON not available"""
        return {
            "ranchi": {
                "attractions": [
                    "Hundru Falls (45 km) - 98m high waterfall",
                    "Jonha Falls (40 km) - Buddhist monastery nearby",
                    "Rock Garden (4 km) - Sculptures and evening walks",
                    "Tagore Hill (3 km) - Panoramic city views",
                    "Pahari Mandir (2 km) - Hilltop Shiva temple"
                ]
            },
            "jamshedpur": {
                "attractions": [
                    "Dalma Wildlife Sanctuary (30 km) - Elephant habitat",
                    "Dimna Lake (13 km) - Boating and water sports",
                    "Jubilee Park (in city) - Rose garden and zoo"
                ]
            },
            "deoghar": {
                "attractions": [
                    "Baidyanath Temple (in city) - One of 12 Jyotirlingas",
                    "Naulakha Temple (1.5 km) - 146 feet high",
                    "Trikuta Parvata (16 km) - Ropeway and scenic views"
                ]
            }
        }
    
    def extract_context(self, user_query: str) -> Dict:
        """Use LLM to understand user's request"""
        prompt = f"""
        Analyze this query about nearby places in Jharkhand:
        Query: "{user_query}"
        
        Extract and return in JSON format:
        {{
            "location": "<city name or null>",
            "attraction_type": "<waterfall/temple/park/wildlife/any or null>",
            "distance_preference": "<walking/short drive/day trip/any or null>",
            "group_context": "<family/couple/solo/friends or null>",
            "time_available": "<few hours/half day/full day or null>"
        }}
        
        Common Jharkhand cities: Ranchi, Jamshedpur, Deoghar, Dhanbad, Bokaro
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Parse response - implement proper JSON extraction
            return self._parse_llm_response(response.text)
        except:
            return {"location": None, "attraction_type": "any"}
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse LLM response to extract parameters"""
        import re
        
        # Default context
        context = {
            "location": None,
            "attraction_type": "any",
            "distance_preference": "any",
            "group_context": None,
            "time_available": None
        }
        
        try:
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
                for key, value in extracted.items():
                    if value and value != "null":
                        context[key] = value
        except:
            # Fallback to simple extraction
            text_lower = response_text.lower()
            
            # Extract location
            for city in ["ranchi", "jamshedpur", "deoghar", "dhanbad", "bokaro"]:
                if city in text_lower:
                    context["location"] = city
                    break
        
        return context
    
    def generate_suggestions(self, context: Dict) -> str:
        """Use LLM to generate contextual suggestions"""
        location = context.get("location")
        
        # Build location data string
        if location and location.lower() in self.location_data:
            location_info = f"Available attractions near {location}:\n"
            attractions = self.location_data[location.lower()].get("attractions", [])
            location_info += "\n".join(f"- {attr}" for attr in attractions)
        else:
            # Provide general Jharkhand attractions
            location_info = """Popular attractions in Jharkhand:
            Ranchi: Hundru Falls, Jonha Falls, Rock Garden, Tagore Hill
            Jamshedpur: Dalma Wildlife Sanctuary, Dimna Lake, Jubilee Park
            Deoghar: Baidyanath Temple, Naulakha Temple, Trikuta Parvata
            Netarhat: Hill station, sunset points
            Betla National Park: Wildlife and nature"""
        
        # Create prompt for suggestions
        suggestion_prompt = f"""
        You are a friendly Jharkhand tourism guide. Based on this context, suggest nearby places:
        
        User Context:
        - Location: {context.get('location', 'not specified')}
        - Interest type: {context.get('attraction_type', 'any')}
        - Distance preference: {context.get('distance_preference', 'any')}
        - Group: {context.get('group_context', 'general visitors')}
        - Time available: {context.get('time_available', 'flexible')}
        
        {location_info}
        
        Provide suggestions in this format:
        1. Start with a warm greeting
        2. List 3-5 relevant places with:
           - Name and distance
           - What makes it special
           - Best time to visit
           - Quick tip
        3. Group by distance if applicable (Walking distance, Short drive, Day trip)
        4. Add practical tips at the end
        5. Use emojis for visual appeal
        
        Keep the tone conversational and helpful, like a local friend giving advice.
        Mention specific local food or experiences where relevant.
        Make the response ~100 words max crisp and rich
        """
        
        try:
            response = self.model.generate_content(suggestion_prompt)
            return self._format_final_suggestions(response.text, context)
        except Exception as e:
            return self._create_fallback_suggestions(context)
    
    def _format_final_suggestions(self, llm_response: str, context: Dict) -> str:
        """Add consistent formatting and additional info"""
        formatted = llm_response
        
        # Add footer with practical info
        formatted += "\n\n" + "="*40 + "\n"
        formatted += "📱 **Quick Info:**\n"
        formatted += "• Tourism Helpline: 1800-123-4567\n"
        formatted += "• Best season: October to March\n"
        formatted += "• Local transport: Auto, taxi, buses available\n"
        
        if context.get("location"):
            formatted += f"• Weather in {context['location'].title()}: Check current conditions\n"
        
        return formatted
    
    def _create_fallback_suggestions(self, context: Dict) -> str:
        """Fallback if LLM fails"""
        location = context.get("location", "Jharkhand")
        
        return f"""🗺️ **Exploring {location.title()}!**

I'd love to help you discover nearby attractions! Here are some popular spots:

**🏞️ Nature & Waterfalls:**
• Hundru Falls - Spectacular 98m waterfall
• Jonha Falls - Sacred Buddhist site
• Dassam Falls - Perfect for picnics

**🛕 Spiritual Sites:**
• Baidyanath Temple (Deoghar) - Ancient Jyotirlinga
• Jagannath Temple (Ranchi) - Beautiful architecture

**🌳 Parks & Wildlife:**
• Betla National Park - Tigers and elephants
• Dalma Wildlife Sanctuary - Elephant habitat

💡 **Tips:** Start early, carry water, and don't miss trying local dhuska!

Need specific directions or timings? Just ask!
"""

def nearby_suggestions(user_query: str, gemini_api_key: str) -> str:
    """Main function for area suggestions"""
    if not gemini_api_key:
        return "I'd love to suggest nearby places! However, I need the API key configured. Please contact the administrator."
    
    try:
        area_guide = AreaSuggestions(gemini_api_key)
        
        # Extract context using LLM
        context = area_guide.extract_context(user_query)
        
        # Generate suggestions
        suggestions = area_guide.generate_suggestions(context)
        
        return suggestions
        
    except Exception as e:
        return (
            "🗺️ I'd be happy to suggest nearby places in Jharkhand! "
            "Try asking:\n"
            "• 'What places are near Ranchi?'\n"
            "• 'Waterfalls around Jamshedpur'\n"
            "• 'Temple visits near Deoghar'\n"
            "• 'Weekend spots for families near Ranchi'\n\n"
            "I'll provide personalized suggestions based on your preferences!"
        )
    
# from dotenv import load_dotenv
# load_dotenv()
# print(nearby_suggestions("I'm in Ranchi, what can I see nearby?", os.getenv("GOOGLE_API_KEY")))