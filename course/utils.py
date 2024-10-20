import openai

def generate_lesson_content(prompt):
    openai.api_key = 'your-openai-api-key'
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()
