"""
EMMA v2.0 — Serveur WebSocket + mDNS
Gestion des connexions ESP32, stream audio PCM/WAV, commandes etat.
Createur : ONANA GREGOIRE LEGRAND | Yaounde, Cameroun
"""

import asyncio
import json
import logging
import socket

import websockets
from zeroconf import ServiceInfo, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

from config import WEBSOCKET_HOST, WEBSOCKET_PORT, MDNS_NAME, MDNS_SERVICE

log = logging.getLogger("emma.ws")

# ─── Registre des connexions ESP32 actives ────────────────────────────────────
connected_clients: set[websockets.WebSocketServerProtocol] = set()

# Queue partagee : audio PCM recu depuis l'ESP32
audio_queue: asyncio.Queue = asyncio.Queue()

# Callbacks injectes par main.py
_on_wake_word: callable = None
_on_audio_chunk: callable = None
_on_audio_end: callable = None


def set_callbacks(wake_word_cb, audio_chunk_cb, audio_end_cb):
    global _on_wake_word, _on_audio_chunk, _on_audio_end
    _on_wake_word   = wake_word_cb
    _on_audio_chunk = audio_chunk_cb
    _on_audio_end   = audio_end_cb


# ─── Gestionnaire de connexion par client ─────────────────────────────────────

async def _handle_client(websocket: websockets.WebSocketServerProtocol, path: str):
    client_ip = websocket.remote_address[0]
    log.info(f"[WS] ESP32 connecte depuis {client_ip}")
    connected_clients.add(websocket)

    # Envoyer etat initial
    await _send_state(websocket, "idle")

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Stream audio PCM binaire
                if _on_audio_chunk:
                    await _on_audio_chunk(message)
                await audio_queue.put(message)

            elif isinstance(message, str):
                try:
                    data = json.loads(message)
                    event = data.get("event", "")

                    if event == "wake_word":
                        log.info("[WS] Wake word detecte !")
                        if _on_wake_word:
                            await _on_wake_word(websocket)

                    elif event == "audio_end":
                        log.info("[WS] Fin du stream audio.")
                        if _on_audio_end:
                            await _on_audio_end(websocket)

                except json.JSONDecodeError:
                    log.warning(f"[WS] Message JSON invalide : {message[:50]}")

    except websockets.exceptions.ConnectionClosedOK:
        log.info(f"[WS] ESP32 {client_ip} deconnecte proprement.")
    except websockets.exceptions.ConnectionClosedError as e:
        log.warning(f"[WS] Connexion perdue avec {client_ip} : {e}")
    finally:
        connected_clients.discard(websocket)


# ─── Envoi d'etat vers l'ESP32 ────────────────────────────────────────────────

async def _send_state(websocket, state: str):
    """Envoie un JSON d'etat a un ESP32 specifique."""
    try:
        await websocket.send(json.dumps({"state": state}))
    except Exception:
        pass


async def broadcast_state(state: str):
    """Diffuse un etat a tous les ESP32 connectes."""
    if connected_clients:
        msg = json.dumps({"state": state})
        await asyncio.gather(
            *[ws.send(msg) for ws in connected_clients],
            return_exceptions=True
        )


async def broadcast_audio(wav_bytes: bytes):
    """Envoie les bytes WAV de la reponse TTS a tous les ESP32."""
    if connected_clients:
        await asyncio.gather(
            *[ws.send(wav_bytes) for ws in connected_clients],
            return_exceptions=True
        )
        log.info(f"[WS] {len(wav_bytes)} bytes WAV envoyes a {len(connected_clients)} ESP32.")


# ─── Annonce mDNS ────────────────────────────────────────────────────────────

async def _announce_mdns():
    """Annonce le service EMMA sur le reseau local via mDNS/Zeroconf."""
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    info = ServiceInfo(
        MDNS_SERVICE,
        f"{MDNS_NAME}.{MDNS_SERVICE}",
        addresses=[socket.inet_aton(local_ip)],
        port=WEBSOCKET_PORT,
        properties={"version": "2.0", "creator": "ONANA GREGOIRE LEGRAND"},
        server=f"{MDNS_NAME}.local.",
    )

    zc = AsyncZeroconf()
    await zc.async_register_service(info)
    log.info(f"[mDNS] EMMA annoncee : {MDNS_NAME}.local → {local_ip}:{WEBSOCKET_PORT}")
    return zc, info


# ─── Demarrage du serveur ─────────────────────────────────────────────────────

async def start_server():
    """Demarre le serveur WebSocket et l'annonce mDNS."""
    zc, info = await _announce_mdns()

    server = await websockets.serve(
        _handle_client,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT,
        ping_interval=20,
        ping_timeout=10,
    )
    log.info(f"[WS] Serveur WebSocket demarre sur {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    return server, zc, info
