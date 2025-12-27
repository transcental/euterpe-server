from contextlib import asynccontextmanager
from tkinter.constants import Y
import uuid
from engineio.base_server import secrets
import socketio
from fastapi import FastAPI
import uvicorn

from euterpe_server.auth import create_access_token, get_user_from_token
from euterpe_server.config import config
from euterpe_server.redis import db

sio: socketio.AsyncServer = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/auth/register")
async def register_device():
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id)
    return {"token": token, "user_id": user_id}


@sio.event
async def connect(sid, environ, auth):
    # Check auth object first (Android), then query params (macOS)
    token = auth.get("token") if auth else None
    if not token:
        from urllib.parse import parse_qs
        query_string = environ.get("QUERY_STRING", "")
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]
    
    if not token:
        print(f"anonymous connection: {sid}")
        return True
    
    user_id = await get_user_from_token(token)
    if not user_id:
        return False

    await sio.save_session(sid, {"user_id": user_id})
    print(f"User {user_id} connected with session id {sid}")
    await sio.enter_room(sid, user_id)


@sio.event
async def request_pairing_code(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id")
    
    code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
    await db.set_pairing_code(code, user_id)
    
    await sio.emit("display_code", {"code": code}, to=sid)
    print(f"Generated pairing code {code} for user {user_id}")


@sio.event
async def submit_pairing_code(sid, data):
    code = data.get("code")
    
    mac_id = await db.get_mac_id_by_code(code)
    if mac_id is not None:
        new_token = create_access_token(mac_id)
        
        # Notify the Android device
        await sio.emit("pairing_success", {
            "token": new_token,
            "user_id": mac_id
        }, to=sid)
        
        # Notify the Mac device (in its room)
        await sio.emit("pairing_success", {
            "token": new_token,
            "user_id": mac_id
        }, room=mac_id, skip_sid=sid)
        
        await sio.enter_room(sid, mac_id)
        await sio.save_session(sid, {"user_id": mac_id})
        
        await db.save_session(new_token, mac_id)
        
        print(f"Paired Mac ID {mac_id} with code {code}")
    else:
        await sio.emit("error", {"message": "Invalid/expired code"}, to=sid)


@sio.event
async def metadata_update(sid, data):
    session = await sio.get_session(sid)
    await sio.emit("update_ui", data, room=session["user_id"], skip_sid=sid)


@sio.event
async def timestamp_update(sid, data):
    session = await sio.get_session(sid)
    await sio.emit("update_timestamp", data, room=session["user_id"], skip_sid=sid)


@sio.event
async def execute_command(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return
    await sio.emit("execute_command", data, room=user_id, skip_sid=sid)


@sio.event
async def seek(sid, data):
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return
    await sio.emit("seek", data, room=user_id, skip_sid=sid)


@sio.event
async def request_sync(sid):
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if not user_id:
        return
    await sio.emit("request_sync", {}, room=user_id, skip_sid=sid)

socket_app = socketio.ASGIApp(sio, app)


def run():
    uvicorn.run("euterpe_server.main:socket_app", host="0.0.0.0", port=config.port, reload=config.debug)


if __name__ == "__main__":
    run()
