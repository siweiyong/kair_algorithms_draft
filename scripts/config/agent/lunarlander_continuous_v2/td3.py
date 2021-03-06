# -*- coding: utf-8 -*-
"""Run module for TD3 on LunarLanderContinuous-v2.

- Author: whikwon
- Contact: whikwon@gmail.com
"""

import torch
import torch.optim as optim

from algorithms.common.networks.mlp import MLP
from algorithms.common.noise import GaussianNoise
from algorithms.td3.agent import Agent

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# hyper parameters
hyper_params = {
    "GAMMA": 0.99,
    "TAU": 5e-3,
    "BUFFER_SIZE": int(1e6),
    "BATCH_SIZE": 100,
    "LR_ACTOR": 1e-3,
    "LR_CRITIC": 1e-3,
    "WEIGHT_DECAY": 0.0,
    "EXPLORATION_NOISE": 0.1,
    "TARGET_POLICY_NOISE": 0.2,
    "TARGET_POLICY_NOISE_CLIP": 0.5,
    "POLICY_UPDATE_FREQ": 2,
    "INITIAL_RANDOM_ACTIONS": 1e4,
    "NETWORK": {"ACTOR_HIDDEN_SIZES": [400, 300], "CRITIC_HIDDEN_SIZES": [400, 300]},
}


def get(env, args):
    """Run training or test.

    Args:
        env (gym.Env): openAI Gym environment with continuous action space
        args (argparse.Namespace): arguments including training settings

    """
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]

    hidden_sizes_actor = hyper_params["NETWORK"]["ACTOR_HIDDEN_SIZES"]
    hidden_sizes_critic = hyper_params["NETWORK"]["CRITIC_HIDDEN_SIZES"]

    # create actor
    actor = MLP(
        input_size=state_dim,
        output_size=action_dim,
        hidden_sizes=hidden_sizes_actor,
        output_activation=torch.tanh,
    ).to(device)

    actor_target = MLP(
        input_size=state_dim,
        output_size=action_dim,
        hidden_sizes=hidden_sizes_actor,
        output_activation=torch.tanh,
    ).to(device)
    actor_target.load_state_dict(actor.state_dict())

    # create critic1
    critic1 = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)

    critic1_target = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)
    critic1_target.load_state_dict(critic1.state_dict())

    # create critic2
    critic2 = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)

    critic2_target = MLP(
        input_size=state_dim + action_dim,
        output_size=1,
        hidden_sizes=hidden_sizes_critic,
    ).to(device)
    critic2_target.load_state_dict(critic2.state_dict())

    # concat critic parameters to use one optim
    critic_parameters = list(critic1.parameters()) + list(critic2.parameters())

    # create optimizer
    actor_optim = optim.Adam(
        actor.parameters(),
        lr=hyper_params["LR_ACTOR"],
        weight_decay=hyper_params["WEIGHT_DECAY"],
    )

    critic_optim = optim.Adam(
        critic_parameters,
        lr=hyper_params["LR_CRITIC"],
        weight_decay=hyper_params["WEIGHT_DECAY"],
    )

    # noise
    exploration_noise = GaussianNoise(
        action_dim,
        min_sigma=hyper_params["EXPLORATION_NOISE"],
        max_sigma=hyper_params["EXPLORATION_NOISE"],
    )

    target_policy_noise = GaussianNoise(
        action_dim,
        min_sigma=hyper_params["TARGET_POLICY_NOISE"],
        max_sigma=hyper_params["TARGET_POLICY_NOISE"],
    )

    # make tuples to create an agent
    models = (actor, actor_target, critic1, critic1_target, critic2, critic2_target)
    optims = (actor_optim, critic_optim)
    noises = (exploration_noise, target_policy_noise)

    # create an agent
    return Agent(env, args, hyper_params, models, optims, noises)
