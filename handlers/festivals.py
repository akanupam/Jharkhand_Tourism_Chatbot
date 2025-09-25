import json
import os
from pathlib import Path
import google.generativeai as genai
from datetime import datetime

class FestivalGuide:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.load_festival_data()
        
    def load_festival_data(self):
        """Load festival information"""
        try:
            data_path = Path(__file__).parent.parent / 'data' / 'festivals.json'
            if not data_path.exists():
                data_path = Path('data/festivals.json')
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.festival_data = json.load(f)
        except:
            self.festival_data = self._get_default_festival_data()
    
    def _get_default_festival_data(self):
        """Default festival data"""
        return {
            "major_festivals": {
                "Sarhul": {
                    "time": "March-April",
                    "type": "Tribal Spring Festival",
                    "locations": ["Ranchi", "Khunti", "Gumla"],
                    "highlights": ["Sal tree worship", "Traditional dance", "Folk songs"]
                },
                "Karma": {
                    "time": "August-September", 
                    "type": "Harvest Festival",
                    "locations": ["Across Jharkhand"],
                    "highlights": ["Karma tree worship", "Night-long dancing"]
                },
                "Tusu": {
                    "time": "January (Makar Sankranti)",
                    "type": "Harvest Festival",
                    "locations": ["Jharkhand-Bengal border areas"],
                    "highlights": ["Folk songs", "Tusu idol immersion"]
                },
                "Chhath": {
                    "time": "October-November",
                    "type": "Sun worship",
                    "locations": ["All major cities"],
                    "highlights": ["River ghats", "Evening prayers"]
                }
            },
            "cultural_events": {
                "Jharkhand Tourism Festival": "November",
                "Netarhat Sunrise Festival": "Year-round",
                "Tribal Dance Festival": "December"
            }
        }
    
    def generate_festival_info(self, query: str) -> str:
        """Generate concise festival information"""
        current_month = datetime.now().strftime("%B")
        festival_context = json.dumps(self.festival_data, indent=2)
        
        prompt = f"""
        You are a Jharkhand festival guide. Current month: {current_month}
        User query: "{query}"
        
        Festival data:
        {festival_context}
        
        Provide festival info in this format (MAX 100 words):
        
        🎊 [Festival/Event Name]:
        
        📅 When: [Time/Date]
        📍 Where: [Main locations]
        ✨ Highlights: [2-3 key attractions]
        
        🎭 Also check: [1-2 other festivals]
        
        💡 Tip: [One visitor tip]
        
        Focus on what's most relevant to the query. If asking about current/upcoming, prioritize those.
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
            truncated = ' '.join(words[:95]) + "..."
            return truncated
        return response
    
    def _create_fallback_response(self, query: str) -> str:
        """Fallback festival information"""
        query_lower = query.lower()
        
        # Check for specific festivals
        if "sarhul" in query_lower:
            return (
                "🎊 Sarhul Festival:\n\n"
                "📅 When: March-April\n"
                "📍 Where: Ranchi, Khunti, Gumla\n"
                "✨ Highlights: Sal tree worship, tribal dances, folk songs\n\n"
                "💡 Tip: Join locals at Morabadi Ground, Ranchi for authentic celebrations!"
            )
        
        elif "karma" in query_lower:
            return (
                "🎊 Karma Festival:\n\n"
                "📅 When: August-September\n"
                "📍 Where: Across Jharkhand\n"
                "✨ Highlights: Karma tree worship, night dancing, harvest celebration\n\n"
                "💡 Tip: Village celebrations are more authentic than city events!"
            )
        
        elif any(word in query_lower for word in ["upcoming", "next", "this month"]):
            return (
                "🎊 Upcoming Festivals:\n\n"
                "🌸 Sarhul: March-April\n"
                "🌾 Karma: August-September\n"
                "☀️ Chhath: October-November\n"
                "🎵 Tusu: January\n\n"
                "💡 Tip: Check Jharkhand Tourism website for exact dates!"
            )
        
        else:
            # General festival info
            return (
                "🎊 Major Jharkhand Festivals:\n\n"
                "🌸 Sarhul (Spring): Tribal new year\n"
                "🌾 Karma (Monsoon): Harvest dance\n"
                "☀️ Chhath (Winter): Sun worship\n"
                "🎵 Tusu (January): Folk songs\n\n"
                "💡 Tip: Experience tribal festivals for authentic culture!"
            )

def festival_info(user_query: str, gemini_api_key: str) -> str:
    """Main function for festival information"""
    if not gemini_api_key:
        return (
            "🎊 Jharkhand Festivals:\n\n"
            "🌸 Sarhul (Mar-Apr): Tribal spring fest\n"
            "🌾 Karma (Aug-Sep): Harvest celebration\n"
            "☀️ Chhath (Oct-Nov): Sun worship\n\n"
            "💡 Visit during festivals for cultural immersion!"
        )
    
    try:
        festival_guide = FestivalGuide(gemini_api_key)
        return festival_guide.generate_festival_info(user_query)
    except Exception as e:
        return (
            "🎊 Festival Calendar:\n"
            "Sarhul: March-April\n"
            "Karma: August-September\n"
            "Chhath: October-November\n"
            "Check Jharkhand Tourism for dates!"
        )
    
# from dotenv import load_dotenv
# load_dotenv()
# print(festival_info("Upcoming festivals in Jharkhand", os.getenv("GOOGLE_API_KEY")))