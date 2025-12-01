# Contributing to PDF-to-GraphRAG

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Provide clear description and reproduction steps
- Include system information (OS, Python version, GPU)

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Write tests** for new functionality
5. **Run tests**: `pytest tests/`
6. **Format code**: `black src/ examples/`
7. **Commit**: `git commit -m "Add feature: your feature"`
8. **Push**: `git push origin feature/your-feature`
9. **Submit Pull Request**

### Code Style

- Follow PEP 8 guidelines
- Use Black formatter (line length: 100)
- Add docstrings for all public functions/classes
- Type hints recommended

### Testing

- Write unit tests for new code
- Ensure existing tests pass
- Aim for >80% code coverage

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/pdf-to-graphrag.git
cd pdf-to-graphrag

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Areas for Contribution

### High Priority

- [ ] Additional vector database support (Pinecone, Weaviate)
- [ ] Multi-language support
- [ ] Improved entity extraction prompts
- [ ] Performance optimizations

### Medium Priority

- [ ] Web UI for queries
- [ ] Visualization of knowledge graph
- [ ] Export/import functionality
- [ ] Monitoring dashboard

### Documentation

- [ ] More examples
- [ ] Tutorial videos
- [ ] API documentation improvements
- [ ] Translations

## Questions?

- Open a discussion on GitHub
- Check existing issues
- Review documentation

Thank you for contributing!
