"""Example Prefect flow demonstrating basic workflow orchestration."""

from prefect import flow, task
from prefect.logging import get_run_logger


@task(name="greet", description="Generate a greeting message")
def greet(name: str) -> str:
    """Generate a greeting message.

    Args:
        name: Name to greet

    Returns:
        Greeting message

    """
    logger = get_run_logger()
    message = f"Hello, {name}!"
    logger.info(f"Generated greeting: {message}")
    return message


@task(name="process_data", description="Process data with transformation")
def process_data(data: list[int]) -> list[int]:
    """Process data by doubling each value.

    Args:
        data: List of integers to process

    Returns:
        List of doubled integers

    """
    logger = get_run_logger()
    result = [x * 2 for x in data]
    logger.info(f"Processed {len(data)} items")
    return result


@flow(name="example-workflow", description="Example workflow demonstrating Prefect")
def example_workflow(
    name: str = "World", numbers: list[int] | None = None
) -> dict[str, str | list[int]]:
    """Demonstrate Prefect task orchestration.

    Args:
        name: Name to greet
        numbers: List of numbers to process

    Returns:
        Dictionary containing greeting and processed numbers

    """
    logger = get_run_logger()
    logger.info("Starting example workflow")

    # Execute tasks
    greeting = greet(name)
    processed = process_data(numbers or [1, 2, 3, 4, 5])

    logger.info("Workflow completed successfully")
    return {"greeting": greeting, "processed": processed}


if __name__ == "__main__":
    # Run the flow
    result = example_workflow(name="Prefect User", numbers=[10, 20, 30])
    print(f"Result: {result}")
