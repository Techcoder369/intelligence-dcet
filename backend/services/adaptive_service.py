from backend.models.database import SessionLocal, StudentPerformance

def update_performance(user_id, unit, is_correct):
    db = SessionLocal()

    record = db.query(StudentPerformance).filter_by(
        user_id=user_id,
        unit=unit
    ).first()

    if not record:
        record = StudentPerformance(
            user_id=user_id,
            unit=unit
        )
        db.add(record)

    record.total_attempted += 1
    if is_correct:
        record.correct_answers += 1

    record.accuracy = record.correct_answers / record.total_attempted
    db.commit()
    db.close()


def get_adaptive_difficulty(user_id, unit):
    db = SessionLocal()
    record = db.query(StudentPerformance).filter_by(
        user_id=user_id,
        unit=unit
    ).first()
    db.close()

    if not record or record.total_attempted < 5:
        return "easy"

    if record.accuracy >= 0.8:
        return "hard"
    elif record.accuracy >= 0.5:
        return "medium"
    else:
        return "easy"
