"""
Database Reset Utility for FreelanceHub
This script helps you reset/clear database tables
"""
import sqlite3

def show_tables():
    """Show all tables in the database"""
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print("\n📊 Tables in database:")
    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
        print(f"  • {table[0]}: {count} records")
    conn.close()

def clear_all_data():
    """Clear all data from all tables (keeps table structure)"""
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    # Get all tables
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    
    print("\n🗑️  Clearing all data...")
    for table in tables:
        table_name = table[0]
        cursor.execute(f"DELETE FROM {table_name}")
        print(f"  ✓ Cleared {table_name}")
    
    conn.commit()
    conn.close()
    print("\n✅ All data cleared successfully!")

def clear_specific_table(table_name):
    """Clear data from a specific table"""
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()
        print(f"\n✅ Cleared all data from '{table_name}' table")
    except sqlite3.OperationalError as e:
        print(f"\n❌ Error: {e}")
    finally:
        conn.close()

def reset_user_data_only():
    """Clear only user-related data (users, sessions)"""
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    print("\n🗑️  Clearing user data...")
    cursor.execute("DELETE FROM users")
    print("  ✓ Cleared users")
    
    conn.commit()
    conn.close()
    print("\n✅ User data cleared successfully!")

def reset_services_only():
    """Clear only services data"""
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    print("\n🗑️  Clearing services...")
    cursor.execute("DELETE FROM services")
    print("  ✓ Cleared services")
    
    conn.commit()
    conn.close()
    print("\n✅ Services cleared successfully!")

def reset_messages_only():
    """Clear chat messages and conversations"""
    conn = sqlite3.connect('project.db')
    cursor = conn.cursor()
    
    print("\n🗑️  Clearing messages and conversations...")
    try:
        cursor.execute("DELETE FROM chat_messages")
        print("  ✓ Cleared chat messages")
        cursor.execute("DELETE FROM conversations")
        print("  ✓ Cleared conversations")
        cursor.execute("DELETE FROM notifications")
        print("  ✓ Cleared notifications")
    except sqlite3.OperationalError as e:
        print(f"  ⚠️  Some tables may not exist: {e}")
    
    conn.commit()
    conn.close()
    print("\n✅ Messages cleared successfully!")

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 FreelanceHub Database Reset Utility")
    print("=" * 50)
    
    # Show current state
    show_tables()
    
    print("\n" + "=" * 50)
    print("Select an option:")
    print("  1. Clear ALL data (everything)")
    print("  2. Clear users only")
    print("  3. Clear services only")
    print("  4. Clear messages/conversations only")
    print("  5. Clear specific table")
    print("  6. Just show tables (no changes)")
    print("  0. Exit")
    print("=" * 50)
    
    choice = input("\nEnter your choice (0-6): ").strip()
    
    if choice == "1":
        confirm = input("\n⚠️  This will delete ALL data! Are you sure? (yes/no): ")
        if confirm.lower() == "yes":
            clear_all_data()
            show_tables()
        else:
            print("❌ Cancelled")
    elif choice == "2":
        reset_user_data_only()
        show_tables()
    elif choice == "3":
        reset_services_only()
        show_tables()
    elif choice == "4":
        reset_messages_only()
        show_tables()
    elif choice == "5":
        table_name = input("Enter table name to clear: ").strip()
        clear_specific_table(table_name)
        show_tables()
    elif choice == "6":
        print("\n✓ Database information displayed above")
    elif choice == "0":
        print("👋 Exiting...")
    else:
        print("❌ Invalid choice")
