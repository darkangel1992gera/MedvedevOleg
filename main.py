import json
import os
import ssl
import tkinter as tk
from tkinter import messagebox, ttk
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FAVORITES_FILE = "favorites.json"


def load_favorites():
    """Загрузить список избранных из JSON-файла."""
    if os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_favorites(favorites):
    """Сохранить список избранных в JSON-файл."""
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, indent=2, ensure_ascii=False)


class GitHubUserFinderApp:
    """Главное окно приложения."""

    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder — Медведев Олег Игоревич")
        self.root.geometry("650x500")
        self.root.resizable(False, False)

        self.favorites = load_favorites()

        # Верхняя панель поиска
        search_frame = ttk.Frame(root, padding=10)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Логин GitHub:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Искать", command=self.search_user).pack(side=tk.LEFT, padx=5)

        # Область результатов
        list_frame = ttk.Frame(root, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(list_frame, text="Результаты поиска:").pack(anchor=tk.W)
        self.results_listbox = tk.Listbox(list_frame, height=10)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        # Кнопки управления избранным
        btn_frame = ttk.Frame(root, padding=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Добавить в избранное", command=self.add_to_favorites).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Показать избранное", command=self.show_favorites).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить из избранного", command=self.remove_favorite).pack(side=tk.LEFT, padx=5)

        # Статусная строка
        self.status_var = tk.StringVar(value="Готов")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Текущие результаты поиска (список кортежей: логин, аватар)
        self.current_results = []

    def search_user(self):
        """Поиск пользователей GitHub через API."""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Ошибка валидации", "Поле поиска не может быть пустым.")
            return

        self.status_var.set(f"Поиск '{query}'...")
        self.root.update()

        try:
            url = f"https://api.github.com/search/users?q={query}&per_page=10"
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})

            # Отключение проверки SSL-сертификата (учебный проект)
            ctx = ssl._create_unverified_context()

            with urlopen(req, context=ctx, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))

            items = data.get("items", [])
            self.current_results = [(item["login"], item["avatar_url"]) for item in items]

            self.results_listbox.delete(0, tk.END)
            if not self.current_results:
                self.results_listbox.insert(tk.END, "Пользователи не найдены.")
                self.status_var.set("Нет результатов.")
            else:
                for username, _ in self.current_results:
                    self.results_listbox.insert(tk.END, username)
                self.status_var.set(f"Найдено: {len(items)}.")
        except (HTTPError, URLError) as e:
            messagebox.showerror("Ошибка API", f"Не удалось получить данные: {e}")
            self.status_var.set("Ошибка.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Непредвиденная ошибка: {e}")
            self.status_var.set("Ошибка.")

    def add_to_favorites(self):
        """Добавить выделенного пользователя в избранное."""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showinfo("Информация", "Сначала выберите пользователя из результатов поиска.")
            return

        index = selection[0]
        if index >= len(self.current_results):
            return

        username, avatar_url = self.current_results[index]
        if any(fav["username"] == username for fav in self.favorites):
            messagebox.showinfo("Информация", f"Пользователь '{username}' уже в избранном.")
            return

        self.favorites.append({"username": username, "avatar_url": avatar_url})
        save_favorites(self.favorites)
        self.status_var.set(f"'{username}' добавлен в избранное.")
        messagebox.showinfo("Успех", f"Пользователь '{username}' добавлен в избранное.")

    def show_favorites(self):
        """Открыть окно со списком избранных."""
        fav_window = tk.Toplevel(self.root)
        fav_window.title("Избранное")
        fav_window.geometry("400x300")
        fav_window.resizable(False, False)

        ttk.Label(fav_window, text="Избранные пользователи GitHub", font=("", 12, "bold")).pack(pady=5)

        fav_listbox = tk.Listbox(fav_window, height=12)
        fav_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for fav in self.favorites:
            fav_listbox.insert(tk.END, fav["username"])

    def remove_favorite(self):
        """Удалить выбранного пользователя из избранного."""
        if not self.favorites:
            messagebox.showinfo("Информация", "Список избранного пуст.")
            return

        remove_win = tk.Toplevel(self.root)
        remove_win.title("Удаление из избранного")
        remove_win.geometry("300x250")
        remove_win.resizable(False, False)

        ttk.Label(remove_win, text="Выберите пользователя для удаления:").pack(pady=5)
        remove_listbox = tk.Listbox(remove_win, height=6)
        remove_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for fav in self.favorites:
            remove_listbox.insert(tk.END, fav["username"])

        def do_remove():
            sel = remove_listbox.curselection()
            if not sel:
                messagebox.showinfo("Информация", "Сначала выберите пользователя.", parent=remove_win)
                return
            idx = sel[0]
            removed = self.favorites.pop(idx)
            save_favorites(self.favorites)
            self.status_var.set(f"'{removed['username']}' удалён из избранного.")
            messagebox.showinfo("Успех", f"'{removed['username']}' удалён из избранного.", parent=remove_win)
            remove_win.destroy()

        ttk.Button(remove_win, text="Удалить выбранного", command=do_remove).pack(pady=10)
        ttk.Button(remove_win, text="Отмена", command=remove_win.destroy).pack()


if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinderApp(root)
    root.mainloop()