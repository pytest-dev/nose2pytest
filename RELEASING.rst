Here are the steps on how to make a new release.

1. Create a ``release-VERSION`` branch from ``upstream/master``.
2. Install ``bumpversion`` and execute:

   ::

    bumpversion minor --new-version 1.0.11

   Changing ``minor`` and ``--new-version`` above accordingly.

3. Push a branch with the changes.
4. Once all builds pass and at least another maintainer approves, push a tag to ``upstream`` in the format ``v1.0.11`.
   This will deploy to PyPI.
5. Merge the PR (do not squash, to keep the tag).
6. Create a new release on GitHub, posting the contents of the current CHANGELOG.
7. Open a new PR clearing the ``CHANGELOG.md`` file.
