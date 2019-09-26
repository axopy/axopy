import numpy as np
from axopy import design


def test_design():
    d = design.Design()
    b = d.add_block()

    # add trial with attributes as args
    t = b.add_trial(attrs={'attr': 1.0})
    # set trial attributes later
    t.attrs['var'] = True
    assert set(t.attrs) == set({'trial': 0, 'block': 0, 'attr': 1.0,
                                'var': True})

    # add an empty array
    t.add_array('1d')
    for i in range(3):
        t.arrays['1d'].stack(np.zeros(5))
    assert t.arrays['1d'].data.shape == (15,)

    t.add_array('2d')
    for i in range(3):
        t.arrays['2d'].stack(np.zeros((2, 5)))
    assert t.arrays['2d'].data.shape == (2, 15)

    t.add_array('static', data=np.random.randn(100))


def test_block_shuffle():
    d = design.Design()
    b = d.add_block()

    for i in range(10):
        b.add_trial()

    for i in range(10):
        b.shuffle()
        assert b[0].attrs['trial'] == 0


def test_block_shuffle_seed():
    d = design.Design()
    for i in range(2):
        b = d.add_block()

        for j in range(10):
            b.add_trial()

        b.shuffle(reset_index=False, seed=10)

    for j in range(10):
        assert d[0][j].attrs['trial'] == d[1][j].attrs['trial']
