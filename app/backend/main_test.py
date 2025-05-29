from sqlmodel import SQLModel
from db.db import init_db, get_session
import numpy as np

from services.user_manager import UserManager
from services.data_manager import DataManager

def main():
    init_db()

    with next(get_session()) as session:
        user_mgr = UserManager(session)

        try:
            df = np.load('data/test.npy')
            print('DataManager: loaded rows =', len(df))
        except FileNotFoundError:
            print('DataManager: sample.csv not found, пропускаем')

        user = user_mgr.register('alice', 'password123')
        print('Registered:', user.username, 'status=', user.status)

        auth = user_mgr.authenticate('alice', 'password123')
        print('Authenticated OK:', bool(auth))

        print('Balance before:', user.balance)
        user_mgr.balance.deposit(user, 150.0)
        print('After deposit:', user.balance)
        try:
            user_mgr.balance.withdraw(user, 50.0)
        except Exception as e:
            print('Withdraw error:', e)
        print('After withdraw:', user.balance)

        pred = user_mgr.prediction.run_prediction(
            user,
            selected_model='lstm',
            selected_city='NewYork',
            cost=20.0,
            sequence=df,
        )
        print('Prediction created id=', pred.id, 'status=', pred.status)

        print('Final balance:', user.balance)
        print('All predictions:', [p.id for p in user_mgr.prediction.list_by_user(user)])


if __name__ == '__main__':
    main()
