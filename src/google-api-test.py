from models import ask_gemini

prompt = "Respond stating that you(Gemini) work."

response = ask_gemini(prompt)

print(response)
