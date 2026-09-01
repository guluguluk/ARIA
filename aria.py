conversation = []


def process_command(command):
    command = command.lower().strip()

    if command == "hello":
        return "Hello! How can I help you?"

    elif command == "status":
        return "All systems are operational."

    elif command == "who are you":
        return "I am ARIA — Adaptive Responsive Intelligent Assistant."

    elif command in ["exit", "quit"]:
        return None

    else:
        return "I don't understand that command yet."


def main():
    print("ARIA is online.")
    print("Adaptive Responsive Intelligent Assistant")
    print()

    while True:
        command = input("You: ")

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