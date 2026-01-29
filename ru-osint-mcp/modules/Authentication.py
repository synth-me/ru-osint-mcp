from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers
from fastmcp.exceptions import ToolError
import os
import sys 
import hashlib 
import sqlite3 

os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_NAME = "../authentication-server/tokens.sqlite"

class SQLiteAuthMiddleware(Middleware):
    def verify_token(self, token: str) -> bool:

        print(f"Token is: {token}")
        
        if not token:
            return False
        
        incoming_hash = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM tokens WHERE token_hash = ?", (incoming_hash,)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        print(headers)
        token = headers.get("authorization") if headers else os.getenv("TOKEN")
        print(f"Token is {token}")
        if not self.verify_token(token):
            raise ToolError("Unauthorized: Invalid or missing secure token.")


        return await call_next(context)


