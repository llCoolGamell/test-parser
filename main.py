"""
GUI-интерфейс для Yandex AI Checker.
Написан на tkinter (входит в стандартную библиотеку Python).
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import time
import pandas as pd
from parser import YandexParser


# ── Цветовая схема ──────────────────────────────────────────────
COLORS = {
    "bg":        "#0f1117",   # фон приложения
    "surface":   "#1a1d27",   # карточки / панели
    "border":    "#2a2d3e",   # бордюры
    "accent":    "#6c63ff",   # акцент (фиолетовый)
    "accent2":   "#00d4aa",   # второй акцент (бирюзовый)
    "danger":    "#ff5252",   # ошибка
    "warn":      "#ffb74d",   # предупреждение
    "ok":        "#69f0ae",   # успех
    "text":      "#e0e0e0",   # основной текст
    "muted":     "#6b7280",   # вторичный текст
    "log_bg":    "#080a0f",   # фон лога
}

# ── Типы лог-сообщений → цвет ───────────────────────────────────
LOG_TAG_COLORS = {
    "info":    COLORS["text"],
    "ok":      COLORS["ok"],
    "error":   COLORS["danger"],
    "warn":    COLORS["warn"],
    "accent":  COLORS["accent2"],
    "muted":   COLORS["muted"],
}

FONT_MONO = ("Consolas", 10) if os.name == "nt" else ("Menlo", 10)
FONT_UI   = ("Segoe UI", 10) if os.name == "nt" else ("SF Pro Display", 10)
FONT_H1   = ("Segoe UI", 14, "bold") if os.name == "nt" else ("SF Pro Display", 14, "bold")
FONT_H2   = ("Segoe UI", 11, "bold") if os.name == "nt" else ("SF Pro Display", 11, "bold")


def _tag(msg: str) -> str:
    """Определяет тег для сообщения лога по первому символу."""
    if msg.startswith("✅") or msg.startswith("🎉"):
        return "ok"
    if msg.startswith("⚠️") or msg.startswith("⚠"):
        return "warn"
    if msg.startswith("❌") or msg.startswith("🛑"):
        return "error"
    if msg.startswith("🔍") or msg.startswith("📎") or msg.startswith("🚀"):
        return "accent"
    if msg.startswith("   "):
        return "muted"
    return "info"


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Yandex AI Checker")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry("900x680")
        self.root.minsize(760, 560)

        self._q: queue.Queue = queue.Queue()       # очередь лог-сообщений
        self._running = False
        self._thread: threading.Thread | None = None

        self._queries_path = tk.StringVar(value="requests.txt")
        self._headless    = tk.BooleanVar(value=False)
        self._output_path = tk.StringVar(value="output/result.xlsx")

        self._total   = tk.IntVar(value=0)
        self._done    = tk.IntVar(value=0)
        self._count_ok  = tk.IntVar(value=0)
        self._count_no  = tk.IntVar(value=0)

        self._build_ui()
        self._schedule_poll()

    # ── Build UI ────────────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        # ── Заголовок ──
        header = tk.Frame(root, bg=COLORS["surface"], pady=14)
        header.pack(fill="x")

        tk.Label(
            header, text="🔎  Yandex AI Checker",
            font=FONT_H1, bg=COLORS["surface"], fg=COLORS["text"]
        ).pack(side="left", padx=20)

        tk.Label(
            header,
            text="Проверка блока «Быстрый ответ Алисы AI» в поисковой выдаче",
            font=FONT_UI, bg=COLORS["surface"], fg=COLORS["muted"]
        ).pack(side="left", padx=4)

        # ── Разделитель ──
        ttk.Separator(root, orient="horizontal").pack(fill="x")

        # ── Основная область (настройки + лог) ──
        body = tk.Frame(root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # Левая панель настроек
        left = tk.Frame(body, bg=COLORS["surface"], width=280,
                        padx=16, pady=16, bd=0,
                        highlightbackground=COLORS["border"], highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._build_settings(left)

        # Правая панель — лог
        right = tk.Frame(body, bg=COLORS["bg"])
        right.pack(side="left", fill="both", expand=True)
        self._build_log_panel(right)

        # ── Статус-бар / прогресс ──
        self._build_statusbar(root)

    def _section(self, parent, title):
        tk.Label(
            parent, text=title.upper(),
            font=("Segoe UI", 8, "bold") if os.name == "nt" else ("SF Pro Display", 8, "bold"),
            bg=COLORS["surface"], fg=COLORS["muted"]
        ).pack(anchor="w", pady=(14, 4))
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=(0, 8))

    def _build_settings(self, parent):
        tk.Label(parent, text="⚙️  Настройки",
                 font=FONT_H2, bg=COLORS["surface"], fg=COLORS["text"]
                 ).pack(anchor="w")

        # -- Файл запросов --
        self._section(parent, "Файл запросов")
        row = tk.Frame(parent, bg=COLORS["surface"])
        row.pack(fill="x")
        self._entry_qpath = tk.Entry(
            row, textvariable=self._queries_path,
            bg=COLORS["log_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat", font=FONT_MONO,
            highlightbackground=COLORS["border"], highlightthickness=1
        )
        self._entry_qpath.pack(side="left", fill="x", expand=True)
        tk.Button(
            row, text="…", command=self._browse_queries,
            bg=COLORS["border"], fg=COLORS["text"],
            relief="flat", padx=8, font=FONT_UI,
            activebackground=COLORS["accent"]
        ).pack(side="left", padx=(4, 0))

        # -- Файл вывода --
        self._section(parent, "Файл результатов")
        row2 = tk.Frame(parent, bg=COLORS["surface"])
        row2.pack(fill="x")
        tk.Entry(
            row2, textvariable=self._output_path,
            bg=COLORS["log_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat", font=FONT_MONO,
            highlightbackground=COLORS["border"], highlightthickness=1
        ).pack(side="left", fill="x", expand=True)
        tk.Button(
            row2, text="…", command=self._browse_output,
            bg=COLORS["border"], fg=COLORS["text"],
            relief="flat", padx=8, font=FONT_UI,
            activebackground=COLORS["accent"]
        ).pack(side="left", padx=(4, 0))

        # -- Опции --
        self._section(parent, "Опции")
        tk.Checkbutton(
            parent, text="Фоновый режим (headless)",
            variable=self._headless,
            bg=COLORS["surface"], fg=COLORS["text"],
            selectcolor=COLORS["log_bg"],
            activebackground=COLORS["surface"],
            font=FONT_UI
        ).pack(anchor="w")

        # -- Статистика --
        self._section(parent, "Статистика")
        stats = tk.Frame(parent, bg=COLORS["surface"])
        stats.pack(fill="x")

        self._stat_labels = {}
        for key, label, color in [
            ("total",    "Всего запросов",   COLORS["text"]),
            ("done",     "Обработано",       COLORS["accent2"]),
            ("count_ok", "Найдено AI-блоков", COLORS["ok"]),
            ("count_no", "Без AI-блока",      COLORS["muted"]),
        ]:
            row_s = tk.Frame(stats, bg=COLORS["surface"])
            row_s.pack(fill="x", pady=1)
            tk.Label(row_s, text=label + ":", fg=COLORS["muted"],
                     bg=COLORS["surface"], font=FONT_UI).pack(side="left")
            lbl = tk.Label(row_s, text="0", fg=color,
                           bg=COLORS["surface"], font=FONT_H2)
            lbl.pack(side="right")
            self._stat_labels[key] = lbl

        # -- Кнопки управления --
        self._section(parent, "Управление")
        self._btn_start = tk.Button(
            parent, text="▶  Запустить",
            command=self._start,
            bg=COLORS["accent"], fg="#ffffff",
            relief="flat", font=FONT_H2,
            padx=10, pady=8,
            activebackground="#857bff",
            cursor="hand2"
        )
        self._btn_start.pack(fill="x", pady=(0, 6))

        self._btn_stop = tk.Button(
            parent, text="⏹  Остановить",
            command=self._stop,
            bg=COLORS["danger"], fg="#ffffff",
            relief="flat", font=FONT_H2,
            padx=10, pady=8,
            activebackground="#ff7070",
            cursor="hand2",
            state="disabled"
        )
        self._btn_stop.pack(fill="x", pady=(0, 6))

        tk.Button(
            parent, text="🗑  Очистить лог",
            command=self._clear_log,
            bg=COLORS["border"], fg=COLORS["text"],
            relief="flat", font=FONT_UI,
            padx=10, pady=6,
            activebackground=COLORS["surface"],
            cursor="hand2"
        ).pack(fill="x")

        # Открыть результат
        tk.Button(
            parent, text="📂  Открыть результат",
            command=self._open_result,
            bg=COLORS["border"], fg=COLORS["accent2"],
            relief="flat", font=FONT_UI,
            padx=10, pady=6,
            activebackground=COLORS["surface"],
            cursor="hand2"
        ).pack(fill="x", pady=(6, 0))

    def _build_log_panel(self, parent):
        header_row = tk.Frame(parent, bg=COLORS["bg"])
        header_row.pack(fill="x", pady=(0, 6))

        tk.Label(header_row, text="📋  Журнал событий",
                 font=FONT_H2, bg=COLORS["bg"], fg=COLORS["text"]
                 ).pack(side="left")

        self._log_box = scrolledtext.ScrolledText(
            parent,
            bg=COLORS["log_bg"],
            fg=COLORS["text"],
            font=FONT_MONO,
            relief="flat",
            wrap="word",
            state="disabled",
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=10, pady=8,
            spacing3=3,
        )
        self._log_box.pack(fill="both", expand=True)

        # Теги цветов
        for tag, color in LOG_TAG_COLORS.items():
            self._log_box.tag_configure(tag, foreground=color)
        self._log_box.tag_configure("ts", foreground=COLORS["muted"])

    def _build_statusbar(self, parent):
        bar = tk.Frame(parent, bg=COLORS["surface"], pady=6, padx=12)
        bar.pack(fill="x", side="bottom")

        self._status_lbl = tk.Label(
            bar, text="Готов к работе",
            bg=COLORS["surface"], fg=COLORS["muted"], font=FONT_UI
        )
        self._status_lbl.pack(side="left")

        self._progress = ttk.Progressbar(
            bar, mode="determinate", length=200
        )
        self._progress.pack(side="right", padx=(10, 0))

        self._pct_lbl = tk.Label(
            bar, text="0%",
            bg=COLORS["surface"], fg=COLORS["accent2"], font=FONT_UI
        )
        self._pct_lbl.pack(side="right")

    # ── Логирование ─────────────────────────────────────────────

    def _log(self, msg: str):
        """Кладём сообщение в очередь (можно вызывать из потока)."""
        self._q.put(msg)

    def _flush_log(self):
        """Переносим сообщения из очереди в виджет (только из главного потока)."""
        try:
            while True:
                msg = self._q.get_nowait()
                self._write_log(msg)
        except queue.Empty:
            pass

    def _write_log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        tag = _tag(msg)
        box = self._log_box
        box.configure(state="normal")
        box.insert("end", f"[{ts}] ", "ts")
        box.insert("end", msg + "\n", tag)
        box.configure(state="disabled")
        box.see("end")

    def _clear_log(self):
        self._log_box.configure(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.configure(state="disabled")

    # ── Опрос очереди ───────────────────────────────────────────

    def _schedule_poll(self):
        self._flush_log()
        self.root.after(100, self._schedule_poll)

    # ── Загрузка запросов ───────────────────────────────────────

    def _load_queries(self, path: str) -> list[str]:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".xlsx":
            df = pd.read_excel(path, header=None)
            return df.iloc[:, 0].dropna().astype(str).tolist()
        elif ext == ".csv":
            df = pd.read_csv(path, header=None)
            return df.iloc[:, 0].dropna().astype(str).tolist()
        else:
            with open(path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]

    # ── Запуск / остановка ──────────────────────────────────────

    def _start(self):
        path = self._queries_path.get().strip()
        if not os.path.exists(path):
            messagebox.showerror("Ошибка", f"Файл не найден:\n{path}")
            return

        try:
            queries = self._load_queries(path)
        except Exception as e:
            messagebox.showerror("Ошибка чтения", str(e))
            return

        if not queries:
            messagebox.showwarning("Пусто", "Файл запросов пуст.")
            return

        os.makedirs(os.path.dirname(self._output_path.get()) or ".", exist_ok=True)

        self._running = True
        self._total.set(len(queries))
        self._done.set(0)
        self._count_ok.set(0)
        self._count_no.set(0)
        self._update_stats()

        self._btn_start.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        self._status_lbl.configure(text="Работает…")

        self._clear_log()
        self._log(f"📋 Загружено запросов: {len(queries)}")
        self._log(f"📁 Результат: {self._output_path.get()}")
        self._log("─" * 50)

        self._thread = threading.Thread(
            target=self._worker,
            args=(queries,),
            daemon=True
        )
        self._thread.start()

    def _stop(self):
        self._running = False
        self._log("⚠️  Остановка после текущего запроса…")
        self._btn_stop.configure(state="disabled")

    def _worker(self, queries: list[str]):
        parser = YandexParser(log_callback=self._log)
        results = []

        try:
            parser.start(headless=self._headless.get())
        except Exception as e:
            self._log(f"❌ Не удалось запустить браузер: {e}")
            self._finish()
            return

        out_path = self._output_path.get()

        try:
            for i, query in enumerate(queries, start=1):
                if not self._running:
                    break

                self._log(f"\n[{i}/{len(queries)}] ────────────────────────────")
                result = parser.check_query(query)

                results.append({
                    "Запрос":               result["query"],
                    "Есть AI-блок":         result["has_ai"],
                    "Источник в AI-блоке":  result["sources"],
                    "Примечание":           result["note"],
                })

                # Обновляем счётчики
                self._done.set(i)
                if result["has_ai"] == "Да":
                    self._count_ok.set(self._count_ok.get() + 1)
                else:
                    self._count_no.set(self._count_no.get() + 1)
                self.root.after(0, self._update_stats)

                # Сохраняем промежуточный результат
                try:
                    pd.DataFrame(results).to_excel(out_path, index=False)
                except Exception as e:
                    self._log(f"⚠️  Ошибка сохранения: {e}")

        finally:
            parser.close()

        if results:
            self._log("\n" + "─" * 50)
            self._log(f"🎉 Готово! Обработано: {len(results)} из {len(queries)}")
            self._log(f"   AI-блок найден: {self._count_ok.get()}")
            self._log(f"   Без AI-блока:   {self._count_no.get()}")
            self._log(f"   Файл сохранён: {out_path}")

        self.root.after(0, self._finish)

    def _finish(self):
        self._running = False
        self._btn_start.configure(state="normal")
        self._btn_stop.configure(state="disabled")
        self._status_lbl.configure(text="Завершено")

    # ── Статистика ───────────────────────────────────────────────

    def _update_stats(self):
        total = self._total.get()
        done  = self._done.get()

        self._stat_labels["total"].configure(text=str(total))
        self._stat_labels["done"].configure(text=str(done))
        self._stat_labels["count_ok"].configure(text=str(self._count_ok.get()))
        self._stat_labels["count_no"].configure(text=str(self._count_no.get()))

        pct = int(done / total * 100) if total else 0
        self._progress["value"] = pct
        self._pct_lbl.configure(text=f"{pct}%")

    # ── Файловые диалоги ────────────────────────────────────────

    def _browse_queries(self):
        path = filedialog.askopenfilename(
            title="Выберите файл запросов",
            filetypes=[("Все форматы", "*.txt *.csv *.xlsx"),
                       ("TXT", "*.txt"), ("CSV", "*.csv"), ("Excel", "*.xlsx")]
        )
        if path:
            self._queries_path.set(path)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Куда сохранить результат",
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")]
        )
        if path:
            self._output_path.set(path)

    def _open_result(self):
        path = self._output_path.get()
        if not os.path.exists(path):
            messagebox.showinfo("Файл не найден", f"Результат ещё не создан:\n{path}")
            return
        import subprocess, sys
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])

    # ── Запуск ──────────────────────────────────────────────────

    def run(self):
        self._write_log("Добро пожаловать в Yandex AI Checker!")
        self._write_log("Укажите файл запросов и нажмите «Запустить».")
        self.root.mainloop()
