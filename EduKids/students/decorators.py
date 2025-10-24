from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def role_required(*allowed_roles: str):
    """Restrict view access to specific user_type values."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if getattr(user, "user_type", None) in allowed_roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("You do not have permission to access this resource.")

        return _wrapped

    return decorator


teacher_required = role_required("teacher", "admin")
student_required = role_required("student", "admin")
admin_required = role_required("admin")



