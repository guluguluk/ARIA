from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

def ask_qwen(command):
    response = client.chat.completions.create(
        model="qwen2.5-coder-7b-instruct",
        messages=[
            {
                "role": "user",
                "content": command
            }
        ]
    )

    return response.choices[0].message.content


print(ask_qwen("Write a Python program that checks whether a number is odd or even."))