Environment Variables
=====================

Typed environment variable reads with defaults, validation, and config file
fallback.

The problem
-----------

In raw Behave, reading environment variables is verbose and error-prone:

.. code-block:: python

   import os

   api_key = os.environ.get("API_KEY")
   if api_key is None:
       raise ValueError("API_KEY is not set")

   timeout_str = os.environ.get("TIMEOUT", "30")
   try:
       timeout = int(timeout_str)
   except ValueError:
       raise ValueError(f"TIMEOUT must be an integer, got '{timeout_str}'")

   debug = os.environ.get("DEBUG", "false").lower() in ("true", "1", "yes")

The solution
------------

.. code-block:: python

   from behave_kit import env

   api_key = env("API_KEY", required=True)               # str, raises if missing
   timeout = env("TIMEOUT", var_type=int, default=30)     # int with default
   debug = env("DEBUG", var_type=bool, default=False)     # bool conversion

API reference
-------------

.. autofunction:: behave_kit.env.variables.env

Examples
--------

Required variables
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import env

   @given("I have an API key")
   def step(context):
       context.api_key = env("API_KEY", required=True)
       # Raises EnvVarError if API_KEY is not set

With defaults
~~~~~~~~~~~~~

.. code-block:: python

   @given("I have a timeout setting")
   def step(context):
       context.timeout = env("TIMEOUT", var_type=int, default=30)

Type conversion
~~~~~~~~~~~~~~~

.. code-block:: python

   # String (default)
   api_key = env("API_KEY")

   # Integer
   port = env("PORT", var_type=int, default=8080)

   # Boolean — accepts: true/false, 1/0, yes/no, on/off (case-insensitive)
   debug = env("DEBUG", var_type=bool, default=False)

   # Float
   threshold = env("THRESHOLD", var_type=float, default=0.5)

Reading from context config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When `setup()` is called with ``env="staging"``, the `env()` function also
checks `context.config` for values defined in `behave.toml`:

.. code-block:: python

   # behave.toml
   [env.default]
   base_url = "http://localhost:8000"

   [env.staging]
   base_url = "https://staging.example.com"

   # steps.py
   @given("I have the base URL")
   def step(context):
       context.base_url = env("base_url", default="http://localhost:8000")
       # Reads from context.config when env var is not set

dotenv support
~~~~~~~~~~~~~~

When the `dotenv` extra is installed (``pip install behave-kit[dotenv]``),
`env()` automatically loads variables from a `.env` file in the project root:

.. code-block:: bash

   pip install "behave-kit[dotenv]"

.. code-block:: bash

   # .env
   API_KEY=secret-key
   DEBUG=true

Error handling
~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import env
   from behave_kit._core.errors import EnvVarError

   try:
       value = env("MISSING_VAR", required=True)
   except EnvVarError as exc:
       print(f"Variable not set: {exc}")
       # "Variable not set: Environment variable 'MISSING_VAR' is required but not set"

Configuration files
-------------------

.. autofunction:: behave_kit.env.config.load_env_config

.. autoclass:: behave_kit._core.config.KitConfig
   :members:

Profile selection
~~~~~~~~~~~~~~~~~

.. autofunction:: behave_kit.env.profiles.select_profile

.. autofunction:: behave_kit.env.profiles.apply_overrides

Example `behave.toml`:

.. code-block:: toml

   [env.default]
   base_url = "http://localhost:8000"
   timeout = "30"

   [env.staging]
   base_url = "https://staging.example.com"
   timeout = "10"

   [env.production]
   base_url = "https://api.example.com"
   timeout = "5"
