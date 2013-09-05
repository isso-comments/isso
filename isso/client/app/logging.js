define({
    error: function(err) {
        if ("status" in err && "reason" in err) {
            console.error("%i: %s", err.status, err.reason)
        } else {
            console.error(err.stack)
        }
    }
})