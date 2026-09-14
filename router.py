from openai import OpenAI

router_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

def detect_obvious_route(command):
    command = command.lower().strip()

    # Level 1 — Built-in ARIA commands
    if any(phrase in command for phrase in [
        "hello", "hi", "hey",
        "who are you",
        "who developed you",
        "who made you",
        "status",
        "exit",
        "quit"
    ]):
        return "LEVEL_1"

    # Level 3 — Clear programming requests
    if any(phrase in command for phrase in [
        "write code",
        "write a program",
        "create code",
        "create a program",
        "write python code",
        "write a python program",
        "debug this",
        "fix this code",
        "fix this program",
        "code this",
        "program this"
    ]):
        return "LEVEL_3"

    # Level 4 — Clearly current/online information
    if any(phrase in command for phrase in [
        "latest",
        "today",
        "current",
        "right now",
        "news",
        "weather",
        "upcoming",
        "release date",
        "when will"
    ]):
        return "LEVEL_4"

    # Nothing obvious
    return None

def classify_command(command):
    prompt = f"""
You are a routing classifier for ARIA.

Your ONLY job is to choose the correct routing level.

ROUTING RULES:

LEVEL_1:
Built-in ARIA commands such as:
- hello
- hi
- who are you
- who made you
- who developed you
- status
- exit
- quit

IMPORTANT:
LEVEL_1 is ONLY for commands that directly interact
with ARIA's built-in identity or system commands.

General requests such as jokes, stories, games,
conversation, explanations, opinions, and casual
entertainment are NOT LEVEL_1 and must be classified under any other appropriate level.

LEVEL_2:
General questions, explanations, casual conversation,
translation, opinions, and lightweight tasks.

Examples:
- explain quantum entanglement
- what is photosynthesis
- translate this sentence
- tell me a joke

LEVEL_3:
Programming and coding tasks.

The user must be asking ARIA to CREATE, WRITE, DEBUG,
FIX, or SOLVE programming/code.

Examples:
- write a Python program
- create a calculator
- debug this code
- fix this program
- write a game
- solve this programming problem

IMPORTANT:
Mentioning a programming language does NOT automatically
mean LEVEL_3.

Example:
"Explain Python lists" → LEVEL_2
"Write a Python program" → LEVEL_3

LEVEL_4:
Requests involving current, recent, upcoming, or
time-sensitive information.

This includes:
- latest information
- today's information
- current events
- news
- weather
- upcoming events
- future projects
- release dates
- upcoming movies, games, products, or technology
- asking when something will happen
- asking what is coming next

Examples:
- what's the weather today
- latest Marvel news
- upcoming MCU projects
- future MCU projects
- when will this movie release
- what games are coming next

IMPORTANT:
If a request refers to something upcoming, future,
latest, current, or time-sensitive, choose LEVEL_4
even if it does not explicitly contain words like
"latest" or "today".

Respond with ONLY one of:
LEVEL_1
LEVEL_2
LEVEL_3
LEVEL_4

USER REQUEST:
{command}
"""

    response = router_client.chat.completions.create(
        model="google/gemma-3-1b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()

def validate_route(route):
    valid_levels = [
        "LEVEL_1",
        "LEVEL_2",
        "LEVEL_3",
        "LEVEL_4"
    ]

    if route in valid_levels:
        return route

    return "LEVEL_2"

def get_route(command):
    obvious_route = detect_obvious_route(command)

    if obvious_route is not None:
        return obvious_route

    route = classify_command(command)
    return validate_route(route)

#validate route function testing
# print(validate_route("LEVEL_3"))
# print(validate_route("LEVEL_7"))
# print(validate_route("I think LEVEL_3"))

#only for overall testing
tests = [
    "Write a Python program to sort a list.",
    "Explain what a Python list is.",
    "Who are you?",
    "What is the latest news?"
]

# for test in tests:
#     route = classify_command(test)
#     route = validate_route(route)

#     print(test)
#     print(route)
#     print()

#detect_obvious_route function testing
# if __name__ == "__main__":
#     tests = [
#         "What's the weather today?",
#         "Who developed you?",
#         "Write a Python calculator.",
#         "Explain quantum entanglement simply.",
#         "When will Spider-Man: Beyond the Spider-Verse release?"
#     ]

#     for test in tests:
#         print(test)
#         print("→", detect_obvious_route(test))
#         print()

#get_route function testing
if __name__ == "__main__":
    tests = [
    "Future MCU Projects",
    "Upcoming Marvel movies",
    "Explain Python dictionaries",
    "Create a Python game",
    "What is quantum entanglement?",
    "What's the latest news?",
    "When will the next GTA game release?",
    "Tell me a joke",
    "Tell me something funny",
    "Make me laugh",
    "Tell me a joke",
    "What's a joke?",
    "Explain gravity simply",
    "Have a casual conversation with me"
    ]

    for test in tests:
        print(test)
        print("→", get_route(test))
        print()