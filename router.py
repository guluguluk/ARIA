from openai import OpenAI

router_client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)


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

LEVEL_2:
Simple questions, explanations, casual conversation, translation,
and lightweight general tasks.

LEVEL_3:
Programming and coding tasks.
Examples:
- write Python code
- create a program
- debug code
- fix a program
- write a game
- solve a programming problem

LEVEL_4:
Requests requiring current or online information.
Examples:
- latest news
- today's weather
- current events
- current information

IMPORTANT:
- "Python" by itself does NOT mean LEVEL_3.
- If the user asks for an explanation about Python, use LEVEL_2.
- If the user asks to WRITE, CREATE, DEBUG, or FIX code, use LEVEL_3.
- Respond with ONLY one of:
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