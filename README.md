from playwright.sync_api import sync_playwright
import time
import random
import tldextract


# Яндексовые домены, которые исключаем из источников
YANDEX_DOMAINS = {
    "yandex.ru", "ya.ru", "yandex.com", "yandex.net",
    "yastatic.net", "yandexcloud.net"
}

# Селекторы блока «Быстрый ответ Алисы AI»
AI_BLOCK_SELECTORS = [
    "[data-type='alice']",
    ".AliceAnswer",
    ".alice-answer",
    "[class*='AliceAnswer']",
    "[class*='alice-answer']",
    "[class*='neural']",
    ".neural-answer",
    "[data-block='alice']",
]

# Ключевые слова в HTML для детектирования AI-блока
AI_KEYWORDS = [
    "Быстрый ответ Алисы",
    "Алиса AI",
    "alice-answer",
    "AliceAnswer",
    "neural-answer",
    "NeuralAnswer",
    "yandex_gpt",
    "YandexGPT",
]


class YandexParser:

    def __init__(self, log_callback=None):
        """
        log_callback — функция(msg: str), вызывается для передачи логов в GUI.
        Если None, логи выводятся в stdout.
        """
        self.browser = None
        self.context = None
        self.page = None
        self.p = None
        self._log = log_callback or print

    def _emit(self, msg: str):
        self._log(msg)

    def start(self, headless: bool = False):
        self._emit("🚀 Запуск браузера Chromium...")
        self.p = sync_playwright().start()

        self.browser = self.p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )

        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            geolocation={"latitude": 55.7558, "longitude": 37.6173},
            permissions=["geolocation"],
        )

        # Скрываем webdriver-флаг
        self.context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.page = self.context.new_page()
        self._emit("✅ Браузер запущен (регион: Москва, десктоп 1920×1080)")

    def _set_moscow_region(self):
        """Принудительно выставляем регион Москва через куки Яндекса."""
        try:
            self.context.add_cookies([
                {
                    "name": "yp",
                    "value": "9999999999.gpauto.55_755820:37_617348:150:1:1714000000",
                    "domain": ".yandex.ru",
                    "path": "/",
                },
                {
                    "name": "my",
                    "value": "YycCAAA=",
                    "domain": ".yandex.ru",
                    "path": "/",
                },
            ])
        except Exception:
            pass

    def check_query(self, query: str) -> dict:
        result = {
            "query": query,
            "has_ai": "Нет",
            "sources": "",
            "note": "",
        }

        self._emit(f'🔍 Проверяем запрос: «{query}»')

        try:
            url = f"https://yandex.ru/search/?text={query}&lr=213"
            self._set_moscow_region()

            self.page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            # Случайная задержка — имитируем живого пользователя
            delay = random.uniform(3, 6)
            self._emit(f"   ⏳ Ждём {delay:.1f}с...")
            time.sleep(delay)

            html = self.page.content()

            # --- Детектирование AI-блока ---
            found_by_keyword = any(kw in html for kw in AI_KEYWORDS)

            found_by_selector = False
            for sel in AI_BLOCK_SELECTORS:
                try:
                    el = self.page.locator(sel).first
                    if el.count() > 0:
                        found_by_selector = True
                        break
                except Exception:
                    pass

            if found_by_keyword or found_by_selector:
                result["has_ai"] = "Да"
                self._emit("   ✅ AI-блок обнаружен!")

                # --- Сбор источников внутри AI-блока ---
                domains = self._collect_ai_sources()
                result["sources"] = "; ".join(sorted(domains)) if domains else "источник не указан"
                self._emit(f"   📎 Источники: {result['sources']}")
            else:
                self._emit("   ❌ AI-блока нет")

        except Exception as e:
            result["note"] = f"Ошибка: {e}"
            self._emit(f"   ⚠️  Ошибка: {e}")

        return result

    def _collect_ai_sources(self) -> set:
        """Собирает домены ссылок внутри AI-блока."""
        domains = set()

        # Пробуем найти контейнер AI-блока и взять ссылки только внутри него
        for sel in AI_BLOCK_SELECTORS:
            try:
                container = self.page.locator(sel).first
                if container.count() > 0:
                    links = container.locator("a").all()
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if href.startswith("http"):
                            ext = tldextract.extract(href)
                            domain = f"{ext.domain}.{ext.suffix}"
                            if domain not in YANDEX_DOMAINS and ext.domain:
                                domains.add(domain)
                    if domains:
                        return domains
            except Exception:
                pass

        # Фолбэк: берём все внешние ссылки на странице
        try:
            for link in self.page.locator("a").all():
                href = link.get_attribute("href") or ""
                if href.startswith("http"):
                    ext = tldextract.extract(href)
                    domain = f"{ext.domain}.{ext.suffix}"
                    if domain not in YANDEX_DOMAINS and ext.domain:
                        domains.add(domain)
        except Exception:
            pass

        return domains

    def close(self):
        try:
            if self.browser:
                self.browser.close()
            if self.p:
                self.p.stop()
            self._emit("🛑 Браузер закрыт.")
        except Exception:
            pass
