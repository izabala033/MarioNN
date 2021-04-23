from PIL import ImageGrab, ImageOps, Image

#CMD bidez irudia atzitzeko, print bat egin Luak ikus dezan

im = ImageGrab.grabclipboard()
gray_image = ImageOps.grayscale(im)
print(gray_image.tobytes())
#gray_image.show()
