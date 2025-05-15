import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import json
import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud import vision

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="Skypad Image Tagging & Explanation MVP", layout="wide")

st.title("Skypad Image Tagging & Explanation MVP")
st.write("""
Upload images and select a vision model to automatically categorize, tag, and explain your photos.
""")

# Setup credentials section - load from environment variables
def get_api_key(service_name):
    if service_name == "OpenAI":
        env_var_name = "OPENAI_API_KEY"
        return os.environ.get(env_var_name, "")
    return None

def get_google_credentials_path():
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

# OpenAI Vision API
def analyze_image_with_openai(image_bytes, api_key):
    try:
        import base64
        # Convert image to base64
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
                            "text": "Analyze this image and provide: 1) A short caption, 2) Five specific tags that categorize what's in the image, and 3) A brief explanation about the image content and context. Format your response as JSON with keys: caption, tags, explanation."
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
            # Parse the content as JSON
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

# Google Vision API implementation using Service Account
def analyze_image_with_google(image_bytes, credentials_path):
    try:
        # Create client from credentials file
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        client = vision.ImageAnnotatorClient(credentials=credentials)
        
        # Create image from bytes
        image = vision.Image(content=image_bytes)
        
        # Perform detection - getting features one by one to avoid issues
        label_detection = client.label_detection(image=image, max_results=10)
        web_detection = client.web_detection(image=image)
        text_detection = client.text_detection(image=image)
        
        # Extract labels (tags)
        labels = []
        if label_detection.label_annotations:
            labels = [
                {
                    "description": label.description,
                    "score": float(label.score) if hasattr(label, 'score') else 0.0
                }
                for label in label_detection.label_annotations[:5]
            ]
        
        # Extract web detection results - fix the access pattern
        web_entities = []
        if hasattr(web_detection, 'web_entities'):
            for entity in web_detection.web_entities:
                if hasattr(entity, 'description') and entity.description:
                    score = 0.0
                    if hasattr(entity, 'score'):
                        score = float(entity.score)
                    web_entities.append({
                        "description": entity.description,
                        "score": score
                    })
            web_entities = web_entities[:5]  # Limit to top 5
        
        # Extract text
        text = ""
        if hasattr(text_detection, 'text_annotations') and text_detection.text_annotations:
            if text_detection.text_annotations:
                text = text_detection.text_annotations[0].description
        
        # Generate caption and explanation with safeguards
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
            "raw_response": {
                "labels": labels,
                "webEntities": web_entities,
                "text": text
            }
        }
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        # For debugging - show raw web detection structure (safely)
        web_detection_structure = "Not available"
        try:
            if 'web_detection' in locals() and web_detection:
                web_detection_structure = str(dir(web_detection))
        except:
            pass
            
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "traceback": tb_str,
            "debug_info": {
                "web_detection_structure": web_detection_structure
            }
        }

# Main UI
tab1, tab2 = st.tabs(["Demo", "About MVP"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        model = st.selectbox(
            "Select Vision Model:",
            ["OpenAI (GPT-4o)", "Google Vision"]
        )
        
        # Handle credentials based on selected model
        if model.startswith("OpenAI"):
            # OpenAI API key handling
            env_api_key = get_api_key("OpenAI")
            
            if not env_api_key:
                api_key = st.text_input(
                    "Enter OpenAI API Key",
                    type="password"
                )
                credentials_source = "manual"
            else:
                api_key = env_api_key
                st.success("OpenAI API key loaded from environment variables")
                if st.checkbox("Override environment API key"):
                    api_key = st.text_input(
                        "Enter OpenAI API Key",
                        value="",
                        type="password"
                    )
                    credentials_source = "manual"
                else:
                    credentials_source = "environment"
                    
            credentials = api_key
        else:  # Google Vision
            # Google credentials handling
            env_credentials_path = get_google_credentials_path()
            
            if not env_credentials_path:
                credentials_path = st.text_input(
                    "Enter path to Google service account JSON file",
                    value=""
                )
                credentials_source = "manual"
            else:
                credentials_path = env_credentials_path
                st.success("Google credentials loaded from environment variables")
                if st.checkbox("Override environment credentials"):
                    credentials_path = st.text_input(
                        "Enter path to Google service account JSON file",
                        value=""
                    )
                    credentials_source = "manual"
                else:
                    credentials_source = "environment"
                    
            credentials = credentials_path
        
        uploaded_file = st.file_uploader(
            "Upload an image", 
            type=["jpg", "jpeg", "png"]
        )
            
        if uploaded_file and credentials and st.button("Analyze Image"):
            with st.spinner(f"Analyzing image with {model.split('(')[0].strip()}..."):
                # Read image and reset position
                image_bytes = uploaded_file.getvalue()
                
                if model.startswith("OpenAI"):
                    result = analyze_image_with_openai(image_bytes, credentials)
                elif model.startswith("Google"):
                    result = analyze_image_with_google(image_bytes, credentials)
                
                # Store results
                st.session_state.analysis_result = result
                st.session_state.current_image = uploaded_file
                st.session_state.credentials_source = credentials_source
        
    with col2:
        if 'current_image' in st.session_state and st.session_state.current_image:
            st.image(st.session_state.current_image, use_container_width=True)
            
            if 'analysis_result' in st.session_state:
                result = st.session_state.analysis_result
                
                if result.get("success", False):
                    st.success("Analysis completed successfully")
                    
                    st.subheader("Caption")
                    st.write(result.get("caption", ""))
                    
                    st.subheader("Tags")
                    tags = result.get("tags", [])
                    if isinstance(tags, list):
                        for tag in tags:
                            st.write(f"- {tag}")
                    else:
                        st.write(tags)
                    
                    st.subheader("Explanation")
                    st.write(result.get("explanation", ""))
                    
                    with st.expander("Raw Response"):
                        st.json(result.get("raw_response", {}))
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
        else:
            st.info("Upload an image and click 'Analyze Image' to see results")

with tab2:
    st.markdown("""
    ## About This MVP
    
    This is a minimally viable product (MVP) demonstration for Skypad International's AI-powered image management.
    
    ### How it works
    1. Upload an image
    2. Choose a vision model (OpenAI GPT-4o or Google Vision API)
    3. View automatic tagging, captioning, and explanations
    
    ### Features
    - Image analysis with OpenAI Vision API
    - Image analysis with Google Vision API
    - Automatic tagging and categorization
    - Image description and explanation
    
    ### Next Steps
    - Add support for batch processing multiple images
    - Implement additional vision models
    - Train custom models for Skypad-specific furniture and design elements
    - Integrate with Digital Asset Management (DAM) systems
    """)