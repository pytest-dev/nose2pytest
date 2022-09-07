## Upgrade Python tests from nose to purest by running nose2pytest on Python 3.6 on Docker
### Assumptions
* The code that you want to upgrade is in a GitHub repo and you have your own fork.
* https://pypi.org/project/nose2pytest has not yet been updated to work on versions of Python > 3.6.
* You do not have Python 3.6 installed locally and you do not wish to install an unsupported version of Python.
### Approach
* Run nose2pytest on Python 3.6 on Docker to get the conversion pull request started and then finish the PR outside of Docker
### Steps
1. Go to the GitHub repo and sync your fork’s default branch to upstream’s default branch.
2. Get a GitHub Personal Access Token
    * https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
3. Open TWO terminal tabs: One for your local system and the other for a Docker-based system
4. In the Docker tab in your terminal…
5. `docker run --rm -it python:3.6 bash`
6. `python —version`  # Ensure that you are on Python 3.6.15.
7. `git config --global user.email "you@example.com"`
8. `git config --global user.name "Your Name"`
9. `git clone https://github.com/my_github_id/repo_name`
10. `cd repo_name`
11. `git remote add upstream  https://github.com/upstream_github_id/repo_name`
12. `git checkout -b nose2pytest`
13. `pip install --upgrade pip`
14. `pip install nose2pytest`
15. `nose2pytest .`
16. `git diff --name-only`  # Ensure that some files were modified.
17. `git commit -am"nose2pytest: Upgrade Python testing from nose to pytest"`
18. `git push --set-upstream origin nose2pytest`
    1. `Username for 'https://github.com':` you@example.com
    2. `Password for 'https://you@example.com@github.com':` your GitHub PAT from step 2.
    3. Follow the URL and create the pull request on GitHub
19. Switch to the local system tab in your terminal…
20. Repeat steps 9, 10, and 11 on your local system (if you have not already done so).
21. `git fetch`
22. `git checkout nose2pytest`
23. `git grep nose`

To finish the process you will need to manually change instances of `nose` to `pytest`.
* Remove `from nose.tools import assert_equal` because `pytest` uses Python’s builtin assert
* Modify `nose.tools.assert_raises` to `pytest.raises` but carefully because they are not equivalent
* Change any pip-related files to install `pytest` instead of `nose`
* Change GitHub Actions, Makefile, tox, etc. to run `pytest` instead of `nose`
