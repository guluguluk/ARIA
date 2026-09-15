def estimate_complexity(command):
    command = command.lower().strip()

    score = 0

    # Length
    if len(command) > 150:
        score += 1

    if len(command) > 300:
        score += 1

    # Advanced task signals
    if any(phrase in command for phrase in [
        "analyze",
        "design",
        "architecture",
        "implement",
        "debug",
        "compare",
        "evaluate",
        "optimize"
    ]):
        score += 2

    # Detailed reasoning signals
    if any(phrase in command for phrase in [
        "step by step",
        "in detail",
        "deep analysis",
        "thoroughly",
        "deeply"
    ]):
        score += 1

    # Explicit difficulty
    if any(word in command for word in [
        "complex",
        "difficult",
        "advanced"
    ]):
        score += 2

    # Multiple requirements
    if command.count(" and ") >= 2:
        score += 2

    # Convert score to complexity
    if score >= 5:
        return "HIGH"

    elif score >= 2:
        return "MEDIUM"

    return "LOW"

def route_command(command):
    command = command.lower().strip()

    if command.rstrip("?!.") in [
        "hello",
        "hi",
        "hey",
        "who are you",
        "who developed you",
        "who made you",
        "status",
        "exit",
        "quit"
    ]:
        return "ARIA_TOOL"

    return "GEMINI_3_5_FLASH_LITE"

def select_model(command):
    route = route_command(command)

    if route == "ARIA_TOOL":
        return "ARIA_TOOL"

    complexity = estimate_complexity(command)

    if complexity in ["MEDIUM", "HIGH"]:
        return "GEMINI_3_6_FLASH"

    return "GEMINI_3_5_FLASH_LITE"

#route_command test
# if __name__ == "__main__":
#     tests = [
#         "Who are you?",
#         "Tell me a joke",
#         "Write a Python program",
#         "Explain quantum entanglement",
#         "What's the weather today?"
#     ]

#     for test in tests:
#         print(test)
#         print("→", route_command(test))
#         print()

#select_model test
# print(select_model("Tell me a joke", "LOW"))
# print(select_model("Solve this difficult problem", "HIGH"))
# print(select_model("Who are you?", "HIGH"))

#estimate_complexity test
tests = [
    "Tell me a joke",
    "Explain photosynthesis",
    "Write a Python program",
    "Explain quantum mechanics in detail",
    "Analyze and compare these two software architectures step by step",
    "Design a complex multi-device AI assistant architecture with memory, tools, permissions, and offline support"
]

for test in tests:
    complexity = estimate_complexity(test)
    model = select_model(test)

    print(test)
    print("Complexity:", complexity)
    print("Model:", model)
    print()