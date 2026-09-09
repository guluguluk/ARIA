from openai import OpenAI

gemma_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

def ask_gemma(command):
    response = gemma_client.chat.completions.create(
        model="google/gemma-3-1b",
        messages=[
            {
                "role": "user",
                "content": command
            }
        ]
    )

    return response.choices[0].message.content

import sys
from google import genai

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

conversation = []

client = genai.Client()

def build_context():
    history = ""

    for message in conversation:
        history += f"{message['role']}: {message['message']}\n"

    return history

def ask_gemini():
    history = build_context()

    prompt = f"""
You are ARIA — Adaptive Responsive Intelligent Assistant.

Identity:
- ARIA is a personal AI assistant developed by Raghul Sambasivam, a 12th Grader CBSE Student who is excellent at programming.
- Github Repository: https://github.com/guluguluk/ARIA
- ARIA is NOT developed by Google, OpenAI, Microsoft, or any other AI company.
- ARIA currently uses Google Gemini 3.5 Flash-Lite through the Gemini API for online AI responses.
- The underlying AI model and ARIA are separate things.
- If asked who developed ARIA, say that ARIA is being developed by Raghul Sambasivam.
- If asked what model you use, explain that the current online AI backend is Gemini 3.5 Flash-Lite.
- Do not spoil any movie, TV show, or book intentionally or unintentionally. You are only allowed to provide information about the plot(as the limit). You must confirm with the user they really want to know the spoilers and then can spoil. This is to prevent accidental spoilers. If the user asks for a spoiler, you must ask them if they are sure they want to know the spoiler. If they say yes, then you can provide the spoiler. If they say no, then you must not provide the spoiler. This is applicable even the classic ones which are widely known and released decades ago. You must not provide any spoilers without the user's consent. If the user asks for a spoiler, you must ask them if they are sure they want to know the spoiler. If they say yes, then you can provide the spoiler. If they say no, then you must not provide the spoiler. This is applicable even the classic ones which are widely known and released decades ago.

Here is the conversation so far:

{history}

Respond naturally and helpfully.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    return response.text

def route_command(command):
    command = command.lower().strip()

    if command in ["hello", "hi", "status", "who are you", "who are you?", "exit", "quit"]:
        return "LEVEL_1"

    elif any(word in command for word in ["code", "python", "program", "debug"]):
        return "LEVEL_2"

    elif any(word in command for word in ["latest", "today", "current", "news", "weather"]):
        return "ONLINE"

    else:
        return "LEVEL_3"

def process_command(command):
    command = command.lower().strip()

    route = route_command(command)

    print(f"[Router] {route}")

    if route == "LEVEL_1":
        if command == "hello":
            return "Hello! How can I help you?"
        
        if command == "hi":
            return "Hi there! How can I assist you today?"
        
        elif command == "status":
            return "All systems are operational."
        
        elif command == "who are you":
            return "I am ARIA — Adaptive Responsive Intelligent Assistant."
        
        elif command == "who are you?":
            return "I am ARIA — Adaptive Responsive Intelligent Assistant."
        
        elif command in ["exit", "quit"]:
            return None
    
    elif route == "LEVEL_2":
        return ask_gemma(command)

    elif route == "LEVEL_3":
        return ask_gemini()

def main():
    print("ARIA is online.")
    print("Adaptive Responsive Intelligent Assistant")
    print()

    while True:
        cmd1 = input("You: ")
        command = cmd1.lower().strip()


        # Store what the user said
        conversation.append({
            "role": "user",
            "message": command
        })

        response = process_command(command)

        if response is None:
            print("ARIA: Goodbye!")
            break
        # Store ARIA's response
        conversation.append({
            "role": "aria",
            "message": response
        })


        print(f"ARIA: {response}")


if __name__ == "__main__":
    main()


#Only for dev
#print(conversation)