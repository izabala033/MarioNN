import random
import numpy as np
from collections import deque
import torch

class PrioBuffer:

    

    """
input:
state_size: egoeraren tamaina
buffer_size: memoriaren tamaina
batch_size: batch baten tamaina
priority: lehentasun bidezko memoria erabili ala ez

output: none

memoria hasieratu, datu guztiak GPU-an alokatuko dira une osoan
    """
    def __init__(self, state_size, buffer_size, batch_size, priority=True):

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.states = torch.zeros((buffer_size,)+state_size).to(self.device)
        self.next_states = torch.zeros((buffer_size,)+state_size).to(self.device)
        self.actions = torch.zeros(buffer_size,1, dtype=torch.long).to(self.device)
        self.rewards = torch.zeros(buffer_size, 1, dtype=torch.float).to(self.device)
        self.dones = torch.zeros(buffer_size, 1, dtype=torch.float).to(self.device)
        self.e = np.ones((buffer_size, 1), dtype=np.float)
        
        self.priority = priority
        self.ptr = 0
        self.n = 0
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.first_time = True
    
    """
    input: S A R S+1 D transizioa
    output: none

    transizioa memorian gordetzen du
    memoria maximora iristen bada elementu zaharrenak ordezkatuko dira
    """
    def push(self, state, action, reward, next_state, done):
        self.states[self.ptr] = torch.from_numpy(state).to(self.device)
        self.next_states[self.ptr] = torch.from_numpy(next_state).to(self.device)
        self.actions[self.ptr] = action
        self.rewards[self.ptr] = reward
        self.dones[self.ptr] = done
        self.e[self.ptr] = self.e.max()
        
        self.ptr += 1
        if self.ptr >= self.buffer_size:
            
            self.ptr = 0 
            self.n = self.buffer_size


    """
input: none
output: transizioen array bat eta  hauen indizeak

ausazko transizioak itzultzen ditu, lehentasuna erabiltzen bada errore handien sortzen duten transizioek probabilitate handiagoa izango dute
    """
    def sample(self):

        n = len(self)

        if self.priority:
            idx = np.random.choice(n, self.batch_size, replace=False, p=(self.e[:n]/self.e[:n].sum()).squeeze(1))
        else:
            idx = np.random.choice(n, self.batch_size, replace=False)
        
        states = self.states[idx]
        next_states = self.next_states[idx]
        actions = self.actions[idx]
        rewards = self.rewards[idx]
        dones = self.dones[idx]
        
        return (states, actions, rewards, next_states, dones), idx
      
        """
input:
idx: transizioen indizeak
e: transizio bakoitzak sortu duen errorea

output: none

entrenatu eta gero erabili diren transizioen lehentasuna/errorea eguneratzen da
    """
    def update_priority(self, idx, e):
        e = abs(e)
        self.e[idx] = e
        

    """
input: none
output: memorian gordetako elementu kopurua
    """
    def __len__(self):
        if self.n == 0:
            return self.ptr
        else:
            return self.n