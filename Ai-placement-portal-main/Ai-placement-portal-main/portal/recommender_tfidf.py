import os
import pickle
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from .models import Job


VECT_PICKLE = os.path.join(settings.BASE_DIR, 'portal_tfidf_vectorizer.pkl')
MATRIX_PICKLE = os.path.join(settings.BASE_DIR, 'portal_tfidf_jobmatrix.pkl')
JOBIDS_PICKLE = os.path.join(settings.BASE_DIR, 'portal_tfidf_jobids.pkl')


def build_and_persist_job_tfidf():
    jobs = Job.objects.all()
    job_texts = []
    job_ids = []

    for j in jobs:
        text = f"{j.title}\n{j.description}"
        job_texts.append(text)
        job_ids.append(j.id)

    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    job_matrix = vectorizer.fit_transform(job_texts)

    with open(VECT_PICKLE, 'wb') as f:
        pickle.dump(vectorizer, f)
    with open(MATRIX_PICKLE, 'wb') as f:
        pickle.dump(job_matrix, f)
    with open(JOBIDS_PICKLE, 'wb') as f:
        pickle.dump(job_ids, f)

    return {'count': len(job_ids)}


def recommend_jobs_by_tfidf(resume_text: str, top_k=5):
    if not os.path.exists(VECT_PICKLE) or not os.path.exists(MATRIX_PICKLE):
        return []

    with open(VECT_PICKLE, 'rb') as f:
        vectorizer = pickle.load(f)
    with open(MATRIX_PICKLE, 'rb') as f:
        job_matrix = pickle.load(f)
    with open(JOBIDS_PICKLE, 'rb') as f:
        job_ids = pickle.load(f)

    q = vectorizer.transform([resume_text])
    sims = cosine_similarity(q, job_matrix).flatten()
    top_idx = sims.argsort()[::-1][:top_k]

    results = []
    for i in top_idx:
        results.append({
            'job_id': int(job_ids[i]),
            'score': float(sims[i])
        })

    return results
