import torch
import torch.nn as nn
import numpy as np

from replay_buffers import PrioBuffer
from models import ConvDQN
from copy import deepcopy

#from torchviz import make_dot

class DQNAgent:

    """
    input: 
        observation_space: egoeraren tamaina (4, 84, 84)
        action_space: ekintza kopurua 4
        batch_size: batch tamaina 32
        train: balio bolearra, sarea entrenatu behar den jakiteko
        file: sarearen balioak entrenatu eta gero duen fitxategiaren izena (string)
        learning_rate: optimizagailuaren balioa eguneraketak egiteko 1e-4
        gamma: Bellman ekuazioaren gamma parametroa 0.99
        buffer_size: esperientzia memoriaren tamaina maximoa, 15000
    output: none

    Dqn hasieraketa funtzioa
    """
    def __init__(self, observation_space,action_space, batch_size, train, file = None, learning_rate=1e-4, gamma=0.99, buffer_size=15000):

        self.observation_space = observation_space
        self.action_space=action_space
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.train = train
        self.batch_size = batch_size
        self.episode_rewards = []
        self.episode_reward = 0
        self.episode_loss = []
        self.losses = []
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.usePER = True #lehentasun bidezko memoria erabili

        if train:
            self.eps = 1
            self.epsmin = 0.05
            self.epsdecay = 0.99
            self.model = ConvDQN(observation_space, action_space.n).to(self.device) #sarea hasieratu
            torch.cuda.empty_cache()
            self.replay_buffer = PrioBuffer(observation_space, buffer_size, batch_size,priority=self.usePER) #memoria hasieratu

        else:
            self.eps = 0.05
            self.epsmin = 0.05
            self.epsdecay = 1
            self.model = torch.load(file).to(self.device)


        self.step_update = 10000
        self.tau = 1
        self.last_update = 0
        self.index = 0
        
        
        self.target_model = deepcopy(self.model) #bigarren sarea sortu (lehenaren kopia dena)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr = learning_rate)

        #self.loss = nn.MSELoss(reduction = 'none') #batazbesteko errore koadratikoa
        self.loss = nn.SmoothL1Loss(reduction = 'none') #Huber loss


    """
    input:
    local_model: lehen sarea, honen parametroak erabiliko dira
    target_model: bigarren sarea, egukaritzen dena
    tau: interpolazio parametroa
    
    output: none

    θ_target = τ*θ_local + (1 - τ)*θ_target eragiketa egiten da
    tau = 1 denean sare osoa kopiatuko da, bestela pixkanaka hurbilduko da
    """

    def soft_update(self, local_model, target_model, tau):
        
        for target_param, local_param in zip(target_model.parameters(),
                                           local_model.parameters()):
            target_param.data.copy_(tau*local_param.data + (1-tau)*target_param.data)

    #input: uneko egoera
    #output: ekintza hoberena (edo ausazkoa, epsilon-greedyren arabera)
    def get_action(self, state):
        state = torch.FloatTensor(state).float().to(self.device)

        self.model.eval()
        with torch.no_grad():
            qvals = self.model(state.unsqueeze(0))
            if not self.train:
                print(qvals)
            action = np.argmax(qvals.cpu().detach().numpy())
        self.model.train()
        
        if(np.random.rand() < self.eps):
            qvals = qvals.cpu().detach().numpy().squeeze(0)
            miniv = qvals.min()
            if miniv < 0:
                qvals = qvals + qvals.min() * -2
            qvals = qvals / qvals.sum()

            return np.random.choice(self.action_space.n, replace = False, p = qvals)

        return action

    #input: none
    #output: memoriatik batch bat atzituko du eta transizio hauek sortzen duten errorea itzuli
    def compute_loss(self):
        transitions, idxs = self.replay_buffer.sample()
        states, actions, rewards, next_states, dones = transitions

        actions = actions.view(actions.size(0), 1)
        dones = dones.view(dones.size(0), 1)
        

        curr_Q = self.model(states)
        curr_Q = curr_Q.gather(1, actions)

        
        with torch.no_grad():
            next_Q = self.target_model(next_states)
            max_next_Q = torch.max(next_Q, 1)[0].unsqueeze(1)
            expected_Q = rewards + self.gamma * max_next_Q * (1-dones)
        
        loss = self.loss(curr_Q, expected_Q)
        
        self.index += 1
        self.last_update += 1

        if(self.eps>self.epsmin):
            self.eps *= self.epsdecay
        
        return loss, idxs

    #input: none
    #output: none

    #backpropagation egiten da errorean eta sarea egukaritzen da
    #10.000 pauso pasa badira, bigarren sarea egukaritzen da
    #transizioen lehentasuna egukaritu egiten da memorian
    def update(self):
        #torch.autograd.set_detect_anomaly(True) #debug
        
        loss, idxs  = self.compute_loss()
        loss_mean = loss.mean()

        
        self.episode_loss.append(loss_mean.item())

        self.optimizer.zero_grad()
        loss_mean.backward()

        #konputazio grafoaren irudia sortzeko
        #dot = make_dot(loss_mean,params=dict(self.model.named_parameters()))
        #dot.render('test', view = True) #loss_mean atzeraka bidea pdf batean gordetzeko

        print(loss_mean)


        self.optimizer.step()
        if self.last_update >= self.step_update and self.index>0:
            self.last_update = 0
            self.soft_update(self.model, self.target_model, self.tau)


        if self.usePER:
            for idx, td_error in zip(idxs, loss.cpu().detach().numpy()):
                self.replay_buffer.update_priority(idx, td_error)
            