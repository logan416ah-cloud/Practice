import random
import time

class Gamba:

    def __init__(self):
        self.balance = 0 

    def deposit(self):
        while True:
            try:
                amount = int(input("What would you like to deposit? $"))
                if amount <= 0:
                    print("Please enter a whole greater number than 0.")
                    continue
                self.balance += amount
                print(f"Deposited {amount}. New balance {self.balance}")
                return amount
            except ValueError:
                print("Please enter a vilid whole number.")

    def roll_dice():
        roll = [random.randint(1,6) for _ in range(5)]
        dealer_roll = [random.randint(1,6) for _ in range(5)]
     

        print(f"DEALER'S ROLL:  {dealer_roll}")
        print(f"DEALER'S TOTAL: {sum(dealer_roll)}")
        
        print(f"YOUR ROLL:  {roll}")
        print(f"YOUR TOTAL: {sum(roll)}")

        print("CHOOSE ONE\n")
        print("(1) Roll Again")
        print("(2) Stay\n")
        
        while True:
            try:
                user_choice = int(input("Enter Choice: "))
                if user_choice not in (1, 2):
                    print("Enter 1 or 2.")
                    continue
                break
            except ValueError:
                print("Enter a valid number (1 or 2).")

        # PLAYER'S TURN ---------------------------------------------------
        total = sum(roll)
        if user_choice == 1:
            while True:
                roll.append(random.randint(1,6))
                total = sum(roll)
                print(f"\nYou rolled again: {roll}")
                print(f"NEW TOTAL = {total}")

                if total > 30:
                    print("YOU BUSTED! Dealer Wins.")
                    return
            
                choice2 = input("\nRoll Again? (yes/no)").lower()
                if choice2 != 'yes':
                    print("\nYou stayed")
                    print(f"FINAL COUNT = {total}")
                    break
        
        if user_choice == 2:
            print("\nYou stayed")
            print(f"FINAL COUNT = {total}")
        
        # DEALER'S TURN ---------------------------------------------------
        print("DEALER'S TURN...")

        dealer_total = sum(dealer_roll)

        print(f"Dealer starts with {dealer_roll}, for a total of {dealer_total}.")

        while dealer_total < total and dealer_total <= 30:
            for _ in range(3):
                print("Rolling.....")
                time.sleep(0.7)

            dealer_roll.append(random.randint(1,6))
            dealer_total = sum(dealer_roll)

            print(f"NEW DEALER ROLL: {dealer_roll}")
            print(f"NEW DEALER TOTAL = {dealer_total}")

            if dealer_total > 30:
                print("DEALER BUSTED! You Win!")
                return
            
        if dealer_total > total:
            print("DEALER WINS!")
        elif dealer_total == total:
            print("\nTIE! Nobody wins.")
        else:
            print("\nYOU WIN!")


    
Gamba.roll_dice()