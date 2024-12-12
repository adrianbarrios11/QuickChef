import tkinter as tk
from tkinter import messagebox
from queue import PriorityQueue
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
import csv
import os

@dataclass
class Dish:
    name: str
    prep_time: int  # in minutes
    ingredients: List[str]
    type: str  # tapas or main dish

current_dir = os.getcwd()

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


class KitchenQueueSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant Kitchen Queue System")
        self.tapas_queue = []  # FIFO queue for tapas
        self.main_dishes_queue = PriorityQueue()  # Priority queue for main dishes
        self.currently_cooking = []
        self.completed_orders = []
        self.tapas_orders = []  # Orders for tapas
        self.main_dish_orders = []  # Orders for main dishes
        self.available_dishes = []  # This will be populated dynamically
        self.load_menu(current_dir + "Menu.csv")  # Load the menu from the CSV file
        self.create_login_screen()

    def load_menu(self, file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Skip header row if there is one
                for row in reader:
                    name, prep_time, dish_type, ingredients = row
                    ingredients_list = ingredients.split(", ")  # Split ingredients into a list
                    self.available_dishes.append(Dish(name, int(prep_time), ingredients_list, dish_type))
            print(f"Loaded {len(self.available_dishes)} dishes from {file_path}.")
        except FileNotFoundError:
            messagebox.showerror("File Error", f"Menu file '{file_path}' not found!")
        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred while loading the menu: {e}")


    def create_login_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Restaurant Management System", font=("Arial", 18)).pack(pady=20)

        tk.Label(self.root, text="Username:", font=("Arial", 14)).pack(pady=5)
        self.username_entry = tk.Entry(self.root, font=("Arial", 14))
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Password:", font=("Arial", 14)).pack(pady=5)
        self.password_entry = tk.Entry(self.root, font=("Arial", 14), show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Login", font=("Arial", 14), command=self.handle_login, width=10).pack(pady=20)

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if username == "admin" and password == "admin123":
            self.main_menu()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")

    def main_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Main Interface", font=("Arial", 18)).pack(pady=20)

        tk.Button(self.root, text="Chef Interface", font=("Arial", 14), command=self.chef_menu, width=20).pack(pady=10)
        tk.Button(self.root, text="Waiter Interface", font=("Arial", 14), command=self.waiter_menu, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Exit", font=("Arial", 14), command=self.root.quit, width=20).pack(pady=10)

    def chef_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Chef Interface", font=("Arial", 18)).pack(pady=20)

        tk.Button(self.root, text="View Orders", font=("Arial", 14), command=self.view_orders, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Start Cooking", font=("Arial", 14), command=self.start_cooking, width=20).pack(
            pady=10)
        tk.Button(self.root, text="View Currently Preparing", font=("Arial", 14), command=self.currently_preparing,
                  width=20).pack(pady=10)
        tk.Button(self.root, text="Send Out Completed Dishes", font=("Arial", 14), command=self.send_out_dish,
                  width=20).pack(pady=10)
        tk.Button(self.root, text="Menu Management", font=("Arial", 14), command=self.menu_management, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Back to Main Menu", font=("Arial", 14), command=self.main_menu, width=20).pack(
            pady=10)


    def view_orders(self):
        self.clear_screen()
        tk.Label(self.root, text="View Orders", font=("Arial", 18)).pack(pady=20)

        # Display tapas orders
        tk.Label(self.root, text="Tapas Orders", font=("Arial", 16)).pack(pady=10)
        if not self.tapas_orders:
            tk.Label(self.root, text="No Tapas Orders.", font=("Arial", 14)).pack(pady=5)
        else:
            for order in self.tapas_orders:
                tk.Label(self.root, text=f"Table {order.table_number}: {order.dish.name}", font=("Arial", 14)).pack()

        # Display main dish orders
        tk.Label(self.root, text="Main Dish Orders", font=("Arial", 16)).pack(pady=10)
        if not self.main_dish_orders:
            tk.Label(self.root, text="No Main Dish Orders.", font=("Arial", 14)).pack(pady=5)
        else:
            for order in self.main_dish_orders:
                tk.Label(self.root, text=f"Table {order.table_number}: {order.dish.name}", font=("Arial", 14)).pack()

        # Buttons for navigation
        tk.Button(self.root, text="To Chef Interface", font=("Arial", 14), command=self.chef_menu, width=20).pack(
            pady=10)
        tk.Button(self.root, text="To Waiter Interface", font=("Arial", 14), command=self.waiter_menu, width=20).pack(
            pady=10)

    def start_cooking(self):
        # Cooking limits
        tapas_limit = 3
        main_dish_limit = 2

        # Add up to 3 tapas to the currently cooking list
        while len([o for o in self.currently_cooking if o.dish.type == "tapas"]) < tapas_limit and self.tapas_orders:
            order = self.tapas_orders.pop(0)
            self.currently_cooking.append(order)

        # Sort main dish orders by preparation time (highest first)
        self.main_dish_orders.sort(key=lambda o: o.dish.prep_time, reverse=True)

        # Add up to 2 main dishes to the currently cooking list
        while len([o for o in self.currently_cooking if
                   o.dish.type == "main dish"]) < main_dish_limit and self.main_dish_orders:
            order = self.main_dish_orders.pop(0)
            self.currently_cooking.append(order)

        if not self.currently_cooking:
            messagebox.showinfo("No Orders", "No orders available to start cooking.")
        else:
            cooking_dishes = ", ".join([order.dish.name for order in self.currently_cooking])
            messagebox.showinfo("Cooking", f"Started cooking: {cooking_dishes}")

    def currently_preparing(self):
        self.clear_screen()
        tk.Label(self.root, text="Currently Preparing", font=("Arial", 18)).pack(pady=20)

        # Display tapas currently being prepared
        tk.Label(self.root, text="Tapas", font=("Arial", 16)).pack(pady=10)
        tapas_preparing = [order for order in self.currently_cooking if order.dish.type == "tapas"]
        if not tapas_preparing:
            tk.Label(self.root, text="No tapas are being prepared.", font=("Arial", 14)).pack(pady=5)
        else:
            for order in tapas_preparing:
                tk.Label(self.root, text=f"Table {order.table_number}: {order.dish.name} ({order.dish.prep_time} min)",
                         font=("Arial", 14)).pack(pady=5)

        # Display main dishes currently being prepared
        tk.Label(self.root, text="Main Dishes", font=("Arial", 16)).pack(pady=10)
        main_dishes_preparing = [order for order in self.currently_cooking if order.dish.type == "main dish"]
        if not main_dishes_preparing:
            tk.Label(self.root, text="No main dishes are being prepared.", font=("Arial", 14)).pack(pady=5)
        else:
            for order in main_dishes_preparing:
                tk.Label(self.root, text=f"Table {order.table_number}: {order.dish.name} ({order.dish.prep_time} min)",
                         font=("Arial", 14)).pack(pady=5)


        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.chef_menu, width=20).pack(pady=20)

    def send_out_dish(self):
        if not self.currently_cooking:
            messagebox.showinfo("No Dishes", "No dishes are currently being prepared.")
            return

        self.clear_screen()
        tk.Label(self.root, text="Select Dish to Send Out", font=("Arial", 18)).pack(pady=20)

        for idx, order in enumerate(self.currently_cooking):
            dish_info = f"{idx + 1}. Table {order.table_number}: {order.dish.name} ({order.dish.type})"
            tk.Button(self.root, text=dish_info, font=("Arial", 14),
                      command=lambda i=idx: self.complete_and_send_out(i), width=40).pack(pady=5)

        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.chef_menu, width=20).pack(pady=10)

    def complete_and_send_out(self, index):
        order = self.currently_cooking.pop(index)
        self.completed_orders.append(order)
        messagebox.showinfo("Dish Completed", f"{order.dish.name} for Table {order.table_number} sent out!")
        self.send_out_dish()

    def menu_management(self):
        self.clear_screen()
        tk.Label(self.root, text="Menu Management", font=("Arial", 18)).pack(pady=20)
        tk.Button(self.root, text="Add New Dish", font=("Arial", 14), command=self.add_new_dish, width=20).pack(pady=10)
        tk.Button(self.root, text="Delete Recipe", font=("Arial", 14), command=self.delete_recipe, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Edit Recipe", font=("Arial", 14), command=self.edit_recipe, width=20).pack(pady=10)

        tk.Button(self.root, text="Back to Chef Interface", font=("Arial", 14), command=self.chef_menu, width=20).pack(
            pady=20)

    def add_new_dish(self):
        self.clear_screen()
        tk.Label(self.root, text="Add New Dish", font=("Arial", 18)).pack(pady=20)

        tk.Label(self.root, text="Dish Name:", font=("Arial", 14)).pack(pady=5)
        self.new_dish_name_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_dish_name_entry.pack(pady=5)

        tk.Label(self.root, text="Dish Type (main dish or tapas):", font=("Arial", 14)).pack(pady=5)
        self.new_dish_type_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_dish_type_entry.pack(pady=5)

        tk.Label(self.root, text="Ingredients (comma separated):", font=("Arial", 14)).pack(pady=5)
        self.new_dish_ingredients_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_dish_ingredients_entry.pack(pady=5)

        tk.Label(self.root, text="Preparation Time (in minutes):", font=("Arial", 14)).pack(pady=5)
        self.new_dish_prep_time_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_dish_prep_time_entry.pack(pady=5)

        tk.Button(self.root, text="Add Dish", font=("Arial", 14), command=self.save_new_dish, width=20).pack(pady=10)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.menu_management, width=20).pack(pady=10)

    def save_new_dish(self):
        name = self.new_dish_name_entry.get().strip()
        dish_type = self.new_dish_type_entry.get().strip().lower()
        ingredients = self.new_dish_ingredients_entry.get().strip()
        prep_time_str = self.new_dish_prep_time_entry.get().strip()

        # Validate inputs
        if not name or not dish_type or not ingredients or not prep_time_str:
            messagebox.showerror("Input Error", "All fields are required.")
            return

        if dish_type not in ["main dish", "tapas"]:
            messagebox.showerror("Input Error", "Dish type must be 'main dish' or 'tapas'.")
            return

        try:
            prep_time = int(prep_time_str)
        except ValueError:
            messagebox.showerror("Input Error", "Preparation time must be a valid number.")
            return

        # Save the new dish to the CSV file
        try:
            with open(current_dir + "Menu.csv", mode='a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([name, prep_time, dish_type, ingredients])

            # Update the available dishes list
            ingredients_list = ingredients.split(", ")
            new_dish = Dish(name, prep_time, ingredients_list, dish_type)
            self.available_dishes.append(new_dish)

            messagebox.showinfo("Success", f"New dish '{name}' added successfully!")
            self.chef_menu()  # Go back to the chef menu

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while saving the dish: {e}")

    def delete_recipe(self):
        self.clear_screen()
        tk.Label(self.root, text="Delete Recipe", font=("Arial", 18)).pack(pady=20)

        # Create a dropdown list of available dishes
        dish_names = [dish.name for dish in self.available_dishes]
        self.dish_to_delete = tk.StringVar(value="Select a dish to delete")
        tk.OptionMenu(self.root, self.dish_to_delete, *dish_names).pack(pady=5)

        # Button to confirm deletion
        tk.Button(self.root, text="Delete", font=("Arial", 14), command=self.confirm_delete_recipe, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.menu_management, width=20).pack(pady=10)

    def confirm_delete_recipe(self):
        dish_name = self.dish_to_delete.get()

        if dish_name == "Select a dish to delete":
            messagebox.showerror("Invalid Selection", "Please select a dish to delete.")
            return

        # Find the dish object in available_dishes
        dish_to_delete = next((dish for dish in self.available_dishes if dish.name == dish_name), None)

        if dish_to_delete:
            # Remove from the list of available dishes
            self.available_dishes = [dish for dish in self.available_dishes if dish != dish_to_delete]

            # Update the CSV file by rewriting it without the deleted dish
            self.update_menu_csv()

            messagebox.showinfo("Success", f"Dish '{dish_name}' has been deleted successfully!")
            self.chef_menu()
        else:
            messagebox.showerror("Error", "Dish not found.")

    def update_menu_csv(self):

        try:
            with open(current_dir + "Menu.csv", mode='w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["name", "prep_time", "type", "ingredients"])  # Write the header
                for dish in self.available_dishes:
                    writer.writerow([dish.name, dish.prep_time, dish.type, ", ".join(dish.ingredients)])
            print(f"Menu updated, {len(self.available_dishes)} dishes remaining.")
        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred while updating the menu: {e}")

    def edit_recipe(self):
        self.clear_screen()
        tk.Label(self.root, text="Edit Recipe", font=("Arial", 18)).pack(pady=20)

        tk.Label(self.root, text="Select Recipe to Edit:", font=("Arial", 14)).pack(pady=5)
        self.recipe_var = tk.StringVar(value="Select a recipe")
        recipe_names = [dish.name for dish in self.available_dishes]
        tk.OptionMenu(self.root, self.recipe_var, *recipe_names).pack(pady=5)

        tk.Button(self.root, text="Edit Selected Recipe", font=("Arial", 14), command=self.edit_selected_recipe,
                  width=20).pack(pady=10)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.menu_management, width=20).pack(pady=10)

    def edit_selected_recipe(self):
        selected_recipe_name = self.recipe_var.get()
        if selected_recipe_name == "Select a recipe":
            messagebox.showerror("Error", "Please select a recipe to edit.")
            return

        self.selected_dish = next((dish for dish in self.available_dishes if dish.name == selected_recipe_name), None)
        if not self.selected_dish:
            messagebox.showerror("Error", "Recipe not found.")
            return

        self.clear_screen()
        tk.Label(self.root, text=f"Editing Recipe: {self.selected_dish.name}", font=("Arial", 18)).pack(pady=20)

        tk.Label(self.root, text="Name:", font=("Arial", 14)).pack(pady=5)
        self.new_name_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_name_entry.insert(0, self.selected_dish.name)
        self.new_name_entry.pack(pady=5)

        tk.Label(self.root, text="Preparation Time (minutes):", font=("Arial", 14)).pack(pady=5)
        self.new_prep_time_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_prep_time_entry.insert(0, str(self.selected_dish.prep_time))
        self.new_prep_time_entry.pack(pady=5)

        tk.Label(self.root, text="Type (tapas/main dish):", font=("Arial", 14)).pack(pady=5)
        self.new_type_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_type_entry.insert(0, self.selected_dish.type)
        self.new_type_entry.pack(pady=5)

        tk.Label(self.root, text="Ingredients (comma-separated):", font=("Arial", 14)).pack(pady=5)
        self.new_ingredients_entry = tk.Entry(self.root, font=("Arial", 14))
        self.new_ingredients_entry.insert(0, ", ".join(self.selected_dish.ingredients))
        self.new_ingredients_entry.pack(pady=5)

        tk.Button(self.root, text="Save Changes", font=("Arial", 14), command=self.save_recipe_changes, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.menu_management, width=20).pack(pady=10)

    def save_recipe_changes(self):
        new_name = self.new_name_entry.get().strip()
        try:
            new_prep_time = int(self.new_prep_time_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Preparation time must be a number.")
            return

        new_type = self.new_type_entry.get().strip()
        new_ingredients = self.new_ingredients_entry.get().strip().split(", ")

        if not new_name or not new_type or not new_ingredients:
            messagebox.showerror("Error", "All fields must be filled out.")
            return

        # Update the dish in available_dishes
        self.selected_dish.name = new_name
        self.selected_dish.prep_time = new_prep_time
        self.selected_dish.type = new_type
        self.selected_dish.ingredients = new_ingredients

        # Update the CSV file
        try:
            with open(current_dir + "Menu.csv", mode="w", encoding="utf-8", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["name", "prep_time", "type", "ingredients"])  # Write header
                for dish in self.available_dishes:
                    writer.writerow([dish.name, dish.prep_time, dish.type, ", ".join(dish.ingredients)])
            messagebox.showinfo("Success", "Recipe updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update the recipe: {e}")
            return

        self.menu_management()

    def waiter_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Waiter Interface", font=("Arial", 18)).pack(pady=20)

        tk.Button(self.root, text="Add New Order", font=("Arial", 14), command=self.add_order, width=20).pack(
            pady=10)
        tk.Button(self.root, text="View Orders", font=("Arial", 14), command=self.view_orders, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Display Menu", font=("Arial", 14), command=self.display_menu, width=20).pack(
            pady=10)
        tk.Button(self.root, text="Back to Main Menu", font=("Arial", 14), command=self.main_menu, width=20).pack(
            pady=10)


    def add_order(self):
        self.clear_screen()
        tk.Label(self.root, text="Add New Order", font=("Arial", 18)).pack(pady=20)

        tk.Label(self.root, text="Table Number:", font=("Arial", 14)).pack(pady=5)
        self.table_number_entry = tk.Entry(self.root, font=("Arial", 14))
        self.table_number_entry.pack(pady=5)

        tk.Label(self.root, text="Select Dish:", font=("Arial", 14)).pack(pady=5)
        self.dish_var = tk.StringVar(value="Select a dish")
        dish_options = [dish.name for dish in self.available_dishes]
        tk.OptionMenu(self.root, self.dish_var, *dish_options).pack(pady=5)

        tk.Button(self.root, text="Place Order", font=("Arial", 14), command=self.place_order, width=20).pack(pady=10)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.waiter_menu, width=20).pack(pady=10)

    def place_order(self):
        try:
            table_number = int(self.table_number_entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Input", "Table number must be an integer!")
            return

        dish_name = self.dish_var.get()
        if dish_name == "Select a dish":
            messagebox.showerror("Invalid Input", "Please select a dish.")
            return

        dish = next((d for d in self.available_dishes if d.name == dish_name), None)
        if not dish:
            messagebox.showerror("Error", "Dish not found.")
            return

        order_time = datetime.now()
        order = Order(table_number, dish, order_time)

        if dish.type == "tapas":
            self.tapas_orders.append(order)
        elif dish.type == "main dish":
            self.main_dish_orders.append(order)

        messagebox.showinfo("Success", f"Order for {dish_name} added successfully!")
        self.waiter_menu()

        if dish.type == "tapas":
            self.tapas_queue.append(order)
        elif dish.type == "main dish":
            self.main_dishes_queue.put(order)

        messagebox.showinfo("Success", f"Order for {dish_name} added successfully!")
        self.waiter_menu()

    def display_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Available Dishes", font=("Arial", 18)).pack(pady=20)

        for dish in self.available_dishes:
            ingredients_str = ", ".join(dish.ingredients)  # Convert ingredients list to a comma-separated string
            tk.Label(self.root,
                     text=f"{dish.name} ({dish.type}) - {dish.prep_time} min\nIngredients: {ingredients_str}",
                     font=("Arial", 14)).pack()

        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.waiter_menu, width=20).pack(pady=10)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = KitchenQueueSystemGUI(root)
    root.mainloop()