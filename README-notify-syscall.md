
# Send Notifications by arbitrary program via python systemcall

The [*isso*] repository was forked by [github user craigphicks](https://github.com/craigphicks). A branch `notify-syscall-180709` was created.  The branch is described herein.

# Motivation

## Security

When *isso* uses the *SMTP* notification backend, it also sends the username and password.  The are various perspectives from which this could be problematic.

- **Password in clear:**  In the worst case TLS (Transport Layer Security) is not established before passing the password and so the password is transmitted in the clear.

- **Key better than password:**  Even with TLS, the password is still in the clear at either end.  While this is usualloy OK, security can be improved by using a key which can be periodically refreshed.  The point of the key is that is that it is only authorizes a narrow range of actions. Especially, it does not allow loggin in as mail account owner, which could be very damaging.

## Dependence on Python SMTP implementation

*Isso* is tied to the Python SMTP implementation.  Even if SMTP is the desired protocol, the may be other software besides the Python SMTP implementation which gives a better result, e.g. in terms of enabling TLS or working with tokens.

Some examples of alternate software are the multitude of generic sendmail programs, e.g. *sendmail, postfix, exim, nullmailer*, all of which all share the [linux sendmail application interface as a standard](http://refspecs.linux-foundation.org/LSB_3.0.0/LSB-PDA/LSB-PDA/baselib-sendmail-1.html).

Also there utilities such as *curl* and *swaks* which are very flexible with many options. In case something is not working it is almost always possible to work through it with these programs (or change to another program).  Although they are not designed for production use, they are sufficient on the usage scale expected by a typical *isso* installation.

# Solution

## Outline

The *isso* administrator specifies the program and it's arguments in the *isso* configuration file.  When a comment notification event occurs the specified program and arguments are executed via a system call.  The message is passed to the standard input of that program.

## Administrator interface

Add `syscall` to the list of notify backends:

```
[general]
...
notify = stdout, syscall
...
```

Create a section `[syscall]` and therein specify the program and its arguments.  The following example shows `curl` being used to transmit an email request through a (free) Mailgun account:  

```
[syscall]
call = /usr/bin/curl
 --trace-ascii
 /tmp/mg1.log
 --user
 api:key-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
 https://api.mailgun.net/v3/example.com/messages
 -F
 to=risu@gmail.com
 -F
 from=isso@pindertek.com
 -F
 subject=isso {{SUBJECT}}
 -F
 text=<-
```

The key `call` appears on the first line followed by equal.  The value is split brwteen lines with exactly one argument per line.  Each successive value line must have an empty space at the beginning. 
Often in a shell command line quotation mark must be used to prevent a parser from interpreting spaces as being argument delimiters.  E.g., for the subject 

```
 subject=isso {{SUBJECT}}
```

a bash script would require quotes placed like `"subject=isso {{SUBJECT}}"` or  `subject="isso {{SUBJECT}}` to keep the argument together.  The shell would interpret the quotes for their synactic meaning, and then remove them before passing each argument phrase to the program as, e.g. *argv[11]* or equivalent.

However, for the *isso* configuatation `call` value above, quotes are not required because the grouping is done by lines.  **In fact quotes for the purpose of syntactic grouping must NOT be used.**   The quotes will not be removed before passing to the program, and the input will likely be invalid. Quotes can still be used as part of the content of any argument, as required. 

Some (but not all) scenarios require the mail subject to be precified as part of the arguments, and not in the standard input data.  The above `curl` example shows such a case.  In order to enable variable subject line content a template parameter `%SUBJECT%` is provided.  The *isso* software will render this template %SUBJECT% as the fixed formula:

> ...<last 15 characters of blog uri> ::: <first 15 characters of comment>...

The last part of the last `curl` argument:  `<-' , is a curl specific instruction to accept data from standard input.  Because the message body is variable it must be transmitted via standard input to the process.  So any program used must be configured (or already be hard coded) to accept standard input.

Be aware that protocol issues depend on the called program and the site receiving the data. It is not handled by the *isso* code.  For example, although the above example appears to transact via HTTPS, there is some possibilty it might downgrading to HTTP after authentication for the message transaction part.  (The log file is still under interpretation.)

**Read the current limitations section at the end of this document.**


## Implementation

The *notify-syscall-180708* branch adds a new module `Syscall` in the `isso/ext/notifications.py` file.

It formats the mail message body in the same way as the existing `SMTP` module, but without the SMTP header and *quopri* / *base64* encoding.

The command and arguments as specified in the configuration are supplied as a list which is the first parameter of `subprocess.run`.

The message body is encoded to binary and passed as standard intput to the invoked process.

When complete, `subprocess.run` returns an object with members `returncode`, `stdout`, and 'stderr'.  All are logged via the global logger (usally to `/var/log/isso.log`).

*Isso* expects that success is indicated by a `returncode` value of zero, and anything else is error.  However, an error does not result in an *isso* program error.  The only difference in *isso* program behavior is that for a non-zero result *isso* will log via

    logger.error(....)

and for a zero result via

    logger.info(....)

# Other changes

The notification backend `Stdout` module was rewritten to fix a bug caused by trying to log a bloom filter as text.  Also, the relation between function names, log content, and events was cleaned up.

# IMPORTANT: Current Limitations

## Implementation

1. `subprocess.run` is not available before *Python 3.5*.  Certainly not in *Python2*. In enviroments where the code will not run it should not be enabled in the configuation file, (if it even compiles). 



