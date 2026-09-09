from app.services.chunker import chunk_pages


pages = [
    {
        "page_number": 1,
        "text": (
            "This is a sample document. "
            "It contains information about annual leave, "
            "sick leave, and employee benefits."
        ),
    },
    {
        "page_number": 2,
        "text": (
            "Employees must submit leave requests "
            "through the internal HR system."
        ),
    },
]


chunks = chunk_pages(
    pages,
    chunk_size=80,
    overlap=20,
)


for chunk in chunks:
    print("=" * 60)
    print("Chunk:", chunk["chunk_index"])
    print("Page:", chunk["page_number"])
    print("Content:", chunk["content"])