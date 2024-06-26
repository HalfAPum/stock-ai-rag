import argparse
import time
import datetime
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE_WITH_CONTEXT = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""


PROMPT_TEMPLATE_PLAN = """
Answer the question: {question}
"""


def main():
    # Create CLI.
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text
    query_rag(query_text)


def query_rag(query_text: str):
    # Prepare the DB.
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt = get_formatted_prompt(context=context_text, question=query_text)
    print(prompt)

    model = Ollama(model="llama3")
    request_time_start = time.time()
    response_text = model.invoke(prompt)
    request_time_difference = datetime.timedelta(seconds=int((time.time() - request_time_start)))
    print("--- Llama 3 response time: %s ---" % request_time_difference)

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)
    return response_text


def get_formatted_prompt(context: str, question: str) -> str:
    if context:
        print("Context has been found: \n" + context)
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE_WITH_CONTEXT)
        return prompt_template.format(context=context, question=question)
    else:
        print("Context is empty. Ask plain question.")
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE_PLAN)
        return prompt_template.format(question=question)


if __name__ == "__main__":
    main()
