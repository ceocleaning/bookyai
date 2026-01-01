"""
Admin Dashboard Users Views
Handles user management: list, detail, edit, delete
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q, Count
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone


@staff_member_required
@login_required
def users_list(request):
    """
    Display all users with search and filtering
    """
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', 'all')  # all, staff, active, inactive
    page_number = request.GET.get('page', 1)
    
    # Base queryset
    users = User.objects.all().select_related('business').prefetch_related('groups')
    
    # Apply search
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Apply filters
    if filter_type == 'staff':
        users = users.filter(is_staff=True)
    elif filter_type == 'active':
        users = users.filter(is_active=True)
    elif filter_type == 'inactive':
        users = users.filter(is_active=False)
    elif filter_type == 'business':
        users = users.filter(business__isnull=False)
    
    # Order by date joined (newest first)
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 20)  # 20 users per page
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    business_users = User.objects.filter(business__isnull=False).count()
    
    context = {
        'page_title': 'User Management',
        'users': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'business_users': business_users,
    }
    
    return render(request, 'admin_dashboard/users/list.html', context)


@staff_member_required
@login_required
def user_detail(request, user_id):
    """
    Display detailed information about a specific user
    """
    user = get_object_or_404(User, id=user_id)
    
    # Get related data
    has_business = hasattr(user, 'business')
    business = user.business if has_business else None
    
    # Get user's groups
    groups = user.groups.all()
    
    # Get user statistics
    if has_business:
        from bookings.models import Booking
        from leads.models import Lead
        from invoices.models import Invoice
        
        total_bookings = Booking.objects.filter(business=business).count()
        total_leads = Lead.objects.filter(business=business).count()
        total_invoices = Invoice.objects.filter(booking__business=business).count()
    else:
        total_bookings = 0
        total_leads = 0
        total_invoices = 0
    
    context = {
        'page_title': f'User: {user.get_full_name() or user.username}',
        'user_obj': user,
        'has_business': has_business,
        'business': business,
        'groups': groups,
        'total_bookings': total_bookings,
        'total_leads': total_leads,
        'total_invoices': total_invoices,
    }
    
    return render(request, 'admin_dashboard/users/detail.html', context)


@staff_member_required
@login_required
def user_edit(request, user_id):
    """
    Edit user information
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update user fields
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        
        # Update boolean fields
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        
        try:
            user.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('admin_dashboard:user_detail', user_id=user.id)
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    context = {
        'page_title': f'Edit User: {user.username}',
        'user_obj': user,
    }
    
    return render(request, 'admin_dashboard/users/edit.html', context)


@staff_member_required
@login_required
def user_delete(request, user_id):
    """
    API endpoint to delete a user
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deleting yourself
    if user.id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'You cannot delete your own account'
        }, status=400)
    
    # Prevent deleting superusers (unless you are one)
    if user.is_superuser and not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'You cannot delete a superuser account'
        }, status=403)
    
    try:
        username = user.username
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {username} deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@login_required
def user_toggle_status(request, user_id):
    """
    API endpoint to toggle user active status
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent deactivating yourself
    if user.id == request.user.id:
        return JsonResponse({
            'success': False,
            'error': 'You cannot deactivate your own account'
        }, status=400)
    
    try:
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        
        return JsonResponse({
            'success': True,
            'message': f'User {user.username} {status} successfully',
            'is_active': user.is_active
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@staff_member_required
@login_required
def get_user_password_info(request, user_id):
    """
    API endpoint to get user password information (hashed)
    Returns password hash and metadata
    """
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user = get_object_or_404(User, id=user_id)
    
    # Get password metadata
    password_hash = user.password
    
    # Determine password algorithm
    if password_hash.startswith('pbkdf2_sha256'):
        algorithm = 'PBKDF2-SHA256'
    elif password_hash.startswith('argon2'):
        algorithm = 'Argon2'
    elif password_hash.startswith('bcrypt'):
        algorithm = 'BCrypt'
    else:
        algorithm = 'Unknown'
    
    # Check if password is usable
    has_usable_password = user.has_usable_password()
    
    return JsonResponse({
        'success': True,
        'user_id': user.id,
        'username': user.username,
        'password_hash': password_hash,
        'algorithm': algorithm,
        'has_usable_password': has_usable_password,
        'last_login': user.last_login.isoformat() if user.last_login else None,
    })


@staff_member_required
@login_required
def change_user_password(request, user_id):
    """
    API endpoint to change user password
    Requires new password and confirmation
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    user = get_object_or_404(User, id=user_id)
    
    # Get passwords from request
    import json
    try:
        data = json.loads(request.body)
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
    except json.JSONDecodeError:
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
    
    # Validation
    if not new_password:
        return JsonResponse({
            'success': False,
            'error': 'New password is required'
        }, status=400)
    
    if len(new_password) < 8:
        return JsonResponse({
            'success': False,
            'error': 'Password must be at least 8 characters long'
        }, status=400)
    
    if new_password != confirm_password:
        return JsonResponse({
            'success': False,
            'error': 'Passwords do not match'
        }, status=400)
    
    # Additional password strength validation
    if new_password.isdigit():
        return JsonResponse({
            'success': False,
            'error': 'Password cannot be entirely numeric'
        }, status=400)
    
    if new_password.lower() in ['password', '12345678', 'qwerty', 'admin']:
        return JsonResponse({
            'success': False,
            'error': 'Password is too common. Please choose a stronger password'
        }, status=400)
    
    try:
        # Set new password (Django handles hashing)
        user.set_password(new_password)
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Password for user {user.username} changed successfully',
            'user_id': user.id,
            'username': user.username
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
