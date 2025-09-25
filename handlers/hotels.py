import json
import os
from pathlib import Path
import google.generativeai as genai

class HotelSuggestions:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.load_hotel_data()
        
    def load_hotel_data(self):
        """Load hotel data for context"""
        try:
            data_path = Path(__file__).parent.parent / 'data' / 'hotels.json'
            if not data_path.exists():
                data_path = Path('data/hotels.json')
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.hotel_data = json.load(f)
        except:
            self.hotel_data = self._get_default_hotel_data()
    
    def _get_default_hotel_data(self):
        """Fallback hotel data"""
        return {
            "ranchi": {
                "luxury": ["Radisson Blu", "The Capitol Hill"],
                "mid_range": ["Hotel Arya", "Hotel Yuvraj Palace"],
                "budget": ["Hotel Akash", "OYO rooms"]
            },
            "jamshedpur": {
                "luxury": ["The Sonnet", "Ramada"],
                "mid_range": ["Ginger Hotel", "Hotel Dayal"],
                "budget": ["Hotel Jiva", "Various OYOs"]
            },
            "deoghar": {
                "luxury": ["Hotel Mahadev Palace"],
                "mid_range": ["Hotel Rajkamal", "Hotel Ashoka"],
                "budget": ["Dharamshala options", "Guest houses"]
            }
        }
    
    def generate_suggestions(self, query: str) -> str:
        """Generate concise hotel suggestions"""
        # Convert hotel data to string for context
        hotel_context = json.dumps(self.hotel_data, indent=2)
        
        prompt = f"""
        You are a Jharkhand hotel booking assistant. 
        User query: "{query}"
        
        Available hotels data:
        {hotel_context}
        
        Provide hotel suggestions in EXACTLY this format (MAX 100 words total):
        
        🏨 [Location] Hotels:
        
        💎 Luxury: [1-2 options with price range]
        🏢 Mid-range: [1-2 options with price range]
        💰 Budget: [1-2 options with price range]
        
        📍 Booking: MakeMyTrip, Booking.com, or call directly
        💡 Tip: [One short tip]
        
        Be specific with hotel names and approximate prices (₹).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._ensure_concise(response.text)
        except:
            return self._create_fallback_response(query)
    
    def _ensure_concise(self, response: str) -> str:
        """Ensure response is under 100 words"""
        words = response.split()
        if len(words) > 100:
            # Truncate and add ellipsis
            truncated = ' '.join(words[:95]) + "... Book via MakeMyTrip/Booking.com"
            return truncated
        return response
    
    def _create_fallback_response(self, query: str) -> str:
        """Fallback if LLM fails"""
        return (
            "🏨 Jharkhand Hotels:\n\n"
            "💎 Luxury: Radisson Blu Ranchi (₹5000+)\n"
            "🏢 Mid: Ginger Hotels (₹2000-3000)\n"
            "💰 Budget: OYO/Guest houses (₹800-1500)\n\n"
            "📍 Book: MakeMyTrip, Booking.com\n"
            "💡 Tip: Book early during festivals!"
        )

def hotel_recommendations(user_query: str, gemini_api_key: str) -> str:
    """Main function for hotel suggestions"""
    if not gemini_api_key:
        return "Hotel search needs API configuration. Please contact support."
    
    try:
        hotel_guide = HotelSuggestions(gemini_api_key)
        return hotel_guide.generate_suggestions(user_query)
    except Exception as e:
        return (
            "🏨 Popular Jharkhand stays:\n"
            "Ranchi: Radisson Blu, Capitol Hill\n"
            "Jamshedpur: The Sonnet, Ramada\n"
            "Netarhat: Forest Rest House\n"
            "Book via MakeMyTrip or call hotels directly!"
        )
    

# from dotenv import load_dotenv
# load_dotenv()
# print(hotel_recommendations("Family hotels near Betla National Park", os.getenv("GOOGLE_API_KEY")))