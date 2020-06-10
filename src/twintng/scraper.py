# This file is part of TwintNG
# Author: richard@trollrensics.com
# License: MIT

import requests
import json
from bs4 import BeautifulSoup
import re
import time
import urllib
import datetime
import logging
import json

def convertToInt(x):
    multDict = {
        "k" : 1000,
        "m" : 1000000,
        "b" : 1000000000,
    }
    try:
        if ',' in x:
            x = x.replace(',', '')
        y = int(x)
        return y
    except:
        pass

    try:
        y = float(str(x)[:-1])
        y = y * multDict[str(x)[-1:].lower()]
        return int(y)
    except:
        pass

    return 0

def runSearch(search):
  params = {
    'vertical': 'default',
    'src': 'unkn',
    'include_available_features': '1',
    'include_entities': '1',
    'reset_error_state': 'false',
    'max_position': '-1',
    'q': search,
  }
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.4; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36'
  }

  session = requests.Session()
  done = False
  retries = 3
  while not done and retries > 0:
    qs = urllib.parse.urlencode(params)
    url = f'https://twitter.com/i/search/timeline?{qs}'
    response = session.get(url, headers=headers)
    jsonResponse = json.loads(response.text)
    html = jsonResponse['items_html']
    soup = BeautifulSoup(html, "html.parser")
    feed = soup.find_all('div', 'tweet')
    if len(feed) > 0:
      retries = 3
    else:
      retries -= 1

    # print(soup.prettify())
    for tweet in feed:
      print(tweet.find('a', 'tweet-timestamp')['title'] + ':' + tweet.find('p', 'tweet-text').text)

    params['max_position'] = jsonResponse["min_position"]
    


def getProfile(username):
  headers = { 
    'X-Requested-With': 'XMLHttpRequest'
  }

  url = f'https://twitter.com/{username}?lang=en'
  session = requests.Session()
  response = session.get(url, headers=headers)
  if response.status_code != 200:
    logging.error(f'Profile for {username} could not be retrieved.')
    return False

  soup = BeautifulSoup(response.text, 'html.parser')
  data = soup.find('div', class_='user-actions')
  urlEl = soup.find('span', 'ProfileHeaderCard-urlText').find('a') 
  if urlEl:
    url = urlEl['title']
  else:
    url = ''
  return { 
    'id': data['data-user-id'],
    'username': data['data-screen-name'],
    'name': data['data-name'],
    'protected': data['data-protected'],
    'bio': soup.find('p', class_='ProfileHeaderCard-bio').text,
    'location': soup.find('span', class_='ProfileHeaderCard-locationText').text.strip(),
    'joined': time.strftime(
      '%Y-%m-%dT%H:%M:%SZ', 
      time.strptime(soup.find('span', class_='ProfileHeaderCard-joinDateText')['title'], '%I:%M %p - %d %b %Y')
    ),
    'following': (int)(soup
      .find('li', class_='ProfileNav-item ProfileNav-item--following')
      .find('span', 'ProfileNav-value')['data-count']),
    'followers': (int)(soup
      .find('li', class_='ProfileNav-item ProfileNav-item--followers')
      .find('span', 'ProfileNav-value')['data-count']),
    'favorites': (int)(soup
      .find('li', class_='ProfileNav-item ProfileNav-item--favorites')
      .find('span', 'ProfileNav-value')['data-count']),
    'tweets': (int)(soup
      .find('li', class_='ProfileNav-item--tweets')
      .find('span', 'ProfileNav-value')['data-count']),
    'avatar': soup.find('a', class_='ProfileAvatar-container')['href'],
    'background-image': soup.find('div', class_='ProfileCanopy-headerBg').find('img')['src'],
    'media_count': convertToInt(soup.find('a', 'PhotoRail-headingWithCount js-nav').text.strip().split(" ")[0]),
    'is_verified': len(soup.find_all('span', 'ProfileHeaderCard-badges')),
    'url': url
  }
 
def getFollowXXXGenerator(url, username):
  done = False
  session = requests.Session()
  fullUrl = url

  while not done:
    response = session.get(fullUrl)
    if response.status_code != 200:
      logging.error(f'List for {username} could not be retrieved.')
      return False
    soup = BeautifulSoup(response.text, 'html.parser')
    followers = soup.find_all('td', class_='screenname')
    for userblock in followers:
      yield {
        'username': userblock.find('a', {'name' : True})['name'],
        'name': userblock.find('strong', class_='fullname').text
      }
              
    cursorCode = soup.find_all("div", "w-button-more")
    if len(cursorCode) < 1:
      break

    match = re.findall(f'cursor=(.*?)">', str(cursorCode))
    if len(match) < 1:
      break

    cursor = (int)(match[0])
    if (cursor > 0):
      fullUrl = f'{url}?cursor={cursor}'

def getFollowersGenerator(username):
  return getFollowXXXGenerator(f'https://mobile.twitter.com/{username}/followers', username)

def getFollowingGenerator(username):
  return getFollowXXXGenerator(f'https://mobile.twitter.com/{username}/following', username)

def getFollowers(username):
  for value in getFollowersGenerator(username):
    print(value)

def getFollowing(username):
  for value in getFollowingGenerator(username):
    print(value)


