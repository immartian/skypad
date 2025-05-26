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

# Import Bella's system prompt
from bella_prompt import BELLA_SYSTEM_PROMPT

# Try to import OpenAI for chat functionality
try:
    import openai
    has_openai = True
except ImportError:
    has_openai = False
    print("Warning: OpenAI not installed. Bella chat will not be available.")

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

st.set_page_config(page_title="Skypad AI Platform - MVP1", layout="wide")

st.title("Skypad AI Platform - MVP1")
st.write("""
**Image Analysis & AI Strategy Guide** - Upload images for AI-powered tagging and chat with Bella about Skypad's AI roadmap.
""")

# Helper functions to handle credentials
def get_api_key(service_name):
    """Get API key from environment variables or return empty string"""
    if service_name == "OpenAI":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Log info about the API key (without showing the key itself)
        if api_key:
            print(f"Found {service_name} API key in environment variables (length: {len(api_key)})")
        else:
            print(f"No {service_name} API key found in environment variables")
        
        return api_key
    return None

def get_google_credentials_path():
    """Get Google credentials path from environment variables or return empty string"""
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Log info about credentials path 
    if cred_path:
        print(f"Found Google credentials path: {cred_path}")
        if os.path.exists(cred_path):
            print(f"Google credentials file exists.")
        else:
            print(f"Warning: Google credentials file not found at {cred_path}")
    else:
        print("No Google credentials path found in environment variables")
        
    return cred_path

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
def analyze_image_with_clip(image_bytes, use_furniture_categories=True, min_confidence=0.05, temperature=0.9):
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
            # Enhanced furniture-specific categories with more detailed descriptions
            categories = [
                # Seating
                "dining chair", "office chair", "accent chair", "armchair", "lounge chair", 
                "recliner", "bar stool", "counter stool", "sofa", "loveseat", "sectional sofa",
                "chaise lounge", "ottoman", "bench", "outdoor bench",
                
                # Tables
                "coffee table", "dining table", "side table", "console table", "desk", 
                "writing desk", "computer desk", "executive desk", "nightstand", "end table",
                "bistro table", "outdoor dining table", "conference table",
                
                # Storage
                "bookcase", "bookshelf", "cabinet", "storage cabinet", "file cabinet", 
                "sideboard", "hutch", "wardrobe", "chest of drawers", "dresser", 
                "credenza", "media console", "display case",
                
                # Beds
                "bed frame", "king bed", "queen bed", "twin bed", "bunk bed", "canopy bed",
                "platform bed", "upholstered bed", "sleeper sofa", "daybed", "murphy bed",
                
                # Lighting
                "floor lamp", "table lamp", "desk lamp", "pendant light", "chandelier",
                "wall sconce", "ceiling light", "outdoor lighting", "task lighting",
                
                # Room types
                "living room", "dining room", "bedroom", "home office", "entry hall", "foyer",
                "kitchen", "bathroom", "outdoor patio", "outdoor terrace", "balcony",
                "hotel lobby", "hotel room", "restaurant dining area", "cafe seating", "conference room",
                
                # Design styles
                "modern interior", "contemporary interior", "minimalist interior", "traditional interior",
                "industrial style", "mid-century modern", "scandinavian design", "rustic interior",
                "coastal style", "bohemian style", "art deco style", "farmhouse style",
                
                # Materials
                "wooden furniture", "leather furniture", "fabric upholstery", "metal furniture",
                "glass furniture", "marble surface", "rattan furniture", "wicker furniture",
                
                # Features
                "upholstered", "ergonomic", "swivel chair", "reclining", "adjustable height",
                "with storage", "extendable", "folding", "stackable", "modular"
            ]
            category_type = "enhanced-furniture-specific"
            prompt_prefix = "a photo of"
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
        
        # Convert text categories to CLIP embeddings with improved prompting
        tokenizer = open_clip.get_tokenizer('ViT-B-32')
        
        # Create more descriptive prompts for better zero-shot performance
        prompts = []
        for category in categories:
            # Use different templates based on category to improve accuracy
            if "room" in category or "interior" in category or "style" in category or "area" in category:
                prompts.append(f"a photo of a {category}")
            elif category.startswith(("with", "ergonomic", "upholstered", "reclining", "adjustable", "extendable", "folding", "stackable", "modular")):
                prompts.append(f"a photo of {category} furniture")
            else:
                prompts.append(f"a photo of a {category}")
        
        text_tokens = tokenizer(prompts).to(device)
        
        # Calculate features
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_tokens)
            
            # Normalize features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity with temperature scaling for better confidence distribution
            # Lower temperature (e.g., 0.8) gives sharper peaks, higher (e.g., 1.2) gives more even distribution
            # Use the temperature parameter passed from the UI
            similarity = (100.0 * image_features @ text_features.T / temperature).softmax(dim=-1)
            
        # Apply confidence threshold to filter out low-confidence predictions
        # This helps prevent generic categories from being assigned when they're not relevant
        # Use the min_confidence parameter passed from the UI
        confidence_mask = similarity[0] >= min_confidence
        
        # If we filtered out everything, just take the top 5
        if not torch.any(confidence_mask):
            values, indices = similarity[0].topk(5)
        else:
            # Get values that meet threshold and take top matches (up to 8)
            filtered_similarity = similarity[0] * confidence_mask
            values, indices = filtered_similarity.topk(min(8, torch.sum(confidence_mask).item()))
        
        # Compile results with filtering for overlapping or redundant categories
        raw_tags = []
        for value, index in zip(values, indices):
            raw_tags.append({
                "description": categories[index],
                "score": float(value)
            })
        
        # Filter out redundant/overlapping categories to ensure diversity in results
        filtered_tags = []
        used_terms = set()
        
        # Helper function to check if a tag overlaps too much with already selected tags
        def is_redundant(tag_desc):
            tag_words = set(tag_desc.lower().split())
            
            # Check overlap with existing terms
            for existing in used_terms:
                # If this is a subset of an existing tag or vice versa, consider redundant
                if tag_words.issubset(existing) or existing.issubset(tag_words):
                    return True
                
                # If there's significant word overlap, consider redundant
                overlap = len(tag_words.intersection(existing)) / min(len(tag_words), len(existing))
                if overlap > 0.7:  # 70% overlap threshold
                    return True
            return False
        
        # Add non-redundant tags to filtered list
        for tag in raw_tags:
            tag_desc = tag["description"].lower()
            tag_words = set(tag_desc.split())
            
            if not is_redundant(tag_desc):
                filtered_tags.append(tag)
                used_terms.add(frozenset(tag_words))
                
            # Stop after we've found 5 diverse tags
            if len(filtered_tags) >= 5:
                break
        
        # If we've filtered too aggressively, add back some of the top tags
        if len(filtered_tags) < 3:
            for tag in raw_tags:
                if tag not in filtered_tags:
                    filtered_tags.append(tag)
                if len(filtered_tags) >= 5:
                    break
        
        # Use the filtered tags
        tags = filtered_tags
        
        # Generate a more descriptive caption based on top tags
        top_tags = [tag["description"] for tag in tags[:3]]
        
        if category_type == "enhanced-furniture-specific":
            # Create a more natural-sounding furniture caption
            if "room" in top_tags[0] or "interior" in top_tags[0]:
                caption = f"Image showing a {top_tags[0]}"
            else:
                caption = f"Image showing {top_tags[0]}"
                
            if len(top_tags) > 1:
                caption += f" with {', '.join(top_tags[1:3])}"
        else:
            # General caption format
            caption = f"Image showing {', '.join(top_tags)}"
        
        # Generate a more informative explanation
        if category_type == "enhanced-furniture-specific":
            explanation = f"This image appears to show {top_tags[0]}. "
            
            # Group categories by type for more coherent explanation
            furniture_items = [t for t in top_tags if any(word in t for word in ["chair", "table", "sofa", "bed", "desk", "cabinet", "shelf", "lamp"])]
            room_types = [t for t in top_tags if any(word in t for word in ["room", "office", "lobby", "restaurant", "cafe", "area", "patio", "terrace"])]
            style_terms = [t for t in top_tags if any(word in t for word in ["style", "design", "modern", "contemporary", "traditional", "industrial", "century", "minimalist"])]
            
            if furniture_items:
                explanation += f"The furniture includes {', '.join(furniture_items)}. "
            if room_types and room_types != furniture_items:
                explanation += f"The space appears to be a {', '.join(room_types)}. "
            if style_terms and style_terms != furniture_items and style_terms != room_types:
                explanation += f"The design style is {', '.join(style_terms)}. "
        else:
            explanation = f"This image appears to be related to {top_tags[0]}. "
            if len(top_tags) > 1:
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
                "filtered_from": raw_tags[:10],  # Include the raw tags before filtering
                "model": "CLIP (ViT-B-32)",
                "device": device,
                "category_type": category_type,
                "parameters": {
                    "temperature": temperature,
                    "min_confidence": min_confidence
                }
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

# Bella Chat Function
# Add model selection parameter
def chat_with_bella(message, api_key, chat_model="gpt-3.5-turbo"):
    """Send a message to Bella and get a response using OpenAI's API"""
    if not has_openai:
        return "Sorry, OpenAI library is not installed. Please install it to use Bella chat."
    
    try:
        # Create the OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Send the message to OpenAI
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
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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
            type=["jpg", "jpeg", "png", "webp"]
        )
        
        # Enhanced CLIP settings with better defaults
        use_furniture_categories = st.checkbox("Use enhanced furniture-specific categories", value=True)
        
        # Advanced options for CLIP model
        if model.startswith("CLIP"):
            with st.expander("Advanced CLIP Settings"):
                clip_confidence = st.slider(
                    "Confidence Threshold (%)", 
                    min_value=1, 
                    max_value=25, 
                    value=5,
                    help="Higher values require stronger confidence for category matches"
                )
                
                clip_temperature = st.slider(
                    "Temperature", 
                    min_value=0.5, 
                    max_value=1.5, 
                    value=0.9, 
                    step=0.1,
                    help="Lower values make predictions more decisive, higher values make them more balanced"
                )
                
                st.info("💡 If CLIP is identifying everything as 'office' or 'restaurant', try increasing the confidence threshold and lowering the temperature.")
            
        if uploaded_file and (credentials or model.startswith("CLIP")) and st.button("Analyze Image"):
            with st.spinner(f"Analyzing image with {model.split('(')[0].strip()}..."):
                # Read image and reset position
                image_bytes = uploaded_file.getvalue()
                
                if model.startswith("OpenAI"):
                    result = analyze_image_with_openai(image_bytes, credentials)
                elif model.startswith("Google"):
                    result = analyze_image_with_google(image_bytes, credentials)
                elif model.startswith("CLIP"):
                    # Pass the advanced settings to the CLIP analysis function
                    clip_params = {
                        "use_furniture_categories": use_furniture_categories
                    }
                    
                    # Add advanced parameters if they exist in the UI
                    if 'clip_confidence' in locals():
                        clip_params["min_confidence"] = clip_confidence / 100.0  # Convert percentage to decimal
                    if 'clip_temperature' in locals():
                        clip_params["temperature"] = clip_temperature
                        
                    result = analyze_image_with_clip(image_bytes, **clip_params)
                
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
    ## About Skypad AI Platform - MVP1
    
    This is **MVP1** of Skypad International's AI platform, featuring both image analysis capabilities and **Bella**, your AI strategy guide.
    
    ### 🖼️ Image Analysis
    1. Upload an image
    2. Choose a vision model:
       - **CLIP (Local)** - runs locally without API costs, enhanced for furniture categories
       - **OpenAI GPT-4o** - advanced analysis with natural language descriptions
       - **Google Vision** - comprehensive object and text detection
    3. View automatic tagging, captioning, and explanations
    
    ### 💬 Chat with Bella
    Bella is your AI guide for Skypad's Human+AI (HAI) strategy. She can help you understand:
    - The six AI use cases for Skypad
    - Implementation roadmap and phases
    - Key terminology (DAM, taxonomy, ontology, etc.)
    - Next steps and priorities
    - Architecture and technical decisions
    
    **Sample questions for Bella:**
    - "What are the main AI use cases for Skypad?"
    - "How does the DAM fit into our roadmap?"
    - "What's the difference between taxonomy and ontology?"
    - "Summarize our HAI strategy in one paragraph"
    
    ### 🎯 MVP1 Goals
    - **Team Alignment**: Make the AI vision accessible to everyone
    - **Knowledge Sharing**: Centralize strategy knowledge through Bella
    - **Foundation Building**: Prepare for future AI agent development
    - **Proof of Concept**: Demonstrate AI capabilities with image analysis
    
    ### 🚀 Next Steps (MVP2+)
    - Connect Bella to live data sources (ERP, CRM)
    - Add specialized AI agents (Vendor Intelligence, Client Insights)
    - Batch image processing and DAM integration
    - Advanced analytics and predictive modeling
    
    ### 📊 Implementation Phases
    - **Phase 0**: Baseline Assessment (1 month)
    - **Phase 1**: Data Foundation (2-3 months) 
    - **Phase 2**: MVP Agents (2 months) ← *We are here*
    - **Phase 3**: Human-in-the-Loop (2 months)
    - **Phase 4**: Expansion (6-10 months)
    - **Phase 5**: Continuous Optimization (6-10 months)
    """)

# Sidebar for Bella Chat
with st.sidebar:
    st.header("💬 Chat with Bella 👩‍💼")
    st.write("*Your AI guide for Skypad's strategy*")
    
    # Chat model selection (cheapest by default)
    chat_models = [
        ("GPT-3.5-turbo (cheapest)", "gpt-3.5-turbo"),
        ("GPT-4o (best quality)", "gpt-4o")
    ]
    chat_model_label = st.selectbox(
        "Choose Chat Model:",
        [label for label, _ in chat_models],
        index=0
    )
    chat_model = dict(chat_models)[chat_model_label]
    
    # Check if we have OpenAI capabilities
    if not has_openai:
        st.warning("⚠️ OpenAI library not installed. Bella chat is not available.")
        st.info("To enable Bella, install OpenAI: `pip install openai`")
    else:
        # API key input for Bella
        bella_api_key = get_api_key("OpenAI")
        
        # Only show input field if no API key found in environment
        if not bella_api_key:
            bella_api_key = st.text_input(
                "OpenAI API Key for Bella:",
                type="password",
                help="Enter your OpenAI API key to chat with Bella"
            )
            if not bella_api_key:
                st.info("👆 Enter your OpenAI API key above to start chatting with Bella")
                
        if bella_api_key:
            st.success("✅ Bella is ready to chat!")
            
            # Display chat history first
            if st.session_state.chat_history:
                st.subheader("Chat History")
                
                # Show recent messages (limit to last 6 messages to save space)
                recent_messages = st.session_state.chat_history[-6:]
                
                for message in recent_messages:
                    if message["role"] == "user":
                        st.markdown(f"**You:** {message['content']}")
                    else:
                        st.markdown(f"**👩‍💼 Bella:** {message['content']}")
                    st.markdown("---")
                
                # Show total message count
                total_messages = len(st.session_state.chat_history)
                if total_messages > 6:
                    st.info(f"Showing last 6 of {total_messages} messages")
            
            # Quick question buttons
            st.subheader("Quick Questions")
            quick_questions = [
                "What are the main AI use cases for Skypad?",
                "What's the difference between taxonomy and ontology?",
                "What's next after MVP0?",
                "Summarize our HAI strategy",
                "How does the DAM fit into our roadmap?"
            ]
            
            for question in quick_questions:
                if st.button(question, key=f"quick_{hash(question)}"):
                    # Add question to history and get response
                    import datetime
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    st.session_state.chat_history.append({
                        "role": "user", 
                        "content": question,
                        "timestamp": current_time
                    })
                    
                    with st.spinner("Bella is thinking..."):
                        bella_response = chat_with_bella(question, bella_api_key, chat_model)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": bella_response,
                        "timestamp": current_time
                    })
                    st.rerun()
            
            # Chat input moved below Quick Questions
            user_message = st.text_area(
                "Ask Bella anything about Skypad's AI strategy:",
                height=100,
                placeholder="e.g., What are the main AI use cases for Skypad?",
                key="chat_input_field"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Send to Bella", type="primary"):
                    if user_message.strip():
                        # Add user message to history
                        import datetime
                        current_time = datetime.datetime.now().strftime("%H:%M:%S")
                        
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": user_message,
                            "timestamp": current_time
                        })
                        
                        # Get Bella's response
                        with st.spinner("Bella is thinking..."):
                            bella_response = chat_with_bella(user_message, bella_api_key, chat_model)
                        
                        # Add Bella's response to history
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": bella_response,
                            "timestamp": current_time
                        })
                        
                        # Clear the input and rerun to refresh the UI
                        st.rerun()
                        
            with col2:
                if st.button("Clear Chat"):
                    st.session_state.chat_history = []
                    st.rerun()
        else:
            st.info("👆 Enter your OpenAI API key above to start chatting with Bella")

# If this script is run directly (not imported), start the Streamlit app
if __name__ == "__main__":
    # This will be handled by Streamlit's script runner
    pass