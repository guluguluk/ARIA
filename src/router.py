aria_tool_phrases = []

def route_command(command):
    command = command.lower().strip()

    if any(phrase in command for phrase in aria_tool_phrases):
        return "ARIA_TOOL"

    return "GEMINI"