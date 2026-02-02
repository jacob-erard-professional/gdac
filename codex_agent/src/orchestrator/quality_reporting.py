def summarize_quality(cleaning_report: dict) -> dict:
    accepted = cleaning_report.get("accepted", 0)
    rejected = cleaning_report.get("rejected", 0)
    breakdown = cleaning_report.get("rejection_breakdown", {})
    return {
        "accepted_records": accepted,
        "rejected_records": rejected,
        "rejection_breakdown": breakdown,
    }
