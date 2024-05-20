import sys
import os
import logging
from typing import Dict
from fastapi import FastAPI, HTTPException, File, UploadFile, Query
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

if __name__ == '__main__':
    file_path = 'C:\\Users\\Windows 11\\OneDrive\\Documents\\MajorProjLMU\\project\\medical_chatbot\\data\\input\\nhs_data.txt'
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        logger.error(f"Error starting the server: {e}")
        sys.exit(1)
