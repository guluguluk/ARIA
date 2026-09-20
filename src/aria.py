import sys
from router import route_command
from models import ask_gemini


sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

conversation = []


def build_context():
    history = ""

    for message in conversation:
        history += f"{message['role']}: {message['message']}\n"

    return history


def build_gemini_prompt():
    history = build_context()

    prompt = f"""
You are ARIA - Adaptive Responsive Intelligent Assistant.

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

    return prompt

def process_command(command):
    command = command.lower().strip()

    if command in ["exit", "quit"]:
        return None

    if command == "hello":
        return "Hello! How can I help you?"

    if command == "hi":
        return "Hi there! How can I assist you today?"

    if command == "status":
        return "All systems are operational."

    if command in ["--version", "version"]:
        return "ARIA v1.0.0 (Online-first architecture with Google Gemini 3.5 Flash-Lite)"

    if command in ["who are you", "who are you?"]:
        return "I am ARIA - Adaptive Responsive Intelligent Assistant."

    if command in ["who developed you", "who developed you?"]:
        return "ARIA is being developed by Raghul Sambasivam."

    if command in ["who made you", "who made you?"]:
        return "ARIA is being developed by Raghul Sambasivam."

    route = route_command(command)

    print(f"[Router] {route}")

    if route == "ARIA_TOOL":
        return "ARIA tool routing is not configured yet."

    prompt = build_gemini_prompt()
    response = ask_gemini(prompt)
    return response


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


# Only for dev
# print(conversation)
