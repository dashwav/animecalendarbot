"""
Utils file to keep the main file clean
"""
from datetime import timezone, datetime


def suffix(d):
    if 11 <= d <= 13:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def getDateStringWithSuffix(format: str, current_date: datetime):
    return current_date.strftime(format).replace(
        '{S}', str(current_date.day) + suffix(current_date.day))


def getDateStringWithoutSuffix(current_date: datetime):
    return f'{current_date.strftime("%B")} {str(current_date.day)}'


def getPushshiftUrl():
    today = datetime.utcnow()
    base_url = "https://api.pushshift.io/reddit/search/submission"
    day_start = int(datetime(today.year, today.month, today.day,
                             0, 0, 0, 0, timezone.utc).timestamp())
    return f"{base_url}?subreddit=animecalendar&after={day_start}"
