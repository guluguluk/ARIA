from google import genai

conversation = []

client = genai.Client()
def ask_gemini(command):
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=command
    )

    return response.text
conversation = []
def process_command(command):
    command = command.lower().strip()

    if command == "hello":
        return "Hello! How can I help you?"

    elif command == "hi":
        return "Hi there! How can I assist you today?"

    elif command == "status":
        return "All systems are operational."

    elif command == "who are you":
        return "I am ARIA — Adaptive Responsive Intelligent Assistant."

    elif command == "who are you?":
        return "I am ARIA — Adaptive Responsive Intelligent Assistant."

    elif command in ["exit", "quit"]:
        return None

    else:
        return ask_gemini(command)


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