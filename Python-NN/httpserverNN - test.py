from http.server import HTTPServer, BaseHTTPRequestHandler

#from io import BytesIO

#import socket
from PIL import ImageGrab, ImageOps#, Image, ImageMath, ImageChops
#from hashlib import sha256
import io
import json
#import tensorflow.compat.v1 as tf
import numpy as np
import random

from dqn import DQNAgent
from gym import spaces #discrete.sample erabiltzeko
from matplotlib import pyplot as plt
import torch





class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    
    state = None
    last_state = None
    reward = None
    process = None
    terminal = False
    cleared = False
    last_action = None
    action = -1
        

    def transformImage(self,im):
        gray_image = ImageOps.grayscale(im)
        gray_image = gray_image.resize((observation_space[1],observation_space[2]))

        
        if not SimpleHTTPRequestHandler.last_state is None:
            if SimpleHTTPRequestHandler.last_action % 2 == 0: #salto egiten badu
                gray_image.putpixel((83,0),(0))
                gray_image.putpixel((83,1),(0))
                gray_image.putpixel((82,0),(0))
                gray_image.putpixel((82,1),(0))

            else:
                gray_image.putpixel((83,0),(255))
                gray_image.putpixel((83,1),(255))
                gray_image.putpixel((82,0),(255))
                gray_image.putpixel((82,1),(255))
        



        npstate = np.array(gray_image)

        #gray_image.show()

        if(SimpleHTTPRequestHandler.state is None):
            SimpleHTTPRequestHandler.state = (npstate,)
        else:

            SimpleHTTPRequestHandler.state = SimpleHTTPRequestHandler.state + (npstate,)

            #print(len(SimpleHTTPRequestHandler.state))
            if(len(SimpleHTTPRequestHandler.state) == observation_space[0]):
                SimpleHTTPRequestHandler.state = np.stack(SimpleHTTPRequestHandler.state, axis=0) #/ 255





        #out = str(list(gray_image.getdata()))
        #out = sha256(out.encode('utf-8')).hexdigest()
        #out = str.encode(out)
        #return out

    def purifyJSON(self, bodys):
        bodys = bodys.replace("b'payload=","")
        bodys = bodys.replace("'","")
        bodys = bodys.replace("%7B","{")
        bodys = bodys.replace("%27","\"")
        bodys = bodys.replace("%3A",":")
        bodys = bodys.replace("%7D","}")
        bodys = bodys.replace("%2C",",")
        bodys = bodys.replace("+","")
        return bodys


    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

    def NN(self):
        
        action = agent.get_action(SimpleHTTPRequestHandler.state)

        SimpleHTTPRequestHandler.last_action = action
        SimpleHTTPRequestHandler.last_state = SimpleHTTPRequestHandler.state
        if self.terminal == 1:
            SimpleHTTPRequestHandler.last_state = None
            SimpleHTTPRequestHandler.last_action = None
        
        return action

    def sendresponse(self):
        self.send_response(200)
        self.end_headers()
        response = io.BytesIO()
        out = str.encode(str(self.action))

        response.write(out)
        self.wfile.write(response.getvalue())


    def do_POST(self):

        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)



        try:
            im = ImageGrab.grabclipboard()
        except OSError:
            self.action = action_space.sample()
            self.sendresponse()
            return

     


        self.transformImage(im)

        bodys = self.purifyJSON(str(body))
        #json example: {"process":"1","score":"51","terminal":"0","cleared":"0"}
        jsons = json.loads(bodys)

        self.process = jsons["process"]
        if(self.process == "1"):
            SimpleHTTPRequestHandler.reward = int(jsons["score"])
            if SimpleHTTPRequestHandler.reward == 0: #penalizazio txiki bat
                SimpleHTTPRequestHandler.reward = -0.1
            self.terminal = jsons["terminal"]
            if(self.terminal == "1"):
                self.terminal = 1
                #SimpleHTTPRequestHandler.reward = -10
            else:
                self.terminal = 0
            self.cleared = jsons["cleared"]
            if(self.cleared == "1"):
                self.cleared = True
                torch.save(agent.model, "model-cleared.pt")
                #exit()
            else:
                self.cleared = False
            #SimpleHTTPRequestHandler.image.show()

            agent.episode_reward+=SimpleHTTPRequestHandler.reward


            if self.terminal == 1:
                agent.episode_rewards.append(agent.episode_reward)
                agent.episode_reward = 0
            if(len(SimpleHTTPRequestHandler.state) == observation_space[0]):

                self.action = self.NN()
            SimpleHTTPRequestHandler.state = None
            
            #print(len(SimpleHTTPRequestHandler.state))

        
            




        #print(out)
        
        #print(agent)
        self.sendresponse()

    


httpd = HTTPServer(('192.168.0.13', 8081), SimpleHTTPRequestHandler)

action_space = spaces.Discrete(4)
observation_space = (4,84,84)


#optimizer = Adam(learning_rate=0.01)


#agent = Agent(action_space,observation_space, optimizer)

batch_size = 32
agent = DQNAgent(observation_space,action_space, batch_size, train = False, file = "final_norm.pt")


print("Server starting.\n")
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    if len(agent.losses)>500:
        #print(agent.losses)
        plt.plot(agent.losses)
        plt.show() 
        plt.plot(agent.episode_rewards)
        plt.show()
        torch.save(agent.model, "model-final.pt")
    print("Agur!")
