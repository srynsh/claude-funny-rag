import os
import anthropic
from pypdf import PdfReader

DATA_DIR = "./data"

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

file_names = []

def make_call(messgaes, system_data = None):
    if (system_data == None):
        return client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0,
            messages=messgaes
        )
              
    return client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0,
        system=system_data,
        messages=messgaes
    )

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
                text = ''.join([page.extract_text() for page in reader.pages])
                command = [
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

                response = make_call(command)
                response = response.content
                summaries.append(response[0].text)
                with open(f"./summary/summary_{filename}.txt", "w") as file:
                    file.write(res[0].text)

    return summaries

def create_context(rel_index, file_names):
    context = ""
    print(rel_index)
    print(file_names)
    for index in rel_index:
        file_name = file_names[index]
        with open(file_name, 'rb') as file:
            reader = PdfReader(file)
            text = ''.join([page.extract_text() for page in reader.pages])

            context += text
            
    return context

summaries = summarize_documents()
conversation = []

while True:
    query = input("Ask a question: ")
    if query == "quit":
        break

    conversation.append(
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


    system_message = f"This is a list of summaries, {summaries}."
    command = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Find the indices of the top 5 most relevant summaries for this question: {query}. Only output the list of (index, score) with 0 indexing and no other text, only the list with no other english words."
                }
            ]
        }
    ]
    best_docs = make_call(command, system_message).content
    # best_docs = best_docs.content
    best_docs = eval(best_docs[0].text)

    # best_docs = eval(best_docs)

    best_indices = []

    for index, score in best_docs:
        if score > 0.1:
            best_indices.append(index)

    print(best_indices)

    best_context = create_context(best_indices, file_names)

    system_message = f"This is some relevent context: {best_context}. Answer the questions based on this context. If you fell that the context is not relevent then ignore it. If there is any issue then return an empty list but never any other text."
    response = make_call(conversation, system_message)

    response = response.content
    print(response[0].text)
    conversation.append(
        {
            "role": "assistant",
            "content": response[0].text
        }
    )