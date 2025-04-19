from flask import Flask, render_template, request
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from dotenv import load_dotenv
from google import genai
import os

load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

app = Flask(__name__)
model = SentenceTransformer('all-MiniLM-L6-v2')

questions = []
options = []
# Define anime characters and their traits
characters_by_theme = {
    "anime": {
        "Naruto Uzumaki": "energetic, loyal, impulsive, never gives up",
        "Lelouch Lamperouge": "strategic, intelligent, calm, manipulative",
        "Goku": "brave, strong, carefree, determined",
        "Light Yagami": "smart, ambitious, justice-driven, secretive",
        "Hinata Hyuga": "shy, kind, loyal, observant",
        "Eren Yeager": "angry, vengeful, passionate, rebellious"
    },
    "fruit": {
        "Pineapple": "bold, spiky, fun, assertive",
        "Banana": "easygoing, dependable, mellow",
        "Strawberry": "sweet, romantic, gentle",
        "Lemon": "sharp, witty, refreshing",
        "Apple": "classic, reliable, balanced",
        "Coconut": "tough outside, sweet inside"
    },
    "color": {
        "Red": "passionate, bold, energetic",
        "Blue": "calm, thoughtful, stable",
        "Yellow": "cheerful, bright, curious",
        "Green": "grounded, calm, empathetic",
        "Purple": "creative, unique, mystical",
        "Black": "elegant, mysterious, confident"
    },
    "hp": {
        "Harry Potter": "brave, loyal, determined, selfless",
        "Hermione Granger": "intelligent, resourceful, passionate",
        "Ron Weasley": "loyal, humorous, courageous",
        "Draco Malfoy": "proud, cunning, conflicted",
        "Luna Lovegood": "quirky, dreamy, insightful",
        "Snape": "complex, secretive, determined"
    },
    "creature": {
        "Dragon": "powerful, fearless, commanding",
        "Unicorn": "gentle, rare, pure-hearted",
        "Phoenix": "resilient, wise, reborn",
        "Mermaid": "mysterious, graceful, curious",
        "Griffin": "regal, fierce, noble",
        "Centaur": "logical, wild, observant"
    },
    "dessert": {
        "Cupcake": "fun, colorful, charming",
        "Cheesecake": "smooth, elegant, refined",
        "Brownie": "comforting, deep, sweet",
        "Ice Cream": "playful, emotional, versatile",
        "Macaron": "stylish, precise, sensitive",
        "Donut": "cheerful, familiar, friendly"
    }

}
@app.route('/')
def theme_select():
    return render_template('theme-select.html')

@app.route('/quiz')
def index():
    # Generate new questions and options
    global questions, options
    questions = []
    options = []
    theme = request.args.get('theme')
    if theme not in characters_by_theme:
        return "Invalid theme selected.", 400
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=[
          
    f"Generate exactly 10 personality quiz questions for the theme: 'What {theme} are you?'.\n"
    "Each question must have exactly 4 distinct, creative options that reflect personality traits or preferences.\n"
    "Format the output exactly as follows:\n"
    "Question: <question text>\n"
    "Options:\n"
    "- <option 1>\n"
    "- <option 2>\n"
    "- <option 3>\n"
    "- <option 4>\n"
    "Repeat this format strictly for all 10 questions."
        ]

    ).text

    # Debugging: Print the raw response to verify its content
    # print("Raw Response:", response)

    # Parse the generated text into separate lists for questions and option

    lines = response.split("\n")
    current_question = None
    current_options = []

    for line in lines:
        line = line.strip()
        if line.startswith("Question:"):
            # Save the previous question and its options if any
            if current_question and current_options:
                questions.append(current_question)
                options.append(current_options)
            # Start a new question
            current_question = line[len("Question:"):].strip()
            current_options = []
        elif line.startswith("-"):
            # Add an option to the current question
            current_options.append(line[1:].strip())

    # Add the last question and its options
    if current_question and current_options:
        questions.append(current_question)
        options.append(current_options)

    # Fallback: Check if questions and options are empty
    if not questions or not options:
        print("Parsing failed. Please check the response format.")
        questions = ["Sample Question 1", "Sample Question 2"]  # Fallback questions
        options = [["Option A", "Option B", "Option C", "Option D"],  # Fallback options
                   ["Option 1", "Option 2", "Option 3", "Option 4"]]

    # print("Questions:", questions)  # Debugging line to check extracted questions
    # print("Options:", options)      # Debugging line to check extracted options

    return render_template('quiz.html', questions=questions, options=options, theme = theme)

@app.route('/submit', methods=['POST'])
def submit():
    global questions, options
    answers = [request.form.get(f'q{i}') for i in range(len(questions))]
    user_profile = ", ".join(answers)
    user_embedding = model.encode(user_profile, convert_to_tensor=True)

    theme = request.form.get('theme')   
    print("Submitted Theme:", theme) 
    characters = characters_by_theme[theme]
    print("Characters in Theme:", characters)

    best_match = None
    best_score = -1

    for name, traits in characters.items():
        char_embedding = model.encode(traits, convert_to_tensor=True)
        score = util.pytorch_cos_sim(user_embedding, char_embedding).item()
        if score > best_score:
            best_score = score
            best_match = name

    return render_template('result.html', character=best_match)

if __name__ == '__main__':
    app.run(debug=True)
