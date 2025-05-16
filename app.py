#!/usr/bin/env python3
"""
Skypad Image Tagging & Explanation - Consolidated Web App
Includes OpenAI Vision API, Google Vision API, and local CLIP model integration.
"""
import os
import sys
import json
import warnings
from io import BytesIO
from PIL import Image
import streamlit as st
import requests

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
try:
    import torch
    import open_clip
    has_clip = True
except ImportError:
    has_clip = False
    print("Warning: CLIP dependencies not installed. CLIP model will not be available.")

st.set_page_config(page_title="Skypad Image Tagging & Explanation", layout="wide")

st.title("Skypad Image Tagging & Explanation")
st.write("""
Upload images and select a vision model to automatically categorize, tag, and explain your photos.
""")

# Helper functions to handle credentials
def get_api_key(service_name):
    """Get API key from environment variables or return empty string"""
    if service_name == "OpenAI":
        return os.environ.get("OPENAI_API_KEY", "")
    return None

def get_google_credentials_path():
    """Get Google credentials path from environment variables or return empty string"""
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

# OpenAI Vision API analysis function
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

# Google Vision API implementation
def analyze_image_with_google(image_bytes, credentials_path):
    if not has_google_vision:
        return {
            "success": False,
            "error": "Google Cloud Vision API is not installed. Install with: pip install google-cloud-vision"
        }
        
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
        
        # Extract web detection results
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
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "traceback": tb_str
        }

# CLIP model implementation (local, no API cost)
def analyze_image_with_clip(image_bytes, use_furniture_categories=True):
    if not has_clip:
        return {
            "success": False,
            "error": "CLIP dependencies not installed. Install with: pip install torch open-clip-torch"
        }
        
    try:
        # Load CLIP model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai')
        model = model.to(device)
        
        # Load and preprocess the image
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image_input = preprocess(image).unsqueeze(0).to(device)
        
        # Define categories to check against
        if use_furniture_categories:
            # Furniture-specific categories for Skypad's domain
            categories = [
                "chair", "sofa", "table", "desk", "bed", "couch", "lamp", "drawer", 
                "cabinet", "furniture", "bedroom", "living room", "dining room",
                "office", "hotel lobby", "restaurant", "modern furniture", "luxury furniture",
                "wooden furniture", "metal furniture", "upholstered furniture", "outdoor furniture",
                "interior design", "minimalist design", "traditional design"
            ]
            category_type = "furniture-specific"
            prompt_prefix = "a photo of a"
        else:
            # Completely general categories - minimal furniture overlap
            categories = [
                # People and animals
                "person", "group of people", "crowd", "child", "baby", "adult",
                "man", "woman", "dog", "cat", "bird", "animal", "wildlife",
                
                # Outdoor scenes
                "landscape", "mountain", "beach", "ocean", "lake", "river", "forest",
                "field", "garden", "park", "city", "urban", "rural", "building",
                "skyscraper", "house", "street", "road", "highway", "bridge",
                
                # Nature elements
                "sky", "clouds", "sunset", "sunrise", "moon", "stars", "tree", 
                "flower", "plant", "grass", "rocks", "waterfall", "snow", "rain",
                
                # Indoor scenes (non-furniture focused)
                "classroom", "gym", "museum", "theater", "stadium", "airport",
                "train station", "grocery store", "mall", "hospital", "school",
                
                # Activities
                "sports", "running", "swimming", "hiking", "dancing", "eating",
                "cooking", "reading", "writing", "driving", "flying", "sailing",
                
                # Abstract concepts
                "happy", "sad", "peaceful", "chaotic", "bright", "dark", "colorful",
                "monochrome", "abstract", "realistic", "vintage", "modern",
                
                # Transportation
                "car", "truck", "bus", "train", "airplane", "boat", "bicycle",
                "motorcycle"
            ]
            category_type = "general"
            prompt_prefix = "a photo of"
            
        # Convert text categories to CLIP embeddings
        tokenizer = open_clip.get_tokenizer('ViT-B-32')
        text_tokens = tokenizer([f"{prompt_prefix} {c}" for c in categories]).to(device)
        
        # Calculate features
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_tokens)
            
            # Normalize features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            
        # Get top matches
        values, indices = similarity[0].topk(5)
        
        # Compile results
        tags = []
        for value, index in zip(values, indices):
            tags.append({
                "description": categories[index],
                "score": float(value)
            })
        
        # Generate a simple caption based on top tags
        top_tags = [tag["description"] for tag in tags[:3]]
        caption = f"Image showing {', '.join(top_tags)}"
        
        # Generate a simple explanation
        explanation = f"This image appears to be related to {top_tags[0]}. "
        explanation += f"It also has elements of {', '.join(top_tags[1:3])}. "
        explanation += "This analysis was done using OpenAI's CLIP model (via open-clip-torch), which matches images to text descriptions without requiring API calls."
        explanation += f"\n\nCategory mode used: {category_type} (toggle checkbox to switch)"
        
        return {
            "success": True,
            "tags": [tag["description"] for tag in tags],
            "caption": caption,
            "explanation": explanation,
            "raw_response": {
                "tags": tags,
                "model": "CLIP (ViT-B-32)",
                "device": device,
                "category_type": category_type
            }
        }
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        return {
            "success": False,
            "error": f"Exception: {str(e)}",
            "traceback": tb_str
        }

# Main UI
tab1, tab2 = st.tabs(["Demo", "About"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Determine available models based on installed dependencies
        available_models = []
        if has_clip:
            available_models.append("CLIP (Local - No API Cost)")
        available_models.append("OpenAI (GPT-4o)")
        if has_google_vision:
            available_models.append("Google Vision")
        
        model = st.selectbox(
            "Select Vision Model:",
            available_models
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
        elif model.startswith("Google"):
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
        else:  # CLIP model
            st.success("CLIP model runs locally - no API key needed")
            credentials = "local"
            credentials_source = "local"
        
        uploaded_file = st.file_uploader(
            "Upload an image", 
            type=["jpg", "jpeg", "png"]
        )
        
        use_furniture_categories = st.checkbox("Use furniture-specific categories", value=True)
            
        if uploaded_file and (credentials or model.startswith("CLIP")) and st.button("Analyze Image"):
            with st.spinner(f"Analyzing image with {model.split('(')[0].strip()}..."):
                # Read image and reset position
                image_bytes = uploaded_file.getvalue()
                
                if model.startswith("OpenAI"):
                    result = analyze_image_with_openai(image_bytes, credentials)
                elif model.startswith("Google"):
                    result = analyze_image_with_google(image_bytes, credentials)
                elif model.startswith("CLIP"):
                    result = analyze_image_with_clip(image_bytes, use_furniture_categories)
                
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
    ## About This App
    
    This is a consolidated application for Skypad International's AI-powered image tagging and explanation system.
    
    ### How it works
    1. Upload an image
    2. Choose a vision model:
       - CLIP (runs locally without API costs)
       - OpenAI GPT-4o (requires API key)
       - Google Vision API (requires credentials)
    3. View automatic tagging, captioning, and explanations
    
    ### Features
    - Image analysis with locally-running CLIP model (no API costs)
    - Image analysis with OpenAI Vision API
    - Image analysis with Google Vision API
    - Automatic tagging and categorization
    - Image description and explanation
    
    ### Next Steps
    - Add support for batch processing multiple images
    - Train custom models for Skypad-specific furniture and design elements
    - Integrate with Digital Asset Management (DAM) systems
    """)

# If this script is run directly (not imported), start the Streamlit app
if __name__ == "__main__":
    # This will be handled by Streamlit's script runner
    pass