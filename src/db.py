import firebase_admin
from datetime import datetime
from logging import Formatter, DEBUG, StreamHandler, getLogger
from firebase_admin import credentials
from firebase_admin import firestore


class DbController():

    def __init__(self):
        # Use a service account
        cred = credentials.Certificate('src/config/serviceAccount.json')
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

        logger = getLogger('firestore')
        console_handler = StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(console_handler)
        logger.setLevel(DEBUG)
        self.logger = logger

    def add_post(self, submission, post):
        today = datetime.utcnow()
        month = today.strftime("%Y-%m-%B")
        date = today.strftime("%d")
        time = today.strftime("%H:%M")
        month_ref = self.db.collection(u'posts').document(month)
        month_doc = month_ref.get()
        if not month_doc.exists:
            self.logger.debug(f"Initializing the month document posts/{month}")
            month_ref.set({
                u'timestamp': firestore.SERVER_TIMESTAMP
            })
            month_doc = month_ref.get()
        day_str = f'{time}-{submission.id}'
        day_ref = month_ref.collection(date).document(day_str)
        day_ref.set({
            u'reddit': {
                u'id': submission.id,
                u'title': submission.title,
                u'url': submission.url,
                u'author': submission.author.name,
                u'permalink': submission.permalink
            },
            u'twitter': {
                u'id': post.id_str,
            }
        })
        self.logger.debug(f"Submission added to firebase: {day_str}")

    def fetch_todays_posts(self):
        today = datetime.utcnow()
        month = today.strftime("%Y-%m-%B")
        date = today.strftime("%d")
        month_ref = self.db.collection(u'posts').document(month)
        month_doc = month_ref.get()
        if not month_doc.exists:
            return None
        day_ref = month_ref.collection(date).stream()
        todays_posts = []
        for post in day_ref:
            todays_posts.append(post.to_dict())
        return todays_posts
