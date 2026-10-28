# Dijalankan saat build di Cloudflare: mengekstrak p-bewan-deck-itch.zip ke folder ini (game + server),
# tanpa menimpa package.json / wrangler.toml / worker/ / .assetsignore milik deploy ini.
import zipfile, sys, os
KEEP = {'package.json', 'wrangler.toml', '.assetsignore', 'unpack.py'}
z = zipfile.ZipFile('p-bewan-deck-itch.zip')
n = 0
for name in z.namelist():
    if name in KEEP or name.startswith('worker/') or name.endswith('/'): continue
    if name.startswith('/') or '..' in name.split('/'): continue   # jaga-jaga path berbahaya
    z.extract(name, '.'); n += 1
print('diekstrak', n, 'file')
# Isi kolom Server otomatis kalau game dibuka dari alamat *.workers.dev (server ada di domain yang sama, jalur /ws)
p = 'src/main.js'; s = open(p, encoding='utf-8').read()
old = "$('srvUrl').value = store.get('srv', '');"
new = "$('srvUrl').value = store.get('srv', /\\.workers\\.dev$|^localhost$/.test(location.hostname) ? (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws' : '');"
if s.count(old) != 1: sys.exit('GAGAL: baris srvUrl di src/main.js tidak ditemukan')
open(p, 'w', encoding='utf-8').write(s.replace(old, new))
# Zip untuk itch.io: isinya sama dengan game, tapi kolom Server sudah terisi alamat Worker ini. Diunduh dari /itch.zip
ITCH_URL = 'wss://p-bewan-deck.godfire017.workers.dev/ws'
itch_main = s.replace(old, "$('srvUrl').value = store.get('srv', '" + ITCH_URL + "');")
if itch_main == s: sys.exit('GAGAL: tidak bisa membuat main.js untuk itch')
with zipfile.ZipFile('itch.zip', 'w', zipfile.ZIP_DEFLATED) as out:
    for name in z.namelist():
        if name in KEEP or name.startswith('worker/') or name.endswith('/') or name.startswith('/') or '..' in name.split('/'): continue
        if name == 'src/main.js': out.writestr(name, itch_main)
        else: out.write(name, name)
print('itch.zip', round(os.path.getsize('itch.zip') / 1048576, 1), 'MB')
for f in ('index.html', 'server/room.js', 'src/core/sim.js', 'assets/models/bow.glb'):
    if not os.path.exists(f): sys.exit('GAGAL: file hilang setelah ekstrak: ' + f)
print('OK')
