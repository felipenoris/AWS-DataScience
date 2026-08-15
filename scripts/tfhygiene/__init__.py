"""Hygiene over the TERRAFORM trees - convention greps, policy JSON, backend literals.

The library behind ``check-tf-conventions.py``, ``check-iam-wildcards.py``,
``gen-backend-hcl.py``, ``check-ou-coverage.py`` (its authored-map half) and
``check-index.py``:

    scan         collect ``.tf`` files with ``.terraform/`` pruned, and the comment-aware
                 line scanner the convention checks share
    policydoc    what plays the part of a ``Sid`` per policy type, and the statement walk
                 the wildcard check judges one statement at a time
    backend      the account-folder -> <env> name-token vocabulary and the one place that
                 knows how to write a slice's ``backend.hcl``
    attachments  the authored per-OU attachment map, loaded and shape-checked

Deliberately independent: no AWS session, no subprocess, nothing imported from ``awslib``
or ``repohygiene``. Everything here reads files it is given and returns data; exit codes
and report text belong to the scripts.
"""
