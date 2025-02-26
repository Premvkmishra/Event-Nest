import mysql.connector
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_db_connection():
    conn = mysql.connector.connect(
        host="hopper.proxy.rlwy.net",
        user="root",
        password="zxyxhaUVPDNCsUSCEhEtVrPPTdlRnMIe",
        database="Event",
        port=45920
    )
    return conn

def execute_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    conn.commit()
    cursor.close()
    conn.close()

def fetch_query(query, params=()):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result
def fetch_events():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, domain FROM event")  
    events = cursor.fetchall()
    conn.close()
    return events

def get_recommendations(event_id):
    events = fetch_events()

    event_descriptions = [event["domain"] for event in events]
    event_ids = [event["id"] for event in events]

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(event_descriptions)

    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    event_index = event_ids.index(event_id)
    similar_indices = similarity_matrix[event_index].argsort()[::-1][1:6]  

    recommended_events = [event_ids[i] for i in similar_indices]

    return [event for event in events if event["id"] in recommended_events]
