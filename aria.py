def main():
    print("ARIA is online.")
    print("Adaptive Responsive Intelligent Assistant")
    print()

    while True:
        command = input("You: ")

        if command.lower() in ["exit", "quit"]:
            print("ARIA: Goodbye!")
            break

        print(f"ARIA: You said '{command}'")


if __name__ == "__main__":
    main()