import sys

from app.rag import answer_question


def main():
    if len(sys.argv) < 2:
        print('Usage: python ask.py "your question"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    result = answer_question(question)

    print("\nANSWER\n" + result["answer"])
    print("\nSOURCES")
    for i, s in enumerate(result["sources"], start=1):
        print(f"[{i}] {s['filename']} - page {s['page']} (distance {s['distance']:.3f})")


if __name__ == "__main__":
    main()