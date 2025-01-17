import praw
import schedule
import twitter
import datetime
import random
import requests
import json
import gila
import os
from logging import Formatter, DEBUG, StreamHandler, getLogger
from utils import getDateStringWithSuffix, getDateStringWithoutSuffix
from utils import getPushshiftUrl
from db import DbController


class Bot():
    """
    Oh boy here i go again
    """

    def __init__(self):
        # Set up Logger
        logger = getLogger('animecalendarbot')
        console_handler = StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s')
        )
        logger.addHandler(console_handler)
        logger.setLevel(DEBUG)

        gila.set_config_name("config")
        gila.add_config_path(f'{os.getcwd()}')
        gila.set_env_prefix("CLDR")
        try:
            logger.info("Attempting to load config file...")
            gila.read_in_config()
        except gila.util.errors.ConfigFileNotFound:
            logger.info("No config file found, falling back to ENV")
        gila.automatic_env()

        # Set up bot context
        self.logger = logger
        self.dailyPosts = []

        # Generate the Reddit API instance
        self.reddit = praw.Reddit(
            client_id=gila.get("reddit_client_id"),
            client_secret=gila.get("reddit_client_secret"),
            user_agent='Python:AnimeCalendarBot:v1.0.0')
        self.subreddit = self.reddit.subreddit('animecalendar')

        # Generate the Twitter API Instance
        self.twitter = twitter.Api(
            consumer_key=gila.get("twitter_consumer_key"),
            consumer_secret=gila.get("twitter_consumer_secret"),
            access_token_key=gila.get("twitter_access_token"),
            access_token_secret=gila.get("twitter_access_token_secret"))

        self.db = DbController()

        todays_posts = self.db.fetch_todays_posts()
        for post in todays_posts:
            self.dailyPosts.append(post['reddit']['id'])
        self.logger.info(f'Loaded in {len(todays_posts)} posts from firestore')

        # This is where the tasks will get scheduled
        self.logger.info(f'Setting up tasks...')
        # TODO: improve this function to be a last check for any post
        # schedule.every().day.at("18:30").do(self.lastDitchCheckForPosts)
        # schedule.every().hour.at(":00").do(self.checkForHotPosts)
        self.logger.info(f'Tasks intitialized')

    def checkForHotPosts(self):
        # We want to check at the interval to see if there are any new
        # posts of the day that break the threshold
        self.logger.debug(
            f"Starting regular check task: {datetime.datetime.now()}")
        url = getPushshiftUrl()
        self.logger.debug(f"Attempting to access {url}")
        r = requests.get(url)
        self.logger.debug(f"Request completed with status: {r.status_code}")
        if r.status_code != 200:
            self.logger.error(
                f"Request to {url} errored out with status code"
                f"{r.status_code}")
            return
        data = json.loads(r.text)
        submissions = data["data"]
        top_post = None
        self.logger.debug(f'There are {len(submissions)} posts to go through')
        count = 0
        for post in submissions:
            sub = self.reddit.submission(id=post["id"])
            count += 1
            if sub.score < 50:
                self.logger.debug(
                    f'Post {count}: {sub.id} has a score below 50 -'
                    f'{sub.score}')
                continue
            if sub.id in self.dailyPosts:
                self.logger.debug(
                    f'Post {count}: {sub.id} has already been posted')
                continue
            if not top_post:
                top_post = sub
                self.logger.debug(
                    f'Post {count}: Top post has been set to {sub.id}')
            if top_post.score < sub.score:
                top_post = sub
                self.logger.debug(f'Post {count}: New top post is {sub.id}')
        if not top_post:
            self.logger.debug(
                f'There were no posts found that matched the criteria')
            return
        self.logger.debug(f'Attempting to post {top_post.id} to twitter...')
        twitter_post = self.postImageToTwitter(top_post.title, top_post.url)
        if twitter_post:
            self.db.add_post(top_post, twitter_post)
            self.dailyPosts.append(top_post.id)

    def lastDitchCheckForPosts(self):
        # We only want to run this if there haven't been any other posts today
        if self.dailyPosts:
            return
        current_date = datetime.datetime.now()
        dateStringSuffix = getDateStringWithSuffix('%B {S}', current_date)
        dateStringBare = getDateStringWithoutSuffix(current_date)
        all_posts = []

        # Search for posts with suffix
        for post in self.subreddit.search(dateStringSuffix):
            if post.is_self:
                continue
            all_posts.append(post)

        # Search for posts without suffix
        for post in self.subreddit.search(dateStringBare):
            if post.is_self:
                continue
            all_posts.append(post)

        chosen_one = random.choice(all_posts)
        self.postImageToTwitter(chosen_one.title, chosen_one.url)

    def postImageToTwitter(self, title: str, image: str):
        self.logger.debug("Attempting to post image to twitter now")
        post = None
        try:
            post = self.twitter.PostUpdate(title, media=image)
        except Exception as e:
            self.logger.critical(f"Error posting image to twitter: {e}")
            return
        self.logger.debug("Finished attempting to post image to twitter")
        return post

    def run(self):
        while(True):
            schedule.run_pending()


if __name__ == '__main__':
    bot = Bot()
    bot.run()
