import anthropic

from ai_pipelines.embedders import embed
from ai_pipelines.vector_store import search

client = anthropic.Anthropic()

def _ask_claude(prompt):
    return client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

from openai import OpenAI

def test_local_llm(response):
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    r = client.chat.completions.create(
        model="qwen3:14b",
        messages=[{"role": "user", "content": response}],
    )
    print(r)
    print(r.choices[0].message.content)

def ask(question, top_k=5):
    # embed the question
    question_vectorized = embed(question)
    prompt= f"""
    Voici la question posée en entrée {question}

    A partir des contenu ressorti par la base vectorielle répond le mieux à la question.

    N'hallucine pas, n'invente rien qui n'est pas fourni par ce que tu as comme contenu fourni.

    Si jamais tu constate qu'un document est plus pertinent que les autres n'hesite pas a le faire remonter via son Document id

    Voici les 10 vecteurs les plus simmilaires par rapport a la base documentaire : 
    """
    top_sim_vectors = search(question_vectorized,top_k)
    for vector in top_sim_vectors:
        prompt += str(vector["content"]) + \
        "\n" + f"Et son score de similarité {vector["score"]}\n" \
        f"Et son document id {vector["document_id"]} \n"
    
    # Call Claude API
    test_local_llm(prompt)