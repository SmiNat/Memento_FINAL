from django.contrib import admin

from .models import ToDoItem, ToDoList, ExpenseItem, ExpenseList

admin.site.register(ToDoList)
admin.site.register(ToDoItem)
admin.site.register(ExpenseList)
admin.site.register(ExpenseItem)
