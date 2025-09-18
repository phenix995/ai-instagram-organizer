# Contributing to AI Instagram Organizer

Thank you for your interest in contributing to the AI Instagram Organizer project! We welcome contributions from the community.

## How to Contribute

### 1. Reporting Issues

- Use the GitHub issue tracker to report bugs or request features
- Provide detailed information including:
  - Steps to reproduce the issue
  - Expected vs. actual behavior
  - Your environment (OS, Python version, AI provider used)
  - Error messages and logs

### 2. Feature Requests

- Check existing issues first to avoid duplicates
- Clearly describe the feature and its use case
- Include mockups or examples if applicable

### 3. Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Commit your changes**: `git commit -m "Add feature: your feature description"`
7. **Push to your fork**: `git push origin feature/your-feature-name`
8. **Create a Pull Request**

### 4. Documentation

- Update README.md for significant changes
- Add docstrings to new functions
- Update this CONTRIBUTING.md if contribution guidelines change

## Development Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/ai-instagram-organizer.git
   cd ai-instagram-organizer
   ```

2. **Install dependencies**:

   ```bash
   pip install pillow imagehash pillow-heif requests
   # Optional for advanced features
   pip install matplotlib seaborn opencv-python
   ```

3. **Run tests**:

   ```bash
   python -m pytest tests/
   ```

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use 4 spaces for indentation
- Use descriptive variable and function names
- Add docstrings to all functions and classes
- Keep line length under 88 characters

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove)
- Reference issue numbers when applicable: `Fix #123: Handle edge case in photo analysis`

### Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting PR
- Test with different AI providers when applicable
- Include integration tests for API interactions

## Areas for Contribution

### High Priority

- Additional AI provider support
- Performance optimizations
- Better error handling and logging
- Enhanced image processing algorithms

### Medium Priority

- More social media platform integrations
- Advanced analytics and reporting
- Mobile app companion
- Web-based interface

### Low Priority

- Plugin system for custom features
- Localization (i18n) support
- Docker containerization
- CI/CD pipeline improvements

## Code Review Process

1. All PRs require review from at least one maintainer
2. Reviewers will check for:
   - Code quality and style
   - Test coverage
   - Documentation updates
   - Breaking changes
3. Address review feedback and push updates
4. Once approved, a maintainer will merge your PR

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Questions?

Feel free to reach out by opening an issue or joining our community discussions!

Thank you for contributing to AI Instagram Organizer! 🎉
