import sys, os
import httplib
import urllib, urllib2
import urlparse
import re
import time
import random
from BeautifulSoup import BeautifulSoup
import cProfile
import threading
import Queue
import datetime
from realtimelinks.twitlinks.models import Link, Hit
import django

class CycleException(Exception):
    pass

def detectcycle(f):
    def new(*args):
        if len(args) > 1 and len(args[1]) > 2:
            r = args[1]
            if r[0] in r[1:]:
                raise CycleException
        return f(*args)
    return new

@detectcycle
def resolv(url, urls = []):
    try:
        s = urlparse.urlsplit(url)
        h = httplib.HTTPConnection(s[1])
        h.request("HEAD", s[2])
        r = h.getresponse()
        urls.insert(0,url)
        if r.status == 301:
            red = r.getheader('location')
            urls = resolv(red,urls)
        return urls
    except (CycleException):
        raise CycleException
    except:
        pass

class Resolver(threading.Thread):

    def __init__(self, workQ, counter, i):
        self.workQ = workQ
        self.i = i
        self.counter = counter
        self.working = 0
        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
                url = self.workQ.get()
                self.working = 1
                self.process(url)
            finally:
                self.working = 0
                self.workQ.task_done()

    def process(self, url):
        try:
            r = resolv(url,[])
            if r and url and r[0] != url:
                title, description, keywords = getUrlInfo(r[0])
                save(url, r[0], title, description, keywords)
                self.counter += 1
        except Exception as err:
            print err

def save(url, longUrl, title, description, keywords):
    existing = Link.objects.filter(long_url = longUrl)
    if existing:
        existing[0].markSeen()
        print 'updating', existing[0]
    else:
        l = Link(short_url = url,
                 long_url = longUrl,
                 first_seen = datetime.datetime.now(),
                 title = title,
                 description = description,
                 keywords = keywords)
        l.save()
        h = Hit()
        h.link = l
        h.at = datetime.datetime.now()
        h.save()
        print 'saving', l
    django.db.connection.close()
    
def getUrlInfo(url):
    html = urllib.urlopen(url).read()
    try:
        b = BeautifulSoup(html)
    except Exception as e:
        return None,None,None
    try:
        title = b.head.findAll('title')[0].contents[0].string
    except Exception:
        title = None
    try:
        description = dict(b.head.findAll('meta',attrs={'name' : 'description'})[0].attrs).get('content', None)
    except Exception:
        description = None
    try:
        keywords = dict(b.head.findAll('meta',attrs={'name' : 'keywords'})[0].attrs).get('content', None)
    except Exception:
        keywords = None
    return title, description, keywords

class Fetcher(threading.Thread):
    
    def __init__(self, workQ, seen):
        self.error = 0
        self.workQ = workQ
        self.seen = seen
        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
#                html = urllib.urlopen('http://twitter.com/statuses/public_timeline.rss', proxies={ 'http' : 'http://'+proxies[random.randint(0,len(proxies)-1)] }).read()
                html = urllib.urlopen('http://twitter.com/statuses/public_timeline.rss', proxies={ 'http' : 'http://127.0.0.1:8118' }).read()
                s = BeautifulSoup(html)
                texts = s.findAll('item')
                tweets = [(t.description.string, t.guid.string) for t in texts]
                for t in tweets:
                    u = re.compile('http://\S+\s*')
                    m = u.findall(t[0])
                    v = re.compile('^http://twitter.com/[^/]+/statuses/(\d+)$')
                    tid = v.findall(t[1])[0]
                    if m != []:
                        url = m[0]
                        if tid not in self.seen:
                            self.seen[tid] = int(time.time())
                            self.workQ.put(url)
                self.error = 0
                time.sleep(5)
            except Exception as err:
                self.error = 1
                print err

counter = 0
def main():
    print 'initializing Q'
    q = Queue.Queue(1000)

    fetchers = []
    seen = {}
    for i in range(50):
        fetcher = Fetcher(q, seen)
        fetcher.start()
        fetchers.append(fetcher)
    print 'started fetchers'

    workers = []
    for i in range(300):
        worker = Resolver(q, counter, i)
        #worker.daemon = True
        worker.start()
        workers.append(worker)
    print 'workers started'
    q.join()
    while True:
        print datetime.datetime.now()
        print 'Q: ', q.qsize(), 'Retrieved: ', sum([x.counter for x in workers]), 'Blocked: ', len(seen)
        err = sum([f.error for f in fetchers])
        w = sum([f.working for f in workers])
        print err, 'erroneous', len(fetchers)-err, 'ok // ', w, 'working', len(workers)-w, 'idle\n'
        time.sleep(15)
        x = int(time.time())
        for (s,last) in seen.copy().iteritems():
            if x - last > 30:
                seen.pop(s)        

if __name__ == '__main__':
    main()

