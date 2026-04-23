import os
from core.config import settings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.llm.MODEL_NAME
        )
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", settings.llm.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        self.chain = self.prompt_template | self.llm

    def generate(self, question: str, docs: list, chat_history: list = None, document_only: bool = False):
        context = "\n".join(self._source_text(doc) for doc in docs)
        if chat_history is None:
            chat_history = []
        
        response = self.chain.invoke({
            "context": context,
            "document_only": "enabled" if document_only else "disabled",
            "chat_history": chat_history,
            "question": question
        })
        
        return response.content

    def stream(self, question: str, docs: list, chat_history: list = None, document_only: bool = False):
        context = "\n".join(self._source_text(doc) for doc in docs)
        if chat_history is None:
            chat_history = []

        for chunk in self.chain.stream({
            "context": context,
            "document_only": "enabled" if document_only else "disabled",
            "chat_history": chat_history,
            "question": question
        }):
            if chunk.content:
                yield chunk.content

    def _source_text(self, source):
        if isinstance(source, dict):
            label = source.get("filename") or "document"
            page = source.get("page_number")
            chunk = source.get("chunk_index")
            location = f"{label}"
            if page:
                location += f", page {page}"
            if chunk is not None:
                location += f", chunk {chunk}"
            return f"[{location}]\n{source.get('content', '')}"
        return str(source)
