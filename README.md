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

See **[posativ.org/isso](http://posativ.org/isso/)** for a **live demo**, more
details and [documentation](https://posativ.org/isso/docs/).

## Screenshot

![Isso in Action](https://user-images.githubusercontent.com/10212877/167268553-3f30b448-25ff-4850-afef-df2f2e599c93.png)

## Geting started

**Requirements**
- Python 3.6+ (+ devel headers)
- SQLite 3.3.8 or later
- a working C compiler

Install Isso from [PyPi](https://pypi.python.org/pypi/isso/):

```console
pip install isso
```

Then, follow the [Quickstart](https://posativ.org/isso/docs/quickstart/) guide.

If you're stuck, follow the [Install guide](https://posativ.org/isso/docs/install/),
see [Troubleshooting](https://posativ.org/isso/docs/troubleshooting/) and browse
the [the full documentation](https://posativ.org/isso/docs/).

## Contributing
- Pull requests are very much welcome! These might be
  [good first issues](https://github.com/posativ/isso/labels/good-first-issue)
- See [Ways to Contribute](https://posativ.org/isso/contribute/)
- [Translate](https://posativ.org/isso/contribute/#translations)

### Development
<!-- TODO also mention "Development & Testing" section once new docs uploaded -->
Refer to the docs for
[Installing from Source](https://posativ.org/isso/docs/install/#install-from-source).

### Help
- Join `#isso` via [Matrix](https://matrix.to/#/#isso:libera.chat) or via IRC on
  [Libera.Chat](https://libera.chat/)
- Ask a question on [GitHub Discussions](https://github.com/posativ/isso/discussions).

## License
MIT, see [LICENSE](LICENSE).
