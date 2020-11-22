#!/usr/bin/python3
import praw
import time
import re
import os
import json
import sys
import traceback

def log(*args, **kwargs):
	print(*args, **kwargs, file = sys.stderr)
	sys.stderr.flush()

if len(sys.argv) != 2:
	log(f"Usage: {sys.argv[0]} <auth-file>")
	exit(1)
try:
	auth = json.load(open(sys.argv[1]))
	reddit = praw.Reddit(
		client_id = auth["id"],
		client_secret = auth["secret"],
		user_agent = auth["user_agent"],
		username = auth["username"],
		password = auth["password"]
	)
except:
	log("Invalid auth file")
	exit(1)

log("bot starting")

replystring = "u/{} has said '/s' {} times.\nTag me in a reply to anyone or mention me as \"u/scountbot u/{{targetperson}}\" anywhere if you want me to count how many times they've said '/s' !"
failreplystring = "Replying failed. Retrying in {} seconds"

def try_replying(comment, reply):
	sleeptime = 1
	while True:
		try:
			comment.reply(reply);
			break;
		except:
			log(traceback.format_exc())
			log(failreplystring.format(sleeptime))
			time.sleep(sleeptime)
			sleeptime <<= 1
			if (sleeptime > (1 << 10)):
				log("exceeded sleep time, stopping trying to reply")
				break
	return

def count_s(text):
	return 0 if re.search("(^| |\n)/(s|S)($| |\n)", text) == None else 1

found = True
while True:
	try:
		for comment in reddit.inbox.unread(limit = None):
			found = True
			if type(comment) is praw.models.SubredditMessage:
				reddit.inbox.mark_read([comment])
				continue
			if (("u/" + reddit.user.me().name) not in comment.body.lower()):
				reddit.inbox.mark_read([comment])
				continue
			words = list(filter(lambda s: s != "", comment.body.lower().replace("\n", " ").split(" ")))
			target_user = None
			if len(words) >= 2 and (words[0] == ("u/" + reddit.user.me().name) or words[0] == ("/u/" + reddit.user.me().name)):
				try:
					if words[1][:2] == "u/":
						target_user = reddit.redditor(words[1][2:])
					elif words[1][:3] == "/u/":
						target_user = reddit.redditor(words[1][3:])
					else:
						target_user = comment.parent().author
				except:
					log(traceback.format_exc())
					log("Getting user u/{} failed.".format(words[1][2:]))
					reddit.inbox.mark_read([comment])
					continue
			if target_user == None:
				target_user = comment.parent().author
			if target_user != None:
				if  target_user.name == reddit.user.me().name:
					try_replying(comment, "Real creative buddy.")
					reddit.inbox.mark_read([comment])
				else:
					log("Counting for {}.".format(target_user.name))
					scnt = 0
					try:
						for usercomment in target_user.comments.new(limit = None):
							scnt += count_s(usercomment.body)	
						log("{} - {}".format(target_user, scnt))
						try_replying(comment, replystring.format(target_user.name, scnt))
						reddit.inbox.mark_read([comment])
					except:
						log(traceback.format_exc())
						log("failed - \"{}\"".format(comment.body))
						reddit.inbox.mark_read([comment])
						continue
			else:
				log("target_user is None (? replying to deleted user)")
				reddit.inbox.mark_read([comment])
		if found:
			log("Waiting for the next comment...")
		found = False
		time.sleep(60)
	except Exception as e:
		log(traceback.format_exc())
		log("unknown error")
		time.sleep(30)
		continue
	
