# -*- coding: utf-8 -*-
"""HORA DO CALDO PC - servidor de pedidos + impressao termica (ESC/POS)."""
import os, sys, sqlite3, socket, webbrowser, datetime, threading, textwrap
from flask import Flask, request, jsonify, send_file

FROZEN = getattr(sys, "frozen", False)
BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HOME, "dados"); os.makedirs(DATA, exist_ok=True)
DB = os.path.join(DATA, "hora_do_caldo.db")
PORT = 5000
app = Flask(__name__)

DEFAULTS = {"title": "HORA DO CALDO", "printer_mode": "windows", "printer_name": "",
            "printer_ip": "192.168.0.50", "printer_port": "9100", "columns": "48",
            "codepage": "cp860", "feed": "4", "cut": "1", "copies": "1", "kitchen_prices": "1"}
CP = {"cp437": 0, "cp850": 2, "cp860": 3, "cp858": 19}

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def q(sql, a=(), one=False, commit=False):
    c = db()
    try:
        cur = c.execute(sql, a)
        if commit:
            c.commit(); return cur.lastrowid
        r = [dict(x) for x in cur.fetchall()]
        return (r[0] if r else None) if one else r
    finally:
        c.close()

def init():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS mesas(id INTEGER PRIMARY KEY, name TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, mesa TEXT, created TEXT, status TEXT DEFAULT 'aberto', note TEXT);
    CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY, order_id INTEGER, name TEXT, price REAL, qty INTEGER, note TEXT);
    CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);""")
    if not c.execute("SELECT 1 FROM mesas").fetchone():
        c.executemany("INSERT INTO mesas(name) VALUES(?)", [(str(i),) for i in range(1, 11)])
    if not c.execute("SELECT 1 FROM products").fetchone():
        c.executemany("INSERT INTO products(name,category,price) VALUES(?,?,?)", [
            ("Caldo de Feijão", "Pratos", 18.0), ("Caldo de Mandioca", "Pratos", 20.0),
            ("Refrigerante Lata", "Bebidas", 6.0), ("Suco Natural", "Bebidas", 8.0)])
    for k, v in DEFAULTS.items():
        c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, v))
    c.commit(); c.close()

def S():
    return {r["k"]: r["v"] for r in q("SELECT * FROM settings")}

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    return r

# ---------------- impressao ----------------
def money(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def line2(l, r, w):
    return l + " " * max(1, w - len(l) - len(r)) + r

def item_lines(txt, price, w):
    if not price:
        return textwrap.wrap(txt, w) or [""]
    if len(txt) + len(price) + 1 <= w:
        return [line2(txt, price, w)]
    return textwrap.wrap(txt, w) + [line2("", price, w)]

def ticket(kind, orders, mesa, s):
    w = int(s["columns"]); L = []
    a = lambda t="", st="n": L.append((t, st))
    a(s["title"], "cbig")
    a("PEDIDO - COZINHA" if kind == "cozinha" else "CONTA DA MESA", "cb")
    a("-" * w)
    a("MESA " + mesa, "cbig")
    a(datetime.datetime.now().strftime("%d/%m/%Y %H:%M"), "c")
    if kind == "cozinha":
        a("Pedido n. " + ", ".join(str(o["id"]) for o in orders), "c")
    a("-" * w)
    show = kind == "conta" or s.get("kitchen_prices") == "1"
    total = 0.0
    for o in orders:
        its = q("SELECT * FROM items WHERE order_id=?", (o["id"],))
        if kind == "conta" and len(orders) > 1:
            a("Pedido %d - %s" % (o["id"], o["created"][11:16]))
        for it in its:
            sub = it["price"] * it["qty"]; total += sub
            for ln in item_lines("%dx %s" % (it["qty"], it["name"]), money(sub) if show else "", w):
                a(ln, "b")
            if it["note"]:
                for ln in textwrap.wrap("OBS: " + it["note"], w - 2):
                    a("  " + ln)
        if o["note"]:
            for ln in textwrap.wrap("OBS PEDIDO: " + o["note"], w):
                a(ln, "b")
    a("-" * w)
    if show:
        a(line2("TOTAL", money(total), w), "b")
        a("-" * w)
    if kind == "conta":
        a("Obrigado pela preferencia!", "c")
    return L, total

def render(L, s):
    cp = s["codepage"]
    out = b"\x1b@" + b"\x1bt" + bytes([CP.get(cp, 3)])
    for t, st in L:
        out += b"\x1ba\x01" if st.startswith("c") else b"\x1ba\x00"
        out += b"\x1bE\x01" if "b" in st else b"\x1bE\x00"
        out += b"\x1d!\x11" if "big" in st else b"\x1d!\x00"
        out += t.encode(cp, "replace") + b"\n"
    out += b"\x1d!\x00\x1bE\x00" + b"\n" * int(s["feed"])
    if s["cut"] == "1":
        out += b"\x1dVB\x00"
    return out

def send(data, s):
    open(os.path.join(DATA, "ultimo_ticket.bin"), "wb").write(data)
    mode = s["printer_mode"]
    for _ in range(max(1, int(s["copies"]))):
        if mode == "rede":
            with socket.create_connection((s["printer_ip"], int(s["printer_port"])), timeout=5) as k:
                k.sendall(data)
        elif mode == "windows":
            import win32print
            name = s["printer_name"] or win32print.GetDefaultPrinter()
            h = win32print.OpenPrinter(name)
            try:
                win32print.StartDocPrinter(h, 1, ("HORA DO CALDO", None, "RAW"))
                win32print.StartPagePrinter(h); win32print.WritePrinter(h, data)
                win32print.EndPagePrinter(h); win32print.EndDocPrinter(h)
            finally:
                win32print.ClosePrinter(h)

def do_print(kind, orders, mesa):
    s = S()
    try:
        L, _ = ticket(kind, orders, mesa, s)
        open(os.path.join(DATA, "ultimo_ticket.txt"), "w", encoding="utf-8").write("\n".join(t for t, _ in L))
        send(render(L, s), s)
        return True, "Impresso"
    except Exception as e:
        return False, "Falha ao imprimir: %s" % e

# ---------------- API ----------------
@app.get("/")
def home():
    return send_file(os.path.join(BASE, "web", "admin.html"))

@app.get("/api/info")
def info():
    return jsonify(name="HORA DO CALDO PC", ip=local_ip(), port=PORT)

@app.get("/api/menu")
def menu():
    return jsonify(q("SELECT id,name,category,price FROM products WHERE active=1 ORDER BY category,name"))

@app.get("/api/mesas")
def mesas():
    r = q("SELECT * FROM mesas")
    r.sort(key=lambda m: (0, int(m["name"])) if m["name"].isdigit() else (1, m["name"]))
    return jsonify(r)

@app.post("/api/mesas")
def mesa_add():
    n = str(request.json.get("name", "")).strip()
    if n: q("INSERT OR IGNORE INTO mesas(name) VALUES(?)", (n,), commit=True)
    return jsonify(ok=True)

@app.delete("/api/mesas/<int:i>")
def mesa_del(i):
    q("DELETE FROM mesas WHERE id=?", (i,), commit=True); return jsonify(ok=True)

@app.get("/api/products")
def prod_list():
    return jsonify(q("SELECT * FROM products ORDER BY category,name"))

@app.post("/api/products")
def prod_save():
    d = request.json; p = (d["name"].strip(), d["category"].strip() or "Geral", float(d["price"]), 1 if d.get("active", 1) else 0)
    if d.get("id"): q("UPDATE products SET name=?,category=?,price=?,active=? WHERE id=?", p + (d["id"],), commit=True)
    else: q("INSERT INTO products(name,category,price,active) VALUES(?,?,?,?)", p, commit=True)
    return jsonify(ok=True)

@app.delete("/api/products/<int:i>")
def prod_del(i):
    q("DELETE FROM products WHERE id=?", (i,), commit=True); return jsonify(ok=True)

@app.get("/api/settings")
def set_get(): return jsonify(S())

@app.post("/api/settings")
def set_save():
    for k, v in request.json.items():
        if k in DEFAULTS: q("INSERT OR REPLACE INTO settings VALUES(?,?)", (k, str(v)), commit=True)
    return jsonify(ok=True)

@app.get("/api/printers")
def printers():
    try:
        import win32print
        return jsonify([p[2] for p in win32print.EnumPrinters(2 | 4)])
    except Exception:
        return jsonify([])

@app.post("/api/test")
def test_print():
    s = S(); L = [(s["title"], "cbig"), ("TESTE DE IMPRESSAO", "cb"), ("-" * int(s["columns"]), "n"),
                  ("Acentuacao: ção é ã õ Ç", "n"), ("1234567890" * 8, "n")]
    try: send(render(L, s), s); return jsonify(ok=True, msg="Teste enviado")
    except Exception as e: return jsonify(ok=False, msg=str(e))

@app.post("/api/orders")
def order_new():
    d = request.get_json(force=True); mesa = str(d.get("mesa", "")).strip()
    if not mesa or not d.get("items"): return jsonify(error="Pedido vazio"), 400
    oid = q("INSERT INTO orders(mesa,created,note) VALUES(?,?,?)",
            (mesa, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), d.get("note", "")), commit=True)
    for i in d["items"]:
        p = q("SELECT * FROM products WHERE id=?", (i["id"],), one=True)
        if p: q("INSERT INTO items(order_id,name,price,qty,note) VALUES(?,?,?,?,?)",
                (oid, p["name"], p["price"], int(i["qty"]), i.get("note", "")), commit=True)
    ok, msg = do_print("cozinha", [q("SELECT * FROM orders WHERE id=?", (oid,), one=True)], mesa)
    return jsonify(id=oid, printed=ok, msg=msg)

@app.get("/api/contas")
def contas():
    res = {}
    for o in q("SELECT * FROM orders WHERE status='aberto' ORDER BY id"):
        o["items"] = q("SELECT * FROM items WHERE order_id=?", (o["id"],))
        o["total"] = sum(i["price"] * i["qty"] for i in o["items"])
        m = res.setdefault(o["mesa"], {"mesa": o["mesa"], "orders": [], "total": 0})
        m["orders"].append(o); m["total"] += o["total"]
    return jsonify(list(res.values()))

@app.post("/api/orders/<int:i>/print")
def order_print(i):
    o = q("SELECT * FROM orders WHERE id=?", (i,), one=True)
    ok, msg = do_print("cozinha", [o], o["mesa"]); return jsonify(ok=ok, msg=msg)

@app.delete("/api/orders/<int:i>")
def order_cancel(i):
    q("UPDATE orders SET status='cancelado' WHERE id=?", (i,), commit=True); return jsonify(ok=True)

@app.post("/api/contas/<mesa>/print")
def conta_print(mesa):
    os_ = q("SELECT * FROM orders WHERE mesa=? AND status='aberto'", (mesa,))
    ok, msg = do_print("conta", os_, mesa); return jsonify(ok=ok, msg=msg)

@app.post("/api/contas/<mesa>/fechar")
def conta_close(mesa):
    q("UPDATE orders SET status='pago' WHERE mesa=? AND status='aberto'", (mesa,), commit=True)
    return jsonify(ok=True)

def local_ip():
    try:
        k = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); k.connect(("8.8.8.8", 80)); ip = k.getsockname()[0]; k.close(); return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    init()
    print("=" * 50, "\n HORA DO CALDO PC rodando!\n Endereco para o app do celular: %s:%d\n NAO FECHE ESTA JANELA\n" % (local_ip(), PORT), "=" * 50)
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:%d" % PORT)).start()
    app.run(host="0.0.0.0", port=PORT, threaded=True)
