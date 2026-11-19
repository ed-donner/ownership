# Intent: Take Ownership

## Problem

Take Ownership sells refurbished laptops, phones and tablets. Odoo has nowhere to record a device's condition or its battery health, so staff keep them in a spreadsheet and customers can't see them in the web shop. The back office also looks like any other copy of Odoo.

## Proposed outcome

Every product has a condition grade: A (like new), B (light wear), C (visible wear) or Parts (for repair). The grade is required and new products start at B. Phones, laptops and tablets also have a battery health percentage. Whether a product has one depends on its category: Laptops, Phones and Tablets (and their child categories) do, Accessories and other categories don't. The grade shows as a colored badge on the product form, the product list and the kanban cards. Battery health shows as a progress bar on the form and the list. Staff can filter and group products by grade. The web shop's product page shows the grade and the battery health. The back office uses the Take Ownership brand from the brand skill, with a Midnight navbar. Light mode only; there is no dark mode.

## Constraints

- All of it goes in a new addon, addons/take_ownership. Odoo's own modules don't change.
- The sample data has the ten devices in docs/photos/, with their photos and with grades, battery figures and prices of your choosing, in Laptops, Phones, Tablets and Accessories. The photo credits in docs/photos/CREDITS.md go with the photos.
- The sample data archives the demo products that come with Odoo, so the product lists and the shop show only our devices.

## Not in this change

- Grades on quotes, orders, invoices or PDFs
- The web shop's theme, the point of sale and the logo
- A grade for each serial number
- A dark mode for the back office

## Success criteria

1. The addon installs on the shop's database and its tests pass.
2. The sample devices show their photo, grade and battery health in each place above.
3. The back office is in the Take Ownership brand.
