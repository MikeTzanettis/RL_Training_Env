import math
import requests
import numpy as np
import time
import gym
import json
from gym import spaces

class AutoScalingEnv(gym.Env):
    def __init__(self,timesteps_file,metrics_file):
        super(AutoScalingEnv, self).__init__()
        self.services = ['service_1', 'service_2', 'service_3']
        self.min_pods = 1
        self.max_pods = 4
        # 3 possible actions: -1=scale down, 0=Do Nothing, +1=scale up
        self.action_space = spaces.Discrete(27)
        self.replicas = len(self.services) * [1]
        self.current_workload_rate = 0.0
        self.steps = 0
        self.max_episode_steps = 192
        low = np.array([
            0, # arrival_rate
            1,
            1,
            1, # replicas
            0  # latency
        ])
        high = np.array([
            np.inf,  # arrival_rate
            4,
            4, 
            4,       # replicas
            np.inf   # latency
        ])

        # Observation space is grid of size:rows x columns
        self.observation_space = spaces.Box(low, high, dtype=np.float64)
        with open(timesteps_file, 'r') as file:
            self.timesteps = json.load(file)
        
        with open(metrics_file, 'r') as file:
            self.metrics = json.load(file)



    def reset(self, seed=None, options=None):
        print("Reset function is called")
        observation = [
            0.0, # arrival rate
            1, # replicas 1
            1, # replicas 2
            1, # replicas 3
            0.0 # latency
        ]

        return observation

    def step(self, action):
        print(f"Step: {self.steps}")
        self.current_workload_rate = self.timesteps[str(self.steps)]["workload"]
        permutation = self.timesteps[str(self.steps)]["permutation"]

        self.replicas = [int(x) for x in permutation.split("-")]
        workload_rate = float(self.current_workload_rate)
        print(f"Current Workload Rate: {workload_rate}")
        print(f"Current Permutation: {permutation}")

        decoded_action = self._decimal_to_base3(action,len(self.services))
        print(f"Decoded Action: {decoded_action}")

        new_replicas = self.replicas
        for idx, action in enumerate(decoded_action):
            updated_replicas = self.replicas[idx] + action
            new_replicas[idx] = max(min(updated_replicas, self.max_pods), self.min_pods)

        print(f"Scaled Replicas: {new_replicas}")
        average_latency = self._get_latency(workload_rate,new_replicas)
        print(f"Latency is {average_latency}")
        observation = [
                       workload_rate,
                       new_replicas[0],
                       new_replicas[1],
                       new_replicas[2],
                       average_latency
                       ]

        reward,done = self._calculate_reward(observation)

        self.steps += 1
        if self.steps == self.max_episode_steps:
            print("Resetting Steps to 0.")
            self.steps = 0
        info = {}
        return observation,reward,done,info
        
    def close(self):
        pass
    
    def render(self):
        pass

    # def _apply_action(self, action):
        
    #     decoded_action = self._decimal_to_base3(action, len(self.services))
    #     invalid_action = False

            
    def _calculate_reward(self, observation):
        """
        Returns a reward with two components regarding the pod utilization
        and the application latency each weighted differently
        Reward range: [0, 100]
        """
        done = False
        is_invalid_action = False
        replicas = [None] * 3
        sla_latency = 0.5

        # Unpack observation
        (_,
         replicas[0],
         replicas[1],
         replicas[2],
         latency) = observation

        reward = 0

        pod_weight = 0.5
        latency_weight = 0.5

        if is_invalid_action:
            reward = -100
            done = True
            return reward,done

        # Pod reward
        pod_reward_total = 0
        for replica_num in replicas:
            pod_reward_total += -100 / (self.max_pods - 1) * replica_num \
                + 100 * self.max_pods / (self.max_pods - 1)
        average_pod_reward = pod_reward_total / 3
        reward += pod_weight * average_pod_reward

        # Hyperparameter that determines the drop on the latency reward part
        d = 10.0
        #d = 20.0
        #d = 50.0

        # Latency as a percentage of the declared SLA value
        latency_ratio = latency / sla_latency

        # Latency reward
        latency_ref_value = 0.8
        if latency_ratio < latency_ref_value:
            latency_reward = 100 * pow(math.e, -0.06 * d * pow(latency_ref_value - latency_ratio, 2))
        elif latency_ratio < 1:
            latency_reward = 100 * pow(math.e, -10 * d * pow(latency_ref_value - latency_ratio, 2))
        else:
            #print("----------Reward is -100------------")
            reward = -100
            #done = True
            return reward,done

        reward += latency_weight * latency_reward

        return reward,done

    def _get_latency(self,current_workload_rate,replicas):
        joint_replicas_string = '-'.join(map(str, replicas))
        workload_rate = str(current_workload_rate)
        latency = self.metrics[joint_replicas_string][workload_rate]["latency"]
        
        return latency

    def _decimal_to_base3(self,decimal_number, number_of_services):
        result = []
        while decimal_number > 0:
            remainder = decimal_number % 3
            result.insert(0, remainder)
            decimal_number //= 3

        while len(result) < number_of_services:
            result.insert(0, 0)

        return tuple(x - 1 for x in result)
