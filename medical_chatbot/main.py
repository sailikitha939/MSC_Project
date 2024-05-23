import sys
import os
import logging
from typing import Dict
from fastapi import FastAPI, HTTPException, File, UploadFile, Query,Form, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS 
from medical_data.pre_processing.text_splitter import RecursiveTextSplitter
from medical_data.pre_processing.preprocessor import DataPreprocessing
from medical_data.utils import logger, util
from dotenv import load_dotenv
import uvicorn
import openai
from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Any, List
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredImageLoader
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# Initialize embeddings and language model
model_name = 'text-embedding-ada-002'
embed = OpenAIEmbeddings(model=model_name, openai_api_key=openai.api_key)
llm = ChatOpenAI(openai_api_key=openai.api_key, model_name='gpt-3.5-turbo', temperature=0.0)

# Initialize utilities
recursive_splitter = RecursiveTextSplitter(max_chunk_size=2000)
pre_processor = DataPreprocessing()

# Configure logging
logger = logging.getLogger("uvicorn")

# Initialize FastAPI app
app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

documents: Dict[str, Dict[str, str]] = {}
document_embeddings: Dict[str, object] = {}

# Endpoint to upload and process documents
@app.post("/upload_document/")
async def upload_document(file: UploadFile = File(...), user_id: str = Query(...)):
    logger.info(f"Upload document request started for user_id: {user_id}")
    try:
        content = await file.read()
        content = content.decode("utf-8")
        
        # Preprocess the text
        processed_text = pre_processor.preprocess_text(content)
        processed_text = pre_processor.remove_stop_words(processed_text)
        
        # Store the original and processed content
        documents[user_id] = {"original": content, "processed": processed_text}
        
        # Split the preprocessed text into chunks
        chunks = recursive_splitter.split_text(processed_text)
        
        # Store the embeddings of the processed text
        document_embeddings[user_id] = FAISS.from_texts(chunks, embed)
        
        logger.info("Document uploaded and processed successfully")
        return {"message": "Document uploaded successfully"}
    except Exception as e:
        logger.error(f"Error in uploading document for user_id {user_id}: {e}")
        return {"error": str(e)}

# Request model for asking questions
class QuestionRequest(BaseModel):
    question: str

# Endpoint to ask questions based on uploaded documents
@app.post("/ask_question/")
async def ask_question(question_request: QuestionRequest):
    user_id = '1'  
    logger.info(f"Asking question: {question_request.question} for user_id: {user_id}")
    try:
        user_document = documents.get(user_id)
        if not user_document:
            raise HTTPException(status_code=404, detail="Document not found for user")
        
        # Retrieve stored embeddings
        docsearch = document_embeddings.get(user_id)
        if not docsearch:
            raise HTTPException(status_code=404, detail="Document embeddings not found for user")
        
        retriever = docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        rqa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
        
        query = question_request.question
        result = rqa(query)
        answer = result['result'] if 'result' in result else "Sorry, I couldn't find an answer."
        
        logger.info("Question answered successfully")
        return {"answer": answer}
    except HTTPException as http_ex:
        logger.error(f"HTTP exception for user_id {user_id}: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        logger.error(f"Error in asking question for user_id {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Welcome endpoint
@app.get("/")
def welcome():
    return {"message": "Welcome to the Document Classification API!"}

# Request model for processing videos
class VideoRequest(BaseModel):
    youtube_link: str

# Endpoint to process YouTube videos
@app.post("/process_video/")
async def process_video(request_body: VideoRequest):
    youtube_link = request_body.youtube_link
    if not youtube_link:
        raise HTTPException(status_code=400, detail="No YouTube link provided")
    
    transcript = await util.extract_transcript(youtube_link)
    if not transcript:
        raise HTTPException(status_code=500, detail="Unable to extract transcript")
    
    summary_and_quiz = await util.generate_summary_and_quiz(transcript)
    return {"summary_and_quiz": summary_and_quiz}

@unique
class ModelType(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_4 = "gpt-4"

BASE_PATH = Path("C:/Users/Windows 11/OneDrive/Documents/MajorProjLMU/project/medical_chatbot")

COMPANY = "Your Company"

SYSTEM_MESSAGE = """
You are an {character_name}, a {character_role} at {company_name}. You are {character_personality}.

Here is the candidate's CV/resume: {cv}

Here is the job description: {job_description}

This is some extra context about the candidate: {user_context}

Below, you may see a conversation history between you, the candidate and your other colleagues: {other_characters}

Conduct an interview with the candidate. Start By Introducing Yourself and ask the candidate to introduce and start the interview. Make sure to grill them on their resume and ask questions related to the job description also. Be aggressive if it doesn't match what they say. Always stay in your character.
"""

class SubmitMessageRequest(BaseModel):
    message: str
    messages: List[str] = []

@dataclass
class Database:
    user_name: str = None
    role: str = None
    cv: str = None
    job_description: str = None
    user_context: str = None
    message_history: List[dict[str, Any]] = field(default_factory=list)
    company: str = COMPANY
    uploaded: bool = False

    def upload(self, document, type="cv"):
        self.uploaded = True
        if type == "cv":
            self.cv = document
        else:
            self.job_description = document

    def init_chat(self, user_name, role, job_description, user_context, company):
        self.user_name = user_name
        self.role = role
        self.job_description = job_description
        self.user_context = user_context
        self.company = company
        if not self.uploaded:
            self.cv = None
        self.message_history = []

database = Database()

characters = [
    {
        "name": "Rose",
        "role": "Vice President of Google",
        "personality": "assertive, analytical, detail-oriented, and inquisitive",
    },
]

def load_documents(file_path, is_pdf):
    if is_pdf:
        loader = PyMuPDFLoader(file_path)
    else:
        loader = UnstructuredImageLoader(file_path)
    documents = loader.load()
    return documents

def get_document_string(file_path, is_pdf):
    documents = load_documents(file_path, is_pdf)
    document_str = "\n".join(doc.page_content for doc in documents)
    return document_str

@app.post("/upload")   #Candidate Form Details
async def upload_file(
    name: str = Form(...),
    role: str = Form(...),
    job_description: str = Form(...),
    file: UploadFile = File(...)
):
    print(f"Received upload request with name: {name}, role: {role}, job_description: {job_description}, file: {file.filename}")

    # Validate input data
    if not name or not role or not job_description or not file:
        raise HTTPException(status_code=400, detail="All fields are required")

    # Validate file type
    allowed_extensions = ['pdf', 'docx', 'txt']
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, and TXT files are allowed")

    try:
        file_path = BASE_PATH / f"data/document-uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        doc_string = get_document_string(str(file_path), is_pdf=(file_extension == "pdf"))
        database.upload(doc_string, type="cv")
        database.init_chat(user_name=name, role=role, job_description=job_description, user_context="", company=COMPANY)
        return {"filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_chat_response(messages, model=ModelType.GPT_3_5_TURBO):
    response = openai.ChatCompletion.create(
        model=model.value,
        messages=messages,
        temperature=0.4,
        max_tokens=150,
    )
    return response

async def generate_next_message(new_message):
    global database
    messages = database.message_history
    current_character = characters[len(messages) % len(characters)]
    other_characters = ", ".join(
        [
            f'{c["name"]}: {c["role"]}'
            for c in characters
            if c["name"] != current_character["name"]
        ]
    )
    system_message = SYSTEM_MESSAGE.format(
        character_name=current_character["name"],
        character_role=current_character["role"],
        character_personality=current_character["personality"],
        company_name=database.company,
        cv=database.cv,
        job_description=database.job_description,
        user_context=database.user_context,
        other_characters=other_characters,
    )
    message = {"role": "user", "content": new_message}
    messages.append(message)
    _messages = [{"role": "system", "content": system_message}]
    _messages += [{"role": m["role"], "content": m["content"]} for m in messages]
    resp = await get_chat_response(_messages)
    output = resp.choices[0].message
    messages.append(output)
    database.message_history = messages
    return output, current_character

@app.post("/submit-message")
async def submit_message(body: SubmitMessageRequest):
    output, current_character = await generate_next_message(body.message)
    return {"user_message": body.message, "message": output["content"], "character": current_character}

@app.post("/generate-feedback")
async def generate_feedback():
    global database
    messages = database.message_history
    if not messages:
        raise HTTPException(status_code=400, detail="No conversation history found.")
    
    feedback_prompt = """
    Please provide feedback on the candidate's performance during the interview. 
    Focus on areas where they did well and areas where they could improve, providing 
    specific suggestions for how they could improve their performance in similar 
    situations in the future.
    
    Here is the conversation history:
    """

    for message in messages:
        feedback_prompt += f"{message['role']}: {message['content']}\n"

    feedback_prompt += "\nEnd of conversation history.\n"
    
    try:
        response = openai.ChatCompletion.create(
            model=ModelType.GPT_3_5_TURBO.value,
            messages=[{"role": "system", "content": feedback_prompt}],
            temperature=0.7,
            max_tokens=200,
        )
        feedback = response.choices[0].message["content"]
        return {"feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == '__main__':
    file_path = 'C:\\Users\\Windows 11\\OneDrive\\Documents\\MajorProjLMU\\project\\medical_chatbot\\data\\input\\nhs_data.txt'
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        logger.error(f"Error starting the server: {e}")
        sys.exit(1)


