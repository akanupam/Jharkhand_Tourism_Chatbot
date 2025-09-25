import json
import os
from pathlib import Path
import google.generativeai as genai

class HelplineService:
    def __init__(self, gemini_api_key: str):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.load_helpline_data()
        
    def load_helpline_data(self):
        """Load helpline numbers"""
        try:
            data_path = Path(__file__).parent.parent / 'data' / 'helplines.json'
            if not data_path.exists():
                data_path = Path('data/helplines.json')
            
            with open(data_path, 'r', encoding='utf-8') as f:
                self.helpline_data = json.load(f)
        except:
            self.helpline_data = self._get_default_helpline_data()
    
    def _get_default_helpline_data(self):
        """Essential helpline numbers"""
        return {
            "emergency": {
                "Police": "100",
                "Ambulance": "108",
                "Fire": "101",
                "Women Helpline": "1091",
                "Child Helpline": "1098"
            },
            "tourism": {
                "Jharkhand Tourism": "1800-123-4567",
                "Tourist Police": "1800-111-363",
                "Forest Department": "1800-123-5555"
            },
            "transport": {
                "Highway Emergency": "1033",
                "Railway Helpline": "139",
                "Airport Info": "0651-2511854"
            },
            "medical": {
                "RIMS Ranchi": "0651-2540629",
                "TMH Jamshedpur": "0657-2224444",
                "Emergency Medical": "108"
            }
        }
    
    def generate_helpline_response(self, query: str) -> str:
        """Generate concise helpline information"""
        helpline_context = json.dumps(self.helpline_data, indent=2)
        
        prompt = f"""
        You are a Jharkhand tourism helpline assistant.
        User query: "{query}"
        
        Available helplines:
        {helpline_context}
        
        Provide ONLY the most relevant helpline numbers in this format (MAX 100 words):
        
        📞 [Category] Helplines:
        
        🚨 [Service]: [Number]
        (List 3-5 most relevant numbers)
        
        💡 Quick tip: [One practical tip]
        
        Focus on what the user specifically needs. If general emergency, show main emergency numbers.
        If tourism-related, prioritize tourism helplines.
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
        """Fallback emergency numbers"""
        query_lower = query.lower()
        
        # Check query type
        if any(word in query_lower for word in ["medical", "hospital", "doctor", "ambulance"]):
            return (
                "📞 Medical Emergency:\n\n"
                "🚨 Ambulance: 108\n"
                "🏥 RIMS Ranchi: 0651-2540629\n"
                "🏥 TMH Jamshedpur: 0657-2224444\n\n"
                "💡 Tip: Save 108 for quick medical help anywhere in Jharkhand!"
            )
        
        elif any(word in query_lower for word in ["tourist", "tourism", "travel"]):
            return (
                "📞 Tourism Helplines:\n\n"
                "🎒 Jharkhand Tourism: 1800-123-4567\n"
                "👮 Tourist Police: 1800-111-363\n"
                "🌲 Forest Dept: 1800-123-5555\n\n"
                "💡 Tip: Tourist helpline assists 24/7 in multiple languages!"
            )
        
        else:
            # General emergency
            return (
                "📞 Emergency Numbers:\n\n"
                "🚨 Police: 100\n"
                "🚑 Ambulance: 108\n"
                "🚒 Fire: 101\n"
                "👩 Women: 1091\n"
                "🎒 Tourism: 1800-123-4567\n\n"
                "💡 Tip: Save these numbers before traveling!"
            )

def get_helpline(user_query: str, gemini_api_key: str) -> str:
    """Main function for helpline information"""
    if not gemini_api_key:
        # Return essential numbers even without API
        return (
            "📞 Emergency Helplines:\n\n"
            "🚨 Police: 100 | Ambulance: 108\n"
            "🎒 Tourism: 1800-123-4567\n"
            "👮 Highway: 1033 | Women: 1091\n\n"
            "💡 Save these numbers before traveling!"
        )
    
    try:
        helpline_service = HelplineService(gemini_api_key)
        return helpline_service.generate_helpline_response(user_query)
    except Exception as e:
        return (
            "📞 Quick Helplines:\n"
            "Emergency: 100 (Police), 108 (Medical)\n"
            "Tourism: 1800-123-4567\n"
            "Highway: 1033\n"
            "Save these numbers!"
        )
    

# from dotenv import load_dotenv
# load_dotenv()
# print(get_helpline("Medical emergency contacts", os.getenv("GOOGLE_API_KEY")))