"""AWS Secrets Manager integration for the environment library."""

import os
from datetime import datetime

from shared.aws import fetch_aws_secret
from http_py.logging.logging import create_logger
from http_py.environment.manager import EnvironmentManager


logger = create_logger(__name__)


def load_aws_env(manager: EnvironmentManager) -> None:  # type: ignore[type-arg]
    """Fetch secrets from AWS Secrets Manager and load them into *manager*.

    Reads ``AWS_REGION`` and ``ENVIRONMENT_SECRET_NAME`` from
    ``os.environ``, fetches the corresponding secrets, and calls
    :meth:`EnvironmentManager.load` with the merged result.

    The manager's ``mandatory_keys`` (configured at
    :func:`~http_py.environment.create_environment` time) are validated
    automatically by :meth:`~EnvironmentManager.load`.

    Args:
        manager: The :class:`EnvironmentManager` instance to populate.

    Raises:
        ValueError: If required env vars or secret keys are missing.
    """
    ref = "load_aws_env:"

    aws_region = os.getenv("AWS_REGION", None)
    if aws_region is None:
        msg = f"{ref} ValueError: AWS_REGION required"
        logger.error(msg)
        raise ValueError(msg)

    environment_secret_name = os.getenv("ENVIRONMENT_SECRET_NAME", None)
    if environment_secret_name is None:
        msg = f"{ref} ValueError: ENVIRONMENT_SECRET_NAME required"
        logger.error(msg)
        raise ValueError(msg)

    secret_values = fetch_aws_secret(environment_secret_name, aws_region)
    if "SECRETS_SECRET_NAME" not in secret_values:
        msg = f"{ref} ValueError: SECRETS_SECRET_NAME not found in secrets"
        logger.error(msg)
        raise ValueError(msg)

    secrets = fetch_aws_secret(secret_values["SECRETS_SECRET_NAME"], aws_region)
    # Sort multiple keys based on datetime from newest to oldest
    if len(secrets) > 1:
        secrets = {
            k: v
            for k, v in sorted(
                ((str(datetime.fromisoformat(k)), v) for k, v in secrets.items()),
                reverse=True,
            )
        }

    merged_dict_env = {**secret_values, "SECRETS": list(secrets.values())}
    manager.load(merged_dict_env)
