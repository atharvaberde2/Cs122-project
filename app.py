from flask import Flask, request, jsonify, render_template
from transaction import Transaction
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

df = pd.read_csv('customer_data.csv')
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['gender'] = le.fit_transform(df['gender'])
df['country'] = le.fit_transform(df['country'])
df['education'] = le.fit_transform(df['education'])
df = df.drop(columns = 'name')
df= df.drop(columns = 'country')
X = df.drop(columns = 'spending')
Y = df['spending']
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, Y, test_size=0.2, random_state=42
)
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor(
    n_estimators=300,
    max_depth=10,
    random_state=42
)

rf.fit(X_train, y_train)

TRANSACTION_FILE = "transactions.csv"
COLS = ["username", "income", "expense", "category"]

def load_transactions():
    try:
        return pd.read_csv(TRANSACTION_FILE, header=None, names=COLS)
    except FileNotFoundError:
        return pd.DataFrame(columns=COLS)

def save_transactions(df):
    df.to_csv(TRANSACTION_FILE, index=False, header=False)

def make_user_category_expense_plot(username, category):
    df = load_transactions()
    mask = (df["username"] == username) & (df["expense"] > 0)
    df_u = df[mask].copy()
    if df_u.empty:
        return None

    df_u = df_u.reset_index(drop=True)
    df_u["tx_index"] = df_u.index + 1
    df_u["cumulative_expense"] = df_u["expense"].cumsum()

    plt.figure()
    plt.plot(df_u["tx_index"], df_u["cumulative_expense"], marker="o")
    plt.title(f"{username}'s cumulative expenses")
    plt.xlabel("Transaction #")
    plt.ylabel("Total expenses")

    os.makedirs("static/plots", exist_ok=True)
    safe_user = username.replace(" ", "_")
    rel_name = f"plots/{safe_user}_expenses.png"
    full_path = os.path.join("static", rel_name)
    plt.savefig(full_path, bbox_inches="tight")
    plt.close()
    return rel_name

@app.route('/', methods=["GET", "POST"])
def home():
    df_all = load_transactions()
    plot_filename = None
    selected_user = None
    selected_category = None

    if "username" in request.form:
        username = request.form["username"]
        amount = float(request.form["amount"])
        ttype = request.form["type"]  # "Income" or "Expense"
        category = request.form["category"]

        # save transaction if Add Transaction form was used
        if username and amount and category and ttype:
            try:
                amount = float(amount)
            except ValueError:
                amount = 0.0

            income = amount if ttype == "Income" else 0.0
            expense = amount if ttype == "Expense" else 0.0

            new_row = pd.DataFrame([{
                "username": username,
                "income": income,
                "expense": expense,
                "category": category,
            }])

            df_all = pd.concat([df_all, new_row], ignore_index=True)
            save_transactions(df_all)

            if ttype == "Expense":
                selected_user = username
                selected_category = category
                plot_filename = make_user_category_expense_plot(username, category)

    total_income = float(df_all["income"].sum()) if not df_all.empty else 0.0
    total_expenses = float(df_all["expense"].sum()) if not df_all.empty else 0.0
    predicted_spending = 0.0

    return render_template(
        "budget.html",
        plot_filename=plot_filename,
        selected_user=selected_user,
        selected_category=selected_category,
        total_income=total_income,
        total_expenses=total_expenses,
        predicted_spending=predicted_spending,
    )

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    input_data = [        
        data['age'],           
        1 if data['gender'] == "Male" else 0, 
        2 if data['education'] == "PHD" else 1 if data['education'] == "Master" else 0 if data['education'] == "Bachelor" else 3,    
        data['income'], 
        data['frequency']      
]
    input_df = pd.DataFrame([input_data], columns=[        
        'age',
        'gender',
        'education', 
        'income',
        'purchase_frequency']
    )
    prediction = rf.predict(input_df)[0]
    return jsonify({'predicted_spending': round(prediction, 2)})

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    try:
        data = request.json
        amount = float(data['amount'])
        category = data['category']
        ttype = data['type']
        if ttype.lower() == 'income':
            income = amount
            amount = 0  
        else:
            income = 0

        tr = Transaction(data['name'], amount, income, category)
        tr.transaction_to_csv()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400      


@app.route('/transaction_summary', methods=['POST'])
def transaction_summary():
    data = request.json
    user = data['name']
    total_spent = Transaction.total_spent_by_user(user)
    total_income = Transaction.total_income_by_user(user)
    category_summary = Transaction.user_category_summary(user)
    return jsonify({
        'total_spent': total_spent,
        'total_income': total_income,
        'category_summary': category_summary
    })

if __name__ == '__main__':
    app.run(debug=True)