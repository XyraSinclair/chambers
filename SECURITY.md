# Security

This repository ships a substrate and its evidence, not a hosted
service. Still: a way to make the meter lie is a security finding here —
a decision path that diverges between the conformant implementations, a
float that crept into accounting, a ledger operation that can erase a
fact, a widening that the type system fails to record.

Report privately to xyra@scry.io. A public issue is fine for anything
that does not hand an attacker a working exploit against a deployment.

There is no bounty program. There is attribution: confirmed findings
land in the specs with your name, unless you ask otherwise.
