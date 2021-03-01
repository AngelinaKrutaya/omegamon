from libs.pyjubula import *

config(log_level=LOG_ERROR)

class TEPMapper:     
    def __init__(self, host, aut_id, threshold=1.0, name_factor=0.2, path_factor=0.8, context_factor=0.0):
        self.agent = AUTAgent()
        self.agent.connect(host)
        self.aut = self.agent.aut_connect(aut_id)
        self.aut.define(threshold, name_factor, path_factor, context_factor)

    def get_mapping(self): 
        self.aut.set_mapping_mode()  
        mapping = self.aut.get_mapping()
        print(str(mapping).replace('\'', '\"'))