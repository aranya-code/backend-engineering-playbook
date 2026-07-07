# Routing Policies — Geolocation and Geoproximity

Two distinct policies, both built around geography but solving different problems.

## Geolocation Routing

Routes traffic based on the **geographic location of the querying user** (by continent, country, or US state) — not performance, purely location.

| Location | Destination |
|---|---|
| India | india.example.com |
| United States | us.example.com |
| (Default) | global.example.com |

**Use cases:**
- Content localization — serving region-specific content or language versions
- Regulatory/compliance requirements — routing EU users to EU-hosted infrastructure for data residency
- Licensing restrictions — content only licensed for certain countries

**Important:** always configure a "Default" record for geolocation routing. Without one, users from any country you haven't explicitly mapped will get **no answer at all** — geolocation routing does not fall back gracefully on its own.

## Geoproximity Routing

Routes traffic based on the geographic *distance* between the user and your resources, with the ability to manually shift the "bias" — expanding or shrinking the effective geographic size of a region's traffic pool.

- **Requires Traffic Flow** (Route 53's visual policy tool — see the next file) to configure
- A positive bias expands a region's reach (it "pulls" traffic from a wider geographic radius); a negative bias shrinks it

**Use case:** gradually shifting load away from a region (e.g., during a partial regional issue or planned maintenance) without a hard failover — a soft, continuous version of shifting traffic geographically.

## Geolocation vs. Geoproximity — Quick Distinction

| | Geolocation | Geoproximity |
|---|---|---|
| Basis | Explicit country/continent/state mapping | Calculated distance + adjustable bias |
| Precision | Exact rule-based | Continuous, distance-weighted |
| Needs Traffic Flow? | No | Yes |
| Typical use | Legal/compliance/localization | Gradual load shifting between regions |
