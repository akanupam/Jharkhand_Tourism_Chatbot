import json
import os
from typing import Dict, Optional, List
from pathlib import Path
import google.generativeai as genai

class RouteHelper:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.load_route_data()
        
    def load_route_data(self):
        """Load transportation and route data"""
        try:
            data_path = Path(__file__).parent.parent / 'data' / 'routes.json'
            if not data_path.exists():
                data_path = Path('data/routes.json')
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.route_data = json.load(f)
        except:
            self.route_data = self._get_default_route_data()
    
    def _get_default_route_data(self):
        """Default route information for major Jharkhand routes"""
        return {
            "major_routes": {
                "ranchi_to_jamshedpur": {
                    "distance": "130 km",
                    "duration": "3-4 hours",
                    "via": "NH-33",
                    "modes": ["bus", "taxi", "train"],
                    "landmarks": ["Bundu", "Tamar", "Chandil"]
                },
                "ranchi_to_deoghar": {
                    "distance": "250 km",
                    "duration": "6-7 hours",
                    "via": "NH-33 and NH-114A",
                    "modes": ["bus", "taxi", "train"],
                    "landmarks": ["Hazaribagh", "Giridih"]
                },
                "ranchi_to_netarhat": {
                    "distance": "150 km",
                    "duration": "4-5 hours",
                    "via": "Ranchi-Lohardaga-Netarhat Road",
                    "modes": ["taxi", "bus"],
                    "landmarks": ["Lohardaga", "Ghaghra Falls"]
                }
            },
            "transport_info": {
                "bus": {
                    "operators": ["Jharkhand State Road Transport", "Private operators"],
                    "frequency": "Regular services from major bus stands",
                    "booking": "Counter booking or online via RedBus"
                },
                "train": {
                    "major_stations": ["Ranchi Junction", "Tatanagar Junction", "Deoghar Junction"],
                    "booking": "IRCTC website or railway counters"
                },
                "taxi": {
                    "options": ["Ola", "Uber", "Local taxi unions"],
                    "approx_rate": "₹12-15 per km for AC cab"
                },
                "auto": {
                    "availability": "Within city limits",
                    "rate": "₹10-15 per km (negotiate before ride)"
                }
            },
            "important_terminals": {
                "ranchi": ["Birsa Munda Bus Terminal", "Ranchi Railway Station", "Birsa Munda Airport"],
                "jamshedpur": ["Mango Bus Stand", "Tatanagar Railway Station"],
                "deoghar": ["Deoghar Bus Stand", "Deoghar Railway Station"]
            }
        }
    
    def extract_route_context(self, user_query: str) -> Dict:
        """Use LLM to understand route request"""
        prompt = f"""
        Analyze this transportation/route query for Jharkhand:
        Query: "{user_query}"
        
        Extract and return in JSON format:
        {{
            "origin": "<starting city/location>",
            "destination": "<ending city/location>",
            "mode_preference": "<bus/train/taxi/any>",
            "time_preference": "<morning/afternoon/evening/night/any>",
            "budget_concern": "<yes/no>",
            "group_size": "<solo/couple/family/group>",
            "special_needs": "<elderly/children/disabled/none>"
        }}
        
        Common Jharkhand locations: Ranchi, Jamshedpur, Deoghar, Dhanbad, Bokaro, Netarhat, 
        Betla National Park, Hundru Falls, Parasnath, Hazaribagh
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_route_context(response.text)
        except:
            return {
                "origin": None,
                "destination": None,
                "mode_preference": "any"
            }
    
    def _parse_route_context(self, response_text: str) -> Dict:
        """Parse LLM response for route context"""
        import re
        
        context = {
            "origin": None,
            "destination": None,
            "mode_preference": "any",
            "time_preference": "any",
            "budget_concern": "no",
            "group_size": "solo",
            "special_needs": "none"
        }
        
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                extracted = json.loads(json_match.group())
                for key, value in extracted.items():
                    if value and value not in ["null", "none", ""]:
                        context[key] = value.lower()
        except:
            # Simple fallback parsing
            text_lower = response_text.lower()
            locations = ["ranchi", "jamshedpur", "deoghar", "dhanbad", "bokaro", 
                        "netarhat", "betla", "hundru", "parasnath", "hazaribagh"]
            
            found_locations = [loc for loc in locations if loc in text_lower]
            if len(found_locations) >= 2:
                context["origin"] = found_locations[0]
                context["destination"] = found_locations[1]
        
        return context
    
    def generate_route_guidance(self, context: Dict) -> str:
        """Generate comprehensive route guidance using LLM"""
        origin = context.get("origin", "your location")
        destination = context.get("destination", "your destination")
        
        # Get relevant route data
        route_key = f"{origin}_to_{destination}".replace(" ", "_").lower()
        specific_route = self.route_data.get("major_routes", {}).get(route_key, {})
        
        # Build context for LLM
        route_info = ""
        if specific_route:
            route_info = f"""
            Known route information:
            - Distance: {specific_route.get('distance', 'N/A')}
            - Duration: {specific_route.get('duration', 'N/A')}
            - Via: {specific_route.get('via', 'N/A')}
            - Landmarks: {', '.join(specific_route.get('landmarks', []))}
            """
        
        transport_details = json.dumps(self.route_data.get("transport_info", {}), indent=2)
        
        # Create comprehensive prompt
        route_prompt = f"""
        You are a helpful Jharkhand travel guide providing route directions.
        
        User wants to travel:
        - From: {origin}
        - To: {destination}
        - Preferred mode: {context.get('mode_preference', 'any')}
        - Time preference: {context.get('time_preference', 'any')}
        - Budget conscious: {context.get('budget_concern', 'no')}
        - Group: {context.get('group_size', 'solo')}
        - Special needs: {context.get('special_needs', 'none')}
        
        {route_info}
        
        Available transport options in Jharkhand:
        {transport_details}
        
        Provide detailed route guidance including:
        1. 🗺️ Route Overview (distance, time, main highway/road)
        2. 🚌 Transportation Options:
           - For each mode (bus/train/taxi), provide:
             * Availability and frequency
             * Approximate cost
             * Where to board
             * Booking tips
        3. 🛤️ Step-by-step directions with landmarks
        4. ⏰ Best time to travel and journey tips
        5. 🍽️ Food/rest stops along the way
        6. ⚠️ Road conditions and safety tips
        7. 📱 Important contacts
        
        Use emojis, be friendly and practical. Include local insights.
        If the route is not common, suggest the best possible way.
        Format clearly with sections.
        Don't exceed over 100 words response unless asked and be under 200 words even if asked.
        """
        
        try:
            response = self.model.generate_content(route_prompt)
            return self._format_route_response(response.text, context)
        except Exception as e:
            return self._create_fallback_route(context)
    
    def _format_route_response(self, llm_response: str, context: Dict) -> str:
        """Add consistent formatting and emergency info"""
        formatted = llm_response
        
        # Add footer information
        formatted += "\n\n" + "="*50 + "\n"
        formatted += "📞 **Emergency Contacts:**\n"
        formatted += "• Highway Police: 1033\n"
        formatted += "• Ambulance: 108\n"
        formatted += "• Tourism Helpline: 1800-123-4567\n\n"
        
        formatted += "💡 **General Travel Tips:**\n"
        formatted += "• Keep some cash (ATMs may be scarce on highways)\n"
        formatted += "• Carry water and snacks\n"
        formatted += "• Share live location with family\n"
        formatted += "• Check vehicle/tickets before departure\n"
        
        return formatted
    
    def _create_fallback_route(self, context: Dict) -> str:
        """Fallback route guidance if LLM fails"""
        origin = context.get("origin", "your location").title()
        destination = context.get("destination", "your destination").title()
        
        return f"""🗺️ **Route Guidance: {origin} to {destination}**

**🚌 Transportation Options:**

**By Bus:**
• Check Jharkhand State Road Transport buses
• Private operators available at major bus stands
• Book online via RedBus or at counter
• Frequency: Usually every 1-2 hours

**By Train:**
• Check trains on IRCTC website
• Major stations: Ranchi, Tatanagar, Deoghar
• Book in advance for confirmed seats

**By Taxi/Cab:**
• Ola/Uber for city routes
• Local taxi unions for long distance
• Rate: ₹12-15 per km (negotiate beforehand)
• Shared taxis available on popular routes

**🛣️ General Route Tips:**
• NH-33 connects Ranchi-Jamshedpur
• NH-114A goes towards Deoghar
• Start early morning to avoid traffic
• Carry valid ID proofs

**⚠️ Important:**
• Road conditions vary, especially in monsoon
• Mobile network may be patchy in some areas
• Keep emergency numbers handy

📞 Highway Emergency: 1033
🚑 Ambulance: 108

"""

def route_directions(user_query: str, gemini_api_key: str) -> str:
    """Main function for route directions"""
    if not gemini_api_key:
        return "I'd love to help with directions! However, I need the API key configured. Please contact the administrator."
    
    try:
        route_helper = RouteHelper(gemini_api_key)
        
        # Extract route context
        context = route_helper.extract_route_context(user_query)
        
        # Validate if we have enough information
        if not context.get("destination"):
            return (
                "🗺️ **I'm here to help you navigate Jharkhand!**\n\n"
                "Please tell me:\n"
                "• Where you want to go (destination)\n"
                "• Where you're starting from (optional)\n"
                "• Your preferred transport mode (optional)\n\n"
                "**Example queries:**\n"
                "• 'How to reach Betla National Park from Ranchi?'\n"
                "• 'Best way to travel from Jamshedpur to Deoghar'\n"
                "• 'Bus routes to Netarhat from Ranchi'\n"
                "• 'Train options from Ranchi to Tatanagar'\n\n"
                "I'll provide detailed directions, transport options, and travel tips!"
            )
        
        # Generate route guidance
        route_guidance = route_helper.generate_route_guidance(context)
        
        return route_guidance
        
    except Exception as e:
        return (
            "🗺️ I'd be happy to help with directions! Please try asking:\n"
            "• 'How to reach Hundru Falls from Ranchi?'\n"
            "• 'Transportation from Jamshedpur to Deoghar'\n"
            "• 'Best route to Betla National Park'\n\n"
            "I'll provide transport options, timings, and travel tips!"
        )



# from dotenv import load_dotenv
# load_dotenv()
# print(route_directions("give me direction to reach hazaribagh from deoghar", os.getenv("GOOGLE_API_KEY")))