from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)

db = client[DB_NAME]

leads_collection = db["leads"]


def save_lead(name, email, phone):

    # Avoid duplicate emails

    existing_user = leads_collection.find_one(
        {"email": email}
    )

    if existing_user:
        return "Lead already exists"

    lead_data = {
        "name": name,
        "email": email,
        "phone": phone,
        "created_at": datetime.utcnow()
    }

    result = leads_collection.insert_one(
        lead_data
    )

    return str(result.inserted_id)


def get_all_leads():

    return list(
        leads_collection.find(
            {},
            {
                "_id": 0,
                "name": 1,
                "email": 1,
                "phone": 1,
                "created_at": 1
            }
        )
    )


def delete_lead(email):

    result = leads_collection.delete_one(
        {"email": email}
    )

    return result.deleted_count


def test_connection():

    try:

        client.admin.command("ping")

        print(
            "MongoDB Connected Successfully"
        )

        return True

    except Exception as e:

        print(
            f"MongoDB Connection Error: {e}"
        )

        return False


if __name__ == "__main__":

    test_connection()