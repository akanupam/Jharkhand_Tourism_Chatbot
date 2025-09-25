import os
import requests
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain import hub
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

github_url = "https://raw.githubusercontent.com/akanupam/my_datasets/main/Jharkhand%20tourism.pdf"
response = requests.get(github_url)

# Save the PDF content to a temporary local file
with open("temp_github_file.pdf", "wb") as f:
    f.write(response.content)

# Load the PDF from the temporary local file
loader = PyPDFLoader(file_path="temp_github_file.pdf")
docs = loader.load()


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=20,
)
texts = text_splitter.split_documents(docs)


vectorstore = Chroma.from_documents( texts,HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"))
retriever = vectorstore.as_retriever()

prompt = hub.pull("rlm/rag-prompt")

from langchain_google_genai import ChatGoogleGenerativeAI


# Make sure you have set the environment variable
from dotenv import load_dotenv
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("Please set the GOOGLE_API_KEY environment variable")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    convert_system_message_to_human=True
)


def format_docs(docs):
  return "\n".join(doc.page_content for doc in docs)

rag_chain= ({"context": retriever| format_docs, "question": RunnablePassthrough()}
            |prompt
            |llm
            |StrOutputParser())

# def main():
#   query = input("Ask your query: ")
#   print(rag_chain.invoke(query))

# main()



from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import nest_asyncio
from handlers.planner import plan_trip
from handlers.area import nearby_suggestions
from handlers.route import route_directions
from handlers.hotels import hotel_recommendations
from handlers.helplines import get_helpline
from handlers.festivals import festival_info
from intents import classify_intent, get_out_of_domain_response



def answer_from_rag(query: str) -> str:
    return rag_chain.invoke(query)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):

    user_msg = req.message
    if not user_msg:
        raise HTTPException(status_code=400, detail="Empty message")
    intent = classify_intent(user_msg)
    if intent == "OUT_OF_DOMAIN":
        reply = get_out_of_domain_response(user_msg)
        return ChatResponse(reply=reply)
    from dotenv import load_dotenv
    load_dotenv()
    gemini_key = os.getenv("GOOGLE_API_KEY")
    if intent == "RAG_FAQ":
        reply = answer_from_rag(user_msg)
    elif intent == "TRIP_PLANNER":
        reply = plan_trip(user_msg, gemini_key)
    elif intent == "AREA_SUGGEST":
        reply = nearby_suggestions(user_msg, gemini_key)
    elif intent == "ROUTE_HELPER":
        reply = route_directions(user_msg, gemini_key)
    elif intent == "HOTEL_SUGGEST":
        reply = hotel_recommendations(user_msg, gemini_key)
    elif intent == "HELPLINE":
        reply = get_helpline(user_msg, gemini_key)
    elif intent == "FESTIVALS":
        reply = festival_info(user_msg, gemini_key)
    else:
        # Fallback
        reply = "Sorry, I couldn't understand your request."
    print(f"User query: {user_msg}, Classified as: {intent}")
    return ChatResponse(reply=reply)



if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)

