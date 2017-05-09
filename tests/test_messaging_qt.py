import pytest
from axopy.messaging import emitter, receiver

class FakeBlock1(object):
    @emitter(data=str) # I don't think this is enforced anywhere
    def emitter1(self, data):
        print("emitting1: {}".format(data))
        return data

    @receiver
    def receiver2(self, data):
        print("recieved2: {}".format(data))
        

class FakeBlock2(object):
    def __init__(self):
        self.number_called = 0

    @receiver
    def receiver1(self, data):
        print("recieved1: {}".format(data))
        self.number_called += 1
        self.emitter2(self.number_called)
        

    @emitter(number=int) # I don't think this is enforced anywhere
    def emitter2(self, number):
        print("emitting2: {}".format(number))
        return number


@emitter(plusthree=float)
def emit_func(num):
    return num + 3.0


@receiver
def recv_func(result):
    print("recv_func received: {}".format(result))


if __name__ == '__main__':
    print("in main, init blocks")
    block1 = FakeBlock1()
    block2 = FakeBlock2()

    print("connecting")
    #block1.emitter1.connect(block2.receiver1)
    block2.receiver1.connect(block1.emitter1)
    block2.emitter2.connect(block1.receiver2)

    print("block1:",block1.emitter1.data_format)
    print("block2:",block2.emitter2.data_format)
    

    print("calling emitter from main")
    block1.emitter1("sending some stuff")

    block1.emitter1.disconnect(block2.receiver1)
    block1.emitter1("sending more stuff")

    emit_func.connect(recv_func)
    emit_func(3.2)
