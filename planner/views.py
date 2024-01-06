import logging

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _

from .forms import ExpenseListForm, ExpenseItemForm, ToDoListForm, ToDoItemForm
from .models import ExpenseList, ExpenseItem, ToDoList, ToDoItem

logger = logging.getLogger("all")


def planner(request, page):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    try:
        expense_list = ExpenseList.objects.filter(
            user=request.user).order_by("-updated")
    except ExpenseList.DoesNotExist:
        expense_list = None
    try:
        todo_list = ToDoList.objects.filter(user=request.user).order_by("-updated")
    except ToDoList.DoesNotExist:
        todo_list = None
    paginator_expense = Paginator(expense_list, per_page=10)
    paginator_todo = Paginator(todo_list, per_page=10)
    page_object_expense = paginator_expense.get_page(page)
    page_object_todo = paginator_todo.get_page(page)
    context = {
        "page_obj_expense": page_object_expense,
        "page_obj_todo": page_object_todo,
        "expense_list": expense_list,
        "todo_list": todo_list,
    }
    return render(request, "planner/planner.html", context)

###############################################################################


def expense_lists(request):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    page_name = "expense-lists"

    try:
        full_expense_list = ExpenseList.objects.filter(
            user=request.user).order_by("-updated")
    except ExpenseList.DoesNotExist:
        full_expense_list = None
        return render(request, "planner/planner_lists.html",
                      {"page_name": page_name,
                       "full_expense_list": full_expense_list})

    search_query = request.GET.get("q")
    if search_query:
        expense_list = ExpenseList.objects.filter(
            user=request.user).filter(
            name__icontains=search_query).order_by("-updated")
    else:
        expense_list = full_expense_list

    page_number = request.GET.get("page")
    paginator_expense = Paginator(expense_list, per_page=10)
    page_object_expense = paginator_expense.get_page(page_number)

    context = {
        "page_name": page_name,
        "paginator": paginator_expense,
        "page_obj": page_object_expense,
        "expense_list": expense_list,
        "full_expense_list": full_expense_list,
        "search_query": search_query
    }
    return render(request, "planner/planner_lists.html", context)


@login_required(login_url="login")
def single_expense_list(request, pk):
    profile = request.user.profile
    page = "single-expense-list"
    list_title = ExpenseList.objects.get(id=pk)
    if list_title:
        if list_title.user != request.user:
            logger.critical(
                "user: %s - enter page: single-expense-list - 🛑 SAFETY BREACH - "
                "attempt to view expense list (id: %s) of another user (id: %s)!"
                % (request.user.id, list_title.id, list_title.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")
    try:
        expense_items = ExpenseItem.objects.filter(
            expense_list=list_title).order_by(Lower("name"))
        estimated_costs = list_title.get_all_estimated_costs()
        paid_costs = list_title.get_all_paid_costs()
    except ExpenseItem.DoesNotExist:
        expense_items = None
        estimated_costs = 0
        paid_costs = 0

    # Searching engine - search through selected fields
    # If search engine is empty, queryset data is displayed in full
    search_query = request.GET.get("q")
    if search_query:
        expense_items_search = ExpenseItem.objects.filter(
            user=request.user).filter(Q(name__icontains=search_query) |
                                      Q(description__icontains=search_query)).order_by(
                                          Lower("name"))
    else:
        expense_items_search = None
    if not expense_items_search:
        expense_items_search = expense_items

    context = {
        "profile": profile,
        "page": page,
        "list_title": list_title,
        "expense_items": expense_items,
        "estimated_costs": estimated_costs,
        "paid_costs": paid_costs,
        "expense_items_search": expense_items_search
    }
    return render(request, "planner/single_list.html", context)


@login_required(login_url="login")
def add_expense_list(request):
    page = "add-expense-list"
    list_names = list(ExpenseList.objects.filter(
        user=request.user).values_list("name", flat=True))
    form = ExpenseListForm(list_names=list_names)
    if request.method == "POST":
        form = ExpenseListForm(request.POST, list_names=list_names)
        if form.is_valid():
            try:
                expense_list_form = form.save(commit=False)
                expense_list_form.user = request.user
                expense_list_form.save()
                messages.success(request, _("Dodano listę wydatków."))
                return redirect("planner:expense-lists")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-expense-list - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-expense-list - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form, "list_names": list_names}
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def edit_expense_list(request, pk):
    page = "edit-expense-list"
    list_title = ExpenseList.objects.get(id=pk)
    list_names = list(ExpenseList.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    form = ExpenseListForm(instance=list_title, list_names=list_names)
    if list_title:
        if list_title.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-expense-list - 🛑 SAFETY BREACH - "
                "attempt to edit expense list (id: %s) of another user (id: %s)!"
                % (request.user.id, list_title.id, list_title.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = ExpenseListForm(request.POST, instance=list_title, list_names=list_names)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zmieniono nazwę listy wydatków."))
                return redirect("planner:single-expense-list", pk=pk)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-expense-list (id: %s)- "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, list_title.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-expense-list - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-expense-list (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, list_title.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "list_title": list_title,
        "list_names": list_names,
    }
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def delete_expense_list(request, pk):
    page = "delete-expense-list"
    try:
        ExpenseList.objects.get(id=pk)
    except ExpenseList.DoesNotExist:
        messages.error(request, _("Brak listy o podanej nazwie w bazie danych."))
        return redirect("planner:planner", page=1)
    list_title = ExpenseList.objects.get(id=pk)
    if list_title:
        if list_title.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-expense-list - 🛑 SAFETY BREACH - "
                "attempt to delete expense list (id: %s) of another user (id: %s)!"
                % (request.user.id, list_title.id, list_title.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        try:
            ExpenseItem.objects.filter(name=list_title)
        except ExpenseItem.DoesNotExist:
            pass
        else:
            expense_items = ExpenseItem.objects.filter(name=list_title)
            expense_items.delete()

        list_title.delete()

        messages.success(request, _("Usunięto listę wydatków wraz z "
                                    "informacjami dodatkowymi."))
        return redirect("planner:planner", page=1)

    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-expense-list (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, list_title.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "list_title": list_title}
    return render(request, "planner/planner_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_expense_item(request, pk):
    page = "add-expense-item"
    expense_list = ExpenseList.objects.get(id=pk)
    form = ExpenseItemForm()
    if request.method == "POST":
        form = ExpenseItemForm(request.POST)
        if form.is_valid():
            try:
                expense_item_form = form.save(commit=False)
                expense_item_form.user = request.user
                expense_item_form.expense_list = expense_list
                expense_item_form.save()
                messages.success(request, _("Dodano element do listy wydatków."))
                return redirect("planner:single-expense-list", pk=expense_list.id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-expense-item - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-expense-item - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. "
                  "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form, "list_title": expense_list}
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def edit_expense_item(request, pk):
    page = "edit-expense-item"
    expense_item = ExpenseItem.objects.get(id=pk)
    expense_list_id = expense_item.expense_list.id
    list_title = expense_item.expense_list
    form = ExpenseItemForm(instance=expense_item)
    if expense_item:
        if expense_item.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-expense-item - 🛑 SAFETY BREACH - "
                "attempt to edit expense item (id: %s) of another user (id: %s)!"
                % (request.user.id, expense_item.id, expense_item.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = ExpenseItemForm(
            request.POST,
            instance=expense_item,
        )
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zmieniono element listy wydatków."))
                return redirect("planner:single-expense-list", pk=expense_list_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-expense-item (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, expense_item.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-expense-item (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, expense_item.id, form.errors))
            messages.error(
                request,
                _("Wystąpił błąd podczas zapisu formularza. Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-expense-item (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, expense_item.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "expense_item": expense_item,
        "form": form,
        "list_title": list_title,
    }
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def delete_expense_item(request, pk):
    page = "delete-expense-item"
    try:
        expense_item = ExpenseItem.objects.get(id=pk)
    except ExpenseItem.DoesNotExist:
        messages.error(request, _("Brak wydatku o podanej nazwie w bazie danych."))
        return redirect("planner:planner", page=1)
    expense_item = ExpenseItem.objects.get(id=pk)
    expense_list_id = expense_item.expense_list.id
    if expense_item:
        if expense_item.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-expense-item - 🛑 SAFETY BREACH - "
                "attempt to delete expense item (id: %s) of another user (id: %s)!"
                % (request.user.id, expense_item.id, expense_item.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        expense_item.delete()
        messages.success(request, _("Usunięto element z listy wydatków."))
        return redirect("planner:single-expense-list", pk=str(expense_list_id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-expense-item (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, expense_item.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "expense_item": expense_item,
        "expense_list_id": expense_list_id
    }
    return render(request, "planner/planner_delete_form.html", context)

###############################################################################


def todo_lists(request,):
    if not request.user.is_authenticated:
        messages.info(request, _("Dostęp tylko dla zalogowanych użytkowników."))
        return redirect("login")
    page_name = "todo-lists"

    try:
        full_todo_list = ToDoList.objects.filter(
            user=request.user).order_by("-updated")
    except ToDoList.DoesNotExist:
        full_todo_list = None
        return render(request, "planner/planner_lists.html",
                      {"page_name": page_name,
                       "full_todo_list": full_todo_list})

    search_query = request.GET.get("q")
    if search_query:
        todo_list = ToDoList.objects.filter(
            user=request.user).filter(
            name__icontains=search_query).order_by("-updated")
    else:
        todo_list = full_todo_list

    page_number = request.GET.get("page")
    paginator_todo = Paginator(todo_list, per_page=10)
    page_object_todo = paginator_todo.get_page(page_number)

    context = {
        "page_name": page_name,
        "paginator": paginator_todo,
        "page_obj": page_object_todo,
        "todo_list": todo_list,
        "full_todo_list": full_todo_list,
        "search_query": search_query
    }
    return render(request, "planner/planner_lists.html", context)


@login_required(login_url="login")
def single_todo_list(request, pk):
    profile = request.user.profile
    page = "single-todo-list"
    list_title = ToDoList.objects.get(id=pk)
    if list_title:
        if list_title.user != request.user:
            logger.critical(
                "user: %s - enter page: single-todo-list - 🛑 SAFETY BREACH - "
                "attempt to view todo list (id: %s) of another user (id: %s)!"
                % (request.user.id, list_title.id, list_title.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do przeglądania tych danych."))
            logout(request)
            return redirect("login")

    try:
        todo_items = ToDoItem.objects.filter(todo_list=list_title).order_by(Lower("name"))
    except ToDoItem.DoesNotExist:
        todo_items = None

    # Searching engine - search through selected fields
    # If search engine is empty, queryset data is displayed in full
    search_query = request.GET.get("q")
    if search_query:
        todo_items_search = ToDoItem.objects.filter(
            user=request.user).filter(Q(name__icontains=search_query) |
                                      Q(description__icontains=search_query) |
                                      Q(notes__icontains=search_query)).order_by(Lower("name"))
    else:
        todo_items_search = None
    if not todo_items_search:
        todo_items_search = todo_items

    context = {
        "profile": profile,
        "page": page,
        "list_title": list_title,
        "todo_items": todo_items,
        "todo_items_search": todo_items_search
    }
    return render(request, "planner/single_list.html", context)


@login_required(login_url="login")
def add_todo_list(request):
    page = "add-todo-list"
    list_names = list(ToDoList.objects.filter(
        user=request.user).values_list("name", flat=True))
    form = ToDoListForm(list_names=list_names)
    if request.method == "POST":
        form = ToDoListForm(request.POST, list_names=list_names)
        if form.is_valid():
            try:
                todo_list_form = form.save(commit=False)
                todo_list_form.user = request.user
                todo_list_form.save()
                messages.success(request, _("Dodano listę zadań."))
                return redirect("planner:todo-lists")
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-todo-list - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-todo-list - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request, _("Wystąpił błąd podczas zapisu formularza. "
                           "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form, "list_names": list_names}
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def edit_todo_list(request, pk):
    page = "edit-todo-list"
    list_title = ToDoList.objects.get(id=pk)
    list_names = list(ToDoList.objects.filter(
        user=request.user).exclude(id=pk).values_list("name", flat=True))
    form = ToDoListForm(instance=list_title, list_names=list_names)
    if list_title:
        if list_title.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-todo-list - 🛑 SAFETY BREACH - "
                "attempt to edit todo list (id: %s) of another user "
                "(id: %s)!"
                % (request.user.id, list_title.id, list_title.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = ToDoListForm(
            request.POST, instance=list_title, list_names=list_names)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zmieniono nazwę listy zadań."))
                return redirect("planner:single-todo-list", pk=pk)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-todo-list (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, list_title.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-todo-list (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, list_title.id, form.errors))
            messages.error(
                request, _("Wystąpił błąd podczas zapisu formularza. "
                           "Sprawdź poprawność danych.")
            )
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-todo-list (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, list_title.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "form": form,
        "list_title": list_title,
        "list_names": list_names,
    }
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def delete_todo_list(request, pk):
    page = "delete-todo-list"
    try:
        list_title = ToDoList.objects.get(id=pk)
    except ToDoList.DoesNotExist:
        messages.error(request, _("Brak listy o podanej nazwie w bazie danych."))
        return redirect("planner:planner", page=1)
    list_title = ToDoList.objects.get(id=pk)
    if list_title:
        if list_title.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-todo-list - 🛑 SAFETY BREACH - "
                "attempt to delete todo list (id: %s) of another "
                "user (id: %s)!"
                % (request.user.id, list_title.id, list_title.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        try:
            todo_items = ToDoItem.objects.filter(name=list_title)
        except ToDoItem.DoesNotExist:
            pass
        else:
            todo_items = ToDoItem.objects.filter(name=list_title)
            todo_items.delete()

        list_title.delete()

        messages.success(
            request, _("Usunięto listę zadań wraz z informacjami dodatkowymi."))
        return redirect("planner:planner", page=1)

    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-todo-list (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, list_title.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {"page": page, "list_title": list_title}
    return render(request, "planner/planner_delete_form.html", context)

###############################################################################


@login_required(login_url="login")
def add_todo_item(request, pk):
    page = "add-todo-item"
    list_title = ToDoList.objects.get(id=pk)
    todo_list_id = list_title.id
    form = ToDoItemForm()
    if request.method == "POST":
        form = ToDoItemForm(request.POST)
        if form.is_valid():
            try:
                todo_item_form = form.save(commit=False)
                todo_item_form.user = request.user
                todo_item_form.todo_list = list_title
                todo_item_form.save()
                messages.success(request, _("Dodano element do listy zadań."))
                return redirect("planner:single-todo-list", pk=todo_list_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: add-todo-item - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, e))
                messages.error(request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: add-todo-item - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, form.errors))
            messages.error(
                request, _("Wystąpił błąd podczas zapisu formularza. "
                           "Sprawdź poprawność danych.")
            )
    context = {"page": page, "form": form, "list_title": list_title}
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def edit_todo_item(request, pk):
    page = "edit-todo-item"
    todo_item = ToDoItem.objects.get(id=pk)
    list_title = todo_item.todo_list
    todo_list_id = list_title.id
    form = ToDoItemForm(instance=todo_item)
    if todo_item:
        if todo_item.user != request.user:
            logger.critical(
                "user: %s - enter page: edit-todo-item - 🛑 SAFETY BREACH - "
                "attempt to edit todo item (id: %s) "
                "of another user (id: %s)!"
                % (request.user.id, todo_item.id, todo_item.user.id))
            messages.error(
                request, _("Nie masz uprawnień do modyfikacji tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        form = ToDoItemForm(
            request.POST, instance=todo_item)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Zmieniono element listy zadań."))
                return redirect("planner:single-todo-list", pk=todo_list_id)
            except ValidationError as e:
                logger.error(
                    "user: %s - enter page: edit-todo-item (id: %s) - "
                    "⚠️ ValidationError with error: %s"
                    % (request.user.id, todo_item.id, e))
                messages.error(
                    request, _("Wystąpił błąd podczas zapisu formularza."))
        else:
            logger.error(
                "user: %s - enter page: edit-todo-item (id: %s) - "
                "⚠️ unsuccessful POST with error: %s"
                % (request.user.id, todo_item.id, form.errors))
            messages.error(
                request, _("Wystąpił błąd podczas zapisu formularza. "
                           "Sprawdź poprawność danych."))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: edit-todo-item (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, todo_item.id))
        messages.error(request, "Niepoprawna metoda zapisu formularza.")
        return HttpResponse("Niepoprawna metoda zapisu formularza.",
                            status=405)
    context = {
        "page": page,
        "todo_item": todo_item,
        "form": form,
        "list_title": list_title,
    }
    return render(request, "planner/planner_form.html", context)


@login_required(login_url="login")
def delete_todo_item(request, pk):
    page = "delete-todo-item"
    try:
        todo_item = ToDoItem.objects.get(id=pk)
    except ToDoItem.DoesNotExist:
        messages.error(
            request, _("Brak zadania o podanej nazwie w bazie danych."))
        return redirect("planner:planner", page=1)
    todo_item = ToDoItem.objects.get(id=pk)
    todo_list_id = todo_item.todo_list.id
    if todo_item:
        if todo_item.user != request.user:
            logger.critical(
                "user: %s - enter page: delete-todo-item - 🛑 SAFETY BREACH - "
                "attempt to delete todo item (id: %s) "
                "of another user (id: %s)!"
                % (request.user.id, todo_item.id,
                   todo_item.user.id))
            messages.error(request,
                           _("Nie masz uprawnień do usunięcia tych danych."))
            logout(request)
            return redirect("login")
    if request.method == "POST":
        todo_item.delete()
        messages.success(request, _("Usunięto element z listy zadań."))
        return redirect("planner:single-todo-list", pk=str(todo_list_id))
    elif request.method not in ["POST", "GET"]:
        logger.error(
            "user: %s - enter page: delete-todo-item (id: %s) - "
            "⚠️ invalid request method (required: POST)"
            % (request.user.id, todo_item.id))
        return HttpResponse("Niepoprawna metoda.", status=405)
    context = {
        "page": page,
        "todo_item": todo_item,
        "todo_list_id": todo_list_id
    }
    return render(request, "planner/planner_delete_form.html", context)
