import os
import json
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from PIL import Image
import io

# 1. Load Environment Variables
load_dotenv()
app = Flask(__name__)

# 2. Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY is missing from .env file!")
else:
    genai.configure(api_key=api_key)

# 3. Safety Settings (Unblock civic content so AI doesn't refuse to see garbage/potholes)
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# 4. 🧠 SMART MODEL AUTO-DETECTOR
def get_best_model_name():
    """Automatically finds the newest available Gemini model."""
    print("🔍 Scanning available models...")
    try:
        # Priority List (Newest First)
        preferences = [
            'models/gemini-2.5-flash',       # Ultra fast & new
            'models/gemini-2.0-flash',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro-vision'
        ]
        
        # Get your actual available models
        my_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Match preference
        for pref in preferences:
            if pref in my_models:
                print(f"✨ Auto-Selected Best Model: {pref}")
                return pref
        
        # Fallback to whatever is first
        if my_models:
            print(f"⚠️ specific preference not found, using: {my_models[0]}")
            return my_models[0]
            
    except Exception as e:
        print(f"⚠️ Model scan failed: {e}")
    
    return 'models/gemini-1.5-flash' # Safe default

# Initialize Model Name Once on Startup
CURRENT_MODEL_NAME = get_best_model_name()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_issue():
    print("--- 📸 Analysis Request Received ---")
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes))

        # ⚡ STRICT JUDGE PROMPT ⚡
        # This ensures scores vary between 1 and 10 based on real danger.
        prompt = """
        Analyze this image of a civic/infrastructure issue.
        Act as a conservative City Engineer and Risk Analyst. Do not exaggerate.
        
        Return valid JSON (no markdown). Keys:
        {
            "title": "Short professional title",
            "description": "Technical description (2 sentences)",
            "severity_score": (Integer 1-10),
            "department": "Relevant Govt Department",
            "impact_forecast": "Scientific prediction of what happens in 30 days if ignored",
            "risks": ["Risk 1", "Risk 2", "Risk 3"],
            "required_evidence": "Suggestion for 1 better angle/photo to take"
        }

        ⛔ SCORING RUBRIC (FOLLOW STRICTLY):
        - Score 1-3 (LOW): Cosmetic only. Graffiti, faded paint, small litter, tiny crack. NO safety risk.
        - Score 4-6 (MEDIUM): Inconvenience. Pothole, overflowing bin, broken bench. Annoying but not deadly.
        - Score 7-8 (HIGH): Health Hazard. Open manhole, exposed electrical wire, massive garbage dump (rats/disease).
        - Score 9-10 (CRITICAL): IMMEDIATE DEATH RISK. Building collapsing, bridge falling, massive fire, deep flood.
        
        Analyze the image reality. Do not default to 8.
        """

        model = genai.GenerativeModel(CURRENT_MODEL_NAME, safety_settings=SAFETY_SETTINGS)
        response = model.generate_content([prompt, image])
        
        # Clean Markdown if the AI adds it (e.g., ```json ... ```)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        print(f"✅ Analysis Done. JSON: {clean_text[:100]}...")
        
        return jsonify(json.loads(clean_text))

    except Exception as e:
        print(f"🔥 ANALYSIS ERROR: {str(e)}")
        return jsonify({'error': f"AI Error: {str(e)}"}), 500


@app.route('/generate-complaint', methods=['POST'])
def generate_complaint():
    print("--- 📝 Drafting Complaint ---")
    
    try:
        data = request.json
        issue_data = data.get('issue_data')
        recipient_type = data.get('recipient_type')

        if not issue_data:
            return jsonify({'error': 'No issue data found'}), 400

        # Context-Aware Prompt
        prompt = f"""
        Act as a professional civic liaison.
        Write a complaint/message regarding: {issue_data.get('title')}.
        
        Context:
        - Issue: {issue_data.get('description')}
        - Severity: {issue_data.get('severity_score')}/10
        - Impact Forecast: {issue_data.get('impact_forecast')}
        
        Recipient: {recipient_type}
        
        Instructions:
        - If 'Official': Write a strict, formal letter to the {issue_data.get('department')}. Use technical terms.
        - If 'MLA': Write a persuasive appeal emphasizing community votes and welfare.
        - If 'Social': Write a viral, urgent WhatsApp message with emojis (⚠️, 🚨).
        
        Output ONLY the message body. No placeholders like [Your Name].
        """

        # Generate Text
        model = genai.GenerativeModel(CURRENT_MODEL_NAME, safety_settings=SAFETY_SETTINGS)
        response = model.generate_content([prompt]) 
        
        print("✅ Complaint Drafted")
        return jsonify({'letter': response.text})

    except Exception as e:
        print(f"🔥 GENERATION ERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)