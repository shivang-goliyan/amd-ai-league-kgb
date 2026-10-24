"""Load the GPU model once and retain the index throughout the evaluation."""
import os
from engine import GPUAgent
from rag_transport import make_server

if __name__=='__main__':
    agent=GPUAgent()
    agent.generate([{'role':'user','content':'Reply with OK.'}],max_tokens=4,seconds=20)
    server=make_server(os.getenv('RAG_SOCKET','/tmp/league-rag.sock'),agent.handle)
    print('RAG_READY',flush=True)
    try:server.serve_forever(poll_interval=.2)
    finally:server.server_close()
