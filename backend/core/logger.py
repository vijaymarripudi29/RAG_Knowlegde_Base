import logging

logging.basicConfig(
    filename="rag_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

def log(query, response):
    logging.info(f"Q: {query} | A: {response}")