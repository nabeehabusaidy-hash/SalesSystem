import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'salesystem2025'

USERNAME = 'admin'
PASSWORD = 'admin123'

def get_db():
    conn = sqlite3.connect('sales.db')
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Wrong username or password. Try again!'
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM sales')
    total_sales = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM customers')
    total_customers = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM products')
    total_products = c.fetchone()[0]
    c.execute('SELECT SUM(total_amount) FROM sales')
    total_revenue = c.fetchone()[0] or 0
    c.execute('SELECT sales.id, customers.name, products.name, sales.quantity, sales.total_amount, sales.date FROM sales JOIN customers ON sales.customer_id = customers.id JOIN products ON sales.product_id = products.id ORDER BY sales.id DESC LIMIT 5')
    recent_sales = c.fetchall()
    conn.close()
    return render_template('dashboard.html', total_sales=total_sales, total_customers=total_customers, total_products=total_products, total_revenue=total_revenue, recent_sales=recent_sales)

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    success = None
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        c.execute('INSERT INTO customers (name, phone, email, address) VALUES (?,?,?,?)',
                  (name, phone, email, address))
        conn.commit()
        success = 'Customer added successfully!'
    c.execute('SELECT * FROM customers')
    all_customers = c.fetchall()
    conn.close()
    return render_template('customers.html', customers=all_customers, success=success)

@app.route('/delete_customer/<int:id>')
def delete_customer(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM customers WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('customers'))
@app.route('/products', methods=['GET', 'POST'])
def products():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    success = None
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        quantity = request.form['quantity']
        c.execute('INSERT INTO products (name, description, price, quantity) VALUES (?,?,?,?)',
                  (name, description, price, quantity))
        conn.commit()
        success = 'Product added successfully!'
    c.execute('SELECT * FROM products')
    all_products = c.fetchall()
    conn.close()
    return render_template('products.html', products=all_products, success=success)

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('products'))
@app.route('/sales', methods=['GET', 'POST'])
def sales():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    success = None
    error = None
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])
        c.execute('SELECT price, quantity FROM products WHERE id=?', (product_id,))
        product = c.fetchone()
        if product[1] < quantity:
            error = 'Not enough stock available!'
        else:
            total_amount = product[0] * quantity
            date = datetime.now().strftime('%Y-%m-%d %H:%M')
            c.execute('INSERT INTO sales (customer_id, product_id, quantity, total_amount, date) VALUES (?,?,?,?,?)',
                      (customer_id, product_id, quantity, total_amount, date))
            c.execute('UPDATE products SET quantity = quantity - ? WHERE id=?',
                      (quantity, product_id))
            conn.commit()
            success = 'Sale recorded successfully!'
    c.execute('SELECT customers.name, products.name, sales.quantity, sales.total_amount, sales.date, sales.id FROM sales JOIN customers ON sales.customer_id = customers.id JOIN products ON sales.product_id = products.id ORDER BY sales.id DESC')
    all_sales = c.fetchall()
    formatted_sales = [(s[5], s[0], s[1], s[2], s[3], s[4]) for s in all_sales]
    c.execute('SELECT * FROM customers')
    all_customers = c.fetchall()
    c.execute('SELECT * FROM products')
    all_products = c.fetchall()
    conn.close()
    return render_template('sales.html', sales=formatted_sales, customers=all_customers, products=all_products, success=success, error=error)

@app.route('/reports')
def reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM sales')
    total_sales = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM customers')
    total_customers = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM products')
    total_products = c.fetchone()[0]
    c.execute('SELECT SUM(total_amount) FROM sales')
    total_revenue = c.fetchone()[0] or 0
    c.execute('SELECT products.name, SUM(sales.quantity), SUM(sales.total_amount) FROM sales JOIN products ON sales.product_id = products.id GROUP BY products.name ORDER BY SUM(sales.quantity) DESC')
    best_products = c.fetchall()
    c.execute('SELECT customers.name, COUNT(sales.id), SUM(sales.total_amount) FROM sales JOIN customers ON sales.customer_id = customers.id GROUP BY customers.name ORDER BY SUM(sales.total_amount) DESC')
    top_customers = c.fetchall()
    c.execute('SELECT sales.id, customers.name, products.name, sales.quantity, sales.total_amount, sales.date FROM sales JOIN customers ON sales.customer_id = customers.id JOIN products ON sales.product_id = products.id ORDER BY sales.id DESC')
    all_sales = c.fetchall()
    conn.close()
    return render_template('reports.html', total_sales=total_sales, total_customers=total_customers, total_products=total_products, total_revenue=total_revenue, best_products=best_products, top_customers=top_customers, all_sales=all_sales)

@app.route('/invoice/<int:id>')
def invoice(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT sales.id, customers.name, products.name, sales.quantity, sales.total_amount, sales.date FROM sales JOIN customers ON sales.customer_id = customers.id JOIN products ON sales.product_id = products.id WHERE sales.id=?', (id,))
    sale = c.fetchone()
    conn.close()
    return render_template('invoice.html', sale=sale)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.after_request
def add_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

if __name__ == '__main__':
   app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
