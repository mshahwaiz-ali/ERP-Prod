# Ledgix FBR & Tax Layer

This document explains how the FBR and tax workflow works inside Ledgix.

It is based on the current repository code only. It does not define, interpret, or extend any external FBR rules.

---

## 1. Overview

The Ledgix FBR & Tax Layer has two main responsibilities:

1. Calculate and store invoice tax details inside Ledgix.
2. Build and submit FBR invoice payloads from submitted Ledgix documents.

The current FBR implementation is focused on the sale side:

| Ledgix document | FBR document type |
|---|---|
| `Ledgix Sale` | `Sale Invoice` |
| `Ledgix Sales Return` | `Credit Note` |

Purchase-side FBR submission is not part of the current implementation. Some tax configuration supports an `applies_to` value of `Purchase` or `Both`, but the current FBR payload and submission code only builds and submits sale invoices and sales return credit notes.

### Why this layer exists

Ledgix stores operational sale data, item data, customer data, and tax settings in its own DocTypes. FBR requires a structured JSON payload. This layer connects both sides by:

- resolving tax category and rate for each item,
- creating an immutable tax snapshot on the invoice,
- validating seller, buyer, item, and tax readiness,
- building the official FBR JSON payload,
- sending validation or post requests to FBR endpoints,
- saving latest FBR status on the sale or return,
- keeping historical logs for every attempt.

---

## 2. Important files

| File | Responsibility |
|---|---|
| `apps/ledgix_saas/api/taxation.py` | Core Ledgix tax engine. Reads tax profile, resolves item/category/shop tax settings, selects tax rates, calculates inclusive/exclusive tax, and writes invoice tax snapshots. |
| `apps/ledgix_saas/api/fbr_payload.py` | FBR readiness validation and payload builder. Builds internal Ledgix payloads and official FBR JSON payloads for sales and sales returns. |
| `apps/ledgix_saas/api/fbr_client.py` | Low-level HTTP client for FBR validate/post endpoints. Handles endpoint selection, Bearer token auth, `requests` dependency checks, response safeguards, and network errors. |
| `apps/ledgix_saas/api/fbr_submission.py` | Submission engine. Manages manual validation, manual post, auto post, submission logs, duplicate protection, retry, offline upload, and status updates. |
| `apps/ledgix_saas/api/fbr_settings.py` | Settings access layer for `Ledgix FBR Settings`. Handles modes, triggers, tokens, permissions, control state, and pause/manual/auto readiness. |
| `apps/ledgix_saas/hooks.py` | Registers scheduled workers for FBR retry and offline upload queues. Also defines Ledgix app metadata, roles, assets, and fixtures. |

---

## 3. Important DocTypes

### Ledgix Tax Profile

`Ledgix Tax Profile` is a Single DocType used by the tax engine for shop-level tax defaults.

Important fields:

| Field | Purpose |
|---|---|
| `tax_enabled` | Enables or disables Ledgix tax calculation. |
| `price_includes_tax` | Controls whether item prices already include tax. |
| `default_tax_category` | Shop-level fallback tax category. |
| `default_sales_type` | Shop-level fallback sales type for FBR rows. |
| `default_buyer_type` | Default buyer type fallback. Options include `Registered`, `Unregistered`, and `Consumer`. |
| `province` | Business province used by tax rate selection and buyer fallback. |
| `outlet_address` | Buyer/address fallback for consumer-style flows. |
| `receipt_tax_display_enabled` | Controls receipt tax display behavior. |
| `fbr_enabled`, `fbr_mode` | Deprecated. The code points FBR configuration to `Ledgix FBR Settings`. |

Permissions:

| Role | Access |
|---|---|
| `System Manager` | Read/write/create/delete. |
| `Ledgix Admin` | Read/write/create/delete. |
| `Ledgix Manager` | Read-only. |

### Ledgix Tax Category

Defines the type of tax category used by items, product categories, and shop defaults.

Important fields:

| Field | Purpose |
|---|---|
| `category_name` | Unique category name. Also used as the document name. |
| `tax_type` | Tax type such as Sales Tax, Further Tax, FED, or Other. |
| `default_rate` | Fallback rate if no active rate history row is found. |
| `is_exempt` | Forces tax rate to zero. |
| `is_zero_rated` | Forces tax rate to zero. |
| `active` | Indicates whether the category is active. |

### Ledgix Tax Rate

Stores rate history for a tax category.

Important fields:

| Field | Purpose |
|---|---|
| `tax_category` | Link to `Ledgix Tax Category`. |
| `rate` | Tax percentage. |
| `effective_from` | Start date for the rate. |
| `effective_to` | Optional end date for the rate. |
| `applies_to` | `Sales`, `Purchase`, or `Both`. |
| `province` | Optional province-specific rate. Blank province works as a general rate. |
| `active` | Only active rows are considered. |

Naming format: `TAX-RATE-{#####}`.

### Ledgix Item Tax Profile

Defines item-level tax and FBR mapping. This is the highest-priority tax source.

Important fields:

| Field | Purpose |
|---|---|
| `item` | Link to `Ledgix Item`. |
| `taxable` | If disabled, the item tax rate becomes zero. |
| `tax_category` | Item-level tax category. |
| `hs_code` | HS Code used in the FBR payload. |
| `uom_for_fbr` | FBR UOM value. |
| `sales_type` | FBR sale type value. |
| `scenario_id` | Sandbox scenario ID when required by the code path. |
| `sro_schedule_number` | Optional SRO schedule number. |
| `sro_item_serial_number` | Optional SRO item serial number. |
| `default_tax_rate` | Read-only helper field. |
| `needs_review` | Allows review state for incomplete mappings. |
| `active` | Only active mappings are used. |

Naming format: `ITEM-TAX-{#####}`.

### Ledgix Invoice Tax Detail

Child table used on `Ledgix Sale.tax_details`. It stores the immutable tax snapshot for a sale.

Important fields:

| Field | Purpose |
|---|---|
| `sale` | Link back to `Ledgix Sale`. |
| `sale_item_row` | Original sale item row reference. |
| `item` | Taxed item. |
| `qty` | Quantity used for tax calculation. |
| `rate` | Sale row rate. |
| `gross_amount` | Gross line amount from sale row. |
| `discount_amount` | Discount amount from sale row. |
| `taxable_amount` | Base amount used for tax. |
| `tax_category` | Resolved tax category. |
| `tax_rate` | Resolved tax rate percentage. |
| `tax_amount` | Calculated tax amount. |
| `net_amount` | Amount including tax when exclusive, or final amount when inclusive. |
| `price_includes_tax` | Whether price was treated as tax-inclusive. |
| `hs_code` | HS Code snapshot. |
| `uom_for_fbr` | FBR UOM snapshot. |
| `sales_type` | FBR sales type snapshot. |
| `scenario_id` | Sandbox scenario ID snapshot. |
| `sro_schedule_number` | SRO schedule number snapshot. |
| `sro_item_serial_number` | SRO item serial number snapshot. |

### Ledgix Return Tax Detail

Child table used on `Ledgix Sales Return.tax_details`. It is generated from the original sale tax snapshot.

Important fields include:

- `sales_return`
- `original_sale`
- `original_sale_item_row`
- `item`
- `returned_qty`
- `gross_amount`
- `taxable_amount`
- `tax_rate`
- `tax_amount`
- `net_amount`
- `price_includes_tax`
- `tax_category`
- `hs_code`
- `uom_for_fbr`
- `sales_type`
- `scenario_id`
- `sro_schedule_number`
- `sro_item_serial_number`

### Ledgix FBR Settings

Single DocType that controls FBR behavior.

Important sections:

| Section | Fields |
|---|---|
| FBR Control | `enabled`, `mode`, `submit_trigger`, `block_sale_if_fbr_fails`, `sandbox_post_on_submit`, `retry_enabled`, `max_retry_count`, `offline_upload_hours` |
| Seller Identity | `seller_ntn_cnic`, `seller_business_name`, `seller_province`, `seller_address` |
| Token Configuration | `sandbox_token`, `production_token` |
| Pause / Safety | `pause_reason`, `paused_at`, `paused_by` |
| Sync Status | `last_sync_status` |

Permissions:

| Role | Access |
|---|---|
| `System Manager` | Read/write/create/delete. |
| `Ledgix Admin` | Read/write/create/delete. |
| `Ledgix Manager` | Read-only. |

### Ledgix FBR Submission Log

Stores historical FBR attempts.

Naming format: `FBR-LOG-{YYYY}-{#####}`.

Important fields:

| Field | Purpose |
|---|---|
| `reference_doctype` | Source document type, such as `Ledgix Sale` or `Ledgix Sales Return`. |
| `reference_name` | Source document name. |
| `invoice_type` | `Sale Invoice`, `Credit Note`, etc. |
| `fbr_status` | Attempt status. |
| `fbr_invoice_number` | FBR invoice or credit note number if returned. |
| `attempt_count` | Retry/post attempt count. |
| `next_retry_time` | Next retry datetime. |
| `request_json` | Payload sent or prepared. |
| `response_json` | FBR/client response. |
| `error_code` | Error code. |
| `error_message` | Safe error message. |
| `submitted_by` | User who caused the log entry. |
| `submitted_at` | Timestamp for final statuses. |

### Ledgix Sale

`Ledgix Sale` is submittable and contains sale totals, payment details, tax details, and FBR status fields.

Important FBR/tax fields:

| Field | Purpose |
|---|---|
| `items` | Sale item rows. |
| `total_amount` | Base sale total. |
| `tax_amount` | Calculated tax total. |
| `grand_total` | Final payable total. |
| `tax_details` | Read-only child table of `Ledgix Invoice Tax Detail`. |
| `fbr_status` | Latest FBR status. |
| `fbr_invoice_number` | FBR invoice number when submitted. |
| `fbr_qr_code` | QR code value if returned. |
| `fbr_submitted_at` | Timestamp for validation/submission. |
| `fbr_upload_due_at` | Offline upload deadline. |
| `fbr_error_code` | Latest FBR error code. |
| `fbr_error_message` | Latest FBR error message. |
| `fbr_submission_log` | Link to latest submission log. |

On validation, `Ledgix Sale` recalculates totals, applies the tax snapshot, and recalculates payments. On submit, it queues the sale for FBR handling after stock/POS work.

### Ledgix Sales Return

`Ledgix Sales Return` is submittable and references an original sale.

Important FBR/tax fields:

| Field | Purpose |
|---|---|
| `original_sale` | Submitted sale being returned. |
| `items` | Return item rows. |
| `tax_details` | Read-only child table of `Ledgix Return Tax Detail`. |
| `tax_amount` | Returned tax amount. |
| `grand_total` | Return grand total. |
| `fbr_status` | Latest FBR status. |
| `fbr_invoice_number` | FBR credit note number. |
| `fbr_submitted_at` | Submission timestamp. |
| `fbr_error_code` | Latest FBR error code. |
| `fbr_error_message` | Latest FBR error message. |
| `fbr_submission_log` | Link to latest submission log. |

Sales return tax is not recalculated from the current item master. It is derived proportionally from the original sale tax snapshot.

### Ledgix Customer

Customer stores FBR buyer details.

Important FBR fields:

| Field | Purpose |
|---|---|
| `buyer_ntn_cnic` | Buyer NTN/CNIC. |
| `buyer_strn` | Buyer STRN. |
| `buyer_registration_type` | `Registered` or `Unregistered`. |
| `buyer_province` | Buyer province. |
| `buyer_fbr_address` | Buyer address used in FBR payload. |
| `fbr_verification_status` | Read-only verification status. |
| `last_fbr_verification_date` | Read-only verification date. |

Address fallback fields used by the payload builder:

- `buyer_fbr_address`
- `address_line_1`
- `area`
- `city`

### Ledgix Category

`Ledgix Category` can define product category tax defaults.

Important tax fields:

| Field | Purpose |
|---|---|
| `tax_defaults_enabled` | Enables category-level tax defaults. |
| `default_tax_category` | Category-level tax category. |
| `default_taxable` | Category-level taxable flag. |
| `default_sales_type` | Category-level FBR sales type. |
| `default_uom_for_fbr` | Category-level FBR UOM. |
| `default_scenario_id` | Category-level sandbox scenario ID. |

---

## 4. Tax Engine

The tax engine lives in `apps/ledgix_saas/api/taxation.py`.

### Tax enabled / disabled

Tax calculation is controlled by `Ledgix Tax Profile.tax_enabled`.

| State | Behavior |
|---|---|
| Disabled | Tax engine returns no sale tax snapshot rows. Sale tax remains effectively inactive. |
| Enabled | Each sale item is resolved against item/category/shop tax settings and tax snapshot rows are generated. |

If the `Ledgix Tax Profile` DocType does not exist, the code treats tax as disabled.

### Item tax context resolution

For every sale item, Ledgix resolves tax context in this priority order:

1. `Ledgix Item Tax Profile`
2. `Ledgix Category` tax defaults
3. `Ledgix Tax Profile` shop defaults

#### Priority 1: Ledgix Item Tax Profile

The engine looks for the latest active `Ledgix Item Tax Profile` for the item. If it has a `tax_category`, that category is used.

This level can provide:

- taxable flag,
- tax category,
- HS Code,
- FBR UOM,
- sales type,
- scenario ID,
- SRO schedule number,
- SRO item serial number.

#### Priority 2: Ledgix Category tax defaults

If no item tax profile category is available, the engine checks the item's product category.

Category defaults are used only when:

- `tax_defaults_enabled` is checked, and
- `default_tax_category` is set.

Category defaults can provide:

- tax category,
- taxable flag,
- sales type,
- FBR UOM,
- scenario ID.

#### Priority 3: Ledgix Tax Profile shop defaults

If item and category mappings do not provide a tax category, the engine uses `Ledgix Tax Profile.default_tax_category`.

Shop defaults can also provide:

- default sales type,
- default buyer type,
- price mode.

### Tax category usage

The resolved tax category points to `Ledgix Tax Category`.

The tax category can:

- define a fallback `default_rate`,
- mark the category as exempt,
- mark the category as zero-rated.

If `is_exempt` or `is_zero_rated` is checked, the effective tax rate becomes `0`.

### Tax rate selection

If the category is not exempt and not zero-rated, Ledgix selects the rate from `Ledgix Tax Rate`.

The rate lookup filters by:

| Filter | Behavior |
|---|---|
| `tax_category` | Must match the resolved category. |
| `active` | Must be active. |
| `effective_from` | Must be on or before the posting date. |
| `effective_to` | If set, must not be before the posting date. |
| `applies_to` | Must be blank, the requested value, or `Both`. For sales snapshots this is `Sales`. |
| `province` | Blank province matches generally. Exact business province match has higher priority. |

Sorting priority:

1. Province-specific match over blank province.
2. Latest `effective_from` date.
3. Latest creation timestamp.

If no active rate row matches, the engine falls back to `Ledgix Tax Category.default_rate`.

### Exempt and zero-rated categories

If the category has either flag checked:

- `is_exempt = 1`, or
- `is_zero_rated = 1`,

then the tax rate becomes `0`, even if a rate history row exists.

If the item context has `taxable = 0`, the tax rate also becomes `0`.

### Price includes tax

`Ledgix Tax Profile.price_includes_tax` controls how amounts are calculated.

| Mode | Meaning | Calculation behavior |
|---|---|---|
| Exclusive | Price does not include tax. | `tax_amount = taxable_amount * tax_rate / 100`; `net_amount = taxable_amount + tax_amount`. |
| Inclusive | Price already includes tax. | Tax is extracted from the final price; `net_amount = gross_amount`. |

In inclusive mode, the customer-facing sale amount remains the final amount. In exclusive mode, tax is added on top of the base amount.

### Tax snapshot generation

When a `Ledgix Sale` is validated, its controller calls `apply_tax_snapshot_to_sale_doc()`.

That function:

1. prepares tax rows from sale items,
2. validates mapping and totals,
3. recalculates `tax_amount`,
4. recalculates `grand_total`,
5. clears existing `tax_details`,
6. appends the new immutable tax snapshot rows.

---

## 5. Tax Snapshot

### What `tax_details` is

`tax_details` is a child table on `Ledgix Sale`. It stores the tax calculation result for each sale item at the time the sale is saved/submitted.

It is designed as an invoice snapshot. The FBR payload reads from this snapshot instead of recalculating from current item/category/rate settings.

### Why it is immutable

Tax settings can change later:

- item tax mappings can change,
- category defaults can change,
- tax rates can change,
- HS codes and FBR UOM mappings can change.

The invoice should keep the values that were used when the sale was created. That is why `tax_details` stores a copy of tax and FBR mapping fields.

### Fields stored in `Ledgix Invoice Tax Detail`

The sale tax snapshot stores these important fields:

| Field | Meaning |
|---|---|
| `item` | Item being sold. |
| `qty` | Quantity used in tax calculation. |
| `rate` | Sale row rate. |
| `gross_amount` | Gross sale row amount. |
| `discount_amount` | Sale row discount amount. |
| `taxable_amount` | Taxable base amount. |
| `tax_category` | Resolved tax category. |
| `tax_rate` | Effective tax rate. |
| `tax_amount` | Calculated tax amount. |
| `net_amount` | Final line amount after tax logic. |
| `price_includes_tax` | Whether price was inclusive. |
| `hs_code` | HS Code snapshot. |
| `uom_for_fbr` | FBR UOM snapshot. |
| `sales_type` | FBR sales type snapshot. |
| `scenario_id` | Sandbox scenario ID snapshot. |
| `sro_schedule_number` | SRO schedule number snapshot. |
| `sro_item_serial_number` | SRO item serial number snapshot. |

### Why FBR payload reads from `tax_details`

The FBR payload builder uses `tax_details` so the payload matches the actual submitted invoice values.

This avoids problems where current master data no longer matches the invoice, for example:

- rate changed after sale,
- item HS Code changed after sale,
- category default changed after sale,
- price mode changed after sale.

If a sale has no `tax_details`, the payload builder attempts to prepare a tax snapshot from the sale document, but normal flow should already have stored the snapshot during sale validation.

---

## 6. FBR Settings

FBR behavior is controlled by `Ledgix FBR Settings` through `apps/ledgix_saas/api/fbr_settings.py`.

### Core settings

| Field | Meaning |
|---|---|
| `enabled` | Enables active FBR behavior only when mode is `Sandbox` or `Production`. |
| `mode` | Controls environment and behavior. |
| `submit_trigger` | Controls when validation/submission runs. |
| `block_sale_if_fbr_fails` | In Production + On Submit mode, blocks sale submit only when readiness validation fails before commit. Live post failures are logged after commit. |
| `sandbox_post_on_submit` | In Sandbox + On Submit mode, posts to sandbox instead of validate-only. |
| `retry_enabled` | Enables retry worker for failed production post attempts. |
| `max_retry_count` | Max retry count. Code clamps this between `0` and `10`. |
| `offline_upload_hours` | Offline upload window. Code clamps this between `1` and `72`. |

### Modes

| Mode | Behavior |
|---|---|
| `Disabled` | FBR is not active. Sales/returns can become `Not Required`. |
| `Sandbox` | Uses sandbox token and sandbox endpoints. Supports validation and post depending on trigger/settings. |
| `Production` | Uses production token and production endpoints. Production post expects an FBR invoice number. |
| `Paused` | FBR flow is paused. Sales can be marked `Paused`. |
| `Manual Only` | Automatic submission is not performed. Manual handling is required. |

### Submit triggers

| Trigger | Behavior |
|---|---|
| `Manual` | Creates pending status/log and requires manual validation/submission. |
| `On Submit` | Queues FBR work when a sale or return is submitted. |
| `Validate Only` | Runs validation but does not post a final invoice. |

### Seller identity fields

| Field | Used for |
|---|---|
| `seller_ntn_cnic` | `sellerNTNCNIC` in FBR payload. |
| `seller_business_name` | `sellerBusinessName`. |
| `seller_province` | `sellerProvince`. |
| `seller_address` | `sellerAddress`. |

### Tokens

| Field | Used for |
|---|---|
| `sandbox_token` | Bearer token for sandbox requests. |
| `production_token` | Bearer token for production requests. |

The settings API exposes token state as boolean flags such as `sandbox_token_configured` and `production_token_configured`. It does not return decrypted token values through the normal settings response.

### Pause and sync fields

| Field | Purpose |
|---|---|
| `pause_reason` | Reason for pausing FBR. |
| `paused_at` | Set automatically when mode changes to `Paused`. |
| `paused_by` | Set automatically when mode changes to `Paused`. |
| `last_sync_status` | Read-only sync status text. |

### Permission roles

The settings API uses these role groups:

| Permission type | Roles |
|---|---|
| View FBR information | `System Manager`, `Ledgix Admin`, `Ledgix Manager` |
| Manage/update FBR settings | `System Manager`, `Ledgix Admin` |

---

## 7. FBR Payload Builder

The payload builder lives in `apps/ledgix_saas/api/fbr_payload.py`.

It builds two types of payload output:

| Payload type | Purpose |
|---|---|
| Internal payload | Ledgix-friendly structure for debugging and review. Includes source, environment, sale summary, seller, buyer, item rows, and totals. |
| Official payload | JSON structure sent to the FBR client for validate/post. |

### Sale payload building

Sale payload flow:

1. Load `Ledgix Sale`.
2. Validate sale readiness.
3. Load `Ledgix Customer`.
4. Read seller block from `Ledgix FBR Settings`.
5. Read buyer block from customer and tax profile fallbacks.
6. Read item rows from `sale.tax_details`.
7. Build official `Sale Invoice` JSON payload.
8. In Sandbox mode, add `scenarioId` if available from tax rows.

### Sales return / credit note payload building

Sales return payload flow:

1. Load `Ledgix Sales Return`.
2. Validate return readiness.
3. Load original `Ledgix Sale`.
4. Require original sale reference.
5. In Production mode, require original sale FBR invoice number.
6. Read return tax rows from `return.tax_details`.
7. Build official `Credit Note` JSON payload.
8. Set `invoiceRefNo` to the original sale FBR invoice number when available.
9. In Sandbox mode, add `scenarioId` if available from return tax rows.

### Seller block

Seller data comes from `Ledgix FBR Settings`:

| Ledgix setting | Payload field |
|---|---|
| `seller_ntn_cnic` | `sellerNTNCNIC` |
| `seller_business_name` | `sellerBusinessName` |
| `seller_province` | `sellerProvince` |
| `seller_address` | `sellerAddress` |

### Buyer block

Buyer data comes from `Ledgix Customer` with fallbacks from `Ledgix Tax Profile`.

| Ledgix source | Payload field |
|---|---|
| `customer.buyer_ntn_cnic` | `buyerNTNCNIC` |
| `customer.customer_name` or document name | `buyerBusinessName` |
| `customer.buyer_province` or tax profile province | `buyerProvince` |
| `customer.buyer_fbr_address` or address fallback | `buyerAddress` |
| `customer.buyer_registration_type` or tax profile default buyer type | `buyerRegistrationType` |

Address fallback order:

1. `buyer_fbr_address`
2. `address_line_1`
3. `area`
4. `city`
5. `Ledgix Tax Profile.outlet_address`

If the default buyer type is `Consumer`, the payload builder normalizes it to `Unregistered` for buyer registration type and can use `Walk-in Customer` fallback values.

### Item rows from `tax_details`

FBR item rows are built from the invoice tax snapshot.

| Snapshot field | Internal item field | Official FBR field |
|---|---|---|
| `item` | `item` | Used to find `productDescription`. |
| Item name | `product_description` | `productDescription` |
| `qty` | `qty` | `quantity` |
| `rate` | `rate` | Not directly sent as item price. Tax rate is sent as `rate`. |
| `gross_amount` | `gross_amount` | Used internally. |
| `discount_amount` | `discount_amount` | `discount` |
| `taxable_amount` | `taxable_amount` | `valueSalesExcludingST` |
| `tax_rate` | `tax_rate` | `rate` formatted as percent, such as `18%`. |
| `tax_amount` | `tax_amount` | `salesTaxApplicable` |
| `net_amount` | `net_amount` | `totalValues` |
| `hs_code` | `hs_code` | `hsCode` |
| `uom_for_fbr` | `uom_for_fbr` | `uoM` |
| `sales_type` | `sales_type` | `saleType` |
| `sro_schedule_number` | `sro_schedule_number` | `sroScheduleNo` |
| `sro_item_serial_number` | `sro_item_serial_number` | `sroItemSerialNo` |

### Official sale invoice field mapping

| Official FBR field | Ledgix source |
|---|---|
| `invoiceType` | Static value: `Sale Invoice`. |
| `invoiceDate` | `Ledgix Sale.sale_date`. |
| `sellerNTNCNIC` | `Ledgix FBR Settings.seller_ntn_cnic`. |
| `sellerBusinessName` | `Ledgix FBR Settings.seller_business_name`. |
| `sellerProvince` | `Ledgix FBR Settings.seller_province`. |
| `sellerAddress` | `Ledgix FBR Settings.seller_address`. |
| `buyerNTNCNIC` | `Ledgix Customer.buyer_ntn_cnic`. |
| `buyerBusinessName` | `Ledgix Customer.customer_name` or document name. |
| `buyerProvince` | Customer buyer province, then tax profile province fallback. |
| `buyerAddress` | Customer FBR/address fallback, then outlet address fallback. |
| `buyerRegistrationType` | Customer buyer registration type or tax profile default. |
| `invoiceRefNo` | Blank for sale invoice. |
| `items` | Built from `Ledgix Sale.tax_details`. |
| `scenarioId` | Added in Sandbox mode when at least one tax row has `scenario_id`. |

### Official credit note field mapping

| Official FBR field | Ledgix source |
|---|---|
| `invoiceType` | Static value: `Credit Note`. |
| `invoiceDate` | Current date from code at payload build time. |
| `sellerNTNCNIC` | `Ledgix FBR Settings.seller_ntn_cnic`. |
| `sellerBusinessName` | `Ledgix FBR Settings.seller_business_name`. |
| `sellerProvince` | `Ledgix FBR Settings.seller_province`. |
| `sellerAddress` | `Ledgix FBR Settings.seller_address`. |
| `buyerNTNCNIC` | Customer buyer NTN/CNIC. |
| `buyerBusinessName` | Customer name fallback. |
| `buyerProvince` | Customer/tax profile fallback. |
| `buyerAddress` | Customer/tax profile address fallback. |
| `buyerRegistrationType` | Customer/tax profile fallback. |
| `invoiceRefNo` | Original sale `fbr_invoice_number`. |
| `items` | Built from `Ledgix Sales Return.tax_details`. |
| `scenarioId` | Added in Sandbox mode when at least one return tax row has `scenario_id`. |

### Internal payload vs official payload

| Area | Internal payload | Official payload |
|---|---|---|
| Purpose | Review/debug inside Ledgix. | Sent to FBR client. |
| Structure | Ledgix grouped sections: `sale`, `seller`, `buyer`, `items`, `totals`. | FBR-style JSON fields. |
| Contains totals | Yes, internal totals section. | Totals are represented at item row level. |
| Contains `payload_version` | Yes. | No. |
| Sent to FBR | No. | Yes. |

---

## 8. FBR Client

The FBR client lives in `apps/ledgix_saas/api/fbr_client.py`.

### Endpoints

| Operation | Mode | URL constant |
|---|---|---|
| Validate | Sandbox | `SANDBOX_VALIDATE_URL` |
| Validate | Production | `PRODUCTION_VALIDATE_URL` |
| Post | Sandbox | `SANDBOX_POST_URL` |
| Post | Production | `PRODUCTION_POST_URL` |

The configured URLs are:

| Constant | URL |
|---|---|
| `SANDBOX_VALIDATE_URL` | `https://gw.fbr.gov.pk/di_data/v1/di/validateinvoicedata_sb` |
| `PRODUCTION_VALIDATE_URL` | `https://gw.fbr.gov.pk/di_data/v1/di/validateinvoicedata` |
| `SANDBOX_POST_URL` | `https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata_sb` |
| `PRODUCTION_POST_URL` | `https://gw.fbr.gov.pk/di_data/v1/di/postinvoicedata` |

### Validate vs post

| Operation | Purpose |
|---|---|
| `validate_invoice()` | Sends the payload to the validate endpoint for Sandbox or Production. It updates validation status through the submission engine. |
| `post_invoice()` | Sends the payload to the post endpoint for Sandbox or Production. Production post requires an invoice number in the response to be treated as submitted. |

### Token handling

The client reads the active token through `get_active_fbr_token(mode)`.

| Mode | Token field |
|---|---|
| `Sandbox` | `sandbox_token` |
| `Production` | `production_token` |

Requests use Bearer authentication:

```text
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
```

### `requests` dependency

The client tries to import Python `requests`.

If `requests` is unavailable:

- network calls are disabled,
- client status reports requests unavailable,
- FBR calls return a `Not Ready` result,
- `ensure_requests_available()` throws a clear error.

### Network error handling

The client wraps network calls and returns structured results:

| Field | Meaning |
|---|---|
| `success` | Whether HTTP and response body are considered successful. |
| `network_call` | Whether a network request was attempted. |
| `http_status` | HTTP status code, if available. |
| `status` | `HTTP OK`, `HTTP Error`, `Network Error`, etc. |
| `response` | JSON response or raw text response. |
| `error` | Safe error message. |
| `fbr_operation` | `validate` or `post`. |
| `fbr_mode` | `Sandbox` or `Production`. |

### Safe error redaction

The client removes Bearer token content from error messages before returning or logging them. This avoids leaking tokens through exceptions or network error text.

### Client status API

`get_client_status()` returns a safe status summary:

- current mode,
- whether `requests` is available,
- whether sandbox/production validate/post are connected based on mode and token configuration,
- whether any token is configured,
- whether network calls are enabled.

Only FBR view roles can call this API.

---

## 9. FBR Submission Engine

The submission engine lives in `apps/ledgix_saas/api/fbr_submission.py`.

### Sale must be submitted first

Both validation and submission require `Ledgix Sale.docstatus == 1`.

Draft and cancelled sales are rejected for FBR payload use.

### Allowed FBR statuses

The sale submission engine supports these statuses:

- `Not Required`
- `Pending`
- `Validated`
- `Submitted`
- `Failed`
- `Offline Pending`
- `Skipped`
- `Paused`

`Ledgix Sales Return` uses the same status family, except its DocType options do not include `Offline Pending`.

### Manual validation flow

Manual validation uses `validate_sale_with_fbr(sale_name)`.

Flow:

```text
Submitted Ledgix Sale
        |
        v
Build FBR payload
        |
        v
Send validate request
        |
        v
Parse FBR response
        |
        +--> Valid   -> Sale fbr_status = Validated
        |
        +--> Invalid -> Sale fbr_status = Failed
        |
        v
Create Ledgix FBR Submission Log
```

There is also `validate_sale_with_fbr_production(sale_name)`, which forces Production validation.

### Manual submit/post flow

Manual submit uses `submit_sale_to_fbr(sale_name)`.

Flow:

```text
Submitted Ledgix Sale
        |
        v
Check duplicate submission
        |
        v
Check settings + token
        |
        v
Acquire submission lock
        |
        v
Build ready payload
        |
        v
Post to Sandbox or Production endpoint
        |
        v
Parse response
        |
        +--> Success -> Submitted or Validated
        |
        +--> Failure -> Failed or Offline Pending
        |
        v
Update Sale FBR fields + create log
```

### Auto submit on sale submit

`Ledgix Sale.on_submit()` calls `queue_fbr_submission_after_sale_work()`.

That function:

1. optionally blocks sale submit in Production + On Submit mode if readiness validation fails before commit,
2. queues the sale through `queue_sale_for_fbr()`,
3. logs failures instead of crashing post-commit work where possible.

### Validate Only flow

If `submit_trigger = Validate Only`, the sale is queued and validation is run. It does not post a final FBR invoice.

### Sandbox behavior

Sandbox mode can validate or post depending on settings:

| Setting | Behavior |
|---|---|
| `submit_trigger = On Submit` and `sandbox_post_on_submit = 0` | Runs sandbox validation only. |
| `submit_trigger = On Submit` and `sandbox_post_on_submit = 1` | Queues sandbox post after commit. |
| Manual validation | Uses sandbox validation unless production validation is explicitly called. |

Sandbox payload requires `scenario_id` according to the code readiness checks.

### Production behavior

Production mode uses production validate/post endpoints and the production token.

For production post:

- the code requires a successful response with an FBR invoice number,
- missing invoice number causes failure,
- network failure during production post can move the sale to `Offline Pending`,
- retry handling applies to production post failures when enabled.

### Duplicate submission protection

Before posting, the engine checks whether the sale already has `fbr_invoice_number`.

If it does, the result is returned as `Already Submitted`, and no new post is sent.

The same protection exists for sales returns using the return `fbr_invoice_number`.

### Submission lock

Sale submission uses a lock to avoid concurrent duplicate posts.

The lock attempts to use Frappe cache locking. If that fails, it falls back to a database lock with `GET_LOCK()` and releases it with `RELEASE_LOCK()`.

### Sale FBR status fields updated

The engine updates these fields on `Ledgix Sale`:

| Field | Updated when |
|---|---|
| `fbr_status` | Every status change. |
| `fbr_invoice_number` | When FBR returns an invoice number. |
| `fbr_qr_code` | When response contains QR code data. |
| `fbr_submitted_at` | When status becomes `Submitted` or `Validated`. |
| `fbr_upload_due_at` | When network failure creates `Offline Pending`; cleared when status becomes `Submitted`. |
| `fbr_error_code` | On failed/invalid response. |
| `fbr_error_message` | On failed/invalid response. |
| `fbr_submission_log` | Latest related submission log. |

### Sales return FBR status fields updated

The engine updates these fields on `Ledgix Sales Return`:

| Field | Updated when |
|---|---|
| `fbr_status` | Every status change. |
| `fbr_invoice_number` | When FBR returns a credit note/invoice number. |
| `fbr_submitted_at` | When status becomes `Submitted`. |
| `fbr_error_code` | On failed/invalid response. |
| `fbr_error_message` | On failed/invalid response. |
| `fbr_submission_log` | Latest related submission log. |

---

## 10. Retry and Offline Handling

Retry and offline workers are registered in `apps/ledgix_saas/hooks.py`.

### Scheduler hooks

| Schedule | Worker |
|---|---|
| Every 15 minutes | `ledgix_saas.api.fbr_submission.process_fbr_retry_queue` |
| Every hour | `ledgix_saas.api.fbr_submission.process_fbr_offline_upload_queue` |

### Retry queue

The retry worker processes failed production post attempts when:

- FBR settings are enabled,
- mode is `Production`,
- `retry_enabled` is checked,
- production token is configured,
- `max_retry_count` is greater than zero.

It looks for submitted `Ledgix Sale` documents where:

- `docstatus = 1`,
- `fbr_status` is `Pending` or `Failed`,
- `fbr_invoice_number` is empty.

It retries only when:

- there is a retryable failed post log, or
- the sale still needs a production post from an On Submit flow,
- attempt count is below `max_retry_count`,
- `next_retry_time` is empty or due.

### Retry timing

The next retry time is based on attempt count:

| Attempt count | Next retry delay |
|---|---|
| 1 or less | 5 minutes |
| 2 | 15 minutes |
| 3 or more | 60 minutes |

### Offline upload queue

The offline upload worker processes sales with:

- `docstatus = 1`,
- `fbr_status = Offline Pending`,
- empty `fbr_invoice_number`.

It retries the post while the offline upload window is still valid.

### When status becomes Offline Pending

A sale becomes `Offline Pending` when:

- mode is `Production`,
- the operation is `post`,
- the post fails,
- a network failure is detected.

The code sets `fbr_upload_due_at` by adding `offline_upload_hours` to the current datetime.

### What happens when the offline window expires

If `fbr_upload_due_at` is earlier than the current time, the offline worker marks the sale as `Failed` with this message:

```text
FBR offline upload window expired.
```

---

## 11. FBR Submission Log

`Ledgix FBR Submission Log` is the historical audit trail for FBR actions.

### Purpose

It records every important validation/post attempt and stores:

- source document reference,
- invoice type,
- request JSON,
- response JSON,
- final or attempt status,
- error details,
- retry metadata,
- submission user/time.

### Naming format

```text
FBR-LOG-{YYYY}-{#####}
```

### Important fields

| Field | Purpose |
|---|---|
| `reference_doctype` | Source DocType. |
| `reference_name` | Source document name. |
| `invoice_type` | `Sale Invoice`, `Credit Note`, etc. |
| `fbr_status` | Attempt status. |
| `fbr_invoice_number` | FBR number if returned. |
| `attempt_count` | Retry/post attempt count. |
| `next_retry_time` | Scheduled next retry. |
| `request_json` | Payload prepared or sent. |
| `response_json` | Client/FBR response. |
| `error_code` | Error code. |
| `error_message` | Safe error message. |
| `submitted_by` | User associated with the attempt. |
| `submitted_at` | Timestamp for final statuses. |

### Latest status vs historical logs

| Location | Purpose |
|---|---|
| `Ledgix Sale.fbr_status` / `Ledgix Sales Return.fbr_status` | Latest current status for quick display and workflow decisions. |
| `Ledgix FBR Submission Log` | Full history of attempts, requests, responses, retry timings, and errors. |

### Permissions

| Role | Access |
|---|---|
| `System Manager` | Read/write/create/delete. |
| `Ledgix Admin` | Read/write/create/delete. |
| `Ledgix Manager` | Read-only. |

---

## 12. Workflow diagrams

### Tax calculation workflow

```text
Ledgix Sale validate
        |
        v
Calculate sale item amounts
        |
        v
Is Ledgix Tax Profile.tax_enabled enabled?
        |
        +-- No --> No tax snapshot rows
        |
        +-- Yes
              |
              v
        For each sale item
              |
              v
        Resolve tax context
              |
              +--> Item Tax Profile
              |       |
              |       v
              |   Category tax defaults
              |       |
              |       v
              |   Shop default tax category
              |
              v
        Resolve tax category + rate
              |
              v
        Calculate inclusive/exclusive tax
              |
              v
        Append Ledgix Invoice Tax Detail row
              |
              v
        Update tax_amount and grand_total
```

### Sale to FBR validation workflow

```text
Submitted Ledgix Sale
        |
        v
validate_sale_with_fbr()
        |
        v
Read FBR Settings
        |
        v
Validate seller + buyer + tax_details
        |
        +-- Invalid --> Create Failed log + mark Sale Failed
        |
        +-- Valid
              |
              v
        Build official Sale Invoice payload
              |
              v
        Send validate request
              |
              v
        Parse FBR response
              |
              +-- Valid --> Sale fbr_status = Validated
              |
              +-- Invalid/Error --> Sale fbr_status = Failed
              |
              v
        Create submission log
```

### Sale to FBR production submission workflow

```text
Submitted Ledgix Sale
        |
        v
submit_sale_to_fbr()
        |
        v
Already has fbr_invoice_number?
        |
        +-- Yes --> Return Already Submitted
        |
        +-- No
              |
              v
        Check Production mode + enabled + token
              |
              v
        Acquire submission lock
              |
              v
        Build ready payload
              |
              v
        POST to production endpoint
              |
              v
        Parse response
              |
              +-- Invoice number returned --> Submitted
              |
              +-- Network failure --> Offline Pending
              |
              +-- Invalid/error --> Failed / retry candidate
              |
              v
        Update Sale fields + create log
```

### Sales return / credit note workflow

```text
Ledgix Sales Return validate
        |
        v
Read original Ledgix Sale tax_details
        |
        v
Calculate proportional returned tax rows
        |
        v
Submit Sales Return
        |
        v
queue_return_for_fbr()
        |
        v
Build Credit Note payload
        |
        v
Use original sale fbr_invoice_number as invoiceRefNo
        |
        v
Post to FBR
        |
        +-- Success --> Return fbr_status = Submitted / Validated
        |
        +-- Failure --> Return fbr_status = Failed
        |
        v
Create submission log
```

### Retry/offline workflow

```text
Production post fails
        |
        +-- Network failure
        |       |
        |       v
        |   Sale fbr_status = Offline Pending
        |       |
        |       v
        |   Hourly offline worker retries until fbr_upload_due_at
        |       |
        |       +-- Success --> Submitted
        |       |
        |       +-- Window expired --> Failed
        |
        +-- Non-network failed post
                |
                v
            If retry enabled and attempts remain
                |
                v
            Set next_retry_time
                |
                v
            15-minute retry worker retries when due
```

---

## 13. Operational notes

- Sandbox mode is for testing FBR payload readiness and endpoint behavior.
- Production mode is live FBR submission behavior in the current code.
- Do not enable Production unless real credentials are configured and seller, buyer, item, HS Code, UOM, sales type, and tax data are verified.
- The code warns that reference API sync/check is not automated yet. Master data should be verified before production submission.
- The code warns that FBR QR/logo printing is not fully configured.
- Do not manually edit historical `tax_details` after an invoice is submitted unless there is a controlled correction process.
- `Ledgix Tax Profile.fbr_enabled` and `fbr_mode` are deprecated. Use `Ledgix FBR Settings`.
- Purchase tax rates may exist in `Ledgix Tax Rate`, but purchase-side FBR submission is not implemented by the current FBR submission engine.
- Sales return credit notes depend on the original sale tax snapshot and, in Production mode, the original sale FBR invoice number.

---

## 14. Troubleshooting

### FBR token missing

Symptoms:

- Readiness validation reports Sandbox or Production token is not configured.
- Client returns `Not Ready`.

Check:

- `Ledgix FBR Settings.sandbox_token` for Sandbox mode.
- `Ledgix FBR Settings.production_token` for Production mode.
- `enabled` is checked.
- `mode` is `Sandbox` or `Production`.

### Python `requests` missing

Symptoms:

- Client status shows `requests_available = false`.
- FBR network calls are not sent.

Check:

- Python `requests` package must be available in the bench environment.
- Restart the bench after installing dependencies.

### Sale is still draft

Symptoms:

- Payload validation says draft sale cannot be used.
- Submission function throws that submitted sale is required.

Fix:

- Submit the `Ledgix Sale` before FBR validation or submission.

### Customer buyer data missing

Symptoms:

- Buyer business name, province, address, or registration type errors.

Check:

- `Ledgix Customer.customer_name`
- `buyer_registration_type`
- `buyer_province`
- `buyer_fbr_address`
- address fallback fields: `address_line_1`, `area`, `city`
- `Ledgix Tax Profile.province`
- `Ledgix Tax Profile.outlet_address`

### HS code missing or invalid

Symptoms:

- Tax row HS Code required.
- HS Code format invalid.

Check:

- `Ledgix Item Tax Profile.hs_code`
- tax snapshot row `hs_code`

The code validates HS Code with a numeric pattern that allows 2 to 8 digits with an optional decimal segment, and also checks for 4 to 8 digits after removing the decimal.

### UOM for FBR missing

Symptoms:

- Tax row UOM for FBR is required.

Check:

- `Ledgix Item Tax Profile.uom_for_fbr`
- `Ledgix Category.default_uom_for_fbr`
- sale `tax_details.uom_for_fbr`

### Sales type missing

Symptoms:

- Tax row sales type is required.

Check fallback order:

1. `Ledgix Item Tax Profile.sales_type`
2. `Ledgix Category.default_sales_type`
3. `Ledgix Tax Profile.default_sales_type`

### Scenario ID missing in Sandbox

Symptoms:

- Sandbox readiness validation requires scenario ID.

Check fallback order:

1. `Ledgix Item Tax Profile.scenario_id`
2. `Ledgix Category.default_scenario_id`

For Sandbox payloads, the first non-empty scenario ID from tax rows is added to the official payload as `scenarioId`.

### Tax amount does not match `tax_details`

Symptoms:

- Readiness validation says sale `tax_amount` does not match `tax_details` total.
- Readiness validation says sale `grand_total` does not match `tax_details` net total.

Check:

- Sale was saved after tax settings were configured.
- `tax_details` rows exist.
- `total_amount`, `tax_amount`, and `grand_total` match current snapshot totals.
- No manual changes were made to submitted tax rows.

### Network error

Symptoms:

- Client status returns `Network Error`.
- Production post can become `Offline Pending`.

Check:

- Internet access from server.
- FBR endpoint availability.
- Token configuration.
- Firewall/proxy/network restrictions.

### FBR response invalid

Symptoms:

- HTTP response may be successful, but body is treated as invalid.
- Status becomes `Failed`.

The client checks response body validity. A response is treated as valid only when validation status and status code indicate success, and item statuses do not indicate invalid rows.

Check:

- FBR response body in `Ledgix FBR Submission Log.response_json`.
- `error_code` and `error_message` in the log.
- Item row validation messages from FBR.

### Duplicate or already submitted sale

Symptoms:

- Submission returns `Already Submitted`.
- No new network call is made.

Reason:

- `Ledgix Sale.fbr_invoice_number` is already set.

Check:

- Sale FBR fields.
- Latest linked `Ledgix FBR Submission Log`.

### Original sale missing for credit note

Symptoms:

- Credit note payload readiness fails.

Check:

- `Ledgix Sales Return.original_sale` is set.
- Original sale exists.
- In Production mode, original sale has `fbr_invoice_number`.

---

## 15. Short examples

### Example: tax source fallback

```text
Item has active Ledgix Item Tax Profile with tax_category
        -> use item-level tax category

Else item category has tax_defaults_enabled and default_tax_category
        -> use category-level tax category

Else Ledgix Tax Profile has default_tax_category
        -> use shop-level tax category
```

### Example: exclusive price

```text
Line amount: 1,000
Tax rate: 18%
Tax amount: 180
Net amount: 1,180
```

### Example: inclusive price

```text
Line amount: 1,000
Tax rate: 18%
Taxable amount is extracted from 1,000
Tax amount is the difference between gross and taxable amount
Net amount remains 1,000
```

### Example: production post result

```text
Production post sent
        |
        +-- FBR invoice number returned
        |       -> fbr_status = Submitted
        |
        +-- Network failure
        |       -> fbr_status = Offline Pending
        |
        +-- Invalid response or missing production invoice number
                -> fbr_status = Failed
```

---

## 16. Summary

The Ledgix FBR & Tax Layer uses a snapshot-first design.

The tax engine calculates item tax rows when the sale is validated. Those rows are stored in `tax_details`. The FBR payload builder then uses the stored snapshot instead of recalculating from current master data.

For FBR, the current implementation supports:

- `Ledgix Sale` to FBR `Sale Invoice`,
- `Ledgix Sales Return` to FBR `Credit Note`,
- manual validation,
- manual post,
- automatic on-submit handling,
- sandbox validation/post behavior,
- production post behavior,
- retry handling,
- offline upload handling,
- submission logs.

Purchase-side FBR submission is not implemented in the current code path.