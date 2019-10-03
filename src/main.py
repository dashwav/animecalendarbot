import praw
import yaml
import schedule
import twitter
import datetime
import random
import os
from time import sleep
from logging import Formatter, INFO, StreamHandler, getLogger
from utils import getDateStringWithSuffix, getDateStringWithoutSuffix, loadEnvConfig

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
    logger.setLevel(INFO)

    try:
      with open("src/config/config.yml", 'r') as yml_config:
          config = yaml.safe_load(yml_config)
    except FileNotFoundError:
      logger.info("No config file found, loading from environment variables instead")
      config = loadEnvConfig(logger)
      logger.info("All environment variables loaded")

    # Set up bot context
    self.config = config
    self.logger = logger

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
    schedule.every().day.at("10:30").do(self.checkForPosts)

  def checkForPosts(self):
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