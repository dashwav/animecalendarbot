import praw
import yaml
import schedule
import twitter
import datetime
import random
import requests
import json
import os
from time import sleep
from logging import Formatter, INFO, DEBUG, StreamHandler, getLogger
from utils import getDateStringWithSuffix, getDateStringWithoutSuffix, loadEnvConfig, getPushshiftUrl

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

    try:
      logger.info("Attempting to load config file...")
      with open("src/config/config.yml", 'r') as yml_config:
          config = yaml.safe_load(yml_config)
          logger.info("Config file loaded from src/config/config.yml")
    except FileNotFoundError:
      logger.info("No config file found, loading from environment variables instead")
      config = loadEnvConfig(logger)
      logger.info("All environment variables loaded")

    # Set up bot context
    self.config = config
    self.logger = logger
    self.dailyPosts = []

    # Generate the Reddit API instance
    self.reddit = praw.Reddit(client_id=config['creds']['reddit']['client_id'],
                              client_secret=config['creds']['reddit']['client_secret'],
                              user_agent='Python:AnimeCalendarBot:v0.0.1')
    self.subreddit = self.reddit.subreddit('animecalendar')

    # Generate the Twitter API Instance
    self.twitter = twitter.Api(consumer_key=config['creds']['twitter']['consumer_key'],
                               consumer_secret=config['creds']['twitter']['consumer_secret'],
                               access_token_key=config['creds']['twitter']['access_token'],
                               access_token_secret=config['creds']['twitter']['access_token_secret'])
    
    # This is where the tasks will get scheduled
    self.logger.info(f'Setting up tasks...')
    # TODO: improve this function to be a last check for any post for the day
    # schedule.every().day.at("18:30").do(self.lastDitchCheckForPosts)
    schedule.every().hour.at(:00).do(self.checkForHotPosts)
    self.logger.info(f'Tasks intitialized')

  def checkForHotPosts(self):
    # We want to check at the interval to see if there are any new posts of the day that break the threshold
    self.logger.debug(f"Starting regular check task: {datetime.datetime.now()}")
    url = getPushshiftUrl()
    self.logger.debug(f"Attempting to access {url}")
    r = requests.get(url)
    self.logger.debug(f"Request completed with status: {r.status_code}")
    if r.status_code != 200:
      self.logger.error(f"Request to {url} errored out with status code {r.status_code}")
      return
    data = json.loads(r.text)
    submissions = data["data"]
    top_post = None
    self.logger.debug(f'There are {len(submissions)} posts to go through')
    count = 0
    for post in submissions:
      count += 1
      if post['score'] < 50:
        self.logger.debug(f'Post {count}: {post["id"]} has a score below 50 - {post["score"]}')
        continue
      if post['id'] in self.dailyPosts:
        self.logger.debug(f'Post {count}: {post["id"]} has already been posted')
        continue
      if not top_post:
        top_post = post
        self.logger.debug(f'Post {count}: Top post has been set to {post["id"]}')
      if top_post['score'] < post['score']:
        top_post = post
        self.logger.debug(f'Post {count}: New top post is {post["id"]}')
    if not top_post:
      self.logger.debug(f'There were no posts found that matched the criteria')
      return
    self.logger.debug(f'Attempting to post {top_post["id"]} to twitter...')
    self.postImageToTwitter(top_post['title'], top_post['url'])
    self.dailyPosts.append(top_post['id'])

  def lastDitchCheckForPosts(self):
    # We only want to run this if there haven't been any other posts today
    if self.dailyPosts:
      return
    current_date = datetime.datetime.now()
    dateStringSuffix = getDateStringWithSuffix('%B {S}',current_date)
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
    self.logger.info("Posting image to twitter now")
    try:
      self.twitter.PostUpdate(title, media=image)
    except Exception as e:
      self.logger.critical(f"Error posting image to twitter: {e}")
    self.logger.info("Finished posting image to twitter")


  def run(self):
    while(True):
      schedule.run_pending()

if __name__ == '__main__':
  bot = Bot()
  bot.run()