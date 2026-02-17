import json
from datetime import datetime

from boto3.session import Session
from mypy_boto3_secretsmanager.client import SecretsManagerClient

from http_py.types import AWSEnvironment
from http_py.logging.services import create_logger


logger = create_logger(__name__)


def fetch_aws_secret(secret_name: str, aws_region: str) -> dict[str, str]:
    client: SecretsManagerClient = Session().client(
        "secretsmanager", region_name=aws_region
    )
    try:
        secret_value = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error(f"fetch_aws_secret:error:{secret_name}: {e!s}")
        raise e
    if "SecretString" not in secret_value:
        raise ValueError(f"Secret {secret_name} not found")
    try:
        as_dict: dict[str, str] = json.loads(secret_value["SecretString"])
        return as_dict
    except Exception as e:
        logger.error(f"fetch_aws_secret:Error parsing secret {secret_name}: {e!s}")
        raise e


def load_aws_env(environment: AWSEnvironment) -> dict[str, str]:
    environment_secret_name = environment.ENVIRONMENT_SECRET_NAME
    aws_region = environment.AWS_REGION

    secret_values = fetch_aws_secret(environment_secret_name, aws_region)
    if "SECRETS_SECRET_NAME" not in secret_values:
        msg = "load_aws_env: ValueError: SECRETS_SECRET_NAME not found in secrets"
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

    merged_dict_env: dict[str, str] = {"SECRETS": "".join(list(secrets.values()))}
    for k, v in secret_values.items():
        merged_dict_env[k] = v
    return merged_dict_env
