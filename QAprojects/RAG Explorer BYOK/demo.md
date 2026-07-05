# Demo Script (~1.5 min)

1. This is RAG Explorer — a visual tool I built to show exactly how Retrieval-Augmented Generation works, step by step.
2. Instead of hiding RAG behind a single chat box, it makes every stage visible: chunking, embedding, vector storage, retrieval, and generation.
3. For this project, I built a full-stack app — a React frontend paired with a Python FastAPI backend.
4. You can ask questions against a default document, or upload your own PDF, text, or markdown file as an isolated knowledge base you can switch to instantly.
5. When you ask a question, it embeds it, searches the vector database, and shows you the actual retrieved chunks with similarity scores — before generating an answer.
6. Only then does it send those chunks to an LLM through Groq, so the answer is grounded in real retrieved content, not guesswork.
7. A pipeline stepper animates through each stage live, so you're watching retrieval and generation happen in real time.
8. I also built it to run two ways — locally with Ollama and ChromaDB, and in production on Vercel using OpenAI embeddings and Pinecone.
9. That's RAG Explorer: a hands-on way to actually see retrieval and generation working together.
