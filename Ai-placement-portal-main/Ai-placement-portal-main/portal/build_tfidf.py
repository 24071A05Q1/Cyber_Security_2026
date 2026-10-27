from django.core.management.base import BaseCommand
from portal.recommender_tfidf import build_and_persist_job_tfidf


class Command(BaseCommand):
    help = 'Build and persist TF-IDF vectorizer and job matrix'


    def handle(self, *args, **kwargs):
        res = build_and_persist_job_tfidf()
        self.stdout.write(self.style.SUCCESS(f"Built TF-IDF for {res['count']} jobs"))