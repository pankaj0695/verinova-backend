from config import tickets_collection  # Import database connection

def get_assigned_tickets_by_email(email):
    """Fetch unresolved tickets assigned to a specific user."""
    return tickets_collection.find(
        {"assigned_to": email, "resolved": False},
        {"_id": 1, "user": 1, "type": 1, "cibil": 1, "query": 1, "resolved": 1}
    )

def resolve_ticket(ticket_id):
    """Mark a ticket as resolved."""
    result = tickets_collection.update_one({"_id": ticket_id}, {"$set": {"resolved": True}})
    return result.modified_count > 0  # Returns True if updated