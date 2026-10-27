import numpy as np


def cosine_sim(a, b):
        a = np.array(a)
        b = np.array(b)
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)




def skills_match_ratio(candidate_skills, job_skills):
    if not job_skills:
        return 0.0
    cand = set([s.lower() for s in candidate_skills or []])
    job = set([s.lower() for s in job_skills or []])        