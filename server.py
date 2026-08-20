import http.server
import socketserver
import sqlite3
import json
import os
import urllib.parse

PORT = int(os.environ.get('PORT', 8080))
DB_PATH = os.path.join(os.path.dirname(__file__), 'brain.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        # Route /admin to admin.html
        if path == '/admin' or path == '/admin/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(os.path.join(os.path.dirname(__file__), 'admin.html'), 'rb') as f:
                self.wfile.write(f.read())
            return

        # API Routes
        if path == '/api/products':
            self.handle_get_products()
            return
        elif path == '/api/customers':
            self.handle_get_customers()
            return
        elif path == '/api/orders':
            self.handle_get_orders()
            return

        # Serve static files for other requests
        super().do_GET()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except Exception:
            data = {}

        if path == '/api/products':
            self.handle_create_product(data)
        elif path == '/api/customers':
            self.handle_create_customer(data)
        elif path == '/api/orders':
            self.handle_create_order(data)
        elif path == '/api/checkout':
            self.handle_checkout(data)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_PUT(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        item_id = int(query.get('id', [0])[0])

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except Exception:
            data = {}

        if path == '/api/products':
            self.handle_update_product(item_id, data)
        elif path == '/api/customers':
            self.handle_update_customer(item_id, data)
        elif path == '/api/orders':
            self.handle_update_order(item_id, data)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        item_id = int(query.get('id', [0])[0])

        if path == '/api/products':
            self.handle_delete_product(item_id)
        elif path == '/api/customers':
            self.handle_delete_customer(item_id)
        elif path == '/api/orders':
            self.handle_delete_order(item_id)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    # --- PRODUCTS ---
    def handle_get_products(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM products ORDER BY id DESC;")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(rows)

    def handle_create_product(self, data):
        conn = get_db()
        cur = conn.cursor()
        name = data.get('name')
        p_type = data.get('type', 'service')
        price = data.get('price', 0)
        description = data.get('description', '')
        stock_quantity = data.get('stock_quantity') if p_type == 'physical' else None

        cur.execute("""
        INSERT INTO products (name, type, price, description, stock_quantity)
        VALUES (?, ?, ?, ?, ?)
        """, (name, p_type, price, description, stock_quantity))
        conn.commit()
        p_id = cur.lastrowid
        conn.close()
        self.send_json({'id': p_id, 'message': 'Product created successfully'})

    def handle_update_product(self, p_id, data):
        conn = get_db()
        cur = conn.cursor()
        name = data.get('name')
        p_type = data.get('type')
        price = data.get('price')
        description = data.get('description')
        stock_quantity = data.get('stock_quantity') if p_type == 'physical' else None

        cur.execute("""
        UPDATE products
        SET name = ?, type = ?, price = ?, description = ?, stock_quantity = ?
        WHERE id = ?
        """, (name, p_type, price, description, stock_quantity, p_id))
        conn.commit()
        conn.close()
        self.send_json({'message': 'Product updated successfully'})

    def handle_delete_product(self, p_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = ?", (p_id,))
        conn.commit()
        conn.close()
        self.send_json({'message': 'Product deleted successfully'})

    # --- CUSTOMERS ---
    def handle_get_customers(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers ORDER BY id DESC;")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(rows)

    def handle_create_customer(self, data):
        conn = get_db()
        cur = conn.cursor()
        name = data.get('name')
        phone = data.get('phone')
        zalo = data.get('zalo', phone)

        cur.execute("""
        INSERT INTO customers (name, phone, zalo)
        VALUES (?, ?, ?)
        """, (name, phone, zalo))
        conn.commit()
        c_id = cur.lastrowid
        conn.close()
        self.send_json({'id': c_id, 'message': 'Customer created successfully'})

    def handle_update_customer(self, c_id, data):
        conn = get_db()
        cur = conn.cursor()
        name = data.get('name')
        phone = data.get('phone')
        zalo = data.get('zalo')

        cur.execute("""
        UPDATE customers
        SET name = ?, phone = ?, zalo = ?
        WHERE id = ?
        """, (name, phone, zalo, c_id))
        conn.commit()
        conn.close()
        self.send_json({'message': 'Customer updated successfully'})

    def handle_delete_customer(self, c_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE id = ?", (c_id,))
        conn.commit()
        conn.close()
        self.send_json({'message': 'Customer deleted successfully'})

    # --- ORDERS (WITH AUTOMATIC STOCK DEDUCTION FOR PHYSICAL PRODUCTS) ---
    def handle_get_orders(self):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        SELECT 
            o.id, o.customer_id, o.product_id, o.amount, o.status, o.created_at,
            c.name as customer_name, c.phone as customer_phone,
            p.name as product_name, p.type as product_type
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        LEFT JOIN products p ON o.product_id = p.id
        ORDER BY o.id DESC;
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        self.send_json(rows)

    def handle_create_order(self, data):
        conn = get_db()
        cur = conn.cursor()
        customer_id = data.get('customer_id')
        product_id = data.get('product_id')
        amount = data.get('amount')
        status = data.get('status', 'paid')

        # 1. Fetch product to check type & stock
        cur.execute("SELECT type, stock_quantity FROM products WHERE id = ?", (product_id,))
        p_row = cur.fetchone()

        if not p_row:
            conn.close()
            self.send_json({'error': 'Product not found'}, 400)
            return

        p_type = p_row['type']
        stock_qty = p_row['stock_quantity']

        # 2. Insert order
        cur.execute("""
        INSERT INTO orders (customer_id, product_id, amount, status)
        VALUES (?, ?, ?, ?)
        """, (customer_id, product_id, amount, status))
        order_id = cur.lastrowid

        # 3. Deduct stock ONLY IF product is physical
        stock_deducted = False
        if p_type == 'physical':
            curr_stock = stock_qty if stock_qty is not None else 0
            new_stock = max(0, curr_stock - 1)
            cur.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (new_stock, product_id))
            stock_deducted = True

        conn.commit()
        conn.close()

        self.send_json({
            'id': order_id,
            'message': 'Order created successfully',
            'product_type': p_type,
            'stock_deducted': stock_deducted
        })

    def handle_checkout(self, data):
        conn = get_db()
        cur = conn.cursor()
        name = str(data.get('name', '')).strip()
        phone = str(data.get('phone', '')).strip()
        zalo = str(data.get('zalo', phone)).strip()
        product_id = int(data.get('product_id', 1))
        amount = float(data.get('amount', 0))

        if not name or not phone:
            conn.close()
            self.send_json({'error': 'Vui lòng nhập đầy đủ họ tên và số điện thoại!'}, 400)
            return

        # 1. Check or insert customer
        cur.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
        c_row = cur.fetchone()
        if c_row:
            customer_id = c_row['id']
            cur.execute("UPDATE customers SET name = ?, zalo = ? WHERE id = ?", (name, zalo, customer_id))
        else:
            cur.execute("INSERT INTO customers (name, phone, zalo) VALUES (?, ?, ?)", (name, phone, zalo))
            customer_id = cur.lastrowid

        # 2. Query product details
        cur.execute("SELECT name, type, price, stock_quantity FROM products WHERE id = ?", (product_id,))
        p_row = cur.fetchone()
        p_name = p_row['name'] if p_row else 'Khóa học Trị Liệu Y Cơ'
        p_type = p_row['type'] if p_row else 'service'

        if amount <= 0 and p_row:
            amount = float(p_row['price'])

        # 3. Insert order
        cur.execute("""
        INSERT INTO orders (customer_id, product_id, amount, status)
        VALUES (?, ?, ?, 'pending')
        """, (customer_id, product_id, amount))
        order_id = cur.lastrowid

        # 4. Deduct stock ONLY IF physical product
        if p_type == 'physical' and p_row:
            curr_stock = p_row['stock_quantity'] if p_row['stock_quantity'] is not None else 0
            new_stock = max(0, curr_stock - 1)
            cur.execute("UPDATE products SET stock_quantity = ? WHERE id = ?", (new_stock, product_id))

        conn.commit()
        conn.close()

        des_code = f"DH{order_id}"

        self.send_json({
            'success': True,
            'order_id': order_id,
            'customer_id': customer_id,
            'customer_name': name,
            'customer_phone': phone,
            'product_name': p_name,
            'amount': amount,
            'des_code': des_code,
            'bank_acc': '8869866617',
            'bank_name': 'BIDV'
        })

    def handle_update_order(self, o_id, data):
        conn = get_db()
        cur = conn.cursor()
        customer_id = data.get('customer_id')
        product_id = data.get('product_id')
        amount = data.get('amount')
        status = data.get('status')

        cur.execute("""
        UPDATE orders
        SET customer_id = ?, product_id = ?, amount = ?, status = ?
        WHERE id = ?
        """, (customer_id, product_id, amount, status, o_id))
        conn.commit()
        conn.close()
        self.send_json({'message': 'Order updated successfully'})

    def handle_delete_order(self, o_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE id = ?", (o_id,))
        conn.commit()
        conn.close()
        self.send_json({'message': 'Order deleted successfully'})

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"Admin Server running at http://localhost:{PORT}/admin")
        httpd.serve_forever()
