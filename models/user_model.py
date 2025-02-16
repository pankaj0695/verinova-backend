from pymongo import MongoClient
import os
from config import users_collection


def create_user(user_data):
    """Inserts a new user into the database."""
    users_collection.insert_one(user_data)

def find_user_by_mobile(mobile_no):
    """Finds a user by their mobile number."""
    return users_collection.find_one({"mobile_no": mobile_no}, {"_id": 0})  # Exclude MongoDB _id

def find_user_by_aadhar(aadhar_number):
    """Finds a user by their Aadhar number."""
    return users_collection.find_one({"aadhar_number": aadhar_number}, {"_id": 0})

def find_user_by_pan(pan_number):
    """Finds a user by their PAN number."""
    return users_collection.find_one({"pan_number": pan_number}, {"_id": 0})
