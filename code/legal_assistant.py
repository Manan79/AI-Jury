


import os
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY"))

LEGAL_SYSTEM_PROMPT = """
You are a Legal AI Assistant with expert knowledge of the Indian Constitution, Indian Penal Code (IPC),
Criminal Procedure Code (CrPC), and Indian laws.

⚖ Rules you MUST follow:
- Only answer questions related to law, constitution, rights, duties, IPC, CrPC, or legal principles.
- If the user asks a non-legal or irrelevant question, respond exactly:
  "I am a Legal AI Assistant and can only answer questions related to law."
- If the Constitution does not provide the information, respond with:
  "The Constitution does not provide this information."
- Always be concise, clear, and legally accurate.
"""

# --- Prompt Template ---
prompt = ChatPromptTemplate.from_messages([
    ("system", LEGAL_SYSTEM_PROMPT),
    ("human", "{question}")
])

# --- Function ---
def ask_legal_ai(question: str):
    chain = prompt | llm
    return chain.invoke({"question": question}).content


# ---------------------- FastAPI ----------------------

app = FastAPI(
    title="Legal Assistant API",
    description="API for querying Indian Constitution using LangChain",
    version="1.0.0"           
)

class Query(BaseModel):
    question: str

@app.get("/")
def home():
    return {
        "message": "Welcome to Legal Assistant API",
        "endpoints": {
            "/query": "POST - Ask questions about the Indian Constitution",
            "/health": "GET - Check API health"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Service is running"}

@app.post("/query") 
def query_constitution(query: Query):
    try:
        # Use the existing ask_legal_ai function to get response
        response = ask_legal_ai(query.question)
        
        return {
            "answer": response,
            "status": "success"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)