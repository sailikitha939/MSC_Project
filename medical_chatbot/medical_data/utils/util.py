import configparser
import os
from youtube_transcript_api import YouTubeTranscriptApi
import openai
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, logger
from urllib.parse import urlparse, parse_qs
from fastapi import APIRouter
from fastapi import FastAPI, HTTPException
from urllib.parse import urlparse, parse_qs
from starlette.concurrency import run_in_threadpool
from youtube_transcript_api import YouTubeTranscriptApi
import openai
from dotenv import load_dotenv
from langchain.vectorstores import FAISS 
from typing import Dict
from medical_data.pre_processing.preprocessor import DataPreprocessing


def get_config(section, key):
    config = configparser.ConfigParser()
    config_file_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.ini')
    config.read(config_file_path)
    return config.get(section, key)

async def extract_transcript(youtube_video_url: str) -> str:
    try:
        url_parsed = urlparse(youtube_video_url)
        if url_parsed.netloc == 'youtu.be':
            video_id = url_parsed.path[1:]  # Remove the first slash
        else:
            query_string = parse_qs(url_parsed.query)
            video_id = query_string.get('v', [None])[0]
        
        if not video_id:
            raise ValueError("YouTube video ID could not be extracted.")
        
        transcript_list = await run_in_threadpool(YouTubeTranscriptApi.get_transcript, video_id)
        transcript = " ".join([item["text"] for item in transcript_list])
        return transcript
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

async def generate_summary_and_quiz(transcript: str) -> str:
    try:
        prompt = """
        You are a Youtube video summarizer and quiz generator. You will be taking the transcript text
        and summarizing the entire video and providing the important summary in points
        within 250 words. Then, generate a few quiz questions based on the summary ask 5 multiple choice questions based on the content and give the answers in the last after all questions. Please provide the summary of the text given here and generated quizzes and answers here:
        """
        response = await run_in_threadpool(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt + transcript}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

