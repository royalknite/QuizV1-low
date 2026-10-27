"""
╔══════════════════════════════════════════════════════════════════════════╗
║                         QUIZBOT — Core Utilities                         ║
║                                                                          ║
║  Shared helpers: quiz rendering, HTML generation, image processing,      ║
║  premium checks, text cleaning, and MongoDB abstractions.                ║
║                                                                          ║
║  Sponsored by  : Qzio — qzio.in                                         ║
║  Developed by  : devgagan — devgagan.in                                  ║
║  License       : MIT                                                     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
import asyncio
import concurrent.futures
import json
import logging
import os
import random
import re
import time
import uuid
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from config import MONGO_URI, DB_NAME
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pymongo.errors import DuplicateKeyError
from unidecode import unidecode
import aiohttp
from config import FREE_BOT

from config import MONGO_URI, DB_NAME
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pymongo.errors import DuplicateKeyError
from unidecode import unidecode


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

PUBLIC_LINK_PATTERN = re.compile(r'(https?://)?(t\.me|telegram\.me)/([^/]+)(/(\d+))?')
PRIVATE_LINK_PATTERN = re.compile(r'(https?://)?(t\.me|telegram\.me)/c/(\d+)(/(\d+))?')

# Initialize MongoDB client
async def is_premium_user(user_id: int) -> bool:
    try:
        if FREE_BOT:
            return True
        r = await api_request(f'/premium/{user_id}')
        return bool(r and r.get('success') and r.get('is_premium'))
    except Exception as e:
        print(f"[is_premium_user] API error for {user_id}: {e}")
        return False


async def add_premium_user(user_id, duration_value, duration_unit):
    """Add a user as premium member with expiration time"""
    try:
        # Calculate expiration time based on duration
        now = datetime.utcnow()
        expiry_date = None
        
        if duration_unit == "min":
            expiry_date = now + timedelta(minutes=duration_value)
        elif duration_unit == "hours":
            expiry_date = now + timedelta(hours=duration_value)
        elif duration_unit == "days":
            expiry_date = now + timedelta(days=duration_value)
        elif duration_unit == "weeks":
            expiry_date = now + timedelta(weeks=duration_value)
        elif duration_unit == "month":
            expiry_date = now + timedelta(days=30 * duration_value)
        elif duration_unit == "year":
            expiry_date = now + timedelta(days=365 * duration_value)
        elif duration_unit == "decades":
            expiry_date = now + timedelta(days=3650 * duration_value)
        else:
            return False, "Invalid duration unit"
            
        # Add user to premium collection
        result = await premium_users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "user_id": user_id,
                "subscription_start": now,
                "subscription_end": expiry_date
            }},
            upsert=True
        )
        
        print(f"Added premium user {user_id}, expires at {expiry_date}")
        return True, expiry_date
        
    except Exception as e:
        print(f"Error adding premium user {user_id}: {e}")
        return False, str(e)




async def get_premium_details(user_id):
    """Get premium subscription details for a user"""
    try:
        user = await premium_users_collection.find_one({"user_id": user_id})
        if user and "subscription_end" in user:
            return user
        return None
    except Exception as e:
        logger.error(f"Error getting premium details for {user_id}: {e}")
        return None


def clean_html(text):
    if not text or not isinstance(text, str):
        return ""
    try:
        # Fix incomplete image URLs
        text = re.sub(r'//storage\.googleapis\.com', 'https://storage.googleapis.com', text)

        # --- Step 1: LaTeX Math Handling ---
        def latex_to_text(latex):
            try:
                # Store original LaTeX to revert if processing fails
                original_latex = latex
                
                # Common LaTeX replacements with proper math symbols
                replacements = {
                    # Basic operations
                    r'\\times': '×',
                    r'\\div': '÷',
                    r'\\cdot': '·',
                    r'\\pm': '±',
                    r'\\mp': '∓',
                    
                    # Comparison operators
                    r'\\neq': '≠',
                    r'\\approx': '≈',
                    r'\\equiv': '≡',
                    r'\\leq': '≤',
                    r'\\geq': '≥',
                    r'\\ll': '≪',
                    r'\\gg': '≫',
                    r'\\sim': '∼',
                    r'\\cong': '≅',
                    
                    # Arrows
                    r'\\to': '→',
                    r'\\rightarrow': '→',
                    r'\\leftarrow': '←',
                    r'\\uparrow': '↑',
                    r'\\downarrow': '↓',
                    r'\\Rightarrow': '⇒',
                    r'\\Leftarrow': '⇐',
                    r'\\leftrightarrow': '↔',
                    r'\\Leftrightarrow': '⇔',
                    
                    # Set theory
                    r'\\in': '∈',
                    r'\\notin': '∉',
                    r'\\subset': '⊂',
                    r'\\supset': '⊃',
                    r'\\subseteq': '⊆',
                    r'\\supseteq': '⊇',
                    r'\\emptyset': '∅',
                    r'\\cap': '∩',
                    r'\\cup': '∪',
                    r'\\setminus': '∖',
                    
                    # Logic
                    r'\\forall': '∀',
                    r'\\exists': '∃',
                    r'\\neg': '¬',
                    r'\\lor': '∨',
                    r'\\land': '∧',
                    r'\\implies': '⇒',
                    r'\\iff': '⇔',
                    
                    # Calculus
                    r'\\int': '∫',
                    r'\\iint': '∬',
                    r'\\iiint': '∭',
                    r'\\oint': '∮',
                    r'\\nabla': '∇',
                    r'\\partial': '∂',
                    r'\\sum': '∑',
                    r'\\prod': '∏',
                    r'\\infty': '∞',
                    r'\\lim': 'lim',
                    
                    # Roots
                    r'\\sqrt\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}': r'√(\1)',
                    r'\\sqrt\[([^]]*)\]\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}': r'∛(\2)',  # Not perfect for all nth roots
                    
                    # Parentheses and brackets
                    r'\\left\(': '(',
                    r'\\right\)': ')',
                    r'\\left\[': '[',
                    r'\\right\]': ']',
                    r'\\left\{': '{',
                    r'\\right\}': '}',
                    r'\\left\|': '|',
                    r'\\right\|': '|',
                    r'\\langle': '⟨',
                    r'\\rangle': '⟩',
                    r'\\lfloor': '⌊',
                    r'\\rfloor': '⌋',
                    r'\\lceil': '⌈',
                    r'\\rceil': '⌉',
                    
                    # Greek letters (lowercase)
                    r'\\alpha': 'α',
                    r'\\beta': 'β',
                    r'\\gamma': 'γ',
                    r'\\delta': 'δ',
                    r'\\epsilon': 'ε',
                    r'\\varepsilon': 'ε',
                    r'\\zeta': 'ζ',
                    r'\\eta': 'η',
                    r'\\theta': 'θ',
                    r'\\vartheta': 'ϑ',
                    r'\\iota': 'ι',
                    r'\\kappa': 'κ',
                    r'\\lambda': 'λ',
                    r'\\mu': 'μ',
                    r'\\nu': 'ν',
                    r'\\xi': 'ξ',
                    r'\\pi': 'π',
                    r'\\varpi': 'ϖ',
                    r'\\rho': 'ρ',
                    r'\\varrho': 'ϱ',
                    r'\\sigma': 'σ',
                    r'\\varsigma': 'ς',
                    r'\\tau': 'τ',
                    r'\\upsilon': 'υ',
                    r'\\phi': 'φ',
                    r'\\varphi': 'φ',
                    r'\\chi': 'χ',
                    r'\\psi': 'ψ',
                    r'\\omega': 'ω',
                    
                    # Greek letters (uppercase)
                    r'\\Gamma': 'Γ',
                    r'\\Delta': 'Δ',
                    r'\\Theta': 'Θ',
                    r'\\Lambda': 'Λ',
                    r'\\Xi': 'Ξ',
                    r'\\Pi': 'Π',
                    r'\\Sigma': 'Σ',
                    r'\\Upsilon': 'Υ',
                    r'\\Phi': 'Φ',
                    r'\\Psi': 'Ψ',
                    r'\\Omega': 'Ω',
                    
                    # Other symbols
                    r'\\hbar': 'ℏ',
                    r'\\ell': 'ℓ',
                    r'\\Re': 'ℜ',
                    r'\\Im': 'ℑ',
                    r'\\wp': '℘',
                    r'\\prime': '′',
                    r'\\backprime': '‵',
                    r'\\degree': '°',
                    r'\\circ': '∘',
                    r'\\bullet': '•',
                    r'\\star': '★',
                    r'\\ast': '∗',
                    r'\\oplus': '⊕',
                    r'\\ominus': '⊖',
                    r'\\otimes': '⊗',
                    r'\\oslash': '⊘',
                }
                
                # Process delimited expressions (e.g., \frac{}{}, \binom{}{}, etc.)
                # Handle fractions first
                def process_frac(match):
                    num = match.group(1)
                    denom = match.group(2)
                    return f"({num}/{denom})"
                
                latex = re.sub(r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', 
                              process_frac, latex)
                
                # Process binomials
                def process_binom(match):
                    n = match.group(1)
                    k = match.group(2)
                    return f"C({n},{k})"
                
                latex = re.sub(r'\\binom\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', 
                              process_binom, latex)
                
                # Apply all symbol replacements
                for pattern, replacement in replacements.items():
                    latex = re.sub(pattern, replacement, latex)
                
                # Handle subscripts and superscripts
                # Simple case: single character or digit
                latex = re.sub(r'([a-zA-Z0-9])\_\{([^{}]+)\}', r'\1_\2', latex)
                latex = re.sub(r'([a-zA-Z0-9])\^\{([^{}]+)\}', r'\1^\2', latex)
                
                # Simple case without braces
                latex = re.sub(r'([a-zA-Z0-9])\_([a-zA-Z0-9])', r'\1_\2', latex)
                latex = re.sub(r'([a-zA-Z0-9])\^([a-zA-Z0-9])', r'\1^\2', latex)
                
                # Handle limits for integrals, sums, etc.
                def process_limits(match):
                    operator = match.group(1)
                    lower = match.group(2)
                    upper = match.group(3)
                    return f"{operator} from {lower} to {upper}"
                
                latex = re.sub(r'(∫|∑|∏|lim)\_\{([^{}]+)\}\^\{([^{}]+)\}', process_limits, latex)
                
                # Clean up any leftover LaTeX commands we missed
                latex = re.sub(r'\\[a-zA-Z]+(\s|$)', '', latex)
                
                # If something went wrong and we made it worse, revert
                if '\\' in latex and len(latex) > len(original_latex):
                    return original_latex
                    
                return latex
            except Exception as e:
                print(f"LaTeX processing error: {e}")
                return latex  # Return original if processing fails
        
        # Process LaTeX in environments
        # Find \begin{equation}...\end{equation} and other math environments
        env_patterns = [
            (r'\\begin\{equation\}(.*?)\\end\{equation\}', r'\1'),
            (r'\\begin\{align\}(.*?)\\end\{align\}', r'\1'),
            (r'\\begin\{aligned\}(.*?)\\end\{aligned\}', r'\1'),
            (r'\\begin\{gather\}(.*?)\\end\{gather\}', r'\1'),
            (r'\\begin\{math\}(.*?)\\end\{math\}', r'\1')
        ]
        
        for pattern, replacement in env_patterns:
            text = re.sub(pattern, lambda m: latex_to_text(m.group(1)), text, flags=re.DOTALL)
        
        # Process LaTeX in \(...\) and \[...\] 
        text = re.sub(
            r'\\\((.*?)\\\)|\\\[(.*?)\\\]',
            lambda m: latex_to_text(m.group(1) if m.group(1) else m.group(2)),
            text,
            flags=re.DOTALL
        )
        
        # Process dollar sign delimited LaTeX
        text = re.sub(
            r'\$(.*?)\$|\$\$(.*?)\$\$',
            lambda m: latex_to_text(m.group(1) if m.group(1) else m.group(2)),
            text,
            flags=re.DOTALL
        )
        
        # Process standalone LaTeX expressions
        # Handle standalone fractions
        while re.search(r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', text):
            text = re.sub(
                r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
                lambda m: f"({m.group(1)}/{m.group(2)})",
                text
            )
        
        # Handle other standalone LaTeX symbols
        tex_symbols = {
            r'\\times': '×', 
            r'\\div': '÷',
            r'\\cdot': '·',
            r'\\pm': '±',
            r'\\sqrt\{([^{}]*)\}': r'√(\1)',
            r'\\neq': '≠',
            r'\\leq': '≤',
            r'\\geq': '≥',
            r'\\alpha': 'α',
            r'\\beta': 'β',
            r'\\gamma': 'γ',
            r'\\delta': 'δ',
            r'\\pi': 'π',
            r'\\theta': 'θ',
            r'\\sigma': 'σ',
            r'\\omega': 'ω',
            r'\\infty': '∞',
            r'\\sum': '∑',
            r'\\prod': '∏',
            r'\\int': '∫',
            r'\\partial': '∂',
        }
        
        for pattern, replacement in tex_symbols.items():
            text = re.sub(pattern, replacement, text)

        # --- Step 2: HTML Cleaning (Original Logic) ---
        soup = BeautifulSoup(text, 'html.parser')

        # Replace <br> with newlines
        for br in soup.find_all("br"):
            br.replace_with("\n")

        # Convert list items to bullets
        for li in soup.find_all("li"):
            li.insert_before("\n• ")
            li.unwrap()

        # Handle tables
        for table in soup.find_all("table"):
            table_text = ""
            for row in table.find_all("tr"):
                cols = row.find_all(["td", "th"])
                row_text = " • ".join([col.get_text(strip=True) for col in cols])
                table_text += f"{row_text}\n"
            table.replace_with(table_text)

        # Add line breaks after <p>
        for p in soup.find_all("p"):
            p.insert_after("\n")
            p.unwrap()

        # Remove unwanted tags
        for tag in soup(["style", "script", "a", "iframe", "img"]):
            tag.decompose()

        clean_text = soup.get_text(separator="\n")
        clean_text = re.sub(r'\n\s*\n+', '\n\n', clean_text)  # Reduce blank lines
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)  # Fix spacing

        return clean_text.strip()

    except Exception as e:
        print(f"HTML cleaning error: {e}")
        return text

async def generate_quiz_html(quiz, chat_id, context, ParseMode, type):
    def js_escape(text):
        if not text:
            return ""
        # Convert to string if not already
        text = str(text)
        # Escape special characters
        text = text.replace('\\', '\\\\')  # must be first
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        return text
    
    # Prepare quiz filename
    quiz_name = re.sub(r"[^a-zA-Z0-9_-]", "", unidecode(quiz["quiz_name"]).replace(" ", "_"))[:100] + ".html"
    max_marks = len(quiz["questions"])
    negative_mark = quiz.get("negative_marking", 0)
    total_time = 0
    if quiz.get("sections"):
        for section in quiz["sections"]:
            start, end = section.get("question_range", (0, -1))
            num_questions = end - start + 1
            section_timer = section.get("timer", 0)
            total_time += section_timer * num_questions
    else:
        total_time = (quiz.get("timer") or 60) * len(quiz["questions"])
    
    # Create question data for JavaScript
    questions_js = []
    for idx, q in enumerate(quiz["questions"]):
        options = q["options"].copy()
        correct_option = options[q["correct_option_id"]]
        random.shuffle(options)
        
        questions_js.append(f"""{{
            id: {idx},
            text: "{js_escape(q["question"])}",
            reference: "{js_escape(q.get("reply_text", ""))}",
            options: {json.dumps(options)},  // Using json.dumps for proper escaping
            correctIndex: {options.index(correct_option)},
            explanation: "{js_escape(q.get("explanation", "No explanation provided"))}"
        }}""")
    
    # Build the optimized HTML content with sound effects
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{quiz['quiz_name']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #4361ee;
            --secondary-color: #3a56d4;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --light-bg: #ffffff;
            --dark-bg: #1a1a2e;
            --light-text: #333333;
            --dark-text: #f8f9fa;
            --card-bg: #ffffff;
            --card-shadow: 0 15px 40px rgba(0,0,0,0.12);
            --option-btn-bg: #ffffff;
            --option-btn-border: #e6e6e6;
            --explanation-bg: #f8f9fa;
            --analysis-bg: #f8f9fa;
            --text-color: #333333;
            --border-color: #e6e6e6;
        }}

        [data-theme="dark"] {{
            --primary-color: #7e96ff;
            --secondary-color: #6a7fd4;
            --light-bg: #1a1a2e;
            --dark-bg: #16213e;
            --light-text: #f8f9fa;
            --dark-text: #e2e2e2;
            --card-bg: #16213e;
            --card-shadow: 0 15px 40px rgba(0,0,0,0.3);
            --option-btn-bg: #1f2a4e;
            --option-btn-border: #2a3a6e;
            --explanation-bg: #1f2a4e;
            --analysis-bg: #1f2a4e;
            --text-color: #f8f9fa;
            --border-color: #2a3a6e;
        }}
        
        

        body {{
            font-family: 'Poppins', sans-serif;
            background: var(--light-bg);
            color: var(--text-color);
            min-height: 100vh;
            padding-bottom: 50px;
            transition: background 0.3s ease, color 0.3s ease;
        }}

        .dark-mode body {{
            background: var(--dark-bg);
            color: var(--dark-text);
        }}
        
        .mcard-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-color); /* Will auto-switch in dark mode */
            margin-bottom: 1rem; /* mb-3 equivalent */
        }}
        
        .quiz-container {{
            max-width: 800px;
            margin: 20px auto;
            background: var(--card-bg);
            border-radius: 15px;
            box-shadow: var(--card-shadow);
            overflow: hidden;
            animation: fadeIn 0.5s;
            touch-action: pan-y;
            transition: background 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .question-text {{
             font-size: 18px;
             line-height: 1.6;
             color: var(--text-color);
             margin-bottom: 20px;
             padding: 10px 0;
            font-weight: 500;
        }}

        .dark-mode .question-text {{
             color: var(--dark-text);
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px) }}
            to {{ opacity: 1; transform: translateY(0) }}
        }}

        @keyframes slideIn {{
            from {{ transform: translateX(20px); opacity: 0 }}
            to {{ transform: translateX(0); opacity: 1 }}
        }}

        .quiz-header {{
            position: sticky;
            top: 0;
            z-index: 1000;
            background: var(--card-bg);
            padding: 15px 20px;
            border-bottom: 1px solid var(--border-color);
            transition: background 0.3s ease, border-color 0.3s ease;
        }}

        .timer {{
            font-size: 22px;
            font-weight: 600;
            color: var(--primary-color);
        }}

        .question-card {{
            border: none;
            box-shadow: 0 5px 20px rgba(0,0,0,0.06);
            margin-bottom: 25px;
            border-radius: 15px;
            overflow: hidden;
            transition: all 0.4s ease;
            animation: slideIn 0.4s;
            background: var(--card-bg);
        }}

        .dark-mode .question-card {{
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}

        .question-reference {{
            background-color: rgba(67, 97, 238, 0.1);
            border-left: 5px solid var(--primary-color);
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            color: var(--text-color);
        }}

        .option-btn {{
            text-align: left;
            padding: 16px 20px;
            margin-bottom: 12px;
            border-radius: 12px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            border: 1px solid var(--option-btn-border);
            background-color: var(--option-btn-bg);
            color: var(--text-color);
            width: 100%;
        }}

        .option-btn:hover {{
            background-color: rgba(67, 97, 238, 0.1);
            transform: translateX(5px);
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }}

        .option-btn.selected {{
            background-color: rgba(67, 97, 238, 0.2);
            border-color: var(--primary-color);
            font-weight: 500;
            box-shadow: 0 5px 15px rgba(67,97,238,0.15);
        }}

        .option-btn.correct {{
            background-color: rgba(40, 167, 69, 0.2);
            border-color: var(--success-color);
        }}

        .option-btn.incorrect {{
            background-color: rgba(220, 53, 69, 0.2);
            border-color: var(--danger-color);
        }}

        .progress {{
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            background-color: rgba(0,0,0,0.1);
        }}

        .dark-mode .progress {{
            background-color: rgba(255,255,255,0.1);
        }}

        .progress-bar {{
            transition: width 1s linear;
        }}

        .result-card {{
            display: none;
            animation: fadeIn 0.5s;
            color: var(--text-color);
        }}

        .score-highlight {{
            font-size: 48px;
            font-weight: 700;
            color: var(--primary-color);
            text-align: center;
            margin: 20px 0;
        }}

        .explanation {{
            background-color: var(--explanation-bg);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            border-left: 3px solid var(--primary-color);
            transition: background 0.3s ease;
            color: var(--text-color);
        }}

        .analysis-panel {{
            background-color: var(--analysis-bg);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
            transition: background 0.3s ease;
            color: var(--text-color);
        }}

        .analysis-item {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            color: var(--text-color);
        }}

        .analysis-icon {{
            width: 24px;
            height: 24px;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            color: white;
        }}

        .btn-primary {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            border-radius: 30px;
            padding: 10px 25px;
            transition: all 0.3s ease;
        }}

        .btn-primary:hover {{
            background-color: var(--secondary-color);
            border-color: var(--secondary-color);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(67,97,238,0.2);
        }}

        .confetti {{
            position: fixed;
            width: 10px;
            height: 10px;
            background-color: #f00;
            position: absolute;
            top: 0;
            z-index: 9999;
        }}

        .chart-container {{
            height: 220px;
        }}

        .time-bar {{
            height: 8px;
            background: rgba(0,0,0,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }}

        .dark-mode .time-bar {{
            background: rgba(255,255,255,0.1);
        }}

        .time-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: 4px;
            transition: width 0.5s;
        }}

        .badge-avg {{
            background-color: rgba(67, 97, 238, 0.2);
            color: var(--primary-color);
            font-weight: 500;
            padding: 5px 10px;
            border-radius: 20px;
        }}

        .badge-fast {{
            background-color: rgba(40, 167, 69, 0.2);
            color: var(--success-color);
            font-weight: 500;
            padding: 5px 10px;
            border-radius: 20px;
        }}

        .badge-slow {{
            background-color: rgba(220, 53, 69, 0.2);
            color: var(--danger-color);
            font-weight: 500;
            padding: 5px 10px;
            border-radius: 20px;
        }}

        /* Mobile-first styles */
        @media (max-width: 768px) {{
            .quiz-container {{
                margin: 10px;
                border-radius: 10px;
            }}

            .quiz-header {{
                padding: 12px 15px;
            }}

            .timer {{
                font-size: 18px;
            }}

            .question-card {{
                margin-bottom: 15px;
                border-radius: 10px;
            }}

            .option-btn {{
                padding: 12px 15px;
                margin-bottom: 8px;
                border-radius: 8px;
            }}

            .score-highlight {{
                font-size: 36px;
            }}
        }}

        /* Hamburger menu styles */
        .menu-toggle {{
            display: none;
            background: none;
            border: none;
            font-size: 24px;
            color: var(--primary-color);
            cursor: pointer;
            padding: 5px;
            margin-right: 10px;
        }}

        .question-list-container {{
            position: fixed;
            top: 0;
            left: -300px;
            width: 280px;
            height: 100vh;
            background: var(--card-bg);
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            z-index: 1100;
            transition: left 0.3s ease;
            overflow-y: auto;
            padding: 20px;
        }}

        .dark-mode .question-list-container {{
            box-shadow: 2px 0 10px rgba(0,0,0,0.3);
        }}

        .question-list-container.show {{
            left: 0;
        }}

        .question-list-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
        }}

        .question-list-title {{
            font-weight: 600;
            font-size: 18px;
            color: var(--primary-color);
        }}

        .close-menu-btn {{
            background: none;
            border: none;
            font-size: 20px;
            color: var(--text-color);
            cursor: pointer;
        }}

        .question-list {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }}

        .question-list-item {{
            padding: 10px;
            text-align: center;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
            font-weight: 600;
            color: var(--text-color);
        }}

        .dark-mode .question-list-item {{
            background: rgba(255,255,255,0.05);
        }}

        .question-list-item:hover {{
            background: rgba(67, 97, 238, 0.1);
            transform: scale(1.05);
        }}

        .question-list-item.active {{
            background: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }}

        .question-list-item.correct {{
            background: var(--success-color);
            color: white;
            border-color: var(--success-color);
        }}

        .question-list-item.incorrect {{
            background: var(--danger-color);
            color: white;
            border-color: var(--danger-color);
        }}

        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1050;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }}

        .overlay.show {{
            opacity: 1;
            visibility: visible;
        }}

        /* Theme toggle button */
        .theme-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--primary-color);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 1000;
            border: none;
            font-size: 20px;
        }}

        @media (max-width: 768px) {{
            .menu-toggle {{
                display: block;
            }}

            .question-list {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        @media (max-width: 480px) {{
            .question-list {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Remove the bottom question navigation */
        .quiz-pagination {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <!-- Hidden audio elements for sound effects -->
    <audio id="clickSound" src="https://assets.mixkit.co/active_storage/sfx/269/269.wav" preload="auto"></audio>
    <audio id="swipeSound" src="https://assets.mixkit.co/active_storage/sfx/1897/1897.wav" preload="auto"></audio>
    <audio id="correctSound" src="https://assets.mixkit.co/active_storage/sfx/2870/2870.wav" preload="auto"></audio>
    <audio id="wrongSound" src="https://assets.mixkit.co/active_storage/sfx/2964/2964.wav" preload="auto"></audio>
    
    <!-- Question list sidebar -->
    <div class="question-list-container" id="questionListContainer">
        <div class="question-list-header">
            <div class="question-list-title">Questions</div>
            <button class="close-menu-btn" id="closeMenuBtn"><i class="fas fa-times"></i></button>
        </div>
        <div class="question-list" id="questionList"></div>
    </div>
    
    <!-- Overlay for sidebar -->
    <div class="overlay" id="overlay"></div>
    
    <!-- Theme toggle button -->
    <button class="theme-toggle" id="themeToggle">
        <i class="fas fa-moon"></i>
    </button>
    
    <div class="container my-4">
        <div class="quiz-container" id="quizContainer">
            <div class="quiz-header shadow-sm">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <button class="menu-toggle" id="menuToggle">
                            <i class="fas fa-bars"></i>
                        </button>
                        <h2 class="m-0 fw-bold">Mocks Wallah</h2>
                    </div>
                    <div id="timer" class="timer">
                        <i class="fas fa-clock me-2"></i>
                        <span id="minutes">00</span>:<span id="seconds">00</span> 
                    </div>
                </div>
                <div class="mt-2 mb-2">
                    <h5 class="m-0">{quiz['quiz_name']}</h5>
                </div>
                <div class="progress mt-3">
                  <div id="timeProgress" class="progress-bar progress-bar-striped progress-bar-animated bg-primary" style="width:100%"></div>
                </div>
            </div>
            
            <div class="p-4">
                <div id="questionContainer"></div>
                <div class="d-flex justify-content-center my-4">
                    <button id="submitBtn" class="btn btn-primary btn-lg px-5 py-2 rounded-pill shadow">
                        <i class="fas fa-paper-plane me-2"></i>Submit Test
                    </button>
                </div>
            </div>
            
            <div id="resultContainer" class="result-card p-4">
                <h3 class="text-center fw-bold mb-4">Quiz Results</h3>
                <div class="score-highlight" id="scoreDisplay"></div>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-4 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title fw-bold">Score Summary</h5>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Total Questions:</div>
                                    <div id="totalQuestions" class="fw-bold">{max_marks}</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Correct Answers:</div>
                                    <div id="correctAnswers" class="fw-bold text-success">0</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Incorrect Answers:</div>
                                    <div id="incorrectAnswers" class="fw-bold text-danger">0</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Unattempted:</div>
                                    <div id="unattempted" class="fw-bold text-warning">0</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Negative Marking:</div>
                                    <div id="negativeMarks" class="fw-bold text-danger">-0.00</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-4 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title fw-bold">Performance</h5>
                                <div class="chart-container">
                                    <canvas id="performanceChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-12">
                        <div class="card mb-4 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title fw-bold">Time Analysis</h5>
                                <div class="chart-container">
                                    <canvas id="timeAnalysisChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="d-flex justify-content-center mt-4">
                    <button id="reviewBtn" class="btn btn-primary btn-lg px-5 py-2 rounded-pill shadow">
                        <i class="fas fa-search me-2"></i>View Solution
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Quiz data and state
        const quizData = {{ questions: [{",".join(questions_js)}] }};
        const state = {{
            currentQuestion: 0,
            answers: Array(quizData.questions.length).fill(null),
            startTime: new Date(),
            timePerQuestion: Array(quizData.questions.length).fill(0),
            avgTimePerQuestion: 0,
            totalTime: {total_time},
            negativeMark: {negative_mark},
            submitted: false,
            touchStartX: 0,
            touchEndX: 0,
            inReviewMode: false,
            lastPlayedQuestion: -1,
            darkMode: false
        }};

        // Audio elements
        const clickSound = document.getElementById('clickSound');
        const swipeSound = document.getElementById('swipeSound');
        const correctSound = document.getElementById('correctSound');
        const wrongSound = document.getElementById('wrongSound');

        // DOM elements
        const menuToggle = document.getElementById('menuToggle');
        const closeMenuBtn = document.getElementById('closeMenuBtn');
        const questionListContainer = document.getElementById('questionListContainer');
        const overlay = document.getElementById('overlay');
        const questionList = document.getElementById('questionList');
        const themeToggle = document.getElementById('themeToggle');

        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => {{
            initQuiz();
            initSwipeDetection();
            initSidebar();
            initTheme();
        }});

        function initQuiz() {{
            startTimer();
            createQuestionList();
            renderQuestion(0);
            
            document.getElementById('submitBtn').addEventListener('click', submitQuiz);
            document.getElementById('reviewBtn').addEventListener('click', reviewAnswers);
            
            // Enable keyboard navigation
            document.addEventListener('keydown', (e) => {{
                if (e.key === 'ArrowLeft') navigate(-1);
                if (e.key === 'ArrowRight') navigate(1);
                if (e.key >= '1' && e.key <= quizData.questions.length.toString()) {{
                    if (!state.submitted) updateQuestionTime();
                    renderQuestion(parseInt(e.key) - 1);
                }}
            }});
        }}

        function initSidebar() {{
            menuToggle.addEventListener('click', () => {{
                questionListContainer.classList.add('show');
                overlay.classList.add('show');
                document.body.style.overflow = 'hidden';
            }});

            closeMenuBtn.addEventListener('click', () => {{
                questionListContainer.classList.remove('show');
                overlay.classList.remove('show');
                document.body.style.overflow = '';
            }});

            overlay.addEventListener('click', () => {{
                questionListContainer.classList.remove('show');
                overlay.classList.remove('show');
                document.body.style.overflow = '';
            }});
        }}

        function initTheme() {{
            // Check for saved theme preference or use preferred color scheme
            const savedTheme = localStorage.getItem('quizTheme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {{
                enableDarkMode();
            }}
            
            themeToggle.addEventListener('click', toggleTheme);
            
            // Update theme toggle icon
            updateThemeIcon();
        }}

        function toggleTheme() {{
            if (state.darkMode) {{
                disableDarkMode();
            }} else {{
                enableDarkMode();
            }}
            updateThemeIcon();
        }}

        function enableDarkMode() {{
            document.body.classList.add('dark-mode');
            document.body.setAttribute('data-theme', 'dark');
            state.darkMode = true;
            localStorage.setItem('quizTheme', 'dark');
        }}

        function disableDarkMode() {{
            document.body.classList.remove('dark-mode');
            document.body.setAttribute('data-theme', 'light');
            state.darkMode = false;
            localStorage.setItem('quizTheme', 'light');
        }}

        function updateThemeIcon() {{
            const icon = themeToggle.querySelector('i');
            if (state.darkMode) {{
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }} else {{
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }}
        }}

        function initSwipeDetection() {{
            const container = document.getElementById('quizContainer');
            container.addEventListener('touchstart', (e) => {{ 
                state.touchStartX = e.changedTouches[0].screenX; 
            }}, false);
            
            container.addEventListener('touchend', (e) => {{
                state.touchEndX = e.changedTouches[0].screenX;
                if (Math.abs(state.touchStartX - state.touchEndX) > 50) {{
                    if (!state.inReviewMode) {{
                        swipeSound.currentTime = 0;
                        swipeSound.play();
                    }}
                    navigate(state.touchStartX > state.touchEndX ? 1 : -1);
                }}
            }}, false);
        }}

        function navigate(direction) {{
            const newIndex = state.currentQuestion + direction;
            if (newIndex >= 0 && newIndex < quizData.questions.length) {{
                if (!state.submitted) updateQuestionTime();
                renderQuestion(newIndex);
            }}
        }}

        function startTimer() {{
            const startTime = new Date().getTime();
            const duration = state.totalTime * 1000;
            const endTime = startTime + duration;
            
            updateTimer(duration);
            
            state.timerInterval = setInterval(() => {{
                const now = new Date().getTime();
                const timeLeft = endTime - now;
                
                if (timeLeft <= 0) {{
                    clearInterval(state.timerInterval);
                    updateTimer(0);
                    submitQuiz();
                }} else {{
                    updateTimer(timeLeft);
                    document.getElementById('timeProgress').style.width = `${{(timeLeft / duration) * 100}}%`;
                    
                    if (timeLeft < duration * 0.25) {{
                        document.getElementById('timeProgress').className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
                    }} else if (timeLeft < duration * 0.5) {{
                        document.getElementById('timeProgress').className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
                    }}
                }}
            }}, 1000);
        }}

        function updateTimer(timeLeft) {{
            const minutes = Math.floor(timeLeft / 60000).toString().padStart(2, '0');
            const seconds = Math.floor((timeLeft % 60000) / 1000).toString().padStart(2, '0');
            
            document.getElementById('minutes').textContent = minutes;
            document.getElementById('seconds').textContent = seconds;
            
            if (timeLeft < 60000) document.getElementById('timer').classList.add('text-danger');
        }}

        function createQuestionList() {{
            quizData.questions.forEach((_, idx) => {{
                const item = document.createElement('div');
                item.className = 'question-list-item';
                item.textContent = idx + 1;
                item.dataset.index = idx;
                item.addEventListener('click', () => {{
                    if (!state.submitted) updateQuestionTime();
                    renderQuestion(idx);
                    questionListContainer.classList.remove('show');
                    overlay.classList.remove('show');
                    document.body.style.overflow = '';
                }});
                questionList.appendChild(item);
            }});
        }}

        function renderQuestion(idx) {{
            state.currentQuestion = idx;
            const question = quizData.questions[idx];
            
            let html = `<div class="card question-card shadow-sm">
                <div class="card-body p-4">
                    <h5 class="mcard-title mb-3">Question ${{idx + 1}} of ${{quizData.questions.length}}</h5>`;
            
            if (question.reference) html += `<div class="question-reference">${{question.reference}}</div>`;
            
            html += `<p class="question-text mb-4 fw-bold">${{question.text}}</p><div class="options">`;
            
            question.options.forEach((option, optionIdx) => {{
                let btnClass = 'option-btn w-100';
                if (state.answers[idx] === optionIdx) btnClass += ' selected';
                if (state.submitted) {{
                    if (optionIdx === question.correctIndex) btnClass += ' correct';
                    else if (state.answers[idx] === optionIdx) btnClass += ' incorrect';
                }}
                html += `<button class="${{btnClass}}" data-index="${{optionIdx}}">${{option}}</button>`;
            }});
            
            html += `</div>`;
            
            // Add explanation section
            html += `<div class="explanation mt-3" ${{state.submitted ? '' : 'style="display:none"'}}>
                <h6 class="fw-bold"><i class="fas fa-lightbulb me-2"></i>Explanation</h6>
                ${{question.explanation}}
            </div>`;
            
            // Add analysis panel when in review mode
            if (state.submitted) {{
                const timeSpent = state.timePerQuestion[idx];
                const avgTime = state.avgTimePerQuestion;
                let timeStatus, iconColor;
                
                if (timeSpent < avgTime * 0.7) {{
                    timeStatus = "Fast";
                    iconColor = "#28a745";
                }} else if (timeSpent > avgTime * 1.3) {{
                    timeStatus = "Slow";
                    iconColor = "#dc3545";
                }} else {{
                    timeStatus = "Average";
                    iconColor = "#4361ee";
                }}
                
                const isCorrect = state.answers[idx] === question.correctIndex;
                const isAttempted = state.answers[idx] !== null;
                
                html += `
                <div class="analysis-panel mt-4">
                    <h6 class="fw-bold mb-3"><i class="fas fa-chart-line me-2"></i>Question Analysis</h6>
                    
                    <div class="analysis-item">
                        <div class="analysis-icon" style="background-color:${{isAttempted ? (isCorrect ? '#28a745' : '#dc3545') : '#ffc107'}}">
                            <i class="fas fa-${{isAttempted ? (isCorrect ? 'check' : 'times') : 'question'}}"></i>
                        </div>
                        <div>Status: <strong>${{isAttempted ? (isCorrect ? 'Correct' : 'Incorrect') : 'Unattempted'}}</strong></div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-icon" style="background-color:${{iconColor}}">
                            <i class="fas fa-clock"></i>
                        </div>
                        <div>Time spent: <strong>${{timeSpent.toFixed(1)}} seconds</strong> 
                            <span class="badge-${{timeStatus.toLowerCase()}}">${{timeStatus}}</span>
                        </div>
                    </div>
                    
                    <div class="mb-2">Time compared to average:</div>
                    <div class="time-bar">
                        <div class="time-fill" style="width:${{Math.min(timeSpent/avgTime * 100, 200)}}%"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1">
                        <small>0s</small>
                        <small>${{avgTime.toFixed(1)}}s (avg)</small>
                        <small>${{(avgTime * 2).toFixed(1)}}s+</small>
                    </div>
                </div>`;
            }}
            
            html += `</div></div>`;
            
            document.getElementById('questionContainer').innerHTML = html;
            
            document.querySelectorAll('.option-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    if (!state.submitted) {{
                        clickSound.currentTime = 0;
                        clickSound.play();
                        selectOption(btn.dataset.index);
                    }}
                }});
            }});
            
            updateQuestionList();
            
            // Play correct/wrong sound when in review mode and showing answer
            if (state.inReviewMode && state.lastPlayedQuestion !== idx) {{
                state.lastPlayedQuestion = idx;
                const question = quizData.questions[idx];
                const isCorrect = state.answers[idx] === question.correctIndex;
                const isAttempted = state.answers[idx] !== null;
                
                if (isAttempted) {{
                    setTimeout(() => {{
                        if (isCorrect) {{
                            correctSound.currentTime = 0;
                            correctSound.play();
                        }} else {{
                            wrongSound.currentTime = 0;
                            wrongSound.play();
                        }}
                    }}, 300);
                }}
            }}
        }}

        function updateQuestionList() {{
            document.querySelectorAll('.question-list-item').forEach((item, idx) => {{
                item.className = 'question-list-item';
                
                if (idx === state.currentQuestion) {{
                    item.classList.add('active');
                }}
                
                if (state.answers[idx] !== null) {{
                    if (state.submitted) {{
                        if (state.answers[idx] === quizData.questions[idx].correctIndex) {{
                            item.classList.add('correct');
                        }} else {{
                            item.classList.add('incorrect');
                        }}
                    }}
                }}
            }});
        }}

        function selectOption(optionIdx) {{
            state.answers[state.currentQuestion] = parseInt(optionIdx);
            
            document.querySelectorAll('.option-btn').forEach(opt => opt.classList.remove('selected'));
            document.querySelector(`.option-btn[data-index="${{optionIdx}}"]`).classList.add('selected');
            
            updateQuestionList();
            
            // Auto advance to next question after selection (with delay)
            if (state.currentQuestion < quizData.questions.length - 1) {{
                setTimeout(() => {{
                    updateQuestionTime();
                    renderQuestion(state.currentQuestion + 1);
                }}, 800);
            }}
        }}

        function updateQuestionTime() {{
            const now = new Date();
            state.timePerQuestion[state.currentQuestion] += (now - state.startTime) / 1000;
            state.startTime = now;
        }}

        function submitQuiz() {{
            if (state.submitted) return;
            
            clearInterval(state.timerInterval);
            updateQuestionTime();
            state.submitted = true;
            
            // Calculate average time per question
            let totalTimeSpent = state.timePerQuestion.reduce((acc, time) => acc + time, 0);
            state.avgTimePerQuestion = totalTimeSpent / quizData.questions.length;
            
            const results = {{
                correct: 0,
                incorrect: 0,
                unattempted: 0,
                score: 0,
                negativeMarks: 0
            }};
            
            state.answers.forEach((answer, idx) => {{
                if (answer === null) {{
                    results.unattempted++;
                }} else if (answer === quizData.questions[idx].correctIndex) {{
                    results.correct++;
                    results.score++;
                }} else {{
                    results.incorrect++;
                    results.score -= state.negativeMark;
                    results.negativeMarks += state.negativeMark;
                }}
            }});
            
            // Don't clamp score to zero - show negative scores if they occur
            const percentage = (results.score / quizData.questions.length) * 100;
            
            document.getElementById('scoreDisplay').textContent = `${{results.score.toFixed(2)}} / ${{quizData.questions.length}} (${{percentage.toFixed(1)}}%)`;
            document.getElementById('correctAnswers').textContent = results.correct;
            document.getElementById('incorrectAnswers').textContent = results.incorrect;
            document.getElementById('unattempted').textContent = results.unattempted;
            document.getElementById('negativeMarks').textContent = `-${{results.negativeMarks.toFixed(2)}}`;
            
            document.getElementById('questionContainer').style.display = 'none';
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('resultContainer').style.display = 'block';
            
            createPerformanceChart(results);
            createTimeAnalysisChart();
            
            // Play appropriate sound based on score
            if (percentage >= 70) {{
                createConfetti();
                correctSound.currentTime = 0;
                correctSound.play();
            }} else if (percentage < 50) {{
                wrongSound.currentTime = 0;
                wrongSound.play();
            }}
        }}

        function createPerformanceChart(results) {{
            const ctx = document.getElementById('performanceChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Correct', 'Incorrect', 'Unattempted'],
                    datasets: [{{
                        data: [results.correct, results.incorrect, results.unattempted],
                        backgroundColor: ['#28a745', '#dc3545', '#ffc107']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'bottom' }} }}
                }}
            }});
        }}
        
        function createTimeAnalysisChart() {{
            const ctx = document.getElementById('timeAnalysisChart').getContext('2d');
            const questionLabels = Array.from({{length: quizData.questions.length}}, (_, i) => `Q${{i+1}}`);
            
            // Create data for correct vs incorrect answers
            const correctData = [];
            const incorrectData = [];
            const unattemptedData = [];
            
            state.answers.forEach((answer, idx) => {{
                const time = state.timePerQuestion[idx];
                if (answer === null) {{
                    unattemptedData.push(time);
                    correctData.push(0);
                    incorrectData.push(0);
                }} else if (answer === quizData.questions[idx].correctIndex) {{
                    correctData.push(time);
                    incorrectData.push(0);
                    unattemptedData.push(0);
                }} else {{
                    incorrectData.push(time);
                    correctData.push(0);
                    unattemptedData.push(0);
                }}
            }});
            
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: questionLabels,
                    datasets: [
                        {{
                            label: 'Correct',
                            data: correctData,
                            backgroundColor: '#28a745',
                            borderColor: '#28a745',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Incorrect',
                            data: incorrectData,
                            backgroundColor: '#dc3545',
                            borderColor: '#dc3545',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Unattempted',
                            data: unattemptedData,
                            backgroundColor: '#ffc107',
                            borderColor: '#ffc107',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            stacked: true,
                            title: {{
                                display: true,
                                text: 'Questions'
                            }}
                        }},
                        y: {{
                            stacked: true,
                            title: {{
                                display: true,
                                text: 'Time (seconds)'
                            }}
                        }}
                    }},
                    plugins: {{
                        tooltip: {{
                            callbacks: {{
                                title: function(tooltipItems) {{
                                    return `Question ${{tooltipItems[0].dataIndex + 1}}`;
                                }},
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label && context.parsed.y > 0) {{
                                        label += `: ${{context.parsed.y.toFixed(1)}} seconds`;
                                    }}
                                    return label;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        function reviewAnswers() {{
            state.inReviewMode = true;
            state.lastPlayedQuestion = -1; // Reset last played question
            document.getElementById('questionContainer').style.display = 'block';
            document.getElementById('resultContainer').style.display = 'none';
            document.getElementById('submitBtn').style.display = 'none';
            renderQuestion(0);
        }}
        
        function createConfetti() {{
            const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];
            for (let i = 0; i < 150; i++) {{
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.left = Math.random() * 100 + 'vw';
                
                document.body.appendChild(confetti);
                
                const animation = confetti.animate([
                    {{ transform: 'translateY(0) rotate(0)', opacity: 1 }},
                    {{ transform: `translateY(${{Math.random() * 500 + 500}}px) rotate(${{Math.random() * 360}}deg)`, opacity: 0 }}
                ], {{ duration: Math.random() * 3000 + 2000, easing: 'cubic-bezier(.23,1,.32,1)' }});
                
                animation.onfinish = () => confetti.remove();
            }}
        }}
    </script>
</body>
</html>"""

    # Save and send HTML file
    quiz_name = f"{uuid.uuid4().hex}.html"
    with open(quiz_name, "w", encoding="utf-8") as file:
        file.write(html_content)
        
    with open(quiz_name, "rb") as file:
        await context.bot.send_document(
            chat_id=chat_id,
            document=file,
            caption=f"📝 {quiz['quiz_name']} \n\n<b><i>Powered by Team SPY</i></b>",
            parse_mode=ParseMode.HTML
        )

    # Cleanup
    import os
    os.remove(quiz_name)

async def old_generate_quiz_html(quiz, chat_id, context, ParseMode, type):
    def js_escape(text):
        if not text:
            return ""
        # Convert to string if not already
        text = str(text)
        # Escape special characters
        text = text.replace('\\', '\\\\')  # must be first
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        return text
    
    # Prepare quiz filename
    quiz_name = re.sub(r"[^a-zA-Z0-9_-]", "", unidecode(quiz["quiz_name"]).replace(" ", "_"))[:100] + ".html"
    max_marks = len(quiz["questions"])
    negative_mark = quiz.get("negative_marking", 0)
    if quiz.get("sections"):
        total_time = sum(section.get("timer", 0) for section in quiz["sections"])
    else:
        total_time = (quiz.get("timer") or 60) * len(quiz["questions"])
    
    # Create question data for JavaScript
    questions_js = []
    for idx, q in enumerate(quiz["questions"]):
        options = q["options"].copy()
        correct_option = options[q["correct_option_id"]]
        random.shuffle(options)
        
        questions_js.append(f"""{{
            id: {idx},
            text: "{js_escape(q["question"])}",
            reference: "{js_escape(q.get("reply_text", ""))}",
            options: {json.dumps(options)},  // Using json.dumps for proper escaping
            correctIndex: {options.index(correct_option)},
            explanation: "{js_escape(q.get("explanation", "No explanation provided"))}"
        }}""")
    
    # Build the optimized HTML content with sound effects
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{quiz['quiz_name']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #4361ee;
            --secondary-color: #3a56d4;
            --success-color: #28a745;
            --danger-color: #dc3545;
            --warning-color: #ffc107;
            --light-bg: #ffffff;
            --dark-bg: #1a1a2e;
            --light-text: #333333;
            --dark-text: #f8f9fa;
            --card-bg: #ffffff;
            --card-shadow: 0 15px 40px rgba(0,0,0,0.12);
            --option-btn-bg: #ffffff;
            --option-btn-border: #e6e6e6;
            --explanation-bg: #f8f9fa;
            --analysis-bg: #f8f9fa;
        }}

        [data-theme="dark"] {{
            --primary-color: #7e96ff;
            --secondary-color: #6a7fd4;
            --light-bg: #1a1a2e;
            --dark-bg: #16213e;
            --light-text: #f8f9fa;
            --dark-text: #e2e2e2;
            --card-bg: #16213e;
            --card-shadow: 0 15px 40px rgba(0,0,0,0.3);
            --option-btn-bg: #1f2a4e;
            --option-btn-border: #2a3a6e;
            --explanation-bg: #1f2a4e;
            --analysis-bg: #1f2a4e;
        }}

        body {{
            font-family: 'Poppins', sans-serif;
            background: var(--light-bg);
            color: var(--light-text);
            min-height: 100vh;
            padding-bottom: 50px;
            transition: background 0.3s ease, color 0.3s ease;
        }}

        .dark-mode body {{
            background: var(--dark-bg);
            color: var(--dark-text);
        }}

        .quiz-container {{
            max-width: 800px;
            margin: 20px auto;
            background: var(--card-bg);
            border-radius: 15px;
            box-shadow: var(--card-shadow);
            overflow: hidden;
            animation: fadeIn 0.5s;
            touch-action: pan-y;
            transition: background 0.3s ease, box-shadow 0.3s ease;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px) }}
            to {{ opacity: 1; transform: translateY(0) }}
        }}

        @keyframes slideIn {{
            from {{ transform: translateX(20px); opacity: 0 }}
            to {{ transform: translateX(0); opacity: 1 }}
        }}

        .quiz-header {{
            position: sticky;
            top: 0;
            z-index: 1000;
            background: var(--card-bg);
            padding: 15px 20px;
            border-bottom: 1px solid rgba(0,0,0,0.08);
            transition: background 0.3s ease;
        }}

        .dark-mode .quiz-header {{
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}

        .timer {{
            font-size: 22px;
            font-weight: 600;
            color: var(--primary-color);
        }}

        .question-card {{
            border: none;
            box-shadow: 0 5px 20px rgba(0,0,0,0.06);
            margin-bottom: 25px;
            border-radius: 15px;
            overflow: hidden;
            transition: all 0.4s ease;
            animation: slideIn 0.4s;
            background: var(--card-bg);
        }}

        .dark-mode .question-card {{
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}

        .question-reference {{
            background-color: rgba(67, 97, 238, 0.1);
            border-left: 5px solid var(--primary-color);
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }}

        .option-btn {{
            text-align: left;
            padding: 16px 20px;
            margin-bottom: 12px;
            border-radius: 12px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            border: 1px solid var(--option-btn-border);
            background-color: var(--option-btn-bg);
            color: var(--light-text);
            width: 100%;
        }}

        .dark-mode .option-btn {{
            color: var(--dark-text);
        }}

        .option-btn:hover {{
            background-color: rgba(67, 97, 238, 0.1);
            transform: translateX(5px);
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }}

        .option-btn.selected {{
            background-color: rgba(67, 97, 238, 0.2);
            border-color: var(--primary-color);
            font-weight: 500;
            box-shadow: 0 5px 15px rgba(67,97,238,0.15);
        }}

        .option-btn.correct {{
            background-color: rgba(40, 167, 69, 0.2);
            border-color: var(--success-color);
        }}

        .option-btn.incorrect {{
            background-color: rgba(220, 53, 69, 0.2);
            border-color: var(--danger-color);
        }}

        .progress {{
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            background-color: rgba(0,0,0,0.1);
        }}

        .dark-mode .progress {{
            background-color: rgba(255,255,255,0.1);
        }}

        .progress-bar {{
            transition: width 1s linear;
        }}

        .result-card {{
            display: none;
            animation: fadeIn 0.5s;
        }}

        .score-highlight {{
            font-size: 48px;
            font-weight: 700;
            color: var(--primary-color);
            text-align: center;
            margin: 20px 0;
        }}

        .quiz-pagination {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
            margin: 15px 0;
            padding: 10px 0;
        }}

        .quiz-pagination .page-box {{
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            background-color: rgba(0,0,0,0.05);
            color: var(--light-text);
            border: 1px solid rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            border-radius: 8px;
        }}

        .dark-mode .quiz-pagination .page-box {{
            background-color: rgba(255,255,255,0.05);
            color: var(--dark-text);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .quiz-pagination .page-box.active {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            color: white;
        }}

        .quiz-pagination .page-box:hover {{
            transform: scale(1.1);
        }}

        .quiz-pagination .page-box.correct {{
            background-color: var(--success-color);
            border-color: var(--success-color);
            color: white;
        }}

        .quiz-pagination .page-box.incorrect {{
            background-color: var(--danger-color);
            border-color: var(--danger-color);
            color: white;
        }}

        .explanation {{
            background-color: var(--explanation-bg);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            border-left: 3px solid var(--primary-color);
            transition: background 0.3s ease;
        }}

        .analysis-panel {{
            background-color: var(--analysis-bg);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
            border: 1px solid rgba(0,0,0,0.1);
            transition: background 0.3s ease;
        }}

        .dark-mode .analysis-panel {{
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .analysis-item {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}

        .analysis-icon {{
            width: 24px;
            height: 24px;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            color: white;
        }}

        .btn-primary {{
            background-color: var(--primary-color);
            border-color: var(--primary-color);
            border-radius: 30px;
            padding: 10px 25px;
            transition: all 0.3s ease;
        }}

        .btn-primary:hover {{
            background-color: var(--secondary-color);
            border-color: var(--secondary-color);
            transform: translateY(-3px);
            box-shadow: 0 5px 15px rgba(67,97,238,0.2);
        }}

        .confetti {{
            position: fixed;
            width: 10px;
            height: 10px;
            background-color: #f00;
            position: absolute;
            top: 0;
            z-index: 9999;
        }}

        .chart-container {{
            height: 220px;
        }}

        .time-bar {{
            height: 8px;
            background: rgba(0,0,0,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }}

        .dark-mode .time-bar {{
            background: rgba(255,255,255,0.1);
        }}

        .time-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: 4px;
            transition: width 0.5s;
        }}

        .badge-avg {{
            background-color: rgba(67, 97, 238, 0.2);
            color: var(--primary-color);
            font-weight: 500;
            padding: 5px 10px;
            border-radius: 20px;
        }}

        .badge-fast {{
            background-color: rgba(40, 167, 69, 0.2);
            color: var(--success-color);
            font-weight: 500;
            padding: 5px 10px;
            border-radius: 20px;
        }}

        .badge-slow {{
            background-color: rgba(220, 53, 69, 0.2);
            color: var(--danger-color);
            font-weight: 500;
            padding: 5px 10px;
            border-radius: 20px;
        }}

        /* Mobile-first styles */
        @media (max-width: 768px) {{
            .quiz-container {{
                margin: 10px;
                border-radius: 10px;
            }}

            .quiz-header {{
                padding: 12px 15px;
            }}

            .timer {{
                font-size: 18px;
            }}

            .question-card {{
                margin-bottom: 15px;
                border-radius: 10px;
            }}

            .option-btn {{
                padding: 12px 15px;
                margin-bottom: 8px;
                border-radius: 8px;
            }}

            .score-highlight {{
                font-size: 36px;
            }}

            .quiz-pagination .page-box {{
                width: 28px;
                height: 28px;
                font-size: 14px;
            }}
        }}

        /* Hamburger menu styles */
        .menu-toggle {{
            display: none;
            background: none;
            border: none;
            font-size: 24px;
            color: var(--primary-color);
            cursor: pointer;
            padding: 5px;
            margin-right: 10px;
        }}

        .question-list-container {{
            position: fixed;
            top: 0;
            left: -300px;
            width: 280px;
            height: 100vh;
            background: var(--card-bg);
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            z-index: 1100;
            transition: left 0.3s ease;
            overflow-y: auto;
            padding: 20px;
        }}

        .question-list-container.show {{
            left: 0;
        }}

        .question-list-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }}

        .dark-mode .question-list-header {{
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}

        .question-list-title {{
            font-weight: 600;
            font-size: 18px;
            color: var(--primary-color);
        }}

        .close-menu-btn {{
            background: none;
            border: none;
            font-size: 20px;
            color: var(--light-text);
            cursor: pointer;
        }}

        .dark-mode .close-menu-btn {{
            color: var(--dark-text);
        }}

        .question-list {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}

        .question-list-item {{
            padding: 8px;
            text-align: center;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(0,0,0,0.05);
            border: 1px solid rgba(0,0,0,0.1);
        }}

        .dark-mode .question-list-item {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .question-list-item:hover {{
            background: rgba(67, 97, 238, 0.1);
            transform: scale(1.05);
        }}

        .question-list-item.active {{
            background: var(--primary-color);
            color: white;
        }}

        .question-list-item.correct {{
            background: var(--success-color);
            color: white;
        }}

        .question-list-item.incorrect {{
            background: var(--danger-color);
            color: white;
        }}

        .overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1050;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }}

        .overlay.show {{
            opacity: 1;
            visibility: visible;
        }}

        /* Theme toggle button */
        .theme-toggle {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--primary-color);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 1000;
            border: none;
            font-size: 20px;
        }}

        @media (max-width: 768px) {{
            .menu-toggle {{
                display: block;
            }}

            .question-list {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <!-- Hidden audio elements for sound effects -->
    <audio id="clickSound" src="https://assets.mixkit.co/active_storage/sfx/269/269.wav" preload="auto"></audio>
    <audio id="swipeSound" src="https://assets.mixkit.co/active_storage/sfx/1897/1897.wav" preload="auto"></audio>
    <audio id="correctSound" src="https://assets.mixkit.co/active_storage/sfx/2870/2870.wav" preload="auto"></audio>
    <audio id="wrongSound" src="https://assets.mixkit.co/active_storage/sfx/2964/2964.wav" preload="auto"></audio>
    
    <!-- Question list sidebar -->
    <div class="question-list-container" id="questionListContainer">
        <div class="question-list-header">
            <div class="question-list-title">Questions</div>
            <button class="close-menu-btn" id="closeMenuBtn"><i class="fas fa-times"></i></button>
        </div>
        <div class="question-list" id="questionList"></div>
    </div>
    
    <!-- Overlay for sidebar -->
    <div class="overlay" id="overlay"></div>
    
    <!-- Theme toggle button -->
    <button class="theme-toggle" id="themeToggle">
        <i class="fas fa-moon"></i>
    </button>
    
    <div class="container my-4">
        <div class="quiz-container" id="quizContainer">
            <div class="quiz-header shadow-sm">
                <div class="d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <button class="menu-toggle" id="menuToggle">
                            <i class="fas fa-bars"></i>
                        </button>
                        <h2 class="m-0 fw-bold">Mock Test</h2>
                    </div>
                    <div id="timer" class="timer">
                        <i class="fas fa-clock me-2"></i>
                        <span id="minutes">00</span>:<span id="seconds">00</span>
                    </div>
                </div>
                <div class="mt-2 mb-2">
                    <h5 class="m-0">{quiz['quiz_name']}</h5>
                </div>
                <div class="progress mt-3">
                  <div id="timeProgress" class="progress-bar progress-bar-striped progress-bar-animated bg-primary" style="width:100%"></div>
                </div>
            </div>
            
            <div class="p-4">
                <div id="questionContainer"></div>
                <div class="quiz-pagination" id="questionNav"></div>
                <div class="d-flex justify-content-center my-4">
                    <button id="submitBtn" class="btn btn-primary btn-lg px-5 py-2 rounded-pill shadow">
                        <i class="fas fa-paper-plane me-2"></i>Submit Test
                    </button>
                </div>
            </div>
            
            <div id="resultContainer" class="result-card p-4">
                <h3 class="text-center fw-bold mb-4">Quiz Results</h3>
                <div class="score-highlight" id="scoreDisplay"></div>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-4 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title fw-bold">Score Summary</h5>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Total Questions:</div>
                                    <div id="totalQuestions" class="fw-bold">{max_marks}</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Correct Answers:</div>
                                    <div id="correctAnswers" class="fw-bold text-success">0</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Incorrect Answers:</div>
                                    <div id="incorrectAnswers" class="fw-bold text-danger">0</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Unattempted:</div>
                                    <div id="unattempted" class="fw-bold text-warning">0</div>
                                </div>
                                <div class="d-flex justify-content-between mb-3">
                                    <div>Negative Marking:</div>
                                    <div id="negativeMarks" class="fw-bold text-danger">-0.00</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-4 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title fw-bold">Performance</h5>
                                <div class="chart-container">
                                    <canvas id="performanceChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-12">
                        <div class="card mb-4 shadow-sm">
                            <div class="card-body">
                                <h5 class="card-title fw-bold">Time Analysis</h5>
                                <div class="chart-container">
                                    <canvas id="timeAnalysisChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="d-flex justify-content-center mt-4">
                    <button id="reviewBtn" class="btn btn-primary btn-lg px-5 py-2 rounded-pill shadow">
                        <i class="fas fa-search me-2"></i>View Solution
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Quiz data and state
        const quizData = {{ questions: [{",".join(questions_js)}] }};
        const state = {{
            currentQuestion: 0,
            answers: Array(quizData.questions.length).fill(null),
            startTime: new Date(),
            timePerQuestion: Array(quizData.questions.length).fill(0),
            avgTimePerQuestion: 0,
            totalTime: {total_time},
            negativeMark: {negative_mark},
            submitted: false,
            touchStartX: 0,
            touchEndX: 0,
            inReviewMode: false,
            lastPlayedQuestion: -1,
            darkMode: false
        }};

        // Audio elements
        const clickSound = document.getElementById('clickSound');
        const swipeSound = document.getElementById('swipeSound');
        const correctSound = document.getElementById('correctSound');
        const wrongSound = document.getElementById('wrongSound');

        // DOM elements
        const menuToggle = document.getElementById('menuToggle');
        const closeMenuBtn = document.getElementById('closeMenuBtn');
        const questionListContainer = document.getElementById('questionListContainer');
        const overlay = document.getElementById('overlay');
        const questionList = document.getElementById('questionList');
        const themeToggle = document.getElementById('themeToggle');

        // Initialize on load
        document.addEventListener('DOMContentLoaded', () => {{
            initQuiz();
            initSwipeDetection();
            initSidebar();
            initTheme();
        }});

        function initQuiz() {{
            startTimer();
            createNumberedNav();
            createQuestionList();
            renderQuestion(0);
            
            document.getElementById('submitBtn').addEventListener('click', submitQuiz);
            document.getElementById('reviewBtn').addEventListener('click', reviewAnswers);
            
            // Enable keyboard navigation
            document.addEventListener('keydown', (e) => {{
                if (e.key === 'ArrowLeft') navigate(-1);
                if (e.key === 'ArrowRight') navigate(1);
                if (e.key >= '1' && e.key <= quizData.questions.length.toString()) {{
                    if (!state.submitted) updateQuestionTime();
                    renderQuestion(parseInt(e.key) - 1);
                }}
            }});
        }}

        function initSidebar() {{
            menuToggle.addEventListener('click', () => {{
                questionListContainer.classList.add('show');
                overlay.classList.add('show');
                document.body.style.overflow = 'hidden';
            }});

            closeMenuBtn.addEventListener('click', () => {{
                questionListContainer.classList.remove('show');
                overlay.classList.remove('show');
                document.body.style.overflow = '';
            }});

            overlay.addEventListener('click', () => {{
                questionListContainer.classList.remove('show');
                overlay.classList.remove('show');
                document.body.style.overflow = '';
            }});
        }}

        function initTheme() {{
            // Check for saved theme preference or use preferred color scheme
            const savedTheme = localStorage.getItem('quizTheme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {{
                enableDarkMode();
            }}
            
            themeToggle.addEventListener('click', toggleTheme);
            
            // Update theme toggle icon
            updateThemeIcon();
        }}

        function toggleTheme() {{
            if (state.darkMode) {{
                disableDarkMode();
            }} else {{
                enableDarkMode();
            }}
            updateThemeIcon();
        }}

        function enableDarkMode() {{
            document.body.classList.add('dark-mode');
            document.body.setAttribute('data-theme', 'dark');
            state.darkMode = true;
            localStorage.setItem('quizTheme', 'dark');
        }}

        function disableDarkMode() {{
            document.body.classList.remove('dark-mode');
            document.body.setAttribute('data-theme', 'light');
            state.darkMode = false;
            localStorage.setItem('quizTheme', 'light');
        }}

        function updateThemeIcon() {{
            const icon = themeToggle.querySelector('i');
            if (state.darkMode) {{
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }} else {{
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }}
        }}

        function initSwipeDetection() {{
            const container = document.getElementById('quizContainer');
            container.addEventListener('touchstart', (e) => {{ 
                state.touchStartX = e.changedTouches[0].screenX; 
            }}, false);
            
            container.addEventListener('touchend', (e) => {{
                state.touchEndX = e.changedTouches[0].screenX;
                if (Math.abs(state.touchStartX - state.touchEndX) > 50) {{
                    if (!state.inReviewMode) {{
                        swipeSound.currentTime = 0;
                        swipeSound.play();
                    }}
                    navigate(state.touchStartX > state.touchEndX ? 1 : -1);
                }}
            }}, false);
        }}

        function navigate(direction) {{
            const newIndex = state.currentQuestion + direction;
            if (newIndex >= 0 && newIndex < quizData.questions.length) {{
                if (!state.submitted) updateQuestionTime();
                renderQuestion(newIndex);
            }}
        }}

        function startTimer() {{
            const startTime = new Date().getTime();
            const duration = state.totalTime * 1000;
            const endTime = startTime + duration;
            
            updateTimer(duration);
            
            state.timerInterval = setInterval(() => {{
                const now = new Date().getTime();
                const timeLeft = endTime - now;
                
                if (timeLeft <= 0) {{
                    clearInterval(state.timerInterval);
                    updateTimer(0);
                    submitQuiz();
                }} else {{
                    updateTimer(timeLeft);
                    document.getElementById('timeProgress').style.width = `${{(timeLeft / duration) * 100}}%`;
                    
                    if (timeLeft < duration * 0.25) {{
                        document.getElementById('timeProgress').className = 'progress-bar progress-bar-striped progress-bar-animated bg-danger';
                    }} else if (timeLeft < duration * 0.5) {{
                        document.getElementById('timeProgress').className = 'progress-bar progress-bar-striped progress-bar-animated bg-warning';
                    }}
                }}
            }}, 1000);
        }}

        function updateTimer(timeLeft) {{
            const minutes = Math.floor(timeLeft / 60000).toString().padStart(2, '0');
            const seconds = Math.floor((timeLeft % 60000) / 1000).toString().padStart(2, '0');
            
            document.getElementById('minutes').textContent = minutes;
            document.getElementById('seconds').textContent = seconds;
            
            if (timeLeft < 60000) document.getElementById('timer').classList.add('text-danger');
        }}

        function createNumberedNav() {{
            const nav = document.getElementById('questionNav');
            quizData.questions.forEach((_, idx) => {{
                const box = document.createElement('div');
                box.className = 'page-box';
                box.textContent = idx + 1;
                box.dataset.index = idx;
                box.addEventListener('click', () => {{
                    if (!state.submitted) updateQuestionTime();
                    renderQuestion(idx);
                }});
                nav.appendChild(box);
            }});
        }}

        function createQuestionList() {{
            quizData.questions.forEach((_, idx) => {{
                const item = document.createElement('div');
                item.className = 'question-list-item';
                item.textContent = idx + 1;
                item.dataset.index = idx;
                item.addEventListener('click', () => {{
                    if (!state.submitted) updateQuestionTime();
                    renderQuestion(idx);
                    questionListContainer.classList.remove('show');
                    overlay.classList.remove('show');
                    document.body.style.overflow = '';
                }});
                questionList.appendChild(item);
            }});
        }}

        function renderQuestion(idx) {{
            state.currentQuestion = idx;
            const question = quizData.questions[idx];
            
            let html = `<div class="card question-card shadow-sm">
                <div class="card-body p-4">
                    <h5 class="card-title mb-3">Question ${{idx + 1}} of ${{quizData.questions.length}}</h5>`;
            
            if (question.reference) html += `<div class="question-reference">${{question.reference}}</div>`;
            
            html += `<p class="question-text mb-4 fw-bold">${{question.text}}</p><div class="options">`;
            
            question.options.forEach((option, optionIdx) => {{
                let btnClass = 'option-btn w-100';
                if (state.answers[idx] === optionIdx) btnClass += ' selected';
                if (state.submitted) {{
                    if (optionIdx === question.correctIndex) btnClass += ' correct';
                    else if (state.answers[idx] === optionIdx) btnClass += ' incorrect';
                }}
                html += `<button class="${{btnClass}}" data-index="${{optionIdx}}">${{option}}</button>`;
            }});
            
            html += `</div>`;
            
            // Add explanation section
            html += `<div class="explanation mt-3" ${{state.submitted ? '' : 'style="display:none"'}}>
                <h6 class="fw-bold"><i class="fas fa-lightbulb me-2"></i>Explanation</h6>
                ${{question.explanation}}
            </div>`;
            
            // Add analysis panel when in review mode
            if (state.submitted) {{
                const timeSpent = state.timePerQuestion[idx];
                const avgTime = state.avgTimePerQuestion;
                let timeStatus, iconColor;
                
                if (timeSpent < avgTime * 0.7) {{
                    timeStatus = "Fast";
                    iconColor = "#28a745";
                }} else if (timeSpent > avgTime * 1.3) {{
                    timeStatus = "Slow";
                    iconColor = "#dc3545";
                }} else {{
                    timeStatus = "Average";
                    iconColor = "#4361ee";
                }}
                
                const isCorrect = state.answers[idx] === question.correctIndex;
                const isAttempted = state.answers[idx] !== null;
                
                html += `
                <div class="analysis-panel mt-4">
                    <h6 class="fw-bold mb-3"><i class="fas fa-chart-line me-2"></i>Question Analysis</h6>
                    
                    <div class="analysis-item">
                        <div class="analysis-icon" style="background-color:${{isAttempted ? (isCorrect ? '#28a745' : '#dc3545') : '#ffc107'}}">
                            <i class="fas fa-${{isAttempted ? (isCorrect ? 'check' : 'times') : 'question'}}"></i>
                        </div>
                        <div>Status: <strong>${{isAttempted ? (isCorrect ? 'Correct' : 'Incorrect') : 'Unattempted'}}</strong></div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-icon" style="background-color:${{iconColor}}">
                            <i class="fas fa-clock"></i>
                        </div>
                        <div>Time spent: <strong>${{timeSpent.toFixed(1)}} seconds</strong> 
                            <span class="badge-${{timeStatus.toLowerCase()}}">${{timeStatus}}</span>
                        </div>
                    </div>
                    
                    <div class="mb-2">Time compared to average:</div>
                    <div class="time-bar">
                        <div class="time-fill" style="width:${{Math.min(timeSpent/avgTime * 100, 200)}}%"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-1">
                        <small>0s</small>
                        <small>${{avgTime.toFixed(1)}}s (avg)</small>
                        <small>${{(avgTime * 2).toFixed(1)}}s+</small>
                    </div>
                </div>`;
            }}
            
            html += `</div></div>`;
            
            document.getElementById('questionContainer').innerHTML = html;
            
            document.querySelectorAll('.option-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    if (!state.submitted) {{
                        clickSound.currentTime = 0;
                        clickSound.play();
                        selectOption(btn.dataset.index);
                    }}
                }});
            }});
            
            updateQuestionNav();
            updateQuestionList();
            
            // Play correct/wrong sound when in review mode and showing answer
            if (state.inReviewMode && state.lastPlayedQuestion !== idx) {{
                state.lastPlayedQuestion = idx;
                const question = quizData.questions[idx];
                const isCorrect = state.answers[idx] === question.correctIndex;
                const isAttempted = state.answers[idx] !== null;
                
                if (isAttempted) {{
                    setTimeout(() => {{
                        if (isCorrect) {{
                            correctSound.currentTime = 0;
                            correctSound.play();
                        }} else {{
                            wrongSound.currentTime = 0;
                            wrongSound.play();
                        }}
                    }}, 300);
                }}
            }}
        }}

        function updateQuestionNav() {{
            document.querySelectorAll('#questionNav .page-box').forEach((box, idx) => {{
                box.className = 'page-box';
                
                if (idx === state.currentQuestion) {{
                    box.classList.add('active');
                }}
                
                if (state.answers[idx] !== null) {{
                    if (state.submitted) {{
                        if (state.answers[idx] === quizData.questions[idx].correctIndex) {{
                            box.classList.add('correct');
                        }} else {{
                            box.classList.add('incorrect');
                        }}
                    }}
                }}
            }});
        }}

        function updateQuestionList() {{
            document.querySelectorAll('.question-list-item').forEach((item, idx) => {{
                item.className = 'question-list-item';
                
                if (idx === state.currentQuestion) {{
                    item.classList.add('active');
                }}
                
                if (state.answers[idx] !== null) {{
                    if (state.submitted) {{
                        if (state.answers[idx] === quizData.questions[idx].correctIndex) {{
                            item.classList.add('correct');
                        }} else {{
                            item.classList.add('incorrect');
                        }}
                    }}
                }}
            }});
        }}

        function selectOption(optionIdx) {{
            state.answers[state.currentQuestion] = parseInt(optionIdx);
            
            document.querySelectorAll('.option-btn').forEach(opt => opt.classList.remove('selected'));
            document.querySelector(`.option-btn[data-index="${{optionIdx}}"]`).classList.add('selected');
            
            updateQuestionNav();
            updateQuestionList();
            
            // Auto advance to next question after selection (with delay)
            if (state.currentQuestion < quizData.questions.length - 1) {{
                setTimeout(() => {{
                    updateQuestionTime();
                    renderQuestion(state.currentQuestion + 1);
                }}, 800);
            }}
        }}

        function updateQuestionTime() {{
            const now = new Date();
            state.timePerQuestion[state.currentQuestion] += (now - state.startTime) / 1000;
            state.startTime = now;
        }}

        function submitQuiz() {{
            if (state.submitted) return;
            
            clearInterval(state.timerInterval);
            updateQuestionTime();
            state.submitted = true;
            
            // Calculate average time per question
            let totalTimeSpent = state.timePerQuestion.reduce((acc, time) => acc + time, 0);
            state.avgTimePerQuestion = totalTimeSpent / quizData.questions.length;
            
            const results = {{
                correct: 0,
                incorrect: 0,
                unattempted: 0,
                score: 0,
                negativeMarks: 0
            }};
            
            state.answers.forEach((answer, idx) => {{
                if (answer === null) {{
                    results.unattempted++;
                }} else if (answer === quizData.questions[idx].correctIndex) {{
                    results.correct++;
                    results.score++;
                }} else {{
                    results.incorrect++;
                    results.score -= state.negativeMark;
                    results.negativeMarks += state.negativeMark;
                }}
            }});
            
            // Don't clamp score to zero - show negative scores if they occur
            const percentage = (results.score / quizData.questions.length) * 100;
            
            document.getElementById('scoreDisplay').textContent = `${{results.score.toFixed(2)}} / ${{quizData.questions.length}} (${{percentage.toFixed(1)}}%)`;
            document.getElementById('correctAnswers').textContent = results.correct;
            document.getElementById('incorrectAnswers').textContent = results.incorrect;
            document.getElementById('unattempted').textContent = results.unattempted;
            document.getElementById('negativeMarks').textContent = `-${{results.negativeMarks.toFixed(2)}}`;
            
            document.getElementById('questionContainer').style.display = 'none';
            document.getElementById('questionNav').style.display = 'none';
            document.getElementById('submitBtn').style.display = 'none';
            document.getElementById('resultContainer').style.display = 'block';
            
            createPerformanceChart(results);
            createTimeAnalysisChart();
            
            // Play appropriate sound based on score
            if (percentage >= 70) {{
                createConfetti();
                correctSound.currentTime = 0;
                correctSound.play();
            }} else if (percentage < 50) {{
                wrongSound.currentTime = 0;
                wrongSound.play();
            }}
        }}

        function createPerformanceChart(results) {{
            const ctx = document.getElementById('performanceChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Correct', 'Incorrect', 'Unattempted'],
                    datasets: [{{
                        data: [results.correct, results.incorrect, results.unattempted],
                        backgroundColor: ['#28a745', '#dc3545', '#ffc107']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ position: 'bottom' }} }}
                }}
            }});
        }}
        
        function createTimeAnalysisChart() {{
            const ctx = document.getElementById('timeAnalysisChart').getContext('2d');
            const questionLabels = Array.from({{length: quizData.questions.length}}, (_, i) => `Q${{i+1}}`);
            
            // Create data for correct vs incorrect answers
            const correctData = [];
            const incorrectData = [];
            const unattemptedData = [];
            
            state.answers.forEach((answer, idx) => {{
                const time = state.timePerQuestion[idx];
                if (answer === null) {{
                    unattemptedData.push(time);
                    correctData.push(0);
                    incorrectData.push(0);
                }} else if (answer === quizData.questions[idx].correctIndex) {{
                    correctData.push(time);
                    incorrectData.push(0);
                    unattemptedData.push(0);
                }} else {{
                    incorrectData.push(time);
                    correctData.push(0);
                    unattemptedData.push(0);
                }}
            }});
            
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: questionLabels,
                    datasets: [
                        {{
                            label: 'Correct',
                            data: correctData,
                            backgroundColor: '#28a745',
                            borderColor: '#28a745',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Incorrect',
                            data: incorrectData,
                            backgroundColor: '#dc3545',
                            borderColor: '#dc3545',
                            borderWidth: 1
                        }},
                        {{
                            label: 'Unattempted',
                            data: unattemptedData,
                            backgroundColor: '#ffc107',
                            borderColor: '#ffc107',
                            borderWidth: 1
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            stacked: true,
                            title: {{
                                display: true,
                                text: 'Questions'
                            }}
                        }},
                        y: {{
                            stacked: true,
                            title: {{
                                display: true,
                                text: 'Time (seconds)'
                            }}
                        }}
                    }},
                    plugins: {{
                        tooltip: {{
                            callbacks: {{
                                title: function(tooltipItems) {{
                                    return `Question ${{tooltipItems[0].dataIndex + 1}}`;
                                }},
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label && context.parsed.y > 0) {{
                                        label += `: ${{context.parsed.y.toFixed(1)}} seconds`;
                                    }}
                                    return label;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        function reviewAnswers() {{
            state.inReviewMode = true;
            state.lastPlayedQuestion = -1; // Reset last played question
            document.getElementById('questionContainer').style.display = 'block';
            document.getElementById('questionNav').style.display = 'flex';
            document.getElementById('resultContainer').style.display = 'none';
            document.getElementById('submitBtn').style.display = 'none';
            renderQuestion(0);
        }}
        
        function createConfetti() {{
            const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];
            for (let i = 0; i < 150; i++) {{
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.left = Math.random() * 100 + 'vw';
                
                document.body.appendChild(confetti);
                
                const animation = confetti.animate([
                    {{ transform: 'translateY(0) rotate(0)', opacity: 1 }},
                    {{ transform: `translateY(${{Math.random() * 500 + 500}}px) rotate(${{Math.random() * 360}}deg)`, opacity: 0 }}
                ], {{ duration: Math.random() * 3000 + 2000, easing: 'cubic-bezier(.23,1,.32,1)' }});
                
                animation.onfinish = () => confetti.remove();
            }}
        }}
    </script>
</body>
</html>"""

    # Save and send HTML file
    quiz_name = f"{uuid.uuid4().hex}.html"
    with open(quiz_name, "w", encoding="utf-8") as file:
        file.write(html_content)
        
    with open(quiz_name, "rb") as file:
        await context.bot.send_document(
            chat_id=chat_id,
            document=file,
            caption=f"📝 {quiz['quiz_name']} \n\n<b><i>Powered by Team SPY</i></b>",
            parse_mode=ParseMode.HTML
        )

    # Cleanup
    import os
    os.remove(quiz_name)


async def generate_analysis_html(quiz_results, quiz_data):
    """Generate HTML analyzing a single quiz result with detailed metrics and visualizations"""
    # Base HTML structure with responsive design and Chart.js
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quiz Performance Analysis</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.1/chart.min.js"></script>
        <style>
            :root {
                --primary: #4361ee;
                --secondary: #3f37c9;
                --success: #4cc9f0;
                --danger: #f72585;
                --warning: #f8961e;
                --info: #4895ef;
                --light: #f8f9fa;
                --dark: #212529;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f5f7fa;
                margin: 0;
                padding: 0;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: linear-gradient(135deg, var(--primary), var(--secondary));
                color: white;
                padding: 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .header h1 {
                margin: 0;
                font-size: 28px;
            }
            
            .header p {
                margin: 10px 0 0;
                opacity: 0.9;
            }
            
            .card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                padding: 25px;
                margin-bottom: 25px;
                transition: transform 0.3s ease;
            }
            
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.1);
            }
            
            .card h2 {
                margin-top: 0;
                color: var(--primary);
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }
            
            .chart-container {
                position: relative;
                height: 300px;
                margin: 20px 0;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            
            .stat-card {
                background: var(--light);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                border-left: 4px solid var(--primary);
            }
            
            .gold {
                border-left-color: #FFD700;
                background-color: rgba(255, 215, 0, 0.1);
            }
            
            .silver {
                border-left-color: #C0C0C0;
                background-color: rgba(192, 192, 192, 0.1);
            }
            
            .bronze {
                border-left-color: #CD7F32;
                background-color: rgba(205, 127, 50, 0.1);
            }
            
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                margin: 10px 0;
                color: var(--dark);
            }
            
            .stat-label {
                font-size: 14px;
                color: #666;
            }
            
            .stat-name {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .question {
                border-left: 4px solid var(--info);
                padding: 15px;
                margin-bottom: 20px;
                background: rgba(72, 149, 239, 0.05);
                border-radius: 0 8px 8px 0;
            }
            
            .question-text {
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .metrics {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .metric {
                flex: 1;
                min-width: 120px;
                background: white;
                padding: 10px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            .metric-value {
                font-size: 18px;
                font-weight: bold;
            }
            
            .metric-label {
                font-size: 12px;
                color: #666;
            }
            
            .leaderboard {
                width: 100%;
                min-width: 600px;  /* Minimum width before scrolling kicks in */
                border-collapse: collapse;
                margin: 20px 0;
            }
            
            .leaderboard th, .leaderboard td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            
            .leaderboard th {
                background-color: var(--light);
                font-weight: bold;
                color: var(--primary);
            }
            
            .leaderboard tr:hover {
                background-color: rgba(67, 97, 238, 0.05);
            }
            
            .rank {
                width: 60px;
                text-align: center;
                font-weight: bold;
            }
            
            .gold-rank {
                color: #FFD700;
            }
            
            .silver-rank {
                color: #808080;
            }
            
            .bronze-rank {
                color: #CD7F32;
            }
            
            .easy {
                background-color: rgba(40, 167, 69, 0.1);
            }
            
            .medium {
                background-color: rgba(255, 193, 7, 0.1);
            }
            
            .hard {
                background-color: rgba(220, 53, 69, 0.1);
            }
            
            .badge {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            
            .easy-badge {
                background-color: rgba(40, 167, 69, 0.2);
                color: #28a745;
            }
            
            .medium-badge {
                background-color: rgba(255, 193, 7, 0.2);
                color: #d39e00;
            }
            
            .hard-badge {
                background-color: rgba(220, 53, 69, 0.2);
                color: #dc3545;
            }
            
            .options-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }
            
            .option {
                display: flex;
                align-items: center;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ddd;
            }
            
            .option-marker {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 12px;
                color: white;
            }
            
            .correct-option {
                background-color: rgba(40, 167, 69, 0.1);
                border-color: #28a745;
            }
            
            .correct-marker {
                background-color: #28a745;
            }
            
            .incorrect-marker {
                background-color: #dc3545;
            }
            
            .popular-marker {
                background-color: #ffc107;
            }

            @media (max-width: 768px) {
                .container {
                    padding: 15px;
                }
                
                .header {
                    padding: 20px;
                }
                
                .card {
                    padding: 15px;
                }
                
                .chart-container {
                    height: 250px;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr 1fr;
                }
                
                .metrics {
                    flex-direction: column;
                }
                
                .metric {
                    width: 100%;
                }
                
                .options-grid {
                    grid-template-columns: 1fr;
                }
                
                .leaderboard {
                    min-width: 100%;
                    }
                    
                .leaderboard th,
                 
                .leaderboard td {
                    padding: 8px;
                    font-size: 14px;
                    }
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Quiz Performance Analysis</h1>
                <p>{quiz_name}</p>
            </div>
    """
    
    # Fill in quiz name
    try:
        html = html.replace("{quiz_name}", quiz_data.get("quiz_name", "Unnamed Quiz"))
    except Exception as e:
        print(f"Error formatting HTML: {e}")
        return None
    
    # Add top performers section
    if quiz_results["participants"]:
        # Sort participants by score
        participants = sorted(quiz_results["participants"], key=lambda x: (x["score"], -x["total_time"]), reverse=True)
        
        # Get top performers
        top_performers = participants[:3] if len(participants) >= 3 else participants
        
        # Top performers cards
        html += """
        <div class="card">
            <h2>Top Performers</h2>
            <div class="stats-grid">
        """
        
        # Add medals for top 3
        medal_classes = ["gold", "silver", "bronze"]
        medal_icons = ["🥇", "🥈", "🥉"]
        
        for i, performer in enumerate(top_performers):
            percentage = (performer["correct"] / len(quiz_data["questions"])) * 100
            minutes, seconds = divmod(performer["total_time"], 60)
            time_str = f"{int(minutes)}m {int(seconds)}s"
            
            html += f"""
            <div class="stat-card {medal_classes[i]}">
                <div class="stat-label">{medal_icons[i]} {i+1}st Place</div>
                <div class="stat-name">{performer["name"]}</div>
                <div class="stat-value">{performer["score"]:.1f}</div>
                <div class="stat-label">Score | {percentage:.1f}% | {time_str}</div>
            </div>
            """
        
        html += """
            </div>
            <div class="chart-container">
                <canvas id="topPerformersChart"></canvas>
            </div>
        </div>
        """
        
        # Class average metrics
        total_participants = len(participants)
        avg_score = sum(p["score"] for p in participants) / total_participants
        avg_correct = sum(p["correct"] for p in participants) / total_participants
        avg_wrong = sum(p["wrong"] for p in participants) / total_participants
        avg_score_percentage = (avg_score / len(quiz_data["questions"])) * 100
        
        html += f"""
        <div class="card">
            <h2>Class Performance</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Participants</div>
                    <div class="stat-value">{total_participants}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Average Score</div>
                    <div class="stat-value">{avg_score:.1f}</div>
                    <div class="stat-label">{avg_score_percentage:.1f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Average Correct</div>
                    <div class="stat-value">{avg_correct:.1f}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Average Wrong</div>
                    <div class="stat-value">{avg_wrong:.1f}</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="scoreDistributionChart"></canvas>
            </div>
        </div>
        """
        
        # Question-by-question analysis
        html += """
        <div class="card">
            <h2>Question Analysis</h2>
            <div class="chart-container">
                <canvas id="questionChart"></canvas>
            </div>
        """
        
        # Process question data
        question_labels = []
        correct_percentages = []
        difficulty_levels = []
        
        for i, question in enumerate(quiz_data["questions"]):
            correct_count = 0
            total_answers = 0
            option_counts = {}
            
            for opt_idx in range(len(question["options"])):
                option_counts[opt_idx] = 0
            
            for user in participants:
                if f"q{i}" in user.get("answers", {}):
                    total_answers += 1
                    selected_option = user["answers"][f"q{i}"]
                    option_counts[selected_option] = option_counts.get(selected_option, 0) + 1
                    
                    if selected_option == question["correct_option_id"]:
                        correct_count += 1
            
            correct_percentage = (correct_count / total_answers * 100) if total_answers > 0 else 0
            correct_percentages.append(correct_percentage)
            question_labels.append(f"Q{i+1}")
            
            if correct_percentage >= 75:
                difficulty = "easy"
                difficulty_label = "Easy"
                difficulty_badge = "easy-badge"
            elif correct_percentage >= 40:
                difficulty = "medium"
                difficulty_label = "Medium"
                difficulty_badge = "medium-badge"
            else:
                difficulty = "hard"
                difficulty_label = "Hard"
                difficulty_badge = "hard-badge"
            
            difficulty_levels.append(difficulty)
            
            wrong_options = {opt: count for opt, count in option_counts.items() 
                            if opt != question["correct_option_id"]}
            most_popular_wrong = max(wrong_options.items(), key=lambda x: x[1]) if wrong_options else (None, 0)
            
            html += f"""
            <div class="question {difficulty}">
                <div class="question-text">
                    Q{i+1}: {question["question"]} 
                    <span class="badge {difficulty_badge}">{difficulty_label}</span>
                </div>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{correct_percentage:.1f}%</div>
                        <div class="metric-label">Correct Answers</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{correct_count}/{total_answers}</div>
                        <div class="metric-label">Students</div>
                    </div>
            """
            
            if most_popular_wrong[0] is not None:
                html += f"""
                    <div class="metric">
                        <div class="metric-value">{most_popular_wrong[1]}</div>
                        <div class="metric-label">Chose Option {most_popular_wrong[0] + 1}</div>
                    </div>
                """
            
            html += """
                </div>
                <div class="options-grid">
            """
            
            for opt_idx, option_text in enumerate(question["options"]):
                option_class = "correct-option" if opt_idx == question["correct_option_id"] else ""
                marker_class = "correct-marker" if opt_idx == question["correct_option_id"] else "incorrect-marker"
                
                if opt_idx == most_popular_wrong[0]:
                    marker_class = "popular-marker"
                
                option_percentage = (option_counts.get(opt_idx, 0) / total_answers * 100) if total_answers > 0 else 0
                
                html += f"""
                <div class="option {option_class}">
                    <div class="option-marker {marker_class}">{opt_idx + 1}</div>
                    <div>{option_text} ({option_percentage:.1f}%)</div>
                </div>
                """
            
            html += """
                </div>
            </div>
            """
        
        # Full leaderboard
        html += """
        </div>
        
        <div class="card">
            <h2>Full Leaderboard</h2>
            <div style="overflow-x: auto;">
                <table class="leaderboard">
                    <thead>
                        <tr>
                            <th class="rank">Rank</th>
                            <th>Name</th>
                            <th>Score</th>
                            <th>Correct</th>
                            <th>Wrong</th>
                            <th>Time</th>
                            <th>Accuracy</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for i, user in enumerate(participants):
            # Calculate percentage and accuracy
            percentage = (user["correct"] / len(quiz_data["questions"])) * 100
            total_attempted = user["correct"] + user["wrong"]
            accuracy = (user["correct"] / total_attempted * 100) if total_attempted > 0 else 0
            
            # Format time
            minutes, seconds = divmod(user["total_time"], 60)
            time_str = f"{int(minutes)}m {int(seconds)}s"
            
            # Determine rank class
            rank_class = ""
            if i == 0:
                rank_class = "gold-rank"
            elif i == 1:
                rank_class = "silver-rank"
            elif i == 2:
                rank_class = "bronze-rank"
            
            html += f"""
                    <tr>
                        <td class="rank {rank_class}">{i+1}</td>
                        <td>{user["name"]}</td>
                        <td>{user["score"]:.1f}</td>
                        <td>{user["correct"]}</td>
                        <td>{user["wrong"]}</td>
                        <td>{time_str}</td>
                        <td>{accuracy:.1f}%</td>
                    </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
        """
        
        # Prepare chart data
        score_data = [p["score"] for p in participants]
        score_distribution_data = [
            len([s for s in score_data if s/len(quiz_data["questions"])*100 <= 20]),
            len([s for s in score_data if 20 < s/len(quiz_data["questions"])*100 <= 40]),
            len([s for s in score_data if 40 < s/len(quiz_data["questions"])*100 <= 60]),
            len([s for s in score_data if 60 < s/len(quiz_data["questions"])*100 <= 80]),
            len([s for s in score_data if s/len(quiz_data["questions"])*100 > 80])
        ]
        
        # Add all JavaScript charts in one script block
        html += """
        <script>
        // Set Chart.js defaults
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.color = '#666';
        
        // Top performers chart
        const topPerformersCtx = document.getElementById('topPerformersChart').getContext('2d');
        const topPerformersChart = new Chart(topPerformersCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps([p["name"] for p in top_performers]) + """,
                datasets: [
                    {
                        label: 'Correct',
                        data: """ + json.dumps([p["correct"] for p in top_performers]) + """,
                        backgroundColor: 'rgba(40, 167, 69, 0.7)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Wrong',
                        data: """ + json.dumps([p["wrong"] for p in top_performers]) + """,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Score',
                        data: """ + json.dumps([p["score"] for p in top_performers]) + """,
                        backgroundColor: 'rgba(67, 97, 238, 0.7)',
                        borderColor: 'rgba(67, 97, 238, 1)',
                        borderWidth: 1,
                        type: 'line',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Top Performers Analysis'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Questions'
                        }
                    },
                    y1: {
                        beginAtZero: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Score'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });

        // Score distribution chart
        const scoreDistCtx = document.getElementById('scoreDistributionChart').getContext('2d');
        const scoreDistChart = new Chart(scoreDistCtx, {
            type: 'bar',
            data: {
                labels: ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
                datasets: [{
                    label: 'Participants',
                    data: """ + json.dumps(score_distribution_data) + """,
                    backgroundColor: [
                        'rgba(220, 53, 69, 0.7)',
                        'rgba(255, 193, 7, 0.7)',
                        'rgba(255, 151, 0, 0.7)',
                        'rgba(40, 167, 69, 0.7)',
                        'rgba(67, 97, 238, 0.7)'
                    ],
                    borderColor: [
                        'rgba(220, 53, 69, 1)',
                        'rgba(255, 193, 7, 1)',
                        'rgba(255, 151, 0, 1)',
                        'rgba(40, 167, 69, 1)',
                        'rgba(67, 97, 238, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Score Distribution'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Participants'
                        },
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });

        // Question analysis chart
        const questionCtx = document.getElementById('questionChart').getContext('2d');
        const questionChart = new Chart(questionCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(question_labels) + """,
                datasets: [{
                    label: 'Correct Answer %',
                    data: """ + json.dumps(correct_percentages) + """,
                    backgroundColor: """ + json.dumps([
                        'rgba(40, 167, 69, 0.7)' if d == "easy" else 
                        'rgba(255, 193, 7, 0.7)' if d == "medium" else 
                        'rgba(220, 53, 69, 0.7)' 
                        for d in difficulty_levels
                    ]) + """,
                    borderColor: """ + json.dumps([
                        'rgba(40, 167, 69, 1)' if d == "easy" else 
                        'rgba(255, 193, 7, 1)' if d == "medium" else 
                        'rgba(220, 53, 69, 1)' 
                        for d in difficulty_levels
                    ]) + """,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Question Difficulty Analysis'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Percentage Correct'
                        }
                    }
                }
            }
        });
        </script>
        </div>
    </body>
    </html>
    """
    
    return html
