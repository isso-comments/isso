# Isso – a commenting server similar to Disqus

Isso – *Ich schrei sonst* – is a lightweight commenting server written in
Python and JavaScript. It aims to be a drop-in replacement for
[Disqus](http://disqus.com).

## Features

- **Comments written in Markdown**  
  Users can edit or delete own comments (within 15 minutes by default).
  Comments in moderation queue are not publicly visible before activation.
- **SQLite backend**  
  *Because comments are not Big Data.*
- **Disqus & WordPress Import**  
  You can migrate your Disqus/WordPress comments without any hassle.
- **Configurable JS client**  
  Embed a single JS file, 65kB (20kB gzipped) and you are done.

See **[isso-comments.de](https://isso-comments.de/)** for a **live demo**, more
details and [documentation](https://isso-comments.de/docs/).

## Screenshot

![Isso in Action](https://user-images.githubusercontent.com/10212877/167268553-3f30b448-25ff-4850-afef-df2f2e599c93.png)

## Getting started

### Requirements

- Python 3.8+ (+ devel headers)
- SQLite 3.3.8 or later
- a working C compiler

Install Isso from [PyPi](https://pypi.python.org/pypi/isso/):

```console
pip install isso
```

Then, follow the [Quickstart](https://isso-comments.de/docs/guides/quickstart/) guide.

If you're stuck, follow the [Install guide](https://isso-comments.de/docs/reference/installation/),
see [Troubleshooting](https://isso-comments.de/docs/guides/troubleshooting/) and browse
the [the full documentation](https://isso-comments.de/docs/).

## Docker

> [!NOTE]  
> The Docker image tagging scheme for stable releases was changed from `:latest`
> to `:release` as of March 2024
> ([#970](https://github.com/isso-comments/isso/pull/970), [#1012](https://github.com/isso-comments/isso/issues/1012))

A [Docker image](https://github.com/isso-comments/isso/pkgs/container/isso) with
the latest stable release is provided at `ghcr.io/isso-comments/isso:release`,
while `isso:latest` is rebuilt on every push to the `master` branch. See
[Using Docker](https://isso-comments.de/docs/reference/installation/#using-docker).

The maintainers recommend pinning the image to a
[release tag](https://github.com/isso-comments/isso/pkgs/container/isso), e.g.
`isso:0.13.0`.

## Contributing

- Pull requests are very much welcome! These might be
  [good first issues](https://github.com/isso-comments/isso/labels/good-first-issue)
- See [Ways to Contribute](https://isso-comments.de/docs/contributing/)
- [Translate](https://isso-comments.de/docs/contributing/#translations)

### Development

<!-- TODO also mention "Development & Testing" section once new docs uploaded -->
Refer to the docs for
[Installing from Source](https://isso-comments.de/docs/reference/installation/#install-from-source).

### Help

- Join `#isso` via IRC on [Libera.Chat](https://libera.chat/)
- Ask a question on [GitHub Discussions](https://github.com/isso-comments/isso/discussions).

## License

MIT, see [LICENSE](LICENSE).
