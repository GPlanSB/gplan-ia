import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiService:

    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-pro")

    def generate(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text
