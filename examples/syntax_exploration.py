class CustomBlockA(Block):
    # 
    def send_messageA(self,data):
        self.message_handler.send(formatting_the_data(data))

    def slot_messageC(self,message):
        self.send_messageA(process_message(message))

class CustomBlockB(Block):

