import os

key_a = 'a'
key_b = 'b'
key_c = 'c'
key_d = 'd'
key_e = 'e'
key_f = 'f'
key_g = 'g'
key_h = 'h'
key_i = 'i'
key_j = 'j'
key_k = 'k'
key_l = 'l'
key_m = 'm'
key_n = 'n'
key_o = 'o'
key_p = 'p'
key_q = 'q'
key_r = 'r'
key_s = 's'
key_t = 't'
key_u = 'u'
key_v = 'v'
key_w = 'w'
key_x = 'x'
key_y = 'y'
key_z = 'z'

key_1 = '1'
key_2 = '2'
key_3 = '3'
key_4 = '4'
key_5 = '5'
key_6 = '6'
key_7 = '7'
key_8 = '8'
key_9 = '9'
key_0 = '0'

key_space = 'space'
key_return = 'return'
key_escape = 'escape'


def makedirs(path, exist_ok=False):
    """Recursively create directories.

    This is needed for Python versions earlier than 3.2, otherwise
    ``os.makedirs(path, exist_ok=True)`` would suffice.

    Parameters
    ----------
    path : str
        Path to directory to create.
    exist_ok : bool, optional
        If `exist_ok` is False (default), an exception is raised. Set to True
        if it is acceptable that the directory already exists.
    """
    try:
        os.makedirs(path)
    except OSError:
        if not exist_ok:
            raise
