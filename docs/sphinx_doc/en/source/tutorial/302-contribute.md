(302-contribute-en)=

# Contribute to AgentScope

Our community thrives on the diverse ideas and contributions of its members. Whether you're fixing a bug, adding a new feature, improving the documentation,  or adding examples, your help is welcome. Here's how you can contribute:

## Report Bugs and Ask For New Features?

Did you find a bug or have a feature request? Please first check the issue tracker to see if it has already been reported. If not, feel free to open a new issue. Include as much detail as possible:

- A descriptive title
- Clear description of the issue
- Steps to reproduce the problem
- Version of the AgentScope you are using
- Any relevant code snippets or error messages

## Contribute to Codebase

### Fork and Clone the Repository

To work on an issue or a new feature, start by forking the AgentScope repository and then cloning your fork locally.

```bash
git clone https://github.com/your-username/AgentScope.git
cd AgentScope
```

### Create a New Branch

Create a new branch for your work. This helps keep proposed changes organized and separate from the `main` branch.

```bash
git checkout -b your-feature-branch-name
```

### Making Changes

With your new branch checked out, you can now make your changes to the code. Remember to keep your changes as focused as possible. If you're addressing multiple issues or features, it's better to create separate branches and pull requests for each.

We provide a developer version with additional `pre-commit` hooks to perform format checks compared to the official version:

```bash
# Install the developer version
pip install -e .[dev]
# Install pre-commit hooks
pre-commit install
```

### Commit Your Changes

Once you've made your changes, it's time to commit them. Write clear and concise commit messages that explain your changes.

```bash
git add -U
git commit -m "A brief description of the changes"
```

You might get some error messages raised by `pre-commit`. Please resolve them according to the error code and commit again.

### Submit a Pull Request

When you're ready for feedback, submit a pull request to the AgentScope `main` branch. In your pull request description, explain the changes you've made and any other relevant context.

We will review your pull request. This process might involve some discussion, additional changes on your part, or both.

### Code Review

Wait for us to review your pull request. We may suggest some changes or improvements. Keep an eye on your GitHub notifications and be responsive to any feedback.

[[Return to the top]](#302-contribute-en)
