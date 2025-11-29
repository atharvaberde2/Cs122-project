from flask import Flask, request, jsonify, render_template
from transaction import Transaction
import pandas as pd
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

@app.route('/')
def home():
    return render_template('budget.html')   



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