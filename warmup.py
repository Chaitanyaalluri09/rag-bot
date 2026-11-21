from sentence_transformers import SentenceTransformer,util
model=SentenceTransformer("all-MiniLM-L6-V2") #Model for creating embeddings
sentences=["The cat sat on the sofa",
           "Python is a popular programming language",
           "How do I reset my account password?",
           "Heavy rain is expected in chennai tomorrow",
           "Steps to recover access to your login"]
question="how will be the weather tomorrow?"
sentence_vectors=model.encode(sentences) #embedding vector
question_vector=model.encode(question)
scores=util.cos_sim(question_vector,sentence_vectors)[0] #similarity between vectors
best=int(scores.argmax()) #position of best similar vector
print(f"closest match: {sentences[best]}")
print(len(question_vector))