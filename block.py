import Queue
import threading
import sys

# This module sets up some nice abstractions, hopefully

# A special exception which indicates execution of a blocking command was interrupted
class InterruptedException(Exception):
    pass

# A special object which when retrieved from a queue indicates that an exception should be thrown
class InterruptObject:
    def __init__(self):
        self.exception=InterruptedException()

# A queue that can be interrupted by calling .interrupt()
# An interrupted get statement raises an exception, an InterruptedException by default.
class InterruptableQueue:
    def __init__(self,base=Queue.Queue,*args,**kwargs):
        self.q=base(*args,**kwargs)

    def put(self,*args,**kwargs):
        self.q.put(*args,**kwargs)

    def get(self,*args,**kwargs):
        result=self.q.get(self,*args,**kwargs)
        if isinstance(result,InterruptObject):
            raise result.exception
        return result

    def interrupt(self,*args,**kwargs):
        self.q.put(InterruptObject(),*args,**kwargs)

# A child is a thread of execution that takes care of some processing
# Children may pass exceptions down to their parents through use of an error handler.
# Children must be stoppable by calling stop()
class Child(threading.Thread):
    def __init__(self,*args,**kwargs):
        threading.Thread.__init__(self)
        self.deamon=True
        self.error_handler=None

    def run(self):
        try:
            self.process()
        except Exception as e:
            if self.error_handler:
                self.error_handler(self,e,sys.exc_info()[2])
            else:
                raise

    def process(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

# A block is a child that listens for data on a queue, and calls a callback when such data arrives.
# The queue should be interruptable for a listener's stop method to work.
class Listener(Child):
    def __init__(self,queue,callback):
        self.queue=queue
        self.callback=callback
        Child.__init__(self)

    def process(self):
        try:
            while True:
                self.callback(self.queue.get())
        except InterruptedException:
            pass

    def stop(self):
        self.queue.interrupt()

# A block is a collection of children.
# Calling run() blocks until the block is asked to stop, at which point it stops all of its children.
class Block:
    def __init__(self):
        self.children=set()
        self.control_queue=InterruptableQueue()

    def run(self): # spin until we are shut down or an error happens
        #print "block running."
        for c in self.children:
            c.start()
        finished=False
        try:
            (e,tb)=self.control_queue.get()
            #print "block error"
        except InterruptedException:
            finished=True
            #print "block finished"
        for c in self.children:
            c.stop()
        #print "joining children"
        for c in self.children:
            c.join()
        if not finished:
            raise Exception,e,tb

    def stop(self): # stop gracefully
        self.control_queue.interrupt()

    def add_child(self,child):
        child.error_handler=self.problem_child
        self.children.add(child)

    def problem_child(self,child,e,tb):
        self.control_queue.put((e,tb))


