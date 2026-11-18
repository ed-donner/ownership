# Ownership

## A large codebase for the AI SDLC course

This repo is a fork of Odoo 20.0 Community, for the large codebase hands-on example in my AI SDLC course ([edwarddonner.com/curriculum](https://edwarddonner.com/curriculum)). Odoo is a suite of business apps with about 3 million lines of code in 650 modules, not counting translations.

Our example business is Take Ownership, a shop that sells refurbished laptops, phones and tablets. We customize Odoo for the shop. Every product gets a condition grade and a battery health figure, and both show in the back office and the web shop. The back office also uses the shop's brand colors and fonts. The change goes in our own addon, `addons/take_ownership`. Odoo's own modules stay as they are.

There are three branches:

| Branch | What it holds |
|---|---|
| `main` | Odoo 20.0, with the skills for your coding agent, the product photos and this README |
| `documented` | `main` plus the documentation for coding agents: `AGENTS.md`, `docs/spec.md` and `docs/specs/` |
| `completed` | `documented` plus the Take Ownership addon |

Odoo Community is licensed under the LGPL version 3 (see `LICENSE` and `COPYRIGHT`), and so is this fork. Odoo is a trademark of Odoo S.A., which doesn't make or endorse this fork. The product photos come from Wikimedia Commons under their own licenses, listed in `docs/photos/CREDITS.md`.

_If you're looking at this in VS Code or Cursor, right-click `README.md` in the Explorer on the left and choose **Open Preview** to see it formatted._

## Get the code

To look at my versions, clone my repo:

```
git clone --depth 1 --no-single-branch https://github.com/ed-donner/ownership.git
```

To build it yourself and push your work, fork it first. Open https://github.com/ed-donner/ownership, click **Fork**, untick **Copy the `main` branch only** so your fork has all three branches, then click **Create fork**. Clone your fork the same way, with your GitHub username in place of `ed-donner`.

`--depth 1` leaves out Odoo's history, which is about 18 GB. `--no-single-branch` brings all three branches.

## Set up Odoo

You need git, uv and PostgreSQL 16 or later.

### PostgreSQL on a Mac

Install PostgreSQL with Homebrew and add a database user for Odoo. The second command puts PostgreSQL's tools on your path:

```
brew install postgresql@16
brew link --force postgresql@16
brew services start postgresql@16
createuser --createdb odoo
```

Installing Odoo's Python packages compiles two of them, so you also need Xcode's command line tools. If you're not sure you have them, run `xcode-select --install`.

### PostgreSQL on Windows

Download the installer from https://www.postgresql.org/download/windows/ and run it. It asks you to choose a password for the `postgres` user. Odoo won't run as that user, so make a user for Odoo: open **SQL Shell (psql)** from the Start menu, press Enter to accept each default, type your password, then run:

```
CREATE ROLE odoo LOGIN CREATEDB PASSWORD 'odoo';
```

### Odoo

In the `ownership` folder, create a file called `odoo.conf` with these lines. Odoo's `.gitignore` already keeps it out of git:

```
[options]
db_name = ownership
db_user = odoo
data_dir = .odoo-data
```

On Windows, add these two lines as well:

```
db_host = localhost
db_password = odoo
```

Install Odoo's Python packages:

```
uv venv --python 3.12
uv pip install -r requirements.txt
```

Create the shop's database with the web shop and Odoo's demo data. This takes a few minutes:

```
uv run python odoo-bin -c odoo.conf -i website_sale --with-demo --stop-after-init
```

Start Odoo, then open http://localhost:8069 and sign in with `admin` as the email and the password:

```
uv run python odoo-bin -c odoo.conf
```

Stop it with Ctrl+C.

## Skip to my versions

To read the documentation my coding agent wrote:

```
git checkout documented
```

To see the finished shop, check out `completed`, add the addon to your database, then start Odoo:

```
git checkout completed
uv run python odoo-bin -c odoo.conf -i take_ownership --stop-after-init
uv run python odoo-bin -c odoo.conf
```

In the Sales app, open **Products** to see the grades and battery health. The web shop is at http://localhost:8069/shop.

This adds my addon to your database. To build it yourself afterward, start from a new database: change `db_name` in `odoo.conf`, for example to `ownership2`, and run the command that creates the shop's database again.

## Build it yourself

I used Claude Code with Sonnet 5.5 at medium effort. Start Claude Code in the `ownership` folder and choose these with `/model` and `/effort`.

### Step 1: documentation for coding agents

```
Use a dynamic workflow to write documentation for coding agents working in this repo. Odoo 20.0 Community is too big to read in full, so cover only these:

- AGENTS.md: how to set up, run, update and test Odoo here, following README.md. Start the server as a background task and stop it by stopping that task. Our changes go in our own addons in addons/, and Odoo's own modules stay unchanged. List the mistakes an agent trained on older versions of Odoo would make.
- docs/spec.md: how Odoo is built (modules, the ORM, views and inheritance, assets, security, tests and the web client), linking to the files in docs/specs/.
- docs/specs/modules.md: one line for every module in addons/, made by a script that reads the manifests.
- An area file in docs/specs/ for each of these: products, sales, invoicing, inventory, the web shop, and the web client with its theming.

Every claim cites a file path. Write a script that checks every cited path exists, and run it.
```

The workflow runs many agents at once. It took about 7 minutes for me. Dynamic workflows are part of Claude Code. With another coding agent, start the prompt with "Use subagents" in place of "Use a dynamic workflow".

```
git add .
git commit -m "Docs: agent documentation"
```

### Step 2: one pass of the AI SDLC

Start a fresh session (`/clear` in Claude Code), so your agent works from the documentation. Then make a branch for the change:

```
git checkout -b take-ownership
```

#### Plan

````
Create docs/changes/take-ownership/intent.md with the text below. Then read it with docs/spec.md and ask me about anything unclear, at most three questions. Update the intent with my answers.

# Intent: Take Ownership

## Problem

Take Ownership sells refurbished laptops, phones and tablets. Odoo has nowhere to record a device's condition or its battery health, so staff keep them in a spreadsheet and customers can't see them in the web shop. The back office also looks like any other copy of Odoo.

## Proposed outcome

Every product has a condition grade: A (like new), B (light wear), C (visible wear) or Parts (for repair). Phones, laptops and tablets also have a battery health percentage. The grade shows as a colored badge on the product form, the product list and the kanban cards. Battery health shows as a progress bar on the form and the list. Staff can filter and group products by grade. The web shop's product page shows the grade and the battery health. The back office uses the Take Ownership brand from the brand skill, with a Midnight navbar.

## Constraints

- All of it goes in a new addon, addons/take_ownership. Odoo's own modules don't change.
- The sample data has the ten devices in docs/photos/, with their photos and with grades, battery figures and prices of your choosing, in Laptops, Phones, Tablets and Accessories. The photo credits in docs/photos/CREDITS.md go with the photos.
- The sample data archives the demo products that come with Odoo, so the product lists and the shop show only our devices.

## Not in this change

- Grades on quotes, orders, invoices or PDFs
- The web shop's theme, the point of sale and the logo
- A grade for each serial number

## Success criteria

1. The addon installs on the shop's database and its tests pass.
2. The sample devices show their photo, grade and battery health in each place above.
3. The back office is in the Take Ownership brand.
````

Answer its questions.

```
git add .
git commit -m "Plan: intent.md agreed"
```

#### Design

```
Read the intent for this branch, in docs/changes/, and update docs/spec.md and the area files in docs/specs/ so they describe this repo with the change, as it will be once it's merged. Add an area file if the change needs one. Use the brand skill. List any concerns at the top of your reply.
```

Answer each concern and ask your agent to update the spec.

```
git add .
git commit -m "Design: the spec"
```

#### Build

```
Read the intent for this branch, in docs/changes/, with docs/spec.md, and write plan.md beside the intent with four sections: Files that change, Order of work, Risks and Proof. Proof lists the tests and the screenshots. Don't write any code yet.
```

```
git add .
git commit -m "Build: plan.md"
```

Start a fresh session (`/clear` in Claude Code), then:

```
Implement the plan.md for this branch, in docs/changes/, following its order of work. Write the tests in its Proof section and run them as you go. Leave the commits to me.
```

This is the longest step, about 20 minutes for me.

```
git add .
git commit -m "Build: Take Ownership"
```

#### Test

```
Run the addon's tests and fix failures until they pass. Then start Odoo, use Playwright to take a screenshot of each place the intent lists and of the back office, and show me.
```

```
git add .
git commit -m "Test: tests and screenshots"
```

#### Deploy

If your agent left Odoo running, ask it to stop the server. Then merge the branch into your `main` and update the addon in the shop's database:

```
git checkout main
git merge --no-ff take-ownership
uv run python odoo-bin -c odoo.conf -u take_ownership --stop-after-init
```

If your build didn't install the addon in the shop's database, use `-i` in place of `-u`. Then start Odoo and look at your shop:

```
uv run python odoo-bin -c odoo.conf
```

To keep your work on GitHub, push it to your fork with `git push`. Please don't open a pull request: your fork is part of Odoo's network of forks on GitHub, so a pull request could reach my repo or Odoo's.

---

# Odoo's original README

## Odoo

[![Build Status](https://runbot.odoo.com/runbot/badge/flat/1/master.svg)](https://runbot.odoo.com/runbot)
[![Tech Doc](https://img.shields.io/badge/master-docs-875A7B.svg?style=flat&colorA=8F8F8F)](https://www.odoo.com/documentation/master)
[![Help](https://img.shields.io/badge/master-help-875A7B.svg?style=flat&colorA=8F8F8F)](https://www.odoo.com/forum/help-1)
[![Nightly Builds](https://img.shields.io/badge/master-nightly-875A7B.svg?style=flat&colorA=8F8F8F)](https://nightly.odoo.com/)

Odoo is a suite of web based open source business apps.

The main Odoo Apps include an [Open Source CRM](https://www.odoo.com/page/crm),
[Website Builder](https://www.odoo.com/app/website),
[eCommerce](https://www.odoo.com/app/ecommerce),
[Warehouse Management](https://www.odoo.com/app/inventory),
[Project Management](https://www.odoo.com/app/project),
[Billing &amp; Accounting](https://www.odoo.com/app/accounting),
[Point of Sale](https://www.odoo.com/app/point-of-sale-shop),
[Human Resources](https://www.odoo.com/app/employees),
[Marketing](https://www.odoo.com/app/social-marketing),
[Manufacturing](https://www.odoo.com/app/manufacturing),
[...](https://www.odoo.com/)

Odoo Apps can be used as stand-alone applications, but they also integrate seamlessly so you get
a full-featured [Open Source ERP](https://www.odoo.com) when you install several Apps.

### Getting started with Odoo

For a standard installation please follow the [Setup instructions](https://www.odoo.com/documentation/master/administration/install/install.html)
from the documentation.

To learn the software, we recommend the [Odoo eLearning](https://www.odoo.com/slides),
or [Scale-up, the business game](https://www.odoo.com/page/scale-up-business-game).
Developers can start with [the developer tutorials](https://www.odoo.com/documentation/master/developer/howtos.html).

### Security

If you believe you have found a security issue, check our [Responsible Disclosure page](https://www.odoo.com/security-report)
for details and get in touch with us via email.
