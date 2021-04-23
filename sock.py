import socket
from PIL import  ImageGrab, ImageOps, Image
from hashlib import sha256
import io


#socket zerbitzaria

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv.bind(('192.168.0.16', 8080))
print("Python server starting")
serv.listen(5)
while True:
    conn, addr = serv.accept()
    from_client = ''
    while True:
        data = conn.recv(4096)
        print("data received")
        if not data: break
        from_client += str(data)
        print(from_client)
        stream = io.BytesIO(data)
        image = Image.open(stream)
        gray_image = ImageOps.grayscale(image)
        #gray_image.show()


        #oso geldoa
        imagestring = ""
        for x in range(0,256):
            for y in range(0,224):
                pixel = gray_image.getpixel((x,y))
                imagestring = imagestring + str(pixel) + '.'


        response = sha256(imagestring.encode('utf-8')).hexdigest()
        print("sending response "+ response)
        conn.send(str.encode(response))

    conn.close()
    print('client disconnected')
