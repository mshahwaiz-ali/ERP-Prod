# FBR Production Checklist

## Sandbox First

- Configure `Ledgix FBR Settings` in Sandbox mode.
- Confirm seller NTN/CNIC, business name, province, and address.
- Confirm item HS codes, FBR UOM, sales type, and tax category mappings.
- Create a submitted test sale and verify the tax snapshot.
- Validate the sale against sandbox FBR.
- Create and validate a sales return where applicable.

## Health Checks

- Run `bench --site SITE execute ledgix_saas.api.fbr_health.check`.
- Confirm the requests package is available.
- Confirm FBR Settings and Submission Log DocTypes exist.
- Confirm retry and offline upload scheduler hooks are registered.
- Confirm token values are configured without printing the values.

## Production Switch

- Enable HTTPS first.
- Confirm backups and restore instructions.
- Switch FBR mode to Production only after sandbox tests are reviewed.
- Keep `submit_trigger` conservative until live behavior is verified.
- Review `Ledgix FBR Submission Log` after every first live attempt.

## Failure Handling

- Confirm failed submissions save safe error messages.
- Confirm retry settings and max retry count.
- Confirm offline upload window.
- Confirm duplicate FBR invoice protection before retrying manually.
