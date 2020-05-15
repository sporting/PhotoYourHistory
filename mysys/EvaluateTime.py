# -*- coding: UTF-8 -*-
from time import time

class EvaluateTimeHelper:
    def start(self,tag):
        self.tag = tag
        self.start_time = time()
    def stop(self):
        useTime = time()-self.start_time
        print(self.tag+':'+str(useTime))
        return useTime

if __name__ == "__main__":
    helper = EvaluateTimeHelper()
    helper.start()
    helper.stop()