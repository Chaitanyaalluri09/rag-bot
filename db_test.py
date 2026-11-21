import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "The cat sat on the sofa.",
    "Python is a popular programming language.",
    "How do I reset my account password?",
    "Heavy rain is expected in Chennai tomorrow.",
    "Steps to recover access to your login.",
]
question = "I forgot my password, what should I do?"

# Connect to the database running in Docker
conn = psycopg.connect(
    "host=localhost port=5432 dbname=ragdb user=postgres password=ragpass",
    autocommit=True,
)
conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
register_vector(conn)

# Fresh table: 384 numbers per row, matching our model
conn.execute("DROP TABLE IF EXISTS sentences")
conn.execute(
    "CREATE TABLE sentences (id SERIAL PRIMARY KEY, content TEXT, embedding vector(384))"
)

# Store each sentence with its embedding
vectors = model.encode(sentences)
for text, vec in zip(sentences, vectors):
    conn.execute(
        "INSERT INTO sentences (content, embedding) VALUES (%s, %s)", (text, vec)
    )

# Search: find the 3 closest sentences to the question
question_vector = model.encode(question)
rows = conn.execute(
    "SELECT content, embedding <=> %s AS distance FROM sentences ORDER BY distance LIMIT 3",
    (question_vector,),
).fetchall()

for content, distance in rows:
    print(f"{distance:.3f}  {content}")