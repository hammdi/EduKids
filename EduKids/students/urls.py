from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import gamification_views
from . import api_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('students/dashboard/', views.dashboard, name='students_dashboard'),
    
    # Student Gamification Routes (Protected by @student_required)
    path('student/gamification/', gamification_views.student_dashboard, name='student_gamification_dashboard'),
    path('student/customize/', gamification_views.student_customize, name='student_customize'),
    path('student/store/', gamification_views.student_store_improved, name='student_store'),
    path('student/inventory/', gamification_views.student_inventory, name='student_inventory'),
    path('student/badges/', gamification_views.student_badges, name='student_badges'),
    path('student/profile/gamification/', gamification_views.student_profile_gamification, name='student_profile_gamification'),
    
    # Student API Routes (REST endpoints)
    path('api/student/points/', api_views.get_student_points, name='api_student_points'),
    path('api/student/points/add', api_views.add_student_points, name='api_add_points'),
    path('api/student/points/daily-reward', api_views.daily_reward, name='api_daily_reward'),
    path('api/student/badges/', api_views.get_student_badges, name='api_student_badges'),
    path('api/student/shop/items', api_views.get_shop_items, name='api_shop_items'),
    path('api/student/shop/buy/<int:item_id>', api_views.buy_shop_item, name='api_buy_item'),
    path('api/student/avatar/inventory', api_views.get_avatar_inventory, name='api_avatar_inventory'),
    path('api/student/avatar/equip/<int:item_id>', api_views.equip_item, name='api_equip_item'),
    path('api/student/avatar/unequip/<int:item_id>', api_views.unequip_item, name='api_unequip_item'),
    
    # Admin CRUD operations
    path('admin/users/', views.user_management, name='user_management'),
    path('admin/users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('admin/users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('admin/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # Redirect old Django default URLs
    path('accounts/profile/', views.profile, name='old_profile'),
]
