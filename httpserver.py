from http.server import HTTPServer, BaseHTTPRequestHandler

#from io import BytesIO

import socket
from PIL import  ImageGrab, ImageOps, Image, ImageMath
from hashlib import sha256
import io


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self): #zerbitzaria piztuta eta atzigarri dagoela ikusteko nabigatzaile bidez
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

    # input: none
    # output: none
    # irudia clipboard-etik atzitu eta erantzuna itzuli
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)


        im = ImageGrab.grabclipboard()
        gray_image = ImageOps.grayscale(im) 
        out = str(list(gray_image.getdata()))
        out = sha256(out.encode('utf-8')).hexdigest()
        out = str.encode(out)
        #print(out)


        self.send_response(200)
        self.end_headers()
        response = io.BytesIO()
        response.write(out)
        self.wfile.write(response.getvalue())


#HTTP zerbitzaria hasieratu
httpd = HTTPServer(('192.168.0.13', 8081), SimpleHTTPRequestHandler)
print("Server starting.\n")
httpd.serve_forever()