from pymongo import MongoClient
import os
from config import accounts_collection


def add_accounts(account_data):
    """Inserts a new ticket into the database."""
    return accounts_collection.insert_many(account_data)

def get_account_by_aadhar(aadhar):
    return accounts_collection.find_one({"aadhar_number": aadhar}, {"_id": 0, "aadhar_number": 0})