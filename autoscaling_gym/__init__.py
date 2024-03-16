from gym import register

gathered_data_dictionary_file = 'json_data.json'
timesteps = 'timesteps.json'

register(
    id='AutoScalingEnv-v0',
    entry_point='autoscaling_gym.envs:AutoScalingEnv',
    kwargs={
        'metrics_file': gathered_data_dictionary_file,
        'timesteps_file': timesteps
    }
)
