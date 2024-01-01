from django.conf import settings
from django.urls import path

from . import views

app_name = "planner"

urlpatterns = [
    path("planner/<int:page>/", views.planner, name="planner"),
    path("expense-lists/", views.expense_lists, name="expense-lists"),
    path("single-expense-list/<str:pk>/", views.single_expense_list, name="single-expense-list"),
    path("todo-lists/", views.todo_lists, name="todo-lists"),
    path("single-todo-list/<str:pk>/", views.single_todo_list, name="single-todo-list"),

    path("add-expense-list/", views.add_expense_list, name="add-expense-list"),
    path("edit-expense-list/<str:pk>/", views.edit_expense_list, name="edit-expense-list"),
    path("delete-expense-list/<str:pk>/", views.delete_expense_list, name="delete-expense-list"),

    path("single-expense-list/<str:pk>/add-expense-item/", views.add_expense_item, name="add-expense-item"),
    path("edit-expense-item/<str:pk>/", views.edit_expense_item, name="edit-expense-item"),
    path("delete-expense-item/<str:pk>/", views.delete_expense_item, name="delete-expense-item"),

    path("add-todo-list/", views.add_todo_list, name="add-todo-list"),
    path("edit-todo-list/<str:pk>/", views.edit_todo_list, name="edit-todo-list"),
    path("delete-todo-list/<str:pk>/", views.delete_todo_list, name="delete-todo-list"),

    path("single-expense-list/<str:pk>/add-todo-item/", views.add_todo_item, name="add-todo-item"),
    path("edit-todo-item/<str:pk>/", views.edit_todo_item, name="edit-todo-item"),
    path("delete-todo-item/<str:pk>/", views.delete_todo_item, name="delete-todo-item"),

]

if settings.DEBUG:  # !!! zmienić na produkcji na serwer docelowy!!! # usunąć na produkcji!
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
