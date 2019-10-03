"""
Utils file to keep the main file clean
"""
import datetime
import os

def loadEnvConfig(logger):
  config = {}
  config['creds'] = {}
  config['creds']['reddit'] = {}
  config['creds']['reddit']['client_id'] = os.environ.get('REDDIT_CLIENT_ID')
  config['creds']['reddit']['client_secret'] = os.environ.get('REDDIT_CLIENT_SECRET')

  for key, value in config['creds']['reddit'].items():
    if not value:
      logger.critical(f"Config for ['reddit']['{key}'] not found, exiting...")
      raise SystemExit

  config['creds']['twitter'] = {}
  config['creds']['twitter']['consumer_key'] = os.environ.get('TWITTER_CONSUMER_KEY')
  config['creds']['twitter']['consumer_secret'] = os.environ.get('TWITTER_CONSUMER_SECRET')
  config['creds']['twitter']['access_token'] = os.environ.get('TWITTER_ACCESS_TOKEN')
  config['creds']['twitter']['access_token_secret'] = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

  for key, value in config['creds']['twitter'].items():
    if not value:
      logger.critical(f"Config for ['twitter']['{key}'] not found, exiting...")
      raise SystemExit
      
  return config

def suffix(d):
  return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def getDateStringWithSuffix(format: str, current_date: datetime):
  return current_date.strftime(format).replace(
    '{S}', str(current_date.day) + suffix(current_date.day))

def getDateStringWithoutSuffix(current_date: datetime):
  return f'{current_date.strftime("%B")} {str(current_date.day)}'