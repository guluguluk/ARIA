import sys
import re
from router import route_command
from models import ask_gemini
from memory import MemoryStore


sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

conversation = []
memory_store = None


def initialize_memory(db_path=None):
    """Initialize ARIA's permanent memory store with an optional database path."""
    global memory_store
    memory_store = MemoryStore(db_path=db_path)
    return memory_store


def _get_memory_store():
    if memory_store is None:
        return initialize_memory()
    return memory_store


def _handle_memory_command(command, store):
    """Handle only explicit, fully-formed permanent-memory commands."""
    remember_match = re.fullmatch(
        r"remember that\s+(.+?)\s+is\s+(.+)", command, re.IGNORECASE
    )
    if remember_match:
        key = remember_match.group(1).strip().casefold()
        content = remember_match.group(2).strip()
        if key and content:
            store.store_memory(key, content)
            return "I'll remember that."

    retrieve_match = re.fullmatch(
        r"what do you remember about\s+(.+?)[?]?", command, re.IGNORECASE
    )
    if retrieve_match:
        key = retrieve_match.group(1).strip().casefold()
        content = store.get_memory(key)
        if content is None:
            return f"I don't remember anything about {key}."
        return f"I remember that {key} is {content}."

    if re.fullmatch(r"what do you remember[?]?", command, re.IGNORECASE):
        memories = store.list_memories()
        if not memories:
            return "I don't have any stored memories."
        lines = ["I remember:"]
        lines.extend(f"- {key}: {content}" for key, content in memories.items())
        return "\n".join(lines)

    forget_match = re.fullmatch(r"forget\s+(.+?)[?]?", command, re.IGNORECASE)
    if forget_match:
        key = forget_match.group(1).strip().casefold()
        if store.delete_memory(key):
            return "I forgot that memory."
        return f"I don't have a memory for {key}."

    return None


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

def process_command(command, store=None):
    command = command.strip()
    normalized_command = command.casefold()
    active_store = store or _get_memory_store()

    if normalized_command in ["exit", "quit"]:
        return None

    memory_response = _handle_memory_command(command, active_store)
    if memory_response is not None:
        return memory_response

    if normalized_command == "hello":
        return "Hello! How can I help you?"

    if normalized_command == "hi":
        return "Hi there! How can I assist you today?"

    if normalized_command == "status":
        return "All systems are operational."

    if normalized_command in ["--version", "version"]:
        return "ARIA v1.0.0 (Online-first architecture with Google Gemini 3.5 Flash-Lite)"

    if normalized_command in ["who are you", "who are you?"]:
        return "I am ARIA - Adaptive Responsive Intelligent Assistant."

    if normalized_command in ["who developed you", "who developed you?"]:
        return "ARIA is being developed by Raghul Sambasivam."

    if normalized_command in ["who made you", "who made you?"]:
        return "ARIA is being developed by Raghul Sambasivam."

    route = route_command(normalized_command)

    print(f"[Router] {route}")

    if route == "ARIA_TOOL":
        return "ARIA tool routing is not configured yet."

    prompt = build_gemini_prompt()
    response = ask_gemini(prompt)
    return response


def main():
    initialize_memory()
    print("ARIA is online.")
    print("Adaptive Responsive Intelligent Assistant")
    print()

    while True:
        cmd1 = input("You: ")
        command = cmd1.strip()

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
