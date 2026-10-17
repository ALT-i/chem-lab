# Connecting the Virtual Lab to your Moodle

This guide is for the administrator who looks after your institution's Moodle
site. It takes about ten minutes, and you only do it once.

Until it is done, students can still run every experiment — their work is
saved — but results cannot be sent to Moodle, and the app will tell them so.

You do not need a developer, and no new version of the lab has to be
released when any of these details change.

---

## What you will need

- An administrator account on your Moodle site.
- The web address of your Moodle site, for example
  `https://yourinstitution.moodlecloud.com`.
- An administrator account on the Virtual Lab dashboard.

---

## Step 1 — Turn on web services in Moodle

In Moodle, go to **Site administration → General → Advanced features** and
tick **Enable web services**. Save.

Then go to **Site administration → Server → Web services → Manage protocols**
and enable **REST protocol**.

## Step 2 — Decide which account the lab will act as

The lab talks to Moodle as one Moodle user. That user needs permission to:

- see who is enrolled on the course, and
- save assignment grades.

A teacher account on the course is usually enough. If you prefer, create a
dedicated account such as `virtual-lab@yourinstitution.edu` and enrol it on
the course as a teacher — that makes it obvious in the logs which changes
came from the lab.

## Step 3 — Create the token

Go to **Site administration → Server → Web services → Manage tokens** and
choose **Create token**.

- **User**: the account from Step 2.
- **Service**: your external service for the lab. If you do not have one,
  create it under **External services** first, and add these functions to it:
  - `core_webservice_get_site_info`
  - `core_user_get_users_by_field`
  - `core_enrol_get_enrolled_users`
  - `mod_assign_save_grade`

Copy the token that Moodle shows you. It is a long string of letters and
numbers. Treat it like a password.

## Step 4 — Find your course ID

Open the course in Moodle and look at the address bar:

```
https://yourinstitution.moodlecloud.com/course/view.php?id=9
                                                          ↑
                                                   this is the course ID
```

## Step 5 — Enter the details in the Virtual Lab dashboard

Sign in to the Virtual Lab admin dashboard as an administrator and go to
**Settings → Moodle**.

| Field | What to enter |
|---|---|
| Moodle site address | `https://yourinstitution.moodlecloud.com` — just the site address, nothing after it |
| Web service token | the token from Step 3 |
| Course ID | the number from Step 4 |
| Fallback assignment ID | optional; used only for experiments that have no assignment of their own |

Press **Save settings**, then **Test connection**.

A successful test names your Moodle site back to you. If it fails, the
message says why — see below.

> The token is never shown again after you save it. The field will show that
> one is stored. Leaving it blank when you edit other settings keeps the
> existing token, so you cannot wipe it by accident.

## Step 6 — Link each experiment to its assignment

Each experiment can post to its own Moodle assignment. In the dashboard, edit
an experiment and set its **Moodle assignment ID** — the `id` in the
assignment's Moodle address.

An experiment with no assignment set will tell students it is not linked yet,
rather than posting their result somewhere else.

---

## If the test fails

**"The Moodle site … redirected the request instead of answering it."**
The address does not point at a live Moodle site. This is also what a
cancelled or expired MoodleCloud site does. Check the address, and check the
site still opens in your browser.

**"Moodle API error: Invalid token"**
The token is wrong, or it has been deleted in Moodle. Create a new one and
paste it in again.

**"Moodle API error: Access control exception"**
The token is valid but its user lacks a permission. Check that the account
from Step 2 is enrolled on the course and can grade assignments, and that all
four functions in Step 3 are on the external service.

**"That address points at a private or internal host."**
The address resolves to an internal network address. The lab only connects to
public Moodle sites.

---

## Changing Moodle later

Go back to **Settings → Moodle** at any time. If you move to a different
Moodle site you must enter that site's own token in the same save — the
previous token is never reused against a new address.

To pause the integration without deleting anything, untick **Moodle
integration enabled**. Students keep working; results simply are not sent.
