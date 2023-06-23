import random
from pyqiwip2p import QiwiP2P

class Payments:
    def __init__(self, token, db):
        self.__db = db
        self.__qiwi = QiwiP2P(auth_key=token)

    def get_bill(self, amount, user_id, lt=60):
        comment = str(user_id) + "_" + str(random.randint(1000, 9999))
        bill = self.__qiwi.bill(amount=amount, lifetime=lt, comment=comment)
        self.__db.add_check(user_id, amount, bill.bill_id)
        return bill

    # 0 - not found in database (the user did not make a request)
    # 1 - not paid
    # 2 - OK, paid
    def check_bill(self, bill):
        check_db = self.__db.get_check(bill)
        if check_db:
            if str(self.__qiwi.check(bill_id=bill).status) == "PAID":
                self.__db.delete_check(bill)
                return 2
            else:
                return 1
        else:
            return 0






if __name__ == "__main__":
    print("This file should be run as a module")