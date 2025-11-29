class Transaction:
    def __init__(self,user, amount, income, category):
        self.user = user
        self.amount = amount
        self.income = income
        self.category = category

    def is_valid(self):
        if self.amount < 0:
            return False
        if self.income < 0:
            return False
        return True
    
    def transaction_to_csv(self, filename='transactions.csv'):
        import csv
        if self.is_valid():
            with open(filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([self.user, self.amount, self.income, self.category])
        else:
            raise ValueError("Invalid transaction data")
    @staticmethod
    def get_user_transactions(user, filename='transactions.csv'):
        import csv
        import os
        if not os.path.exists(filename):
            return []
        transactions = []
        with open(filename, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == user:
                    transactions.append({
                        'amount': float(row[1]),
                        'income': float(row[2]),
                        'category': row[3]
                    })
        return transactions
    @staticmethod
    def total_spent_by_user(user, filename='transactions.csv'):
        transactions = Transaction.get_user_transactions(user, filename)
        total = sum(t['amount'] for t in transactions)
        return total
    @staticmethod
    def total_income_by_user(user, filename='transactions.csv'):
        transactions = Transaction.get_user_transactions(user, filename)
        total = sum(t['income'] for t in transactions)
        return total
    @staticmethod
    def user_category_summary(user, filename='transactions.csv'):
        transactions = Transaction.get_user_transactions(user, filename)
        summary = {}
        for t in transactions:
            category = t['category']
            amount = t['amount']
            if category in summary:
                summary[category] += amount
            else:
                summary[category] = amount
        return summary


    
