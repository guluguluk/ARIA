from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

def ask_gemma(command):
    response = client.chat.completions.create(
        model="google/gemma-3-1b",
        messages=[
            {
                "role": "user",
                "content": command
            }
        ]
    )

    return response.choices[0].message.content


print(ask_gemma("Explain what a Python list is in one sentence."))