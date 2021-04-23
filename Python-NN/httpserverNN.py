from http.server import HTTPServer, BaseHTTPRequestHandler

#from io import BytesIO

#import socket
from PIL import ImageGrab, ImageOps, Image#, ImageMath, ImageChops
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
        

    """
input: irudi bat
output: none

irudia gris eskalara pasako da eta tamaina jeitsiko da
4 irudi edukitzean egoera bat sortzeko nahikoa dago, beraz lau (4,84,84)ko irudien stack bat sortu
    """
    def transformImage(self,im):
        gray_image = ImageOps.grayscale(im)

        gray_image = gray_image.crop((80, 31, 255, 223))
        #gray_image.show()
        #exit()
        gray_image = gray_image.resize((observation_space[1],observation_space[2]))
        
        
        if not SimpleHTTPRequestHandler.last_state is None: #Markov propietatea hobetzeko egiten den aldaketa
            if SimpleHTTPRequestHandler.last_action % 2 == 0: #salto egin badu beltzez margotu
                gray_image.putpixel((83,0),(0))
                gray_image.putpixel((83,1),(0))
                gray_image.putpixel((82,0),(0))
                gray_image.putpixel((82,1),(0))

            else:                                             #salto egin ez badu zuriz margotu
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
            if(len(SimpleHTTPRequestHandler.state) == observation_space[0]):
                SimpleHTTPRequestHandler.state = np.stack(SimpleHTTPRequestHandler.state, axis=0)


    """
input: json string bat
output: json string zuzendua

karaktere berezien zuzenketak egiten dira, ondoren python json liburutegiak arazorik izan ez dezan
    """
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


#nabigatzailetik zerbitzaria atzigarri dagoen ikusteko
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')


    """
input: none
output: ausazko ekintza baldin eta memoriaren tamaina batch tamaina baina txikiagoa den, bestela sareak kalkulatu duen ekintza hoberena (epsilon-greedy kontuan hartuz)

egin behar den ekintza kalkulatzen du
transizioa memorian gordetzen da ere
sarearen eguneraketa egiten du, backpropagation bidez (agent.update())
amaierako egoera bada aurreko egoera eta azken ekintza garbitzen ditu, hurrengo egoera hasierako egoera izango delako
    """
    def NN(self):
        if len(agent.replay_buffer) <= agent.batch_size:
            action = random.randint(0,3)
        else:
            action = agent.get_action(SimpleHTTPRequestHandler.state)

        if not SimpleHTTPRequestHandler.last_state is None:
            agent.replay_buffer.push(SimpleHTTPRequestHandler.last_state, SimpleHTTPRequestHandler.last_action, SimpleHTTPRequestHandler.reward, SimpleHTTPRequestHandler.state, self.terminal)
        if len(agent.replay_buffer) > agent.batch_size:
            agent.update()

        SimpleHTTPRequestHandler.last_action = action
        SimpleHTTPRequestHandler.last_state = SimpleHTTPRequestHandler.state
        if self.terminal == 1:
            SimpleHTTPRequestHandler.last_state = None
            SimpleHTTPRequestHandler.last_action = None
        
        return action

    """
input: none
output: none

aukeratu den ekintza itzultzen du (self.action)
    """
    def sendresponse(self):
        self.send_response(200)
        self.end_headers()
        response = io.BytesIO()
        out = str.encode(str(self.action))

        response.write(out)
        self.wfile.write(response.getvalue())


    """
input: none
output: none

Lua-k eskaera egitean hemendik hasiko da exekuzioa
    """
    def do_POST(self):

        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        #batzuetan ezin da irudia atzitu, kasu horretan edozein ekintza itzuli
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


        #json fitxategia prozesatu
        self.process = jsons["process"]
        if(self.process == "1"): #process = 1 bada laugarren irudia daukagu, egoera bat sortzeko beharrezkoa dena
            SimpleHTTPRequestHandler.reward = int(jsons["score"])
            if SimpleHTTPRequestHandler.reward == 0: #penalizazio txiki bat ez bada mugitzen
                SimpleHTTPRequestHandler.reward = -1
            self.terminal = jsons["terminal"]
            if(self.terminal == "1"):
                self.terminal = 1
                SimpleHTTPRequestHandler.reward = -10 #penalizazio bat hiltzerakoan
            else:
                self.terminal = 0
            self.cleared = jsons["cleared"]
            if(self.cleared == "1"):
                self.cleared = True
                SimpleHTTPRequestHandler.reward = 10
                torch.save(agent.model, "model-cleared.pt") #maila pasatzen duenean, sarearen parametroak gorde
            else:
                self.cleared = False


            agent.episode_reward+=SimpleHTTPRequestHandler.reward


            if self.terminal == 1:
                agent.episode_rewards.append(agent.episode_reward)
                agent.episode_reward = 0
                agent.losses.append(sum(agent.episode_loss) / len(agent.episode_loss))
                agent.episode_loss = []

            if(len(SimpleHTTPRequestHandler.state) == observation_space[0]): #lau irudi lortu badira (egoera bat sortzeko nahikoa dena)
                self.action = self.NN()
            SimpleHTTPRequestHandler.state = None
        
        self.sendresponse()

    


#hasieraketak egin
httpd = HTTPServer(('192.168.0.18', 8081), SimpleHTTPRequestHandler)

action_space = spaces.Discrete(4)
observation_space = (4,84,84)
batch_size = 32
agent = DQNAgent(observation_space,action_space, batch_size, train = True)


print("Server starting.\n")
try:
    httpd.serve_forever()
except KeyboardInterrupt: #programa geratzen denean batazbesteko errorea eta batazbesteko sariaren grafikak sortu, baita ere sareak une horretan dituen aldagaien pisua gorde
    if len(agent.losses)>1:
        print("Batazbesteko errorea: ", sum(agent.losses)/len(agent.losses))
        print("Batazbesteko saria: ",sum(agent.episode_rewards)/len(agent.episode_rewards))
        idl = np.arange(len(agent.losses))
        idr = np.arange(len(agent.episode_rewards))
        plt.bar(idl, agent.losses)
        plt.show() 
        plt.bar(idr, agent.episode_rewards)
        plt.show()
        torch.save(agent.model, "model-final.pt")
    print("Agur!")
