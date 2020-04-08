# About URI filtering

This feature causes *Isso* to accept or reject comments based on URI of a page a new comment is supposed to belong to. This is done by mentioning a pattern in `[guard]` section of the server config file in a field named `uri-filter`. You should set an unqueted [Python regex](https://docs.python.org/3/library/re.html) string.

## Examples

* To accept comments for a single page under `/path/to/index.html` and reject others, use:
```ini
[guard]
enabled = true
uri-filter = /path/to/index\.html
```

* Use this config to accept comments for a page under `/path/to/article/`, which also can be retreived under `/path/to/article/index.html`:

```
[guard]
enabled = true
uri-filter = /path/to/article/(index\.html)?
``` 

* To accept URI's only with common path `/articles/` or `/news/`, use this:

```ini
[guard]
enabled = true
uri-filter = /(articles|news)/.+
```

* This configuration causes isso to accept comments for `/posts/2019-01-01/*` through `/posts/2019-12-30/*` and reject anything else:

```ini
[guard]
enabled = true
uri-filter = /posts/2019-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|30|31)/.+
```
