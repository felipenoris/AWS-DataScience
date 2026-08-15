"""Shared plumbing for the read-only snapshot scripts in ``aws/``.

Every script in ``aws/`` used to be a self-contained shell file repeating the same seven
helpers (``note``, ``h1``, ``aws_``, ``run``, ``show``, ``tabulate``, the preflight). This
package is those helpers written once:

    context    where am I - repository root, output directory, the CloudShell fallback
    awscli     the ``aws`` CLI as a subprocess: profile/region handling, capture, tolerate
    report     the report file: headers, exact ``column -t`` tables, the failed-calls log
    profiles   which awsds-* profiles exist, and which of them authenticate right now
    cidr       IPv4 CIDR overlap, needed by the networking scripts
    policydoc  what plays the part of a ``Sid`` in each of the four policy types

THE RULE OF THE FOLDER STILL HOLDS: nothing imported from here creates, updates or deletes
anything in AWS. The one write this package performs is the report file under
``aws/output/``, which is untracked.

WHY THIS PACKAGE LIVES INSIDE ``aws/`` AND NOT IN A TOP-LEVEL LIB. The scripts must keep
working in CloudShell, where uv does not exist and the fallback is the system interpreter
(``python3 aws/<script>.py -``). Python puts the *script's own directory* on ``sys.path``,
so a package sitting beside the scripts is importable with no environment at all - which is
the entire CloudShell story, and the reason this package must not grow an import from
``scripts/`` (the hygiene packages) or any third-party dependency.
"""
