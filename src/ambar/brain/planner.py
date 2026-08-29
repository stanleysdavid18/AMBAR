class Planner:
    """
    Divide una petición en varias tareas.
    """

    def plan(self, message: str):

        text = message.lower()

        separators = [
            " y luego ",
            " luego ",
            " después ",
            " despues ",
            " y "
        ]

        tasks = [text]

        for separator in separators:

            new_tasks = []

            for task in tasks:
                new_tasks.extend(task.split(separator))

            tasks = new_tasks

        return [
            task.strip()
            for task in tasks
            if task.strip()
        ]