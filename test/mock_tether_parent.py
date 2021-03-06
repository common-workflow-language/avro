from __future__ import print_function
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from future import standard_library
standard_library.install_aliases()
import sys
import set_avro_test_path
from http.server import BaseHTTPRequestHandler, HTTPServer
from avro import ipc
from avro import protocol
from avro import tether

import socket

def find_port():
  """
  Return an unbound port
  """
  s=socket.socket()
  s.bind(("127.0.0.1",0))

  port=s.getsockname()[1]
  s.close()

  return port

SERVER_ADDRESS = ('localhost', find_port())

class MockParentResponder(ipc.Responder):
  """
  The responder for the mocked parent
  """
  def __init__(self):
    ipc.Responder.__init__(self, tether.outputProtocol)

  def invoke(self, message, request):
    if message.name=='configure':
      print("MockParentResponder: Recieved 'configure': inputPort={0}".format(request["port"]))

    elif message.name=='status':
      print("MockParentResponder: Recieved 'status': message={0}".format(request["message"]))
    elif message.name=='fail':
      print("MockParentResponder: Recieved 'fail': message={0}".format(request["message"]))
    else:
      print("MockParentResponder: Recieved {0}".format(message.name))

    # flush the output so it shows up in the parent process
    sys.stdout.flush()

    return None

class MockParentHandler(BaseHTTPRequestHandler):
  """Create a handler for the parent.
  """
  def do_POST(self):
    self.responder =MockParentResponder()
    call_request_reader = ipc.FramedReader(self.rfile)
    call_request = call_request_reader.read_framed_message()
    resp_body = self.responder.respond(call_request)
    self.send_response(200)
    self.send_header('Content-Type', 'avro/binary')
    self.end_headers()
    resp_writer = ipc.FramedWriter(self.wfile)
    resp_writer.write_framed_message(resp_body)

if __name__ == '__main__':
  if (len(sys.argv)<=1):
    raise ValueError("Usage: mock_tether_parent command")

  cmd=sys.argv[1].lower()
  if (sys.argv[1]=='start_server'):
    if (len(sys.argv)==3):
      port=int(sys.argv[2])
    else:
      raise ValueError("Usage: mock_tether_parent start_server port")

    SERVER_ADDRESS=(SERVER_ADDRESS[0],port)
    print("mock_tether_parent: Launching Server on Port: {0}".format(SERVER_ADDRESS[1]))

    # flush the output so it shows up in the parent process
    sys.stdout.flush()
    parent_server = HTTPServer(SERVER_ADDRESS, MockParentHandler)
    parent_server.allow_reuse_address = True
    parent_server.serve_forever()
