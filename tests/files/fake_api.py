#!/usr/bin/python

'''Fake Moira API Server

'''

import json

from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8081


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
            state = {
                'trigger_id': trigger_id
            }
            self.log_message(
                'Handling: MoiraTrigger.has_image for %s' % trigger_id)

            self.wfile.write(json.dumps(state).encode())

    def do_PUT(self):

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_len = int(self.headers.get('content-length', 0))
        post_body = self.rfile.read(content_len)
        post_dict = json.loads(post_body.decode())

        if 'id' in post_dict:

            test_id = post_dict['id']
            response = {
                'id': test_id,
                'checkResult': ''
            }
            self.log_message(
                'Handling: MoiraTriggerManager.edit for %s' % test_id)

            self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":

    server = HTTPServer(('localhost', PORT), MoiraApiHandler)
    print('Starting fake api on port %s' % PORT)
    server.serve_forever()
