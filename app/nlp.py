import requests
from transformers import pipeline
import re
import warnings
from word2number import w2n
from sentence_transformers import SentenceTransformer
import chromadb
import os
import time
import json
import google.generativeai as genai

# Suppress the specific warning about grouped_entities
warnings.filterwarnings("ignore", message=".*grouped_entities.*")

# Initialize Gemini AI
# Using the provided API key directly
genai.configure(api_key="AIzaSyBP34KRObP85dy1gQ_Q8QcjnRAmFQB478w")

# Initialize embedding model and ChromaDB collections (in-memory)
model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.Client()
names_collection = chroma_client.get_or_create_collection("names")
years_collection = chroma_client.get_or_create_collection("years_experience")
skills_collection = chroma_client.get_or_create_collection("skills")
roles_collection = chroma_client.get_or_create_collection("roles")

def get_embedding(text):
    return model.encode([text])[0].tolist()

def add_to_chroma(collection, label):
    emb = get_embedding(label)
    collection.add(
        embeddings=[emb],
        documents=[label],
        ids=[label.lower()]
    )

def find_similar(collection, candidate, threshold=0.8):
    emb = get_embedding(candidate)
    results = collection.query(
        query_embeddings=[emb],
        n_results=1
    )
    # Fix: Check if results are non-empty and distances are present
    if (
        results['ids'] and results['distances'] and 
        len(results['distances']) > 0 and len(results['distances'][0]) > 0
    ):
        if results['distances'][0][0] < (1-threshold):
            return results['documents'][0][0]
    return None

def convert_spoken_numbers_to_digits(text: str) -> str:
    # Convert spoken numbers to digits: "three years" → "3 years"
    words = text.split()
    for i, word in enumerate(words):
        try:
            words[i] = str(w2n.word_to_num(word))
        except:
            continue
    return ' '.join(words)

def merge_ner_tokens(ner_results):
    merged = []
    skip_next = False
    for i, ent in enumerate(ner_results):
        if skip_next:
            skip_next = False
            continue
        word = ent['word']
        label = ent.get('entity_group', '')
        # Merge with next if next word starts with ##
        if i + 1 < len(ner_results) and ner_results[i+1]['word'].startswith('##'):
            merged_word = word + ner_results[i+1]['word'][2:]
            merged.append({'entity_group': label, 'word': merged_word})
            skip_next = True
        else:
            merged.append({'entity_group': label, 'word': word})
    return merged

def extract_first_json_object(text):
    start = text.find('{')
    if start == -1:
        return None
    stack = []
    for i in range(start, len(text)):
        if text[i] == '{':
            stack.append('{')
        elif text[i] == '}':
            stack.pop()
            if not stack:
                try:
                    return json.loads(text[start:i+1])
                except Exception:
                    return None
    return None


def gemini_extract_entities_and_faq(transcription: str) -> dict:
    """
    Extract entities and generate dynamic FAQs from the transcription using Gemini AI.
    """
    prompt = (
        "You are an HR assistant analyzing an interview transcript for a hiring manager. "
        "Your task is to extract key information and summarize the candidate's claims into a structured JSON format. "
        "Respond ONLY with a valid JSON object containing the following keys:\n"
        "- 'candidate_name': (string) The candidate's full name as stated.\n"
        "- 'skills': (list of strings) A list of all specific skills, technologies, or tools the candidate mentioned.\n"
        "- 'years_experience': (number) The total number of years of experience claimed by the candidate. If not mentioned, use null.\n"
        "- 'desired_role': (string) The specific job title or role the candidate is seeking.\n"
        "- 'faq': (list of objects) A summary of the candidate's key claims, formatted as 3-4 question-answer pairs for the hiring manager. "
        "Each object must have 'question' and 'answer' keys.\n"
        "  - The 'question' should be a factual query about a topic the candidate brought up (e.g., 'What is the candidate's experience with databases?', 'What are their core front-end skills?').\n"
        "  - The 'answer' should be a concise summary of what the candidate said about that topic, based *only* on the provided transcript.\n\n"
        "Transcript to analyze:\n" + transcription
    )
    
    try:
        print(f"[GEMINI] Sending request for combined entity and FAQ generation.")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        if response.text:
            # Extract JSON from the response
            json_response_str = response.text.strip()
            # Remove any markdown formatting if present
            if json_response_str.startswith('```json'):
                json_response_str = json_response_str[7:]
            if json_response_str.endswith('```'):
                json_response_str = json_response_str[:-3]
            
            entities = json.loads(json_response_str.strip())
            print(f"[GEMINI] Extracted entities and FAQs: {entities}")
            return entities
        else:
            print(f"[GEMINI] No response text received")
            return {}
            
    except json.JSONDecodeError as e:
        print(f"[GEMINI] JSON Decode Error: {e}")
        print(f"[GEMINI] Raw response content: {response.text if hasattr(response, 'text') else 'No text'}")
        return {}
    except Exception as e:
        print(f"[GEMINI] Extraction error: {e}")
        return {}

def extract_entities(transcription: str) -> dict:
    print(f"[NLP] Input transcription for combined processing: {transcription}")
    # This single call now gets both entities and dynamic FAQs using Gemini
    gemini_data = gemini_extract_entities_and_faq(transcription)
    # Normalize and process the data as before, returning a final dictionary
    # The structure now comes directly from the single Gemini call
    final_data = {
        "candidate_name": gemini_data.get("candidate_name", "Unknown"),
        "skills": gemini_data.get("skills", []),
        "years_experience": gemini_data.get("years_experience"),
        "desired_role": gemini_data.get("desired_role", "Unknown"),
        "faq": gemini_data.get("faq", [])  # This now contains dynamic Q&A
    }
    print(f"[NLP] Final processed data: {final_data}")
    return final_data 

