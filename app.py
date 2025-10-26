from flask import Flask, request, render_template, send_file, redirect, url_for
from jinja2 import DictLoader
import json
import os
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)


ACCOUNTS_FILE = "accounts.json"
TRANSACTIONS_FILE = "transactions.json"


def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4, default=str)


accounts = load_json(ACCOUNTS_FILE)  
transactions = load_json(TRANSACTIONS_FILE)  

if not isinstance(accounts, dict):
    accounts = {}
if not isinstance(transactions, dict):
    transactions = {}

CATEGORIES = ["Salary", "Rent", "Groceries", "Utilities", "Transport", "Fees", "Entertainment", "Other"]


class Transaction:
    def __init__(self, type_, amount, details="", category="Other", date=None, id=None):
        self.type = type_
        self.amount = amount
        self.details = details
        self.category = category
        
        self.date = date if date else datetime.utcnow().isoformat()
        self.id = id if id else str(uuid.uuid4())

    def to_dict(self):
        return {
            "type": self.type,
            "amount": self.amount,
            "details": self.details,
            "category": self.category,
            "date": self.date,
            "id": self.id
        }


for acc, tlist in list(transactions.items()):
    new_list = []
    for t in tlist:
        
        if "type_" in t and "type" not in t:
            t["type"] = t.pop("type_")
        
        t.setdefault("details", "")
        t.setdefault("category", "Other")
        t.setdefault("date", datetime.utcnow().isoformat())
        t.setdefault("id", str(uuid.uuid4()))
    
        try:
            t["amount"] = int(t["amount"])
        except Exception:
            try:
                t["amount"] = int(float(t["amount"]))
            except Exception:
                t["amount"] = 0
        new_list.append(t)
    transactions[acc] = new_list


def persist_transactions():
    save_json(TRANSACTIONS_FILE, transactions)

def persist_accounts():
    save_json(ACCOUNTS_FILE, accounts)


template_dict = {
    "base.html": """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Byte Bank - Finance</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  <style>
    body{font-family:Arial,Helvetica,sans-serif;background:#f7f9fb;margin:0;padding:0}
    .container{width:90%;max-width:1100px;margin:30px auto;background:#fff;padding:20px;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.06)}
    nav a{margin-right:10px;text-decoration:none;color:#1a73e8}
    table{width:100%;border-collapse:collapse;margin-top:10px}
    th,td{padding:8px;border:1px solid #e6e9ee;text-align:left}
    th{background:#1a73e8;color:#fff}
    .success{color:green}.error{color:red}
    input,select,button{padding:6px;margin:6px 0}
    .row{display:flex;gap:12px;flex-wrap:wrap}
    .col{flex:1;min-width:160px}
    .small{width:120px}
  </style>
</head>
<body>
  <div class="container">
    <h1>Byte Bank — Personal Finance</h1>
    <nav>
      <a href="{{ url_for('index') }}">Home</a> |
      <a href="{{ url_for('create_account') }}">Create Account</a> |
      <a href="{{ url_for('deposit') }}">Deposit</a> |
      <a href="{{ url_for('withdraw') }}">Withdraw</a> |
      <a href="{{ url_for('transfer') }}">Transfer</a> |
      <a href="{{ url_for('expenses') }}">Expenses</a> |
      <a href="{{ url_for('list_accounts') }}">Accounts</a> |
      <a href="{{ url_for('reports') }}">Reports</a> |
      <a href="{{ url_for('export_json') }}">Export JSON</a>
    </nav>
    <hr>
    {% block content %}{% endblock %}
  </div>
  <!-- Chart.js from CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
""",
    "index.html": """
{% extends "base.html" %}
{% block content %}
<h2>Welcome</h2>
<p>Manage accounts, expenses, categories, filters and view reports.</p>
{% endblock %}
""",
    "create_account.html": """
{% extends "base.html" %}
{% block content %}
<h2>Create Account</h2>
<form method="post">
  <input name="name" placeholder="Account name" required>
  <button type="submit">Create</button>
</form>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}
{% endblock %}
""",
    "list_accounts.html": """
{% extends "base.html" %}
{% block content %}
<h2>Accounts</h2>
{% if accounts %}
<table>
  <tr><th>Name</th><th>Balance</th><th>Transactions</th></tr>
  {% for name, balance in accounts.items() %}
  <tr>
    <td>{{ name }}</td>
    <td>{{ balance }}</td>
    <td><a href="{{ url_for('view_transactions', account=name) }}">View</a></td>
  </tr>
  {% endfor %}
</table>
{% else %}
<p>No accounts yet.</p>
{% endif %}
{% endblock %}
""",
    "deposit.html": """
{% extends "base.html" %}
{% block content %}
<h2>Deposit</h2>
<form method="post">
  <select name="account" required>
    {% for n in accounts %}<option value="{{ n }}">{{ n }}</option>{% endfor %}
  </select>
  <input name="amount" type="number" min="1" placeholder="Amount" required>
  <button type="submit">Deposit</button>
</form>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}
{% endblock %}
""",
    "withdraw.html": """
{% extends "base.html" %}
{% block content %}
<h2>Withdraw</h2>
<form method="post">
  <select name="account" required>
    {% for n in accounts %}<option value="{{ n }}">{{ n }}</option>{% endfor %}
  </select>
  <input name="amount" type="number" min="1" placeholder="Amount" required>
  <button type="submit">Withdraw</button>
</form>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}
{% endblock %}
""",
    "transfer.html": """
{% extends "base.html" %}
{% block content %}
<h2>Transfer</h2>
<form method="post">
  <select name="from_account" required>
    {% for n in accounts %}<option value="{{ n }}">{{ n }}</option>{% endfor %}
  </select>
  <select name="to_account" required>
    {% for n in accounts %}<option value="{{ n }}">{{ n }}</option>{% endfor %}
  </select>
  <input name="amount" type="number" min="1" placeholder="Amount" required>
  <button type="submit">Transfer</button>
</form>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}
{% endblock %}
""",
    "expenses.html": """
{% extends "base.html" %}
{% block content %}
<h2>Expenses / Add / Filter / Manage</h2>

<!-- Add Expense -->
<h3>Add Expense</h3>
<form method="post" action="{{ url_for('expenses') }}">
  <div class="row">
    <div class="col">
      <select name="account" required>
        {% for n in accounts %}<option value="{{ n }}">{{ n }}</option>{% endfor %}
      </select>
    </div>
    <div class="col">
      <input name="details" placeholder="Description (e.g. Rent)" required>
    </div>
    <div class="col">
      <select name="category">
        {% for c in categories %}<option value="{{ c }}">{{ c }}</option>{% endfor %}
      </select>
    </div>
    <div class="col small">
      <input name="amount" type="number" min="1" placeholder="Amount" required>
    </div>
    <div class="col small">
      <button type="submit">Add Expense</button>
    </div>
  </div>
</form>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}

<hr>

<!-- Filter -->
<h3>Filter Expenses</h3>
<form method="get" action="{{ url_for('expenses') }}">
  <div class="row">
    <div class="col">
      <select name="account_filter">
        <option value="">All Accounts</option>
        {% for n in accounts %}<option value="{{ n }}" {% if request.args.get('account_filter')==n %}selected{% endif %}>{{ n }}</option>{% endfor %}
      </select>
    </div>
    <div class="col">
      <select name="category_filter">
        <option value="">All Categories</option>
        {% for c in categories %}<option value="{{ c }}" {% if request.args.get('category_filter')==c %}selected{% endif %}>{{ c }}</option>{% endfor %}
      </select>
    </div>
    <div class="col">
      <input type="date" name="date_from" value="{{ request.args.get('date_from','') }}">
    </div>
    <div class="col">
      <input type="date" name="date_to" value="{{ request.args.get('date_to','') }}">
    </div>
    <div class="col small">
      <button type="submit">Apply</button>
    </div>
  </div>
</form>

<!-- Expense List -->
<h3>Expense Transactions</h3>
{% if filtered %}
<table>
  <tr><th>Date</th><th>Account</th><th>Type</th><th>Category</th><th>Amount</th><th>Details</th><th>Actions</th></tr>
  {% for t in filtered %}
  <tr>
    <td>{{ t.date.split('T')[0] }}</td>
    <td>{{ t.account }}</td>
    <td>{{ t.type }}</td>
    <td>{{ t.category }}</td>
    <td>{{ t.amount }}</td>
    <td>{{ t.details }}</td>
    <td>
      <a href="{{ url_for('edit_expense', account=t.account, txid=t.id) }}">Edit</a> |
      <form style="display:inline" method="post" action="{{ url_for('delete_expense', account=t.account, txid=t.id) }}">
        <button type="submit" onclick="return confirm('Delete this expense?')">Delete</button>
      </form>
    </td>
  </tr>
  {% endfor %}
</table>
{% else %}
<p>No transactions match the filter.</p>
{% endif %}
{% endblock %}
""",
    "edit_expense.html": """
{% extends "base.html" %}
{% block content %}
<h2>Edit Expense</h2>
<form method="post">
  <div class="row">
    <div class="col">
      <label>Account</label>
      <select name="account" required>
        {% for n in accounts %}
          <option value="{{ n }}" {% if n==tx.account %}selected{% endif %}>{{ n }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="col">
      <label>Details</label>
      <input name="details" value="{{ tx.details }}" required>
    </div>
    <div class="col">
      <label>Category</label>
      <select name="category">
        {% for c in categories %}
          <option value="{{ c }}" {% if c==tx.category %}selected{% endif %}>{{ c }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="col small">
      <label>Amount</label>
      <input name="amount" type="number" min="1" value="{{ tx.amount }}" required>
    </div>
    <div class="col small">
      <label>&nbsp;</label><br>
      <button type="submit">Save</button>
    </div>
  </div>
</form>
{% if message %}<p class="{{ 'error' if error else 'success' }}">{{ message }}</p>{% endif %}
{% endblock %}
""",
    "transactions.html": """
{% extends "base.html" %}
{% block content %}
<h2>Transactions for {{ account }}</h2>
{% if txs %}
<table>
  <tr><th>Date</th><th>Type</th><th>Category</th><th>Amount</th><th>Details</th></tr>
  {% for t in txs %}
  <tr>
    <td>{{ t.date.split('T')[0] }}</td>
    <td>{{ t.type }}</td>
    <td>{{ t.category }}</td>
    <td>{{ t.amount }}</td>
    <td>{{ t.details }}</td>
  </tr>
  {% endfor %}
</table>
{% else %}
<p>No transactions yet.</p>
{% endif %}
{% endblock %}
""",
    "reports.html": """
{% extends "base.html" %}
{% block content %}
<h2>Reports</h2>

<h3>Monthly Income vs Expense (last 12 months)</h3>
<canvas id="barChart" width="800" height="300"></canvas>

<h3>Expense Category Breakdown (last 12 months)</h3>
<canvas id="pieChart" width="400" height="300"></canvas>

<hr>
<h3>Summary Table (last 12 months)</h3>
<table>
  <tr><th>Month</th><th>Income</th><th>Expense</th><th>Net</th></tr>
  {% for row in summary_table %}
    <tr>
      <td>{{ row.month }}</td>
      <td>{{ row.income }}</td>
      <td>{{ row.expense }}</td>
      <td>{{ row.net }}</td>
    </tr>
  {% endfor %}
</table>

<script>
  // Bar chart
  const ctx = document.getElementById('barChart').getContext('2d');
  const labels = {{ labels | safe }};
  const incomeData = {{ income_data | safe }};
  const expenseData = {{ expense_data | safe }};
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'Income', data: incomeData, backgroundColor: 'rgba(0,123,255,0.6)' },
        { label: 'Expense', data: expenseData, backgroundColor: 'rgba(220,53,69,0.6)' }
      ]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } }
    }
  });

  // Pie chart
  const pctx = document.getElementById('pieChart').getContext('2d');
  const catLabels = {{ cat_labels | safe }};
  const catValues = {{ cat_values | safe }};
  new Chart(pctx, {
    type: 'pie',
    data: {
      labels: catLabels,
      datasets: [{ data: catValues }]
    },
    options: { responsive: true }
  });
</script>
{% endblock %}
"""
}

app.jinja_loader = DictLoader(template_dict)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    message = ""
    error = False
    if request.method == "POST":
        name = request.form["name"].strip()
        if not name:
            message = "Name required."
            error = True
        elif name in accounts:
            message = "Account already exists."
            error = True
        else:
            accounts[name] = 0
            transactions[name] = []
            persist_accounts()
            persist_transactions()
            message = f"Account '{name}' created."
    return render_template("create_account.html", message=message, error=error)

@app.route("/accounts")
def list_accounts():
    return render_template("list_accounts.html", accounts=accounts)

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    message = ""
    error = False
    if request.method == "POST":
        acc = request.form["account"]
        try:
            amount = int(request.form["amount"])
        except:
            amount = 0
        if acc not in accounts:
            message = "Invalid account."
            error = True
        else:
            accounts[acc] += amount
            persist_accounts()
            
            t = Transaction("Deposit", amount, details="Deposit", category="Salary" if amount>0 else "Other")
            transactions.setdefault(acc, []).append(t.to_dict())
            persist_transactions()
            message = f"Deposited {amount} bytes to {acc}."
    return render_template("deposit.html", accounts=accounts, message=message, error=error)

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    message = ""
    error = False
    if request.method == "POST":
        acc = request.form["account"]
        try:
            amount = int(request.form["amount"])
        except:
            amount = 0
        if acc not in accounts:
            message = "Invalid account."
            error = True
        elif accounts[acc] < amount:
            message = "Insufficient funds."
            error = True
        else:
            accounts[acc] -= amount
            persist_accounts()
            t = Transaction("Withdraw", amount, details="Withdraw", category="Other")
            transactions.setdefault(acc, []).append(t.to_dict())
            persist_transactions()
            message = f"Withdrew {amount} bytes from {acc}."
    return render_template("withdraw.html", accounts=accounts, message=message, error=error)

@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    message = ""
    error = False
    if request.method == "POST":
        from_acc = request.form["from_account"]
        to_acc = request.form["to_account"]
        try:
            amount = int(request.form["amount"])
        except:
            amount = 0
        if from_acc == to_acc:
            message = "Cannot transfer to the same account."
            error = True
        elif from_acc not in accounts or to_acc not in accounts:
            message = "Invalid accounts."
            error = True
        elif accounts[from_acc] < amount:
            message = "Insufficient balance."
            error = True
        else:
            accounts[from_acc] -= amount
            accounts[to_acc] += amount
            persist_accounts()
            transactions.setdefault(from_acc, []).append(Transaction("Transfer Out", amount, details=f"To {to_acc}", category="Other").to_dict())
            transactions.setdefault(to_acc, []).append(Transaction("Transfer In", amount, details=f"From {from_acc}", category="Other").to_dict())
            persist_transactions()
            message = f"Transferred {amount} bytes from {from_acc} to {to_acc}."
    return render_template("transfer.html", accounts=accounts, message=message, error=error)


@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    message = ""
    error = False

    
    if request.method == "POST":
        acc = request.form.get("account")
        details = request.form.get("details", "").strip()
        category = request.form.get("category", "Other")
        try:
            amount = int(request.form.get("amount", "0"))
        except:
            amount = 0

        if acc not in accounts:
            message = "Invalid account."
            error = True
        elif amount <= 0:
            message = "Enter a valid amount."
            error = True
        elif accounts[acc] < amount:
            message = "Insufficient balance for this expense."
            error = True
        else:
            accounts[acc] -= amount
            persist_accounts()
            t = Transaction("Expense", amount, details=details, category=category)
            transactions.setdefault(acc, []).append(t.to_dict())
            persist_transactions()
            message = f"Expense '{details}' of {amount} recorded for {acc}."

    
    account_filter = request.args.get("account_filter", "")
    category_filter = request.args.get("category_filter", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    
    all_tx = []
    for acc, tlist in transactions.items():
        for t in tlist:
            tx = dict(t)  
            tx.setdefault("account", acc)
            all_tx.append(tx)

    
    filtered = []
    for tx in sorted(all_tx, key=lambda x: x.get("date",""), reverse=True):
        
        if account_filter and tx.get("account") != account_filter:
            continue
        if category_filter and tx.get("category") != category_filter:
            continue
        if date_from:
            try:
                if tx.get("date","")[:10] < date_from:
                    continue
            except:
                pass
        if date_to:
            try:
                if tx.get("date","")[:10] > date_to:
                    continue
            except:
                pass
        filtered.append(tx)

    
    if not (account_filter or category_filter or date_from or date_to):
        filtered = filtered[:200]

    return render_template("expenses.html",
                           accounts=accounts,
                           categories=CATEGORIES,
                           filtered=filtered,
                           message=message,
                           error=error,
                           request=request)


@app.route("/expenses/edit/<account>/<txid>", methods=["GET", "POST"])
def edit_expense(account, txid):
    if account not in transactions:
        return "Account not found", 404

    tx = next((t for t in transactions[account] if t.get("id") == txid), None)
    if not tx:
        return "Transaction not found", 404

    message = ""
    error = False
    if request.method == "POST":
        
        prev_amount = int(tx.get("amount", 0))
        prev_account = account

        new_account = request.form.get("account")
        new_details = request.form.get("details", "").strip()
        new_category = request.form.get("category", "Other")
        try:
            new_amount = int(request.form.get("amount", "0"))
        except:
            new_amount = 0

        
        if new_account not in accounts:
            message = "Invalid account selected."
            error = True
        elif new_amount <= 0:
            message = "Amount must be positive."
            error = True
        else:
            
            
            accounts[prev_account] += prev_amount
            
            if accounts[new_account] < new_amount:
                
                accounts[prev_account] -= prev_amount
                message = "Insufficient balance in the selected account for updated amount."
                error = True
            else:
                accounts[new_account] -= new_amount
                persist_accounts()

                
                tx.update({
                    "amount": new_amount,
                    "details": new_details,
                    "category": new_category,
                    "date": datetime.utcnow().isoformat()
                })
            
                if new_account != prev_account:
                    
                    transactions[prev_account] = [t for t in transactions[prev_account] if t.get("id") != txid]
                    transactions.setdefault(new_account, []).append(tx)
                persist_transactions()
                message = "Expense updated."
    
    tx_for_template = dict(tx)
    tx_for_template["account"] = account
    return render_template("edit_expense.html", accounts=accounts, categories=CATEGORIES, tx=tx_for_template, message=message, error=error)


@app.route("/expenses/delete/<account>/<txid>", methods=["POST"])
def delete_expense(account, txid):
    if account not in transactions:
        return "Account not found", 404
    tx = next((t for t in transactions[account] if t.get("id") == txid), None)
    if not tx:
        return "Transaction not found", 404
    
    try:
        amount = int(tx.get("amount", 0))
    except:
        amount = 0

    if tx.get("type") in ["Expense", "Withdraw", "Transfer Out"]:
        accounts.setdefault(account, 0)
        accounts[account] += amount
        persist_accounts()
    
    transactions[account] = [t for t in transactions[account] if t.get("id") != txid]
    persist_transactions()
    return redirect(url_for('expenses'))

@app.route("/transactions/<account>")
def view_transactions(account):
    if account not in transactions:
        return "Account not found", 404
    txs = sorted(transactions.get(account, []), key=lambda x: x.get("date",""), reverse=True)
    return render_template("transactions.html", account=account, txs=txs)


@app.route("/reports")
def reports():
    
    now = datetime.utcnow()
    months = []
    for i in range(11, -1, -1):
        m = (now - timedelta(days=30*i)).replace(day=1)
        months.append(m.strftime("%Y-%m"))

    
    income_by_month = {m: 0 for m in months}
    expense_by_month = {m: 0 for m in months}
    category_totals = {c: 0 for c in CATEGORIES}
    category_totals["Other"] = category_totals.get("Other", 0)

    
    income_types = {"Deposit", "Transfer In"}
    expense_types = {"Expense", "Withdraw", "Transfer Out"}

    
    for acc, tlist in transactions.items():
        for t in tlist:
            try:
                tdate = t.get("date","")
                month = tdate[:7]  # YYYY-MM
                amt = int(t.get("amount", 0))
                ttype = t.get("type","")
                cat = t.get("category","Other")
            except:
                continue
            if month in months:
                if ttype in income_types:
                    income_by_month[month] += amt
                elif ttype in expense_types:
                    expense_by_month[month] += amt
                
                if ttype in expense_types:
                    category_totals.setdefault(cat, 0)
                    category_totals[cat] += amt

    labels = months
    income_data = [income_by_month[m] for m in months]
    expense_data = [expense_by_month[m] for m in months]

    
    cat_labels = []
    cat_values = []
    for cat, val in category_totals.items():
        if val > 0:
            cat_labels.append(cat)
            cat_values.append(val)


    summary_table = []
    for m in months:
        inc = income_by_month[m]
        exp = expense_by_month[m]
        summary_table.append({"month": m, "income": inc, "expense": exp, "net": inc - exp})

    return render_template("reports.html",
                           labels=json.dumps(labels),
                           income_data=json.dumps(income_data),
                           expense_data=json.dumps(expense_data),
                           cat_labels=json.dumps(cat_labels),
                           cat_values=json.dumps(cat_values),
                           summary_table=summary_table)

@app.route("/export_json")
def export_json():
    export_file = "bank_export.json"
    data = {
        "accounts": accounts,
        "transactions": transactions
    }
    save_json(export_file, data)
    return send_file(export_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
