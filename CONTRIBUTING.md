# Contributing to Adaptive Music Box

## How to Contribute

- Fork the repository
- Create a new branch for your feature or bugfix
- Make your changes
- Submit a pull request

## Ways to Contribute

- **Coding Style**: Any functions directly called from user input have no underscore (_), while any functions called solely within another do. Setup functions called once in `__init__()` are preceded by two udnerscores.
- **Compatibility**: Currently only confirmed functional on Windows. Main issues are likely with directory logic and packaging into executable.
- **Tests**: Currently there are no unit tests to ensure functionality. They would make development and testing much easier.