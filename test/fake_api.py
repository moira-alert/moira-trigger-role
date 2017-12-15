#!/usr/bin/python

'''Fake Moira API Server

'''

import json
import logging

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

PORT = 80


class MoiraApiHandler(BaseHTTPRequestHandler):

    '''Handling upcoming HTTP Requsts.

    '''

    def do_GET(self):

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if self.path.endswith('state'):

            api_trigger_path = self.path.split('/')
            trigger_id = api_trigger_path[2]
            state = '{"trigger_id":"%s"}' % trigger_id

            logging.info(
                'Handling: MoiraTrigger.has_image for %s' % trigger_id)

            self.wfile.write(state.encode())

        if self.path.endswith('tag'):

            taglist = '{"list":"[]"}'
            logging.info(
                'Handling: main.tag_cleanup')

            self.wfile.write(taglist.encode())

    def do_PUT(self):

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        post_dict = json.loads(post_body.decode())

        if 'id' in post_dict:

            testid = post_dict['id']
            response = '{"id":"%s"}' % testid
            logging.info(
                'Handling: MoiraTriggerManager.edit for %s' % testid)

            self.wfile.write(response.encode())

if __name__ == "__main__":

    server = HTTPServer(('localhost', PORT), MoiraApiHandler)
    logging.info('Starting fake api on port %s' % PORT)
    server.serve_forever()
