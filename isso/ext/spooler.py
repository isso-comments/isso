def spooler(args):
    try:
        self._sendmail(args[b"subject"].decode("utf-8"),
                       args["body"].decode("utf-8"))
    except smtplib.SMTPConnectError:
        return uwsgi.SPOOL_RETRY
    else:
        return uwsgi.SPOOL_OK

uwsgi.spooler = spooler
