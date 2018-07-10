
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
nargs=8
0 = /usr/bin/curl
1 = --trace-ascii, /tmp/mg1.log
2 = --user, api:<key>
3 = https://api.mailgun.net/v3/<domain>/messages
4 = -F, to=user@gmail.com
5 = -F, from=isso@example.com
6 = -F, subject=isso notify
7 = -F, text=<-
```

The arguments are divided up into multiple lists only for convenience.  When more than one argument is used placed the same line, they must be saperated by a comma.  Whitespaces within an argument are preserved, but whitespaces around an argument are removed.

The argument lines must by numbered in order from zero (0).

`nargs` must be set to the number of argument lines, which is the maximum line number plus one.

The last part of the last `curl` argument:  `<-' , is a curl specific instruction to accept data from standard input.  Because the message body is variable it must be transmitted via standard input to the process.  So any program used must be configured (or hard coded) to accept standard input.

Be aware that protocol issues depend on the called program and the site receiving the data. It is not handled by the *isso* code.  For example, although the above example appears to transact via HTTPS, there is some possibilty it might downgrading to HTTP after authentication for the message transaction part.  The log file is still under interpretation.

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

## Administration interface

1. Currently the arguments specified in the cofig file cannot contain a comma. This limitation needs to be fixed. 
2. For many choices of programs the mail subject is only configuarable as a program argument. However the subject is usually variable.  Currently there is no way to add variability to a subject line specified in the configuation file.  A template solution (e.g. `%SUBJECT%` in the argument) could be used to solve this problem.  


## Implementation

3. `subprocess.run` might not be available in *Python2*. It is available in *Python3*.  In the case of Python2, *syscall* should not be enabled ion the configuation file, if it even compiles. 



