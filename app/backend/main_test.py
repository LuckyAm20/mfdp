import time

from workers.publisher import publish_prediction_task
from db.db import init_db, get_session

from services.user_manager import UserManager

def main():
    init_db()
    time.sleep(60)
    with next(get_session()) as session:
        user_mgr = UserManager(session)

        user = user_mgr.register('alice', 'password123')
        print('Registered:', user.username, 'status=', user.status)
        user_mgr.user = user

        auth = user_mgr.authenticate('alice', 'password123')
        print('Authenticated OK:', bool(auth))

        print('Balance before:', user_mgr.user.balance)
        user_mgr.balance.deposit(150.0)
        print('After deposit:', user_mgr.user.balance)
        try:
            user_mgr.balance.withdraw(50.0)
        except Exception as e:
            print('Withdraw error:', e)
        print('After withdraw:', user_mgr.user.balance)

        pred = publish_prediction_task(user_mgr.user.id, 'lstm', 'NYC', 10, 1, 1)
        print('Prediction created id=', pred.id, 'status=', pred.status)

        print('Final balance:', user_mgr.user.balance)
        print('All predictions:', [p for p in user_mgr.prediction.list_by_user()])


if __name__ == '__main__':
    main()
