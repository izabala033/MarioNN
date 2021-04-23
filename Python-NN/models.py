import torch
import torch.nn as nn
import torch.autograd as autograd
import torch.nn.functional as F
import numpy as np

from matplotlib import pyplot as plt

class ConvDQN(nn.Module):

    """
input:
	num_inputs: egoeraren tamaina (4,84,84)
	num_actions: ekintza kopurua 4
output: none

hasieraketa funtzioa
    """
    def __init__(self,num_inputs, num_actions):
        super(ConvDQN, self).__init__()

        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels = num_inputs[0] , out_channels=32, kernel_size=8, stride=4),
            nn.ReLU(),
        )

        self.conv2 = nn.Sequential(      
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU()
        )

        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU()
        )

        self.fc = nn.Sequential(
            nn.Linear(3136, 512),
            nn.ReLU(),
            nn.Linear(512, num_actions)
        )
        
        self.val = nn.Sequential(
            nn.Linear(3136, 512),
            nn.ReLU(),
            nn.Linear(512,1)
        )


    """
input: egoera bat
output: egoera horretan ekintza bakoitzarekin lortuko den sari maximoaren hurbilpena

egoera bat erabiliz sarean aurreraka egiten da
    """
    def forward(self, x):


        x = self.conv1(x)
        #x1 = x
        x = self.conv2(x)#+x1 #skip connection
        x = self.conv3(x)

        x = x.view(x.size(0),-1)
        #print(x.shape)

        adv = self.fc(x)
        #val = self.val(x) #dueling dqn



        #print(x.shape)


        return adv# + val - adv.mean(1, keepdim = True) #dueling dqn
        