# Non-profit programs and discounts

[← Research index](README.md) · Surveyed September 2026

RN is a registered non-profit, and most of the hosted services this stack would
lean on run non-profit or open-source programs. The savings are large enough to
change which options are affordable, so this is worth doing before committing to
paid tiers.

## The one caveat that matters most

**Most "AI for non-profits" programs discount seats, not API usage.** This
project's recurring cost is API tokens, not per-user licences. Read every offer
for which of the two it covers before counting on it.

## Verification is the bottleneck, not the asking

Nearly every vendor outsources charity validation to the same two or three
places — **TechSoup** (which operates in Sweden as
[techsoup.se](https://www.techsoup.se/)), **Goodstack**, or **Percent**. Getting
validated once unlocks most of the list, so do that first rather than per-vendor.

Programs written around US 501(c)(3) status almost always accept "equivalent
charitable registration in your jurisdiction" — a Swedish *ideell förening* with
an organisationsnummer and stadgar generally qualifies. Google additionally
requires **re-verification every 12 months**.

## Confirmed programs

| Service | Offer | Notes |
|---|---|---|
| **[Langfuse](https://langfuse.com/non-profit)** | **US $199/month in credits** — covers the full Pro plan base fee plus 100k events; additional events US $8 / 100k | Cloud only (self-hosting is free under MIT anyway). Registered non-profit, charity or equivalent; fiscally sponsored projects qualify via their sponsor. Short form, verification typically under 48h, promo code applied under Settings → Billing. Credits reset monthly, no rollover, one per organisation |
| **[Claude for Nonprofits](https://www.anthropic.com/news/claude-for-nonprofits)** | Up to **75% off Team and Enterprise** plans; reported $500 in credits for newly eligible organisations | Launched August 2026, global. **Covers seats, not clearly API usage** — the announcement does not say API credits are included. Worth asking directly. Apply at claude.com/solutions/nonprofits |
| **[Slack for Nonprofits](https://slack.com/help/articles/204368833-Apply-for-the-Slack-for-Nonprofits-discount)** | **Pro free** for workspaces ≤250 members; 85% off above that; 85% off Business+ at any size | Verified through Goodstack/TechSoup |
| **[Google for Nonprofits](https://www.google.com/intl/sv/nonprofits/offerings/workspace/)** | **Google Workspace for Nonprofits free** (100 TB pooled storage) | Available in Sweden. TechSoup verification, renewed every 12 months. Directly relevant — the mail and calendar integrations sit on this |
| **[GitHub for Nonprofits](https://docs.github.com/en/nonprofit/nonprofit-teams-plan)** | **Free Team plan** — unlimited private repos and users; 25% off Enterprise Cloud | Must be non-governmental, non-academic, non-commercial, non-political. Allow about a week |

## Confirmed as not available

| Service | Finding |
|---|---|
| **[Heroku](https://help.heroku.com/VF2KIQ5S/does-heroku-offer-non-profit-or-educational-discounts)** | No non-profit or educational discount. Only tax-exemption status on request via support, plus the free add-ons in the marketplace. Salesforce's own non-profit programme does not extend to Heroku dynos |

## Not eligible, but worth knowing

**[Anthropic AI for Science](https://support.claude.com/en/articles/11199177-anthropic-s-ai-for-science-program)** hands out substantial API credits — recent rounds ran to $30k–50k per project — but it is scoped to scientific research in academia and non-profits. Event-technology automation does not fit. Listed here so nobody spends an afternoon on the application.

## Worth asking — not yet researched

Most of these are early-stage vendors where a polite email from a registered
non-profit has a good hit rate, and none of it is documented publicly:

- **Sentry** — states it offers discounts and sponsorship to non-profits and open
  source projects; terms not published, so ask
- **PostHog** — a [startup programme](https://posthog.com/startups) exists with
  substantial credits; no dedicated non-profit programme found. Already in use by
  backstage2, so worth one email
- **Laminar, Trigger.dev, Inngest, Temporal Cloud, Dagster+** — no published
  programmes found. All small enough that asking costs nothing

## How this affects the stack choice

- The [observability self-hosting trap](landscape-typescript.md#observability-has-a-self-hosting-trap)
  mostly dissolves. Langfuse Cloud at $199/month of credits removes the reason to
  run ClickHouse + Postgres + Redis ourselves, which was the main argument against
  Langfuse at our size.
- **Heroku is not discounted**, so dyno and Postgres cost stays a real constraint.
  That reinforces keeping the worker footprint small and staying on one Postgres
  instance rather than adding infrastructure.
- Claude for Nonprofits does not obviously reduce **API** cost, which is the
  dominant spend. Budget as though it does not, and treat the
  [batch API's roughly 50% saving](architecture-sketch.md#6-data-pipelines) as the
  real lever.

## Next steps

1. Get validated with TechSoup Sweden and Goodstack once — unlocks most of the list.
2. Apply for Langfuse, Google for Nonprofits, GitHub Team, Slack.
3. Ask Anthropic directly whether non-profit pricing extends to API usage.
4. Email Sentry and PostHog.

---

Next: [Open questions](open-questions.md)
