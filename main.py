from datetime import datetime, timedelta
import json
import os

# ====================== DATA ======================
ROOMS = {
    101: {"type": "Single", "price_per_night": 80},
    102: {"type": "Single", "price_per_night": 85},
    103: {"type": "Double", "price_per_night": 120},
    104: {"type": "Double", "price_per_night": 130},
    201: {"type": "Deluxe", "price_per_night": 180},
    202: {"type": "Suite", "price_per_night": 250},
}

BOOKINGS = {}  # booking_id: booking_details
BANNED_USERS = [] # List of blocked names
next_booking_id = 1
DATA_FILE = "hotel_data.json"
ADMIN_PASSWORD = "9222"

# ====================== HELPER FUNCTIONS ======================
def load_data():
    global BOOKINGS, next_booking_id, ROOMS, BANNED_USERS
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                BOOKINGS = {int(k): v for k, v in data.get("bookings", {}).items()}
                if "rooms" in data:
                    ROOMS = {int(k): v for k, v in data["rooms"].items()}
                BANNED_USERS = data.get("banned_users", [])
                next_booking_id = data.get("next_booking_id", 1)
        except Exception as e:
            print(f"Error loading data: {e}")

def save_data():
    data = {
        "bookings": BOOKINGS,
        "next_booking_id": next_booking_id,
        "rooms": ROOMS,
        "banned_users": BANNED_USERS
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def check_availability(room_number, check_in_dt, check_out_dt):
    for booking in BOOKINGS.values():
        if booking["room_number"] == room_number and booking["status"] in ["confirmed", "checked_in"]:
            b_ci = datetime.strptime(booking["check_in"], "%Y-%m-%d")
            b_co = datetime.strptime(booking["check_out"], "%Y-%m-%d")
            if check_in_dt < b_co and check_out_dt > b_ci:
                return False
    return True

def show_rooms():
    print("\n=== Today's Room Status ===")
    print(f"{'Room':<6} {'Type':<12} {'Price/Night':<15} {'Status'}")
    print("-" * 50)

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    for room_no, info in ROOMS.items():
        is_free_today = check_availability(room_no, today, tomorrow)
        status_text = "Available" if is_free_today else "Occupied"
        status_color = "✅ " if is_free_today else "❌"
        print(f"{room_no:<6} {info['type']:<12} ${info['price_per_night']:<14} {status_color} {status_text}")

def calculate_stay_duration(check_in, check_out):
    try:
        ci = datetime.strptime(check_in, "%Y-%m-%d")
        co = datetime.strptime(check_out, "%Y-%m-%d")
        days = (co - ci).days
        return days if days > 0 else 1
    except:
        return 1

def calculate_payment(room_number, check_in, check_out):
    if room_number not in ROOMS:
        return 0
    days = calculate_stay_duration(check_in, check_out)
    price = ROOMS[room_number]["price_per_night"]
    total = price * days
    tax = total * 0.18
    return round(total + tax, 2)

def get_rooms_booked_by_user(guest_name):
    """Helper function to find all rooms ever booked by a specific user."""
    booked_rooms = set()
    for b in BOOKINGS.values():
        if b["guest_name"].lower() == guest_name.lower():
            booked_rooms.add(str(b["room_number"]))
    return ", ".join(booked_rooms) if booked_rooms else "None"

# ====================== ADMIN PANEL ======================
def admin_panel():
    print("\n🔒 Admin Access Required")
    pwd = input("Enter Admin Password: ")
    if pwd != ADMIN_PASSWORD:
        print("❌ Incorrect password. Access denied.")
        return

    while True:
        print("\n=== 🛠️ Admin Panel ===")
        print("1. Ban/Block a Scammer (Cancels active bookings)")
        print("2. Un-ban a User")
        print("3. View Banned Users")
        print("4. Add or Update a Room")
        print("5. Force Free a Room")
        print("6. Exit Admin Panel")

        choice = input("Enter choice (1-6): ").strip()

        if choice == "1":
            print("\n--- Guest Booking History ---")
            unique_guests = set(b["guest_name"] for b in BOOKINGS.values())

            if not unique_guests:
                print("No booking history available yet.")
            else:
                for guest in unique_guests:
                    rooms = get_rooms_booked_by_user(guest)
                    print(f"Guest: {guest} | Associated Rooms: {rooms}")

            print("-" * 35)
            name = input("Enter exact guest name to ban: ").strip()

            if name.lower() not in [u.lower() for u in BANNED_USERS]:
                BANNED_USERS.append(name)

                # --- NEW LOGIC: Cancel active bookings for banned user ---
                cancelled_count = 0
                for b in BOOKINGS.values():
                    if b["guest_name"].lower() == name.lower() and b["status"] in ["confirmed", "checked_in"]:
                        b["status"] = "cancelled_by_admin"
                        cancelled_count += 1

                print(f"✅ User '{name}' has been banned from booking.")
                if cancelled_count > 0:
                    print(f"✅ Automatically cancelled {cancelled_count} active booking(s) for '{name}'. Rooms are now free.")

                save_data()
            else:
                print("⚠️ User is already in the ban list.")

        elif choice == "2":
            print("\n=== Un-ban a User ===")
            if not BANNED_USERS:
                print("No users currently banned.")
            else:
                for i, name in enumerate(BANNED_USERS, 1):
                    rooms = get_rooms_booked_by_user(name)
                    print(f"{i}. {name} | Associated Rooms: {rooms}")

                print("-" * 35)
                unban_name = input("Enter exact guest name to UN-BAN: ").strip()

                found = False
                for u in BANNED_USERS:
                    if u.lower() == unban_name.lower():
                        BANNED_USERS.remove(u)
                        found = True
                        print(f"✅ User '{u}' has been successfully removed from the ban list.")
                        save_data()
                        break

                if not found:
                    print("❌ User not found in the ban list.")

        elif choice == "3":
            print("\n=== Banned Users ===")
            if not BANNED_USERS:
                print("No users currently banned.")
            else:
                for i, name in enumerate(BANNED_USERS, 1):
                    rooms = get_rooms_booked_by_user(name)
                    print(f"{i}. {name} | Associated Rooms: {rooms}")

        elif choice == "4":
            print("\n--- Current Rooms Configuration ---")
            for r_no, info in ROOMS.items():
                print(f"Room {r_no}: {info['type']} - ${info['price_per_night']}/night")
            print("-" * 35)

            try:
                r_no = int(input("Enter Room Number to Add/Update: "))
                r_type = input("Enter Room Type (e.g., Single, Double, Penthouse): ")
                r_price = float(input("Enter Price per night: "))
                ROOMS[r_no] = {"type": r_type, "price_per_night": r_price}
                print(f"✅ Room {r_no} successfully updated/added.")
                save_data()
            except ValueError:
                print("❌ Invalid input! Numbers required for Room and Price.")

        elif choice == "5":
            print("\n--- Currently Occupied / Booked Rooms ---")
            occupied_count = 0
            for b in BOOKINGS.values():
                if b["status"] in ["confirmed", "checked_in"]:
                    print(f"Room {b['room_number']} | Booked by: {b['guest_name']} | Dates: {b['check_in']} to {b['check_out']}")
                    occupied_count += 1

            if occupied_count == 0:
                print("No rooms are currently booked or occupied.")
                continue
            print("-" * 43)

            try:
                r_no = int(input("Enter Room Number to force free: "))
                if r_no in ROOMS:
                    freed = False
                    for b in BOOKINGS.values():
                        if b["room_number"] == r_no and b["status"] in ["confirmed", "checked_in"]:
                            b["status"] = "cancelled_by_admin"
                            freed = True
                    if freed:
                        print(f"✅ Room {r_no} has been force-freed. Active bookings were cancelled.")
                        save_data()
                    else:
                        print(f"⚠️ Room {r_no} has no active bookings to clear.")
                else:
                    print("❌ Room does not exist.")
            except ValueError:
                print("❌ Invalid input!")

        elif choice == "6":
            print("Exiting Admin Panel...")
            break
        else:
            print("❌ Invalid choice.")

# ====================== MAIN OPERATIONS ======================
def book_room():
    global next_booking_id
    guest_name = input("\nGuest Name: ").strip()

    if guest_name.lower() in [u.lower() for u in BANNED_USERS]:
        print("❌ Booking Denied: This user has been banned by the administrator!")
        return

    while True:
        check_in = input("Check-in Date (YYYY-MM-DD): ")
        check_out = input("Check-out Date (YYYY-MM-DD): ")

        try:
            ci = datetime.strptime(check_in, "%Y-%m-%d")
            co = datetime.strptime(check_out, "%Y-%m-%d")

            if co <= ci:
                print("❌ Error: Check-out date must be after Check-in date!\n")
                continue
            break
        except ValueError:
            print("❌ Invalid date format! Please use YYYY-MM-DD format.\n")

    print(f"\n=== Available Rooms ({check_in} to {check_out}) ===")
    available_rooms = []
    print(f"{'Room':<6} {'Type':<12} {'Price/Night'}")
    print("-" * 35)

    for room_no, info in ROOMS.items():
        if check_availability(room_no, ci, co):
            available_rooms.append(room_no)
            print(f"{room_no:<6} {info['type']:<12} ${info['price_per_night']}")

    if not available_rooms:
        print("Sorry, no rooms are available for the selected dates.")
        return

    try:
        room_no = int(input("\nEnter Room Number to book: "))
        if room_no not in available_rooms:
            print("❌ Invalid selection or Room not available for these dates!")
            return

        days = calculate_stay_duration(check_in, check_out)
        total_amount = calculate_payment(room_no, check_in, check_out)

        BOOKINGS[next_booking_id] = {
            "booking_id": next_booking_id,
            "guest_name": guest_name,
            "room_number": room_no,
            "check_in": check_in,
            "check_out": check_out,
            "days": days,
            "total_amount": total_amount,
            "status": "confirmed"
        }

        print(f"\n✅ Booking successful! Booking ID: {next_booking_id}")
        print(f"Total Amount (incl. 18% tax): ${total_amount}")

        next_booking_id += 1
        save_data()
    except ValueError:
        print("❌ Invalid input!")

def check_in():
    try:
        booking_id = int(input("\nEnter Booking ID for Check-in: "))
        if booking_id in BOOKINGS and BOOKINGS[booking_id]["status"] == "confirmed":
            BOOKINGS[booking_id]["status"] = "checked_in"
            print(f"✅ Guest {BOOKINGS[booking_id]['guest_name']} has been checked in!")
            save_data()
        else:
            print("❌ Booking not found or already checked in.")
    except ValueError:
        print("❌ Invalid Input!")

def check_out():
    try:
        booking_id = int(input("\nEnter Booking ID for Check-out: "))
        if booking_id in BOOKINGS and BOOKINGS[booking_id]["status"] == "checked_in":
            booking = BOOKINGS[booking_id]
            room_no = booking["room_number"]

            print("\n=== Check-out Details ===")
            print(f"Guest : {booking['guest_name']}")
            print(f"Room : {room_no} ({ROOMS[room_no]['type']})")
            print(f"Stay : {booking['days']} nights")
            print(f"Total Bill : ${booking['total_amount']}")

            if input("Has payment been received? (yes/no): ").lower() == "yes":
                booking["status"] = "checked_out"
                print("✅ Check-out successful!")
                save_data()
            else:
                print("Payment pending.")
        else:
            print("❌ Invalid booking or not checked in yet.")
    except ValueError:
        print("❌ Invalid Input!")

def view_bookings():
    print("\n=== All Bookings ===")
    if not BOOKINGS:
        print("No bookings yet.")
        return
    print(f"{'ID':<4} {'Guest':<20} {'Room':<6} {'Check-in':<12} {'Check-out':<12} {'Status':<18} {'Amount'}")
    print("-" * 90)
    for bid, b in BOOKINGS.items():
        print(f"{bid:<4} {b['guest_name'][:19]:<20} {b['room_number']:<6} {b['check_in']:<12} {b['check_out']:<12} {b['status']:<18} ${b['total_amount']}")

# ====================== MAIN MENU ======================
def main():
    load_data()
    print("🏨 Welcome to Hotel Haven Management System")

    while True:
        print("\n" + "="*50)
        print("1. Show Today's Room Status")
        print("2. Book Room")
        print("3. Check-in")
        print("4. Check-out")
        print("5. View All Bookings")
        print("6. Admin Panel 🔒")
        print("7. Exit")
        print("="*50)

        choice = input("Enter your choice (1-7): ").strip()

        if choice == "1": show_rooms()
        elif choice == "2": book_room()
        elif choice == "3": check_in()
        elif choice == "4": check_out()
        elif choice == "5": view_bookings()
        elif choice == "6": admin_panel()
        elif choice == "7":
            save_data()
            print("Thank you for using Hotel Haven System. Goodbye! 👋")
            break
        else:
            print("❌ Invalid choice! Please try again.")

if __name__ == "__main__":
    main()