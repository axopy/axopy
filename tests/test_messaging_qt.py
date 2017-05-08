from axopy.messaging import emitter, receiver

class FakeEmitterBlock(object):
    @emitter(data=str)
    def fake_emitter(self, data):
        print("emitting: {}".format(data))
        return data

class FakeReceiverBlock(object):
    @receiver
    def fake_receiver(self, data):
        print("recieved: {}".format(data))

if __name__ == '__main__':
    print("in main, init blocks")
    block1 = FakeEmitterBlock()
    block2 = FakeReceiverBlock()

    print("connecting")
    # block1.fake_emitter.connect(block2.fake_receiver)
    block2.fake_receiver.connect(block1.fake_emitter)
    print(block1.fake_emitter.data_format)
    

    print("calling emitter from main")
    block1.fake_emitter("sending some stuff")
