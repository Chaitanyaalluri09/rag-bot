import sys

from app.ingest_service import ingest_pdf


def main():
    if len(sys.argv) != 2:
        print("Usage: python ingest.py data/mydoc.pdf")
        sys.exit(1)
    print(ingest_pdf(sys.argv[1], show_progress=True))


if __name__ == "__main__":
    main()