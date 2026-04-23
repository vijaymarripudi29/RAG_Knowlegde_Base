class RAGService:
    def __init__(self, vector_repo, llm_service):
        self.vector_repo = vector_repo
        self.llm = llm_service

    def query(self, user_id, question, embedding_fn, chat_history=None, session_id=None, query_mode="hybrid"):
        greeting = self._get_greeting_response(question)
        if greeting:
            return {
                "answer": greeting,
                "sources": []
            }

        query_emb = embedding_fn(question)

        docs = self.vector_repo.search(user_id, query_emb, session_id=session_id)

        if query_mode == "document_only" and not docs:
            answer = "I could not find relevant information in the uploaded documents for this chat."
        else:
            answer = self.llm.generate(question, docs, chat_history, document_only=query_mode == "document_only")

        return {
            "answer": answer,
            "sources": docs
        }

    def _get_greeting_response(self, question):
        normalized = question.strip().lower().strip("!.?, ")
        greetings = {
            "hi",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "namaste",
            "how are you",
            "how are you doing",
        }
        if normalized in greetings:
            return "Hello! How can I help you today?"
        return None
