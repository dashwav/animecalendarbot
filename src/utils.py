"""
Utils file to keep the main file clean
"""
import datetime


def suffix(d):
  return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def getDateStringWithSuffix(format: str, current_date: datetime):
  return current_date.strftime(format).replace(
    '{S}', str(current_date.day) + suffix(current_date.day))

def getDateStringWithoutSuffix(current_date: datetime):
  return f'{current_date.strftime("%B")} {str(current_date.day)}'