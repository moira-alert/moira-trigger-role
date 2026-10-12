#!/usr/bin/python

'''Stateful Fake Moira API Server

Serves the minimum of the Moira API that the moira_trigger module uses and
keeps the stored trigger data in memory, so consecutive requests behave like
a real server: a trigger that was just created is returned by the next
fetch, which is what the idempotency test relies on.

Endpoints:
    GET    /api/trigger                         -> 200 {} (readiness)
    GET    /api/trigger/{id}/state              -> existing trigger state
    GET    /api/trigger/{id}                    -> stored trigger data
    PUT    /api/trigger?validate                -> create/update a trigger
    PUT    /api/trigger/{id}?validate           -> create/update a trigger
    DELETE /api/trigger/{id}                    -> remove a trigger

'''

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

PORT = 8081

# In-memory trigger store: trigger_id -> trigger dict.
TRIGGERS = {}


def path_parts(path):
    return [part for part in urlparse(path).path.split('/') if part]


class MoiraApiHandler(BaseHTTPRequestHandler):

    '''Handling upcoming HTTP Requests.

    '''

    def _write(self, payload):
        body = json.dumps(payload).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parts = path_parts(self.path)
        # /api/trigger/{id}/state
        if len(parts) == 4 and parts[1] == 'trigger' and parts[3] == 'state':
            trigger_id = parts[2]
            if trigger_id in TRIGGERS:
                self.log_message('Recognized trigger %s' % trigger_id)
                self._write({
                    'trigger_id': trigger_id,
                    'state': 'OK'
                })
            else:
                self._write({'trigger_id': trigger_id})
            return

        # /api/trigger/{id}
        if len(parts) == 3 and parts[1] == 'trigger':
            trigger_id = parts[2]
            if trigger_id in TRIGGERS:
                self._write(TRIGGERS[trigger_id])
            else:
                self._write({'trigger_id': trigger_id})
            return

        # /api/trigger -> readiness
        if len(parts) <= 2 and (not parts or parts[0] == 'api'):
            self._write({})
            return

        self.send_response(404)
        self.end_headers()

    def do_PUT(self):
        parts = path_parts(self.path)
        content_len = int(self.headers.get('content-length', 0))
        post_body = self.rfile.read(content_len)
        post_dict = json.loads(post_body.decode('utf-8'))

        trigger_id = parts[2] if len(parts) == 3 else post_dict.get('id')
        if not trigger_id:
            self.send_response(400)
            self.end_headers()
            return

        post_dict['id'] = trigger_id
        TRIGGERS[trigger_id] = post_dict
        self.log_message('Stored trigger %s' % trigger_id)
        self._write({'id': trigger_id, 'checkResult': ''})

    def do_DELETE(self):
        parts = path_parts(self.path)
        trigger_id = parts[2] if len(parts) == 3 else None
        if trigger_id:
            TRIGGERS.pop(trigger_id, None)
            self.log_message('Removed trigger %s' % trigger_id)
        self._write({})


if __name__ == '__main__':
    server = HTTPServer(('localhost', PORT), MoiraApiHandler)
    print('Starting stateful fake api on port %s' % PORT)
    server.serve_forever()