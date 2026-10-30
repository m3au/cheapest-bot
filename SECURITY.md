# Security

Cheapest Bot is a read-only service: GET/HEAD/OPTIONS only, no auth, no write endpoints, no database, no cookies, and no access logs (the server never records client IPs).

If you find a security issue (for example a way to read files outside `public/` and `data/`, a crash on crafted input, or an XSS on the page), please report it privately through GitHub's "Report a vulnerability" button on this repository instead of a public issue.

Wrong prices are not a security issue; open a normal PR (see CONTRIBUTING.md).
