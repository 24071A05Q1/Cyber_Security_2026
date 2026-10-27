#!/usr/bin/env python
"""
Script to create an admin user with the correct role.
Run this script to create an admin user that can access the admin dashboard.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'placement_project.settings')
django.setup()

from accounts.models import CustomUser

def create_admin_user():
    """Create an admin user with the correct role."""
    print("Creating Admin User...")
    print("=" * 40)
    
    # Get user input
    username = input("Enter username for admin: ")
    email = input("Enter email for admin: ")
    password = input("Enter password for admin: ")
    
    # Check if user already exists
    if CustomUser.objects.filter(username=username).exists():
        print(f"User '{username}' already exists!")
        return
    
    if CustomUser.objects.filter(email=email).exists():
        print(f"Email '{email}' is already registered!")
        return
    
    # Create the admin user
    try:
        admin_user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"Role: {admin_user.role}")
        print(f"Email: {admin_user.email}")
        print("\nYou can now:")
        print("1. Login at: http://127.0.0.1:8000/login/")
        print("2. Access admin dashboard at: http://127.0.0.1:8000/admin/dashboard/")
        print("3. Access Django admin at: http://127.0.0.1:8000/django-admin/")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

def update_existing_superuser():
    """Update an existing superuser to have admin role."""
    print("Update Existing Superuser to Admin Role")
    print("=" * 40)
    
    username = input("Enter the username of existing superuser: ")
    
    try:
        user = CustomUser.objects.get(username=username)
        if user.is_superuser:
            user.role = 'admin'
            user.save()
            print(f"✅ User '{username}' role updated to 'admin'!")
            print(f"Role: {user.role}")
            print(f"Email: {user.email}")
            print("\nYou can now:")
            print("1. Login at: http://127.0.0.1:8000/login/")
            print("2. Access admin dashboard at: http://127.0.0.1:8000/admin/dashboard/")
            print("3. Access Django admin at: http://127.0.0.1:8000/django-admin/")
        else:
            print(f"❌ User '{username}' is not a superuser!")
    except CustomUser.DoesNotExist:
        print(f"❌ User '{username}' not found!")

def list_admin_users():
    """List all admin users."""
    print("Current Admin Users")
    print("=" * 40)
    
    admin_users = CustomUser.objects.filter(role='admin')
    if admin_users.exists():
        for user in admin_users:
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Superuser: {user.is_superuser}")
            print("-" * 20)
    else:
        print("No admin users found!")

if __name__ == "__main__":
    print("Admin User Management")
    print("=" * 40)
    print("1. Create new admin user")
    print("2. Update existing superuser to admin role")
    print("3. List current admin users")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == "1":
        create_admin_user()
    elif choice == "2":
        update_existing_superuser()
    elif choice == "3":
        list_admin_users()
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice!") 