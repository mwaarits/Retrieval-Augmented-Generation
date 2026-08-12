from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a helpful assistant answering questions based ONLY on the provided context.
Rules:
1. Grounding: Base your entire response strictly on the facts presented in the context. Do not use any external knowledge, assumptions, or extrapolation from your pre-trained memory.
2. Missing Information: If the context does not contain enough information to answer the query completely, you must respond with: "I cannot find this information in the provided documents." Do not guess or fill in gaps.
3. Conflict Resolution: If multiple context blocks contradict each other, explicitly note the discrepancy based only on the provided text rather than choosing a side arbitrarily.
4. Tone & Style: Maintain an objective, professional, and concise tone. Avoid conversational filler. Answer without markdown symbol.

Context:
Konteks:
{context}""",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)
