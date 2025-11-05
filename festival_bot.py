import json
import os
from datetime import datetime, timedelta
import sys

DATA_FILE = "festivals.json"
DATE_FORMAT = "%Y-%m-%d"  # ISO format for easy sorting & validation

try:
    from prettytable import PrettyTable
    _HAS_PRETTY = True
except Exception:
    _HAS_PRETTY = False

try:
    from plyer import notification
    _HAS_PLYER = True
except Exception:
    _HAS_PLYER = False


def clear_console():
    """Clear console in a cross-platform way."""
    os.system('cls' if os.name == 'nt' else 'clear')


def load_data():
    """Load festival list from DATA_FILE. Returns a list of dicts."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # ensure correct keys
            valid = []
            for item in data:
                if 'name' in item and 'date' in item:
                    valid.append(item)
            return valid
    except Exception as e:
        print(f"Warning: could not read {DATA_FILE}: {e}")
        return []


def save_data(festivals):
    """Save list of festivals to DATA_FILE."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(festivals, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error: could not write to {DATA_FILE}: {e}")


def parse_date(date_str):
    """Parse a date string in YYYY-MM-DD. Returns datetime.date or None."""
    try:
        dt = datetime.strptime(date_str, DATE_FORMAT).date()
        return dt
    except ValueError:
        return None


def format_date(date_obj):
    return date_obj.strftime(DATE_FORMAT)


def sort_festivals(festivals):
    """Return a new list sorted by next occurrence date (this year or next if passed)."""
    # We'll sort by raw date string to keep simple (YYYY-MM-DD) — but to show upcoming in a rolling year
    def key_fn(item):
        try:
            return datetime.strptime(item['date'], DATE_FORMAT).date()
        except Exception:
            return datetime.max.date()
    return sorted(festivals, key=key_fn)


def view_all(festivals):
    if not festivals:
        print("No festivals saved yet. Add one from the menu.")
        return
    festivals_sorted = sort_festivals(festivals)
    if _HAS_PRETTY:
        table = PrettyTable()
        table.field_names = ["#", "Name", "Date", "Notes"]
        for i, f in enumerate(festivals_sorted, start=1):
            table.add_row([i, f.get('name',''), f.get('date',''), f.get('notes','')])
        print(table)
    else:
        print("\nSaved festivals:")
        for i, f in enumerate(festivals_sorted, start=1):
            print(f"{i}. {f.get('name','')} — {f.get('date','')}" + (f" — {f.get('notes')}" if f.get('notes') else ""))


def add_festival(festivals):
    name = input("Festival name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    date_input = input(f"Date (YYYY-MM-DD): ").strip()
    dt = parse_date(date_input)
    if not dt:
        print("Invalid date format. Use YYYY-MM-DD.")
        return
    notes = input("Optional notes/description (press Enter to skip): ").strip()
    # check duplicates (same name and date)
    for f in festivals:
        if f['name'].lower() == name.lower() and f['date'] == format_date(dt):
            print("A festival with this name and date already exists.")
            return
    festivals.append({'name': name, 'date': format_date(dt), 'notes': notes})
    save_data(festivals)
    print("Festival added and saved.")


def delete_festival(festivals):
    if not festivals:
        print("No festivals to delete.")
        return
    view_all(festivals)
    try:
        idx = int(input("Enter the number of the festival to delete (0 to cancel): ").strip())
    except ValueError:
        print("Invalid input.")
        return
    if idx == 0:
        print("Cancelled.")
        return
    if 1 <= idx <= len(festivals):
        removed = festivals.pop(idx-1)
        save_data(festivals)
        print(f"Removed festival: {removed.get('name')} — {removed.get('date')}")
    else:
        print("Index out of range.")


def upcoming_from_today(festivals, days_range=30):
    """Return festivals occurring within the next `days_range` days (including today).
       Uses the festival date as given (no yearly recurrence logic)."""
    today = datetime.today().date()
    end = today + timedelta(days=days_range)
    result = []
    for f in festivals:
        dt = parse_date(f['date'])
        if not dt:
            continue
        if today <= dt <= end:
            result.append((f, dt))
    result.sort(key=lambda x: x[1])
    return result


def check_reminders(festivals):
    today = datetime.today().date()
    within_7 = []
    today_list = []
    for f in festivals:
        dt = parse_date(f['date'])
        if not dt:
            continue
        delta = (dt - today).days
        if delta == 0:
            today_list.append((f, dt))
        elif 1 <= delta <= 7:
            within_7.append((f, dt))
    # Print results
    if today_list:
        print("\n🎉 Festivals happening TODAY:")
        for f, dt in today_list:
            print(f" - {f['name']} ({f['date']})" + (f" — {f.get('notes')}") if f.get('notes') else "")
            notify(f"{f['name']} is today!", f.get('notes',''))
    else:
        print("\nNo festivals today.")

    if within_7:
        print("\n📅 Festivals within the next 7 days:")
        for f, dt in within_7:
            dleft = (dt - today).days
            print(f" - {f['name']} on {f['date']} (in {dleft} day{'s' if dleft>1 else ''})" + (f" — {f.get('notes')}") if f.get('notes') else "")
            notify(f"Upcoming: {f['name']} in {dleft} day{'s' if dleft>1 else ''}", f.get('notes',''))
    else:
        print("\nNo festivals within the next 7 days.")


def notify(title, message=''):
    """Send desktop notification if plyer is installed; otherwise do nothing.
       Keep simple and cross-platform.
    """
    if not _HAS_PLYER:
        return
    try:
        notification.notify(title=title, message=message or title, app_name="FestivalBot", timeout=6)
    except Exception:
        pass


def init_demo_data(festivals):
    """Add some demo data if empty — you can remove this after testing."""
    if festivals:
        return
    sample = [
        {"name": "New Year", "date": f"{datetime.today().year}-01-01", "notes": "Start of the year"},
        {"name": "Independence Day", "date": f"{datetime.today().year}-08-15", "notes": "National holiday"},
        {"name": "Festival Example", "date": format_date(datetime.today().date() + timedelta(days=3)), "notes": "Demo festival in 3 days"}
    ]
    festivals.extend(sample)
    save_data(festivals)


def main_menu():
    festivals = load_data()
    # Uncomment the following line to seed demo data automatically (optional)
    # init_demo_data(festivals)

    while True:
        print("\n=== Festival Reminder Bot ===")
        print("1. View all saved festivals")
        print("2. Add a new festival")
        print("3. Delete a festival")
        print("4. Check reminders (today / next 7 days)")
        print("5. Show upcoming festivals within next N days")
        print("6. Export festivals to JSON (backup)")
        print("7. Exit")
        choice = input("Choose an option (1-7): ").strip()
        if choice == '1':
            clear_console()
            view_all(festivals)
        elif choice == '2':
            add_festival(festivals)
        elif choice == '3':
            delete_festival(festivals)
        elif choice == '4':
            check_reminders(festivals)
        elif choice == '5':
            try:
                n = int(input("Show upcoming within how many days? (e.g. 30): ").strip())
            except ValueError:
                print("Invalid number.")
                continue
            ups = upcoming_from_today(festivals, days_range=n)
            if not ups:
                print(f"No festivals within next {n} days.")
            else:
                print(f"Festivals within next {n} days:")
                for f, dt in ups:
                    print(f" - {f['name']} on {f['date']}")
        elif choice == '6':
            backup_name = input("Backup filename (press Enter for 'festivals_backup.json'): ").strip() or 'festivals_backup.json'
            try:
                with open(backup_name, 'w', encoding='utf-8') as bf:
                    json.dump(festivals, bf, ensure_ascii=False, indent=2)
                print(f"Exported to {backup_name}")
            except Exception as e:
                print(f"Failed to export: {e}")
        elif choice == '7':
            print("Goodbye — reminders saved.")
            save_data(festivals)
            sys.exit(0)
        else:
            print("Invalid choice. Choose 1-7.")


if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting. Bye!")

