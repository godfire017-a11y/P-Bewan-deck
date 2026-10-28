import { Lobby } from '../server/room.js';

export class GameLobby {
  constructor() { this.lobby = new Lobby(); this.where = new WeakMap(); this.socks = new Set(); this.timer = null; this.reaper = null; }

  fetch(request) {
    if (request.headers.get('Upgrade') !== 'websocket') return new Response('Butuh WebSocket', { status: 426 });
    const pair = new WebSocketPair(); const [client, ws] = Object.values(pair);
    ws.accept(); ws.seen = Date.now(); this.socks.add(ws); this.startTimers();
    ws.addEventListener('message', (ev) => {
      ws.seen = Date.now();
      const d = ev.data; if (typeof d !== 'string' || d.length > 2048) return;
      let m; try { m = JSON.parse(d); } catch (e) { return; }
      if (!m || typeof m.t !== 'string') return;
      const room = this.where.get(ws);
      if (m.t === 'quick') this.where.set(ws, this.lobby.quick(ws, m.pick, m.stage));
      else if (m.t === 'create') this.where.set(ws, this.lobby.create(ws, m.pick, m.stage));
      else if (m.t === 'join') { const r = this.lobby.joinCode(ws, m.code, m.pick); if (r) this.where.set(ws, r); }
      else if (room) room.onMessage(ws, m);
      else if (m.t === 'ping') ws.send(JSON.stringify({ t: 'pong', c: m.c }));
    });
    const gone = () => { if (!this.socks.delete(ws)) return; const r = this.where.get(ws); if (r) r.leave(ws); if (!this.socks.size) this.stopTimers(); };
    ws.addEventListener('close', gone); ws.addEventListener('error', gone);
    return new Response(null, { status: 101, webSocket: client });
  }

  startTimers() {
    if (this.timer) return;
    this.timer = setInterval(() => this.lobby.tick(), 1000 / 60);
    this.reaper = setInterval(() => { const now = Date.now(); for (const s of this.socks) if (now - s.seen > 30000) { try { s.close(1000, 'idle'); } catch (e) {} } }, 10000);
  }
  stopTimers() { clearInterval(this.timer); clearInterval(this.reaper); this.timer = this.reaper = null; }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/ws') return env.LOBBY.get(env.LOBBY.idFromName('main')).fetch(request);
    return new Response('Tidak ditemukan', { status: 404 });
  },
};
