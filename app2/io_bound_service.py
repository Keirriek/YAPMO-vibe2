"""Centrale service voor io_bound taken volgens NiceGUI documentatie."""

from collections.abc import Callable

from nicegui import run


class IOBoundService:
    """Centrale service voor het uitvoeren van io_bound taken."""

    def __init__(self) -> None:
        """Initialize the I/O bound service."""
        self.running_tasks: dict[str, bool] = {}
        self.task_results: dict[str, object] = {}
        self.task_callbacks: dict[str, Callable] = {}

    async def run_task(
        self,
        task_name: str,
        task_func: Callable,
        *args: object,
        callback: Callable | None = None,
        **kwargs: object,
    ) -> None:
        """Voer een io_bound taak uit.

        Args:
        ----
            task_name: Unieke naam voor de taak
            task_func: Functie die uitgevoerd moet worden
            callback: Callback functie die aangeroepen wordt na voltooiing
            *args: Positionele argumenten voor task_func
            **kwargs: Keyword argumenten voor task_func

        """
        if self.running_tasks.get(task_name):
            return  # Taak draait al

        self.running_tasks[task_name] = True
        if callback:
            self.task_callbacks[task_name] = callback

        try:
            # Voer de taak uit met run.io_bound
            result = await run.io_bound(task_func, *args, **kwargs)
            self.task_results[task_name] = result

            # Roep callback aan als die bestaat
            if callback:
                await callback(result)

        except (OSError, ValueError, RuntimeError) as e:
            # Handle I/O and other errors
            self.task_results[task_name] = {"error": str(e)}
            if callback:
                await callback({"error": str(e)})
        finally:
            self.running_tasks[task_name] = False

    def is_task_running(self, task_name: str) -> bool:
        """Check of een taak nog draait."""
        return self.running_tasks.get(task_name, False)

    def stop_task(self, task_name: str) -> None:
        """Stop een taak (voor toekomstige implementatie)."""
        self.running_tasks[task_name] = False

    def get_task_result(self, task_name: str) -> object:  # type: ignore[return-value]
        """Haal het resultaat van een taak op."""
        return self.task_results.get(task_name)

    def clear_task_result(self, task_name: str) -> None:
        """Verwijder het resultaat van een taak."""
        if task_name in self.task_results:
            del self.task_results[task_name]


# Globale instantie
io_bound_service = IOBoundService()
