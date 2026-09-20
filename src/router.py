# ARIA Intelligent Router
# Responsible for deciding whether a command should be handled by ARIA tools
# or routed to the online Gemini AI backend.

aria_tool_phrases = [
    # Future built-in tool trigger phrases can be added here
]

def route_command(command):
    """
    Determine the appropriate routing destination for a user command.
    Returns 'ARIA_TOOL' if a tool phrase matches, otherwise defaults to 'GEMINI'.
    """
    command = command.lower().strip()

    if any(phrase in command for phrase in aria_tool_phrases):
        return "ARIA_TOOL"

    return "GEMINI"