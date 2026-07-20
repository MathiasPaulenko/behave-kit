Data Loading
============

Load test data from CSV, JSON, YAML, and Excel files with a single `load_data()`
call.  Includes caching and named data providers.

Supported formats
-----------------

- **CSV** — returns ``list[dict[str, str]]`` (built-in)
- **JSON** — returns the parsed JSON object (built-in)
- **YAML** — returns the parsed YAML object (requires ``[yaml]`` extra)
- **XLSX** — returns ``list[dict[str, str]]`` (requires ``[excel]`` extra)

API reference
-------------

.. autofunction:: behave_kit.data.loader.load_data

.. autofunction:: behave_kit.data.loader.load_examples_from

.. autoclass:: behave_kit.data.cache.DataCache
   :members:

Data providers
--------------

.. autofunction:: behave_kit.data.providers.data_provider

.. autofunction:: behave_kit.data.providers.get_provider

Examples
--------

Loading CSV
~~~~~~~~~~~

Given a file ``tests/data/users.csv``:

.. code-block:: csv

   name,email,age
   Alice,alice@example.com,30
   Bob,bob@example.com,25

.. code-block:: python

   from behave_kit import load_data

   @given("I have a list of users")
   def step(context):
       context.users = load_data("tests/data/users.csv")
       # Returns: [{"name": "Alice", "email": "alice@example.com", "age": "30"},
       #           {"name": "Bob", "email": "bob@example.com", "age": "25"}]

   @then("there should be {count:d} users")
   def step(context, count):
       assert len(context.users) == count

   @then('the first user should be named {name}')
   def step(context, name):
       assert context.users[0]["name"] == name

Loading JSON
~~~~~~~~~~~~

Given a file ``tests/data/config.json``:

.. code-block:: json

   {
     "base_url": "https://api.example.com",
     "timeout": 30,
     "retries": 3
   }

.. code-block:: python

   from behave_kit import load_data

   @given("I have the API config")
   def step(context):
       context.config = load_data("tests/data/config.json")
       # Returns: {"base_url": "https://api.example.com", "timeout": 30, "retries": 3}

   @then('the base URL should be {url}')
   def step(context, url):
       assert context.config["base_url"] == url

Loading YAML
~~~~~~~~~~~~

.. code-block:: bash

   pip install "behave-kit[yaml]"

Given a file ``tests/data/users.yaml``:

.. code-block:: yaml

   - name: Alice
     email: alice@example.com
     age: 30
   - name: Bob
     email: bob@example.com
     age: 25

.. code-block:: python

   from behave_kit import load_data

   @given("I have a list of users from YAML")
   def step(context):
       context.users = load_data("tests/data/users.yaml")

Loading Excel
~~~~~~~~~~~~~

.. code-block:: bash

   pip install "behave-kit[excel]"

.. code-block:: python

   from behave_kit import load_data

   @given("I have a list of users from Excel")
   def step(context):
       context.users = load_data("tests/data/users.xlsx")
       # Returns: list[dict[str, str]] — one dict per row, keys from header row

Using load_examples_from
~~~~~~~~~~~~~~~~~~~~~~~~

Load data and use it as Behave Examples (scenario outlines):

.. code-block:: python

   from behave_kit import load_examples_from

   @given("I have users from CSV as examples")
   def step(context):
       users = load_examples_from("tests/data/users.csv")
       for user in users:
           print(user["name"], user["email"])

Named data providers
~~~~~~~~~~~~~~~~~~~~

Register reusable data factory functions:

.. code-block:: python

   from behave_kit import data_provider, get_provider

   @data_provider("default_user")
   def make_default_user():
       return {"name": "Alice", "email": "alice@example.com", "age": 30}

   @given("I have a default user")
   def step(context):
       create_user = get_provider("default_user")
       context.user = create_user()

   @data_provider("admin_user")
   def make_admin_user():
       return {"name": "Admin", "email": "admin@example.com", "role": "admin"}

   @given("I have an admin user")
   def step(context):
       create_admin = get_provider("admin_user")
       context.user = create_admin()

Caching
~~~~~~~

`DataCache` caches loaded data to avoid re-reading files:

.. code-block:: python

   from behave_kit import DataCache

   cache = DataCache()

   @given("I load users data")
   def step(context):
       context.users = cache.get("tests/data/users.csv")
       # First call reads the file; subsequent calls return cached data

Error handling
~~~~~~~~~~~~~~

.. code-block:: python

   from behave_kit import load_data
   from behave_kit._core.errors import DataError

   try:
       data = load_data("tests/data/missing.csv")
   except DataError as exc:
       print(f"Failed to load: {exc}")

   try:
       data = load_data("tests/data/broken.json")
   except DataError as exc:
       print(f"Invalid JSON: {exc}")
