import os
import anthropic
from pypdf import PdfReader

DATA_DIR = "./data"

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

file_names = []

def summarize_documents():
    summaries = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(DATA_DIR, filename)
            file_names.append(pdf_path)
            if os.path.exists(f"./summary/summary_{filename}.txt"):
                with open(f"./summary/summary_{filename}.txt", "r") as file:
                    summary = file.read()
                    summaries.append(summary)
                continue


            
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                number_of_pages = len(reader.pages)
                text = ''.join([page.extract_text() for page in reader.pages])
                message = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    temperature=0,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Summarize this document in words: {text}"
                                }
                            ]
                        }
                    ]
                )

                res = message.content
                summaries.append(res[0].text)
                with open(f"./summary/summary_{filename}.txt", "w") as file:
                    file.write(res[0].text)

    # print(summaries)

    return summaries

def create_context(rel_index, file_names):
    context = ""
    for index in rel_index:
        file_name = file_names[index]
        print(file_name)
        with open(file_name, 'rb') as file:
            reader = PdfReader(file)
            number_of_pages = len(reader.pages)
            text = ''.join([page.extract_text() for page in reader.pages])

            context += text
            
    return context

summaries = summarize_documents()
messages = []
print(file_names)

while True:
    query = input("Ask a question: ")
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": query
                }
            ]
        }
    )

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        system=f"This is a list of summaries, {summaries}.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Find the indices of the top 5 most relevant summaries for this question: {query}. Only output the list of (index, score) and no other text, only the list with no other english words."
                    }
                ]
            }
        ]
    )

    res = message.content
    res = res[0].text

    # read the string as a list of tuples
    res = eval(res)
    print(res)

    best_indices = []

    for index, score in res:
        if score > 0.1:
            best_indices.append(index)

    best_context = create_context(best_indices, file_names)

    # exit()

    message = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        system=f"This is some relevent context: {best_context}. Answer the questions based on this context.",
        messages=messages
    )

    res = message.content
    print(res[0].text)
    messages.append(
        {
            "role": "assistant",
            "content": res[0].text
        }
    )