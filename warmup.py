from sentence_transformers import SentenceTransformer,util
model=SentenceTransformer("all-MiniLM-L6-V2")
sentences=["The cat sat on the sofa",
           "Python is a popular programming language",
           "How do I reset my account password?",
           "Heavy rain is expected in chennai tomorrow",
           "Steps to recover access to your login"]
question="how will be the weather tomorrow?"
sentence_vectors=model.encode(sentences)
question_vector=model.encode(question)
scores=util.cos_sim(question_vector,sentence_vectors)[0]
best=int(scores.argmax())
print(f"closest match: {sentences[best]}")
print(len(question_vector))