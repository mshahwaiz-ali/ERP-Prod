# Ledgix FBR & Tax Module

Ledgix includes a built-in tax and FBR digital invoicing layer for POS sales, sales returns, tax calculation, invoice payload generation, FBR validation, FBR submission, retry handling, and audit logging.

This module is designed to solve a practical retail compliance problem:

> Create normal POS sales inside Ledgix, calculate tax from configured rules, freeze invoice tax data at submit time, generate an FBR-compatible invoice payload, submit or validate it with FBR, and keep full request/response logs for audit and troubleshooting.

---

## What This Module Solves

Retail and wholesale businesses usually face these issues when integrating with FBR:

* Tax rates change over time.
* Different items can have different tax categories.
* FBR requires HS codes, UOM, sale type, buyer/seller information, and scenario data.
* Submitted invoices must not silently change after tax configuration changes.
* Network/API failures need retry and offline handling.
* Every submission needs traceable logs.

Ledgix solves this by separating tax configuration, invoice tax snapshots, FBR settings, payload generation, and submission logs.

---

## High-Level Flow

```text
Tax Profile / Tax Categories / Tax Rates / Item Tax Profiles
        ↓
POS Sale / Ledgix Sale
        ↓
Tax Snapshot is calculated
        ↓
Sale is submitted
        ↓
FBR readiness validation runs
        ↓
FBR payload is generated
        ↓
Manual / Validate Only / On Submit flow runs
        ↓
FBR response is saved
        ↓
Sale gets FBR status + invoice number / error
        ↓
Submission Log stores request, response, errors, retries
```

---

## Main DocTypes

### 1. Ledgix Tax Profile

Single setup document for shop/business-level tax defaults.

Used for:

* Business name
* NTN
* STRN
* Province
* Business type
* Default tax category
* Default sales type
* Default buyer type
* Tax enabled flag
* Price includes tax setting
* Receipt tax display setting
* POS registration number
* Outlet name/address

This controls the default tax behavior of the shop.

---

### 2. Ledgix Tax Category

Defines the type of tax applied to items.

Common examples:

* Sales Tax
* Further Tax
* FED
* Other

Important fields:

* Category Name
* Tax Type
* Default Rate %
* Is Exempt
* Is Zero Rated
* Active

Use this when multiple tax categories are needed, for example standard taxable goods, exempt goods, zero-rated goods, or FED-related items.

---

### 3. Ledgix Tax Rate

Stores effective-dated tax rates.

Important fields:

* Tax Category
* Rate %
* Effective From
* Effective To
* Applies To: Sales, Purchase, Both
* Province
* Active

This allows tax rates to change over time without breaking old invoices.

Example:

```text
Tax Category: Standard Sales Tax
Rate: 18%
Effective From: 2026-07-01
Applies To: Sales
Province: Punjab
```

---

### 4. Ledgix Item Tax Profile

Maps each item to tax and FBR metadata.

Important fields:

* Item
* Taxable
* Tax Category
* HS Code
* UOM for FBR
* Sales Type
* Scenario ID
* SRO Schedule Number
* SRO Item Serial Number
* Needs Review
* Active

This is one of the most important setup documents for FBR readiness.

Each taxable item should ideally have:

```text
Item
Tax Category
HS Code
UOM for FBR
Sales Type
Scenario ID for Sandbox testing
```

---

### 5. Ledgix Sale

The sale document contains the actual POS invoice data.

Important FBR/tax fields:

* Tax Amount
* Grand Total
* Tax Details
* FBR Status
* FBR Invoice Number
* FBR QR Code
* FBR Submitted At
* FBR Upload Due At
* FBR Error Code
* FBR Error Message
* FBR Submission Log

The `Tax Details` child table is treated as an immutable snapshot. Once a sale is submitted, the invoice should keep the tax calculation that was valid at that time.

---

### 6. Ledgix FBR Settings

Single setup document for FBR control.

Important fields:

* Enabled
* Mode
* Submit Trigger
* Block Sale If FBR Readiness Fails
* Sandbox Post On Submit
* Retry Enabled
* Max Retry Count
* Offline Upload Window
* Seller NTN/CNIC
* Seller Business Name
* Seller Province
* Seller Address
* Sandbox Token
* Production Token
* Pause Reason

Supported modes:

```text
Disabled
Sandbox
Production
Paused
Manual Only
```

Supported submit triggers:

```text
Manual
On Submit
Validate Only
```

---

### 7. Ledgix FBR Submission Log

Stores every FBR attempt.

Important fields:

* Reference DocType
* Reference Name
* Invoice Type
* FBR Status
* FBR Invoice Number
* Attempt Count
* Next Retry Time
* Request JSON
* Response JSON
* Error Code
* Error Message
* Submitted By
* Submitted At

This is the audit trail for FBR troubleshooting.

---

## Tax Resolution Logic

Ledgix resolves tax in this order:

```text
1. Item Tax Profile
2. Product Category defaults
3. Shop default Tax Profile
```

This means item-specific tax mapping has the highest priority.

If an item has no direct tax mapping, Ledgix can still use category-level or shop-level defaults, but for FBR production readiness, item-level mapping is recommended because HS code, FBR UOM, sales type, and scenario information are usually item-specific.

---

## Inclusive vs Exclusive Tax

Ledgix supports both pricing styles.

### Tax Exclusive

```text
Item amount = 1,000
Tax rate = 18%
Tax amount = 180
Grand total = 1,180
```

### Tax Inclusive

```text
Shelf price = 1,000
Tax rate = 18%
Tax is extracted from inside 1,000
Grand total remains 1,000
```

This is controlled from `Ledgix Tax Profile` using:

```text
Price Includes Tax
```

---

## FBR Payload Requirements

Before an invoice can be submitted to FBR, Ledgix checks that required data exists.

### Seller Required Data

Configure in `Ledgix FBR Settings`:

```text
Seller NTN/CNIC
Seller Business Name
Seller Province
Seller Address
Sandbox Token or Production Token
```

### Buyer Required Data

Configure in `Ledgix Customer`:

```text
Buyer Business Name
Buyer Registration Type
Buyer Province
Buyer FBR Address
Buyer NTN/CNIC for registered buyers
Buyer STRN if available
```

For walk-in or consumer sales, Ledgix can use defaults from the tax profile where appropriate.

### Item Required Data

Configure in `Ledgix Item Tax Profile`:

```text
HS Code
UOM for FBR
Sales Type
Scenario ID for Sandbox
Tax Category
Tax Rate
SRO Schedule Number if applicable
SRO Item Serial Number if applicable
```

---

## FBR Setup Steps

### Step 1: Enable Tax

Open:

```text
Ledgix Tax Profile
```

Set:

```text
Tax Enabled = Yes
Price Includes Tax = Yes or No
Default Buyer Type = Registered / Unregistered / Consumer
Province = business province
Outlet Address = shop/outlet address
```

---

### Step 2: Create Tax Categories

Open:

```text
Ledgix Tax Category
```

Create required categories, for example:

```text
Standard Sales Tax
Exempt
Zero Rated
FED
```

For each category, set:

```text
Tax Type
Default Rate %
Is Exempt
Is Zero Rated
Active
```

---

### Step 3: Create Tax Rates

Open:

```text
Ledgix Tax Rate
```

Create effective-dated rates:

```text
Tax Category
Rate %
Effective From
Effective To, if any
Applies To
Province
Active
```

This keeps old invoices safe when tax rates change later.

---

### Step 4: Configure Item Tax Profiles

Open:

```text
Ledgix Item Tax Profile
```

For each taxable item, set:

```text
Item
Taxable
Tax Category
HS Code
UOM for FBR
Sales Type
Scenario ID
SRO Schedule Number, if required
SRO Item Serial Number, if required
Active
```

Items with missing HS code or FBR fields should stay marked as `Needs Review` until verified.

---

### Step 5: Configure Customers

For registered buyers, make sure customer records contain:

```text
Buyer NTN/CNIC
Buyer STRN
Buyer Registration Type = Registered
Buyer Province
Buyer FBR Address
```

For walk-in customers, use:

```text
Buyer Registration Type = Unregistered or Consumer
```

---

### Step 6: Configure FBR Settings

Open:

```text
Ledgix FBR Settings
```

For testing:

```text
Enabled = Yes
Mode = Sandbox
Submit Trigger = Validate Only or Manual
Sandbox Token = your FBR sandbox token
Seller NTN/CNIC = business NTN/CNIC
Seller Business Name = registered business name
Seller Province = business province
Seller Address = registered/outlet address
```

For production:

```text
Enabled = Yes
Mode = Production
Submit Trigger = Manual or On Submit
Production Token = live FBR token
Retry Enabled = Yes
Max Retry Count = 3
Offline Upload Window = 24
```

Recommended production start:

```text
Mode = Production
Submit Trigger = Manual
```

After successful testing, switch to:

```text
Submit Trigger = On Submit
```

---

## Submit Trigger Modes

### Manual

Sale is created and submitted inside Ledgix, but FBR submission is triggered manually.

Best for:

```text
Initial setup
Testing
Production rollout
Controlled submission
```

---

### Validate Only

Ledgix builds the payload and validates it with FBR, but does not fully post it as a final production invoice.

Best for:

```text
Sandbox testing
Data readiness testing
Item mapping validation
```

---

### On Submit

Ledgix automatically queues FBR work after sale submit.

Best for:

```text
Stable production
Fully mapped items
Verified tokens
Clean customer data
```

---

## FBR Status Meaning

```text
Not Required      FBR disabled or not needed
Pending           Waiting for manual/auto submission
Validated         Payload validated successfully
Submitted         FBR accepted invoice and returned invoice number
Failed            Validation/post failed
Offline Pending   Network failure; invoice needs retry/upload
Skipped           Submission intentionally skipped
Paused            FBR mode paused
```

---

## Recommended Rollout Plan

### Phase 1: Setup

```text
Tax Profile
Tax Categories
Tax Rates
Item Tax Profiles
Customer FBR fields
FBR Settings in Sandbox
```

### Phase 2: Sandbox Testing

```text
Create test sales
Preview tax snapshot
Validate FBR readiness
Generate payload
Validate with FBR sandbox
Fix HS code, UOM, sales type, scenario issues
```

### Phase 3: Controlled Production

```text
Switch mode to Production
Keep Submit Trigger = Manual
Submit selected invoices manually
Check FBR invoice number
Check submission logs
Check print format
```

### Phase 4: Auto Submission

```text
Switch Submit Trigger = On Submit
Enable retry
Monitor failed/offline invoices
Review FBR logs daily
```

---

## What Is Already Solved

Ledgix already handles:

* Tax category setup
* Effective-dated tax rates
* Inclusive/exclusive tax calculation
* Item-level FBR mapping
* Immutable sale tax snapshot
* FBR readiness validation
* FBR official payload generation
* Sandbox validation
* Production submission
* FBR response parsing
* FBR invoice number storage
* FBR QR code field storage
* Submission audit logs
* Retry queue
* Offline pending state
* Manual, validate-only, and on-submit flows
* FBR pause/manual-only safety modes

---

## Current Known Gaps

The following areas should be completed before a serious production rollout:

```text
1. FBR reference/master data sync is not automated yet.
2. QR/logo printing needs final print-format integration.
3. Production token and scenario values must be verified with real FBR credentials.
4. Item HS codes, UOM, sales type, and SRO data need business-side review.
5. Failed/offline submission dashboard should be polished for daily operations.
```

---

## Recommended Production Checklist

Before enabling production auto-submit:

```text
[ ] Tax Enabled is active
[ ] Seller NTN/CNIC is configured
[ ] Seller business name is configured
[ ] Seller province is configured
[ ] Seller address is configured
[ ] Production token is configured
[ ] All active items have Item Tax Profiles
[ ] All taxable items have HS codes
[ ] All taxable items have UOM for FBR
[ ] Sales Type is configured
[ ] Sandbox validation passed
[ ] Test production invoice submitted manually
[ ] FBR invoice number returned successfully
[ ] Submission log stores request/response correctly
[ ] Invoice print shows FBR invoice number
[ ] QR code print is tested
[ ] Retry worker is enabled
[ ] Offline upload handling is tested
```

---

## Practical Recommendation

Use this rollout order:

```text
Disabled
   ↓
Sandbox + Validate Only
   ↓
Sandbox + Manual
   ↓
Production + Manual
   ↓
Production + On Submit
```

Do not directly start with production auto-submit until item mappings, customer fields, token configuration, and print format are fully verified.
