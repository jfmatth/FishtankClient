import httplib, mimetypes


def encrypt_upload():
    pass




def httppost_multipart(host=None, url=None, fields=None, files=None):
    """
	A function to post a file / fields to a HTTP server.
	
	see http://code.activestate.com/recipes/146306-http-client-to-post-using-multipartform-data/
	
	sample:	
	post_multipart2(host="172.16.223.128:8000", 
					url="/manager/uploadtest/", 
					fields=[("myfield","this is my value")], 
					files=[("xfile","file.txt",open("file.txt","rb").read() )] 
					)
   
    """
    if (host==None or url==None):
        raise Exception("must provide at least host and url parameters")
    
    content_type, body = encode_multipart_formdata(fields, files)
    h = httplib.HTTPConnection(host)
    headers = {
        'User-Agent': 'Python-httplib/2.6',
        'Content-Type': content_type
        }
    h.request('POST', url, body, headers)
    res = h.getresponse()

    return res.status, res.reason, res.read()


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'