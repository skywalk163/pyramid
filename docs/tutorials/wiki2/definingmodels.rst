.. _wiki2_defining_the_domain_model:

=========================
Defining the Domain Model
=========================

The first change we'll make to our stock cookiecutter-generated application will
be to define a wiki page :term:`domain model`.

.. note::

  There is nothing special about the filename ``user.py`` or ``page.py`` except
  that they are Python modules.  A project may have many models throughout its
  codebase in arbitrarily named modules.  Modules implementing models often
  have ``model`` in their names or they may live in a Python subpackage of
  your application package named ``models`` (as we've done in this tutorial),
  but this is only a convention and not a requirement.


Declaring dependencies in our ``setup.py`` file
===============================================

The models code in our application will depend on a package which is not a
dependency of the original "tutorial" application.  The original "tutorial"
application was generated by the cookiecutter; it doesn't know about our
custom application requirements.

We need to add a dependency, the `bcrypt <https://pypi.org/project/bcrypt/>`_ package, to our ``tutorial``
package's ``setup.py`` file by assigning this dependency to the ``requires``
parameter in the ``setup()`` function.

Open ``tutorial/setup.py`` and edit it to look like the following:

.. literalinclude:: src/models/setup.py
    :linenos:
    :emphasize-lines: 13
    :language: python

Only the highlighted line needs to be added.

.. note::

    We are using the ``bcrypt`` package from PyPI to hash our passwords securely. There are other one-way hash algorithms for passwords if ``bcrypt`` is an issue on your system. Just make sure that it's an algorithm approved for storing passwords versus a generic one-way hash.


Running ``pip install -e .``
============================

Since a new software dependency was added, you will need to run ``pip install
-e .`` again inside the root of the ``tutorial`` package to obtain and register
the newly added dependency distribution.

Make sure your current working directory is the root of the project (the
directory in which ``setup.py`` lives) and execute the following command.

On Unix:

.. code-block:: bash

    $VENV/bin/pip install -e .

On Windows:

.. code-block:: doscon

    %VENV%\Scripts\pip install -e .

Success executing this command will end with a line to the console something
like the following.

.. code-block:: text

    Successfully installed bcrypt-3.1.4 cffi-1.11.5 pycparser-2.18 tutorial


Remove ``mymodel.py``
=====================

Let's delete the file ``tutorial/models/mymodel.py``. The ``MyModel`` class is
only a sample and we're not going to use it.


Add ``user.py``
===============

Create a new file ``tutorial/models/user.py`` with the following contents:

.. literalinclude:: src/models/tutorial/models/user.py
    :linenos:
    :language: py

This is a very basic model for a user who can authenticate with our wiki.

We discussed briefly in the previous chapter that our models will inherit from
an SQLAlchemy :func:`sqlalchemy.ext.declarative.declarative_base`. This will
attach the model to our schema.

As you can see, our ``User`` class has a class-level attribute
``__tablename__`` which equals the string ``users``. Our ``User`` class will
also have class-level attributes named ``id``, ``name``, ``password_hash``,
and ``role`` (all instances of :class:`sqlalchemy.schema.Column`). These will
map to columns in the ``users`` table. The ``id`` attribute will be the primary
key in the table. The ``name`` attribute will be a text column, each value of
which needs to be unique within the column. The ``password_hash`` is a nullable
text attribute that will contain a securely hashed password. Finally, the
``role`` text attribute will hold the role of the user.

There are two helper methods that will help us later when using the user
objects. The first is ``set_password`` which will take a raw password and
transform it using ``bcrypt`` into an irreversible representation, a process known
as "hashing". The second method, ``check_password``, will allow us to compare
the hashed value of the submitted password against the hashed value of the
password stored in the user's record in the database. If the two hashed values
match, then the submitted password is valid, and we can authenticate the user.

We hash passwords so that it is impossible to decrypt them and use them to
authenticate in the application. If we stored passwords foolishly in clear
text, then anyone with access to the database could retrieve any password to
authenticate as any user.


Add ``page.py``
===============

Create a new file ``tutorial/models/page.py`` with the following contents:

.. literalinclude:: src/models/tutorial/models/page.py
    :linenos:
    :language: py

As you can see, our ``Page`` class is very similar to the ``User`` defined
above, except with attributes focused on storing information about a wiki page,
including ``id``, ``name``, and ``data``. The only new construct introduced
here is the ``creator_id`` column, which is a foreign key referencing the
``users`` table. Foreign keys are very useful at the schema-level, but since we
want to relate ``User`` objects with ``Page`` objects, we also define a
``creator`` attribute as an ORM-level mapping between the two tables.
SQLAlchemy will automatically populate this value using the foreign key
referencing the user. Since the foreign key has ``nullable=False``, we are
guaranteed that an instance of ``page`` will have a corresponding
``page.creator``, which will be a ``User`` instance.


Edit ``models/__init__.py``
===========================

Since we are using a package for our models, we also need to update our
``__init__.py`` file to ensure that the models are attached to the metadata.

Open the ``tutorial/models/__init__.py`` file and edit it to look like
the following:

.. literalinclude:: src/models/tutorial/models/__init__.py
    :linenos:
    :language: py
    :emphasize-lines: 8,9

Here we align our imports with the names of the models, ``Page`` and ``User``.


.. _wiki2_migrate_database_alembic:

Migrate the database with Alembic
=================================

Now that we have written our models, we need to modify the database schema to reflect the changes to our code. Let's generate a new revision, then upgrade the database to the latest revision (head).

On Unix:

.. code-block:: bash

    $VENV/bin/alembic -c development.ini revision --autogenerate \
        -m "use new models Page and User"
    $VENV/bin/alembic -c development.ini upgrade head

On Windows:

.. code-block:: doscon

    %VENV%\Scripts\alembic -c development.ini revision \
        --autogenerate -m "use new models Page and User"
    %VENV%\Scripts\alembic -c development.ini upgrade head

Success executing these commands will generate output similar to the following.

.. code-block:: text

    2018-06-29 01:28:42,407 INFO  [sqlalchemy.engine.base.Engine:1254][MainThread] SELECT CAST('test plain returns' AS VARCHAR(60)) AS anon_1
    2018-06-29 01:28:42,407 INFO  [sqlalchemy.engine.base.Engine:1255][MainThread] ()
    2018-06-29 01:28:42,408 INFO  [sqlalchemy.engine.base.Engine:1254][MainThread] SELECT CAST('test unicode returns' AS VARCHAR(60)) AS anon_1
    2018-06-29 01:28:42,408 INFO  [sqlalchemy.engine.base.Engine:1255][MainThread] ()
    2018-06-29 01:28:42,409 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA table_info("alembic_version")
    2018-06-29 01:28:42,409 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,410 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] SELECT alembic_version.version_num
    FROM alembic_version
    2018-06-29 01:28:42,410 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,411 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
    2018-06-29 01:28:42,412 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,413 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA table_info("models")
    2018-06-29 01:28:42,413 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,414 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] SELECT sql FROM  (SELECT * FROM sqlite_master UNION ALL   SELECT * FROM sqlite_temp_master) WHERE name = 'models' AND type = 'table'
    2018-06-29 01:28:42,414 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,414 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA foreign_key_list("models")
    2018-06-29 01:28:42,414 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,414 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] SELECT sql FROM  (SELECT * FROM sqlite_master UNION ALL   SELECT * FROM sqlite_temp_master) WHERE name = 'models' AND type = 'table'
    2018-06-29 01:28:42,415 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,416 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA index_list("models")
    2018-06-29 01:28:42,416 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,416 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA index_info("my_index")
    2018-06-29 01:28:42,416 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,417 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA index_list("models")
    2018-06-29 01:28:42,417 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,417 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA index_info("my_index")
    2018-06-29 01:28:42,417 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:28:42,417 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] SELECT sql FROM  (SELECT * FROM sqlite_master UNION ALL   SELECT * FROM sqlite_temp_master) WHERE name = 'models' AND type = 'table'
    2018-06-29 01:28:42,417 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
      Generating /<somepath>/tutorial/tutorial/alembic/versions/20180629_23e9f8eb6c28.py ... done

.. code-block:: text

    2018-06-29 01:29:37,957 INFO  [sqlalchemy.engine.base.Engine:1254][MainThread] SELECT CAST('test plain returns' AS VARCHAR(60)) AS anon_1
    2018-06-29 01:29:37,958 INFO  [sqlalchemy.engine.base.Engine:1255][MainThread] ()
    2018-06-29 01:29:37,958 INFO  [sqlalchemy.engine.base.Engine:1254][MainThread] SELECT CAST('test unicode returns' AS VARCHAR(60)) AS anon_1
    2018-06-29 01:29:37,958 INFO  [sqlalchemy.engine.base.Engine:1255][MainThread] ()
    2018-06-29 01:29:37,960 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] PRAGMA table_info("alembic_version")
    2018-06-29 01:29:37,960 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:29:37,960 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] SELECT alembic_version.version_num
    FROM alembic_version
    2018-06-29 01:29:37,960 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:29:37,963 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread]
    CREATE TABLE users (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT,
            CONSTRAINT pk_users PRIMARY KEY (id),
            CONSTRAINT uq_users_name UNIQUE (name)
    )


    2018-06-29 01:29:37,963 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:29:37,966 INFO  [sqlalchemy.engine.base.Engine:722][MainThread] COMMIT
    2018-06-29 01:29:37,968 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread]
    CREATE TABLE pages (
            id INTEGER NOT NULL,
            name TEXT NOT NULL,
            data TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            CONSTRAINT pk_pages PRIMARY KEY (id),
            CONSTRAINT fk_pages_creator_id_users FOREIGN KEY(creator_id) REFERENCES users (id),
            CONSTRAINT uq_pages_name UNIQUE (name)
    )


    2018-06-29 01:29:37,968 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:29:37,969 INFO  [sqlalchemy.engine.base.Engine:722][MainThread] COMMIT
    2018-06-29 01:29:37,969 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread]
    DROP INDEX my_index
    2018-06-29 01:29:37,969 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:29:37,970 INFO  [sqlalchemy.engine.base.Engine:722][MainThread] COMMIT
    2018-06-29 01:29:37,970 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread]
    DROP TABLE models
    2018-06-29 01:29:37,970 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:29:37,971 INFO  [sqlalchemy.engine.base.Engine:722][MainThread] COMMIT
    2018-06-29 01:29:37,972 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] UPDATE alembic_version SET version_num='23e9f8eb6c28' WHERE alembic_version.version_num = 'b6b22ae3e628'
    2018-06-29 01:29:37,972 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ()
    2018-06-29 01:29:37,972 INFO  [sqlalchemy.engine.base.Engine:722][MainThread] COMMIT


.. _wiki2_alembic_overview:

Alembic overview
----------------

Let's briefly discuss our configuration for Alembic.

In the alchemy cookiecutter's ``development.ini`` file, the setting for ``script_location`` configures Alembic to look for the migration script in the directory ``tutorial/alembic``.
By default Alembic stores the migration files one level deeper in ``tutorial/alembic/versions``.
These files are generated by Alembic, then executed when we run upgrade or downgrade migrations.
The setting ``file_template`` provides the format for each migration's file name.
We've configured the ``file_template`` setting to make it somewhat easy to find migrations by file name.

At this point in this tutorial, we have two migration files.
Examine them to see what Alembic will do when you upgrade or downgrade the database to a specific revision.
Notice the revision identifiers and how they relate to one another in a chained sequence.

.. seealso:: For further information, see the `Alembic documentation <http://alembic.zzzcomputing.com/en/latest/>`_.


Edit ``scripts/initialize_db.py``
=================================

We haven't looked at the details of this file yet, but within the ``scripts``
directory of your ``tutorial`` package is a file named ``initialize_db.py``.
Code in this file is executed whenever we run the ``initialize_tutorial_db``
command, as we did in the installation step of this tutorial.

.. note::

    The command is named ``initialize_tutorial_db`` because of the mapping defined in the ``[console_scripts]`` entry point of our project's ``setup.py`` file.

Since we've changed our model, we need to make changes to our
``initialize_db.py`` script.  In particular, we'll replace our import of
``MyModel`` with those of ``User`` and ``Page``. We'll also change the the script to create two ``User`` objects (``basic`` and ``editor``) as well
as a ``Page``, rather than a ``MyModel``, and add them to our ``dbsession``.

Open ``tutorial/scripts/initialize_db.py`` and edit it to look like the
following:

.. literalinclude:: src/models/tutorial/scripts/initialize_db.py
    :linenos:
    :language: python
    :emphasize-lines: 11-24

Only the highlighted lines need to be changed.


Populating the database
=======================

Because our model has changed, and to repopulate the database, we
need to rerun the ``initialize_tutorial_db`` command to pick up the changes
we've made to the initialize_db.py file. See :ref:`initialize_db_wiki2` for instructions.

Success will look something like this:

.. code-block:: text

    2018-06-29 01:30:39,326 INFO  [sqlalchemy.engine.base.Engine:1254][MainThread] SELECT CAST('test plain returns' AS VARCHAR(60)) AS anon_1
    2018-06-29 01:30:39,326 INFO  [sqlalchemy.engine.base.Engine:1255][MainThread] ()
    2018-06-29 01:30:39,327 INFO  [sqlalchemy.engine.base.Engine:1254][MainThread] SELECT CAST('test unicode returns' AS VARCHAR(60)) AS anon_1
    2018-06-29 01:30:39,327 INFO  [sqlalchemy.engine.base.Engine:1255][MainThread] ()
    2018-06-29 01:30:39,328 INFO  [sqlalchemy.engine.base.Engine:682][MainThread] BEGIN (implicit)
    2018-06-29 01:30:39,329 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] INSERT INTO users (name, role, password_hash) VALUES (?, ?, ?)
    2018-06-29 01:30:39,329 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ('editor', 'editor', '$2b$12$PlaJSN7goVbyx8OFs8yAju9n5gHGdI6PZ2QRJGM2jDCiEU4ItUNxy')
    2018-06-29 01:30:39,330 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] INSERT INTO users (name, role, password_hash) VALUES (?, ?, ?)
    2018-06-29 01:30:39,330 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ('basic', 'basic', '$2b$12$MvXdM8jlkbjEyPZ6uXzRg.yatZZK8jCwfPaM7kFkmVJiJjRoCCvmW')
    2018-06-29 01:30:39,331 INFO  [sqlalchemy.engine.base.Engine:1151][MainThread] INSERT INTO pages (name, data, creator_id) VALUES (?, ?, ?)
    2018-06-29 01:30:39,331 INFO  [sqlalchemy.engine.base.Engine:1154][MainThread] ('FrontPage', 'This is the front page', 1)
    2018-06-29 01:30:39,332 INFO  [sqlalchemy.engine.base.Engine:722][MainThread] COMMIT


View the application in a browser
=================================

We can't.  At this point, our system is in a "non-runnable" state; we'll need
to change view-related files in the next chapter to be able to start the
application successfully.  If you try to start the application (see
:ref:`wiki2-start-the-application`) and visit http://localhost:6543, you'll wind up with a Python traceback on
your console that ends with this exception:

.. code-block:: text

    AttributeError: module 'tutorial.models' has no attribute 'MyModel'

This will also happen if you attempt to run the tests.
