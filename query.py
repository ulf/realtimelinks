from whoosh import index
from whoosh.qparser import QueryParser
import sys
from pprint import pprint

idx = index.open_dir("index")
s = idx.searcher()
p = QueryParser("title", schema = idx.schema)
print 'Holding ', idx.doc_count(),'documents.'

while True:
    print 'Query: '
    i = sys.stdin.readline()
    if i == None or i == '\n':
        break
    q = p.parse(unicode(i))
    res = s.search(q)
    for r in res:
        pprint(r)
