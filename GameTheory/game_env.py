import gymnasium as gym
from gymnasium import spaces
from collections import deque

from game_modes import GameModes
from game_renderer import GameRenderer

class GameEnv(gym.Env):
    def __init__(self, game_type, render_mode, max_rounds=10):
        super(GameEnv, self).__init__()

        self.game_modes = GameModes(game_type)  # Pass game_type to the GameModes
        self.game = self.game_modes.get_game()
        self.action_names = self.game_modes.get_action_names()

        # Dynamically set the action and observation space based on the game
        num_actions = len(self.action_names)
        self.action_space = spaces.Discrete(num_actions)
        self.observation_space = spaces.Discrete(num_actions)

        self.renderer = GameRenderer(self.game_modes)  # Pass instantiated GameModes object to GameRenderer

        # reset after each step
        self.agent1_action = None
        self.agent2_action = None
        self.agent1_reward = 0
        self.agent2_reward = 0

        # reset after each episode
        self.agent1_cumulative_reward = 0
        self.agent2_cumulative_reward = 0
        self.agent1_avg_reward = 0
        self.agent2_avg_reward = 0

        # never reset
        self.agent1_total_cumulative_reward = 0
        self.agent2_total_cumulative_reward = 0
        self.agent1_total_avg_reward = 0
        self.agent2_total_avg_reward = 0

        self.should_render = render_mode
        self.max_rounds = max_rounds
        self.current_round = 0
        self.total_rounds = 0
        self.episode_counter = 1  # Initialize episode counter
        self.history = deque(maxlen=self.max_rounds)  # To store history of actions

        self.terminated = False
        self.truncated = False

    def reset(self):
        self.agent1_cumulative_reward = 0
        self.agent2_cumulative_reward = 0
        self.agent1_avg_reward = 0
        self.agent2_avg_reward = 0
        self.history.clear()
        self.current_round = 0
        return list(self.history)

    def step(self, action_agent1, action_agent2):
        self.current_round += 1
        self.total_rounds += 1
        self.agent1_action = action_agent1
        self.agent2_action = action_agent2  # This is our opponent for agent1

        # Adjusted this line to get the payoff using game_modes
        payoff = self.game_modes.get_payoff(self.agent1_action, self.agent2_action)
        self.agent1_reward = payoff[0]
        self.agent2_reward = payoff[1]

        self.agent1_cumulative_reward += self.agent1_reward
        self.agent2_cumulative_reward += self.agent2_reward

        self.agent1_avg_reward = self.agent1_cumulative_reward / self.current_round
        self.agent2_avg_reward = self.agent2_cumulative_reward / self.current_round

        # Update total cumulative rewards
        self.agent1_total_cumulative_reward += self.agent1_reward
        self.agent2_total_cumulative_reward += self.agent2_reward

        # Update total average rewards
        self.agent1_total_avg_reward = self.agent1_total_cumulative_reward / self.total_rounds
        self.agent2_total_avg_reward = self.agent2_total_cumulative_reward / self.total_rounds

        self.terminated = self.current_round >= self.max_rounds
        self.truncated = False  # This can remain False for now

        # Storing history
        self.history.append((self.agent1_action, self.agent2_action))

        # Return formatted for two agents
        return (self.agent2_action, self.agent1_action), (self.agent1_reward, self.agent2_reward), self.terminated, self.truncated, {}

    def render(self, mode='human'):
        if self.should_render and mode == 'human':
            self.renderer.render(self.agent1_action, self.agent2_action, self.agent1_reward, self.agent2_reward,
                                 self.agent1_cumulative_reward, self.agent2_cumulative_reward,
                                 self.agent1_avg_reward, self.agent2_avg_reward,
                                 self.agent1_total_cumulative_reward, self.agent2_total_cumulative_reward,
                                 self.agent1_total_avg_reward, self.agent2_total_avg_reward,
                                 self.episode_counter,
                                 self.current_round)  # Added episode and round counters as parameters

    def close(self):
        self.renderer.close()