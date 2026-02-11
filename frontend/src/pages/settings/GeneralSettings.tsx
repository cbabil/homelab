/**
 * General Settings Component
 *
 * Application-wide general preferences including language, timezone, and display options.
 * Single card with vertical sections separated by dividers.
 */

import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Stack,
  Box,
  Typography,
  Divider,
  Select,
  MenuItem,
  FormControl,
  SelectChangeEvent,
} from '@mui/material';
import { SettingRow } from './components';
import { TimezoneDropdown } from '@/components/settings/TimezoneDropdown';
import { useSettingsContext } from '@/providers/SettingsProvider';
import { useSettingsSaving } from './SettingsSavingContext';

const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Français', value: 'fr' },
  { label: 'Deutsch', value: 'de' },
  { label: 'Español', value: 'es' },
  { label: '日本語', value: 'ja' },
  { label: '中文', value: 'zh' },
  { label: 'Português', value: 'pt' },
  { label: '한국어', value: 'ko' },
  { label: 'Italiano', value: 'it' },
  { label: 'العربية', value: 'ar' },
];

// These need to be functions that return arrays to use translations
const getRefreshOptions = (t: (key: string) => string) => [
  { label: t('settings.generalSettings.refreshOptions.30seconds'), value: '30' },
  { label: t('settings.generalSettings.refreshOptions.1minute'), value: '60' },
  { label: t('settings.generalSettings.refreshOptions.5minutes'), value: '300' },
];

const getDefaultPageOptions = (t: (key: string) => string) => [
  { label: t('settings.generalSettings.pageOptions.dashboard'), value: 'dashboard' },
  { label: t('settings.generalSettings.pageOptions.servers'), value: 'servers' },
  { label: t('settings.generalSettings.pageOptions.applications'), value: 'applications' },
];

// Common select styles for MUI Select
const selectStyles = {
  height: 32,
  minWidth: 144,
  fontSize: '0.75rem',
  borderRadius: 1,
  bgcolor: 'transparent',
  '& .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.23)',
  },
  '&:hover .MuiOutlinedInput-notchedOutline': {
    borderColor: 'rgba(255, 255, 255, 0.4)',
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: 'primary.main',
    borderWidth: 1,
  },
  '& .MuiSelect-select': {
    py: 0.5,
    px: 1,
  },
};

const menuProps = {
  PaperProps: {
    sx: {
      '& .MuiMenuItem-root': {
        fontSize: '0.75rem',
      },
    },
  },
};

export function GeneralSettings() {
  const { t } = useTranslation();
  const { settings, updateSettings } = useSettingsContext();
  const { setIsSaving } = useSettingsSaving();

  // UI settings (persisted)
  const language = settings?.ui?.language ?? 'en';
  const refreshRate = String(settings?.ui?.refreshRate ?? 60);
  const defaultPage = settings?.ui?.defaultPage ?? 'dashboard';

  // Helper to save with indicator
  const saveWithIndicator = useCallback(
    async (updates: Record<string, unknown>) => {
      setIsSaving(true);
      try {
        await updateSettings('ui', updates);
      } finally {
        setIsSaving(false);
      }
    },
    [updateSettings, setIsSaving]
  );

  // Handlers
  const handleLanguageChange = (event: SelectChangeEvent) => {
    saveWithIndicator({ language: event.target.value });
  };

  const handleRefreshRateChange = (event: SelectChangeEvent) => {
    saveWithIndicator({ refreshRate: parseInt(event.target.value, 10) });
  };

  const handleDefaultPageChange = (event: SelectChangeEvent) => {
    saveWithIndicator({ defaultPage: event.target.value });
  };

  return (
    <Box
      sx={{
        bgcolor: 'background.paper',
        borderRadius: 2,
        border: 1,
        borderColor: 'divider',
        p: 2,
        flex: 1,
      }}
    >
      {/* Language & Region */}
      <Box>
        <Typography
          sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}
        >
          {t('settings.generalSettings.languageRegion')}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t('settings.generalSettings.languageRegionDescription')}
        </Typography>
        <Stack spacing={0.5}>
          <SettingRow
            label={t('settings.generalSettings.language')}
            description={t('settings.generalSettings.languageDescription')}
          >
            <FormControl size="small">
              <Select
                value={language}
                onChange={handleLanguageChange}
                size="small"
                sx={selectStyles}
                MenuProps={menuProps}
              >
                {languageOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </SettingRow>
          <SettingRow
            label={t('settings.generalSettings.timezone')}
            description={t('settings.generalSettings.timezoneDescription')}
          >
            <TimezoneDropdown />
          </SettingRow>
        </Stack>
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* Application */}
      <Box>
        <Typography
          sx={{ fontSize: '0.9rem', fontWeight: 600, color: 'primary.main', lineHeight: 1.2 }}
        >
          {t('settings.generalSettings.application')}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t('settings.generalSettings.applicationDescription')}
        </Typography>
        <Stack spacing={0.5}>
          <SettingRow
            label={t('settings.generalSettings.autoRefresh')}
            description={t('settings.generalSettings.autoRefreshDescription')}
          >
            <FormControl size="small">
              <Select
                value={refreshRate}
                onChange={handleRefreshRateChange}
                size="small"
                sx={selectStyles}
                MenuProps={menuProps}
              >
                {getRefreshOptions(t).map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </SettingRow>
          <SettingRow
            label={t('settings.generalSettings.defaultPage')}
            description={t('settings.generalSettings.defaultPageDescription')}
          >
            <FormControl size="small">
              <Select
                value={defaultPage}
                onChange={handleDefaultPageChange}
                size="small"
                sx={selectStyles}
                MenuProps={menuProps}
              >
                {getDefaultPageOptions(t).map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </SettingRow>
        </Stack>
      </Box>
    </Box>
  );
}
