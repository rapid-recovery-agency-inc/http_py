import os
import json
import inspect
from enum import Enum
from typing import Any, cast, Literal, NamedTuple, get_type_hints
from datetime import datetime

from dotenv import load_dotenv

from shared.aws import fetch_aws_secret
from modules.types import BooleanString, to_boolean_string
from modules.logging.logging import create_logger
from shared.address_tagging.types import TextTransformation


logger = create_logger(__name__)

load_dotenv()

AwsIntendedUse = Literal["SingleUse", "Storage"]
__MANDATORY_KEYS = [
    "SECRETS",
]


class Environment(NamedTuple):
    AWS_REGION: str = ""
    ENVIRONMENT_SECRET_NAME: str = ""
    SECRETS_SECRET_NAME: str = ""
    LOG_LEVEL: str = ""
    SECRETS: list[str] = []
    CORS_ORIGINS: list[str] = []
    URL_API: str = ""
    HMAC_SIGNATURE_HEADER_NAME: str = ""
    GOOGLE_API_KEY: str = ""
    LOCATIONIQ_API_KEY: str = ""
    MAPBOX_ACCESS_TOKEN: str = ""
    MAPBOX_STATIC_MAP_BASE_URL: str = ""
    MAPBOX_STATIC_MAP_DEFAULT_STYLE: str = ""
    DB_READER_HOSTS: str = ""
    DB_PASSWORD: str = ""
    DB_PORT: str = ""
    DB_USERNAME: str = ""
    DB_WRITER_HOST: str = ""
    DB_NAME: str = ""
    DB_POOL_TIMEOUT: int = 30
    DB_MIN_POOL_SIZE: int = 1
    DB_MAX_POOL_SIZE: int = 5000
    DB_POOL_MAX_IDLE_TIME_SECONDS: int = 5
    DISABLE_HMAC: bool = False
    DISABLE_RATE_LIMITER: bool = False
    DEBUG: bool = False
    USER_AGENT: str = "insightt-io/address-microservice"
    ADDRESS_CACHE_TTL_SECONDS: int = 157784760  # 5 years in seconds
    ADDRESS_CACHE_REV_GEOCODE_PROXIMITY_METERS: int = 15
    TRANSFORM_DIRECTIONALS: TextTransformation = TextTransformation.CONTRACT
    TRANSFORM_STREET_TYPES: TextTransformation = TextTransformation.CONTRACT
    TRANSFORM_OCCUPANCY: TextTransformation = TextTransformation.CONTRACT
    TRANSFORM_COUNTY: TextTransformation = TextTransformation.CONTRACT
    TRANSFORM_STATE: TextTransformation = TextTransformation.CONTRACT
    TRANSFORM_COUNTRY: TextTransformation = TextTransformation.CONTRACT
    REVERSE_GEOCODE_DISTANCE_METERS: int = 5
    TEST_DATABASE_URL: str = ""
    AWS_INTENDED_USE: str = "SingleUse"
    MAPBOX_PERMANENT: BooleanString = "false"
    HTTP_LOGGING: bool = False


def __convert_to_expected_type(expected_type: type, value: Any) -> Any:  # noqa: PLR0912, PLR0911, C901
    """Converts a string value to the expected type. Useful in coercing AWS Secrets
    Manager values to the expected type in the local Environment object.

    Args:
    ----
        expected_type (Union[type, Enum]): The expected type to convert the value to.
        value (str): The string value to convert.

    Returns:
    -------
        Any: The converted value.

    Raises:
    ------
        ValueError: If the value cannot be converted to the expected type.

    """
    if expected_type is str:
        if isinstance(value, str):
            return value
        return str(value)

    if expected_type is bool:
        if isinstance(value, bool):
            return value
        return value.lower() == "true"

    if expected_type is int:
        return int(value)

    if expected_type is float:
        return float(value)

    if expected_type is list:
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return value.split(",")
        raise ValueError(f"Expected list or str, got {type(value)}")

    if expected_type in (set, tuple):
        if isinstance(value, expected_type):
            return value
        return value.split(",")

    if expected_type is dict:
        return json.loads(value)

    if expected_type == BooleanString:  # type: ignore
        return to_boolean_string(value)

    if inspect.isclass(expected_type):
        if issubclass(expected_type, Enum):
            return expected_type[value]

    return value


def __validate_environment(environment: dict[str, Any]) -> None:
    global __MANDATORY_KEYS  # noqa: PLW0602
    # check for mandatory keys
    missing_keys = [key for key in __MANDATORY_KEYS if key not in environment]
    if len(missing_keys) > 0:
        msg = (
            f"__validate_environment:AWS Secrets is missing keys defined in Environment"
            f" that are MANDATORY: {', '.join(missing_keys)}"
        )
        raise ValueError(msg)


def __to_environment_dict(environment_like: dict[str, str]) -> dict[str, str]:
    valid_fields = set(Environment._fields)
    env_type_hints = get_type_hints(Environment)
    environment_dict: dict[str, str] = {}
    for key in valid_fields:
        maybe_new_value = environment_like.get(key)
        if maybe_new_value is not None:
            expected_type = env_type_hints[key]
            environment_dict[key] = __convert_to_expected_type(
                expected_type,
                maybe_new_value,
            )
    return environment_dict


__local_environment: dict[str, str] = __to_environment_dict(
    cast(dict[str, str], os.environ),
)
__env: dict[str, str] = dict(__local_environment)


def set_environment(new_environment: dict[str, Any]) -> None:
    global __env, __local_environment  # noqa: PLW0602, PLW0603
    new_environment_dict = __to_environment_dict(new_environment)
    merged_environment = new_environment_dict | __local_environment
    # local always takes precedence
    __env = dict(merged_environment)


def load_aws_env() -> None:
    """If load_env() is executed in the FastAPI lifespan context, we ensure that the
    AWS secrets are fetched first, prior to other parts of the application initializing
    and accessing an env that is not fully loaded.
    """
    ref = "environment:load_env:"
    # Environment Secrets

    aws_region = os.getenv("AWS_REGION", None)
    if aws_region is None:
        msg = f"{ref}ValueError: AWS_REGION required"
        logger.error(msg)
        raise ValueError(msg)

    environment_secret_name = os.getenv("ENVIRONMENT_SECRET_NAME", None)
    if environment_secret_name is None:
        msg = f"{ref}ValueError: ENVIRONMENT_SECRET_NAME required"
        logger.error(msg)
        raise ValueError(msg)

    secret_values = fetch_aws_secret(environment_secret_name, aws_region)
    if "SECRETS_SECRET_NAME" not in secret_values:
        msg = f"{ref}ValueError: SECRETS_SECRET_NAME not found in secrets"
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
    __validate_environment(merged_dict_env)
    set_environment(merged_dict_env)


def env() -> Environment:
    global __env, __local_environment  # noqa: PLW0602, PLW0603
    merged_env_dict = {**__env, **__local_environment}
    return Environment(**merged_env_dict)  # type: ignore
