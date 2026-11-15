from .loader import load


def post_init_hook(env):
    load(env)
