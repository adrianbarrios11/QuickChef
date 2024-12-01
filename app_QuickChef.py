import csv
import os
import time
from queue import PriorityQueue
from dataclasses import dataclass
from typing import List
from datetime import datetime, timedelta
import json
import hashlib
import getpass
from queue import Queue


@dataclass
class Dish:
    name: str
    prep_time: int  # in minutes
    ingredients: List[str]
    type: str  # tapas or main dish


class Order:
    def __init__(self, table_number: int, dish: Dish, order_time: datetime):
        self.table_number = table_number
        self.dish = dish
        self.order_time = order_time
        self.status = "pending"
        self.priority = order_time.timestamp()
        self.estimated_completion = None

    def __lt__(self, other):
        return self.priority < other.priority


class UserAuth:
    def __init__(self):
        self.users_file = "restaurant_users.json"
        self.users = self.load_users()

    def load_users(self):
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default admin user if file doesn't exist
            default_users = {
                "admin": {"password": self.hash_password("admin123"), "role": "admin"}
            }

            with open(self.users_file, 'w') as f:
                json.dump(default_users, f, indent=4)
            return default_users

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self):
        attempts = 3
        while attempts > 0:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n=== Restaurant Management System Login ===")
            username = input("Username: ")
            password = getpass.getpass("Password: ")

            if username in self.users:
                if self.users[username]["password"] == self.hash_password(password):
                    return True, self.users[username]["role"]

            attempts -= 1
            print(f"\nInvalid credentials. {attempts} attempts remaining.")
            time.sleep(1)

        return False, ""


class KitchenQueueSystem:
    def __init__(self):
        self.tapas_queue = []  # FIFO queue for tapas
        self.main_dishes_queue = PriorityQueue()  # Priority queue for main dishes
        self.currently_cooking = []
        self.completed_orders = []
        self.menu_file = "Menu.csv"
        self.load_menu()
        self.orders = Queue()
        self.auth = UserAuth()

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def load_menu(self):
        """Load menu recipes from the CSV file."""
        self.available_dishes = []
        try:
            with open(self.menu_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    dish = Dish(
                        name=row["name"],
                        prep_time=int(row["prep_time"]),
                        ingredients=row["ingredients"].split(","),
                        type=row["type"],
                    )
                    self.available_dishes.append(dish)
        except FileNotFoundError:
            # Initialize an empty CSV if file not found
            with open(self.menu_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["name", "prep_time", "type", "ingredients"])
                writer.writeheader()

    def save_menu(self):
        """Save the current menu to the CSV file."""
        with open(self.menu_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "prep_time", "type", "ingredients"])
            writer.writeheader()
            for dish in self.available_dishes:
                writer.writerow({
                    "name": dish.name,
                    "prep_time": dish.prep_time,
                    "type": dish.type,
                    "ingredients": ",".join(dish.ingredients),
                })

    def remove_menu_item(self):
        """Remove a dish from the menu."""
        self.clear_screen()
        print("\n=== Remove Menu Item ===")

        if not self.available_dishes:
            print("No dishes available in the menu.")
            input("\nPress Enter to continue...")
            return

        print("\nAvailable Dishes:")
        for i, dish in enumerate(self.available_dishes, 1):
            print(f"{i}. {dish.name} (Type: {dish.type})")

        try:
            choice = int(input("\nEnter the number of the dish to remove: ")) - 1
            if 0 <= choice < len(self.available_dishes):
                removed_dish = self.available_dishes.pop(choice)
                self.save_menu()
                print(f"\nRemoved '{removed_dish.name}' from the menu.")
            else:
                print("Invalid dish number!")
        except ValueError:
            print("Please enter a valid number!")

        input("\nPress Enter to continue...")

    def add_new_recipe(self):
        """Add a new recipe and save it to the menu."""
        self.clear_screen()
        print("\n=== Add New Recipe ===")
        name = input("Enter the name of the dish: ").strip()
        try:
            prep_time = int(input("Enter the preparation time (in minutes): "))
        except ValueError:
            print("Invalid input. Preparation time must be an integer.")
            return

        dish_type = input("Enter the type (tapas or main dish): ").strip().lower()
        if dish_type not in ["tapas", "main dish"]:
            print("Invalid type. Must be 'tapas' or 'main dish'.")
            return

        ingredients = []
        print("\nEnter ingredients one by one. Type 'done' when finished:")
        while True:
            ingredient = input("Ingredient (type 'done' when finished): ").strip()
            if ingredient.lower() == "done":
                break
            if ingredient:
                ingredients.append(ingredient)

        if not ingredients:
            print("No ingredients provided. Recipe creation canceled.")
            return

        # Add new dish and save it
        new_dish = Dish(name=name, prep_time=prep_time, ingredients=ingredients, type=dish_type)
        self.available_dishes.append(new_dish)
        self.save_menu()
        print(f"\nNew recipe '{name}' added successfully!")

    def add_order(self):
        self.clear_screen()
        print("\n=== Add New Order ===")

        print("\nAvailable Dishes:")
        for i, dish in enumerate(self.available_dishes, 1):
            print(f"{i}. {dish.name} (Type: {dish.type}, Prep time: {dish.prep_time} mins)")

        try:
            dish_index = int(input("\nEnter dish number: ")) - 1
            if not 0 <= dish_index < len(self.available_dishes):
                print("Invalid dish number!")
                time.sleep(2)
                return
        except ValueError:
            print("Please enter a valid number!")
            time.sleep(2)
            return

        try:
            table_number = int(input("Enter table number: "))
        except ValueError:
            print("Please enter a valid table number!")
            time.sleep(2)
            return

        order = Order(table_number, self.available_dishes[dish_index], datetime.now())
        self.orders.put(order)

        print("\nOrder added successfully!")
        print(f"Table {table_number} - {order.dish.name}")
        time.sleep(2)

    def start_cooking(self):
        self.clear_screen()
        print("\n=== Start Cooking ===")

        if len(self.currently_cooking) >= 5:
            print("Maximum cooking capacity reached! Finish some dishes first.")
            time.sleep(2)
            return

        tapas_cooking = [order for order in self.tapas_queue if order.status == "pending"]
        main_dishes_cooking = [order for order in self.main_dishes_queue.queue if order.status == "pending"]

        while len(self.currently_cooking) < 5 and tapas_cooking:
            order = tapas_cooking.pop(0)
            order.status = "cooking"
            order.estimated_completion = datetime.now() + timedelta(minutes=order.dish.prep_time)
            self.currently_cooking.append(order)

        while len(self.currently_cooking) < 5 and main_dishes_cooking:
            order = main_dishes_cooking.pop(0)
            order.status = "cooking"
            order.estimated_completion = datetime.now() + timedelta(minutes=order.dish.prep_time)
            self.currently_cooking.append(order)

        if not self.currently_cooking:
            print("No orders available to cook.")
        else:
            print("\nTapas (FIFO):")
            tapas_cooking = [order for order in self.currently_cooking if order.dish.type == "tapas"]
            if not tapas_cooking:
                print("No tapas currently cooking.")
            else:
                for i, order in enumerate(tapas_cooking, 1):
                    print(f"{i}. Table {order.table_number} - {order.dish.name} "
                          f"(Estimated completion: {order.estimated_completion.strftime('%H:%M:%S')})")

            print("\nMain Dishes (Priority):")
            main_dishes_cooking = [order for order in self.currently_cooking if order.dish.type == "main dish"]
            if not main_dishes_cooking:
                print("No main dishes currently cooking.")
            else:
                for i, order in enumerate(main_dishes_cooking, 1):
                    print(f"{i}. Table {order.table_number} - {order.dish.name} "
                          f"(Estimated completion: {order.estimated_completion.strftime('%H:%M:%S')})")

        input("\nPress Enter to continue...")

    def currently_preparing(self):
        self.clear_screen()
        print("\n=== Currently Preparing ===")

        tapas_cooking = [order for order in self.currently_cooking if order.dish.type == "tapas"]
        main_dishes_cooking = [order for order in self.currently_cooking if order.dish.type == "main dish"]

        print("\nTapas (FIFO):")
        if not tapas_cooking:
            print("No tapas currently cooking.")
        else:
            for i, order in enumerate(tapas_cooking, 1):
                print(f"{i}. Table {order.table_number} - {order.dish.name} "
                      f"(Estimated completion: {order.estimated_completion.strftime('%H:%M:%S')})")

        print("\nMain Dishes (Priority):")
        if not main_dishes_cooking:
            print("No main dishes currently cooking.")
        else:
            for i, order in enumerate(main_dishes_cooking, 1):
                print(f"{i}. Table {order.table_number} - {order.dish.name} "
                      f"(Estimated completion: {order.estimated_completion.strftime('%H:%M:%S')})")

        input("\nPress Enter to continue...")

    def send_out_dish(self):
        self.clear_screen()
        print("\n=== Send Out Dish ===")

        if not self.currently_cooking:
            print("No dishes currently cooking.")
            return

        print("\nCurrently Cooking:")
        for i, order in enumerate(self.currently_cooking, 1):
            print(f"{i}. Table {order.table_number} - {order.dish.name}")

        completed_dishes = input("\nEnter the numbers of completed dishes (comma-separated): ").strip()
        try:
            completed_indices = [int(x) - 1 for x in completed_dishes.split(",")]
        except ValueError:
            print("Invalid input. Please enter numbers only.")
            return

        completed_orders = [self.currently_cooking[i] for i in completed_indices if
                            0 <= i < len(self.currently_cooking)]
        self.currently_cooking = [order for i, order in enumerate(self.currently_cooking) if i not in completed_indices]
        self.completed_orders.extend(completed_orders)

        print("\nSent out the following dishes:")
        for order in completed_orders:
            print(f"Table {order.table_number} - {order.dish.name}")

        # Refill cooking list
        while len(self.currently_cooking) < 5 and not self.orders.empty():
            order = self.orders.get()
            order.status = "cooking"
            order.estimated_completion = datetime.now() + timedelta(minutes=order.dish.prep_time)
            self.currently_cooking.append(order)

        input("\nPress Enter to continue...")

    def view_completed_orders(self):
        self.clear_screen()
        print("\n=== Completed Orders ===")
        if not self.completed_orders:
            print("No orders have been completed yet.")
        else:
            for i, order in enumerate(self.completed_orders, 1):
                print(f"{i}. Table {order.table_number} - {order.dish.name} "
                      f"(Completed at: {order.estimated_completion.strftime('%H:%M:%S')})")
        input("\nPress Enter to continue...")

    # --- Chef Menu ---
    def chef_menu(self):
        while True:
            self.clear_screen()
            print("\n=== Chef Interface ===")
            print("1. Start Cooking")
            print("2. View Currently Preparing Orders")
            print("3. Send Out Completed Dishes")
            print("4. View Completed Orders")
            print("5. Remove Menu Item")
            print("6. Return to Main Menu")

            try:
                choice = int(input("\nEnter your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 6.")
                time.sleep(2)
                continue

            if choice == 1:
                self.start_cooking()
            elif choice == 2:
                self.currently_preparing()
            elif choice == 3:
                self.send_out_dish()
            elif choice == 4:
                self.view_completed_orders()
            elif choice == 5:
                self.remove_menu_item()
            elif choice == 6:
                break
            else:
                print("Invalid choice. Please try again.")
                time.sleep(2)

    # --- Waiter Menu ---
    def waiter_menu(self):
        while True:
            self.clear_screen()
            print("\n=== Waiter Interface ===")
            print("1. Add New Orders")
            print("2. View Orders")
            print("3. Display Menu")
            print("4. Return to Main Menu")

            try:
                choice = int(input("\nEnter your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 4.")
                time.sleep(2)
                continue

            if choice == 1:
                self.add_orders()
            elif choice == 2:
                self.view_orders()
            elif choice == 3:
                self.display_menu()
            elif choice == 4:
                break
            else:
                print("Invalid choice. Please try again.")
                time.sleep(2)

    def display_menu(self):
        """Display the current menu of available dishes."""
        self.clear_screen()
        print("\n=== Current Menu ===")

        if not self.available_dishes:
            print("No dishes available in the menu.")
            input("\nPress Enter to continue...")
            return

        print("\nTapas:")
        tapas_dishes = [dish for dish in self.available_dishes if dish.type == "tapas"]
        if not tapas_dishes:
            print("  No tapas dishes available.")
        else:
            for dish in tapas_dishes:
                print(f"  - {dish.name}")
                print(f"    Preparation Time: {dish.prep_time} mins")
                print(f"    Ingredients: {', '.join(dish.ingredients)}")

        print("\nMain Dishes:")
        main_dishes = [dish for dish in self.available_dishes if dish.type == "main dish"]
        if not main_dishes:
            print("  No main dishes available.")
        else:
            for dish in main_dishes:
                print(f"  - {dish.name}")
                print(f"    Preparation Time: {dish.prep_time} mins")
                print(f"    Ingredients: {', '.join(dish.ingredients)}")

        input("\nPress Enter to continue...")

    def add_orders(self):
        self.clear_screen()
        print("\n=== Add New Orders ===")

        print("\nAvailable Dishes:")
        for i, dish in enumerate(self.available_dishes, 1):
            print(f"{i}. {dish.name} (Type: {dish.type}, Prep time: {dish.prep_time} mins)")

        while True:
            try:
                dish_input = input("\nEnter dish number (or press Enter to finish): ").strip()
                if dish_input == "":
                    break

                dish_index = int(dish_input) - 1
                if not 0 <= dish_index < len(self.available_dishes):
                    print("Invalid dish number!")
                    time.sleep(2)
                    continue
            except ValueError:
                print("Please enter a valid number!")
                time.sleep(2)
                continue

            try:
                table_number = int(input("Enter table number: "))
            except ValueError:
                print("Please enter a valid table number!")
                time.sleep(2)
                continue

            order = Order(table_number, self.available_dishes[dish_index], datetime.now())

            # Add order to the appropriate queue
            if order.dish.type == "tapas":
                self.tapas_queue.append(order)
            elif order.dish.type == "main dish":
                # Priority queue: negative prep time for longest first
                order.priority = -order.dish.prep_time
                self.main_dishes_queue.put(order)

            print(f"\nOrder for Table {table_number} - {order.dish.name} added successfully!")

        print("\nFinished adding orders. Returning to Waiter Interface...")
        time.sleep(2)

    def view_orders(self):
        self.clear_screen()
        print("\n=== Orders ===")

        # Combine all the orders from tapas_queue and main_dishes_queue into a single list
        all_orders = list(self.tapas_queue) + list(self.main_dishes_queue.queue)

        if not all_orders:
            print("No orders have been placed yet.")
        else:
            for i, order in enumerate(all_orders, 1):
                print(f"{i}. Table {order.table_number} - {order.dish.name} (Status: {order.status})")

        input("\nPress Enter to continue...")

    def main_menu(self):
        while True:
            self.clear_screen()
            print("\n=== Restaurant Kitchen Queue System ===")
            print("1. Chef Interface")
            print("2. Waiter Interface")
            print("3. Add a New Recipe")
            print("4. Exit")

            try:
                choice = int(input("\nEnter your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number between 1 and 4.")
                time.sleep(2)
                continue

            if choice == 1:
                self.chef_menu()
            elif choice == 2:
                self.waiter_menu()
            elif choice == 3:
                self.add_new_recipe()
            elif choice == 4:
                print("\nExiting the system. Goodbye!")
                time.sleep(1)
                break
            else:
                print("Invalid choice. Please try again.")
                time.sleep(2)


if __name__ == "__main__":
    kitchen_system = KitchenQueueSystem()
    auth = UserAuth()

    authenticated, role = auth.login()
    if authenticated:
        print(f"\nLogin successful! Welcome, {role.capitalize()}!")
        time.sleep(2)
        if role == "chef":
            kitchen_system.chef_menu()
        elif role == "waiter":
            kitchen_system.waiter_menu()
        else:
            kitchen_system.main_menu()
    else:
        print("\nLogin failed. Exiting the system.")
        time.sleep(2)
        