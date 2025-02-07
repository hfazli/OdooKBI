from typing import Any, List


class OdooModelWrapper:
    """
    Wraps Odoo Model object and allows to invoke 'search', 'search_count' and 'search_read' methods
    with a predefined base domain expression.
    """

    def __init__(self, model: Any, base_domain=None):
        self._model = model
        self._base_domain = base_domain

    def __iter__(self):
        return iter(self._model)

    def __getattr__(self, item):
        return getattr(self._model, item)

    def search(self, domain=None, *args, **kwargs) -> Any:
        combined_domain = self._base_domain + (domain or [])
        return self._model.search(combined_domain, *args, **kwargs)

    def search_count(self, domain=None, *args, **kwargs) -> int:
        combined_domain = self._base_domain + (domain or [])
        return self._model.search_count(combined_domain, *args, **kwargs)

    def search_read(self, domain=None, *args, **kwargs) -> List:
        combined_domain = self._base_domain + (domain or [])
        return self._model.search_read(combined_domain, *args, **kwargs)
