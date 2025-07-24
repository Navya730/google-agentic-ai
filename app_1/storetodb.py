import os
from datetime import datetime
from google.cloud import firestore
project_id = os.getenv("PROJECT_ID")
db = firestore.Client(project=project_id)

def save_conversation(user_id, messages):
    conversation_data = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "messages": messages
    }
    db.collection("conversations").add(conversation_data)
    print("Conversation saved to Firestore!")


