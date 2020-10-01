#!/usr/bin/python3
import praw
from auth import *
import time
import re
import os
def try_replying(comment, reply):
	sleeptime = 1
	while True:
		try:
			comment.reply(reply);
			break;
		except:
			debug(failreplystring.format(sleeptime))
			time.sleep(sleeptime)
			sleeptime <<= 1
			if (sleeptime > (1 << 10)):
				break
	return

def count_s(text):
	return 0 if re.search("(^| |\n)/(s|S)($| |\n)", text) == None else 1
def debug(text):
    with open("./log.txt", "a") as f:
        f.write(text + "\n");
        
reddit = praw.Reddit (
	client_id = id,
	client_secret = secret,
	user_agent = user_agent,
	username = username,
	password = password
)
replystring = "u/{} has said '/s' {} times.\nTag me in a reply to anyone or mention me as \"u/scountbot u/{{targetperson}}\" anywhere if you want me to count how many times they've said '/s' !"
failreplystring = "Replying failed. Retrying in {} seconds"
while True:
	try:
		for comment in reddit.inbox.unread(limit = None):
			if type(comment) is praw.models.SubredditMessage:
				reddit.inbox.mark_read([comment])
				continue
			if (("u/" + reddit.user.me().name) not in comment.body.lower()):
				reddit.inbox.mark_read([comment])
				continue
			words = list(filter(lambda s: s != "", comment.body.lower().replace("\n", " ").split(" ")))
			if len(words) >= 2 and (words[0] == ("u/" + reddit.user.me().name) or words[0] == ("/u/" + reddit.user.me().name)):
				try:
					if words[1][:2] == "u/":
						target_user = reddit.redditor(words[1][2:])
					elif words[1][:3] == "/u/":
						target_user = reddit.redditor(words[1][3:])
					else:
						target_user = comment.parent().author
				except:
					debug("Getting user u/{} failed.".format(words[1][2:]))
					reddit.inbox.mark_read([comment])
					continue
			else:
				target_user = comment.parent().author
			if target_user.name == reddit.user.me().name:
				debug("real creative buddy")
				try_replying(comment, "Real creative buddy.")
				reddit.inbox.mark_read([comment])
			else:
				debug("Counting for {}.".format(target_user.name))
				scnt = 0
				try:
					for usercomment in target_user.comments.new(limit = None):
						scnt += count_s(usercomment.body)	
					debug("{} - {}".format(target_user, scnt))
					try_replying(comment, replystring.format(target_user.name, scnt))
					reddit.inbox.mark_read([comment])
				except:
					debug("failed - \"{}\"".format(comment.body))
					reddit.inbox.mark_read([comment])
					continue
		time.sleep(9)
	except Exception as e:
		debug(str(e))
		time.sleep(30)
		continue
	
