# Task 09: Add i18n Labels

## Overview

Add internationalization labels for all new NIST compliance UI elements.

## File to Modify

`frontend/src/i18n/locales/en/translation.json`

## New Labels to Add

Add to the `settings.securitySettings` section:

```json
{
  "settings": {
    "securitySettings": {
      "// Existing labels...": "",

      "// NIST Compliance labels": "",
      "nistCompliance": "NIST SP 800-63B Compliance",
      "nistComplianceDescription": "Enable modern password policy based on length and blocklist screening instead of complexity rules",
      "nistModeInfo": "NIST compliance mode enforces a minimum 15 character password, screens against known breached passwords, and removes arbitrary complexity rules and mandatory password expiration.",
      "legacyModeWarning": "Legacy password complexity rules are being phased out. Consider enabling NIST compliance mode for modern security standards.",

      "// Blocklist settings": "",
      "blocklistCheck": "Password blocklist screening",
      "blocklistCheckDescription": "Screen new passwords against known breached and commonly used passwords",
      "hibpCheck": "Have I Been Pwned API",
      "hibpCheckDescription": "Check passwords against the HIBP breach database (requires internet connectivity, uses privacy-preserving k-Anonymity)",

      "// Unicode settings": "",
      "allowUnicode": "Allow Unicode passwords",
      "allowUnicodeDescription": "Allow spaces, emojis, and international characters in passwords",

      "// Updated descriptions for legacy mode": "",
      "requireUppercaseLegacy": "Require uppercase letters (legacy)",
      "requireNumbersLegacy": "Require numbers (legacy)",
      "requireSpecialLegacy": "Require special characters (legacy)"
    }
  }
}
```

Add to the `auth` section for password strength indicator:

```json
{
  "auth": {
    "// Existing labels...": "",

    "passwordRequirements": {
      "// NIST mode requirements": "",
      "minLengthNist": "At least {{count}} characters",
      "notCommon": "Not a commonly used password",
      "noSequential": "No sequential patterns (1234, abcd)",
      "noRepetitive": "No repetitive characters (aaaa)",
      "noUsername": "Does not contain your username",
      "passphraseTip": "Tip: Use a passphrase like \"correct-horse-battery-staple\"",

      "// Legacy mode requirements": "",
      "minLength": "At least {{count}} characters",
      "hasUppercase": "One uppercase letter",
      "hasLowercase": "One lowercase letter",
      "hasNumber": "One number",
      "hasSpecialChar": "One special character",

      "// Strength labels": "",
      "strengthTooShort": "Too Short",
      "strengthWeak": "Weak",
      "strengthFair": "Fair",
      "strengthGood": "Good",
      "strengthStrong": "Strong",
      "strengthExcellent": "Excellent"
    }
  }
}
```

## Full Context in translation.json

Here's the complete structure showing where to add the new labels:

```json
{
  "settings": {
    "securitySettings": {
      "title": "Security",
      "accountLocking": "Account Locking",
      "accountLockingDescription": "Configure account lockout settings after failed login attempts",
      "maxAttempts": "Maximum login attempts",
      "maxAttemptsDescription": "Number of failed attempts before account lockout",
      "lockoutDuration": "Lockout duration",
      "lockoutDurationCurrent": "Current: {{duration}}",

      "passwordPolicy": "Password Policy",
      "passwordPolicyDescription": "Configure password requirements for new passwords",
      "minLength": "Minimum length",
      "minLengthDescription": "Minimum number of characters required",
      "requireUppercase": "Require uppercase",
      "requireUppercaseDescription": "Password must contain at least one uppercase letter",
      "requireNumbers": "Require numbers",
      "requireNumbersDescription": "Password must contain at least one digit",
      "requireSpecial": "Require special characters",
      "requireSpecialDescription": "Password must contain at least one special character",
      "passwordExpiration": "Password expiration",
      "passwordExpirationCurrent": "Current: {{duration}}",

      "// NEW NIST labels (add these)": "",
      "nistCompliance": "NIST SP 800-63B Compliance",
      "nistComplianceDescription": "Enable modern password policy based on length and blocklist screening instead of complexity rules",
      "nistModeInfo": "NIST compliance mode enforces a minimum 15 character password, screens against known breached passwords, and removes arbitrary complexity rules and mandatory password expiration.",
      "legacyModeWarning": "Legacy password complexity rules are being phased out. Consider enabling NIST compliance mode for modern security standards.",
      "blocklistCheck": "Password blocklist screening",
      "blocklistCheckDescription": "Screen new passwords against known breached and commonly used passwords",
      "hibpCheck": "Have I Been Pwned API",
      "hibpCheckDescription": "Check passwords against the HIBP breach database (requires internet connectivity)",
      "allowUnicode": "Allow Unicode passwords",
      "allowUnicodeDescription": "Allow spaces, emojis, and international characters in passwords",

      "securitySettingsSaved": "Security settings saved",
      "failedToSave": "Failed to save security settings",
      "reset": "Reset",
      "saveChanges": "Save Changes"
    }
  },

  "auth": {
    "passwordRequirements": {
      "// NEW NIST labels (add these)": "",
      "minLengthNist": "At least {{count}} characters",
      "notCommon": "Not a commonly used password",
      "noSequential": "No sequential patterns (1234, abcd)",
      "noRepetitive": "No repetitive characters (aaaa)",
      "noUsername": "Does not contain your username",
      "passphraseTip": "Tip: Use a passphrase like \"correct-horse-battery-staple\"",
      "strengthTooShort": "Too Short",
      "strengthWeak": "Weak",
      "strengthFair": "Fair",
      "strengthGood": "Good",
      "strengthStrong": "Strong",
      "strengthExcellent": "Excellent"
    }
  }
}
```

## Additional Locale Files

If the application supports multiple languages, similar labels should be added to:
- `frontend/src/i18n/locales/fr/translation.json` (if French support)
- `frontend/src/i18n/locales/es/translation.json` (if Spanish support)
- etc.

## French Example (if applicable)

```json
{
  "settings": {
    "securitySettings": {
      "nistCompliance": "Conformité NIST SP 800-63B",
      "nistComplianceDescription": "Activer la politique de mot de passe moderne basée sur la longueur et le filtrage des listes noires",
      "nistModeInfo": "Le mode de conformité NIST impose un minimum de 15 caractères, vérifie les mots de passe compromis connus et supprime les règles de complexité arbitraires.",
      "legacyModeWarning": "Les règles de complexité héritées sont en cours de suppression. Envisagez d'activer le mode de conformité NIST.",
      "blocklistCheck": "Vérification de la liste noire",
      "blocklistCheckDescription": "Vérifier les nouveaux mots de passe par rapport aux mots de passe compromis connus",
      "hibpCheck": "API Have I Been Pwned",
      "hibpCheckDescription": "Vérifier les mots de passe dans la base de données HIBP (nécessite une connexion Internet)"
    }
  },
  "auth": {
    "passwordRequirements": {
      "minLengthNist": "Au moins {{count}} caractères",
      "notCommon": "Pas un mot de passe couramment utilisé",
      "noSequential": "Pas de motifs séquentiels (1234, abcd)",
      "noRepetitive": "Pas de caractères répétitifs (aaaa)",
      "passphraseTip": "Conseil: Utilisez une phrase de passe comme \"correct-cheval-batterie-agrafe\""
    }
  }
}
```

## Acceptance Criteria

- [ ] All NIST-related labels added to English translation file
- [ ] Labels follow existing naming conventions
- [ ] Labels are clear and descriptive
- [ ] Placeholders ({{count}}, {{duration}}) used where appropriate
- [ ] No duplicate keys
- [ ] JSON is valid (no syntax errors)
