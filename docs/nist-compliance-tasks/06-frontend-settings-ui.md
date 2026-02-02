# Task 06: Update Frontend Security Settings UI

## Overview

Update the Security Settings page to support NIST compliance mode with conditional rendering based on the selected mode.

## File to Modify

`frontend/src/pages/settings/SecuritySettings.tsx`

## Requirements

1. Add NIST Compliance Mode toggle
2. Show different UI based on mode:
   - NIST mode: Length + blocklist settings, hide complexity
   - Legacy mode: Existing complexity toggles
3. Add info/warning banners for each mode
4. Fetch and save new NIST settings

## Changes to State Interface

```typescript
interface SecuritySettingsState {
  // Existing fields
  maxLoginAttempts: number
  lockoutDuration: number
  passwordMinLength: number
  passwordRequireSpecial: boolean
  passwordRequireNumbers: boolean
  passwordRequireUppercase: boolean
  passwordExpirationDays: number
  // New NIST fields
  nistComplianceMode: boolean
  passwordMaxLength: number
  enableBlocklistCheck: boolean
  enableHibpCheck: boolean
  allowUnicodePasswords: boolean
}

const DEFAULT_SETTINGS: SecuritySettingsState = {
  // Existing defaults
  maxLoginAttempts: 5,
  lockoutDuration: 900,
  passwordMinLength: 8,
  passwordRequireSpecial: true,
  passwordRequireNumbers: true,
  passwordRequireUppercase: true,
  passwordExpirationDays: 90,
  // New NIST defaults
  nistComplianceMode: false,
  passwordMaxLength: 128,
  enableBlocklistCheck: true,
  enableHibpCheck: false,
  allowUnicodePasswords: true
}
```

## Updated Render Section

```tsx
{/* Password Policy Section */}
<Box>
  <Typography sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}>
    {t('settings.securitySettings.passwordPolicy')}
  </Typography>
  <Typography variant="caption" color="text.secondary">
    {t('settings.securitySettings.passwordPolicyDescription')}
  </Typography>

  <Stack spacing={0.5}>
    {/* NIST Compliance Mode Toggle */}
    <SettingRow
      label={t('settings.securitySettings.nistCompliance')}
      description={t('settings.securitySettings.nistComplianceDescription')}
    >
      <Toggle
        checked={settings.nistComplianceMode}
        onChange={(checked) => {
          updateSetting('nistComplianceMode', checked)
          // Auto-adjust min length when enabling NIST mode
          if (checked && settings.passwordMinLength < 15) {
            updateSetting('passwordMinLength', 15)
          }
        }}
        aria-label={t('settings.securitySettings.nistCompliance')}
      />
    </SettingRow>

    {/* Mode-specific info banner */}
    {settings.nistComplianceMode ? (
      <Alert severity="info" sx={{ my: 1, fontSize: '0.75rem' }}>
        {t('settings.securitySettings.nistModeInfo')}
      </Alert>
    ) : (
      <Alert severity="warning" sx={{ my: 1, fontSize: '0.75rem' }}>
        {t('settings.securitySettings.legacyModeWarning')}
      </Alert>
    )}

    {/* Minimum Length - different range based on mode */}
    <SettingRow
      label={t('settings.securitySettings.minLength')}
      description={t('settings.securitySettings.minLengthDescription')}
    >
      <TextField
        type="number"
        size="small"
        value={settings.passwordMinLength}
        onChange={(e) => {
          const min = settings.nistComplianceMode ? 15 : 6
          const max = settings.nistComplianceMode ? 64 : 32
          updateSetting('passwordMinLength',
            Math.max(min, Math.min(max, parseInt(e.target.value) || min)))
        }}
        inputProps={{
          min: settings.nistComplianceMode ? 15 : 6,
          max: settings.nistComplianceMode ? 64 : 32
        }}
        sx={{ width: 80 }}
      />
    </SettingRow>

    {settings.nistComplianceMode ? (
      // NIST Mode UI
      <>
        <SettingRow
          label={t('settings.securitySettings.blocklistCheck')}
          description={t('settings.securitySettings.blocklistCheckDescription')}
        >
          <Toggle
            checked={settings.enableBlocklistCheck}
            onChange={(checked) => updateSetting('enableBlocklistCheck', checked)}
            aria-label={t('settings.securitySettings.blocklistCheck')}
          />
        </SettingRow>

        <SettingRow
          label={t('settings.securitySettings.hibpCheck')}
          description={t('settings.securitySettings.hibpCheckDescription')}
        >
          <Toggle
            checked={settings.enableHibpCheck}
            onChange={(checked) => updateSetting('enableHibpCheck', checked)}
            aria-label={t('settings.securitySettings.hibpCheck')}
          />
        </SettingRow>

        <SettingRow
          label={t('settings.securitySettings.allowUnicode')}
          description={t('settings.securitySettings.allowUnicodeDescription')}
        >
          <Toggle
            checked={settings.allowUnicodePasswords}
            onChange={(checked) => updateSetting('allowUnicodePasswords', checked)}
            aria-label={t('settings.securitySettings.allowUnicode')}
          />
        </SettingRow>
      </>
    ) : (
      // Legacy Mode UI (existing code)
      <>
        <SettingRow
          label={t('settings.securitySettings.requireUppercase')}
          description={t('settings.securitySettings.requireUppercaseDescription')}
        >
          <Toggle
            checked={settings.passwordRequireUppercase}
            onChange={(checked) => updateSetting('passwordRequireUppercase', checked)}
            aria-label={t('settings.securitySettings.requireUppercase')}
          />
        </SettingRow>

        <SettingRow
          label={t('settings.securitySettings.requireNumbers')}
          description={t('settings.securitySettings.requireNumbersDescription')}
        >
          <Toggle
            checked={settings.passwordRequireNumbers}
            onChange={(checked) => updateSetting('passwordRequireNumbers', checked)}
            aria-label={t('settings.securitySettings.requireNumbers')}
          />
        </SettingRow>

        <SettingRow
          label={t('settings.securitySettings.requireSpecial')}
          description={t('settings.securitySettings.requireSpecialDescription')}
        >
          <Toggle
            checked={settings.passwordRequireSpecial}
            onChange={(checked) => updateSetting('passwordRequireSpecial', checked)}
            aria-label={t('settings.securitySettings.requireSpecial')}
          />
        </SettingRow>

        <SettingRow
          label={t('settings.securitySettings.passwordExpiration')}
          description={t('settings.securitySettings.passwordExpirationCurrent', {
            duration: formatExpiration(settings.passwordExpirationDays)
          })}
        >
          <FormControl size="small">
            <Select
              value={String(settings.passwordExpirationDays)}
              onChange={(e) => updateSetting('passwordExpirationDays', parseInt(e.target.value))}
              size="small"
              sx={selectStyles}
              MenuProps={menuProps}
            >
              <MenuItem value={0}>{t('settings.durations.never')}</MenuItem>
              <MenuItem value={30}>30 days</MenuItem>
              <MenuItem value={60}>60 days</MenuItem>
              <MenuItem value={90}>90 days</MenuItem>
              <MenuItem value={180}>180 days</MenuItem>
              <MenuItem value={365}>1 year</MenuItem>
            </Select>
          </FormControl>
        </SettingRow>
      </>
    )}
  </Stack>
</Box>
```

## Update Fetch Function

```typescript
const fetchSecuritySettings = useCallback(async () => {
  // ... existing code ...

  const response = await client.callTool<SecuritySettingsResponse>(
    'get_settings',
    {
      user_id: 'admin',
      setting_keys: [
        // Existing keys
        'security.max_login_attempts',
        'security.account_lockout_duration',
        'security.password_min_length',
        'security.password_require_special_chars',
        'security.password_require_numbers',
        'security.password_require_uppercase',
        'security.force_password_change_days',
        // New NIST keys
        'security.nist_compliance_mode',
        'security.password_max_length',
        'security.enable_blocklist_check',
        'security.enable_hibp_api_check',
        'security.allow_unicode_passwords'
      ],
      include_system_defaults: true
    }
  )

  // ... parse response including new fields ...
}, [isConnected, client])
```

## Update Save Function

```typescript
const handleSaveSettings = async () => {
  // ... existing code ...

  const response = await client.callTool<SettingsUpdateResponse>(
    'update_settings',
    {
      user_id: 'admin',
      settings: {
        // Existing settings
        'security.max_login_attempts': settings.maxLoginAttempts,
        'security.account_lockout_duration': settings.lockoutDuration,
        'security.password_min_length': settings.passwordMinLength,
        'security.password_require_special_chars': settings.passwordRequireSpecial,
        'security.password_require_numbers': settings.passwordRequireNumbers,
        'security.password_require_uppercase': settings.passwordRequireUppercase,
        'security.force_password_change_days': settings.passwordExpirationDays,
        // New NIST settings
        'security.nist_compliance_mode': settings.nistComplianceMode,
        'security.password_max_length': settings.passwordMaxLength,
        'security.enable_blocklist_check': settings.enableBlocklistCheck,
        'security.enable_hibp_api_check': settings.enableHibpCheck,
        'security.allow_unicode_passwords': settings.allowUnicodePasswords
      },
      change_reason: 'Updated via Settings page'
    }
  )

  // ... handle response ...
}
```

## Dependencies

- Task 05: Database settings must exist
- Task 09: i18n labels must be added

## Acceptance Criteria

- [ ] NIST Compliance toggle is visible at top of Password Policy section
- [ ] Enabling NIST mode auto-adjusts min length to 15
- [ ] NIST mode hides complexity toggles and expiration
- [ ] NIST mode shows blocklist and HIBP settings
- [ ] Legacy mode shows all existing toggles
- [ ] Info banner shown in NIST mode
- [ ] Warning banner shown in legacy mode
- [ ] Settings save and load correctly
- [ ] UI is responsive and accessible
