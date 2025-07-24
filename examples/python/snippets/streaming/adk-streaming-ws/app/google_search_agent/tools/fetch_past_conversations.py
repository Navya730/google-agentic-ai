import os

from google.cloud import firestore

project_id = os.getenv("PROJECT_ID")
db = firestore.Client(project=project_id)
def get_last_5_conversations(phone_number:str) -> dict:
    """
    Retrieves the past five conversations of the farmer.

    Args:
        phone_number (str): phone number of the user

    Returns:
        dict: past 5 conversations
    """

    try:

        conversations_ref = db.collection("conversations")
        query = (
            conversations_ref
            .where("user_id", "==", int(phone_number))
            # .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(5)
        )

        docs = query.stream()

        conversations = []
        for doc in docs:
            data = doc.to_dict()
            conversations.append(data)

        print(conversations)

        return {"conversations": conversations}
    except Exception as e:
        return {}


# get_last_5_conversations("846240145")