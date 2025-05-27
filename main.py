#!/usr/bin/env python3
"""
Skypad Image Tagging & Explanation - FastAPI Application
"""
import os
import sys
import json
import warnings
from io import BytesIO
from PIL import Image
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware # Import CORS middleware
import openai
from dotenv import load_dotenv
from bella_prompt import BELLA_SYSTEM_PROMPT

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
# Ensure your OPENAI_API_KEY is set in your .env file or environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    print("Warning: OPENAI_API_KEY not found. OpenAI API calls will fail.")

# Suppress warnings
warnings.filterwarnings("ignore")

# Try to import dotenv - not critical
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

# Try to import Google Vision - not critical
try:
    from google.oauth2 import service_account
    from google.cloud import vision
    has_google_vision = True
except ImportError:
    has_google_vision = False
    print("Warning: Google Cloud Vision not installed. Google Vision API will not be available.")

# Try to import CLIP dependencies - not critical
# try:
#     import torch
#     import open_clip
#     has_clip = True
# except ImportError:
#     has_clip = False
#     print("Warning: CLIP dependencies not installed. CLIP model will not be available.")
has_clip = False # Explicitly disable CLIP

app = FastAPI(title="Skypad AI Platform", version="1.0")

# --- CORS Middleware --- 
# This will allow your frontend (running on a different port) to communicate with the backend.
# For development, allowing all origins is fine. For production, restrict this to your frontend's domain.
origins = [
    "http://localhost",          # For local development if frontend is served from root
    "http://localhost:3000",     # Common port for create-react-app
    "http://localhost:5173",     # Common port for Vite
    # Add any other origins your frontend might be served from
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Static Files ---
# Mount the static files directory to serve the React app\'s build output
# This assumes your React app is built into \'frontend/dist\' and those files are copied to \'static\'
# in your Dockerfile or build process.
app.mount("/static", StaticFiles(directory="static", html=True), name="static_assets")

# --- Helper functions (copied and adapted from app.py) ---
def get_api_key(service_name: str) -> Optional[str]:
    """Get API key from environment variables or return None"""
    if service_name == "OpenAI":
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            print(f"Found {service_name} API key in environment variables (length: {len(api_key)})")
        else:
            print(f"No {service_name} API key found in environment variables")
        return api_key
    return None

def get_google_credentials_path() -> Optional[str]:
    """Get Google credentials path from environment variables or return None"""
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path:
        print(f"Found Google credentials path: {cred_path}")
        if os.path.exists(cred_path):
            print(f"Google credentials file exists.")
        else:
            print(f"Warning: Google credentials file not found at {cred_path}")
    else:
        print("No Google credentials path found in environment variables")
    return cred_path

# --- Pydantic Models for Request/Response ---
class ImageAnalysisResponse(BaseModel):
    success: bool
    tags: Optional[List[str]] = None
    caption: Optional[str] = None
    explanation: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    traceback: Optional[str] = None

class BellaChatRequest(BaseModel):
    message: str
    api_key: Optional[str] = None # Can be passed in request or read from env
    chat_model: str = "gpt-3.5-turbo"

class BellaChatResponse(BaseModel):
    response: str
    error: Optional[str] = None

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# --- API Endpoints ---

# Serve index.html for the root path
@app.get("/")
async def serve_react_app(request: Request): # Add request: Request
    return FileResponse("static/index.html")

@app.post("/analyze-image/", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(
    model_name: str = Form(...), # openai, google
    image: UploadFile = File(...),
    openai_api_key: Optional[str] = Form(None),
    google_credentials_path: Optional[str] = Form(None)
    # Remove CLIP specific form parameters:
    # use_furniture_categories: bool = Form(True),
    # clip_min_confidence: float = Form(0.05),
    # clip_temperature: float = Form(0.9)
):
    image_bytes = await image.read()

    if model_name.lower() == "openai":
        api_key_to_use = openai_api_key or get_api_key("OpenAI")
        if not api_key_to_use:
            raise HTTPException(status_code=400, detail="OpenAI API key not provided or found in environment.")
        return analyze_image_with_openai(image_bytes, api_key_to_use)
    elif model_name.lower() == "google":
        creds_path_to_use = google_credentials_path or get_google_credentials_path()
        if not creds_path_to_use:
            raise HTTPException(status_code=400, detail="Google credentials path not provided or found in environment.")
        if not has_google_vision:
             return ImageAnalysisResponse(success=False, error="Google Cloud Vision API is not installed on the server.")
        return analyze_image_with_google(image_bytes, creds_path_to_use)
    # elif model_name.lower() == "clip": # REMOVE CLIP BLOCK
    #     if not has_clip:
    #         return ImageAnalysisResponse(success=False, error="CLIP dependencies not installed on the server.")
    #     clip_params = {
    #         "use_furniture_categories": use_furniture_categories,
    #         "min_confidence": clip_min_confidence,
    #         "temperature": clip_temperature
    #     }
    #     return analyze_image_with_clip(image_bytes, **clip_params)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model_name}. Choose 'openai' or 'google'.")

@app.post("/chat-with-bella/", response_model=BellaChatResponse)
async def chat_with_bella_endpoint(request: BellaChatRequest):
    if not has_openai:
        return BellaChatResponse(response="", error="OpenAI library is not installed on the server.")

    api_key_to_use = request.api_key or get_api_key("OpenAI")
    if not api_key_to_use:
        return BellaChatResponse(response="", error="OpenAI API key not provided or found in environment.")

    try:
        response_content = chat_with_bella(request.message, api_key_to_use, request.chat_model)
        return BellaChatResponse(response=response_content)
    except Exception as e:
        return BellaChatResponse(response="", error=f"Sorry, I encountered an error: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_bella(chat_message: ChatMessage):
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured.")
    try:
        # For simplicity, we are not maintaining conversation history here yet.
        # In a more advanced setup, you would manage a list of messages (system, user, assistant).
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Or your preferred model, e.g., "gpt-4"
            messages=[
                {"role": "system", "content": BELLA_SYSTEM_PROMPT},
                {"role": "user", "content": chat_message.message}
            ]
        )
        # Correct way to access the message content from the response
        reply_content = completion.choices[0].message.content
        if reply_content is None:
            # Handle cases where content might be None, though rare for successful completions
            raise HTTPException(status_code=500, detail="OpenAI API returned an empty message.")
        return ChatResponse(reply=reply_content)
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred with the OpenAI API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# --- Analysis Functions (copied and adapted from app.py) ---

def analyze_image_with_openai(image_bytes: bytes, api_key: str) -> Dict[str, Any]:
    try:
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this image and provide: 1) A short caption, 2) Five specific tags that categorize what's in the image, 3) A brief explanation about the image content and context. Format your response as JSON with keys: caption, tags, explanation."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "response_format": {"type": "json_object"}
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            content = json.loads(result["choices"][0]["message"]["content"])
            return {
                "success": True,
                "tags": content.get("tags", []),
                "caption": content.get("caption", ""),
                "explanation": content.get("explanation", ""),
                "raw_response": content
            }
        else:
            return {
                "success": False,
                "error": f"Error: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Exception: {str(e)}"
        }

def analyze_image_with_google(image_bytes: bytes, credentials_path: str) -> Dict[str, Any]:
    if not has_google_vision: # Should be caught by endpoint, but good to double check
        return {
            "success": False,
            "error": "Google Cloud Vision API is not installed. Install with: pip install google-cloud-vision"
        }
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = vision.ImageAnnotatorClient(credentials=credentials)
        image = vision.Image(content=image_bytes)
        
        label_detection = client.label_detection(image=image, max_results=10)
        web_detection = client.web_detection(image=image)
        text_detection = client.text_detection(image=image)
        
        labels = []
        if label_detection.label_annotations:
            labels = [
                {"description": label.description, "score": float(label.score) if hasattr(label, 'score') else 0.0}
                for label in label_detection.label_annotations[:5]
            ]
        
        web_entities = []
        if hasattr(web_detection, 'web_entities'):
            for entity in web_detection.web_entities:
                if hasattr(entity, 'description') and entity.description:
                    score = float(entity.score) if hasattr(entity, 'score') else 0.0
                    web_entities.append({"description": entity.description, "score": score})
            web_entities = web_entities[:5]
        
        text = ""
        if hasattr(text_detection, 'text_annotations') and text_detection.text_annotations:
            text = text_detection.text_annotations[0].description
        
        caption_parts = [label["description"] for label in labels[:3]] if labels else ["Image"]
        caption = "Image containing " + ", ".join(caption_parts)
        
        explanation = "This image was analyzed. "
        if labels:
            explanation = f"This image appears to show {', '.join([label['description'] for label in labels[:3]])}. "
        if web_entities:
            explanation += f"Web analysis suggests it's related to {', '.join([entity['description'] for entity in web_entities[:3]])}. "
        if text:
            explanation += f"The image contains text: '{text[:100]}{'...' if len(text) > 100 else ''}'"
        
        return {
            "success": True,
            "tags": [label["description"] for label in labels],
            "caption": caption,
            "explanation": explanation,
            "raw_response": {"labels": labels, "webEntities": web_entities, "text": text}
        }
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        return {"success": False, "error": f"Exception: {str(e)}", "traceback": tb_str}

# def analyze_image_with_clip(image_bytes: bytes, use_furniture_categories: bool = True, min_confidence: float = 0.05, temperature: float = 0.9) -> Dict[str, Any]: # REMOVE ENTIRE FUNCTION
#     # ... entire function content ...
#     pass # Placeholder if the function is completely removed or commented out

def chat_with_bella(message: str, api_key: str, chat_model: str = "gpt-3.5-turbo") -> str:
    if not has_openai: # Should be caught by endpoint
        raise Exception("OpenAI library is not installed.")
    
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": BELLA_SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],
        max_tokens=800,
        temperature=0.7
    )
    return response.choices[0].message.content

# --- Main application runner (for local development) ---
if __name__ == "__main__":
    import uvicorn
    # Ensure the 'static' directory exists if you are running this directly
    # and expect index.html to be served.
    if not os.path.exists("static"):
        os.makedirs("static")
        # Create a dummy index.html if it doesn't exist, for development convenience
        if not os.path.exists("static/index.html"):
            with open("static/index.html", "w") as f:
                f.write("<html><body><h1>FastAPI Backend Running</h1><p>React frontend should replace this.</p></body></html>")
    
    # app.mount("/static", StaticFiles(directory="static"), name="static") # Mount after all routes are defined
    uvicorn.run(app, host="0.0.0.0", port=8000)
