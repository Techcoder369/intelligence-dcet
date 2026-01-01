from backend.services.rag_service import rag_service

def train_pyq():
    pyqs = [
        {
            "text": "What is the full form of ATM?",
            "unit": "Computer Fundamentals",
            "difficulty": "easy"
        },
        {
            "text": "Define Ohm’s Law.",
            "unit": "Electrical Engineering",
            "difficulty": "easy"
        },
        {
            "text": "Which memory is volatile?",
            "unit": "Computer Fundamentals",
            "difficulty": "medium"
        }
    ]

    for q in pyqs:
        rag_service.add_document(
            text=q["text"],
            metadata={
                "type": "pyq",
                "unit": q["unit"],
                "difficulty": q["difficulty"]
            }
        )

    print("✅ PYQ training completed")

if __name__ == "__main__":
    train_pyq()
