from pymongo import MongoClient
import os
from config import tickets_collection
from bson.objectid import ObjectId


def add_ticket_to_queue(ticket_data):
    """Inserts a new ticket into the database."""
    return tickets_collection.insert_one(ticket_data)

def get_assigned_tickets_by_email(email):
    """Finds a tickets assigned to a given email"""
    return tickets_collection.find({"assignedTo": email})  # Exclude MongoDB _id

def update_ticket(id, status):
    """Update data of a given ticket."""
    return tickets_collection.update_one({"_id": ObjectId(id)}, {"$set": {"status": status}})

def get_all_tickets():
    return tickets_collection.find()