import asyncio
import functools
from typing import Callable, Dict, Any, Optional, List
import inspect
import re
import logging
import ast

from view.base import MViewItem

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('router_errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Router:
    def __init__(self):
        self.routes: Dict[str, Dict[str, Any]] = {}
        self.base_controller = None
        self.middlewares: List[Callable] = []
        self.current_item: MViewItem | None = None  # Для хранения текущего элемента формы

    def add_middleware(self, middleware: Callable):
        self.middlewares.append(middleware)

    def get_current_item(self):
        """Возвращает текущий активный элемент (MViewItem)"""
        if self.current_item:
            return self.current_item
        else:
            return MViewItem(title="Ошибка", text="Ошибка формы")

    def set_current_item(self, item):
        """Устанавливает текущий активный элемент"""
        self.current_item = item

    def route(self, path: str, handler: Callable):
        """Регистрация обработчика без декоратора"""

        param_pattern = re.compile(r'\{(\w+)\}')
        params = param_pattern.findall(path)

        regex_path = re.sub(r'\{\w+\}', r'([^/]+)', path)
        regex_path = f'^{regex_path}$'

        self.routes[path] = {
            'handler': handler,
            'params': params,
            'regex': re.compile(regex_path)
        }
        return handler

    async def handle(self, request_path: str, *args, **kwargs) -> Any:
        """Основной метод обработки запросов с поддержкой формы"""
        # Проверяем, если это запрос формы (начинается с form_)
        print(request_path)
        if request_path.startswith(('form_choice:', 'form_back:')):
            try:
                return await self._handle_form_request(request_path, *args, **kwargs)
            except ValueError as e:
                print(f"Form handling error: {e}")
                raise

        # Стандартная обработка маршрутов
        matched_route = None
        params_values = {}
        matched_path: str = ''

        for path, route_data in self.routes.items():
            match = route_data['regex'].match(request_path)
            if match:
                matched_route = route_data
                matched_path = path
                params_values = {
                    param: value
                    for param, value in zip(
                        route_data['params'],
                        match.groups()
                    )
                }
                break

        if not matched_route:
            print("Available routes:", self.routes.items())
            raise ValueError(f"No route found for path: {request_path}")

        # Добавляем update в params_values, если он передан в kwargs
        if 'update' in kwargs:
            params_values['update'] = kwargs['update']

        # Добавляем параметры из URL в kwargs
        kwargs.update(params_values)

        # Передаем оригинальный путь, а не имя обработчика
        return await self._execute_route(matched_path, *args, **kwargs)

    async def _handle_form_request(self, request_path: str, *args, **kwargs) -> Any:
        """Обработка запросов формы"""
        current_item = self.get_current_item()
        if not current_item or not getattr(current_item, 'form_fields', None):
            raise ValueError("No active form to handle")

        if request_path.startswith("form_choice:"):
            _, step, value = request_path.split(":")
            step = int(step)
            if step == current_item.current_form_step:
                current_item.getFormField(step).current_value = value
                current_item.current_form_step += 1
                if current_item.current_form_step >= len(current_item.form_fields):
                    # Форма завершена
                    form_data = {
                        field.name: field.current_value for field in current_item.form_fields}
                    if "form_completed" in self.routes:
                        kwargs['form_data'] = form_data
                        return await self._execute_route("form_completed", **kwargs)
                    return form_data
        elif request_path.startswith("form_back:"):
            step = int(request_path.split(":")[1])
            current_item.current_form_step = max(0, step - 1)

        return None

    async def _execute_route(self, path: str, *args, **kwargs) -> Any:
        """Выполняет обработку маршрута с автоподстановкой None для отсутствующих параметров"""
        try:
            matched_route = self.routes.get(path)
            if not matched_route:
                error_msg = f"No route found for path: {path}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Применяем middleware
            for middleware in self.middlewares:
                try:
                    if inspect.iscoroutinefunction(middleware):
                        await middleware(*args, **kwargs)
                    else:
                        middleware(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Middleware error: {str(e)}", exc_info=True)
                    continue

            # Анализируем параметры обработчика
            handler_params = inspect.signature(
                matched_route['handler']).parameters
            final_kwargs = {}

            # Заполняем параметры
            for param_name, param in handler_params.items():
                if param_name in kwargs:
                    # Берем переданное значение
                    final_kwargs[param_name] = kwargs[param_name]
                elif param.default is not param.empty:
                    # Используем значение по умолчанию из функции
                    final_kwargs[param_name] = param.default
                else:
                    # Устанавливаем None для обязательных параметров
                    final_kwargs[param_name] = None

            # Логируем параметры
            logger.info(
                f"Calling {matched_route['handler'].__name__} with args: {final_kwargs}")
            if self.returns_a_function(matched_route['handler']):
                result = matched_route['handler'](**final_kwargs)
                render_func = await result if inspect.isawaitable(result) else result
                return await render_func(**kwargs)
            else:
                error_msg = "Функция не вернула ответ в виде асинхронной функции" + \
                    f" {matched_route['handler'].__name__} из модуля {matched_route['handler'].__module__}" + \
                    "Функция должна вернуть результат вида return partial( self.driver.render_message, content=MViewItem())"
                logger.error(error_msg)
                raise ValueError(error_msg)

        except Exception as e:
            logger.critical(f"Route execution failed: {str(e)}", exc_info=True)
            raise

    def returns_a_function(self, func):
        try:
            # First try to get the source code
            try:
                source = inspect.getsource(func)
            except (TypeError, OSError):
                return False  # Can't get source for lambdas/compiled functions

            # Normalize indentation
            lines = source.splitlines()
            if not lines:
                return False

            # Find minimum indentation (excluding empty lines)
            min_indent = min(len(line) - len(line.lstrip())
                             for line in lines if line.strip())

            # Remove common indentation
            normalized_source = "\n".join(
                line[min_indent:] if line.strip() else line
                for line in lines
            )

            # Parse the AST
            tree = ast.parse(normalized_source)

            # Check for return statements that return callables
            for node in ast.walk(tree):
                if isinstance(node, ast.Return):
                    if isinstance(node.value, (ast.Lambda, ast.Call, ast.Name)):
                        return True
                    # Also check for attributes (like methods)
                    if isinstance(node.value, ast.Attribute):
                        return True

            return False

        except (IndentationError, SyntaxError) as e:
            logger.warning(f"Could not parse function {func.__name__}: {str(e)}")
            return False