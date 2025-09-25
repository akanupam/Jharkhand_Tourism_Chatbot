# 🏞️ Jharkhand Tourism Chatbot

An **AI-powered Tourism Assistant** for exploring **Jharkhand, India**, built with **FastAPI**, **LangChain**, and **Google Gemini**.  

💡 This chatbot acts as a **friendly Jharkhand tour guide**, helping travelers with:
- 🗓️ **Trip Planning** – Day-wise itineraries  
- 🗺️ **Nearby Attractions** – Area-aware suggestions  
- 🛣️ **Routes & Directions** – Text-based travel help (no maps)  
- 🏨 **Hotels** – Recommendations with links and pricing  
- 📞 **Helplines** – Emergency contact numbers  
- 🎉 **Festivals** – Information on local cultural events  
- ❓ **General FAQs** – Handled through RAG (Retrieval Augmented Generation) pipeline  

---

## ✨ Features
- 🌍 Domain-restricted: Only answers about **Jharkhand Tourism** (rejects “Paris”, “Goa”, etc.)  
- ⚡ FastAPI-powered REST API (`/api/chat`) with interactive Swagger docs  
- 📚 Retrieval-Augmented Generation (RAG) over Jharkhand tourism PDFs & JSON data  
- 🤖 Google Gemini (LLM) for conversational context, itineraries, and natural answers  
- 📦 Modular codebase (`handlers/` for each feature, `data/` for structured knowledge)  
- 🎨 Friendly, guide-like response style  
- 🚀 Cloud deployable (Render, Railway, Fly.io, Heroku, etc.)

---

## 🛠️ Tech Stack
- [FastAPI](https://fastapi.tiangolo.com/) – High-performance Python API framework  
- [Uvicorn](https://www.uvicorn.org/) – ASGI web server  
- [LangChain](https://www.langchain.com/) – Building RAG & LLM pipelines  
- [ChromaDB](https://www.trychroma.com/) – Vector database for embeddings  
- [Google Gemini API](https://ai.google.dev/) – Large Language Model for responses  
- [Pydantic](https://docs.pydantic.dev/) – Data validation  
- [Python-dotenv](https://pypi.org/project/python-dotenv/) – Environment variable management  

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/Jharkhand_Tourism_Chatbot.git
cd Jharkhand_Tourism_Chatbot
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

GOOGLE_API_KEY=your_google_gemini_api_key_here
