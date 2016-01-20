"""Support for uploading RDF data directly to a Sesame instance"""

import urllib, urllib2
import os
import json
from rdflib import URIRef
from convert.namespaces import bind_graph

import configmanager
configmanager.configinit()

RDF_GRAPH_FORMAT = configmanager.get_config("RDF_GRAPH_FORMAT", "nt")

import tempfile

class RequestWithMethod(urllib2.Request):
  def __init__(self, *args, **kwargs):
    self._method = kwargs.get('method')
    if self._method:
        del kwargs['method']
    urllib2.Request.__init__(self, *args, **kwargs)

  def get_method(self):
    return self._method if self._method else super(RequestWithMethod, self).get_method()


class SesameServer():
    """A utility class to support HTTP interaction with a sesame triple store"""

    def __init__(self, url):

        self.url = url

    def _get(self, url):
        """Send a get request to the given URL (which can also be a Request object)
        and return a tuple of the response code and the response body ('200', 'whatever')"""


        try:
            h = urllib2.urlopen(url)
            result = h.read()
            return (h.code, result)
        except urllib2.HTTPError, e:

            result = e.read()
            print "Error", e, result
            return (e.code, result)


    def size(self):
        """Query the repository size, return size
        in triples"""

        path = "/size"

        result = self._get(self.url + path)

        return result[1]


    def upload(self, filename):
        """Upload RDF data from filename"""

        return self.upload_many([filename])
        
        
    def upload_many(self, filenames):
        """Upload RDF data from multiple files in a single request"""
        
        if len(filenames) > 1:
            print "Uploading", len(filenames), "files"

        path = "/statements"
        
        data = ''
        for filename in filenames:
            h = open(filename)
            data += '\n'+ h.read() # add a newline in case there isn't one at the end of file
            h.close()
        
        # need to replace true|false with quoted version
        # because the turtle that Sesame understands is not quite
        # the same as the turtle that rdflib generates
        data = data.replace(" true;", ' "true";')
        data = data.replace(" false;", ' "false";')

        if RDF_GRAPH_FORMAT == 'turtle':
            headers = {'Content-Type': 'application/x-turtle'}
        elif RDF_GRAPH_FORMAT == 'nt':
            headers = {'Content-Type': 'text/plain'}
        else:
            print "Unknown graph format in configuration: ", RDF_GRAPH_FORMAT
            exit()
            
        req = urllib2.Request(self.url+path, data=data, headers=headers)

        result = self._get(req)
        # check that return code is 204
        if result[0] == 204:
            return result[1]
        else:
            raise Exception("Problem with upload of data, result code %s" % result[0])

        

    def upload_dir(self, dirname):
        """upload all RDF files found inside dirname and
        subdirectories (recursively)"""

        BATCH_UPLOAD_RDF = configmanager.get_config('BATCH_UPLOAD_RDF', 'no') == 'yes'
        BATCH_UPLOAD_SIZE = int(configmanager.get_config('BATCH_UPLOAD_SIZE', 100))

        retry = []
        rdffiles = []
        for dirpath, dirnames, filenames in os.walk(dirname):
            print "Directory: ", dirpath
            for fn in filenames:
                if fn.endswith(RDF_GRAPH_FORMAT):
                    if BATCH_UPLOAD_RDF:
                        rdffiles.append(os.path.join(dirpath, fn))
                        if len(rdffiles) > BATCH_UPLOAD_SIZE:
                            try:
                                self.upload_many(rdffiles)
                                rdffiles = []
                            except Exception as e:
                                print "problem uploading", len(rdffiles), "files from ", dirname
                                print e
                                retry.extend(rdffiles)
                                rdffiles = []
                    else:
                        try:
                            self.upload(os.path.join(dirpath, fn))
                        except:
                            print "problem uploading", fn
                            retry.append(os.path.join(dirpath, fn))
                            
        # upload any remaining batch of files
        if BATCH_UPLOAD_RDF and len(rdffiles) > 0:
            try:
                self.upload_many(rdffiles)
                rdffiles = []
            except:
                print "problem uploading", len(rdffiles), "files from ", dirname
                retry.extend(rdffiles)

        if len(retry) > 0:
            print "Retrying ", len(retry), "uploads"
            while len(retry) > 0:
                fn = retry.pop()
                print "Upload", fn
                try:
                    self.upload(fn)
                except Exception as e:
                    print "problem with retry of ", fn
                    print e
                    #retry.append(fn)

    def output_graph(self, graph, name=None):
        """Output the contents of the graph to a file"""

        # add namespaces to the graph before output
        graph = bind_graph(graph)

        data = graph.serialize(format=RDF_GRAPH_FORMAT)

        # check to see if we should store the graphs somewhere
        graphdir = configmanager.get_config('OUTPUT_DIR', '')
        
        if not os.path.exists(graphdir):
            os.makedirs(graphdir)
        if name!=None:
            # write out to the filename given with a suffix
            filename = os.path.join(graphdir, name + "." + RDF_GRAPH_FORMAT)
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            h = open(filename, 'w')
        else:
            # make a temp file name
            (fd, filename) = tempfile.mkstemp(prefix='graph-', suffix='.'+RDF_GRAPH_FORMAT, dir=graphdir)
            h = os.fdopen(fd)

        h.write(data)
        h.close()
        return filename
        


    def clear(self, context=None):
        """Remove all triples in the store"""


        if context != None:
            args = {'context': "<%s>" % context}
            path = "/statements?%s" % urllib.urlencode(args)
        else:
            path = "/statements"

        req = RequestWithMethod(self.url+path, method="DELETE")

        result = self._get(req)

        return result


    def query(self, query):
        """Send a query to the server, return results as
        a dictionary converted from the JSON result"""

        # query goes in a GET request with a query string
        # query=<urlencoded sparql>
        # can use Accept header to modify the return type

        query_enc = urllib.urlencode({'query': query})
        headers = {'Accept': 'application/sparql-results+json'}
        req = urllib2.Request(self.url+'?' + query_enc, headers=headers)

        result = self._get(req)
        if result[0] == 200:
            return json.loads(result[1])
        else:
            raise Exception("Error in query")



if __name__=='__main__':

    import sys

    url = "http://sesame.stevecassidy.net/openrdf-sesame/repositories/bigasc"
    filename = sys.argv[1]

    server = SesameServer(url)

   # server.clear()
    server.upload(filename)

    size = server.size()

    print "Size: ", size
