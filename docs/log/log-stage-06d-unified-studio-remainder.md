# Log — Stage 6d: Unified Studio, what 6a left owed

*The stage file is [`docs/plan/stages/stage-06d-unified-studio-remainder.md`](../plan/stages/stage-06d-unified-studio-remainder.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an apply; `[user]` is something done by hand, with any measurement pasted verbatim.*

---

## 2026-09-07 — two readings taken ahead of the stage, because both are inputs to other people's steps

*Stage 6c's pass 6 is waiting on four `[user]` readings, so the two 6d steps that need nothing from
anybody were taken first. Both turned out to be worth taking early for the reason their own step
texts give: each one is a **lead time**, not a portal click.*

### 3.6 — the two portal surfaces, measured against the Region's own catalog

- **[Claude] All four names exist in `us-west-2`** — read from
  `describe-vpc-endpoint-services`, not from the vendor table:

  | name | in the catalog | in an estate list |
  |---|---|---|
  | `logs` | yes | **yes** — it is in `vpc-egress`'s `core_services`, so **CloudWatch is already covered in every VPC** |
  | `sqlworkbench` | yes | **no** |
  | `sqlworkbench-v2` | yes | **no** |
  | `codeconnections.api` | yes | no — **Stage 7's** input (open question 26's `gitConnectionArn`), not this stage's |
  | `codestar-connections.api` | yes | no — same, and the older spelling of it |

- **[Claude] The finding is the asymmetry.** One of the two surfaces the optional table names is
  covered by accident — `logs` was in the core list from Stage 3 for a different reason — and the
  other, **Portal Query Editors, has no endpoint in any VPC**. Under design B that is not a slower
  path, it is **no path at all**: a portal feature that exists in the UI and fails on first use.
- **[Claude] WHAT IS NOT DECIDED HERE, deliberately.** Both spellings exist, and which one the portal
  actually calls is a measurement that needs the feature opened — a step that belongs to whoever
  opens it. Adding both would be 0.020/h for a feature nobody has used; adding neither is the state
  today. **Recorded as a named gap rather than closed by guess**, and it is a cheap one to close once
  somebody clicks the editor: the symptom will be a 403 or a timeout with `sqlworkbench` in it.

### 7.2 — which principal makes the remote-IDE call, and the static half is decisive

- **[Claude] The step asks the right question and the answer is worse than it feared.** 6a step 3.2
  attached two denies — `DenyRemoteSessionOnSomeoneElsesSpace` and `DenyRemoteSessionAsSomeoneElse`,
  both on `sagemaker:StartSession` — to the **six persona sets**, to *scope* the remote-IDE channel
  rather than deny it. Read back from Identity Center today, `DataScientistAccess` carries:

  ```
  Deny   DenyRemoteSessionOnSomeoneElsesSpace   sagemaker:StartSession
  Deny   DenyRemoteSessionAsSomeoneElse         sagemaker:StartSession
  Allow  ReadSageMakerStatus                    sagemaker:Search, List*, GetSearchSuggestions, Describe*
  ```

  **There is no `Allow` for `sagemaker:StartSession` anywhere in the set.** The only SageMaker Allow
  is read-only status. And `policies-sagemaker.tf` says in its own comment where the grant does live:
  *"these six sets are not where `sagemaker:StartSession` is granted — the project role is"*.
- **[Claude] So the pair is attached to a principal that cannot make the call, and absent from the
  principal that can.** Whichever way 7.5's CloudTrail resolves the caller, the conclusion holds:
  - if the laptop connects with the **persona's** credentials, the call fails for want of an
    `Allow` — an access-denied that is **not** the deny pair, and that reads like a broken feature
    rather than a scoping decision;
  - if it connects with the **project role**, it succeeds **unscoped**, because that role carries
    neither deny.
  Either way **the objective's scoping was granted by nothing**. This is Lesson 18 in its plainest
  form — a policy never constrains the principal that authors it — with Lesson 28 underneath: the
  grant and the constraint are in two different slices, and neither file shows the gap.
- **[Claude] The repair the step already names is the right one and is NOT a new SCP.** An SCP would
  deny the feature rather than scope it. The estate has exactly one instrument that reaches a role a
  blueprint writes: **the D13 permissions boundary of 6a step 2.1**. The two conditions move there.
  **Not done here**: it changes a boundary on a blueprint-authored role, the boundary field is
  write-only (always `get-role`, never `list-roles`), and 7.5's CloudTrail is what names the role to
  attach it to. Recorded so the repair is not rediscovered as a design question.
- **[Claude] What this does NOT settle**: whether a space is created with remote access at all (7.3,
  the user's decision) and which of the three connection methods works (7.4). The reading above makes
  7.3's recommendation stronger rather than weaker — *on for one space, by hand, off as the default* —
  because the scoping everyone assumed was in place is not.
