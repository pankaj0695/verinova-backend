from pymongo import MongoClient
import os
from config import support_emp_collection

def get_employee_by_email(email):
    return support_emp_collection.find_one({"email":email})


def add_employees(emp_data):
    """Inserts a new ticket into the database."""
    return support_emp_collection.insert_many(emp_data)

def get_least_loaded_employee():
    toReturn = support_emp_collection.find_one({}, sort=[("ticket_count", 1)])
    support_emp_collection.update_one(toReturn, {"$inc": {'ticket_count': 1}})
    return toReturn

def get_all_employees():
    return support_emp_collection.find()