#!/usr/bin/env python
import sys
import pika
import json
import uuid
import hub.lib.config as config
import hub.lib.error as error

class Client(object):

    '''Class representing things that can get jobs.'''

    def __init__(self, config_file):
        try:
            conf = config.setup(config_file)
        except error.ConfigError, e:
            print e.msg
            raise e
        self.conf = config.setup()
        self.broker = conf.get('HUB', 'broker')
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.broker))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
                        self.on_response,
                        no_ack=True,
                        queue=self.callback_queue)

    def on_response(self, channel, method, properties, body):
        if self.corr_id == properties.correlation_id:
            self.response = body    

    def post_wait(self, jobid, request_type, taskdata=None, job=None):
        '''Takes a job as python dict and posts as json object.'''
        #Are we doing create, update, get?        
        if request_type is 'create':
            self.routing_key='hub_jobs'
            self.body = job
        elif request_type is 'update':
            self.routing_key='hub_results'
            self.body = json.dumps(taskdata)
        else:
            self.routing_key='hub_status'
            self.body = json.dumps(jobid)
                        
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print 'Submitting request for job with id %s' % jobid
        self.channel.basic_publish(exchange='',
                         routing_key=self.routing_key,
                         properties=pika.BasicProperties(
                              content_type='application/json',
                              reply_to = self.callback_queue,
                              correlation_id = self.corr_id,
                              ),
                         body=self.body)
        while self.response is None:
            self.connection.process_data_events()
        return str(self.response)
    
    def post(self, jobid, request_type, taskdata=None, job=None):
        '''Takes a job as python dict and posts as json object.'''
        #Are we doing create, update, get?        
        if request_type is 'create':
            self.routing_key='hub_jobs'
            self.body = job
            return "Please use post_wait"
        elif request_type is 'update':
            self.routing_key='hub_results'
            self.body = json.dumps(taskdata)
        else:
            self.routing_key='hub_status'
            self.body = json.dumps(jobid)
            return "please use post_wait"
            
        self.response = None
        self.corr_id = str(uuid.uuid4())
        print 'Submitting request for job with id %s' % jobid
        self.channel.basic_publish(exchange='',
                         routing_key=self.routing_key,
                         properties=pika.BasicProperties(
                              content_type='application/json',
                              reply_to = self.callback_queue,
                              correlation_id = str(jobid),
                              ),
                         body=self.body)
        return str(self.response)