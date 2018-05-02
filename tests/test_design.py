import numpy as np
from axopy import design

d = design.Design()
b = d.add_block()
t = b.add_trial(attrs={'attr': 0})
t.attrs['var'] = True
t.add_array('static', data=np.random.randn(100))
t.add_array('dynamic')
for i in range(10):
    t.arrays['dynamic'].stack(np.random.randn(5))

# class CustomTask(Task):
# 
#     def setup_design(self, design):
#         for i in range(10):
#             block = design.add_block()
#             for j in range(10):
#                 # can set trial attributes optionally
#                 trial = block.add_trial(
#                     attrs={
#                         'target_x': j,
#                         'target_y': j
#                     }
#                 )
#                 # can add/reset attrs at any time
#                 trial.attrs['extra'] = 0
# 
#                 # add array with data already in it
#                 trial.add_array('random', data=np.random.randn(100))
# 
#                 # add an empty array
#                 trial.add_array('cursor')
# 
#             block.shuffle()
# 
#     def update(self, data):
#         # stack data in a trial array
#         self.trial.arrays['cursor'].stack(data)
# 
#     def finish_trial(self):
#         # set a trial attribute
#         self.trial.attrs['extra'] = 1
# 
#         self.storage.write(self.trial)
