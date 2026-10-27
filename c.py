"""
╔══════════════════════════════════════════════════════════════════════════╗
║                     QUIZBOT — HTML Report Generator                      ║
║                                                                          ║
║  Generates beautiful, self-contained HTML quiz reports and analysis      ║
║  pages with light/dark theme support and interactive score displays.     ║
║                                                                          ║
║  Sponsored by  : Qzio — qzio.in                                          ║
║  Developed by  : devgagan — devgagan.in                                  ║
║  License       : MIT                                                     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
import os
from unidecode import unidecode
import re
import json
import random, uuid
from bs4 import BeautifulSoup

async def pyro_generate_quiz_html(quiz, chat_id, client):
    quiz_name = quiz["quiz_name"].replace(" ", "_")
    quiz_name = unidecode(quiz_name)  
    quiz_name = re.sub(r"[^a-zA-Z0-9_-]", "", quiz_name)  
    max_length = 100
    html_filename = quiz_name[:max_length] + ".html"  # Keep it within limit
    
    max_marks = len(quiz["questions"])
    negative_mark = quiz.get("negative_marks", 1/3)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{quiz['quiz_name']} - Team SPY</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron&display=swap');

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                font-family: 'Orbitron', sans-serif;
                background: #0d0d0d;
                color: #0ff;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
                overflow-y: auto;
                transition: background 0.3s, color 0.3s;
            }}

            .header {{
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: #0d0d0d;
                box-shadow: 0 0 15px cyan;
                border-radius: 8px;
                transition: background 0.3s, box-shadow 0.3s;
                position: sticky;
                top: 0;
                z-index: 1000;
            }}

            .header h1 {{
                margin: 0;
                font-size: 20px;
                color: cyan;
                transition: color 0.3s;
            }}

            .score-counter {{
                font-size: 18px;
                color: cyan;
                margin-left: 20px;
            }}

            .switch {{
                position: relative;
                display: inline-block;
                width: 50px;
                height: 24px;
            }}

            .switch input {{
                opacity: 0;
                width: 0;
                height: 0;
            }}

            .slider {{
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: cyan;
                transition: 0.4s;
                border-radius: 24px;
            }}

            .slider:before {{
                position: absolute;
                content: "";
                height: 18px;
                width: 18px;
                left: 4px;
                bottom: 3px;
                background-color: black;
                transition: 0.4s;
                border-radius: 50%;
            }}

            input:checked + .slider {{
                background-color: #333;
            }}

            input:checked + .slider:before {{
                transform: translateX(26px);
                background-color: white;
            }}

            .light-mode {{
                background: white !important;
                color: black !important;
            }}

            .light-mode .header {{
                background: white;
                box-shadow: 0 0 15px gray;
            }}

            .light-mode h2 {{
                color: black !important;
                text-shadow: none;
            }}

            .light-mode .score-counter {{
            color: black !important; /* Change score counter text color to black in light mode */
            
            }}

            .light-mode .header h1 {{
                color: black;
            }}

            .light-mode .ai-response {{
                color: black !important;
            }}

            .light-mode .container {{
                background: rgba(0, 0, 0, 0.1);
                box-shadow: 0 0 15px gray;
            }}

            .light-mode .question {{
                color: black;
            }}

            .light-mode .options button {{
                background: rgba(0, 0, 0, 0.3);
                color: black;
                text-shadow: none;
                box-shadow: 0 0 10px gray;
            }}

            .light-mode .options button:hover {{
                background: black;
                color: white;
                box-shadow: 0 0 20px gray;
            }}

            .container {{
                max-width: 600px;
                width: 100%;
                margin-top: 20px;
                background: rgba(0, 255, 255, 0.1);
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 0 15px cyan;
                text-align: center;
                animation: fadeIn 1s ease-in-out;
                margin-bottom: 20px;
                transition: background 0.3s, box-shadow 0.3s;
            }}

            h2 {{
                color: cyan;
                text-shadow: 0 0 10px cyan;
                margin-bottom: 10px;
                transition: color 0.3s, text-shadow 0.3s;
            }}

            .question {{
                font-size: 20px;
                font-weight: bold;
                color: white;
                margin: 15px 0;
                transition: color 0.3s;
            }}

            .options {{
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-top: 10px;
            }}

            .options button {{
                font-size: 18px;
                padding: 12px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                background: rgba(0, 255, 255, 0.3);
                color: #fff;
                text-shadow: 0 0 10px cyan;
                transition: all 0.3s;
                box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            }}

            .options button:hover {{
                background: cyan;
                color: #000;
                transform: scale(1.05);
                box-shadow: 0 0 20px cyan;
            }}

            .correct {{
                background: lime !important;
                color: #000 !important;
                box-shadow: 0 0 15px lime !important;
            }}

            .wrong {{
                background: red !important;
                color: #fff !important;
                box-shadow: 0 0 15px red !important;
            }}

            .ai-response {{
                margin-top: 12px;
                font-size: 16px;
                font-style: italic;
                visibility: hidden;
                color: lime;
                opacity: 0;
                transition: opacity 0.5s ease-in-out, visibility 0.5s;
            }}

            .xp-bar {{
                width: 90%;
                height: 10px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                margin-top: 20px;
                overflow: hidden;
            }}

            .xp-progress {{
                height: 100%;
                width: 0%;
                background: lime;
                transition: width 0.5s ease-in-out;
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
    <header class="header">
        <h1>Quiz</h1>
        <div class="score-counter">🎯: <span id="score">0</span> / {max_marks}</div>
        <label class="switch">
            <input type="checkbox" id="theme-toggle">
            <span class="slider"></span>
        </label>
    </header>
    <div class="container">
        <h2>{quiz['quiz_name']}</h2>
        <p id="ai-assistant">🤖 <b>AI:</b> Let's see if you can beat me!</p>
    """

    for idx, question in enumerate(quiz["questions"]):
        question_text = question["question"]
        correct_index = question["correct_option_id"]
        explanation = question.get("explanation", "No explanation provided.")

        html_content += f"""
            <div class="question">{idx + 1}. {question_text}</div>
            <div class="options" id="options{idx}">
        """

        for i, option in enumerate(question["options"]):
            correct = "true" if i == correct_index else "false"
            html_content += f"""
                <button onclick="checkAnswer(this, {correct}, {idx}, {correct_index})">{option}</button>
            """

        html_content += f"""
            </div>
            <p class="ai-response" id="exp{idx}">🔍 <b>AI:</b> {explanation}</p>
        """

    html_content += """
        </div>
        <div class="xp-bar"><div class="xp-progress" id="xp-bar"></div></div>
        
        <script>
            let xp = localStorage.getItem('xp') || 0;
            let score = 0;
            const maxMarks = """ + str(max_marks) + """;
            const negativeMark = """ + str(negative_mark) + """;
            document.getElementById('xp-bar').style.width = xp + '%';

            function checkAnswer(button, isCorrect, qIndex, correctIndex) {
                let options = document.querySelectorAll(`#options${qIndex} button`);
                options.forEach(btn => btn.disabled = true);

                if (isCorrect) {
                    button.classList.add('correct');
                    button.innerHTML += " ✅";
                    score += 1;
                    document.getElementById('ai-assistant').innerHTML = "🤖 <b>AI:</b> Impressive! You're on fire! 🔥";
                    playSound('correct');
                } else {
                    button.classList.add('wrong');
                    button.innerHTML += " ❌";
                    options[correctIndex].classList.add('correct');
                    options[correctIndex].innerHTML += " ✅";
                    score -= negativeMark;
                    document.getElementById('ai-assistant').innerHTML = "🤖 <b>AI:</b> Oops! That wasn't right.";
                    playSound('wrong');
                }

                let explanation = document.getElementById('exp' + qIndex);
                explanation.style.visibility = "visible";
                explanation.style.opacity = "1";
                document.getElementById('score').innerText = Math.max(0, score).toFixed(2);
                xp = Math.min(100, parseInt(xp) + 10);
                document.getElementById('xp-bar').style.width = xp + '%';
                localStorage.setItem('xp', xp);
            }

            function playSound(type) {
                let audio = new Audio(type === 'correct' ? 'https://www.fesliyanstudios.com/play-mp3/387' : 'https://www.fesliyanstudios.com/play-mp3/391');
                audio.play();
            }

            document.addEventListener("DOMContentLoaded", () => {
                const toggleSwitch = document.getElementById("theme-toggle");
                const body = document.body;

                if (localStorage.getItem("theme") === "light") {
                    body.classList.add("light-mode");
                    toggleSwitch.checked = true;
                }

                toggleSwitch.addEventListener("change", () => {
                    if (toggleSwitch.checked) {
                        body.classList.add("light-mode");
                        localStorage.setItem("theme", "light");
                    } else {
                        body.classList.remove("light-mode");
                        localStorage.setItem("theme", "dark");
                    }
                });
            });
        </script>
    </body>
    </html>
    """

    # Save HTML file
    with open(html_filename, "w", encoding="utf-8") as file:
        file.write(html_content)

    # Send HTML file to the user
    await client.send_document(chat_id, html_filename, caption=f"📄 {quiz['quiz_name']} \n\n**__Powered by Quiz Bot__**", protect_content=True)

    # Cleanup
    os.remove(html_filename)
    

async def old_generate_quiz_html(quiz, chat_id, context, ParseMode, type):
    quiz_name = quiz["quiz_name"].replace(" ", "_")
    quiz_name = unidecode(quiz_name)  
    quiz_name = re.sub(r"[^a-zA-Z0-9_-]", "", quiz_name)  
    max_length = 100
    html_filename = quiz_name[:max_length] + ".html"  # Keep it within limit
    max_marks = len(quiz["questions"])
    negative_mark = quiz.get("negative_marks", 1/4)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{quiz['quiz_name']} - Team SPY</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron&display=swap');

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                font-family: 'Orbitron', sans-serif;
                background: #0d0d0d;
                color: #0ff;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                min-height: 100vh;
                overflow-y: auto;
                transition: background 0.3s, color 0.3s;
            }}

            .header {{
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: #0d0d0d;
                box-shadow: 0 0 15px cyan;
                border-radius: 8px;
                transition: background 0.3s, box-shadow 0.3s;
                position: sticky;
                top: 0;
                z-index: 1000;
            }}

            .header h1 {{
                margin: 0;
                font-size: 20px;
                color: cyan;
                transition: color 0.3s;
            }}

            .score-counter {{
                font-size: 18px;
                color: cyan;
                margin-left: 20px;
            }}

            .switch {{
                position: relative;
                display: inline-block;
                width: 50px;
                height: 24px;
            }}

            .switch input {{
                opacity: 0;
                width: 0;
                height: 0;
            }}

            .slider {{
                position: absolute;
                cursor: pointer;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: cyan;
                transition: 0.4s;
                border-radius: 24px;
            }}

            .slider:before {{
                position: absolute;
                content: "";
                height: 18px;
                width: 18px;
                left: 4px;
                bottom: 3px;
                background-color: black;
                transition: 0.4s;
                border-radius: 50%;
            }}

            input:checked + .slider {{
                background-color: #333;
            }}

            input:checked + .slider:before {{
                transform: translateX(26px);
                background-color: white;
            }}

            .light-mode {{
                background: white !important;
                color: black !important;
            }}

            .light-mode .header {{
                background: white;
                box-shadow: 0 0 15px gray;
            }}

            .light-mode h2 {{
                color: black !important;
                text-shadow: none;
            }}

            .light-mode .score-counter {{
            color: black !important; /* Change score counter text color to black in light mode */
            
            }}

            .light-mode .header h1 {{
                color: black;
            }}

            .light-mode .ai-response {{
                color: black !important;
            }}

            .light-mode .container {{
                background: rgba(0, 0, 0, 0.1);
                box-shadow: 0 0 15px gray;
            }}

            .light-mode .question {{
                color: black;
            }}

            .light-mode .options button {{
                background: rgba(0, 0, 0, 0.3);
                color: black;
                text-shadow: none;
                box-shadow: 0 0 10px gray;
            }}

            .light-mode .options button:hover {{
                background: black;
                color: white;
                box-shadow: 0 0 20px gray;
            }}

            .container {{
                max-width: 600px;
                width: 100%;
                margin-top: 20px;
                background: rgba(0, 255, 255, 0.1);
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 0 15px cyan;
                text-align: center;
                animation: fadeIn 1s ease-in-out;
                margin-bottom: 20px;
                transition: background 0.3s, box-shadow 0.3s;
            }}

            h2 {{
                color: cyan;
                text-shadow: 0 0 10px cyan;
                margin-bottom: 10px;
                transition: color 0.3s, text-shadow 0.3s;
            }}

            .question {{
                font-size: 20px;
                font-weight: bold;
                color: white;
                margin: 15px 0;
                transition: color 0.3s;
            }}

            .options {{
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-top: 10px;
            }}

            .options button {{
                font-size: 18px;
                padding: 12px;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                background: rgba(0, 255, 255, 0.3);
                color: #fff;
                text-shadow: 0 0 10px cyan;
                transition: all 0.3s;
                box-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
            }}

            .options button:hover {{
                background: cyan;
                color: #000;
                transform: scale(1.05);
                box-shadow: 0 0 20px cyan;
            }}

            .correct {{
                background: lime !important;
                color: #000 !important;
                box-shadow: 0 0 15px lime !important;
            }}

            .wrong {{
                background: red !important;
                color: #fff !important;
                box-shadow: 0 0 15px red !important;
            }}

            .ai-response {{
                margin-top: 12px;
                font-size: 16px;
                font-style: italic;
                visibility: hidden;
                color: lime;
                opacity: 0;
                transition: opacity 0.5s ease-in-out, visibility 0.5s;
            }}

            .xp-bar {{
                width: 90%;
                height: 10px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                margin-top: 20px;
                overflow: hidden;
            }}

            .xp-progress {{
                height: 100%;
                width: 0%;
                background: lime;
                transition: width 0.5s ease-in-out;
            }}

            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
    <header class="header">
        <h1>Quiz</h1>
        <div class="score-counter">🎯: <span id="score">0</span> / {max_marks}</div>
        <label class="switch">
            <input type="checkbox" id="theme-toggle">
            <span class="slider"></span>
        </label>
    </header>
    <div class="container">
        <h2>{quiz['quiz_name']}</h2>
        <p id="ai-assistant">🤖 <b>AI:</b> Let's see if you can beat me!</p>
    """

    for idx, question in enumerate(quiz["questions"]):
        question_text = question["question"]
        correct_index = question["correct_option_id"]
        explanation = question.get("explanation", "No explanation provided.")

        html_content += f"""
            <div class="question">{idx + 1}. {question_text}</div>
            <div class="options" id="options{idx}">
        """

        for i, option in enumerate(question["options"]):
            correct = "true" if i == correct_index else "false"
            html_content += f"""
                <button onclick="checkAnswer(this, {correct}, {idx}, {correct_index})">{option}</button>
            """

        html_content += f"""
            </div>
            <p class="ai-response" id="exp{idx}">🔍 <b>AI:</b> {explanation}</p>
        """

    html_content += """
        </div>
        <div class="xp-bar"><div class="xp-progress" id="xp-bar"></div></div>
        
        <script>
            let xp = localStorage.getItem('xp') || 0;
            let score = 0;
            const maxMarks = """ + str(max_marks) + """;
            const negativeMark = """ + str(negative_mark) + """;
            document.getElementById('xp-bar').style.width = xp + '%';

            function checkAnswer(button, isCorrect, qIndex, correctIndex) {
                let options = document.querySelectorAll(`#options${qIndex} button`);
                options.forEach(btn => btn.disabled = true);

                if (isCorrect) {
                    button.classList.add('correct');
                    button.innerHTML += " ✅";
                    score += 1;
                    document.getElementById('ai-assistant').innerHTML = "🤖 <b>AI:</b> Impressive! You're on fire! 🔥";
                    playSound('correct');
                } else {
                    button.classList.add('wrong');
                    button.innerHTML += " ❌";
                    options[correctIndex].classList.add('correct');
                    options[correctIndex].innerHTML += " ✅";
                    score -= negativeMark;
                    document.getElementById('ai-assistant').innerHTML = "🤖 <b>AI:</b> Oops! That wasn't right.";
                    playSound('wrong');
                }

                let explanation = document.getElementById('exp' + qIndex);
                explanation.style.visibility = "visible";
                explanation.style.opacity = "1";
                document.getElementById('score').innerText = Math.max(0, score).toFixed(2);
                xp = Math.min(100, parseInt(xp) + 10);
                document.getElementById('xp-bar').style.width = xp + '%';
                localStorage.setItem('xp', xp);
            }

            function playSound(type) {
                let audio = new Audio(type === 'correct' ? 'https://www.fesliyanstudios.com/play-mp3/387' : 'https://www.fesliyanstudios.com/play-mp3/391');
                audio.play();
            }

            document.addEventListener("DOMContentLoaded", () => {
                const toggleSwitch = document.getElementById("theme-toggle");
                const body = document.body;

                if (localStorage.getItem("theme") === "light") {
                    body.classList.add("light-mode");
                    toggleSwitch.checked = true;
                }

                toggleSwitch.addEventListener("change", () => {
                    if (toggleSwitch.checked) {
                        body.classList.add("light-mode");
                        localStorage.setItem("theme", "light");
                    } else {
                        body.classList.remove("light-mode");
                        localStorage.setItem("theme", "dark");
                    }
                });
            });
        </script>
    </body>
    </html>
    """

    # Save HTML file
    with open(html_filename, "w", encoding="utf-8") as file:
        file.write(html_content)
        
    with open(html_filename, "rb") as file:
        await context.bot.send_document(
            chat_id=chat_id,
            document=file,
            caption=f"📄 {quiz['quiz_name']} \n\n<b><i>Powered by Quiz Bot</i></b>",
            parse_mode=ParseMode.HTML,
            protect_content=type
        )

    # Cleanup
    os.remove(html_filename)


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


async def workinggenerate_quiz_html(quiz, chat_id, context, ParseMode, type):
    """
    Premium Quiz HTML Generator with Exam/Practice Modes
    Enhanced with dark mode, better UX, and improved navigation
    """
    
    def js_escape(text):
        """Escape special characters for JavaScript with proper white-space handling"""
        if not text:
            return ""
        text = str(text)
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        return text
    
    # Prepare quiz metadata
    quiz_name = re.sub(r"[^a-zA-Z0-9_-]", "", unidecode(quiz["quiz_name"]).replace(" ", "_"))[:100] + ".html"
    max_marks = len(quiz["questions"])
    negative_mark = quiz.get("negative_marks", 0.25)
    default_time = quiz.get("timer", 60) * len(quiz["questions"])
    
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
            options: {json.dumps(options)},
            correctIndex: {options.index(correct_option)},
            explanation: "{js_escape(q.get("explanation", "No explanation provided"))}"
        }}""")
    
    # Build the Enhanced HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{quiz['quiz_name']}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }}
        
        :root {{
            --primary: #667eea;
            --primary-dark: #5568d3;
            --secondary: #764ba2;
            --success: #48bb78;
            --danger: #f5576c;
            --warning: #fbbf24;
            --info: #4facfe;
            --bg-light: #f7fafc;
            --bg-white: #ffffff;
            --text-dark: #1a202c;
            --text-light: #718096;
            --border: #e2e8f0;
        }}
        
        [data-theme="dark"] {{
            --bg-light: #1a202c;
            --bg-white: #2d3748;
            --text-dark: #f7fafc;
            --text-light: #cbd5e0;
            --border: #4a5568;
        }}
        
        body {{
            font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            min-height: 100vh;
            overflow: hidden;
            user-select: none;
            -webkit-user-select: none;
            transition: background 0.3s ease;
        }}
        
        /* Scrollbar Styles */
        .scrollable::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .scrollable::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        .scrollable::-webkit-scrollbar-thumb {{
            background: var(--primary);
            border-radius: 10px;
        }}
        
        /* Content Protection */
        .protected-content {{
            white-space: pre-wrap;
            word-wrap: break-word;
            word-break: break-word;
            line-height: 1.6;
            user-select: none;
        }}
        
        /* Mode Selection Screen */
        #modeSelection {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            padding: 20px;
            overflow-y: auto;
        }}
        
        .mode-container {{
            background: #ffffff;
            border-radius: 24px;
            padding: 40px 30px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: modalSlideIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}
        
        @keyframes modalSlideIn {{
            from {{
                opacity: 0;
                transform: translateY(40px) scale(0.95);
            }}
            to {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
        }}
        
        .mode-header {{
            text-align: center;
            margin-bottom: 32px;
        }}
        
        .mode-header-icon {{
            width: 70px;
            height: 70px;
            margin: 0 auto 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            color: white;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
        }}
        
        .mode-header h2 {{
            font-size: 24px;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 8px;
        }}
        
        .mode-header p {{
            font-size: 14px;
            color: #718096;
            font-weight: 400;
        }}
        
        .mode-cards {{
            display: grid;
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .mode-card {{
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 16px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .mode-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 28px rgba(102, 126, 234, 0.15);
            border-color: #cbd5e0;
        }}
        
        .mode-card.selected {{
            border-color: #667eea;
            background: #ffffff;
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }}
        
        .mode-card-header {{
            display: flex;
            align-items: center;
        }}
        
        .mode-icon {{
            width: 54px;
            height: 54px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-right: 16px;
            flex-shrink: 0;
        }}
        
        .exam-mode .mode-icon {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        
        .practice-mode .mode-icon {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }}
        
        .mode-info h3 {{
            font-size: 17px;
            font-weight: 700;
            color: #1a202c;
            margin-bottom: 4px;
        }}
        
        .mode-info p {{
            font-size: 13px;
            color: #718096;
            line-height: 1.4;
        }}
        
        .timer-config {{
            margin-bottom: 24px;
        }}
        
        .timer-config label {{
            display: block;
            font-size: 14px;
            font-weight: 600;
            color: #1a202c;
            margin-bottom: 10px;
        }}
        
        .timer-config label i {{
            margin-right: 6px;
            color: #667eea;
        }}
        
        .timer-input {{
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 500;
            transition: all 0.3s ease;
            background: white;
            font-family: 'Poppins', sans-serif;
            color: #1a202c;
        }}
        
        .timer-input::placeholder {{
            color: #a0aec0;
        }}
        
        .timer-input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        .start-btn {{
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.35);
        }}
        
        .start-btn:hover:not(:disabled) {{
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(102, 126, 234, 0.45);
        }}
        
        .start-btn:active:not(:disabled) {{
            transform: translateY(0px);
        }}
        
        .start-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            background: #cbd5e0;
            box-shadow: none;
        }}
        
        /* Quiz Container - Fixed Layout */
        #quizContainer {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            background: var(--bg-light);
            overflow: hidden;
        }}
        
        /* Header - Fixed */
        .quiz-header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: var(--bg-white);
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.08);
            z-index: 100;
            padding: 16px 20px;
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            gap: 10px;
        }}
        
        .quiz-title {{
            font-size: 15px;
            font-weight: 700;
            color: var(--text-dark);
            display: flex;
            align-items: center;
            gap: 8px;
            flex: 1;
            min-width: 0;
        }}
        
        .quiz-title-text {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 150px;
        }}
        
        .mode-badge {{
            font-size: 10px;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }}
        
        .mode-badge.exam {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }}
        
        .mode-badge.practice {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }}
        
        .header-actions {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}
        
        .theme-toggle {{
            width: 36px;
            height: 36px;
            background: var(--bg-light);
            border: none;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            color: var(--text-dark);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.1);
        }}
        
        .timer-display {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 16px;
            font-weight: 700;
            color: var(--primary);
            padding: 8px 14px;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
            border-radius: 12px;
            white-space: nowrap;
        }}
        
        .timer-display.warning {{
            color: var(--danger);
            background: linear-gradient(135deg, rgba(245, 87, 108, 0.15) 0%, rgba(240, 147, 251, 0.15) 100%);
            animation: pulse 1s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        
        .header-progress {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-light);
            margin-bottom: 8px;
        }}
        
        .progress-bar-container {{
            height: 6px;
            background: var(--border);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
            transition: width 0.3s ease;
            border-radius: 10px;
        }}
        
        /* Question Section - Scrollable */
        .question-section {{
            position: fixed;
            top: 140px;
            left: 0;
            right: 0;
            bottom: 80px;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
            -webkit-overflow-scrolling: touch;
        }}
        
        .question-section.scrollable {{
            scrollbar-width: thin;
            scrollbar-color: var(--primary) transparent;
        }}
        
        .question-card {{
            background: var(--bg-white);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .question-number {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 700;
            color: var(--primary);
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
            padding: 6px 14px;
            border-radius: 20px;
            margin-bottom: 16px;
        }}
        
        .question-reference {{
            background: linear-gradient(135deg, rgba(79, 172, 254, 0.15) 0%, rgba(0, 242, 254, 0.15) 100%);
            border-left: 4px solid var(--info);
            padding: 14px 16px;
            border-radius: 10px;
            margin-bottom: 16px;
            font-size: 14px;
            color: var(--text-dark);
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .question-text {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-dark);
            line-height: 1.7;
            margin-bottom: 20px;
            white-space: pre-wrap;
            word-wrap: break-word;
            word-break: break-word;
        }}
        
        .options-container {{
            display: grid;
            gap: 12px;
        }}
        
        .option-btn {{
            width: 100%;
            padding: 16px 18px;
            background: var(--bg-light);
            border: 3px solid var(--border);
            border-radius: 14px;
            text-align: left;
            font-size: 15px;
            color: var(--text-dark);
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
            word-break: break-word;
            user-select: none;
        }}
        
        .option-btn:active {{
            transform: scale(0.98);
        }}
        
        .option-indicator {{
            min-width: 28px;
            height: 28px;
            border-radius: 50%;
            background: var(--bg-white);
            border: 2px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .option-text {{
            flex: 1;
            padding-top: 3px;
        }}
        
        .option-btn:hover:not(.disabled) {{
            border-color: var(--primary);
            transform: translateX(4px);
        }}
        
        .option-btn.selected {{
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
            border-color: var(--primary);
        }}
        
        .option-btn.selected .option-indicator {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border-color: transparent;
        }}
        
        .option-btn.correct {{
            background: linear-gradient(135deg, rgba(72, 187, 120, 0.15) 0%, rgba(72, 187, 120, 0.15) 100%);
            border-color: var(--success);
        }}
        
        .option-btn.correct .option-indicator {{
            background: var(--success);
            color: white;
            border-color: transparent;
        }}
        
        .option-btn.incorrect {{
            background: linear-gradient(135deg, rgba(245, 87, 108, 0.15) 0%, rgba(245, 87, 108, 0.15) 100%);
            border-color: var(--danger);
        }}
        
        .option-btn.incorrect .option-indicator {{
            background: var(--danger);
            color: white;
            border-color: transparent;
        }}
        
        .option-btn.disabled {{
            pointer-events: none;
            opacity: 0.6;
        }}
        
        /* Explanation */
        .explanation-box {{
            display: none;
            background: linear-gradient(135deg, rgba(254, 245, 231, 0.5) 0%, rgba(251, 191, 36, 0.2) 100%);
            border-left: 4px solid var(--warning);
            border-radius: 12px;
            padding: 16px;
            margin-top: 20px;
            animation: slideDown 0.3s ease-out;
        }}
        
        @keyframes slideDown {{
            from {{
                opacity: 0;
                max-height: 0;
                padding: 0;
            }}
            to {{
                opacity: 1;
                max-height: 500px;
                padding: 16px;
            }}
        }}
        
        .explanation-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 700;
            color: #92400e;
            margin-bottom: 10px;
        }}
        
        .explanation-text {{
            font-size: 14px;
            color: #78350f;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        [data-theme="dark"] .explanation-text {{
            color: #fbbf24;
        }}
        
        /* Navigation Controls - Fixed */
        .nav-controls {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--bg-white);
            padding: 16px 20px;
            box-shadow: 0 -2px 15px rgba(0, 0, 0, 0.08);
            display: flex;
            gap: 12px;
            z-index: 90;
        }}
        
        .nav-btn {{
            flex: 1;
            padding: 14px;
            border: none;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }}
        
        .nav-btn.primary {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
        }}
        
        .nav-btn.secondary {{
            background: var(--bg-light);
            color: var(--text-dark);
            border: 2px solid var(--border);
        }}
        
        .nav-btn:active {{
            transform: scale(0.96);
        }}
        
        .nav-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}
        
        /* Question Navigator */
        .question-nav-toggle {{
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border: none;
            border-radius: 50%;
            font-size: 22px;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            z-index: 85;
            transition: all 0.3s ease;
        }}
        
        .question-nav-toggle:active {{
            transform: scale(0.95);
        }}
        
        .question-nav-panel {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: var(--bg-white);
            border-radius: 24px 24px 0 0;
            box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.15);
            z-index: 95;
            max-height: 70vh;
            overflow-y: auto;
            transform: translateY(100%);
            transition: transform 0.3s ease;
            padding: 20px;
        }}
        
        .question-nav-panel.open {{
            transform: translateY(0);
        }}
        
        .nav-panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 2px solid var(--border);
        }}
        
        .nav-panel-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--text-dark);
        }}
        
        .nav-close-btn {{
            width: 32px;
            height: 32px;
            background: var(--bg-light);
            border: none;
            border-radius: 50%;
            font-size: 16px;
            cursor: pointer;
            color: var(--text-light);
        }}
        
        .nav-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 20px;
            font-size: 12px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .legend-box {{
            width: 20px;
            height: 20px;
            border-radius: 6px;
        }}
        
        .legend-box.answered {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        }}
        
        .legend-box.marked {{
            background: linear-gradient(135deg, var(--warning) 0%, #f59e0b 100%);
        }}
        
        .legend-box.unanswered {{
            background: var(--border);
        }}
        
        .question-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
        }}
        
        .question-nav-item {{
            aspect-ratio: 1;
            border: 2px solid var(--border);
            border-radius: 10px;
            background: var(--bg-white);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            color: var(--text-light);
        }}
        
        .question-nav-item:active {{
            transform: scale(0.95);
        }}
        
        .question-nav-item.current {{
            border-color: var(--primary);
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
            color: var(--primary);
        }}
        
        .question-nav-item.answered {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            border-color: transparent;
        }}
        
        .question-nav-item.marked {{
            background: linear-gradient(135deg, var(--warning) 0%, #f59e0b 100%);
            color: white;
            border-color: transparent;
        }}
        
        .question-nav-item.correct {{
            background: linear-gradient(135deg, var(--success) 0%, #38a169 100%);
            color: white;
            border-color: transparent;
        }}
        
        .question-nav-item.incorrect {{
            background: linear-gradient(135deg, var(--danger) 0%, #e53e3e 100%);
            color: white;
            border-color: transparent;
        }}
        
        /* Results Screen */
        #resultsContainer {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            background: var(--bg-light);
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
            z-index: 1000;
        }}
        
        #resultsContainer.scrollable {{
            scrollbar-width: thin;
            scrollbar-color: var(--primary) transparent;
        }}
        
        .results-header {{
            text-align: center;
            padding: 40px 20px;
            background: var(--bg-white);
            border-radius: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        }}
        
        .results-icon {{
            font-size: 80px;
            margin-bottom: 20px;
        }}
        
        .results-title {{
            font-size: 28px;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 10px;
        }}
        
        .results-score {{
            font-size: 52px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}
        
        .results-percentage {{
            font-size: 20px;
            color: var(--text-light);
            font-weight: 600;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .stat-card {{
            background: var(--bg-white);
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        }}
        
        .stat-icon {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-bottom: 12px;
        }}
        
        .stat-icon.correct {{
            background: linear-gradient(135deg, var(--success) 0%, #38a169 100%);
            color: white;
        }}
        
        .stat-icon.incorrect {{
            background: linear-gradient(135deg, var(--danger) 0%, #e53e3e 100%);
            color: white;
        }}
        
        .stat-icon.unattempted {{
            background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
            color: white;
        }}
        
        .stat-icon.negative {{
            background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
            color: white;
        }}
        
        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--text-dark);
            margin-bottom: 4px;
        }}
        
        .stat-label {{
            font-size: 13px;
            color: var(--text-light);
            font-weight: 500;
        }}
        
        .action-buttons {{
            display: grid;
            gap: 12px;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .action-btn {{
            width: 100%;
            padding: 18px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
        }}
        
        .action-btn.primary {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
        }}
        
        .action-btn.secondary {{
            background: var(--bg-white);
            color: var(--text-dark);
            border: 2px solid var(--border);
        }}
        
        .action-btn:hover {{
            transform: translateY(-2px);
        }}
        
        /* Desktop Styles */
        @media (min-width: 768px) {{
            .quiz-title-text {{
                max-width: 300px;
            }}
            
            .question-grid {{
                grid-template-columns: repeat(8, 1fr);
            }}
            
            .question-nav-toggle {{
                display: none;
            }}
            
            .question-nav-panel {{
                position: static;
                transform: translateY(0);
                border-radius: 20px;
                margin: 20px auto;
                max-height: none;
                max-width: 800px;
            }}
            
            .nav-close-btn {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <!-- Mode Selection Screen -->
    <div id="modeSelection">
        <div class="mode-container">
            <div class="mode-header">
                <div class="mode-header-icon">
                    <i class="fas fa-graduation-cap"></i>
                </div>
                <h2>{quiz['quiz_name']}</h2>
                <p>Choose your preferred test mode</p>
            </div>
            
            <div class="mode-cards">
                <div class="mode-card exam-mode" data-mode="exam">
                    <div class="mode-card-header">
                        <div class="mode-icon">
                            <i class="fas fa-file-alt"></i>
                        </div>
                        <div class="mode-info">
                            <h3>Exam Mode</h3>
                            <p>Complete all questions, results shown after submission</p>
                        </div>
                    </div>
                </div>
                
                <div class="mode-card practice-mode" data-mode="practice">
                    <div class="mode-card-header">
                        <div class="mode-icon">
                            <i class="fas fa-book-open"></i>
                        </div>
                        <div class="mode-info">
                            <h3>Practice Mode</h3>
                            <p>Instant feedback with detailed explanations</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="timer-config">
                <label for="customTimer">
                    <i class="fas fa-clock"></i> Custom Timer (minutes)
                </label>
                <input 
                    type="number" 
                    id="customTimer" 
                    class="timer-input" 
                    placeholder="Default: {int(default_time/60)} minutes"
                    min="1"
                    max="300"
                />
            </div>
            
            <button class="start-btn" id="startQuizBtn" disabled>
                <i class="fas fa-play-circle"></i>
                <span>Start Quiz</span>
            </button>
        </div>
    </div>
    
    <!-- Quiz Container -->
    <div id="quizContainer">
        <div class="quiz-header">
            <div class="header-top">
                <div class="quiz-title">
                    <i class="fas fa-clipboard-list"></i>
                    <span class="quiz-title-text" title="{quiz['quiz_name']}">{quiz['quiz_name']}</span>
                    <span class="mode-badge" id="modeBadge"></span>
                </div>
                <div class="header-actions">
                    <button class="theme-toggle" id="themeToggle" title="Toggle Dark Mode">
                        <i class="fas fa-moon"></i>
                    </button>
                    <div class="timer-display" id="timerDisplay">
                        <i class="fas fa-clock"></i>
                        <span id="timeText">00:00</span>
                    </div>
                </div>
            </div>
            <div class="header-progress">
                <span id="progressText">Question 1 of {max_marks}</span>
                <span id="attemptedText">Attempted: 0/{max_marks}</span>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" id="progressBar"></div>
            </div>
        </div>
        
        <div class="question-section scrollable" id="questionSection">
            <!-- Questions will be rendered here -->
        </div>
        
        <div class="nav-controls">
            <button class="nav-btn secondary" id="prevBtn">
                <i class="fas fa-chevron-left"></i>
                Previous
            </button>
            <button class="nav-btn secondary" id="markBtn">
                <i class="fas fa-bookmark"></i>
                Mark
            </button>
            <button class="nav-btn primary" id="nextBtn">
                Next
                <i class="fas fa-chevron-right"></i>
            </button>
            <button class="nav-btn primary" id="submitBtn" style="display: none;">
                <i class="fas fa-paper-plane"></i>
                Submit
            </button>
        </div>
        
        <button class="question-nav-toggle" id="navToggleBtn">
            <i class="fas fa-th"></i>
        </button>
        
        <div class="question-nav-panel" id="navPanel">
            <div class="nav-panel-header">
                <h3 class="nav-panel-title">
                    <i class="fas fa-map-marked-alt"></i> Question Navigator
                </h3>
                <button class="nav-close-btn" id="navCloseBtn">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="nav-legend">
                <div class="legend-item">
                    <div class="legend-box answered"></div>
                    <span>Answered</span>
                </div>
                <div class="legend-item">
                    <div class="legend-box marked"></div>
                    <span>Marked</span>
                </div>
                <div class="legend-item">
                    <div class="legend-box unanswered"></div>
                    <span>Not Answered</span>
                </div>
            </div>
            <div class="question-grid" id="questionGrid">
                <!-- Question navigation items will be rendered here -->
            </div>
        </div>
    </div>
    
    <!-- Results Container -->
    <div id="resultsContainer">
        <div class="results-header">
            <div class="results-icon" id="resultsIcon"></div>
            <h2 class="results-title" id="resultsTitle"></h2>
            <div class="results-score" id="resultsScore"></div>
            <div class="results-percentage" id="resultsPercentage"></div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon correct">
                    <i class="fas fa-check"></i>
                </div>
                <div class="stat-value" id="correctCount">0</div>
                <div class="stat-label">Correct</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon incorrect">
                    <i class="fas fa-times"></i>
                </div>
                <div class="stat-value" id="incorrectCount">0</div>
                <div class="stat-label">Incorrect</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon unattempted">
                    <i class="fas fa-minus"></i>
                </div>
                <div class="stat-value" id="unattemptedCount">0</div>
                <div class="stat-label">Unattempted</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon negative">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="stat-value" id="negativeMarks">0</div>
                <div class="stat-label">Negative Marks</div>
            </div>
        </div>
        
        <div class="action-buttons">
            <button class="action-btn primary" id="reviewBtn">
                <i class="fas fa-search"></i>
                Review Answers
            </button>
            <button class="action-btn secondary" id="restartBtn">
                <i class="fas fa-redo"></i>
                Restart Quiz
            </button>
        </div>
    </div>

    <script>
        // Quiz State
        const quizData = {{
            questions: [{",".join(questions_js)}],
            mode: null,
            totalTime: {default_time},
            negativeMark: {negative_mark}
        }};
        
        const state = {{
            currentQuestion: 0,
            answers: Array(quizData.questions.length).fill(null),
            marked: Array(quizData.questions.length).fill(false),
            timeRemaining: quizData.totalTime,
            timerInterval: null,
            isSubmitted: false,
            isReviewMode: false,
            theme: 'light'
        }};
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            setupModeSelection();
            preventContentCopy();
            loadTheme();
        }});
        
        // Theme Management
        function loadTheme() {{
            const savedTheme = localStorage.getItem('quizTheme') || 'light';
            state.theme = savedTheme;
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeIcon();
        }}
        
        function toggleTheme() {{
            state.theme = state.theme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', state.theme);
            localStorage.setItem('quizTheme', state.theme);
            updateThemeIcon();
        }}
        
        function updateThemeIcon() {{
            const icon = document.querySelector('#themeToggle i');
            if (icon) {{
                icon.className = state.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
            }}
        }}
        
        // Prevent content copying
        function preventContentCopy() {{
            document.addEventListener('contextmenu', e => e.preventDefault());
            document.addEventListener('copy', e => e.preventDefault());
            document.addEventListener('cut', e => e.preventDefault());
            document.addEventListener('selectstart', e => {{
                if (!e.target.tagName.match(/INPUT|TEXTAREA/i)) {{
                    e.preventDefault();
                }}
            }});
        }}
        
        // Mode Selection
        function setupModeSelection() {{
            const modeCards = document.querySelectorAll('.mode-card');
            const startQuizBtn = document.getElementById('startQuizBtn');
            
            modeCards.forEach(card => {{
                card.addEventListener('click', () => {{
                    modeCards.forEach(c => c.classList.remove('selected'));
                    card.classList.add('selected');
                    quizData.mode = card.dataset.mode;
                    startQuizBtn.disabled = false;
                }});
            }});
            
            startQuizBtn.addEventListener('click', startQuiz);
        }}
        
        function startQuiz() {{
            const customTimer = document.getElementById('customTimer');
            const customTime = parseInt(customTimer.value);
            if (customTime && customTime > 0) {{
                state.timeRemaining = customTime * 60;
                quizData.totalTime = customTime * 60;
            }}
            
            // Enable page lock when quiz starts
            document.body.style.overflow = 'hidden';
            
            document.getElementById('modeSelection').style.display = 'none';
            document.getElementById('quizContainer').style.display = 'block';
            
            document.getElementById('modeBadge').textContent = quizData.mode;
            document.getElementById('modeBadge').className = 'mode-badge ' + quizData.mode;
            
            initQuiz();
        }}
        
        function initQuiz() {{
            renderQuestion(0);
            renderQuestionGrid();
            startTimer();
            setupNavigation();
        }}
        
        // Timer
        function startTimer() {{
            updateTimerDisplay();
            state.timerInterval = setInterval(() => {{
                state.timeRemaining--;
                updateTimerDisplay();
                
                if (state.timeRemaining <= 0) {{
                    clearInterval(state.timerInterval);
                    submitQuiz();
                }}
                
                if (state.timeRemaining <= 60) {{
                    document.getElementById('timerDisplay').classList.add('warning');
                }}
            }}, 1000);
        }}
        
        function updateTimerDisplay() {{
            const minutes = Math.floor(state.timeRemaining / 60);
            const seconds = state.timeRemaining % 60;
            document.getElementById('timeText').textContent = 
                `${{String(minutes).padStart(2, '0')}}:${{String(seconds).padStart(2, '0')}}`;
        }}
        
        // Render Question
        function renderQuestion(index) {{
            state.currentQuestion = index;
            const question = quizData.questions[index];
            const questionSection = document.getElementById('questionSection');
            
            let html = `
                <div class="question-card">
                    <div class="question-number">
                        <i class="fas fa-question-circle"></i>
                        Question ${{index + 1}} of ${{quizData.questions.length}}
                    </div>`;
            
            if (question.reference) {{
                html += `
                    <div class="question-reference protected-content">
                        <i class="fas fa-info-circle"></i> ${{question.reference}}
                    </div>`;
            }}
            
            html += `
                    <div class="question-text protected-content">${{question.text}}</div>
                    <div class="options-container">`;
            
            question.options.forEach((option, idx) => {{
                let btnClass = 'option-btn';
                let indicatorContent = String.fromCharCode(65 + idx);
                
                const isSelected = state.answers[index] === idx;
                const isCorrect = idx === question.correctIndex;
                const showAnswer = (quizData.mode === 'practice' && state.answers[index] !== null) || state.isSubmitted;
                
                if (isSelected) {{
                    btnClass += ' selected';
                }}
                
                if (showAnswer) {{
                    btnClass += ' disabled';
                    if (isCorrect) {{
                        btnClass += ' correct';
                        indicatorContent = '<i class="fas fa-check"></i>';
                    }} else if (isSelected && !isCorrect) {{
                        btnClass += ' incorrect';
                        indicatorContent = '<i class="fas fa-times"></i>';
                    }}
                }}
                
                html += `
                    <button class="${{btnClass}}" data-index="${{idx}}" onclick="selectOption(${{idx}})">
                        <div class="option-indicator">${{indicatorContent}}</div>
                        <div class="option-text protected-content">${{option}}</div>
                    </button>`;
            }});
            
            html += `</div>`;
            
            // Show explanation in practice mode or after submission
            const showExplanation = (quizData.mode === 'practice' && state.answers[index] !== null) || 
                                    state.isSubmitted;
            
            if (showExplanation) {{
                html += `
                    <div class="explanation-box" style="display: block;">
                        <div class="explanation-header">
                            <i class="fas fa-lightbulb"></i>
                            Explanation
                        </div>
                        <div class="explanation-text protected-content">${{question.explanation}}</div>
                    </div>`;
            }}
            
            html += `</div>`;
            
            questionSection.innerHTML = html;
            questionSection.scrollTop = 0;
            updateProgress();
            updateNavButtons();
            updateQuestionGrid();
        }}
        
        function selectOption(optionIndex) {{
            if (state.isSubmitted || state.answers[state.currentQuestion] !== null) return;
            
            state.answers[state.currentQuestion] = optionIndex;
            renderQuestion(state.currentQuestion);
            
            // Don't auto-advance - let user click Next manually
        }}
        
        // Navigation
        function setupNavigation() {{
            document.getElementById('prevBtn').addEventListener('click', navigatePrev);
            document.getElementById('nextBtn').addEventListener('click', navigateNext);
            document.getElementById('markBtn').addEventListener('click', toggleMark);
            document.getElementById('submitBtn').addEventListener('click', confirmSubmit);
            document.getElementById('navToggleBtn').addEventListener('click', toggleNavPanel);
            document.getElementById('navCloseBtn').addEventListener('click', toggleNavPanel);
            document.getElementById('reviewBtn').addEventListener('click', reviewAnswers);
            document.getElementById('restartBtn').addEventListener('click', restartQuiz);
            document.getElementById('themeToggle').addEventListener('click', toggleTheme);
            
            // Keyboard navigation
            document.addEventListener('keydown', (e) => {{
                if (state.isSubmitted) return;
                if (e.key === 'ArrowLeft') navigatePrev();
                if (e.key === 'ArrowRight') navigateNext();
            }});
        }}
        
        function navigatePrev() {{
            if (state.currentQuestion > 0) {{
                renderQuestion(state.currentQuestion - 1);
            }}
        }}
        
        function navigateNext() {{
            if (state.currentQuestion < quizData.questions.length - 1) {{
                renderQuestion(state.currentQuestion + 1);
            }}
        }}
        
        function toggleMark() {{
            state.marked[state.currentQuestion] = !state.marked[state.currentQuestion];
            updateQuestionGrid();
            
            const markBtn = document.getElementById('markBtn');
            if (state.marked[state.currentQuestion]) {{
                markBtn.innerHTML = '<i class="fas fa-bookmark"></i> Unmark';
            }} else {{
                markBtn.innerHTML = '<i class="fas fa-bookmark"></i> Mark';
            }}
        }}
        
        function updateNavButtons() {{
            document.getElementById('prevBtn').disabled = state.currentQuestion === 0;
            
            if (state.currentQuestion === quizData.questions.length - 1) {{
                document.getElementById('nextBtn').style.display = 'none';
                document.getElementById('submitBtn').style.display = 'flex';
            }} else {{
                document.getElementById('nextBtn').style.display = 'flex';
                document.getElementById('submitBtn').style.display = 'none';
            }}
            
            const markBtn = document.getElementById('markBtn');
            if (state.marked[state.currentQuestion]) {{
                markBtn.innerHTML = '<i class="fas fa-bookmark"></i> Unmark';
            }} else {{
                markBtn.innerHTML = '<i class="fas fa-bookmark"></i> Mark';
            }}
        }}
        
        function updateProgress() {{
            const attempted = state.answers.filter(a => a !== null).length;
            const progress = ((state.currentQuestion + 1) / quizData.questions.length) * 100;
            
            document.getElementById('progressText').textContent = 
                `Question ${{state.currentQuestion + 1}} of ${{quizData.questions.length}}`;
            document.getElementById('attemptedText').textContent = 
                `Attempted: ${{attempted}}/${{quizData.questions.length}}`;
            document.getElementById('progressBar').style.width = progress + '%';
        }}
        
        // Question Grid
        function renderQuestionGrid() {{
            const grid = document.getElementById('questionGrid');
            grid.innerHTML = '';
            
            quizData.questions.forEach((_, index) => {{
                const item = document.createElement('div');
                item.className = 'question-nav-item';
                item.textContent = index + 1;
                item.onclick = () => {{
                    renderQuestion(index);
                    if (window.innerWidth < 768) {{
                        toggleNavPanel();
                    }}
                }};
                grid.appendChild(item);
            }});
        }}
        
        function updateQuestionGrid() {{
            const items = document.querySelectorAll('.question-nav-item');
            items.forEach((item, index) => {{
                item.className = 'question-nav-item';
                
                if (index === state.currentQuestion) {{
                    item.classList.add('current');
                }}
                
                if (state.isSubmitted) {{
                    if (state.answers[index] === quizData.questions[index].correctIndex) {{
                        item.classList.add('correct');
                    }} else if (state.answers[index] !== null) {{
                        item.classList.add('incorrect');
                    }}
                }} else {{
                    if (state.answers[index] !== null) {{
                        item.classList.add('answered');
                    }}
                    if (state.marked[index]) {{
                        item.classList.add('marked');
                    }}
                }}
            }});
        }}
        
        function toggleNavPanel() {{
            document.getElementById('navPanel').classList.toggle('open');
        }}
        
        // Submit Quiz
        function confirmSubmit() {{
            const unattempted = state.answers.filter(a => a === null).length;
            if (unattempted > 0) {{
                const confirm = window.confirm(
                    `You have ${{unattempted}} unattempted question(s). Do you want to submit?`
                );
                if (!confirm) return;
            }}
            submitQuiz();
        }}
        
        function submitQuiz() {{
            clearInterval(state.timerInterval);
            state.isSubmitted = true;
            
            // Calculate results
            let correct = 0, incorrect = 0, unattempted = 0, negativeMarks = 0;
            
            state.answers.forEach((answer, index) => {{
                if (answer === null) {{
                    unattempted++;
                }} else if (answer === quizData.questions[index].correctIndex) {{
                    correct++;
                }} else {{
                    incorrect++;
                    negativeMarks += quizData.negativeMark;
                }}
            }});
            
            const totalScore = correct - negativeMarks;
            const percentage = (totalScore / quizData.questions.length) * 100;
            
            // Disable page lock - enable scrolling for results
            document.body.style.overflow = 'auto';
            
            // Show results
            document.getElementById('quizContainer').style.display = 'none';
            document.getElementById('resultsContainer').style.display = 'block';
            document.getElementById('resultsContainer').classList.add('scrollable');
            
            // Set results
            if (percentage >= 70) {{
                document.getElementById('resultsIcon').innerHTML = '<i class="fas fa-trophy" style="color: #fbbf24;"></i>';
                document.getElementById('resultsTitle').textContent = 'Excellent Performance!';
            }} else if (percentage >= 50) {{
                document.getElementById('resultsIcon').innerHTML = '<i class="far fa-smile" style="color: #48bb78;"></i>';
                document.getElementById('resultsTitle').textContent = 'Good Job!';
            }} else {{
                document.getElementById('resultsIcon').innerHTML = '<i class="far fa-meh" style="color: #f5576c;"></i>';
                document.getElementById('resultsTitle').textContent = 'Keep Practicing!';
            }}
            
            document.getElementById('resultsScore').textContent = totalScore.toFixed(2) + ' / ' + quizData.questions.length;
            document.getElementById('resultsPercentage').textContent = percentage.toFixed(1) + '%';
            document.getElementById('correctCount').textContent = correct;
            document.getElementById('incorrectCount').textContent = incorrect;
            document.getElementById('unattemptedCount').textContent = unattempted;
            document.getElementById('negativeMarks').textContent = '-' + negativeMarks.toFixed(2);
        }}
        
        function reviewAnswers() {{
            state.isReviewMode = true;
            
            // Re-enable page lock for review mode
            document.body.style.overflow = 'hidden';
            
            document.getElementById('resultsContainer').style.display = 'none';
            document.getElementById('quizContainer').style.display = 'block';
            renderQuestion(0);
            updateQuestionGrid();
        }}
        
        function restartQuiz() {{
            // Re-enable page lock
            document.body.style.overflow = 'hidden';
            location.reload();
        }}
    </script>
</body>
</html>"""

    # Save and send HTML file
    quiz_file_name = f"{uuid.uuid4().hex}.html"
    with open(quiz_file_name, "w", encoding="utf-8") as file:
        file.write(html_content)
        
    with open(quiz_file_name, "rb") as file:
        await context.bot.send_document(
            chat_id=chat_id,
            document=file,
            caption=f"{quiz['quiz_name']}",
            protect_content=type
        )

    # Cleanup
    import os
    os.remove(quiz_file_name)


async def generate_quiz_html2(quiz, chat_id, context, ParseMode, type):
    """Premium Quiz HTML Generator - Mobile + Desktop CBT Platform"""
    
    def je(t):
        """JS escape"""
        if not t: return ""
        t = str(t)
        return t.replace('\\','\\\\').replace('"','\\"').replace("'","\\'").replace('\n','\\n').replace('\r','\\r').replace('\t','\\t')
    
    # Quiz metadata
    qn = re.sub(r"[^a-zA-Z0-9_-]", "", unidecode(quiz["quiz_name"]).replace(" ", "_"))[:100] + ".html"
    mm = len(quiz["questions"])
    nm = quiz.get("negative_marks", 0.25)
    dt = quiz.get("timer", 60) * len(quiz["questions"])
    
    # Build questions JS
    qjs = []
    for i, q in enumerate(quiz["questions"]):
        opts = q["options"].copy()
        co = opts[q["correct_option_id"]]
        random.shuffle(opts)
        qjs.append(f'''{{id:{i},txt:"{je(q["question"])}",ref:"{je(q.get("reply_text",""))}",opts:{json.dumps(opts)},ci:{opts.index(co)},exp:"{je(q.get("explanation","No explanation"))}"}}''')
    
    # Desktop CBT Styles
    dsk_css = """
    @media (min-width: 1024px) {
        body { overflow: auto !important; }
        
        #quizContainer {
            display: grid !important;
            grid-template-columns: 1fr 320px;
            grid-template-rows: auto 1fr auto;
            gap: 0;
            height: 100vh;
            overflow: hidden;
        }
        
        .quiz-header {
            grid-column: 1 / -1;
            position: static;
            padding: 20px 32px;
            border-bottom: 3px solid var(--border);
        }
        
        .header-top {
            max-width: none;
            margin-bottom: 16px;
        }
        
        .quiz-title-text { max-width: 400px; }
        
        .timer-display {
            padding: 10px 20px;
            font-size: 18px;
        }
        
        /* Main content area - scrollable */
        .question-section {
            position: static !important;
            grid-column: 1;
            grid-row: 2;
            overflow-y: auto;
            padding: 32px;
            background: var(--bg-light);
            top: auto !important;
            bottom: auto !important;
        }
        
        .question-card {
            max-width: 900px;
            padding: 32px;
            margin: 0 auto 24px;
        }
        
        .question-text {
            font-size: 18px;
            margin-bottom: 24px;
        }
        
        .option-btn {
            padding: 18px 20px;
            font-size: 16px;
        }
        
        .option-indicator {
            min-width: 32px;
            height: 32px;
            font-size: 14px;
        }
        
        /* Desktop Question Navigator - Right Panel */
        .question-nav-panel {
            position: static !important;
            grid-column: 2;
            grid-row: 2;
            transform: none !important;
            max-height: none;
            height: 100%;
            border-radius: 0;
            border-left: 3px solid var(--border);
            box-shadow: none;
            padding: 24px;
            overflow-y: auto;
            background: var(--bg-white);
        }
        
        .question-nav-panel.open { transform: none !important; }
        
        .nav-panel-header {
            position: sticky;
            top: 0;
            background: var(--bg-white);
            z-index: 10;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        
        .nav-panel-title {
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .nav-close-btn { display: none; }
        
        .nav-legend {
            position: sticky;
            top: 60px;
            background: var(--bg-white);
            z-index: 9;
            padding: 16px;
            margin: -16px -16px 20px;
            border-radius: 12px;
            background: var(--bg-light);
        }
        
        .question-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }
        
        .question-nav-item {
            aspect-ratio: 1;
            font-size: 16px;
            border-radius: 12px;
        }
        
        .question-nav-toggle { display: none; }
        
        /* Footer Navigation - Sticky */
        .nav-controls {
            position: static;
            grid-column: 1;
            grid-row: 3;
            padding: 20px 32px;
            border-top: 3px solid var(--border);
            max-width: none;
            display: flex;
            justify-content: center;
            gap: 16px;
        }
        
        .nav-btn {
            min-width: 160px;
            padding: 16px 24px;
            font-size: 16px;
        }
        
        /* Results Desktop Layout */
        #resultsContainer {
            padding: 40px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .results-header {
            padding: 60px 40px;
            margin-bottom: 32px;
        }
        
        .results-icon { font-size: 100px; }
        .results-title { font-size: 36px; }
        .results-score { font-size: 64px; }
        .results-percentage { font-size: 24px; }
        
        .stats-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 32px;
            max-width: none;
        }
        
        .stat-card { padding: 32px; }
        .stat-icon { width: 54px; height: 54px; font-size: 24px; }
        .stat-value { font-size: 40px; }
        .stat-label { font-size: 14px; }
        
        .action-buttons {
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            max-width: 800px;
        }
        
        .action-btn { padding: 20px; font-size: 17px; }
        
        /* Mode Selection Desktop */
        .mode-container {
            max-width: 600px;
            padding: 50px 40px;
        }
        
        .mode-header-icon {
            width: 80px;
            height: 80px;
            font-size: 40px;
        }
        
        .mode-header h2 { font-size: 28px; }
        .mode-header p { font-size: 15px; }
        
        .mode-cards { gap: 20px; }
        
        .mode-card {
            padding: 24px;
            border-radius: 18px;
        }
        
        .mode-icon {
            width: 60px;
            height: 60px;
            font-size: 28px;
            margin-right: 20px;
        }
        
        .mode-info h3 { font-size: 19px; }
        .mode-info p { font-size: 14px; }
        
        .timer-input { padding: 16px 18px; font-size: 16px; }
        .start-btn { padding: 18px; font-size: 17px; }
    }
    
    /* Ultra-wide Desktop */
    @media (min-width: 1440px) {
        #quizContainer {
            grid-template-columns: 1fr 380px;
        }
        
        .question-section { padding: 40px 60px; }
        .question-card { max-width: 1000px; padding: 40px; }
        .question-nav-panel { padding: 32px; }
        .question-grid { grid-template-columns: repeat(5, 1fr); }
        .nav-controls { padding: 24px 60px; }
    }
    """
    
    # Main HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{quiz['quiz_name']}</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
:root{{--primary:#667eea;--primary-dark:#5568d3;--secondary:#764ba2;--success:#48bb78;--danger:#f5576c;--warning:#fbbf24;--info:#4facfe;--bg-light:#f7fafc;--bg-white:#fff;--text-dark:#1a202c;--text-light:#718096;--border:#e2e8f0}}
[data-theme="dark"]{{--bg-light:#1a202c;--bg-white:#2d3748;--text-dark:#f7fafc;--text-light:#cbd5e0;--border:#4a5568}}
body{{font-family:'Poppins',-apple-system,BlinkMacSystemFont,sans-serif;background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);min-height:100vh;overflow:hidden;user-select:none;-webkit-user-select:none;transition:background .3s}}
.scrollable::-webkit-scrollbar{{width:6px}}
.scrollable::-webkit-scrollbar-track{{background:transparent}}
.scrollable::-webkit-scrollbar-thumb{{background:var(--primary);border-radius:10px}}
.protected-content{{white-space:pre-wrap;word-wrap:break-word;word-break:break-word;line-height:1.6;user-select:none}}
#modeSelection{{position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;align-items:center;justify-content:center;z-index:9999;padding:20px;overflow-y:auto}}
.mode-container{{background:#fff;border-radius:24px;padding:40px 30px;max-width:500px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.3);animation:ms .5s cubic-bezier(.34,1.56,.64,1)}}
@keyframes ms{{from{{opacity:0;transform:translateY(40px) scale(.95)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
.mode-header{{text-align:center;margin-bottom:32px}}
.mode-header-icon{{width:70px;height:70px;margin:0 auto 16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:36px;color:#fff;box-shadow:0 8px 24px rgba(102,126,234,.3)}}
.mode-header h2{{font-size:24px;font-weight:700;color:#1a202c;margin-bottom:8px}}
.mode-header p{{font-size:14px;color:#718096;font-weight:400}}
.mode-cards{{display:grid;gap:16px;margin-bottom:24px}}
.mode-card{{background:#f7fafc;border:2px solid #e2e8f0;border-radius:16px;padding:20px;cursor:pointer;transition:all .3s;position:relative}}
.mode-card:hover{{transform:translateY(-3px);box-shadow:0 12px 28px rgba(102,126,234,.15);border-color:#cbd5e0}}
.mode-card.selected{{border-color:#667eea;background:#fff;box-shadow:0 8px 24px rgba(102,126,234,.2);transform:translateY(-2px)}}
.mode-card-header{{display:flex;align-items:center}}
.mode-icon{{width:54px;height:54px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;margin-right:16px;flex-shrink:0}}
.exam-mode .mode-icon{{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:#fff}}
.practice-mode .mode-icon{{background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:#fff}}
.mode-info h3{{font-size:17px;font-weight:700;color:#1a202c;margin-bottom:4px}}
.mode-info p{{font-size:13px;color:#718096;line-height:1.4}}
.timer-config{{margin-bottom:24px}}
.timer-config label{{display:block;font-size:14px;font-weight:600;color:#1a202c;margin-bottom:10px}}
.timer-config label i{{margin-right:6px;color:#667eea}}
.timer-input{{width:100%;padding:14px 16px;border:2px solid #e2e8f0;border-radius:12px;font-size:15px;font-weight:500;transition:all .3s;background:#fff;font-family:'Poppins',sans-serif;color:#1a202c}}
.timer-input::placeholder{{color:#a0aec0}}
.timer-input:focus{{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.1)}}
.start-btn{{width:100%;padding:16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;border-radius:14px;font-size:16px;font-weight:700;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;gap:10px;box-shadow:0 8px 20px rgba(102,126,234,.35)}}
.start-btn:hover:not(:disabled){{transform:translateY(-2px);box-shadow:0 12px 28px rgba(102,126,234,.45)}}
.start-btn:active:not(:disabled){{transform:translateY(0)}}
.start-btn:disabled{{opacity:.5;cursor:not-allowed;background:#cbd5e0;box-shadow:none}}
#quizContainer{{display:none;position:fixed;top:0;left:0;width:100%;height:100vh;background:var(--bg-light);overflow:hidden}}
.quiz-header{{position:fixed;top:0;left:0;right:0;background:var(--bg-white);box-shadow:0 2px 15px rgba(0,0,0,.08);z-index:100;padding:16px 20px}}
.header-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:10px}}
.quiz-title{{font-size:15px;font-weight:700;color:var(--text-dark);display:flex;align-items:center;gap:8px;flex:1;min-width:0}}
.quiz-title-text{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px}}
.mode-badge{{font-size:10px;padding:4px 10px;border-radius:20px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}}
.mode-badge.exam{{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:#fff}}
.mode-badge.practice{{background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:#fff}}
.header-actions{{display:flex;gap:8px;align-items:center}}
.theme-toggle{{width:36px;height:36px;background:var(--bg-light);border:none;border-radius:10px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;color:var(--text-dark);transition:all .3s}}
.theme-toggle:hover{{transform:scale(1.1)}}
.timer-display{{display:flex;align-items:center;gap:8px;font-size:16px;font-weight:700;color:var(--primary);padding:8px 14px;background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);border-radius:12px;white-space:nowrap}}
.timer-display.warning{{color:var(--danger);background:linear-gradient(135deg,rgba(245,87,108,.15) 0%,rgba(240,147,251,.15) 100%);animation:pulse 1s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
.header-progress{{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--text-light);margin-bottom:8px}}
.progress-bar-container{{height:6px;background:var(--border);border-radius:10px;overflow:hidden}}
.progress-bar{{height:100%;background:linear-gradient(90deg,var(--primary) 0%,var(--secondary) 100%);transition:width .3s;border-radius:10px}}
.question-section{{position:fixed;top:140px;left:0;right:0;bottom:80px;overflow-y:auto;overflow-x:hidden;padding:20px;-webkit-overflow-scrolling:touch}}
.question-section.scrollable{{scrollbar-width:thin;scrollbar-color:var(--primary) transparent}}
.question-card{{background:var(--bg-white);border-radius:20px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,.06);max-width:800px;margin:0 auto}}
.question-number{{display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:700;color:var(--primary);background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);padding:6px 14px;border-radius:20px;margin-bottom:16px}}
.question-reference{{background:linear-gradient(135deg,rgba(79,172,254,.15) 0%,rgba(0,242,254,.15) 100%);border-left:4px solid var(--info);padding:14px 16px;border-radius:10px;margin-bottom:16px;font-size:14px;color:var(--text-dark);line-height:1.6;white-space:pre-wrap;word-wrap:break-word}}
.question-text{{font-size:16px;font-weight:600;color:var(--text-dark);line-height:1.7;margin-bottom:20px;white-space:pre-wrap;word-wrap:break-word;word-break:break-word}}
.options-container{{display:grid;gap:12px}}
.option-btn{{width:100%;padding:16px 18px;background:var(--bg-light);border:3px solid var(--border);border-radius:14px;text-align:left;font-size:15px;color:var(--text-dark);cursor:pointer;transition:all .3s;display:flex;align-items:flex-start;gap:12px;line-height:1.6;white-space:pre-wrap;word-wrap:break-word;word-break:break-word;user-select:none}}
.option-btn:active{{transform:scale(.98)}}
.option-indicator{{min-width:28px;height:28px;border-radius:50%;background:var(--bg-white);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;transition:all .3s}}
.option-text{{flex:1;padding-top:3px}}
.option-btn:hover:not(.disabled){{border-color:var(--primary);transform:translateX(4px)}}
.option-btn.selected{{background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);border-color:var(--primary)}}
.option-btn.selected .option-indicator{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff;border-color:transparent}}
.option-btn.correct{{background:linear-gradient(135deg,rgba(72,187,120,.15) 0%,rgba(72,187,120,.15) 100%);border-color:var(--success)}}
.option-btn.correct .option-indicator{{background:var(--success);color:#fff;border-color:transparent}}
.option-btn.incorrect{{background:linear-gradient(135deg,rgba(245,87,108,.15) 0%,rgba(245,87,108,.15) 100%);border-color:var(--danger)}}
.option-btn.incorrect .option-indicator{{background:var(--danger);color:#fff;border-color:transparent}}
.option-btn.disabled{{pointer-events:none;opacity:.6}}
.explanation-box{{display:none;background:linear-gradient(135deg,rgba(254,245,231,.5) 0%,rgba(251,191,36,.2) 100%);border-left:4px solid var(--warning);border-radius:12px;padding:16px;margin-top:20px;animation:sd .3s ease-out}}
@keyframes sd{{from{{opacity:0;max-height:0;padding:0}}to{{opacity:1;max-height:500px;padding:16px}}}}
.explanation-header{{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:700;color:#92400e;margin-bottom:10px}}
.explanation-text{{font-size:14px;color:#78350f;line-height:1.6;white-space:pre-wrap;word-wrap:break-word}}
[data-theme="dark"] .explanation-text{{color:#fbbf24}}
.nav-controls{{position:fixed;bottom:0;left:0;right:0;background:var(--bg-white);padding:16px 20px;box-shadow:0 -2px 15px rgba(0,0,0,.08);display:flex;gap:12px;z-index:90}}
.nav-btn{{flex:1;padding:14px;border:none;border-radius:12px;font-size:15px;font-weight:600;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;gap:8px}}
.nav-btn.primary{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff}}
.nav-btn.secondary{{background:var(--bg-light);color:var(--text-dark);border:2px solid var(--border)}}
.nav-btn:active{{transform:scale(.96)}}
.nav-btn:disabled{{opacity:.5;cursor:not-allowed;transform:none}}
.question-nav-toggle{{position:fixed;bottom:100px;right:20px;width:56px;height:56px;background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff;border:none;border-radius:50%;font-size:22px;cursor:pointer;box-shadow:0 8px 20px rgba(102,126,234,.4);z-index:85;transition:all .3s}}
.question-nav-toggle:active{{transform:scale(.95)}}
.question-nav-panel{{position:fixed;bottom:0;left:0;right:0;background:var(--bg-white);border-radius:24px 24px 0 0;box-shadow:0 -4px 30px rgba(0,0,0,.15);z-index:95;max-height:70vh;overflow-y:auto;transform:translateY(100%);transition:transform .3s;padding:20px}}
.question-nav-panel.open{{transform:translateY(0)}}
.nav-panel-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:16px;border-bottom:2px solid var(--border)}}
.nav-panel-title{{font-size:18px;font-weight:700;color:var(--text-dark)}}
.nav-close-btn{{width:32px;height:32px;background:var(--bg-light);border:none;border-radius:50%;font-size:16px;cursor:pointer;color:var(--text-light)}}
.nav-legend{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:20px;font-size:12px;color:var(--text-dark)}}
.legend-item{{display:flex;align-items:center;gap:6px;color:var(--text-dark)}}
.legend-box{{width:20px;height:20px;border-radius:6px}}
.legend-box.answered{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%)}}
.legend-box.marked{{background:linear-gradient(135deg,var(--warning) 0%,#f59e0b 100%)}}
.legend-box.unanswered{{background:var(--border)}}
.question-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.question-nav-item{{aspect-ratio:1;border:2px solid var(--border);border-radius:10px;background:var(--bg-white);display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:600;cursor:pointer;transition:all .3s;color:var(--text-light)}}
.question-nav-item:active{{transform:scale(.95)}}
.question-nav-item.current{{border-color:var(--primary);background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);color:var(--primary)}}
.question-nav-item.answered{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff;border-color:transparent}}
.question-nav-item.marked{{background:linear-gradient(135deg,var(--warning) 0%,#f59e0b 100%);color:#fff;border-color:transparent}}
.question-nav-item.correct{{background:linear-gradient(135deg,var(--success) 0%,#38a169 100%);color:#fff;border-color:transparent}}
.question-nav-item.incorrect{{background:linear-gradient(135deg,var(--danger) 0%,#e53e3e 100%);color:#fff;border-color:transparent}}
#resultsContainer{{display:none;position:fixed;top:0;left:0;width:100%;height:100vh;background:var(--bg-light);overflow-y:auto;overflow-x:hidden;padding:20px;z-index:1000}}
#resultsContainer.scrollable{{scrollbar-width:thin;scrollbar-color:var(--primary) transparent}}
.results-header{{text-align:center;padding:40px 20px;background:var(--bg-white);border-radius:20px;margin-bottom:20px;box-shadow:0 4px 20px rgba(0,0,0,.06)}}
.results-icon{{font-size:80px;margin-bottom:20px}}
.results-title{{font-size:28px;font-weight:700;color:var(--text-dark);margin-bottom:10px}}
.results-score{{font-size:52px;font-weight:800;background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}}
.results-percentage{{font-size:20px;color:var(--text-light);font-weight:600}}
.stats-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px;max-width:800px;margin-left:auto;margin-right:auto}}
.stat-card{{background:var(--bg-white);padding:24px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.06)}}
.stat-icon{{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;margin-bottom:12px}}
.stat-icon.correct{{background:linear-gradient(135deg,var(--success) 0%,#38a169 100%);color:#fff}}
.stat-icon.incorrect{{background:linear-gradient(135deg,var(--danger) 0%,#e53e3e 100%);color:#fff}}
.stat-icon.unattempted{{background:linear-gradient(135deg,#a0aec0 0%,#718096 100%);color:#fff}}
.stat-icon.negative{{background:linear-gradient(135deg,#ed8936 0%,#dd6b20 100%);color:#fff}}
.stat-value{{font-size:32px;font-weight:700;color:var(--text-dark);margin-bottom:4px}}
.stat-label{{font-size:13px;color:var(--text-light);font-weight:500}}
.action-buttons{{display:grid;gap:12px;max-width:800px;margin:0 auto}}
.action-btn{{width:100%;padding:18px;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px;transition:all .3s}}
.action-btn.primary{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff}}
.action-btn.secondary{{background:var(--bg-white);color:var(--text-dark);border:2px solid var(--border)}}
.action-btn:hover{{transform:translateY(-2px)}}
{dsk_css}
</style>
</head>
<body>
<div id="modeSelection">
<div class="mode-container">
<div class="mode-header">
<div class="mode-header-icon"><i class="fas fa-graduation-cap"></i></div>
<h2>{quiz['quiz_name']}</h2>
<p>Choose your preferred test mode</p>
</div>
<div class="mode-cards">
<div class="mode-card exam-mode" data-mode="exam">
<div class="mode-card-header">
<div class="mode-icon"><i class="fas fa-file-alt"></i></div>
<div class="mode-info">
<h3>Exam Mode</h3>
<p>Complete all questions, results shown after submission</p>
</div>
</div>
</div>
<div class="mode-card practice-mode" data-mode="practice">
<div class="mode-card-header">
<div class="mode-icon"><i class="fas fa-book-open"></i></div>
<div class="mode-info">
<h3>Practice Mode</h3>
<p>Instant feedback with detailed explanations</p>
</div>
</div>
</div>
</div>
<div class="timer-config">
<label for="ct"><i class="fas fa-clock"></i> Custom Timer (minutes)</label>
<input type="number" id="ct" class="timer-input" placeholder="Default: {int(dt/60)} minutes" min="1" max="300"/>
</div>
<button class="start-btn" id="sb" disabled><i class="fas fa-play-circle"></i><span>Start Quiz</span></button>
</div>
</div>
<div id="quizContainer">
<div class="quiz-header">
<div class="header-top">
<div class="quiz-title">
<i class="fas fa-clipboard-list"></i>
<span class="quiz-title-text" title="{quiz['quiz_name']}">{quiz['quiz_name']}</span>
<span class="mode-badge" id="mb"></span>
</div>
<div class="header-actions">
<button class="theme-toggle" id="tt" title="Toggle Dark Mode"><i class="fas fa-moon"></i></button>
<div class="timer-display" id="td"><i class="fas fa-clock"></i><span id="tt2">00:00</span></div>
</div>
</div>
<div class="header-progress">
<span id="pt">Question 1 of {mm}</span>
<span id="at">Attempted: 0/{mm}</span>
</div>
<div class="progress-bar-container"><div class="progress-bar" id="pb"></div></div>
</div>
<div class="question-section scrollable" id="qs"></div>
<div class="nav-controls">
<button class="nav-btn secondary" id="pv"><i class="fas fa-chevron-left"></i>Previous</button>
<button class="nav-btn secondary" id="mk"><i class="fas fa-bookmark"></i>Mark</button>
<button class="nav-btn primary" id="nx">Next<i class="fas fa-chevron-right"></i></button>
<button class="nav-btn primary" id="sm" style="display:none"><i class="fas fa-paper-plane"></i>Submit</button>
</div>
<button class="question-nav-toggle" id="nt"><i class="fas fa-th"></i></button>
<div class="question-nav-panel" id="np">
<div class="nav-panel-header">
<h3 class="nav-panel-title"><i class="fas fa-map-marked-alt"></i> Question Navigator</h3>
<button class="nav-close-btn" id="nc"><i class="fas fa-times"></i></button>
</div>
<div class="nav-legend">
<div class="legend-item"><div class="legend-box answered"></div><span>Answered</span></div>
<div class="legend-item"><div class="legend-box marked"></div><span>Marked</span></div>
<div class="legend-item"><div class="legend-box unanswered"></div><span>Not Answered</span></div>
</div>
<div class="question-grid" id="qg"></div>
</div>
</div>
<div id="resultsContainer">
<div class="results-header">
<div class="results-icon" id="ri"></div>
<h2 class="results-title" id="rt"></h2>
<div class="results-score" id="rs"></div>
<div class="results-percentage" id="rp"></div>
</div>
<div class="stats-grid">
<div class="stat-card"><div class="stat-icon correct"><i class="fas fa-check"></i></div><div class="stat-value" id="cc">0</div><div class="stat-label">Correct</div></div>
<div class="stat-card"><div class="stat-icon incorrect"><i class="fas fa-times"></i></div><div class="stat-value" id="ic">0</div><div class="stat-label">Incorrect</div></div>
<div class="stat-card"><div class="stat-icon unattempted"><i class="fas fa-minus"></i></div><div class="stat-value" id="uc">0</div><div class="stat-label">Unattempted</div></div>
<div class="stat-card"><div class="stat-icon negative"><i class="fas fa-exclamation-triangle"></i></div><div class="stat-value" id="nm">0</div><div class="stat-label">Negative Marks</div></div>
</div>
<div class="action-buttons">
<button class="action-btn primary" id="rb"><i class="fas fa-search"></i>Review Answers</button>
<button class="action-btn secondary" id="rsb"><i class="fas fa-redo"></i>Restart Quiz</button>
</div>
</div>
<script>
const qd={{q:[{",".join(qjs)}],m:null,tt:{dt},nm:{nm}}},
st={{cq:0,a:Array(qd.q.length).fill(null),mk:Array(qd.q.length).fill(false),tr:qd.tt,ti:null,sb:false,rv:false,th:'light'}};
document.addEventListener('DOMContentLoaded',()=>{{sms();pcc();lt()}});
function lt(){{const t=localStorage.getItem('qt')||'light';st.th=t;document.documentElement.setAttribute('data-theme',t);uti()}}
function tgt(){{st.th=st.th==='light'?'dark':'light';document.documentElement.setAttribute('data-theme',st.th);localStorage.setItem('qt',st.th);uti()}}
function uti(){{const i=document.querySelector('#tt i');if(i)i.className=st.th==='light'?'fas fa-moon':'fas fa-sun'}}
function pcc(){{document.addEventListener('contextmenu',e=>e.preventDefault());document.addEventListener('copy',e=>e.preventDefault());document.addEventListener('cut',e=>e.preventDefault());document.addEventListener('selectstart',e=>{{if(!e.target.tagName.match(/INPUT|TEXTAREA/i))e.preventDefault()}})}}
function sms(){{const mc=document.querySelectorAll('.mode-card'),sb=document.getElementById('sb');mc.forEach(c=>{{c.addEventListener('click',()=>{{mc.forEach(x=>x.classList.remove('selected'));c.classList.add('selected');qd.m=c.dataset.mode;sb.disabled=false}})}});sb.addEventListener('click',sq)}}
function sq(){{const ct=document.getElementById('ct'),ctv=parseInt(ct.value);if(ctv&&ctv>0){{st.tr=ctv*60;qd.tt=ctv*60}}document.body.style.overflow='hidden';document.getElementById('modeSelection').style.display='none';document.getElementById('quizContainer').style.display='block';document.getElementById('mb').textContent=qd.m;document.getElementById('mb').className='mode-badge '+qd.m;iq()}}
function iq(){{rq(0);rqg();stt();sn()}}
function stt(){{utd();st.ti=setInterval(()=>{{st.tr--;utd();if(st.tr<=0){{clearInterval(st.ti);sbq()}}if(st.tr<=60)document.getElementById('td').classList.add('warning')}},1000)}}
function utd(){{const m=Math.floor(st.tr/60),s=st.tr%60;document.getElementById('tt2').textContent=`${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`}}
function rq(i){{st.cq=i;const q=qd.q[i],qs=document.getElementById('qs');let h=`<div class="question-card"><div class="question-number"><i class="fas fa-question-circle"></i>Question ${{i+1}} of ${{qd.q.length}}</div>`;if(q.ref)h+=`<div class="question-reference protected-content"><i class="fas fa-info-circle"></i> ${{q.ref}}</div>`;h+=`<div class="question-text protected-content">${{q.txt}}</div><div class="options-container">`;q.opts.forEach((o,x)=>{{let bc='option-btn',ic=String.fromCharCode(65+x);const isSel=st.a[i]===x,isCor=x===q.ci,shAns=(qd.m==='practice'&&st.a[i]!==null)||st.sb;if(isSel)bc+=' selected';if(shAns){{bc+=' disabled';if(isCor){{bc+=' correct';ic='<i class="fas fa-check"></i>'}}else if(isSel&&!isCor){{bc+=' incorrect';ic='<i class="fas fa-times"></i>'}}}}h+=`<button class="${{bc}}" data-index="${{x}}" onclick="so(${{x}})"><div class="option-indicator">${{ic}}</div><div class="option-text protected-content">${{o}}</div></button>`}});h+=`</div>`;const shExp=(qd.m==='practice'&&st.a[i]!==null)||st.sb;if(shExp)h+=`<div class="explanation-box" style="display:block"><div class="explanation-header"><i class="fas fa-lightbulb"></i>Explanation</div><div class="explanation-text protected-content">${{q.exp}}</div></div>`;h+=`</div>`;qs.innerHTML=h;qs.scrollTop=0;up();unb();uqg()}}
function so(oi){{if(st.sb)return;if(st.a[st.cq]===oi){{st.a[st.cq]=null}}else{{st.a[st.cq]=oi}}rq(st.cq)}}
function sn(){{document.getElementById('pv').addEventListener('click',np);document.getElementById('nx').addEventListener('click',nn);document.getElementById('mk').addEventListener('click',tm);document.getElementById('sm').addEventListener('click',cs);document.getElementById('nt').addEventListener('click',tnp);document.getElementById('nc').addEventListener('click',tnp);document.getElementById('rb').addEventListener('click',ra);document.getElementById('rsb').addEventListener('click',rs);document.getElementById('tt').addEventListener('click',tgt);document.addEventListener('keydown',e=>{{if(st.sb)return;if(e.key==='ArrowLeft')np();if(e.key==='ArrowRight')nn()}})}}
function np(){{if(st.cq>0)rq(st.cq-1)}}
function nn(){{if(st.cq<qd.q.length-1)rq(st.cq+1)}}
function tm(){{st.mk[st.cq]=!st.mk[st.cq];uqg();const mb=document.getElementById('mk');mb.innerHTML=st.mk[st.cq]?'<i class="fas fa-bookmark"></i> Unmark':'<i class="fas fa-bookmark"></i> Mark'}}
function unb(){{document.getElementById('pv').disabled=st.cq===0;if(st.cq===qd.q.length-1){{document.getElementById('nx').style.display='none';document.getElementById('sm').style.display='flex'}}else{{document.getElementById('nx').style.display='flex';document.getElementById('sm').style.display='none'}}const mb=document.getElementById('mk');mb.innerHTML=st.mk[st.cq]?'<i class="fas fa-bookmark"></i> Unmark':'<i class="fas fa-bookmark"></i> Mark'}}
function up(){{const at=st.a.filter(a=>a!==null).length,pr=((st.cq+1)/qd.q.length)*100;document.getElementById('pt').textContent=`Question ${{st.cq+1}} of ${{qd.q.length}}`;document.getElementById('at').textContent=`Attempted: ${{at}}/${{qd.q.length}}`;document.getElementById('pb').style.width=pr+'%'}}
function rqg(){{const g=document.getElementById('qg');g.innerHTML='';qd.q.forEach((_,i)=>{{const it=document.createElement('div');it.className='question-nav-item';it.textContent=i+1;it.onclick=()=>{{rq(i);if(window.innerWidth<768)tnp()}};g.appendChild(it)}})}}
function uqg() {{
    const its = document.querySelectorAll('.question-nav-item');
    its.forEach((it, i) => {{
        it.className = 'question-nav-item';
        if (i === st.cq) it.classList.add('current');
        if (st.sb) {{
            if (st.a[i] === qd.q[i].ci) it.classList.add('correct');
            else if (st.a[i] !== null) it.classList.add('incorrect');
        }} else {{
            if (st.a[i] !== null) it.classList.add('answered');
            if (st.mk[i]) it.classList.add('marked');
        }}
    }});
}}
function tnp(){{document.getElementById('np').classList.toggle('open')}}
function cs(){{const u=st.a.filter(a=>a===null).length;if(u>0){{const c=window.confirm(`You have ${{u}} unattempted question(s). Do you want to submit?`);if(!c)return}}sbq()}}
function sbq(){{clearInterval(st.ti);st.sb=true;let c=0,ic=0,u=0,nm=0;st.a.forEach((a,i)=>{{if(a===null)u++;else if(a===qd.q[i].ci)c++;else{{ic++;nm+=qd.nm}}}});const ts=c-nm,pc=(ts/qd.q.length)*100;document.body.style.overflow='auto';document.getElementById('quizContainer').style.display='none';document.getElementById('resultsContainer').style.display='block';document.getElementById('resultsContainer').classList.add('scrollable');if(pc>=70){{document.getElementById('ri').innerHTML='<i class="fas fa-trophy" style="color:#fbbf24"></i>';document.getElementById('rt').textContent='Excellent Performance!'}}else if(pc>=50){{document.getElementById('ri').innerHTML='<i class="far fa-smile" style="color:#48bb78"></i>';document.getElementById('rt').textContent='Good Job!'}}else{{document.getElementById('ri').innerHTML='<i class="far fa-meh" style="color:#f5576c"></i>';document.getElementById('rt').textContent='Keep Practicing!'}}document.getElementById('rs').textContent=ts.toFixed(2)+' / '+qd.q.length;document.getElementById('rp').textContent=pc.toFixed(1)+'%';document.getElementById('cc').textContent=c;document.getElementById('ic').textContent=ic;document.getElementById('uc').textContent=u;document.getElementById('nm').textContent='-'+nm.toFixed(2)}}
function ra(){{st.rv=true;document.body.style.overflow='hidden';document.getElementById('resultsContainer').style.display='none';document.getElementById('quizContainer').style.display='block';rq(0);uqg()}}
function rs(){{document.body.style.overflow='hidden';location.reload()}}
</script>
</body>
</html>"""

    # Save and send
    fn = f"{uuid.uuid4().hex}.html"
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    with open(fn, "rb") as f:
        await context.bot.send_document(chat_id=chat_id, document=f, caption=f"{quiz['quiz_name']}\n\nPremium Quiz Bot", protect_content=type)
        # await context.bot.send_document(chat_id=chat_id, document=f, caption=f"<i class='fas fa-file-alt'></i> {quiz['quiz_name']}\\n\\n<b><i>Premium Quiz by Team SPY</i></b>", parse_mode=ParseMode.HTML)
    import os
    os.remove(fn)


async def generate_quiz_html(quiz, chat_id, context, ParseMode, type):
    """Premium Quiz HTML Generator - Mobile + Desktop CBT Platform"""
    
    def je(t):
        """JS escape"""
        if not t: return ""
        t = str(t)
        return t.replace('\\','\\\\').replace('"','\\"').replace("'","\\'").replace('\n','\\n').replace('\r','\\r').replace('\t','\\t')
    
    # Quiz metadata
    qn = re.sub(r"[^a-zA-Z0-9_-]", "", unidecode(quiz["quiz_name"]).replace(" ", "_"))[:100] + ".html"
    mm = len(quiz["questions"])
    nm = quiz.get("negative_marks", 0.25)
    
    # ── Section support ──────────────────────────────────────────────
    sections = quiz.get("sections", [])
    has_sections = bool(sections)

    if has_sections:
        # Build section JS array: [{name, start(0-idx), end(0-idx), timer(sec)}]
        sec_js_parts = []
        total_sec_time = 0
        for s in sections:
            sname = je(s["name"])
            sr = s["question_range"]          # 1-indexed tuple (start, end)
            s_start = int(sr[0]) - 1          # convert to 0-indexed
            s_end   = int(sr[1]) - 1
            num_q_in_section = s_end - s_start + 1
            s_timer = int(s.get("timer", 60)) * num_q_in_section
            total_sec_time += s_timer
            sec_js_parts.append(
                f'{{name:"{sname}",start:{s_start},end:{s_end},timer:{s_timer}}}'
            )
        sec_js = "[" + ",".join(sec_js_parts) + "]"
        dt = total_sec_time                   # total quiz time in seconds
    else:
        sec_js = "[]"
        timer_per_q = quiz.get("timer", 60)
        if timer_per_q is None:
            timer_per_q = 60
        dt = timer_per_q * mm
    # ────────────────────────────────────────────────────────────────

    # Build questions JS
    qjs = []
    for i, q in enumerate(quiz["questions"]):
        opts = q["options"].copy()
        co = opts[q["correct_option_id"]]
        random.shuffle(opts)
        qjs.append(f'''{{id:{i},txt:"{je(q["question"])}",ref:"{je(q.get("reply_text",""))}",opts:{json.dumps(opts)},ci:{opts.index(co)},exp:"{je(q.get("explanation","No explanation"))}"}}''')
    
    # Desktop CBT Styles
    dsk_css = """
    @media (min-width: 1024px) {
        body { overflow: auto !important; }
        
        #quizContainer {
            display: grid !important;
            grid-template-columns: 1fr 320px;
            grid-template-rows: auto 1fr auto;
            gap: 0;
            height: 100vh;
            overflow: hidden;
        }
        
        .quiz-header {
            grid-column: 1 / -1;
            position: static;
            padding: 20px 32px;
            border-bottom: 3px solid var(--border);
        }
        
        .header-top {
            max-width: none;
            margin-bottom: 16px;
        }
        
        .quiz-title-text { max-width: 400px; }
        
        .timer-display {
            padding: 10px 20px;
            font-size: 18px;
        }
        
        /* Main content area - scrollable */
        .question-section {
            position: static !important;
            grid-column: 1;
            grid-row: 2;
            overflow-y: auto;
            padding: 32px;
            background: var(--bg-light);
            top: auto !important;
            bottom: auto !important;
        }
        
        .question-card {
            max-width: 900px;
            padding: 32px;
            margin: 0 auto 24px;
        }
        
        .question-text {
            font-size: 18px;
            margin-bottom: 24px;
        }
        
        .option-btn {
            padding: 18px 20px;
            font-size: 16px;
        }
        
        .option-indicator {
            min-width: 32px;
            height: 32px;
            font-size: 14px;
        }
        
        /* Desktop Question Navigator - Right Panel */
        .question-nav-panel {
            position: static !important;
            grid-column: 2;
            grid-row: 2;
            transform: none !important;
            max-height: none;
            height: 100%;
            border-radius: 0;
            border-left: 3px solid var(--border);
            box-shadow: none;
            padding: 24px;
            overflow-y: auto;
            background: var(--bg-white);
        }
        
        .question-nav-panel.open { transform: none !important; }
        
        .nav-panel-header {
            position: sticky;
            top: 0;
            background: var(--bg-white);
            z-index: 10;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        
        .nav-panel-title {
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .nav-close-btn { display: none; }
        
        .nav-legend {
            position: sticky;
            top: 60px;
            background: var(--bg-white);
            z-index: 9;
            padding: 16px;
            margin: -16px -16px 20px;
            border-radius: 12px;
            background: var(--bg-light);
        }
        
        .question-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }
        
        .question-nav-item {
            aspect-ratio: 1;
            font-size: 16px;
            border-radius: 12px;
        }
        
        .question-nav-toggle { display: none; }
        
        /* Footer Navigation - Sticky */
        .nav-controls {
            position: static;
            grid-column: 1;
            grid-row: 3;
            padding: 20px 32px;
            border-top: 3px solid var(--border);
            max-width: none;
            display: flex;
            justify-content: center;
            gap: 16px;
        }
        
        .nav-btn {
            min-width: 160px;
            padding: 16px 24px;
            font-size: 16px;
        }
        
        /* Results Desktop Layout */
        #resultsContainer {
            padding: 40px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .results-header {
            padding: 60px 40px;
            margin-bottom: 32px;
        }
        
        .results-icon { font-size: 100px; }
        .results-title { font-size: 36px; }
        .results-score { font-size: 64px; }
        .results-percentage { font-size: 24px; }
        
        .stats-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 32px;
            max-width: none;
        }
        
        .stat-card { padding: 32px; }
        .stat-icon { width: 54px; height: 54px; font-size: 24px; }
        .stat-value { font-size: 40px; }
        .stat-label { font-size: 14px; }
        
        .action-buttons {
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            max-width: 800px;
        }
        
        .action-btn { padding: 20px; font-size: 17px; }
        
        /* Mode Selection Desktop */
        .mode-container {
            max-width: 600px;
            padding: 50px 40px;
        }
        
        .mode-header-icon {
            width: 80px;
            height: 80px;
            font-size: 40px;
        }
        
        .mode-header h2 { font-size: 28px; }
        .mode-header p { font-size: 15px; }
        
        .mode-cards { gap: 20px; }
        
        .mode-card {
            padding: 24px;
            border-radius: 18px;
        }
        
        .mode-icon {
            width: 60px;
            height: 60px;
            font-size: 28px;
            margin-right: 20px;
        }
        
        .mode-info h3 { font-size: 19px; }
        .mode-info p { font-size: 14px; }
        
        .timer-input { padding: 16px 18px; font-size: 16px; }
        .start-btn { padding: 18px; font-size: 17px; }
    }
    
    /* Ultra-wide Desktop */
    @media (min-width: 1440px) {
        #quizContainer {
            grid-template-columns: 1fr 380px;
        }
        
        .question-section { padding: 40px 60px; }
        .question-card { max-width: 1000px; padding: 40px; }
        .question-nav-panel { padding: 32px; }
        .question-grid { grid-template-columns: repeat(5, 1fr); }
        .nav-controls { padding: 24px 60px; }
    }
    """
    
    # Main HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{quiz['quiz_name']}</title>
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
:root{{--primary:#667eea;--primary-dark:#5568d3;--secondary:#764ba2;--success:#48bb78;--danger:#f5576c;--warning:#fbbf24;--info:#4facfe;--bg-light:#f7fafc;--bg-white:#fff;--text-dark:#1a202c;--text-light:#718096;--border:#e2e8f0}}
[data-theme="dark"]{{--bg-light:#1a202c;--bg-white:#2d3748;--text-dark:#f7fafc;--text-light:#cbd5e0;--border:#4a5568}}
body{{font-family:'Poppins',-apple-system,BlinkMacSystemFont,sans-serif;background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);min-height:100vh;overflow:hidden;user-select:none;-webkit-user-select:none;transition:background .3s}}
.scrollable::-webkit-scrollbar{{width:6px}}
.scrollable::-webkit-scrollbar-track{{background:transparent}}
.scrollable::-webkit-scrollbar-thumb{{background:var(--primary);border-radius:10px}}
.protected-content{{white-space:pre-wrap!important;word-wrap:break-word!important;word-break:break-word!important;overflow-wrap:break-word!important;line-height:1.7;user-select:none}}
.option-btn .protected-content,.option-text.protected-content{{display:block;min-width:0;max-width:100%}}
#modeSelection{{position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);display:flex;align-items:center;justify-content:center;z-index:9999;padding:20px;overflow-y:auto}}
.mode-container{{background:#fff;border-radius:24px;padding:40px 30px;max-width:500px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.3);animation:ms .5s cubic-bezier(.34,1.56,.64,1)}}
@keyframes ms{{from{{opacity:0;transform:translateY(40px) scale(.95)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
.mode-header{{text-align:center;margin-bottom:32px}}
.mode-header-icon{{width:70px;height:70px;margin:0 auto 16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:20px;display:flex;align-items:center;justify-content:center;font-size:36px;color:#fff;box-shadow:0 8px 24px rgba(102,126,234,.3)}}
.mode-header h2{{font-size:24px;font-weight:700;color:#1a202c;margin-bottom:8px}}
.mode-header p{{font-size:14px;color:#718096;font-weight:400}}
.mode-cards{{display:grid;gap:16px;margin-bottom:24px}}
.mode-card{{background:#f7fafc;border:2px solid #e2e8f0;border-radius:16px;padding:20px;cursor:pointer;transition:all .3s;position:relative}}
.mode-card:hover{{transform:translateY(-3px);box-shadow:0 12px 28px rgba(102,126,234,.15);border-color:#cbd5e0}}
.mode-card.selected{{border-color:#667eea;background:#fff;box-shadow:0 8px 24px rgba(102,126,234,.2);transform:translateY(-2px)}}
.mode-card-header{{display:flex;align-items:center}}
.mode-icon{{width:54px;height:54px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;margin-right:16px;flex-shrink:0}}
.exam-mode .mode-icon{{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:#fff}}
.practice-mode .mode-icon{{background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:#fff}}
.mode-info h3{{font-size:17px;font-weight:700;color:#1a202c;margin-bottom:4px}}
.mode-info p{{font-size:13px;color:#718096;line-height:1.4}}
.timer-config{{margin-bottom:24px}}
.timer-config label{{display:block;font-size:14px;font-weight:600;color:#1a202c;margin-bottom:10px}}
.timer-config label i{{margin-right:6px;color:#667eea}}
.timer-input{{width:100%;padding:14px 16px;border:2px solid #e2e8f0;border-radius:12px;font-size:15px;font-weight:500;transition:all .3s;background:#fff;font-family:'Poppins',sans-serif;color:#1a202c}}
.timer-input::placeholder{{color:#a0aec0}}
.timer-input:focus{{outline:none;border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.1)}}
.start-btn{{width:100%;padding:16px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;border-radius:14px;font-size:16px;font-weight:700;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;gap:10px;box-shadow:0 8px 20px rgba(102,126,234,.35)}}
.start-btn:hover:not(:disabled){{transform:translateY(-2px);box-shadow:0 12px 28px rgba(102,126,234,.45)}}
.start-btn:active:not(:disabled){{transform:translateY(0)}}
.start-btn:disabled{{opacity:.5;cursor:not-allowed;background:#cbd5e0;box-shadow:none}}
#quizContainer{{display:none;position:fixed;top:0;left:0;width:100%;height:100vh;background:var(--bg-light);overflow:hidden}}
.quiz-header{{position:fixed;top:0;left:0;right:0;background:var(--bg-white);box-shadow:0 2px 15px rgba(0,0,0,.08);z-index:100;padding:16px 20px}}
.header-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:10px}}
.quiz-title{{font-size:15px;font-weight:700;color:var(--text-dark);display:flex;align-items:center;gap:8px;flex:1;min-width:0}}
.quiz-title-text{{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:150px}}
.mode-badge{{font-size:10px;padding:4px 10px;border-radius:20px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}}
.mode-badge.exam{{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:#fff}}
.mode-badge.practice{{background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:#fff}}
.header-actions{{display:flex;gap:8px;align-items:center}}
.theme-toggle{{width:36px;height:36px;background:var(--bg-light);border:none;border-radius:10px;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;color:var(--text-dark);transition:all .3s}}
.theme-toggle:hover{{transform:scale(1.1)}}
.timer-display{{display:flex;align-items:center;gap:8px;font-size:16px;font-weight:700;color:var(--primary);padding:8px 14px;background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);border-radius:12px;white-space:nowrap}}
.timer-display.warning{{color:var(--danger);background:linear-gradient(135deg,rgba(245,87,108,.15) 0%,rgba(240,147,251,.15) 100%);animation:pulse 1s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
.header-progress{{display:flex;justify-content:space-between;align-items:center;font-size:12px;color:var(--text-light);margin-bottom:8px}}
.progress-bar-container{{height:6px;background:var(--border);border-radius:10px;overflow:hidden}}
.progress-bar{{height:100%;background:linear-gradient(90deg,var(--primary) 0%,var(--secondary) 100%);transition:width .3s;border-radius:10px}}
.section-badge{{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:700;color:#fff;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);padding:4px 12px;border-radius:20px;margin-bottom:10px}}
.question-section{{position:fixed;top:140px;left:0;right:0;bottom:80px;overflow-y:auto;overflow-x:hidden;padding:20px;-webkit-overflow-scrolling:touch}}
.question-section.scrollable{{scrollbar-width:thin;scrollbar-color:var(--primary) transparent}}
.question-card{{background:var(--bg-white);border-radius:20px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,.06);max-width:800px;margin:0 auto}}
.question-number{{display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:700;color:var(--primary);background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);padding:6px 14px;border-radius:20px;margin-bottom:16px}}
.question-reference{{background:linear-gradient(135deg,rgba(79,172,254,.15) 0%,rgba(0,242,254,.15) 100%);border-left:4px solid var(--info);padding:14px 16px;border-radius:10px;margin-bottom:16px;font-size:14px;color:var(--text-dark);line-height:1.7;white-space:pre-wrap!important;word-wrap:break-word!important;word-break:break-word!important;overflow-wrap:break-word!important}}
.question-text{{font-size:16px;font-weight:600;color:var(--text-dark);line-height:1.7;margin-bottom:20px;white-space:pre-wrap!important;word-wrap:break-word!important;word-break:break-word!important;overflow-wrap:break-word!important}}
.options-container{{display:grid;gap:12px}}
.option-btn{{width:100%;padding:16px 18px;background:var(--bg-light);border:3px solid var(--border);border-radius:14px;text-align:left;font-size:15px;color:var(--text-dark);cursor:pointer;transition:all .3s;display:flex;align-items:flex-start;gap:12px;line-height:1.7;user-select:none}}
.option-btn:active{{transform:scale(.98)}}
.option-indicator{{min-width:28px;height:28px;border-radius:50%;background:var(--bg-white);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;transition:all .3s}}
.option-text{{flex:1;padding-top:3px;white-space:pre-wrap!important;word-wrap:break-word!important;word-break:break-word!important;overflow-wrap:break-word!important;min-width:0}}
.option-btn:hover:not(.disabled){{border-color:var(--primary);transform:translateX(4px)}}
.option-btn.selected{{background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);border-color:var(--primary)}}
.option-btn.selected .option-indicator{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff;border-color:transparent}}
.option-btn.correct{{background:linear-gradient(135deg,rgba(72,187,120,.15) 0%,rgba(72,187,120,.15) 100%);border-color:var(--success)}}
.option-btn.correct .option-indicator{{background:var(--success);color:#fff;border-color:transparent}}
.option-btn.incorrect{{background:linear-gradient(135deg,rgba(245,87,108,.15) 0%,rgba(245,87,108,.15) 100%);border-color:var(--danger)}}
.option-btn.incorrect .option-indicator{{background:var(--danger);color:#fff;border-color:transparent}}
.option-btn.disabled{{pointer-events:none;opacity:.6}}
.explanation-box{{display:none;background:linear-gradient(135deg,rgba(254,245,231,.5) 0%,rgba(251,191,36,.2) 100%);border-left:4px solid var(--warning);border-radius:12px;padding:16px;margin-top:20px;animation:sd .3s ease-out}}
@keyframes sd{{from{{opacity:0;max-height:0;padding:0}}to{{opacity:1;max-height:500px;padding:16px}}}}
.explanation-header{{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:700;color:#92400e;margin-bottom:10px}}
.explanation-text{{font-size:14px;color:#78350f;line-height:1.7;white-space:pre-wrap!important;word-wrap:break-word!important;word-break:break-word!important;overflow-wrap:break-word!important}}
[data-theme="dark"] .explanation-text{{color:#fbbf24}}
.nav-controls{{position:fixed;bottom:0;left:0;right:0;background:var(--bg-white);padding:16px 20px;box-shadow:0 -2px 15px rgba(0,0,0,.08);display:flex;gap:12px;z-index:90}}
.nav-btn{{flex:1;padding:14px;border:none;border-radius:12px;font-size:15px;font-weight:600;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;gap:8px}}
.nav-btn.primary{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff}}
.nav-btn.secondary{{background:var(--bg-light);color:var(--text-dark);border:2px solid var(--border)}}
.nav-btn:active{{transform:scale(.96)}}
.nav-btn:disabled{{opacity:.5;cursor:not-allowed;transform:none}}
.question-nav-toggle{{position:fixed;bottom:100px;right:20px;width:56px;height:56px;background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff;border:none;border-radius:50%;font-size:22px;cursor:pointer;box-shadow:0 8px 20px rgba(102,126,234,.4);z-index:85;transition:all .3s}}
.question-nav-toggle:active{{transform:scale(.95)}}
.question-nav-panel{{position:fixed;bottom:0;left:0;right:0;background:var(--bg-white);border-radius:24px 24px 0 0;box-shadow:0 -4px 30px rgba(0,0,0,.15);z-index:95;max-height:70vh;overflow-y:auto;transform:translateY(100%);transition:transform .3s;padding:20px}}
.question-nav-panel.open{{transform:translateY(0)}}
.nav-panel-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:16px;border-bottom:2px solid var(--border)}}
.nav-panel-title{{font-size:18px;font-weight:700;color:var(--text-dark)}}
.nav-close-btn{{width:32px;height:32px;background:var(--bg-light);border:none;border-radius:50%;font-size:16px;cursor:pointer;color:var(--text-light)}}
.nav-legend{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:20px;font-size:12px;color:var(--text-dark)}}
.legend-item{{display:flex;align-items:center;gap:6px;color:var(--text-dark)}}
.legend-box{{width:20px;height:20px;border-radius:6px}}
.legend-box.answered{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%)}}
.legend-box.marked{{background:linear-gradient(135deg,var(--warning) 0%,#f59e0b 100%)}}
.legend-box.unanswered{{background:var(--border)}}
.question-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
.question-nav-item{{aspect-ratio:1;border:2px solid var(--border);border-radius:10px;background:var(--bg-white);display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:600;cursor:pointer;transition:all .3s;color:var(--text-light)}}
.question-nav-item:active{{transform:scale(.95)}}
.question-nav-item.current{{border-color:var(--primary);background:linear-gradient(135deg,rgba(102,126,234,.15) 0%,rgba(118,75,162,.15) 100%);color:var(--primary)}}
.question-nav-item.answered{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff;border-color:transparent}}
.question-nav-item.marked{{background:linear-gradient(135deg,var(--warning) 0%,#f59e0b 100%);color:#fff;border-color:transparent}}
.question-nav-item.correct{{background:linear-gradient(135deg,var(--success) 0%,#38a169 100%);color:#fff;border-color:transparent}}
.question-nav-item.incorrect{{background:linear-gradient(135deg,var(--danger) 0%,#e53e3e 100%);color:#fff;border-color:transparent}}
.nav-section-label{{grid-column:1/-1;font-size:11px;font-weight:700;color:var(--text-light);text-transform:uppercase;letter-spacing:.5px;padding:6px 0 2px;border-top:1px solid var(--border);margin-top:4px}}
#resultsContainer{{display:none;position:fixed;top:0;left:0;width:100%;height:100vh;background:var(--bg-light);overflow-y:auto;overflow-x:hidden;padding:20px;z-index:1000}}
#resultsContainer.scrollable{{scrollbar-width:thin;scrollbar-color:var(--primary) transparent}}
.results-header{{text-align:center;padding:40px 20px;background:var(--bg-white);border-radius:20px;margin-bottom:20px;box-shadow:0 4px 20px rgba(0,0,0,.06)}}
.results-icon{{font-size:80px;margin-bottom:20px}}
.results-title{{font-size:28px;font-weight:700;color:var(--text-dark);margin-bottom:10px}}
.results-score{{font-size:52px;font-weight:800;background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}}
.results-percentage{{font-size:20px;color:var(--text-light);font-weight:600}}
.stats-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px;max-width:800px;margin-left:auto;margin-right:auto}}
.stat-card{{background:var(--bg-white);padding:24px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.06)}}
.stat-icon{{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px;margin-bottom:12px}}
.stat-icon.correct{{background:linear-gradient(135deg,var(--success) 0%,#38a169 100%);color:#fff}}
.stat-icon.incorrect{{background:linear-gradient(135deg,var(--danger) 0%,#e53e3e 100%);color:#fff}}
.stat-icon.unattempted{{background:linear-gradient(135deg,#a0aec0 0%,#718096 100%);color:#fff}}
.stat-icon.negative{{background:linear-gradient(135deg,#ed8936 0%,#dd6b20 100%);color:#fff}}
.stat-value{{font-size:32px;font-weight:700;color:var(--text-dark);margin-bottom:4px}}
.stat-label{{font-size:13px;color:var(--text-light);font-weight:500}}
.action-buttons{{display:grid;gap:12px;max-width:800px;margin:0 auto}}
.action-btn{{width:100%;padding:18px;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:10px;transition:all .3s}}
.action-btn.primary{{background:linear-gradient(135deg,var(--primary) 0%,var(--secondary) 100%);color:#fff}}
.action-btn.secondary{{background:var(--bg-white);color:var(--text-dark);border:2px solid var(--border)}}
.action-btn:hover{{transform:translateY(-2px)}}
{dsk_css}
</style>
</head>
<body>
<div id="modeSelection">
<div class="mode-container">
<div class="mode-header">
<div class="mode-header-icon"><i class="fas fa-graduation-cap"></i></div>
<h2>{quiz['quiz_name']}</h2>
<p>Choose your preferred test mode</p>
</div>
<div class="mode-cards">
<div class="mode-card exam-mode" data-mode="exam">
<div class="mode-card-header">
<div class="mode-icon"><i class="fas fa-file-alt"></i></div>
<div class="mode-info">
<h3>Exam Mode</h3>
<p>Complete all questions, results shown after submission</p>
</div>
</div>
</div>
<div class="mode-card practice-mode" data-mode="practice">
<div class="mode-card-header">
<div class="mode-icon"><i class="fas fa-book-open"></i></div>
<div class="mode-info">
<h3>Practice Mode</h3>
<p>Instant feedback with detailed explanations</p>
</div>
</div>
</div>
</div>
<div class="timer-config">
<label for="ct"><i class="fas fa-clock"></i> Custom Timer (minutes)</label>
<input type="number" id="ct" class="timer-input" placeholder="Default: {int(dt/60)} minutes" min="1" max="300"/>
</div>
<button class="start-btn" id="sb" disabled><i class="fas fa-play-circle"></i><span>Start Quiz</span></button>
</div>
</div>
<div id="quizContainer">
<div class="quiz-header">
<div class="header-top">
<div class="quiz-title">
<i class="fas fa-clipboard-list"></i>
<span class="quiz-title-text" title="{quiz['quiz_name']}">{quiz['quiz_name']}</span>
<span class="mode-badge" id="mb"></span>
</div>
<div class="header-actions">
<button class="theme-toggle" id="tt" title="Toggle Dark Mode"><i class="fas fa-moon"></i></button>
<div class="timer-display" id="td"><i class="fas fa-clock"></i><span id="tt2">00:00</span></div>
</div>
</div>
<div class="header-progress">
<span id="pt">Question 1 of {mm}</span>
<span id="at">Attempted: 0/{mm}</span>
</div>
<div class="progress-bar-container"><div class="progress-bar" id="pb"></div></div>
</div>
<div class="question-section scrollable" id="qs"></div>
<div class="nav-controls">
<button class="nav-btn secondary" id="pv"><i class="fas fa-chevron-left"></i>Previous</button>
<button class="nav-btn secondary" id="mk"><i class="fas fa-bookmark"></i>Mark</button>
<button class="nav-btn primary" id="nx">Next<i class="fas fa-chevron-right"></i></button>
<button class="nav-btn primary" id="sm" style="display:none"><i class="fas fa-paper-plane"></i>Submit</button>
</div>
<button class="question-nav-toggle" id="nt"><i class="fas fa-th"></i></button>
<div class="question-nav-panel" id="np">
<div class="nav-panel-header">
<h3 class="nav-panel-title"><i class="fas fa-map-marked-alt"></i> Question Navigator</h3>
<button class="nav-close-btn" id="nc"><i class="fas fa-times"></i></button>
</div>
<div class="nav-legend">
<div class="legend-item"><div class="legend-box answered"></div><span>Answered</span></div>
<div class="legend-item"><div class="legend-box marked"></div><span>Marked</span></div>
<div class="legend-item"><div class="legend-box unanswered"></div><span>Not Answered</span></div>
</div>
<div class="question-grid" id="qg"></div>
</div>
</div>
<div id="resultsContainer">
<div class="results-header">
<div class="results-icon" id="ri"></div>
<h2 class="results-title" id="rt"></h2>
<div class="results-score" id="rs"></div>
<div class="results-percentage" id="rp"></div>
</div>
<div class="stats-grid">
<div class="stat-card"><div class="stat-icon correct"><i class="fas fa-check"></i></div><div class="stat-value" id="cc">0</div><div class="stat-label">Correct</div></div>
<div class="stat-card"><div class="stat-icon incorrect"><i class="fas fa-times"></i></div><div class="stat-value" id="ic">0</div><div class="stat-label">Incorrect</div></div>
<div class="stat-card"><div class="stat-icon unattempted"><i class="fas fa-minus"></i></div><div class="stat-value" id="uc">0</div><div class="stat-label">Unattempted</div></div>
<div class="stat-card"><div class="stat-icon negative"><i class="fas fa-exclamation-triangle"></i></div><div class="stat-value" id="nm">0</div><div class="stat-label">Negative Marks</div></div>
</div>
<div class="action-buttons">
<button class="action-btn primary" id="rb"><i class="fas fa-search"></i>Review Answers</button>
<button class="action-btn secondary" id="rsb"><i class="fas fa-redo"></i>Restart Quiz</button>
</div>
</div>
<script>
const qd={{q:[{",".join(qjs)}],m:null,tt:{dt},nm:{nm},sections:{sec_js}}},
st={{cq:0,a:Array(qd.q.length).fill(null),mk:Array(qd.q.length).fill(false),tr:qd.tt,csi:0,sti:null,ti:null,sb:false,rv:false,th:'light'}};

// ── Section helpers ─────────────────────────────────────────────
function getSectionForQ(qi){{
  if(!qd.sections.length) return null;
  for(let i=0;i<qd.sections.length;i++){{
    const s=qd.sections[i];
    if(qi>=s.start&&qi<=s.end) return {{idx:i,sec:s}};
  }}
  return null;
}}
function initSectionTimer(){{
  if(!qd.sections.length) return;
  // Reset each section timer on quiz start
  qd.sections.forEach(s=>{{s.tr=s.timer;}});
  st.csi=0;
  st.tr=qd.sections[0].tr;
}}
function getCurrentSection(){{
  if(!qd.sections.length) return null;
  return qd.sections[st.csi]||null;
}}
function advanceSectionIfNeeded(){{
  if(!qd.sections.length) return;
  const sec=qd.sections[st.csi];
  if(!sec) return;
  // Save remaining time back
  sec.tr=st.tr;
  // Check if user moved beyond this section's last question
  if(st.cq>sec.end&&st.csi<qd.sections.length-1){{
    st.csi++;
    st.tr=qd.sections[st.csi].tr;
    utd();
  }} else if(st.cq<sec.start&&st.csi>0){{
    st.csi--;
    st.tr=qd.sections[st.csi].tr;
    utd();
  }}
}}
// ────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded',()=>{{sms();pcc();lt()}});
function lt(){{const t=localStorage.getItem('qt')||'light';st.th=t;document.documentElement.setAttribute('data-theme',t);uti()}}
function tgt(){{st.th=st.th==='light'?'dark':'light';document.documentElement.setAttribute('data-theme',st.th);localStorage.setItem('qt',st.th);uti()}}
function uti(){{const i=document.querySelector('#tt i');if(i)i.className=st.th==='light'?'fas fa-moon':'fas fa-sun'}}
function pcc(){{document.addEventListener('contextmenu',e=>e.preventDefault());document.addEventListener('copy',e=>e.preventDefault());document.addEventListener('cut',e=>e.preventDefault());document.addEventListener('selectstart',e=>{{if(!e.target.tagName.match(/INPUT|TEXTAREA/i))e.preventDefault()}})}}
function sms(){{const mc=document.querySelectorAll('.mode-card'),sb=document.getElementById('sb');mc.forEach(c=>{{c.addEventListener('click',()=>{{mc.forEach(x=>x.classList.remove('selected'));c.classList.add('selected');qd.m=c.dataset.mode;sb.disabled=false}})}}); sb.addEventListener('click',sq)}}
function sq(){{
  const ct=document.getElementById('ct'),ctv=parseInt(ct.value);
  if(!qd.sections.length&&ctv&&ctv>0){{st.tr=ctv*60;qd.tt=ctv*60}}
  document.body.style.overflow='hidden';
  document.getElementById('modeSelection').style.display='none';
  document.getElementById('quizContainer').style.display='block';
  document.getElementById('mb').textContent=qd.m;
  document.getElementById('mb').className='mode-badge '+qd.m;
  iq();
}}
function iq(){{initSectionTimer();rq(0);rqg();stt();sn()}}
function stt(){{
  utd();
  st.ti=setInterval(()=>{{
    st.tr--;
    if(qd.sections.length){{
      const sec=getCurrentSection();
      if(sec) sec.tr=st.tr;
    }}
    utd();
    if(st.tr<=0){{
      if(qd.sections.length&&st.csi<qd.sections.length-1){{
        // Section time up — lock section questions and move to next section
        const sec=qd.sections[st.csi];
        // Force-lock all unanswered in this section (keep nulls, just advance)
        st.csi++;
        st.tr=qd.sections[st.csi].timer;
        qd.sections[st.csi].tr=st.tr;
        rq(qd.sections[st.csi].start);
        utd();
      }} else {{
        clearInterval(st.ti);sbq();
      }}
    }}
    if(st.tr<=60) document.getElementById('td').classList.add('warning');
    else document.getElementById('td').classList.remove('warning');
  }},1000);
}}
function utd(){{
  const m=Math.floor(st.tr/60),s=st.tr%60;
  document.getElementById('tt2').textContent=`${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
}}
function rq(i){{
  st.cq=i;
  advanceSectionIfNeeded();
  const q=qd.q[i],qs=document.getElementById('qs');
  let h=`<div class="question-card">`;
  // Section badge
  const si=getSectionForQ(i);
  if(si)h+=`<div class="section-badge"><i class="fas fa-layer-group"></i>${{si.sec.name}}</div>`;
  h+=`<div class="question-number"><i class="fas fa-question-circle"></i>Question ${{i+1}} of ${{qd.q.length}}</div>`;
  if(q.ref)h+=`<div class="question-reference protected-content"><i class="fas fa-info-circle"></i> ${{q.ref}}</div>`;
  h+=`<div class="question-text protected-content">${{q.txt}}</div><div class="options-container">`;
  q.opts.forEach((o,x)=>{{
    let bc='option-btn',ic=String.fromCharCode(65+x);
    const isSel=st.a[i]===x,isCor=x===q.ci,shAns=(qd.m==='practice'&&st.a[i]!==null)||st.sb;
    // Lock options for completed sections in exam mode
    const sectionDone=si&&st.csi>si.idx&&!st.rv;
    if(isSel)bc+=' selected';
    if(shAns||sectionDone){{
      bc+=' disabled';
      if(isCor){{bc+=' correct';ic='<i class="fas fa-check"></i>'}}
      else if(isSel&&!isCor){{bc+=' incorrect';ic='<i class="fas fa-times"></i>'}}
    }}
    h+=`<button class="${{bc}}" data-index="${{x}}" onclick="so(${{x}})"><div class="option-indicator">${{ic}}</div><div class="option-text protected-content">${{o}}</div></button>`;
  }});
  h+=`</div>`;
  const shExp=(qd.m==='practice'&&st.a[i]!==null)||st.sb;
  if(shExp)h+=`<div class="explanation-box" style="display:block"><div class="explanation-header"><i class="fas fa-lightbulb"></i>Explanation</div><div class="explanation-text protected-content">${{q.exp}}</div></div>`;
  h+=`</div>`;
  qs.innerHTML=h;qs.scrollTop=0;up();unb();uqg();
}}
function so(oi){{
  if(st.sb) return;
  // Block input if this question's section time is up
  const si=getSectionForQ(st.cq);
  if(si&&st.csi>si.idx) return;
  if(st.a[st.cq]===oi){{st.a[st.cq]=null}}else{{st.a[st.cq]=oi}}
  rq(st.cq);
}}
function sn(){{document.getElementById('pv').addEventListener('click',np);document.getElementById('nx').addEventListener('click',nn);document.getElementById('mk').addEventListener('click',tm);document.getElementById('sm').addEventListener('click',cs);document.getElementById('nt').addEventListener('click',tnp);document.getElementById('nc').addEventListener('click',tnp);document.getElementById('rb').addEventListener('click',ra);document.getElementById('rsb').addEventListener('click',rs);document.getElementById('tt').addEventListener('click',tgt);document.addEventListener('keydown',e=>{{if(st.sb)return;if(e.key==='ArrowLeft')np();if(e.key==='ArrowRight')nn()}})}}
function np(){{if(st.cq>0)rq(st.cq-1)}}
function nn(){{if(st.cq<qd.q.length-1)rq(st.cq+1)}}
function tm(){{st.mk[st.cq]=!st.mk[st.cq];uqg();const mb=document.getElementById('mk');mb.innerHTML=st.mk[st.cq]?'<i class="fas fa-bookmark"></i> Unmark':'<i class="fas fa-bookmark"></i> Mark'}}
function unb(){{document.getElementById('pv').disabled=st.cq===0;if(st.cq===qd.q.length-1){{document.getElementById('nx').style.display='none';document.getElementById('sm').style.display='flex'}}else{{document.getElementById('nx').style.display='flex';document.getElementById('sm').style.display='none'}}const mb=document.getElementById('mk');mb.innerHTML=st.mk[st.cq]?'<i class="fas fa-bookmark"></i> Unmark':'<i class="fas fa-bookmark"></i> Mark'}}
function up(){{const at=st.a.filter(a=>a!==null).length,pr=((st.cq+1)/qd.q.length)*100;document.getElementById('pt').textContent=`Question ${{st.cq+1}} of ${{qd.q.length}}`;document.getElementById('at').textContent=`Attempted: ${{at}}/${{qd.q.length}}`;document.getElementById('pb').style.width=pr+'%'}}
function rqg(){{
  const g=document.getElementById('qg');
  g.innerHTML='';
  if(qd.sections.length){{
    qd.sections.forEach((sec,si)=>{{
      const lbl=document.createElement('div');
      lbl.className='nav-section-label';
      lbl.textContent=sec.name;
      g.appendChild(lbl);
      for(let i=sec.start;i<=sec.end;i++){{
        const it=document.createElement('div');
        it.className='question-nav-item';
        it.textContent=i+1;
        it.onclick=(()=>{{const idx=i;return()=>{{rq(idx);if(window.innerWidth<768)tnp()}}}})();
        g.appendChild(it);
      }}
    }});
  }} else {{
    qd.q.forEach((_,i)=>{{
      const it=document.createElement('div');
      it.className='question-nav-item';
      it.textContent=i+1;
      it.onclick=()=>{{rq(i);if(window.innerWidth<768)tnp()}};
      g.appendChild(it);
    }});
  }}
}}
function uqg(){{
  const its=document.querySelectorAll('.question-nav-item');
  let qi=0;
  its.forEach(it=>{{
    if(it.classList.contains('nav-section-label')) return;
    const i=parseInt(it.textContent)-1;
    it.className='question-nav-item';
    if(i===st.cq) it.classList.add('current');
    if(st.sb){{
      if(st.a[i]===qd.q[i].ci) it.classList.add('correct');
      else if(st.a[i]!==null) it.classList.add('incorrect');
    }} else {{
      if(st.a[i]!==null) it.classList.add('answered');
      if(st.mk[i]) it.classList.add('marked');
    }}
  }});
}}
function tnp(){{document.getElementById('np').classList.toggle('open')}}
function cs(){{const u=st.a.filter(a=>a===null).length;if(u>0){{const c=window.confirm(`You have ${{u}} unattempted question(s). Do you want to submit?`);if(!c)return}}sbq()}}
function sbq(){{
  clearInterval(st.ti);st.sb=true;
  let c=0,ic=0,u=0,nm=0;
  st.a.forEach((a,i)=>{{if(a===null)u++;else if(a===qd.q[i].ci)c++;else{{ic++;nm+=qd.nm}}}});
  const ts=c-nm,pc=(ts/qd.q.length)*100;
  document.body.style.overflow='auto';
  document.getElementById('quizContainer').style.display='none';
  document.getElementById('resultsContainer').style.display='block';
  document.getElementById('resultsContainer').classList.add('scrollable');
  if(pc>=70){{document.getElementById('ri').innerHTML='<i class="fas fa-trophy" style="color:#fbbf24"></i>';document.getElementById('rt').textContent='Excellent Performance!'}}
  else if(pc>=50){{document.getElementById('ri').innerHTML='<i class="far fa-smile" style="color:#48bb78"></i>';document.getElementById('rt').textContent='Good Job!'}}
  else{{document.getElementById('ri').innerHTML='<i class="far fa-meh" style="color:#f5576c"></i>';document.getElementById('rt').textContent='Keep Practicing!'}}
  document.getElementById('rs').textContent=ts.toFixed(2)+' / '+qd.q.length;
  document.getElementById('rp').textContent=pc.toFixed(1)+'%';
  document.getElementById('cc').textContent=c;
  document.getElementById('ic').textContent=ic;
  document.getElementById('uc').textContent=u;
  document.getElementById('nm').textContent='-'+nm.toFixed(2);
}}
function ra(){{st.rv=true;document.body.style.overflow='hidden';document.getElementById('resultsContainer').style.display='none';document.getElementById('quizContainer').style.display='block';rq(0);uqg()}}
function rs(){{document.body.style.overflow='hidden';location.reload()}}
</script>
</body>
</html>"""

    # Save and send
    fn = f"{uuid.uuid4().hex}.html"
    with open(fn, "w", encoding="utf-8") as f:
        f.write(html)
    with open(fn, "rb") as f:
        await context.bot.send_document(chat_id=chat_id, document=f, caption=f"{quiz['quiz_name']}\n\nPremium Quiz Bot", protect_content=type)
    import os
    os.remove(fn)
